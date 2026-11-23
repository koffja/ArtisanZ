---
phase: analysis-overlay-final-review
reviewed: 2026-07-23T19:59:10Z
depth: deep
files_reviewed: 8
files_reviewed_list:
  - src/artisanlib/plot_snapshot.py
  - src/artisanlib/plot_snapshot_extractor.py
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/artisanlib/canvas.py
  - src/artisanlib/main.py
  - src/test/unitary/artisanlib/test_plot_snapshot.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
findings:
  critical: 0
  warning: 4
  info: 0
  total: 4
status: issues_found
---

# Analysis Overlay Final Review

**Reviewed:** 2026-07-23T19:59:10Z  
**Depth:** deep  
**Files Reviewed:** 8  
**Status:** ISSUES

## 结论

ISSUES。无 P0。存在 1 个 P1、3 个 P2。不能 PASS。

已确认：

- `analysisShowResults` 先写 interval、segment text、analysis text、`analysis_active`，再 `redraw`。
- 新增 qmc 状态已加入真实 `tgraphcanvas.__slots__`。
- `statisticsflags[0]`、`[1]`、`[6]` 独立映射。
- analysis result z=31；segment result z=30。
- 8 个 `axvspan` 等价项存在：4 个全高区间 + 4 个上下边缘条，mask z=20。
- PyQtGraph analysis/statistics item 会随 snapshot signature 重建并清理。

## P0

无。

## P1

### P1-01：清理 qmc 状态后仍从旧 Matplotlib annotation 恢复结果框

**File:** `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/plot_snapshot_extractor.py:1022-1025`  
**Related cleanup:** `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/canvas.py:9297-9304`; `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/main.py:14842-14849`; `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/main.py:26285-26291`

**Issue:** `_statistics_backgrounds()` 在 qmc 文本为空时回退到 `source.aw.analysisresultsanno` / `segmentresultsanno`。reset、profile load、delete background 只清空 qmc 新字段，没有清空 `ApplicationWindow` 上旧 annotation 引用。因此旧分析结果在这些操作后仍被 snapshot 提取，PyQtGraph 结果框重新出现。已用 `get_text()` 旧 annotation 复现。

**Fix:** 统一清理入口，同时清空 qmc 状态和 `ApplicationWindow.analysisresultsanno`、`ApplicationWindow.segmentresultsanno`，并移除旧 Matplotlib artists；或移除 snapshot 对旧 annotation 对象的回退，只把 qmc renderer-handoff 状态作为 PyQtGraph 数据源。

## P2

### P2-01：阶段事件索引只校验 DROP，非法 DRY/FC 索引会抛 `IndexError`

**File:** `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/plot_snapshot_extractor.py:901-914`

**Issue:** `_phase_event_times()` 只检查 `drop_index >= len(timex)`，没有检查 `charge_index`、`dry_index`、`first_crack_index`。坏 profile 或中间状态可让 `timex[dry_index]` / `timex[first_crack_index]` 越界；已用 `dry_index=99`、有效 DROP index 复现 `IndexError`。调用链会使 PyQtGraph snapshot 同步失败并触发 renderer fallback。该函数也未拒绝 `timex` 中的 `NaN/Inf`，`_time_ranges()` 可能继续生成非有限区间。

**Fix:** 对四个 index 做统一 `0 <= index < len(timex)` 校验；捕获 `IndexError`、`TypeError`、`ValueError`、`OverflowError`；转换后要求四个时间均 `math.isfinite()` 且严格递增，否则返回 `None`。

### P2-02：NaN alpha 被 clamp 成 1.0，非法输入会生成不透明 overlay

**File:** `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/plot_snapshot_extractor.py:1173-1180`

**Issue:** `_palette_opacity()` 对 `float('nan')` 直接执行 `max(0.0, min(1.0, numeric))`。Python 结果为 `1.0`，所以坏 alpha 会被当成完全不透明，而不是回退默认值。该值直接用于 analysis mask 和 statistics background snapshot。

**Fix:** clamp 前先检查 `math.isfinite(numeric)`；非有限值返回 `default`。同类 flags/overlay 数值入口保持一致的 finite policy。

### P2-03：`Development` 阶段标签在中文 i18n 下没有有效 Label 翻译

**File:** `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/plot_snapshot_extractor.py:856-878`; translation evidence: `/Users/chengzhe/Projects/ArtisanZ/src/translations/artisan_zh_CN.ts:3973-3974`

**Issue:** `_phase_label()` 使用 `QApplication.translate('Label', 'Development')`。`artisan_zh_CN.ts` 中对应条目位于 `Curves` context 且为 unfinished empty translation；`Label` context 没有有效 `Development` 翻译。因此真实中文界面 phase summary 会显示英文 `Development`。`Drying`/`Maillard` 有 Label 翻译，问题只在该阶段明显。

**Fix:** 为 `Label/Development` 增加各语言有效翻译并重新生成 `.qm`；或使用项目已有、已翻译的同义 UI source（如产品术语确认后使用 `Finishing`）。不要依赖其他 context 的 translation 条目。

## P3

无。

## Verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q`：`91 passed`。
- `.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/canvas.py artisanlib/main.py`：通过。
- `git diff --check`：通过。
- `.venv` ruff 检查另报 `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/main.py:28732` 未使用 `QFileDialog`；该行不在本轮 diff，未计入本报告 findings。
- 系统 `/usr/bin/python3` 为 Python 3.9.6，不满足项目 `requires-python >=3.12`；系统 pytest 8.4.2 也低于项目 pytest 9.0 要求。未用其结果判断本轮代码。

---

_Reviewed: 2026-07-23T19:59:10Z_  
_Reviewer: Codex (gsd-code-reviewer)_  
_Depth: deep_
