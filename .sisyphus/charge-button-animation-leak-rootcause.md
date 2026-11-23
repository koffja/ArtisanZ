# CHARGE 按钮动画泄漏 — 根因报告

**日期**: 2026-07-27
**症状**: 打开 artisan.py 烘焙一次后，停止采样，电脑整体持续卡顿；进程内存涨到
3.4G，系统 swap 占满（10.5G/11G），WindowServer CPU 飙高。

## 根因（已确认并修复）

`buttonCHARGE` 的脉冲动画（`AnimatedMajorEventPushButton`，`QPropertyAnimation`
+ `setLoopCount(-1)` 无限循环）在**停止录制时没有被停止**，以 60 FPS 持续运行。
每一帧调用 `setBackColor` → `setStyleSheet(...)`，Qt 重新 polish 整个样式表，
macOS 上等价于一次 CoreAnimation 事务提交（`CA::Transaction::commit → mach_msg`）。
这一个按钮就把主线程和 WindowServer 打爆。

## Bug 链条

| 步骤 | 函数 | 行为 |
|------|------|------|
| 开始录制 | `OnRecorder` (canvas.py:15958) | `buttonCHARGE.startAnimation()` 启动闪烁，等用户投豆 |
| 用户投豆 | `markCharge` (canvas.py:16264) | `buttonCHARGE.stopAnimation()` 正常停止 ✓ |
| **没投豆就停录制** | `OffRecorder` (canvas.py:15995) | **没有任何代码停动画** ❌ ← bug |
| 重置 | `reset` (canvas.py:9528) | 有 `stopAnimation()`，但 OffRecorder 不调用 reset |

`OffRecorder` 只停录制、不重置状态，所以 `reset` 里的 stopAnimation 救不了它。

## 证据

### 1. macOS sample（系统级）

主线程 50% 时间在 CoreAnimation flush：
```
QEventLoop::exec → NSApplication run → CFRunLoop
  → UC::DriverCore::continueProcessing (1596/3177 采样 = 50%)
    → CA::Transaction::flush_as_runloop_observer
      → CA::Render::Encoder::send_message → mach_msg (往 GPU 发消息)
```

### 2. perf pulse 日志（应用级，修复前）

停采样后动画持续 4 分钟直到退出：
```
15:48:37  MODE: OFF MONITOR / STOP RECORDING / OFF MONITOR DONE   ← 停采样
15:48:45  frame=63/s    ← 又回到 60 FPS
15:50:53  frame=61/s    ← 持续
15:52:34  frame=61/s    ← 停采样 4 分钟后仍在狂转
15:52:43  MODE: QUIT    ← 退出
```

## 修复

`canvas.py` `OffRecorder` 里，在 `self.flagstart = False` 之后加：

```python
self.flagstart = False
# Stop the CHARGE button blink animation if it is still running.
# OnRecorder() starts it (waiting for the user to CHARGE); markCharge()
# stops it on a real CHARGE. But if recording stops *before* CHARGE is
# pressed, nothing stopped it and the looping QPropertyAnimation kept
# re-polishing the stylesheet at ~60 FPS (driving a CoreAnimation flush
# storm that stalled the whole machine). stopAnimation() is a no-op if
# the animation is not running, so an unconditional call is safe here.
self.aw.buttonCHARGE.stopAnimation()
```

`stopAnimation()` 对未运行的动画是 no-op（Qt `QPropertyAnimation.stop()` 行为），
所以无条件调用安全，无需额外判断。

## 验证

端到端测试（offscreen）模拟"OnRecorder 启动 → 用户不 charge 直接 OffRecorder"：

| 阶段 | `active_animations` gauge | `animating` | 300ms 后 frame 增量 |
|------|--------------------------|-------------|---------------------|
| 初始 | (未上报) | False | — |
| OnRecorder 启动后 | 1 | True | — |
| OffRecorder 停止后（修复后）| 0 | False | **0**（修复前会是 ~18）|

单元测试：widgets/canvas/animation 相关 222 passed，0 failed。

## 新增的诊断设施

为了定位这个 bug，扩展了 `artisanlib/performance.py`：

1. **pulse 桶**：滚动 1 秒窗口的计数器速率（区分"累计 N 次"和"现在每秒 N 次"）
2. **gauge**：当前值（区别于累计 count），用于暴露"当前有几个动画在跑"这类状态
3. **周期日志线程**：每 5 秒把 top 高频计数器 + 非零 gauge 写到 `artisan.log`
4. **`AnimatedMajorEventPushButton` 的 WeakSet 追踪**：`_ANIMATED_EVENT_BUTTONS`
   记录所有实例，`_report_animated_event_button_gauge()` 上报当前活跃数

启用方式（默认零开销）：
```bash
ARTISANZ_GUI_PERF=1 .venv/bin/python artisan.py
grep " artisanlib.gui_perf" ~/Library/Application\ Support/artisan-scope/Artisan/artisan.log
```

## 教训

- **资源获取与释放必须成对**：`OnRecorder` 启动动画，停录制的 `OffRecorder` 必须对应停止。
  `reset()` 里的清理覆盖不了"只停录制不重置"的场景。
- **无限循环动画的代价在 macOS 上被放大**：每帧 `setStyleSheet` 触发 CoreAnimation
  flush，60 FPS × 每次 mach_msg = 打爆 WindowServer。这种动画应尽量避免，或用
  `QGraphicsColorizeEffect` 等更轻量的方式。
- **诊断时 gauge（当前值）比 counter（累计值）更有用**：counter 只能说"调过 N 次"，
  gauge 能说"现在有 1 个没停"。这次正是 `active_animations=1` 在停采样后不归零，
  直接暴露了泄漏。
