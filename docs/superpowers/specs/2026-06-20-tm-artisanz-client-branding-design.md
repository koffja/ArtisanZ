# TM-ArtisanZ 客户端与品牌拆分规格

日期：2026-06-20  
更新：2026-06-21

项目：ArtisanZ

状态：设计已认可；Taster-Matrix 后端 adapter 首版已实现并部署，2026-06-21 gzip request 解压已在仓库实现并验证，等待后端下一次部署后在线上生效。ArtisanZ 客户端可开始 C1/C3 小阶段。

## 0. 当前后端状态

Taster-Matrix 后端已经提供第一阶段 Plus-compatible adapter；其中 gzip request 解压已在 Taster-Matrix 仓库通过测试，真实上传联调前需确认后端已部署最新版本：

```text
https://tastermatrix.com/api/tm-artisanz/v1
```

当前 endpoint：

- `POST /accounts/users/authenticate`
- `GET /acoffees`
- `GET /notifications`
- `POST /aroast`
- `GET /aroast/{roastUUID}`
- `POST /aschedule/lock`

对 ArtisanZ 客户端的关键含义：

- 登录返回 Taster-Matrix JWT，但外层 response 仍保持 Plus-compatible envelope。
- `/aroast` 在最新 Taster-Matrix 后端代码中支持普通 JSON 与 `Content-Encoding: gzip` JSON；可以保留现有 gzip POST 行为，但真实联调前需确认后端部署版本。
- 后端按 `Idempotency-Key` 去重；同 key 同 body 返回原响应，同 key 不同 body 返回错误且不写入。
- `viewer`/只读组织成员可登录，但 `POST /aroast` 会返回 403。
- 后端保存 `roast_id` 为 `roasting.roast_records.source_record_id`，客户端不需要知道内部表结构。

## 1. 目标

在 ArtisanZ 客户端复用原 `src/plus/` 的登录、outbox、重试、sync cache 能力，将同步目标改为 Taster-Matrix 后端 `/api/tm-artisanz/v1`，并新增 DROP 后确认上传流程。

同时将“可开源的通用功能”和“TM-ArtisanZ 专属品牌配置”隔离，方便未来公开 ArtisanZ 功能代码时，只释放通用能力，不释放 Taster-Matrix 专属品牌、域名、服务说明或商业配置。

## 2. 边界

ArtisanZ 负责：

- 登录入口和状态显示。
- endpoint、keyring service、web link 的客户端配置。
- DROP 后批次确认对话框。
- 首次确认上传的 full roast record 入队。
- 完整 Artisan profile 的 `tm_profile` 序列化。
- 未确认前阻止服务器写入。
- 已同步后的后续属性 diff update。

ArtisanZ 不负责：

- Taster-Matrix 账号系统实现。
- Taster-Matrix 组织权限和订阅判断。
- RoastRecord 数据库结构。
- Taster-Matrix 管理后台页面。
- 服务端幂等和冲突处理。

## 3. API 目标

客户端目标 API 前缀：

```text
https://tastermatrix.com/api/tm-artisanz/v1
```

第一阶段使用的 Plus-compatible endpoint：

- `POST /accounts/users/authenticate`
- `POST /aroast`
- `GET /aroast/{roastUUID}`
- `GET /acoffees`
- `POST /aschedule/lock`
- `GET /notifications`

客户端只依赖这些 HTTP contract，不依赖 Taster-Matrix 内部表结构。

## 4. 功能与品牌拆分原则

未来开源时希望释放：

- DROP 后确认上传功能。
- 完整 profile 序列化为 `tm_profile`。
- 可配置云同步 provider。
- 队列首传 full record、后续 diff update 的稳定逻辑。
- 测试和通用文档。

未来不希望随功能一起释放：

- Taster-Matrix 正式域名。
- TM-ArtisanZ 专属品牌文案。
- 商业服务说明、订阅链接、管理后台入口。
- 私有部署 endpoint。
- 私有 keyring service 名称。

因此客户端实现应避免把品牌字串散落在 UI 和业务逻辑中。

## 5. 建议配置结构

