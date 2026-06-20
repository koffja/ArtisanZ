# TM-ArtisanZ Plus-Compatible 集成设计

日期：2026-06-20

项目：ArtisanZ + Taster-Matrix

状态：设计已由用户口头认可，并已拆分为后端规格与客户端/品牌拆分规格。

拆分规格：

- Taster-Matrix 后端规格：`/Users/chengzhe/Projects/Taster-Matrix/docs/integrations/tm-artisanz/backend-spec.md`
- ArtisanZ 客户端与品牌拆分规格：`/Users/chengzhe/Projects/ArtisanZ/docs/superpowers/specs/2026-06-20-tm-artisanz-client-branding-design.md`

## 1. 背景与目标

ArtisanZ 是基于 upstream Artisan 的定制分支。当前项目已有 charge target、中文本地化、Windows portable packaging 等定制内容，因此本次目标不是把官方 Artisan 当作不可修改黑盒，而是在 ArtisanZ 产品分支中复用 Artisan Plus 客户端代码，将云同步目标从 `artisan.plus` 改为我们自己的 Taster-Matrix 后台。

目标系统暂名为 TM-ArtisanZ。它需要做到：

1. ArtisanZ 不再向 `artisan.plus` 上传数据。
2. 用户登录完全使用 Taster-Matrix 现有账号体系。
3. 用户结束烘焙后，先在 ArtisanZ 中确认烘焙批次信息，再上传至 Taster-Matrix。
4. 第一阶段尽量兼容 Artisan Plus 协议，让 `src/plus/` 的登录、队列、重试、同步能力可以继续复用。
5. 上传后的烘焙记录成为 Taster-Matrix 的原生 RoastRecord 数据，而不是长期停留在 Plus payload 的临时结构中。

第一阶段选择“核心兼容优先”：

- 真实实现登录、烘焙上传、烘焙读取/同步。
- 库存、排程、通知端点先返回最小兼容数据，让 ArtisanZ 不报错。
- 后续再把 Taster-Matrix 的材料库、库存、排程、组织权限逐步映射到 ArtisanZ 的 Plus UI。

## 2. 对现有报告的判断

`ARTISAN_PLUS_INTEGRATION_SPEC.md` 作为 Plus 协议和源码索引是合理的，尤其是这些结论可以直接采用：

- `src/plus/` 是独立子包，包含 config、connection、controller、login、queue、roast、sync、stock、schedule 等模块。
- `connection.py` 是 HTTP chokepoint，统一处理 headers、gzip、Bearer token、401 re-auth。
- `queue.py` 使用 SQLite outbox，适合断网重试。
- `roast.py:getRoast()` 能构建 Plus `/aroast` 上传摘要。
- `sync.py` 使用 `modified_at` 和 sync record hash 做最后写入者优先的增量同步。
- `canvas.py`、`main.py`、`roast_properties.py` 已经有 CHARGE、DROP、保存、属性编辑等上传触发点。

但这份报告对 TM-ArtisanZ 目标不完整，需要修订：

1. 报告说“do not fork Artisan”，这与 ArtisanZ 的项目现实不符。ArtisanZ 本来就是产品定制分支，应允许低侵入客户端改造。
2. 报告默认推荐 Plan A + Plan B，即文件监听和 MQTT。这个路径适合外部接入官方 Artisan，但不适合作为 ArtisanZ 产品化主线。
3. 报告的 Plan D 把目标描述成完整替代 artisan.plus，范围过大。TM-ArtisanZ 第一阶段应拆成“核心 auth/roast 兼容 + stock/schedule/notifications stub”。
4. Plus `/aroast` payload 主要是烘焙摘要和同步字段，不包含完整 `timex/temp1/temp2` 曲线数组。若 Taster-Matrix 要做曲线管理，必须扩展上传完整 Artisan profile。
5. 报告没有纳入 Taster-Matrix 的现有账号、组织、权限、PostgreSQL/Drizzle 架构。
6. 报告没有设计“DROP 后确认再上传”的产品流程。

建议在报告中新增一个主路线：Plan E - TM-ArtisanZ Plus-Compatible Adapter。

