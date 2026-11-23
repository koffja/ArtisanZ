---
phase: 1-6-1-12-followup
reviewed: 2026-07-23T18:58:52Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - src/artisanlib/gui_theme.py
  - src/artisanlib/axis.py
  - src/artisanlib/plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_gui_theme.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
findings:
  p0: 0
  p1: 0
  p2: 2
  p3: 2
  total: 4
status: issues_found
---

# Phase 1-6-1-12 修复后独立复审

**结论:** P0/P1 = 0。阻塞项 PASS。整体未 PASS：2 个 P2、2 个 P3。

已读六个审查文件、当前 diff、上一轮报告。未修改源代码，未提交。

验证：

- `83 passed`：三个目标测试文件。
- `ruff check`：通过。
- Qt 实际 QSS smoke：确认固定 `maximumWidth` 仍会被样式最小宽度突破。

## 上一轮问题关闭情况

- P1 extraDelta 仅在 `delta_ax` 存在时使用 RoR 轴：已关闭。`plot_snapshot_extractor.py:349-360` 有 `delta_ax is None` 防护；已有回归测试覆盖。
- P2 selection 的 `inf`/`NaN`/`None`/不可迭代值及整组空数据：已关闭对应崩溃路径。当前转换先做 `math.isfinite`，series/flag helper 对 `None` 和不可迭代值安全返回空结果。
- P2 固定宽度不被 GUI theme 覆盖：未完全关闭。Python 控件宽度逻辑已收敛，但全局 QSS 仍突破固定宽度，见 P2-01。
- P3 selection/掩码/长度边界测试：部分关闭；仍缺关键边界，见 P3-01。
- P3 QSS 选择器和实际布局测试：未关闭，见 P3-02。

## P0

无。

## P1

无。P0/P1 阻塞项 PASS。

## P2

### P2-01：QSS 最小宽度仍突破已有固定最大宽度

**文件:** `src/artisanlib/gui_theme.py:427-465,568-576`

**触发条件:** 任意现代对话框控件已有较小固定 `maximumWidth`，并且应用了 `modern_application_stylesheet()`。密集对话框中更容易触发，例如 `roast_properties` 的单位 ComboBox 固定为 60 px。

**问题:** `_polish_dialog_combo_box()`/`_polish_dialog_spin_box()` 不再直接改普通控件的 `maximumWidth`，但 QSS 仍设置 `QComboBox min-width: 72px`、SpinBox 类 `min-width: 48px`，密集对话框再设置 ComboBox `104px`、SpinBox `110px`。Qt 实际 style size hint 会把控件最小尺寸推过调用方的最大尺寸。

实际 smoke 结果：普通现代对话框中 `maximumWidth=60` 的 ComboBox 实际 `minimumWidth=114`；`maximumWidth=50` 的 SpinBox 实际 `minimumWidth=90`。密集对话框中 `maximumWidth=80` 的 ComboBox/SpinBox 分别达到 `146/152` px。会破坏紧凑行布局，扩大或挤压其它对话框；与上一轮“固定宽度不覆盖”目标不一致。

**修复:** 不要对所有现代控件用无条件 QSS `min-width`。将宽度规则限定到 `modernExpandValueControl="true"`，或在应用 stylesheet 后验证并保留 `minimumWidth <= maximumWidth`；ComboBox 长文本仅扩展 popup view。补充带真实 application stylesheet、`show()`、`processEvents()` 的 Qt 几何测试。

### P2-02：非整数 extra selection 被静默截断

**文件:** `src/artisanlib/plot_snapshot_extractor.py:289-294`

**触发条件:** 外部 source、旧配置或测试对象把 `xtcurveidx`/`ytcurveidx` 设成 `1.5`、`2.5` 等有限正浮点值。

**问题:** 代码先 `float()`，再直接 `int(selection_value)`。`1.5` 被当成 selection 1，`2.5` 被当成 selection 2，可能显示错误设备/奇偶通道；这不是安全的无效状态跳过。

**修复:** 转换前拒绝非整数：

```python
if (
    not math.isfinite(selection_value)
    or selection_value <= 0
    or not selection_value.is_integer()
):
    return None
selection = int(selection_value)
```

增加 `1.5`/`2.5` 回归测试，确认不产生曲线。

## P3

### P3-01：extra selection 边界回归仍不完整

**文件:** `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py:319-337`

**触发条件:** 后续改动破坏 selection 4、无效选择、录制 raw 数据、长度截断或 `-1`/NaN 掩码。

**问题:** 当前参数化只覆盖 `1/2/3` 的 smoothed 映射。未覆盖：`4` 的第二设备 `temp2BX`、`0`、负数、越界、`flagon=True` raw 分支、x/y 长度不一致、`-1`/NaN 值、delta flag 短数组和两种 delta 轴条件的完整组合。实现当前对多数情况有保护，但回归测试不足以证明 odd/even、bounds、length、mask、axis 语义持续正确。

**修复:** 参数化 `1/2/3/4`；添加 invalid/out-of-range skip、raw/smoothed、长度截断、`-1`/NaN、短 mask、`delta_ax=None`/存在的独立断言。同步验证生成曲线的 `y_axis` 和 renderer 目标 plot。

### P3-02：QSS 测试仍只数文本，未验证选择器和实际布局

**文件:** `src/test/unitary/artisanlib/test_gui_theme.py:88-91,283-307`

**触发条件:** `padding-right` 出现在其它规则，或 stylesheet 的 `min-width` 覆盖控件最大宽度时。

**问题:** `stylesheet.count('padding-right: 32px;') >= 2` 不能证明 ComboBox、SpinBox、TimeEdit、DateEdit 规则正确。固定宽度测试未设置真实 application stylesheet，也未检查 show 后实际 geometry；因此无法捕获 P2-01 的真实回归。

**修复:** 按具体 selector 断言 QSS；在 Qt 测试中设置 `modern_application_stylesheet()`，覆盖普通/密集对话框、ComboBox popup、固定 `maximumWidth`，调用 `show()`/`processEvents()` 后断言控件尺寸和布局边界。

---

_Reviewed: 2026-07-23T18:58:52Z_
_Reviewer: Codex (gsd-code-reviewer)_
_Depth: deep_