第一阶段仍可保留 `src/plus/` 包名，降低 upstream merge 成本。新增一个集中式 service identity 层，将品牌和 endpoint 收口。

建议新增：

- `src/plus/service_identity.py`
- `src/plus/confirmed_upload.py`
- `src/plus/tm_profile.py`

`service_identity.py` 职责：

- 提供 display name。
- 提供 API base URL。
- 提供 web base URL。
- 提供 shop/subscription URL。
- 提供 keyring service 名称。
- 提供用户可见文案所需的 service label。

公开代码中的默认配置应是中性默认值，例如：

```python
DEFAULT_SERVICE_ID = "custom-roast-sync"
DEFAULT_DISPLAY_NAME = "Custom Roast Sync"
DEFAULT_API_BASE_URL = ""
DEFAULT_WEB_BASE_URL = ""
DEFAULT_KEYRING_SERVICE = "custom-roast-sync"
```

TM-ArtisanZ 私有发行包通过 private overlay 或 build-time config 覆盖：

```python
SERVICE_ID = "tm-artisanz"
DISPLAY_NAME = "TM-ArtisanZ"
API_BASE_URL = "https://tastermatrix.com/api/tm-artisanz/v1"
WEB_BASE_URL = "https://tastermatrix.com"
KEYRING_SERVICE = "tm-artisanz"
```

实施时可选择其中一种覆盖方式：

1. 私有分支覆盖 `service_identity.py`。
2. 读取 `service_identity.local.json`，该文件不进入开源发布。
3. 打包脚本注入环境变量或生成配置文件。

推荐第一阶段使用“集中配置文件 + 私有分支覆盖”，因为改动少、可验证快。后续若要正式对外开源，再升级为 build-time config。

## 6. 保留与替换策略

保留内部变量名：

- `plus_account`
- `plus_account_id`
- `plus_user_id`
- `plus_readonly`
- `plus_sync_record_hash`
- `src/plus/*`

理由：减少和 upstream Artisan Plus 模块的冲突。

必须替换用户可见层：

- 登录窗口标题。
- 连接状态。
- 上传成功/失败提示。
- disconnect 提示。
- 菜单或 toolbar 文案。
- keyring service。
- API/web/shop URL。

替换方式：

- UI 文案调用 `service_identity.display_name()`。
- 网络 URL 调用 `service_identity.api_base_url()`。
- keyring 调用 `service_identity.keyring_service()`。
- 不在 UI 文件中硬编码 `TM-ArtisanZ`。

## 7. 登录设计

保留原 Plus 登录流程的邮箱/密码输入方式。

登录请求目标：

```http
POST /api/tm-artisanz/v1/accounts/users/authenticate
```

登录成功后：

- `plus.config.token` 保存 Taster-Matrix JWT。
- `aw.plus_account` 保存用户输入邮箱。
- `aw.plus_account_id` 保存 Taster-Matrix organization id。
- `aw.plus_user_id` 保存 Taster-Matrix user id。
- `aw.plus_readonly` 由服务端 readonly 决定。

readonly 用户：

- 可以登录。
- 可以查看同步状态。
- 不允许上传 roast。
- DROP 后不应弹出“上传”主动作，可提示当前账号只读。

## 8. DROP 后确认上传

目标流程：

```text
DROP 事件完成
  -> TM-ArtisanZ provider 已启用
  -> 当前 roast 尚未确认上传
  -> 打开批次确认对话框
  -> 用户选择上传/稍后上传/取消
```

确认对话框字段：

- 批次标题
- 批号
- 批次前缀
- 批次序号
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

- 上传：保存对话框字段到当前 profile，构建 full roast record，加入 outbox。
- 稍后上传：保存 profile，不上传，状态标记为未同步。
- 取消：关闭对话框，不上传，不改变同步状态。

## 9. 上传门控

现有 Plus 上传触发点包括：

- DROP 自动上传入口：`src/artisanlib/canvas.py` 中的 `addRoast()`。
- Roast Properties 保存时录制中上传入口：`src/artisanlib/roast_properties.py`。
- 保存/自动保存后的 `updateSyncRecordHashAndSync()`。

第一阶段规则：

