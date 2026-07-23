# Phase 3.3 可执行边界审计

审计日期：2026-07-24
范围：`src/artisanlib/canvas.py` 的 `sample_processing()`、`src/artisanlib/sample_processing.py`、`ProcessedFrameRequest`/`ProcessedFrameWorker`、相关单元测试。
限制：只审计，不改代码，不提交。

## 结论

**PASS：具备继续拆分的安全边界，但不建议一次性把整个 `sample_processing()` 搬进 worker。**

当前 Phase 3.2 worker 接收的是已经完成输入滤波、平滑、RoR、PID process-value 计算后的结果。Phase 3.3 应扩展不可变输入快照和纯结果模型，逐步前移计算。GUI 继续负责状态提交、设备语义、事件、报警、PID 副作用和绘图。

## 当前代码边界

- `ProcessedFrameRequest` 位于 `src/artisanlib/processed_frame_worker.py:14`，当前只携带 `smoothed_et`、`smoothed_bt`、`pid_process_value`、`raw_delta_et`、`raw_delta_bt` 等派生值。
- `sample_processing()` 在 `src/artisanlib/canvas.py:5420-5607` 仍负责输入滤波、历史列表追加、平滑、PID process-value、RoR、RoR 平滑和 RoR 数学公式。
- worker 只执行 `build_live_processed_sample_frame()`；纯展示限幅、RoR 窗口、坐标轴延伸和自动事件候选位于 `src/artisanlib/sample_processing.py:972-1088`。
- worker 结果由 GUI 回调消费；回调负责列表追加、曲线、事件信号、PID SV、AUC、外部程序、报警和收尾。这个状态所有权应保持不变。

## 可安全纳入不可变 request 的计算

### 1. 平滑

可移入。纯函数链：

- `smoothing_weights_for_recent_readings()`：`sample_processing.py:98`
- `decay_weighted_average()`：`sample_processing.py:112`
- `smoothed_temperature_value()`：`sample_processing.py:153`

request 必须携带不可变的 connected ET/BT 时间和值快照、采样间隔、curve-filter 权重。worker 返回 `smoothed_et`、`smoothed_bt`。不能把 `self.temp1`、`self.ctemp1` 等 live list 引用传入。

### 2. RoR

可移入，但必须拆开“纯数值计算”和“GUI 数学表达式”。可移入：

- `simple_rate_of_rise_per_minute()`：`sample_processing.py:851`
- `rate_of_rise_per_minute()`：`sample_processing.py:891`
- `smoothed_rate_of_change_value()`：`sample_processing.py:838`
- `delta_smoothing_filter_size()`：`sample_processing.py:829`
- `displayed_ror_value()`、`ror_curve_window()`：`sample_processing.py:916-947`

request 必须携带不可变时间、已平滑温度历史、上一批未平滑 RoR 历史、`delta_samples`、polyfit 开关、采样间隔、delta smoothing 配置和 RoR 限制。`DeltaETfunction`、`DeltaBTfunction` 当前通过 `self.eval_math_expression()` 修改实时符号上下文，不能在本切片直接搬入 worker；先保留 GUI，worker 放在数学公式之前或之后必须明确等价顺序。

注意 ET、BT 不能共享一个可变 `self.decay_weights` 快取作为隐式输入。request 应为每个通道提供独立 tuple 权重，或由纯函数根据明确配置生成。

### 3. PID process-value 数值选择

可移入。纯函数：

- `pid_process_value_update_enabled()`：`sample_processing.py:434`
- `pid_process_value()`：`sample_processing.py:444`

request 只需携带 `pid_source`、平滑 ET/BT、extra-device 当前通道值的 immutable snapshot。`self.pid.update(process_value)` 必须留在 GUI；它是控制器状态副作用，不是纯计算。`externalPIDControl()` 的惰性读取和控制按钮状态也应由 GUI 先决定，再把布尔/枚举结果传入 request。

### 4. 前置输入滤波：仅纯决策部分可移入

可移入的纯函数：

- `input_filter_previous_values()`：`sample_processing.py:291`
- `input_filter_result()`：`sample_processing.py:301`
- `input_filter_backfill_updates()`：`sample_processing.py:265`
- `connected_curve_point()`：`sample_processing.py:253`

但整个 `tgraphcanvas.inputFilter()` 不能直接搬入。当前调用位于 `canvas.py:5420-5447`，会依据设备条件调用，并将 backfill 结果写入 `sample_temp*`、`sample_ctemp*`。安全设计：worker 只接收当前通道的历史快照和过滤配置，返回 `InputFilterResult`/backfill tuple；GUI 按序验证 generation 后应用 backfill，再 append 当前值。

extra-device 过滤不能与 ET/BT 一起盲搬。它还依赖 virtual-device 排除、`dummy_or_special_device()`、extra buffer 长度、数学表达式和各通道映射。先完成 ET/BT 单独切片，再为 extra-device 建立同构 request 和差分测试。

## 必须保留 GUI 的状态与副作用

