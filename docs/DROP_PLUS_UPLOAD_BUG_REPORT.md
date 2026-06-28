# DROP 误触上传 artisan.plus Bug 报告

| 项 | 值 |
|---|---|
| **报告日期** | 2026-06-22 |
| **严重性** | High（数据污染 + 不可撤销） |
| **状态** | Fixed locally，待回归合并 |
| **影响版本** | ArtisanZ 当前 HEAD（基于 upstream v4.0.x） |
| **报告人** | 用户反馈 + 代码审查定位 |
| **指派** | Codex 处理 |

---

## TL;DR

在修复前，已连接 artisan.plus 的情况下，**用户误按 DROP（排豆）按钮时，即使立即取消后续弹出的"烘焙属性"对话框，烘焙记录也会被立即上传到 artisan.plus**，且无法通过 Undo DROP 撤回。本报告定位了三处独立的问题点，并给出三个候选修复方案。

**实施结论（2026-06-22）**：问题存在，根因是 `canvas.py` 的 DROP 本地状态变更路径提前调用 `plus.queue.addRoast()`。已采用长期方案 B：DROP 只更新本地状态，artisan.plus 上传、schedule completed 注册和 plus status 刷新统一延迟到烘焙属性对话框 OK/accept 后的 `queueConfirmedCompletedRoastUpload()` 路径。

---

## 术语澄清（重要）

用户原始反馈中提到的"Cotrix"在 ArtisanZ 代码库里**没有任何上传代码**。`src/artisanlib/cropster.py`（共 1360 行）只是 Cropster XLS 文件的**只读导入器**（`extractProfileCropsterXLS`），其中不包含任何网络上传或 sync 逻辑。

实际在 DROP 时触发上传的目标是 **artisan.plus**（Artisan 官方的云端服务），入口在 `src/plus/queue.py:469` 的 `addRoast()`。因此：

- 如果用户实际看到的是 artisan.plus 上的记录被创建，那是本报告描述的 bug
- 如果用户确实有 Cropster 账户收到记录，那是 artisan.plus 网页端的第三方桥接集成（在云端转发，不在本地代码里），本报告的修复仍然有效（因为修复点在本地发送侧）

---

## 问题 1：DROP 按钮按下即同步上传，无任何确认环节【主因】

### 现象

连上 artisan.plus 后，用户不小心点到 DROP（排豆）按钮：

- **不点属性对话框的"确定"** → 烘焙记录仍然被上传
- **立即关闭属性对话框** → 烘焙记录仍然被上传
- **立即按 Undo DROP** → 烘焙记录仍然被上传（详见问题 2）

### 触发链（完整调用栈）

| # | 文件:行号 | 代码 | 说明 |
|---|---|---|---|
| 1 | `src/artisanlib/main.py:3302` | `self.buttonDROP.clicked.connect(self.qmc.markDrop)` | DROP 按钮 clicked 信号直接绑定到 `markDrop`，**没有中间确认对话框** |
| 2 | `src/artisanlib/canvas.py:15375` | `def markDrop(self, noaction:bool = False)` | DROP 事件处理器，按下立即执行 |
| 3 | `canvas.py:15390` | `firstDROP = self.timeindex[6] == 0` | 标记"这是首次 DROP"（防 redo 重复上传，**但不防误按**） |
| 4 | `canvas.py:15416` | `elif not self.aw.buttonDROP.isFlat():` | 进入真正的 DROP 分支 |
| 5 | `canvas.py:15432` | `self.timeindex[6] = max(0,len(self.timex)-1)` | **标记 DROP 事件索引（按下即生效）** |
| 6 | `canvas.py:15442-15473` | 绘制 DROP 标注、`updateBackground()` | 同步副作用 |
| 7 | **`canvas.py:15490-15504`** | **`#PLUS if firstDROP and self.autoDROPenabled and self.aw.plus_account is not None: ... addRoast()`** | **★上传就在这里发生，按下即执行，无确认★** |
| 8 | `canvas.py:15570-15571` | `if self.roastpropertiesAutoOpenDropFlag: self.aw.openPropertiesSignal.emit()` | **上传之后**才弹出"烘焙属性"对话框（即用户感知的"关闭按钮"） |