- 未确认上传前，任何入口都不能向服务器写入 roast。
- DROP 后首传必须由确认对话框触发。
- 首次确认上传必须保留 full record，不走 diff 删除字段。
- 已同步 roast 的后续属性更新可以走原 Plus diff update。

建议本地状态：

- `qmc.tm_artisanz_upload_confirmed: bool`
- 或 profile 字段 `tm_artisanz_upload_confirmed`

状态规则：

- `False`：未确认，不允许 server write。
- `True`：允许后续 diff sync。
- profile 另存为新文件时应重新评估 roast UUID 与确认状态。

## 10. Full record 与 diff update

现有 `plus.queue.addRoast(roast_record)` 在传入 `roast_record` 时会调用 `sync.diffCachedSyncRecord()`。这适合后续属性更新，但不适合首次确认上传，因为首传必须携带：

- `roast_id`
- `date`
- `amount`
- `modified_at`
- 完整 Plus roast fields
- `tm_profile`

建议新增封装：

```python
def buildConfirmedRoastRecord() -> dict[str, Any]:
    record = plus.roast.getRoast()
    record["tm_profile"] = tm_profile.serialize(config.app_window)
    return record


def addConfirmedRoast() -> None:
    record = buildConfirmedRoastRecord()
    plus.queue.addFullRoastRecord(record, unsynced=True)
```

`addFullRoastRecord()` 应复用：

- `queue_roast_item()`
- `sync.suppress_zero_values()`
- 现有 worker
- 现有 success 后 `sync.addSync()`

但它不应在首次上传前调用 `sync.diffCachedSyncRecord()`。

## 11. `tm_profile` 序列化

新增 `src/plus/tm_profile.py`。

职责：

- 从当前 `app_window` / `qmc` / profile 数据构建完整 JSON。
- 至少包含曲线数组、事件索引、额外设备曲线、computed 指标、机器和批次上下文。
- 输出必须 JSON serializable。
- 不改变 Artisan 原始 profile 保存格式。

第一阶段最少字段：

- `roastUUID`
- `title`
- `beans`
- `operator`
- `roastertype`
- `mode`
- `roastepoch`
- `roastbatchnr`
- `roastbatchprefix`
- `roastbatchpos`
- `timex`
- `temp1`
- `temp2`
- `extratimex`
- `extratemp1`
- `extratemp2`
- `timeindex`
- `specialevents`
- `specialeventstype`
- `specialeventsvalue`
- `specialeventsStrings`
- `computed`

注意：

- `tm_profile` 可能较大；Taster-Matrix 后端最新代码已经支持 `/aroast` gzip request 解压，因此可保留 `connection.py` 的 gzip POST 行为。真实上传联调前先确认 Taster-Matrix 后端已部署该版本。
- `tm_profile` 不参与客户端 sync diff 回写。
- 服务端解析失败不应导致客户端丢失 roast 主记录。

## 12. 品牌私有信息隔离

私有信息集中位置：

- service display name。
- endpoint host。
- web/admin URL。
- subscription/shop URL。
- keyring service。
- support/contact URL。

禁止：

- 在 `canvas.py`、`main.py`、`roast_properties.py` 等业务文件中硬编码专属品牌。
- 在测试 fixture 中写入真实生产域名。
- 在开源文档中写入私有后台入口。

允许：

- 通用文档使用 `Custom Roast Sync` 或 `TM-compatible provider`。
- 私有发行说明单独保存在不公开的 overlay 文档中。
- 开源功能保留 provider extension point。

建议未来开源时的目录策略：

```text
公开：
  src/plus/service_identity.py         # 中性默认值
  src/plus/confirmed_upload.py
  src/plus/tm_profile.py
  src/artisanlib/cloud_upload_dialog.py

私有：
  packaging/branding/tm-artisanz.json
  release-overlays/tm-artisanz/
  private docs/deployment/tm-artisanz.md
```

## 13. 测试计划

客户端 focused tests：

- `tm_profile.serialize()` 输出 JSON serializable。
- 确认上传构建 full record，包含 `date`、`amount`、`roast_id`、`tm_profile`。
- 未确认状态下 DROP 不直接调用 server write。
- 稍后上传只保存状态，不入队。
- readonly 用户不入队。
- 已同步后保存可走 diff update。

