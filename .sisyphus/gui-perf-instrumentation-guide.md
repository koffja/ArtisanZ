# GUI 性能打点使用指南

用于诊断「打开 artisan.py 后电脑整体变慢、内存持续增长」这类 GUI 回归。
基于 2026-07-27 的现场诊断（`sample` 抓到主线程 50% 时间在
`CA::Transaction::commit → mach_msg`，进程 RSS 峰值 3.4G、系统 swap 10.5G/11G）。

## 快速使用

```bash
cd src
# 开启打点（默认每 5 秒把高频计数器写到 artisan.log，单次/秒超 100 次会 WARN）
ARTISANZ_GUI_PERF=1 python3 artisan.py

# 可选：调更激进的阈值（每秒 30 次就告警，便于抓轻微泄漏）
ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_PULSE_WARN=30 python3 artisan.py

# 可选：缩短周期日志间隔到 2 秒
ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_LOG_INTERVAL=2 python3 artisan.py
```

退出时会同时把完整累计计数导出到 `/tmp/artisanz-gui-perf.jsonl`（可用
`ARTISANZ_GUI_PERF_FILE=/path/to.jsonl` 覆盖）。

## 怎么看输出

### 1. 实时周期日志（在 artisan.log 里）

```
 artisanlib.gui_perf INFO: pulse snapshot (top trailing-1s rates): canvas.mpl.draw=240/s, canvas.redraw=60/s
```

含义：过去 1 秒内，matplotlib 的 `draw` 被调了 240 次，`redraw` 60 次。
**正常空闲时这行不应该出现**（所有 rate 归零会被跳过）。一旦空闲时仍反复打印，
那个计数器就是 CoreAnimation flush 的元凶。

### 2. 阈值告警（单条 WARN）

```
 artisanlib.gui_perf WARNING: gui-perf pulse: canvas.mpl.draw fired 240 times/sec ...
```

某个计数器在 1 秒窗口内首次突破阈值时打一次（避免刷屏）。出现即说明该路径在狂飙。

快速 grep：

```bash
grep " artisanlib.gui_perf" ~/Library/Application\ Support/artisan-scope/Artisan/artisan.log
```

## 已埋的计数器

| 计数器 | 含义 | 诊断意义 |
|--------|------|---------|
| `canvas.updategraphics.call` | 主重绘调度入口 | 采样时高频正常；空闲时持续涨=异常 |
| `canvas.updategraphics.worker_pending_skip` | 因 worker 忙跳过的重绘 | 偶发正常，持续涨=worker 跟不上 |
| `canvas.redraw` | matplotlib 全量重绘（含耗时） | 空闲时不应持续 |
| `canvas.lazyredraw.call` / `.lock_skip` | resize 触发的轻量重绘 | 拿不到锁跳过是正常 |
| `canvas.apply_live_plot_frame.call` | pyqtgraph 实时帧应用 | 采样时随采样率；停采样后应归零 |
| `canvas.updateLCDs.call` | LCD 数字刷新 | 每次重绘会刷多个 LCD |
| `pyqtgraph.update_live_frame.call` (+耗时) | pyqtgraph 快照渲染核心 | 耗时高=曲线/图层过多 |
| `canvas.mpl.draw` / `mpl.draw_idle` / `mpl.blit` | matplotlib 实际像素重绘 | **CoreAnimation flush 的直接来源** |
| `canvas.mpl_fig.draw` / ... | figure.canvas 上的同上 | 同上（matplotlib 内部触发路径） |
| `widgets.event_button.animation.start/stop` | CHARGE 按钮动画启停 | start 数 > stop 数 = 动画泄漏 |
| `widgets.event_button.animation.frame` | 动画每帧（驱动 setStyleSheet） | 持续涨=有按钮一直在动画 |

## 典型故障模式对照

- **空闲时 `canvas.mpl.draw` 持续 100+/s** → matplotlib 在被反复要求重绘，
  定位是哪个调用点（grep `fig.canvas.draw` 在 canvas.py 的分布）。
- **`widgets.event_button.animation.frame` 持续 ~60/s 但 stop 不足** →
  `buttonCHARGE` 动画启动后没停，`setStyleSheet` 每帧触发全 widget polish。
- **`canvas.redraw` 在采样停止后仍持续** → `redrawTimer` 或某个信号没断开。
- **`pyqtgraph.update_live_frame` 耗时 >50ms** → 曲线点数或 overlay 过多。

## 实现位置（改动文件）

- `src/artisanlib/performance.py` — pulse 桶、周期日志线程、`instrument_draw_calls`
- `src/artisanlib/canvas.py` — drawgraphics/redraw/lazyredraw/apply_live_plot_frame/updateLCDs 打点 + matplotlib draw 包装
- `src/artisanlib/plot_pyqtgraph_adapter.py` — `update_live_frame` 耗时 span
- `src/artisanlib/widgets.py` — EventPushButton 动画启停/帧计数
- `src/artisanlib/main.py` — `main()` 开头启动周期日志（perf-gated，默认 no-op）

所有打点在 `ARTISANZ_GUI_PERF` 未设置时**零开销**（recorder.enabled=False，
count/span 立即返回）。