## 3. 选定方案

采用“后端 Plus-compatible Adapter + 客户端低侵入改造”的方案。

整体结构：

```text
ArtisanZ desktop
  └─ src/plus/* 复用登录、队列、同步、roast payload
      └─ https://tastermatrix.com/api/tm-artisanz/v1/*
          └─ Taster-Matrix Fastify adapter
              ├─ auth/account-service.ts 账号登录
              ├─ tenant.organizations / tenant.org_members 组织归属
              └─ roast_records / roast_curve_points / roast_events / roast_measures
```

关键原则：

- 协议兼容留在 Taster-Matrix adapter。
- 产品体验留在 ArtisanZ 客户端。
- 烘焙领域数据落在 Taster-Matrix 原生 roast 表。
- Plus 代码只作为客户端能力来源，不让业务语义继续绑定 `artisan.plus`。

## 4. 范围

第一阶段包含：

1. Taster-Matrix 后端新增 `/api/tm-artisanz/v1` 路由组。
2. 实现 Plus-compatible 登录响应。
3. 实现 Plus-compatible roast upsert 和 roast sync fetch。
4. 新增 RoastRecord 相关 PostgreSQL 表。
5. ArtisanZ 客户端指向 Taster-Matrix endpoint。
6. ArtisanZ 客户端将 `artisan.plus` 文案、keyring service、链接逐步替换成 TM-ArtisanZ。
7. DROP 后打开批次确认对话框，用户确认后才上传。
8. 上传 payload 扩展携带完整 Artisan profile。

第一阶段不包含：

- 完整 stock/coffee/blend/store/schedule 管理。
- 真实排程锁定。
- 云端通知系统。
- 多组织登录选择 UI 的完整产品化。
- Taster-Matrix 前端 roast overview/detail/compare 管理页面。
- 远程控制 ArtisanZ 开始/结束烘焙。

## 5. Taster-Matrix 现有能力映射

Taster-Matrix 当前后端是 Fastify + PostgreSQL + Drizzle，主要入口在 `vps-backend/`。

可复用能力：

- `src/app.ts`：统一注册 Fastify routes/plugins。
- `src/plugins/auth.ts`：Bearer token 校验插件。
- `src/services/auth/account-service.ts`：账号登录、密码校验、token 生成。
- `src/services/auth/auth-service.ts`：`createAuthToken()`、`validateAuthTokenWithRevocation()`。
- `src/db/schema/identity.ts`：`users`、`user_identities`、`auth_sessions`。
- `src/db/schema/tenant.ts`：`tenant.organizations`、`tenant.org_members`、组织权限和订阅字段。
- `src/services/organization/organization-manager-service.ts`：组织成员权限检查参考。
- `src/services/coffee-materials/coffee-materials-service.ts`：现有材料库，但第一阶段不直接映射到 Plus stock。

重要安全约束：

- `tenantId` 只是路由/归属线索，不能作为权限证明。
- 组织权限必须通过 `tenant.org_members` 与 `tenant.organizations` 的 accepted membership 判断。
- `viewer` 角色应在 Plus 响应中映射为 `readonly: true`。

## 6. 后端路由设计

新增文件建议：

- `vps-backend/src/routes/tm-artisanz.ts`
- `vps-backend/src/services/tm-artisanz/auth-adapter-service.ts`
- `vps-backend/src/services/tm-artisanz/roast-sync-service.ts`
- `vps-backend/src/services/tm-artisanz/roast-profile-normalizer.ts`
- `vps-backend/src/schemas/tm-artisanz.ts`
- `vps-backend/src/db/schema/artisanz-roasts.ts`
- `vps-backend/src/db/migrations/00xx_artisanz_roasts.sql`

在 `src/app.ts` 中注册：

```ts
await registerArtisanZPlusRoutes(app)
```

### 6.1 登录端点

Endpoint：

```http
POST /api/tm-artisanz/v1/accounts/users/authenticate
Content-Type: application/json

{"email":"user@example.com","password":"plain password"}
```

处理逻辑：