Focused verification：

```bash
cd /Users/chengzhe/Projects/ArtisanZ/src
python3 -m py_compile plus/config.py plus/queue.py plus/roast.py plus/service_identity.py plus/confirmed_upload.py plus/tm_profile.py artisanlib/canvas.py artisanlib/roast_properties.py
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

若新增独立测试，优先放在：

```text
src/test/unitary/plus/
```

## 14. 里程碑

### C1：品牌与 endpoint 收口

目标：所有网络目标和用户可见服务名从集中配置读取。

任务：

1. 新增 service identity 层。
2. `plus.config` 从 service identity 读取 endpoint 和 app name。
3. 登录、状态、上传消息改为读取 display name。
4. keyring service 改为新配置。

验收：

- 代码中不再散落专属 endpoint。
- 切换 provider 配置不需要改 UI 业务文件。

### C2：确认上传对话框

目标：DROP 后用户确认批次信息。

任务：

1. 新增确认对话框。
2. 从现有 profile 预填字段。
3. 保存用户编辑回 profile。
4. 实现上传/稍后上传/取消三种行为。

验收：

- DROP 后不直接上传。
- 用户确认前服务器没有 roast 写入。

### C3：Full record outbox

目标：首次确认上传完整 roast + `tm_profile`。

任务：

1. 新增 `tm_profile.py`。
2. 新增 `confirmed_upload.py`。
3. 新增 full record queue 方法或等价封装。
4. 接入 DROP 和 Roast Properties 入口门控。

验收：

- 首传 payload 包含完整字段。
- 首传不被 diff 删除。
- 断网后 outbox 保留。

### C4：后续同步与 polish

目标：已同步 roast 后续编辑可继续 sync，文案和状态完整。

任务：

1. 已同步后的保存/自动保存走 diff update。
2. 状态图标和提示适配新 display name。
3. readonly、401 re-auth、5xx retry 行为验证。

验收：

- 已同步 profile 打开、保存、重启后状态正常。
- 网络错误不会丢任务。

## 15. 完成定义

客户端第一阶段完成时必须满足：

1. ArtisanZ 不访问 `artisan.plus`。
2. API 目标为 `/api/tm-artisanz/v1`。
3. 登录使用 Taster-Matrix 账号。
4. DROP 后出现确认上传流程。
5. 用户确认前不会写服务器。
6. 首次确认上传包含 full record 与 `tm_profile`。
7. 后续编辑可继续 sync。
8. 专属品牌信息集中在 service identity 或私有 overlay。
9. 未来开源时可释放通用功能而不释放私有品牌配置。

## 16. 交给 ArtisanZ 负责 AI 的执行指令

建议下一个小阶段名称：

```text
C1/C3 TM-ArtisanZ provider foundation
```

执行前必须阅读：

- `/Users/chengzhe/Projects/ArtisanZ/AGENTS.md`
- `/Users/chengzhe/Projects/ArtisanZ/docs/superpowers/specs/2026-06-20-tm-artisanz-client-branding-design.md`
- `/Users/chengzhe/Projects/Taster-Matrix/docs/integrations/tm-artisanz/backend-spec.md`
- `/Users/chengzhe/Projects/ArtisanZ/ARTISAN_PLUS_INTEGRATION_SPEC.md`
- `/Users/chengzhe/Projects/ArtisanZ/src/plus/config.py`
- `/Users/chengzhe/Projects/ArtisanZ/src/plus/connection.py`
- `/Users/chengzhe/Projects/ArtisanZ/src/plus/queue.py`
- `/Users/chengzhe/Projects/ArtisanZ/src/plus/roast.py`
- `/Users/chengzhe/Projects/ArtisanZ/src/plus/sync.py`
- `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/canvas.py`
- `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`

推荐首批任务：

1. 新增 `src/plus/service_identity.py`，把 display name、API base URL、web URL、keyring service 收口。
2. 修改 `src/plus/config.py`，让 `app_name`、`api_base_url`、`web_base_url`、`shop_base_url` 和 endpoint URLs 从 `service_identity.py` 派生。
3. 修改 `src/plus/connection.py`，keyring service 使用 `service_identity.keyring_service()`，不要继续和 `artisan.plus` 共用凭证槽。
4. 新增 `src/plus/tm_profile.py`，提供 `serialize(app_window)`，输出 JSON serializable 的完整曲线/事件/profile 上下文。
5. 新增 `src/plus/confirmed_upload.py`，提供 `build_confirmed_roast_record()` 与 `add_confirmed_roast()`；首传必须包含 full record 与 `tm_profile`。
6. 在 `src/plus/queue.py` 新增 full record 入队路径，例如 `addFullRoastRecord(record, unsynced=True)`，不得对首传调用 `sync.diffCachedSyncRecord()`。
7. 暂时不要接入 DROP 自动弹窗；先用单元测试证明 confirmed upload helper 会构建正确 payload、入 outbox，并保留现有 gzip/Idempotency-Key 行为。

可直接下达给负责 AI 的提示词：

```text
你在 /Users/chengzhe/Projects/ArtisanZ 工作。先阅读 AGENTS.md，并确认当前分支是 ArtisanZ，保留所有未提交/未追踪用户文件，不要提交。