### 根因

`markDrop()` 内 `#PLUS` 块（canvas.py:15490-15504）的三个 gating 条件里，**没有一个**是用户确认：

```python
# canvas.py:15490-15504
if firstDROP and self.autoDROPenabled and self.aw.plus_account is not None:
    if self.aw.schedule_window is not None:
        self.aw.schedule_window.register_completed_roast.emit()
    try:
        self.aw.updatePlusStatus()
    except Exception as e:
        _log.exception(e)
    try:
        addRoast()                    # ← 立即入队上传
    except Exception as e:
        _log.exception(e)
```

- `firstDROP` — 仅判断是否首次 DROP，不判断用户意图
- `self.autoDROPenabled` — 是"自动 DROP 启用"配置开关，**不是确认弹窗**
- `self.aw.plus_account is not None` — 仅判断是否登录 artisan.plus

### 影响

- **数据污染**：artisan.plus 账户里会堆积虚假的烘焙记录（误按、立刻 Undo 的记录全部被上传）
- **配额消耗**：如果 artisan.plus 按记录数计费或有限额，会白白消耗
- **需要手动清理**：用户必须登录 artisan.plus 网页端逐条删除，本地 Undo 无能为力
- **心理负担**：烘焙师不敢在连 plus 时操作，影响工作流

---

## 问题 2：Undo DROP 不能撤回已发出的上传

### 现象

用户误按 DROP 后立即再按一次 DROP（即 Undo），曲线上的 DROP 标记消失了，但 **artisan.plus 上已经创建的那条 roast 记录没有任何撤销机制**。

### 根因

`canvas.py:15391-15415` 是 Undo DROP 分支：

```python
# canvas.py:15391-15401
if self.aw.buttonDROP.isFlat() and self.timeindex[6] > 0:
    _log.debug('EVENT: undo DROP')
    self.aw.setTimerColorSignal.emit('timer')
    self.autoDropIdx = -1
    self.autoDROPenabled = False
    self.timeindex[6] = 0
    self.decBatchCounter()
    removed = True
    # ... 删除标注 ...
```

注释 `# on UNDO DROP we do not send the record to plus`（在 15390 行）说的只是"**undo 时不再发一次**"，但**第一次按 DROP 时已经入队的那条上传，本地没有任何 API 能把它从 `plus/queue.py` 的发送队列里撤回**，更不能从 artisan.plus 服务端删除。

`plus/queue.py:469` 的 `addRoast()` 一旦执行，记录就进了出站队列；如果网络在线，几秒内就发送到服务端，永久存在。

---

## 问题 3（已验证并修复）：`eventsaction` 拖动路径可能触发二次上传

`canvas.py:4281-4316` 是 `eventsaction` 函数里 `action.key[0] == 6`（DROP）的分支，处理**用户在曲线上拖动已有的 DROP 标记**的场景。该路径的注释同样写有 `# only on first setting the DROP event ... we upload to PLUS`，结构上和 `markDrop` 里的 `#PLUS` 块类似。

**验证结论（2026-06-22）**：

1. 此路径确实有独立 `addRoast()` 调用，条件同样不是用户确认。
2. 修复已删除该路径里的 early upload 逻辑，避免绕过属性对话框确认。
3. `plus/queue.py` 的去重只比较最近一次 queued item 是否为子集，不能作为误触上传的正确性保证，也不能撤回已发送记录。

```python
# canvas.py:4281-4316（疑似二次上传路径）
elif action.key[0] == 6:    # DROP
    # ... 类似 #PLUS 的逻辑 ...
    # 需要验证此处的 addRoast() 是否也有 gating
```

---

## 问题 4（附带）：用户对"关闭按钮"的误解

用户原话："为什么当按排豆时，上方还有一个关闭按钮需要点击才会正式结束"