1. 接收 Plus 客户端发来的 `{email, password}`。
2. 内部复用 Taster-Matrix 现有账号登录逻辑。
3. 查询用户 accepted organizations。
4. 选择当前 organization 作为 Plus account。
5. 转换为 Plus 客户端期望响应。

响应结构：

```json
{
  "success": true,
  "result": {
    "user": {
      "token": "<taster-matrix-jwt>",
      "nickname": "<nickname>",
      "language": "zh-CN",
      "user_id": "<tm-user-id>",
      "readonly": false,
      "account": {
        "_id": "<tm-org-id-or-personal-account-id>",
        "subscription": "PRO",
        "paidUntil": "2099-12-31T00:00:00.000Z",
        "limit": {
          "rlimit": 999999,
          "rused": 0
        }
      }
    }
  },
  "notifications": {
    "unqualified": 0,
    "machines": []
  },
  "ol": {
    "rlimit": 999999,
    "rused": 0
  },
  "pu": "2099-12-31T00:00:00.000Z"
}
```

错误：

- 账号不存在：`404`
- 密码错误：`401`
- 账号被封禁/关闭：`403`
- 后端不可用：`503`

### 6.2 Roast upsert

Endpoint：

```http
POST /api/tm-artisanz/v1/aroast
Authorization: Bearer <token>
Idempotency-Key: <uuid>
Content-Encoding: gzip
```

输入包含原 Plus roast payload，并扩展一个可选字段：

```json
{
  "roast_id": "32-char-hex",
  "date": "2026-06-20T10:20:30.000Z",
  "amount": 1.2,
  "modified_at": "2026-06-20T10:25:30.000Z",
  "tm_profile": {
    "roastUUID": "...",
    "timex": [],
    "temp1": [],
    "temp2": [],
    "timeindex": [],
    "computed": {}
  }
}
```

处理逻辑：

1. 验证 Bearer token。
2. 解析 gzip body。
3. 读取 `Idempotency-Key`。
4. 校验 `roast_id`、`modified_at`。
5. 根据 token 解析 user，再解析当前 organization。
6. 以 `(org_id, roast_uuid)` 幂等 upsert `roast_records`。
7. 如果同一 `Idempotency-Key` 已处理过，返回原响应，不重复写入。
8. 如果有 `tm_profile`，解析曲线、事件、指标。
9. 写入 raw payload 和 profile hash，保留追溯能力。

响应：

```json
{
  "success": true,
  "result": {
    "roast_id": "<roast_id>",
    "modified_at": "<server-modified-at>"
  },
  "notifications": {
    "unqualified": 0,
    "machines": []
  },
  "ol": {
    "rlimit": 999999,
    "rused": 0
  },
  "pu": "2099-12-31T00:00:00.000Z"
}
```

### 6.3 Roast sync fetch

Endpoint：

```http
GET /api/tm-artisanz/v1/aroast/{roastUUID}?modified_at=<client_ms_epoch>
Authorization: Bearer <token>
```

处理逻辑：

1. 验证 Bearer token。
2. 以 user organization + `roastUUID` 查找记录。
3. 找不到返回 `404`。
4. 服务端 `modified_at` 不比客户端新，返回 `204`。
5. 服务端较新，返回 `200` 和 Plus sync record。

返回的 `result` 只包含 ArtisanZ 能安全回写到 Roast Properties 的字段：

- `roast_id`
- `location`
- `coffee`
- `blend`
- `amount`
- `end_weight`
- `defects_weight`
- `density_roasted`
- `batch_number`
- `batch_prefix`
- `batch_pos`
- `whole_color`
- `ground_color`
- `color_system`
- `moisture`
- `label`
- `notes`
- `cupping_notes`
- `cupping_score`
- `s_item_id`
- `modified_at`

完整曲线不通过此端点回灌。第一阶段只把完整曲线作为服务端管理和后续前端可视化数据。

### 6.4 Stock stub

Endpoint：

```http
GET /api/tm-artisanz/v1/acoffees?today=YYYY-MM-DD&lsrt=<serverTime>
```

第一阶段响应：

