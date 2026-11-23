---
phase: analysis-overlay-parity
reviewed: 2026-07-23T19:46:37Z
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
  warning: 3
  info: 1
  total: 4
priority:
  P0: 0
  P1: 3
  P2: 1
  P3: 0
status: issues_found
---

# Analysis Overlay Parity Review

**Reviewed:** 2026-07-23T19:46:37Z  
**Depth:** deep  
**Files Reviewed:** 8  
**Status:** issues_found

## Summary

发现 3 个 P1、1 个 P2。无 P0。

旧版 `analysisShowResults()` 的 8 个 `axvspan` 语义已核对：PyQtGraph 生成 4 个区间遮罩 + 4 个上下边缘带；坐标轴、遮罩透明度、`z=20`、无分析数据时不生成、snapshot signature 清理逻辑基本正确。mask 清理保存 `(plot, item)`，从原 plot 移除，正确。

Matplotlib adapter 未改，新增 snapshot 字段被忽略，兼容性保持。`tgraphcanvas.__slots__` 已包含新增 analysis 状态字段。

但新分析文本首帧不会进入 PyQtGraph snapshot；reset/profile load 后 analysis 状态可能残留；phase delta 可见性使用错误 flag。结果框 z-order 未显式保持旧版 analysis=31。

验证：用户已提供 `344 passed, 1 skipped`。本地 `src/.venv` scoped tests `90 passed`，py_compile、git diff --check 通过。scoped Ruff 唯一报错为已存在的 `src/artisanlib/main.py:28722` `QFileDialog` F401，非本轮回归。

## P0

无。

## P1

### P1-01: 新分析结果在首帧 PyQtGraph redraw 中缺失

**File:** `src/artisanlib/main.py:28360-28371`; renderer snapshot path: `src/artisanlib/canvas.py:6322-6333`

**触发条件:** 调用 `analysisShowResults()`，传入新的非空 `resultstr`。

**问题:** `analysisShowResults()` 先写区间，再在 `28366` 调用 `self.qmc.redraw()`；`qmc.analysisresultsstr = resultstr` 到 `28371` 才执行。redraw 期间 `build_roast_plot_snapshot()` 已读取 `statistics_backgrounds`，因此 PyQtGraph 首次 snapshot 只能看到旧结果文本；函数后续只更新 Matplotlib annotation，不再触发 PyQtGraph snapshot。首帧没有 analysis result background，直到下一次 redraw 才出现。

**修复:** 先解析空结果的 fallback，再一次性写入 `analysisresultsstr`、`segmentresultstr`、四个区间和 `analysis_active`，最后调用 `qmc.redraw()`。`analysis_active` 同时考虑 analysis/segment 文本。

### P1-02: reset/profile load 不清理新增 analysis 状态

**File:** `src/artisanlib/canvas.py:9297-9298`, `src/artisanlib/canvas.py:9370-9372`; state initialization: `src/artisanlib/canvas.py:2818-2826`

**触发条件:** 先完成一次分析，再执行 `reset()`，随后加载或开始有有效 CHARGE/DRY/FCs/DROP 的新 profile。

**问题:** reset 只清 `analysisresultsstr`。`curvefit_starttime`、`curvefit_endtime`、`analysis_starttime`、`analysis_endtime`、`segmentresultstr`、`analysis_active` 保留旧值。reset 之后会 redraw；当新 profile 的 phase 时间有效时，extractor 会把旧区间重新导出为 mask/guide，旧 segment result 也会重新导出为 background。当前空数据阶段暂时因 `_phase_event_times()` 返回空而不显示，不能消除状态污染。

**修复:** reset 清零四个区间、清空 `segmentresultstr`、置 `analysis_active=False`，并确保 profile load 的 redraw 使用清理后的 state。增加 reset → load profile → redraw 回归测试。

### P1-03: phase delta visibility 使用错误的 statistics flag

**File:** `src/artisanlib/plot_snapshot_extractor.py:797-813`; flag contract: `src/artisanlib/canvas.py:851-855`

**触发条件:** `statisticsflags[0]` 与 `statisticsflags[6]` 不同，例如 `[False, True, ..., True]` 或 `[True, True, ..., False]`。

**问题:** 项目注释规定 `[0]` 是 stat time、`[1]` 是 stat bar、`[6]` 是 stat delta temp。但 extractor 设置 `delta_visible=label_visible`，把 delta 错绑到 `[0]`。结果：关闭 phase time/label 时 delta 被错误隐藏；关闭 delta 时仍可能显示 delta。当前测试只验证 label，未覆盖 delta 独立 gating。

**修复:** 使用 `delta_visible=_statistics_flag(source, 6, True)`。补充两组相反 flag 组合测试，分别验证 bar、label、delta 独立可见性。

## P2

### P2-01: analysis/segment result box 未保持旧版显式 z-order

**File:** `src/artisanlib/plot_snapshot.py:115-123`, `src/artisanlib/plot_snapshot_extractor.py:1017-1034`, `src/artisanlib/plot_pyqtgraph_adapter.py:850-865`; old Matplotlib ordering: `src/artisanlib/main.py:28418-28425`, `src/artisanlib/main.py:28453-28460`

**触发条件:** segment result 与 analysis result 同时存在且文本框在图上重叠。

**问题:** 旧版 segment annotation 使用 zorder 30，analysis annotation 使用 zorder 31。新的 `StatisticsBackgroundSnapshot.z_value` 默认都是 30，extractor 创建两者时也都使用默认值。当前 segment 先 add、analysis 后 add，实际显示依赖 PyQtGraph 同 z item 的插入顺序，不是稳定的 parity contract；后续改变 overlay 构建顺序可能让 segment 覆盖 analysis。

**修复:** extractor 对 `kind='analysis'` 明确写 `z_value=31.0`，segment 保持 `30.0`；或 adapter 按 kind 映射默认 z。增加同时存在且重叠时检查 z 值的测试。

## P3

无。

## Passed Checks

- 旧版 8 个 analysis `axvspan`：PyQtGraph 4 个外侧 full-height spans + 4 个上下 2.5% edge bands，`z=20`。
- analysis guide 使用 vertical/data-x 坐标，interval extractor 拒绝 `NaN`/`Inf`、逆序区间；无有效 analysis interval 时不生成 mask/guide。
- result background 坐标使用 axes fraction 转 data coordinates；非法/边界 position、空文本、非法 axis span 会被跳过或回退。
- analysis mask cleanup 使用保存的 plot/item pair；statistics background 始终添加/移除 temperature plot，归属一致。
- `clearResults()` 已清四个区间、两个结果文本和 `analysis_active`，并触发 redraw；问题 P1-02 仅针对 reset/profile load 路径。
- `src/artisanlib/plot_matplotlib_adapter.py` 未被本轮改动；Matplotlib path 不消费新增 overlay fields。

---

_Reviewed: 2026-07-23T19:46:37Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: deep_