**事实澄清**：修复前 DROP 的所有副作用（标记事件、画标注、上传 plus、增批量计数、关 PID 等）在 `markDrop()` 里**同步执行完毕**。修复后，DROP 仍会同步完成本地标记、画标注、增批量计数、关 PID 等本地动作，但 artisan.plus 上传已延迟到"烘焙属性"对话框 OK/accept 后。那个"上方的关闭按钮"是 DROP 之后**自动弹出**的"烘焙属性"对话框（由 `roastpropertiesAutoOpenDropFlag` 控制，canvas.py:15570-15571），用来填失重率、风味笔记等元数据。

这是 UX 设计选择（DROP 后正好要称重记笔记），不是逻辑必需。**这个不需要 Codex 修复**，只是要在用户文档/FAQ 里说明，避免误解。

---

## 修复方案

### 方案 A：最小侵入——在 `#PLUS` 块前加确认弹窗（推荐用于快速止血）

**改动位置**：`src/artisanlib/canvas.py:15490` 之前插入

**改动内容**：

```python
# canvas.py:15488 后,15490 前
#PLUS
if firstDROP and self.autoDROPenabled and self.aw.plus_account is not None:
    # 误按防护：仅连了 plus 时弹确认
    reply = QMessageBox.warning(
        self.aw,
        QApplication.translate('Message', 'Confirm Upload'),
        QApplication.translate('Message',
            'Drop recorded. Upload this roast to artisan.plus?'),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if reply != QMessageBox.StandardButton.Yes:
        # 用户选 No，跳过上传但保留 DROP 事件标记
        pass
    else:
        # ... 原有 schedule_window / updatePlusStatus / addRoast() 逻辑 ...
```

注意：同样改动**需要镜像到 `canvas.py:4314` 附近**（`eventsaction` 的 DROP 分支），防止二次路径绕过。

| 优点 | 缺点 |
|---|---|
| 改动最小，3-5 行代码 | 每次正常 DROP 也会弹窗，打断流畅工作流 |
| 不影响其他功能 | 用户可能习惯性点 Yes，起不到防护作用 |
| 不破坏现有 plus 用户的肌肉记忆 | — |

---

### 方案 B：改语义——上传延迟到属性对话框 accept 时（推荐用于彻底修复）

**核心思路**：把"上传触发"从 `markDrop()` 里移除，统一挪到烘焙属性对话框 OK/accept 后调用的 `queueConfirmedCompletedRoastUpload()` 里。该 helper 复用 `shouldQueueRoastPropertiesUpload()`，并把上传、schedule completed 注册、plus status 刷新绑定到同一个确认后的门禁。

**改动步骤**：

1. **`src/artisanlib/canvas.py:15490-15504`** — 删除整个 `#PLUS` 块（含 `addRoast()` 和 `register_completed_roast.emit()`）
2. **`src/artisanlib/canvas.py:4281-4316`** — 同样删除或注释掉 `eventsaction` 路径里的 `addRoast()`
3. **`src/artisanlib/roast_properties.py`** — 使用确认后的 helper 集中执行门禁和副作用：

   ```python
   queueConfirmedCompletedRoastUpload(
       self.aw,
       start_recording_on_exit=self.start_recording_on_exit,
   )
   ```

   helper 的 gate 覆盖：recording started、safe-save dirty state、CHARGE/DROP 已设置、plus 已登录、readonly plus 账号排除、simulator 排除、以及 `start_recording_on_exit` 排除。

4. **处理 Undo 场景**：不新增本地撤回 API。因为 DROP 本身不再入队，Undo DROP 在属性对话框 accept 前不会产生远端记录；这比尝试从 `plus.queue` 撤回未必还没发送的记录更可靠。

**副作用评估**：

- artisan.plus 用户的现有工作流会变（从"DROP 即上传"变成"DROP + 填属性 + OK 才上传"）
- 如果用户 DROP 后**直接关闭对话框**（点 X 而不是 OK/Cancel），需要确认 Qt 的默认行为是 reject 还是 accept——如果是 reject，则不上传，正合预期
- 需要更新用户文档，说明新的上传时机

