---
phase: 1-6-1-12
reviewed: 2026-07-23T18:47:38Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/artisanlib/gui_theme.py
  - src/artisanlib/plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_gui_theme.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
findings:
  p0: 0
  p1: 1
  p2: 2
  p3: 2
  total: 5
status: issues_found
---

# Phase 1-6-1-12 Code Review Report

**Reviewed:** 2026-07-23T18:47:38Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## 结论

非 PASS。无 P0，但有 1 个 P1、2 个 P2。旧 Matplotlib 的 1/2/3/4 奇偶映射本身正确；录制 raw、CHARGE/DROP 遮罩、`-1`/NaN 数据转换、透明度和样式路径均已保留。

聚焦测试：`.venv/bin/python -m pytest ... -q`，`77 passed`。系统 Python 缺 pytest，未据此宣称测试通过。

## P1

### P1-01：extraDelta 轴选择未保留 `delta_ax is not None` 条件

**文件:** `src/artisanlib/plot_snapshot_extractor.py:308-311,340-343`

**触发条件:** `source.aw.extraDelta1b[index]` 或 `extraDelta2b[index]` 为真，但 `source.delta_ax is None`，同时渲染器仍配置了 `ror_plot`。

**问题:** 旧 Matplotlib 在 `delta_ax` 不存在时使用 `self.ax.transData`，曲线仍画在温度轴。新代码只看 `extraDelta*` 标志，快照把曲线标为 `y_axis='ror'`；PyQtGraph 会把它放到 RoR plot，导致轴和旧行为不一致。`build_roast_plot_snapshot()` 也可能产生 `ror_axis=None` 与 RoR 曲线并存的不一致状态。

**修复建议:** `extraDelta*` 为真且 `getattr(source, 'delta_ax', None) is not None` 时才返回 `True`；否则返回温度轴。增加 `delta_ax=None` 的回归测试，并通过 renderer 验证实际 plot。

## P2

### P2-01：全局控件最小宽度会覆盖已有固定宽度并破坏紧凑布局

**文件:** `src/artisanlib/gui_theme.py:199-203,212-215,223-226`

**触发条件:** 现代对话框中的 `QComboBox`、`QLineEdit` 或 `QAbstractSpinBox` 预先设置了小于 104/110 px 的 `maximumWidth`，例如单位、端口、时间和轴限制输入框。

**问题:** polish 先把最小宽度强制到 104/110 px；发现 `maximumWidth < minimumWidth` 后又把最大宽度改成最小宽度（SpinBox 再加 8）。这会取消调用方的固定宽度，多个控件叠加后扩大表单、挤压同一行的标签/按钮，或让窄对话框出现水平裁切/滚动。目标是给文本和右侧按钮留白，不应改变所有已有布局约束。

**修复建议:** 不上调调用方已设置的 `maximumWidth`；保留控件宽度，在 `QComboBox.view()` 上单独设置 popup 最小宽度。对 SpinBox/LineEdit 仅在没有显式固定最大宽度时扩大，或增加明确的 opt-in 属性。补充含固定宽度控件的真实 Qt 布局测试。

### P2-02：无穷选择值和整组 `None` 数据仍会让快照构建抛异常

**文件:** `src/artisanlib/plot_snapshot_extractor.py:289-301,327-343`

**触发条件:** 持久化/外部 source 给 `xtcurveidx` 或 `ytcurveidx` 传入 `float('inf')`；或选择有效 extra 曲线时，`extratimexB`、`temp*BX`、`stemp*BX` 或 `aw.extraDelta*` 整体为 `None`。

**问题:** `int(float('inf'))` 抛 `OverflowError`，当前 except 未捕获。`_sequence()` 对整体 `None` 调用 `list(None)` 也抛 `TypeError`，所以 `_background_extra_series()` 的局部空值保护不起作用。同步绘图路径可能回退，但导出/报告等直接调用 `build_roast_plot_snapshot()` 的路径会直接失败。

**修复建议:** 选择值转换捕获 `OverflowError`，并在转换前拒绝非有限或非正整数。对 extra series 和 delta flag 使用安全序列化 helper：属性缺失、`None`、不可迭代值统一返回空序列/无 RoR；增加 `None`、NaN、`-1`、越界和无穷选择测试。

## P3

### P3-01：extra curve 测试未覆盖 selection=3 和关键边界

**文件:** `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py:260-316`

**触发条件:** 后续改动破坏第二设备 `temp1BX` 映射，或改变录制/异常数据处理。

**问题:** 新测试覆盖 selection 1、2、4，但没有直接覆盖需求中明确的 selection=3（第二设备 `temp1BX`）；也没有覆盖 `0/-1/越界`、`flagon=True` raw 数据、`None/NaN/-1`、x/y 长度不一致和 `delta_ax=None`。现有两个样例不足以锁住全部旧语义。

**修复建议:** 参数化 1/2/3/4 映射；分别断言 raw/smoothed、CHARGE/DROP 遮罩、无效选择跳过、长度截断和两种 RoR 轴条件。

### P3-02：QSS 测试只数文本，不验证选择器和实际布局

**文件:** `src/test/unitary/artisanlib/test_gui_theme.py:88-92`

**触发条件:** `padding-right` 出现在无关 CSS 规则中，或 QSS 选择器写错但仍保留两个字符串。

**问题:** `stylesheet.count('padding-right: 32px;') >= 2` 不能证明 ComboBox、SpinBox、TimeEdit 的规则分别生效；新增宽度行为也没有验证固定宽度控件、弹出菜单宽度或窄对话框布局。

**修复建议:** 按控件选择器断言规则内容，并增加 Qt 控件测试：长中文项、空项、TimeEdit/DateEdit、预设 maximumWidth，以及布局在 polish 后的 sizeHint/geometry 不发生不可接受扩张。

---

_Reviewed: 2026-07-23T18:47:38Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