本阶段目标是实现 C1/C3 TM-ArtisanZ provider foundation：让 ArtisanZ 的 plus 同步层可以通过集中 service identity 指向 https://tastermatrix.com/api/tm-artisanz/v1，并新增 confirmed full roast upload 的基础能力，但暂不做完整 DROP 弹窗 UI。

Taster-Matrix 后端最新仓库代码已支持 `/aroast` 的 `Content-Encoding: gzip`；如果要做真实服务器上传联调，请先确认 Taster-Matrix 后端已经部署 2026-06-21 之后的版本。未确认前先用本地 focused tests 验证 payload、outbox、gzip/Idempotency-Key 行为。

必须先阅读：
- /Users/chengzhe/Projects/ArtisanZ/docs/superpowers/specs/2026-06-20-tm-artisanz-client-branding-design.md
- /Users/chengzhe/Projects/Taster-Matrix/docs/integrations/tm-artisanz/backend-spec.md
- /Users/chengzhe/Projects/ArtisanZ/ARTISAN_PLUS_INTEGRATION_SPEC.md
- src/plus/config.py
- src/plus/connection.py
- src/plus/queue.py
- src/plus/roast.py
- src/plus/sync.py
- src/artisanlib/canvas.py
- src/artisanlib/roast_properties.py

请按 TDD 做：
1. 为 service_identity/config URL 派生写测试或可执行断言。
2. 为 tm_profile.serialize() 写 JSON serializable 测试。
3. 为 confirmed_upload.build_confirmed_roast_record() 写测试，断言包含 roast_id/date/amount/modified_at/tm_profile。
4. 为 queue full record path 写测试，断言首传不会调用 sync.diffCachedSyncRecord()。

实现要求：
- 新增 src/plus/service_identity.py，集中 display name、API base URL、web URL、keyring service。
- 修改 src/plus/config.py 从 service_identity 派生 API endpoints。
- 修改 src/plus/connection.py 的 keyring service，不再使用 artisan.plus。
- 新增 src/plus/tm_profile.py，只序列化，不改变 .alog 格式。
- 新增 src/plus/confirmed_upload.py。
- 新增或等价实现 addFullRoastRecord(record, unsynced=True)，首传保留完整字段与 tm_profile。
- 不要把 TM-ArtisanZ 品牌字串散落到 canvas.py/main.py/roast_properties.py。
- 不要接入 DROP 自动上传 UI；本阶段只做 provider foundation 和 full record outbox 能力。

验证命令至少运行：
cd /Users/chengzhe/Projects/ArtisanZ/src
python3 -m py_compile plus/config.py plus/connection.py plus/queue.py plus/roast.py plus/service_identity.py plus/confirmed_upload.py plus/tm_profile.py
python3 -m pytest test/unitary/plus -q

如果 test/unitary/plus 尚不存在，请新增最小 focused tests。
```