| 优点 | 缺点 |
|---|---|
| 语义最正确——属性填完才上传 | 改动较大，影响 plus 模块和属性对话框 |
| Undo DROP 自然不会上传（属性对话框还没 accept） | 需要回归测试 plus 同步功能 |
| 与 `shouldQueueRoastPropertiesUpload` 的现有设计一致 | 可能影响 artisan.plus 的"实时同步"卖点 |

---

### 方案 C：增加"飞行模式"开关——让用户显式控制何时上传

**核心思路**：在主工具栏加一个"暂停 plus 同步"按钮（类似飞机模式），按下时所有 `addRoast()` 调用都被跳过；再次按下时恢复并批量上传所有积压记录。

**改动步骤**：

1. `src/plus/queue.py` — 增加 `paused: bool` 状态和 `pause()` / `resume()` 方法
2. `src/plus/queue.py:469` `addRoast()` 开头加 `if paused: enqueue_to_backlog(); return`
3. `src/artisanlib/main.py` — 加工具栏按钮，连接到 `plus.queue.pause()` / `resume()`
4. UI 提示：工具栏图标变色 + tooltip 显示积压记录数

| 优点 | 缺点 |
|---|---|
| 不改变现有 DROP 语义 | 用户必须记得开关，治标不治本 |
| 给烘焙师完全的掌控感 | 增加 UI 复杂度 |
| 可以作为"事后批量上传"的基础 | 与 Artisan 的"实时同步"理念冲突 |

---

## 推荐组合

| 严重度 | 推荐方案 | 理由 |
|---|---|---|
| **立即止血**（本周） | 已不采用方案 A | 弹窗止血仍把上传绑在错误生命周期上，会打断正常 DROP 流程 |
| **彻底修复**（当前实现） | 方案 B | 等属性对话框 accept 才上传，语义最正确 |
| **长期增强**（可选） | 方案 C | 给高级用户更多控制权，不影响普通流程 |

当前实现直接采用方案 B，避免先落地短期弹窗再迁移的二次改动。

---

## 验证清单（修复后必须通过）

### 功能验证

- [x] **正常 DROP 流程（自动化覆盖）**：连 plus → CHARGE → 烘焙 → DROP → 属性对话框 OK → artisan.plus upload queue 收到 1 次确认后的入队请求
- [x] **误按 DROP 立即 Undo（自动化覆盖）**：连 plus → 误按 DROP → 未 accept 属性对话框 → artisan.plus upload queue **不应**收到任何记录
- [x] **DROP 后取消属性对话框（自动化覆盖）**：连 plus → DROP → 属性对话框弹起 → 点 Cancel/X → artisan.plus 不应收到记录（方案 B 的预期行为）
- [ ] **未连 plus**：不登录 plus → DROP → 不应报错，曲线正常
- [x] **Readonly plus 账号（自动化覆盖）**：readonly plus 账号 → 属性对话框 OK → 不应上传，也不应注册 schedule completed 或刷新 plus status
- [x] **Simulator 模式（自动化覆盖）**：开 simulator → 属性对话框 OK → 不应上传（覆盖 `shouldQueueRoastPropertiesUpload` 的 `simulator` 参数）
- [x] **拖动 DROP 标记（静态回归覆盖）**：DROP 后拖动/设置标记位置 → `event_popup_action` 不再调用 `addRoast()`
- [ ] **Auto-DROP 触发**：配置 autoDROP → 达到条件自动 DROP → 应该正常上传（不能因为修复误按而把 autoDROP 也禁掉）

### 回归测试

- [x] 运行 `src/test/unitary/plus/test_confirmed_upload.py` 全绿（通过 focused suite 覆盖）
- [x] 运行 `src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py` 全绿
- [ ] 手动验证 ArtisanZ 现有 CHARGE 目标功能不受影响（`src/test/unitary/artisanlib/test_charge_manager.py` 全绿）

### 涉及的测试文件（Codex 可能需要更新）

- `src/test/unitary/plus/test_confirmed_upload.py`
- `src/test/unitary/plus/test_plus_util.py`
- `src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`

---