```json
{
  "success": true,
  "result": {
    "coffees": [],
    "blends": [],
    "replBlends": [],
    "schedule": [],
    "retrieved": 1780000000,
    "serverTime": 1780000000
  }
}
```

如果带 `lsrt` 且没有变更，可返回 `204`。

### 6.5 Schedule lock stub

Endpoint：

```http
POST /api/tm-artisanz/v1/aschedule/lock?today=YYYY-MM-DD
```

第一阶段记录审计信息后返回成功，不做真实排程锁。

### 6.6 Notifications stub

Endpoint：

```http
GET /api/tm-artisanz/v1/notifications?machine=<name>
```

第一阶段返回空通知。

## 7. 数据模型设计

新增 schema 建议命名为 `artisanz` 或 `roasting`。为避免与现有 `business`、`tenant` 混淆，建议使用 `roasting` schema。

### 7.1 roast_records

用途：烘焙主档。以组织和 roast UUID 幂等。

核心字段：

- `id uuid primary key`
- `org_id uuid not null`
- `user_id uuid not null`
- `roast_uuid text not null`
- `source text not null default 'artisanz'`
- `label text`
- `beans text`
- `operator text`
- `machine text`
- `setup text`
- `temperature_unit text`
- `roasted_at timestamptz`
- `batch_number integer`
- `batch_prefix text`
- `batch_pos integer`
- `amount_kg numeric`
- `end_weight_kg numeric`
- `defects_weight_kg numeric`
- `weight_loss_pct numeric`
- `whole_color numeric`
- `ground_color numeric`
- `color_system text`
- `moisture numeric`
- `notes text`
- `cupping_notes text`
- `cupping_score numeric`
- `plus_sync_record jsonb`
- `raw_plus_payload jsonb`
- `raw_profile jsonb`
- `profile_hash text`
- `modified_at timestamptz not null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

约束：

- unique `(org_id, roast_uuid)`。
- `roast_uuid` 必须非空。
- 若某些历史账号没有组织，登录 adapter 应先解析或创建 personal organization。不要让 `roast_records.org_id` 长期 nullable，否则 PostgreSQL unique 约束无法可靠防止同一用户重复写入同一 roast。

### 7.2 roast_curve_points

用途：图表曲线点位。

核心字段：

- `id uuid primary key`
- `roast_record_id uuid not null references roast_records(id)`
- `series text not null`
- `sample_index integer not null`
- `time_seconds numeric not null`
- `value numeric`
- `unit text`
- `metadata jsonb`

典型 series：

- `BT`
- `ET`
- `BT_ROR`
- `ET_ROR`
- `extra_temp1:<device-index>`
- `extra_temp2:<device-index>`

约束：

- unique `(roast_record_id, series, sample_index)`

### 7.3 roast_events

用途：标准事件和自定义事件。

核心字段：

- `id uuid primary key`
- `roast_record_id uuid not null references roast_records(id)`
- `event_type text not null`
- `event_label text`
- `time_seconds numeric`
- `sample_index integer`
- `temperature_bt numeric`
- `temperature_et numeric`
- `value numeric`
- `metadata jsonb`
- `created_at timestamptz`

标准事件：

- `CHARGE`
- `DRY`
- `FCs`
- `FCe`
- `SCs`
- `SCe`
- `DROP`
- `COOL`

自定义事件从 `specialevents`、`specialeventstype`、`specialeventsvalue`、`specialeventsStrings` 解析。

### 7.4 roast_measures

用途：指标和派生值。

核心字段：

- `id uuid primary key`
- `roast_record_id uuid not null references roast_records(id)`
- `measure_key text not null`
- `measure_value numeric`
- `unit text`
- `source text`
- `metadata jsonb`

典型指标：

- `TP_time`
- `DRY_time`
- `FCs_time`
- `FCe_time`
- `DROP_time`
- `DEV_time`
- `DEV_ratio`
- `AUC`
- `AUC_base`
- `FCs_RoR`
- `CM_ETD`
- `CM_BTD`
- `BTU_*`
- `CO2_*`

### 7.5 roast_idempotency_keys

用途：支持 Plus 客户端 POST 重放安全。

核心字段：

- `id uuid primary key`
- `org_id uuid not null`
- `user_id uuid not null`
- `idempotency_key text not null`
- `request_hash text not null`
- `response_body jsonb not null`
- `status_code integer not null`
- `created_at timestamptz not null default now()`

约束：

- unique `(org_id, user_id, idempotency_key)`

## 8. Payload 映射

Plus payload 到 `roast_records`：

- `roast_id` -> `roast_uuid`
- `date` -> `roasted_at`
- `label` -> `label`
- `machine` -> `machine`
- `setup` -> `setup`
- `batch_number` -> `batch_number`
- `batch_prefix` -> `batch_prefix`
- `batch_pos` -> `batch_pos`
- `amount` -> `amount_kg`
- `end_weight` -> `end_weight_kg`
- `defects_weight` -> `defects_weight_kg`
- `whole_color` -> `whole_color`
- `ground_color` -> `ground_color`
- `color_system` -> `color_system`
- `moisture` -> `moisture`
- `notes` -> `notes`
- `cupping_notes` -> `cupping_notes`
- `cupping_score` -> `cupping_score`
- `modified_at` -> `modified_at`

`tm_profile` 到 `roast_records`：

- `roastUUID` -> `roast_uuid`
- `title` -> `label`
- `beans` -> `beans`
- `operator` -> `operator`
- `roastertype` -> `machine`
- `mode` -> `temperature_unit`
- `roastepoch` -> `roasted_at`
- `roastbatchnr` -> `batch_number`
- `roastbatchprefix` -> `batch_prefix`
- `roastbatchpos` -> `batch_pos`
- `computed.weight_loss` -> `weight_loss_pct`

`tm_profile` 到 `roast_curve_points`：

- `timex[i] + temp2[i]` -> `BT`
- `timex[i] + temp1[i]` -> `ET`
- `extratimex[n][i] + extratemp1[n][i]` -> `extra_temp1:n`
- `extratimex[n][i] + extratemp2[n][i]` -> `extra_temp2:n`

`tm_profile` 到 `roast_events`：

- `timeindex[0]` -> `CHARGE`
- `timeindex[1]` -> `DRY`
- `timeindex[2]` -> `FCs`
- `timeindex[3]` -> `FCe`
- `timeindex[4]` -> `SCs`
- `timeindex[5]` -> `SCe`
- `timeindex[6]` -> `DROP`
- `timeindex[7]` -> `COOL`
- `specialevents*` -> custom events

`tm_profile.computed` 到 `roast_measures`：

- 逐项提取可数值化字段，保留单位和原始 key。

## 9. ArtisanZ 客户端设计

### 9.1 配置与品牌

修改 `src/plus/config.py`：

- `app_name` 从 `artisan.plus` 改为 `tm-artisanz` 或 `TM-ArtisanZ`。
- `api_base_url` 改为 Taster-Matrix endpoint。
- `web_base_url` 改为 Taster-Matrix 管理后台。
- `shop_base_url` 第一阶段可指向 Taster-Matrix 订阅/组织页面或不启用。
- keyring service 使用新 app name，避免读取/覆盖原 artisan.plus 凭据。

替换用户可见文案：

- `Connected to artisan.plus` -> `Connected to TM-ArtisanZ`
- `Upload to artisan.plus` -> `Upload to TM-ArtisanZ`
- `Disconnect artisan.plus?` -> `Disconnect TM-ArtisanZ?`

第一阶段可以继续保留内部变量名 `plus_account`、`plus_sync_record_hash`，以降低合并 upstream 的成本。用户可见层和网络目标必须替换。

### 9.2 登录

保留现有 `plus.login` 的邮箱/密码弹窗，但文案改为 TM-ArtisanZ。

登录成功后：

- `aw.plus_account` 保存用户输入邮箱。
- `aw.plus_account_id` 保存 Taster-Matrix organization id。
- `aw.plus_user_id` 保存 Taster-Matrix user id。
- `aw.plus_readonly` 由服务端 readonly 决定。
- `plus.config.token` 保存 Taster-Matrix JWT。

### 9.3 DROP 后确认上传

当前 DROP 时会直接 `addRoast()`，第一阶段改为：

```text
DROP 事件完成
  -> 如果 TM-ArtisanZ 已启用
  -> 打开批次确认对话框
  -> 用户确认
  -> 构建 payload
  -> queue.addConfirmedRoast(payload)
