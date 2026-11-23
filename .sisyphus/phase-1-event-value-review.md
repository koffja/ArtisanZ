---
phase: 1-event-value
reviewed: 2026-07-23T13:28:37Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
findings:
  critical: 0
  warning: 1
  info: 1
  total: 2
status: issues_found
---

# Phase 1: Event Value Rendering Code Review

**Reviewed:** 2026-07-23T13:28:37Z  
**Depth:** deep  
**Files Reviewed:** 2  
**Status:** NEEDS PATCH — not PASS

## Summary

审查范围：PyQtGraph 事件值从竖向 stem 改为 `ScatterPlotItem` 单点。`pyqtgraph==0.14.0` API 调用可用。坐标映射、Z 值、overlay 清理、静态签名、导出、Qt GUI 调用路径无新崩溃或线程风险。Matplotlib 生产路径未被修改；同源快照和 parity 测试通过。

发现 1 个兼容性警告，需修补后才能 PASS；另有 1 个测试覆盖缺口。

验证：

- `test_plot_pyqtgraph_adapter.py`: 24 passed
- PyQtGraph export/parity/user-export/WebSocket smoke: 15 passed
- `test_plot_matplotlib_adapter.py`: 4 passed
- `ruff check`、`py_compile`、`git diff --check`: passed

## Warnings

### WR-01: Event opacity 被强制改写，破坏 Matplotlib/PyQtGraph 行为一致性

**File:** `src/artisanlib/plot_pyqtgraph_adapter.py:580-587`

**Issue:** `event_value.opacity` 被限制到 `0.25..0.85`。同时 pen alpha 使用 `opacity + 0.20`。因此输入 `opacity=0` 或 `0.1` 时，PyQtGraph 仍绘制可见点和边框；输入 `opacity=1.0` 时又被降低。Matplotlib 路径直接传 `alpha=event_value.opacity`（`src/artisanlib/plot_matplotlib_adapter.py:201-207`），同一 `RoastPlotSnapshot` 在两个 backend 的可见性不一致。当前 extractor 只产生 `0.34`/`0.55`，所以现有数据未触发；公共 snapshot API 仍允许其他值。

**Fix:** 保留 snapshot opacity 语义，只做 `[0, 1]` 安全裁剪；若需要更清晰边框，不能让 zero-opacity marker 重新出现。推荐：

```python
opacity = max(0.0, min(1.0, float(event_value.opacity)))
pen=pg.mkPen(
    color=_color_with_alpha(pg, event_value.color, opacity),
    width=1.0,
)
brush=pg.mkBrush(_color_with_alpha(pg, event_value.color, opacity))
```

并增加 `opacity=0.0`、`0.34`、`1.0` 的 backend parity 回归测试。

## Info

### IN-01: 新测试未验证核心坐标行为

**File:** `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py:893-914`

**Issue:** 测试只断言类型、symbol、尺寸、pen 宽度。未断言 Scatter 点实际位于 `(event_value.time, _event_value_y_position(...))`，也未断言 baseline 不再生成第二个 stem 点。未来实现即使 y 坐标错误，测试仍会通过。

**Fix:** 检查 `item.data` 中只有一个点，并验证当前 snapshot 下 `x == 4.5`、`y == 180.0`；补充轴内值、百分比值、超轴值和不同 `event_type` symbol。

## Explicit Verdict

NEEDS PATCH. 修复 WR-01 后，再补 IN-01 测试，阶段可标记 PASS。无 Critical、Security、Qt 线程安全问题。

---

_Reviewed: 2026-07-23T13:28:37Z_  
_Reviewer: Codex (gsd-code-reviewer)_  
_Depth: deep_