- `qmc` 历史 list：`timex/temp/ctemp/tstemp/unfiltereddelta/delta`，以及 `on_*` 窗口 list。包括 append、backfill、截断、长度维护。
- `RTtemp*`、`RTextratemp*`、数学表达式执行、设备转换和 virtual/special-device 分支。
- `flagon`、`flagstart`、`timeindex`、`TPalarmtimeindex`、自动事件 index/flag、generation、pending continuation。
- `self.rateofchange*`、`unfiltereddelta*_pure` 等供 projection、分析、保存档案使用的 GUI-owned 状态。worker 只能返回值，不能写这些字段。
- `pid.update()`、`calcSV()`、`setSV()`、Fuji PID、硬件控制输出。
- CHARGE/TP/DRY/FCs/DROP 信号和 `mark*()`；报警锁、报警状态、报警动作和声音。
- AUC/BBP/cache、background playback、external program output、profile save、PyQtGraph/Matplotlib item、Qt signal、LCD 和消息栏。
- reset、停止采样、停止应用、worker shutdown 的 generation invalidation、锁归还和 stale-result 丢弃。

## 最小可交付切片

建议拆成两个小步，均使用现有 Phase 3.2 worker，不扩大 GUI 状态边界。

### Phase 3.3-A：温度平滑 + RoR 数值 + PID PV

1. 新增 frozen、深度 immutable 的温度/RoR/PID 输入快照；不要继续把 `ProcessedFrameRequest` 做成无结构的字段堆。
2. GUI 先完成设备转换、数学表达式、输入滤波、connected-history append；随后复制必要 tuple 快照并提交 worker。
3. worker 返回 `smoothed_et/bt`、raw/smoothed RoR、PID process-value 及必要的展示值。
4. GUI 只应用结果：更新历史/`self.rateofchange*`、调用 `pid.update()`、组建现有 `ProcessedSampleFrame`，再走既有事件/报警/渲染路径。
5. 先保留 Delta 数学表达式在 GUI，确保公式执行顺序和实时符号状态不变。

这是最小安全切片。收益明确，纯函数已有覆盖，回滚面小。

### Phase 3.3-B：ET/BT 输入滤波决策

1. worker 接收 ET/BT 原始历史 tuple、当前读数、时间和过滤配置。
2. worker 返回当前值、错误类型语义和 backfill tuple。
3. GUI generation 校验后先应用 backfill，再追加 connected/raw 历史；任何 stale/cancel 结果不得写 list。
4. extra-device 过滤另开后续子切片，不和 ET/BT 首次迁移绑定。

## 必须新增测试

- worker request 深度不可变：所有新增 nested list 都转 tuple；源 list 后续修改不能影响 request。
- 纯计算 golden/differential 测试：单点、短历史、`-1` dropout、`None`、polyfit fallback、delta smoothing warm-up、RoR limit、CHARGE 前后、DROP 后窗口。
- 输入滤波差分：duplicate、min/max violation、spike、两次/三次重复读数 backfill、ET/BT 独立历史、virtual extra-device 不过滤。
- PID PV：BT、ET、extra channel 1/2、source 缺失、`-1`、控制按钮关闭、external PID 缺失；确认 stale frame 不触发 `pid.update()`。
- 端到端连续序列：同步旧路径和 worker 路径逐样本比较 `tstemp`、RoR、PV、显示 RoR、曲线窗口、事件候选和最终 `timeindex`。
- 并发：reset/stop 后 stale result、worker error fallback、单飞队列、shutdown、profile lock ownership、generation/sequence mismatch。
- 采样完整性：确认 worker 忙时不会无意丢掉输入读数，或明确并测试“最新值合并”策略。
- 性能：1 Hz、5 Hz、10 Hz，短历史和长历史，记录 GUI p50/p95/p99、worker p50/p95/p99、pending/skip 数和内存增长；至少覆盖 WebSocket 与 simulator，之后再做硬件代表性测试。

## 主要风险

1. **采样丢失风险。** 当前 `sample_processing()` 在 `self._processed_frame_pending is not None` 时直接返回（`canvas.py:5206-5209`）。这会跳过本次输入的历史追加。Phase 3.3 计算变重后，丢样概率会上升。必须在计划中选择并验证：阻塞/有界队列、最新值合并，或允许丢样并记录契约；不能默默扩大单飞跳过。
2. **浅冻结风险。** `ProcessedFrameRequest` 是 frozen，但当前只在 `__post_init__` 转换 `sample_times`；新增 nested histories 必须深度 tuple 化。
3. **时序风险。** input backfill、connected append、平滑、RoR 和 Delta 数学公式有严格顺序。改变顺序会造成 RoR 延迟或数值漂移。
4. **共享快取风险。** `self.temp_decay_weights`、`self.decay_weights` 是可变 GUI 状态；不能作为 worker 隐式依赖，也不能由 worker 回写。
5. **控制副作用风险。** PID、报警、事件是“计算结果被接受”后才允许发生；任何 stale/error/fallback 路径都必须保证最多一次。
6. **设备覆盖风险。** extra-device、virtual-device、数学表达式、温标转换、特殊设备分支远比 ET/BT 复杂。首切片不要全量迁移。

## 明确建议

**PASS，建议进入 Phase 3.3-A。** 先迁移“平滑 + 纯 RoR 数值 + PID PV 选择”，保留输入滤波写回、数学表达式、设备分支和所有副作用在 GUI。完成并通过差分、连续采样完整性、并发和性能测试后，再进入 Phase 3.3-B 输入滤波。不要在本审计结论上直接提交代码。