```

确认对话框字段：

- 批次标题
- 批号/批次前缀/批次序号
- 生豆名称或自由文本
- 投豆重量
- 出豆重量
- 瑕疵重量
- 烘焙机
- 操作员
- 全豆色值
- 粉色值
- 色值体系
- 熟豆水分
- 烘焙备注
- 杯测备注

按钮：

- `上传`
- `稍后上传`
- `取消`

行为：

- 上传：先保存对话框字段到当前 profile，再排队上传。
- 稍后上传：保存 profile，不上传，状态显示未同步。
- 取消：关闭对话框，不上传。

### 9.4 上传 payload 扩展

新增封装函数，例如：

```python
def buildConfirmedRoastRecord() -> dict[str, Any]:
    record = plus.roast.getRoast()
    record["tm_profile"] = tm_profile.serialize(config.app_window)
    return record


def addConfirmedRoast() -> None:
    record = buildConfirmedRoastRecord()
    plus.queue.addFullRoastRecord(record, unsynced=True)
```

更稳妥的做法是新增 `plus/confirmed_upload.py`，让确认流程与原 `queue.py` 保持低耦合。

注意现有 `plus.queue.addRoast(roast_record)` 在传入 `roast_record` 时会调用 `sync.diffCachedSyncRecord()`，适合已同步后的属性更新，但首次确认上传必须保留 `date`、`amount`、`roast_id`、`tm_profile` 等完整字段。因此建议新增 `queue.addFullRoastRecord()` 或 `confirmed_upload.queueConfirmedRoast()`，复用 `queue_roast_item()`、`sync.suppress_zero_values()` 和现有 worker，但绕过首次上传的 diff。已确认同步后的保存/编辑，继续走原 Plus diff update。

注意：

- `tm_profile` 会比较大，但 `connection.py` 已支持 gzip POST。
- `tm_profile` 不参与 Plus sync diff 回写，只用于 Taster-Matrix 解析完整曲线。
- 后续保存/编辑时，如果该 roast 已确认同步，可以继续走原 `updateSyncRecordHashAndSync()` 的 diff update。

### 9.5 拦截上传触发点

第一阶段需要处理：

- DROP 自动上传入口：`src/artisanlib/canvas.py` 中两处 `addRoast()`。
- Roast Properties 保存时录制中上传入口：`src/artisanlib/roast_properties.py`。
- 保存/自动保存后的 `updateSyncRecordHashAndSync()`：未确认上传前不应把更新发往服务器。

建议添加本地状态：

- `qmc.tm_artisanz_upload_confirmed: bool`
- 或写入 profile 的 `tm_artisanz_upload_confirmed`

规则：

- 未确认时，不产生服务器写入。
- 确认上传成功后，将本地 sync cache 标记为已同步。
- 已同步 roast 的后续属性更新可以走原 Plus diff update。

## 10. 同步与冲突策略

第一阶段沿用 Plus 的简单策略：

- 主冲突字段：`modified_at`
- 比较粒度：毫秒 epoch
- 客户端更新较新：服务端接受 upsert
- 服务端更新较新：`GET /aroast/{uuid}` 返回 sync record
- 客户端收到更新后只回写 Roast Properties 安全字段，不自动重写完整曲线

服务端规则：

- `POST /aroast` 如果 incoming `modified_at` 大于等于当前记录，更新。
- incoming 更旧时，仍可返回 `200`，但不覆盖较新的服务端记录。
- 仅在不可恢复的数据错误时返回 `409`，因为 Artisan Plus queue 遇到 409 会丢弃任务。

## 11. 错误处理

客户端期望：

- `401`：触发 re-auth。
- `409`：任务被丢弃，不重试。
- `5xx` 或网络错误：outbox 保留并重试。
- `204`：无内容，视为成功或无需更新。

后端策略：

- 鉴权失败返回 `401`。
- 权限不足返回 `403`。
- payload 缺少 `roast_id` 返回 `400`。
- schema 对未知字段宽容，未知字段写入 `raw_plus_payload`。
- PostgreSQL 暂不可用返回 `503`。
- 默认不返回 `409`。

## 12. 安全与隐私

必须遵守：

- 不记录明文密码。
- 不在日志中记录完整 token。
- `raw_profile` 可能包含操作员、备注、批次信息，属于业务敏感数据。
- 组织权限通过 `tenant.org_members` 判断。
- `viewer` 不允许上传，映射为 `readonly: true`。
- Idempotency key 与 request hash 不应包含明文 password。

建议：

- `/api/tm-artisanz/v1/accounts/users/authenticate` 单独增加登录速率限制。
- `/aroast` 记录 user/org/roast_uuid/request_id，但不记录完整 raw body。
- 对 `tm_profile` 设置最大 body 限制，防止异常 profile 撑爆请求。

## 13. 测试计划

### 13.1 后端单元与集成测试

新增 node:test：

- 登录成功返回 Plus-compatible response。
- 账号不存在返回 404。
- 密码错误返回 401。
- viewer 用户登录后 readonly 为 true。
- `/acoffees` 返回空兼容结构。
- `/notifications` 返回空兼容结构。
- `/aschedule/lock` 幂等成功。
- `/aroast` 可 upsert 最小 payload。
- `/aroast` 可解析带 `tm_profile` 的完整 payload。
- 重放同一 `Idempotency-Key` 不重复写入。
- `GET /aroast/{uuid}` 对旧客户端时间返回 200。
- `GET /aroast/{uuid}` 对新客户端时间返回 204。
- 未授权 `/aroast` 返回 401。

### 13.2 ArtisanZ 客户端测试

聚焦命令：

```bash
cd src
python3 -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py plus/config.py plus/queue.py plus/roast.py
```

新增或更新测试：

- DROP 后不直接排队上传。
- 确认上传后 payload 包含 `tm_profile`。
- 稍后上传不写 outbox。
- 未登录时触发登录流程。
- 已同步后保存触发 diff update。

### 13.3 端到端验收

使用真实 ArtisanZ 构建验证：

1. 登录 TM-ArtisanZ。
2. 开始模拟或真实烘焙。
3. DROP 后出现确认对话框。
4. 确认上传。
5. 后端出现 roast record、curve points、events、measures。
6. 断网后上传留在 outbox。
7. 网络恢复后 outbox 自动清空。
8. 重启 ArtisanZ 后打开已同步 profile，不报错。

## 14. 里程碑计划

### M1：后端兼容骨架

目标：ArtisanZ 能登录 Taster-Matrix，stock/schedule/notifications 不报错。

任务：

1. 新增 `tm-artisanz` route/service/schema。
2. 实现 Plus-compatible 登录响应。
3. 实现 organization selection。
4. 实现 `/acoffees`、`/notifications`、`/aschedule/lock` stub。
5. 接入 `src/app.ts`。
6. 添加后端测试。
7. 运行 `cd vps-backend && npm run build && npm test`。

验收：

- ArtisanZ 指向新 endpoint 后能登录。
- 登录后不访问 `artisan.plus`。
- 空库存/空排程不导致 UI 崩溃。

### M2：RoastRecord 内核与上传同步

目标：烘焙记录能落库并支持 Plus sync fetch。

任务：

1. 新增 Drizzle schema 和 SQL migration。
2. 实现 `/aroast` upsert。
3. 实现 idempotency replay。
4. 实现 `tm_profile` parser。
5. 写入 `roast_records`、`roast_curve_points`、`roast_events`、`roast_measures`。
6. 实现 `GET /aroast/{uuid}`。
7. 添加 profile fixture 测试。

验收：

- 最小 Plus payload 可写入主表。
- 完整 `tm_profile` 可写入曲线、事件、指标。
- 同一 idempotency key 不重复写入。
- ArtisanZ 可以回读 sync record。

### M3：ArtisanZ 确认上传体验

目标：用户结束烘焙后确认批次信息，再上传。

任务：

1. 修改 `src/plus/config.py` endpoint、app name、web link。
2. 修改登录弹窗与状态提示文案。
3. 新增 TM-ArtisanZ 批次确认对话框。
4. 拦截 DROP 自动上传。
5. 确认后构建 Plus payload + `tm_profile`。
6. 调用 outbox queue。
7. 实现稍后上传状态。
8. 添加 Python 测试或最小可验证覆盖。

验收：

- DROP 后不直接上传。
- 确认后才上传。
- 上传失败时 outbox 保留。
- 成功后本地 sync 状态正确。

### M4：管理后台前置准备

目标：为后续 Taster-Matrix 前端 roast 页面打基础。

任务：

1. 新增内部查询 API 或 service，用于 roast list/detail。
2. 后端返回归一化后的 curve series，不让前端解析 raw profile。
3. 为曲线抽稀、事件时间线和指标卡预留 service 边界。

M4 不要求第一阶段立即实现页面。

## 15. 风险与缓解

风险：Plus payload 不含完整曲线。

缓解：使用 `tm_profile` 扩展字段，服务端同时保留 raw profile。

风险：ArtisanZ 上传触发点很多，容易漏掉自动上传。

缓解：第一阶段只允许“确认后首传”；未确认前所有 `addRoast()` 入口都必须被门控。

风险：Taster-Matrix 用户可能属于多个组织。

缓解：第一阶段按 `usage.current_organization_id` 或第一个 accepted org 选择，后续补组织选择 UI。

风险：Plus queue 遇到 409 会丢任务。

缓解：服务端默认不用 409；业务冲突用 200 + result 状态或 400 处理。

风险：raw profile 数据量较大。

缓解：启用 gzip、限制 body 大小、曲线点批量写入、raw profile hash 存储。

风险：upstream Artisan 后续更新 Plus 模块。

缓解：保留 `plus_*` 内部变量名，减少重命名范围；TM-ArtisanZ 行为通过小封装接入。

## 16. 实施顺序建议

严格顺序：

1. 后端 auth adapter。
2. 后端 stub endpoints。
3. ArtisanZ endpoint 切换，本地验证登录。
4. 后端 roast schema + `/aroast` 最小 upsert。
5. ArtisanZ 确认上传对话框，但先只发 Plus payload。
6. 增加 `tm_profile`。
7. 后端解析曲线、事件、指标。
8. 完成 E2E 验收。

原因：

- 先登录，才能验证所有后续端点。
- 先 stub stock/schedule，避免客户端登录后被无关功能阻塞。
- 先最小 roast upsert，再解析完整 profile，方便定位问题。
- 确认上传流程必须在真实上传前完成，避免“未确认写服务器”。

## 17. 完成定义

本设计完成后的第一阶段 Definition of Done：

1. ArtisanZ 登录 TM-ArtisanZ，不访问 `artisan.plus`。
2. DROP 后出现确认上传流程。
3. 用户确认前服务器没有 roast 写入。
4. 用户确认后 roast 进入 outbox 并最终上传。
5. 后端保存主记录、曲线点、事件、指标、raw payload。
6. 断网和服务端 5xx 时 outbox 会重试。
7. 重复 POST 不产生重复 roast。
8. `GET /aroast/{uuid}` 支持 Plus sync 语义。
9. stock/schedule/notifications stub 不影响客户端使用。
10. 相关后端测试和客户端 focused checks 通过。

## 18. 后续扩展

第一阶段完成后，再规划：

- Taster-Matrix roast overview 页面。
- Roast detail 曲线图和事件时间线。
- Roast compare。
- Taster-Matrix 材料库到 Plus `/acoffees` 的映射。
- 排程任务到 ArtisanZ Scheduler 的映射。
- 多组织选择 UI。
- 机器、操作员、地点管理。
- RoastRecord 与 cupping record 的关联分析。
- 库存扣减和熟豆产出。
- AI 复盘：曲线、事件、杯测结果的差异解释。
