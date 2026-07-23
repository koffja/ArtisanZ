---
phase: projection-parity
reviewed: 2026-07-23T20:42:11Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - src/artisanlib/plot_snapshot_extractor.py
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
findings:
  P0: 0
  P1: 0
  P2: 0
  P3: 0
  critical: 0
  warning: 0
  info: 0
  total: 0
status: PASS
---

# Projection Parity Review

**结论：PASS**

## 审查范围

审查四个目标文件。对照 `src/artisanlib/canvas.py:12584-12609` 旧 Matplotlib projection 实现。未修改源代码，未提交。

## 核对结果

- `src/artisanlib/plot_snapshot_extractor.py:420-436`：Delta BT/ET projection 仅在对应投影开关、`projectDeltaFlag`、Delta 开关及 `delta_ax is not None` 同时满足时导出。
- `src/artisanlib/plot_snapshot_extractor.py:402-413`：BT/ET projection 使用 temperature axis。
- `src/artisanlib/plot_snapshot_extractor.py:416-437`：Delta BT/ET projection 使用 `y_axis='ror'`。
- `src/artisanlib/plot_snapshot_extractor.py:454-465`：四类 projection 均使用 `line_style='-.'`、`line_width=8.0`、`opacity=0.3`。
- `src/artisanlib/plot_pyqtgraph_adapter.py:263-275`：projection item 使用 z-order `45`；Delta 曲线在存在 ror plot 时进入 ror plot。
- `src/artisanlib/plot_pyqtgraph_adapter.py:211-226`：不可见/缺失曲线仍执行 `setVisible(False)` 清理路径。
- `src/artisanlib/plot_pyqtgraph_adapter.py:250-261`、`464-465`：projection 排除 legend。
- 新增测试覆盖样式、axis routing、Delta axis gating、z-order、legend exclusion、不可见 projection。

## P0-P3

| 级别 | 数量 |
|---|---:|
| P0 | 0 |
| P1 | 0 |
| P2 | 0 |
| P3 | 0 |

## 验证

- `src/.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q`
  - `87 passed`
- `src/.venv/bin/python -m py_compile artisanlib/plot_snapshot_extractor.py artisanlib/plot_pyqtgraph_adapter.py`
  - 通过
- `git diff --check`
  - 通过
- 目标 diff 仅包含四个审查文件。
- 测试前后 `git status --short` 一致；既存无关脏文件未被触碰。新增本报告文件属于本次审查产物。

## 环境备注

系统 `python3` 为 Python 3.9.6，不满足项目 pytest 9.0 与 Python 3.12+ 要求；改用项目 `src/.venv`（Python 3.14.5、pytest 9.0.3）完成验证。

_Reviewed: 2026-07-23T20:42:11Z_
_Reviewer: Codex (gsd-code-reviewer)_