## 附录：相关文件与符号索引

### 核心改动点（按优先级）

| 文件 | 行号 | 符号 | 用途 |
|---|---|---|---|
| `src/artisanlib/canvas.py` | 15375 | `markDrop` | DROP 主处理函数 |
| `src/artisanlib/canvas.py` | 15490-15504 | 原 `#PLUS` 块 | **已删除的主 early upload 触发点** |
| `src/artisanlib/canvas.py` | 15391-15415 | Undo DROP 分支 | 不再需要撤回上传；DROP 未确认前不会入队 |
| `src/artisanlib/canvas.py` | 4281-4316 | `eventsaction` DROP 分支 | **已删除的二次 early upload 路径** |
| `src/artisanlib/canvas.py` | 15570-15571 | `roastpropertiesAutoOpenDropFlag` | 触发属性对话框弹出 |
| `src/artisanlib/main.py` | 3302 | `buttonDROP.clicked.connect` | 按钮→处理器的接线 |
| `src/artisanlib/roast_properties.py` | 81 | `shouldQueueRoastPropertiesUpload` | 方案 B 的集中 gate |
| `src/artisanlib/roast_properties.py` | 103 | `queueConfirmedCompletedRoastUpload` | 确认后的上传、schedule、status 副作用入口 |
| `src/plus/queue.py` | 469 | `addRoast` | 实际入队函数 |
| `src/plus/queue.py` | 382 | 去重注释 | 需要验证去重逻辑是否覆盖误按场景 |

### 设计/上下文文档

- `CHARGE_TARGET_SUMMARY.md` — ArtisanZ 自定义的"投豆目标"功能总结（与本 bug **无关**，是另一个 charge 相关功能）
- `charge_target_plan.md` — 投豆目标功能的设计文档
- `src/plus/queue.py` 顶部注释 — plus 队列的整体设计说明

### 不相关的 charge 功能（避免混淆）

ArtisanZ 仓库里有两个完全不同的 "charge"：

1. **CHARGE 事件按钮**（`buttonCHARGE` → `markCharge`）— 标记烘焙开始（投豆入锅），是 Artisan 原生功能，**与本 bug 无关**
2. **投豆目标功能**（`ChargeTargetManager` + `ChargeTempRorDlg`）— ArtisanZ 自定义的预测功能，用来在投豆前预测达到目标温度的时间，**也与本 bug 无关**

本报告描述的 bug **只涉及 DROP 事件按钮 + artisan.plus 上传**。

---

## 给 Codex 的执行指引

1. **先跑一遍现有的 plus 相关测试**，确认基线是绿的：
   ```bash
   cd src && python3 -m pytest test/unitary/plus/ -q
   ```

2. **实施方案 A 时**，注意 `QMessageBox` 的 import 在 canvas.py 里是否已存在（应该有，因为别处也用过）。如果改动超过 10 行，说明想多了。

3. **实施方案 B 时**，先把 `shouldQueueRoastPropertiesUpload` 的现有逻辑完整读一遍（`src/artisanlib/plus/util.py` 或 `roast_properties.py` 里），确认它能否正确区分"DROP 已设但用户 Cancel 属性对话框"和"正常完成"。如果不能，需要给它加一个 `dialog_accepted: bool` 参数。

4. **无论哪个方案**，都需要镜像改动到 `eventsaction` 的 DROP 分支（canvas.py:4281-4316），否则拖动 DROP 标记会绕过防护。

5. **不要动 `cropster.py`**——它只是导入器，和这个 bug 无关。也不要动 `charge_manager.py` / `charge_dialog.py`——那是另一个功能。

6. **commit 规范**：在 ArtisanZ 分支提交，commit message 用 `fix(plus): gate DROP upload behind user confirmation` 之类的 conventional commit 格式。

---

**报告结束。任何疑问请回头查阅原始调研记录：**
- `bg_ea20d36a`（Cropster/upload 触发链调研）
- `bg_46e6856e`（charge 状态机调研，用于排除干扰）
- `bg_07866a1e`（charge/drop 流程调研）
