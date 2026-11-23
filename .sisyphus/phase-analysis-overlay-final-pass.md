---
phase: analysis-overlay-final-pass
reviewed: 2026-07-23T20:17:13Z
depth: deep
files_reviewed: 10
files_reviewed_list:
  - src/artisanlib/plot_snapshot.py
  - src/artisanlib/plot_snapshot_extractor.py
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/artisanlib/canvas.py
  - src/artisanlib/main.py
  - src/test/unitary/artisanlib/test_plot_snapshot.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
  - src/translations/artisan_zh_CN.ts
  - src/translations/artisan_zh_CN.qm
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
conclusion: ISSUES
---

# Analysis Overlay Parity Final Pass

**Reviewed:** 2026-07-23T20:17:13Z  
**Depth:** deep  
**Conclusion:** ISSUES

## Summary

本轮指定修复已核对：

- PyQtGraph 结果文本只读 qmc renderer-handoff state；不再回退旧 Matplotlib annotation。
- `_phase_event_times()` 检查 charge/dry/FCs/drop 四索引边界、float 转换、有限性、严格递增。
- `_palette_opacity()` 对 NaN/Inf 回退默认值。
- `Label/Development` 为 `发展期`；Qt6 `QTranslator` 成功加载 `artisan_zh_CN.qm` 并返回该翻译。
- `analysisShowResults()` 在 redraw 前写入完整状态；reset、profile load、delete background、`clearResults()` 清理 qmc 状态；statisticsflags `[0]`、`[1]`、`[6]` 独立；analysis/segment z-order 为 31/30。
- 未修改源代码或无关用户脏文件。

发现 1 个用户可见逻辑问题，另有 2 个测试覆盖缺口。无 P0/P1。

## P0

无。

## P1

无。

## P2

### P2-01: `statssummary=False` 仍渲染 phase summaries

**File:** `src/artisanlib/plot_snapshot_extractor.py:771-816,819-826`

**Issue:** `_phase_summaries()` 没有调用已定义的 `_statistics_summary_enabled()`。因此真实 qmc 的 `statssummary=False` 仍会生成 3 个 phase summary；`sync_pyqtgraph_snapshot_from_canvas()` 和 live static overlay 会把它们交给 PyQtGraph renderer，显示应被 Statistics summary 开关关闭的 phase bar、label、delta。已用 fixture 设置 `statssummary=False` 复现：仍得到 `phase_summaries=3`。

**Fix:** 在 `_phase_summaries()` 入口返回空 tuple：

```python
if not _statistics_summary_enabled(source):
    return ()
```

增加 `statssummary=True/False` 的 extractor/renderer 回归测试。

## P3

### P3-01: 首帧与生命周期清理缺少集成回归测试

**File:** `src/artisanlib/main.py:28368-28381`; `src/artisanlib/canvas.py:9297-9304`; `src/artisanlib/main.py:14842-14849,26285-26291,28089-28103`

**Issue:** 当前新增测试覆盖 extractor、snapshot contract、adapter cleanup，但没有断言 `analysisShowResults()` 的 qmc 状态写入发生在 `redraw()` 之前，也没有覆盖 reset、profile load、delete background、`clearResults()` 后的 snapshot 为空。已有实现顺序经源码核对正确，但这些路径的回归仍可能只靠人工发现。

**Fix:** 用 spy/mock qmc 增加生命周期测试：redraw spy 读取到新 interval/text；各清理入口后构建 snapshot，断言 analysis masks、guides、statistics backgrounds 均为空。

### P3-02: 四索引及严格递增边界测试不完整

**File:** `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py:583-596`

**Issue:** 现有测试只覆盖 dry index 越界和一个 NaN 时间值，未分别覆盖 charge、FCs、DROP 越界，Inf、相等时间、逆序时间，以及 float 转换异常。实现已有对应防护，但测试不能锁定完整契约。

**Fix:** 参数化四个 event-index 位置和 `timex` 异常值，分别断言 `phase_summaries`、`time_ranges` 返回空 tuple 且不抛异常。

## Verification

- Focused overlay suite: `95 passed`。
- Shared `main.py`/`canvas.py`/renderer selection suite: `397 passed, 1 skipped`。
- `py_compile`: passed for all touched runtime modules。
- `git diff --check`: passed。
- Qt6 `QTranslator`: `artisan_zh_CN.qm` loaded successfully; `Label/Development` → `发展期`。
- Full suite blocked during collection by unrelated environment/repository issues: missing `pytest_asyncio` and missing `tools.peak_p1_proxy` modules (`6 errors`)。
- Scoped Ruff only reported pre-existing `src/artisanlib/main.py:28732` unused `QFileDialog`, outside this round's diff。
- `lrelease` executable was not present on PATH; `.qm` runtime validity verified, but generator command provenance could not be independently re-run.

---

_Reviewed: 2026-07-23T20:17:13Z_  
_Reviewer: Codex (gsd-code-reviewer)_  
_Depth: deep_
