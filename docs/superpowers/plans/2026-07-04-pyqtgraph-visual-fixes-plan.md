# PyQtGraph Visual Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 5 visual issues in the PyQtGraph renderer (phase band colors, BT gradient, background curve differentiation, phase summary labels) and add a CurvesDlg "Phase & Style" tab for user-adjustable controls.

**Architecture:** Change default values + opacity caps in extractor/adapter; add new QSettings keys (`bt_gradient_enabled`, `background_line_style`, `phase_summary_labels`, `phase_band_opacity`); add CurvesDlg tab 6 with color pickers, sliders, checkboxes bound to those settings. No new files, no new dependencies.

**Tech Stack:** Python 3.12+, PyQt6 6.11.0, pyqtgraph 0.14.0, existing QSettings persistence.

**Spec:** `docs/superpowers/specs/2026-07-04-pyqtgraph-visual-fixes-curves-tab-design.md`

## Global Constraints

- Branch: `ArtisanZ` (current HEAD `527409e06`)
- Python 3.12+; run all commands from `src/`
- PyQt6 pinned at `6.11.0`, pyqtgraph pinned at `0.14.0`
- All new settings persisted via QSettings (existing pattern)
- Match existing dataclass/dialog/QSS patterns
- Conventional commits (`feat(gui):`, `fix(gui):`)

---

## Task 1: Phase Band Default Colors + Opacity Cap (D1)

**Files:**
- Modify: `src/Ƀʀartisan/plot_snapshot_extractor.py` (lines 612-614 phase summary defaults; lines 1039-1044 gray-fallback)
- Modify: `src/Ƀʀartisan/plot_pyqtgraph_adapter.py` (lines 837-838 `_visible_phase_band_opacity`)
- Modify: `src/Ƀʀartisan/canvas.py` (lines 183-185 palette defaults)
- Test: `src/test/unitary/Ƀʀartisan/test_plot_snapshot_extractor.py`

- [ ] **Step 1: Write failing test** — add `test_phase_band_defaults_use_light_morandi_colors` asserting gray-fallback colors are `#F5F5F0` / `#F5F0E1` / `#F4F2EC` and phase summary defaults match.
- [ ] **Step 2: Run test, verify FAIL**
- [ ] **Step 3: Change gray-fallback** at `plot_snapshot_extractor.py:1044` from `('#DDE8E0', '#E7DEC9', '#D9E4EA')` to `('#F5F5F0', '#F5F0E1', '#F4F2EC')`.
- [ ] **Step 4: Change phase summary defaults** at `plot_snapshot_extractor.py:612-614` from `('#DDE8E0', '#E7DEC9', '#FFF6A8')` to `('#F5F5F0', '#F5F0E1', '#F4F2EC')`.
- [ ] **Step 5: Change canvas palette defaults** at `canvas.py:183-185` from `#F7F6F0/#EEF2F0/#F4F2EC` to `#F5F5F0/#F5F0E1/#F4F2EC`.
- [ ] **Step 6: Change opacity cap** at `plot_pyqtgraph_adapter.py:837-838` from `min(0.38, max(0.24, opacity * 1.5))` to `min(0.22, max(0.10, opacity * 1.2))`.
- [ ] **Step 7: Run test, verify PASS**
- [ ] **Step 8: py_compile + ruff**
- [ ] **Step 9: Commit** `fix(gui): use light Morandi phase band defaults + lower opacity cap`

---

## Task 2: BT Gradient Default Off (D2)

**Files:**
- Modify: `src/Ƀʀartisan/plot_pyqtgraph_adapter.py` (lines 366-388 `_default_pen_factory`)
- Modify: `src/Ƀʀartisan/plot_pyqtgraph_widget.py` or `plot_renderer_settings.py` — add `bt_gradient_enabled` setting (default `False`)
- Test: `src/test/unitary/Ƀʀartisan/test_plot_pyqtgraph_adapter.py`

- [ ] **Step 1: Write failing test** — `test_bt_gradient_disabled_by_default_returns_solid_pen` asserting that with `bt_gradient_enabled=False`, BT curve gets solid pen not gradient.
- [ ] **Step 2: Run test, verify FAIL**
- [ ] **Step 3: Add setting** — add `bt_gradient_enabled: bool = False` to renderer settings (read from QSettings with key `bt_gradient_enabled`).
- [ ] **Step 4: Gate the gradient** — in `_default_pen_factory`, wrap the gradient block in `if bt_gradient_enabled:` condition. Pass `bt_gradient_enabled` via `CurvePenFactory` callable signature or via snapshot metadata.
- [ ] **Step 5: Run test, verify PASS**
- [ ] **Step 6: py_compile + ruff**
- [ ] **Step 7: Commit** `feat(gui): default BT gradient pen off, add bt_gradient_enabled setting`

---

## Task 3: Background Curve Dashed + Lower Alpha (D3)

**Files:**
- Modify: `src/Ƀʀartisan/plot_snapshot_extractor.py` (`_background_curves` around lines 165-237)
- Test: `src/test/unitary/Ƀʀartisan/test_plot_snapshot_extractor.py`

- [ ] **Step 1: Write failing test** — `test_background_curves_default_to_dashed_style` asserting background curves have `line_style='--'` and `opacity <= 0.35`.
- [ ] **Step 2: Run test, verify FAIL**
- [ ] **Step 3: Change defaults** — in `_background_curve`, change `_line_style` default from `'-'` to `'--'`; change `_opacity` fallback from `0.45` to `0.35`.
- [ ] **Step 4: Run test, verify PASS**
- [ ] **Step 5: py_compile + ruff**
- [ ] **Step 6: Commit** `fix(gui): default background curves to dashed style + lower alpha`

---

## Task 4: Phase Summary Labels (D4)

**Files:**
- Modify: `src/Ƀʀartisan/plot_pyqtgraph_adapter.py` (`_default_phase_summary_item_factory` around lines 685-717)
- Test: `src/test/unitary/Ƀʀartisan/test_plot_pyqtgraph_adapter.py`

- [ ] **Step 1: Write failing test** — `test_phase_summary_renders_label_text` asserting the TextItem text includes `summary.label` (e.g. "Drying").
- [ ] **Step 2: Run test, verify FAIL**
- [ ] **Step 3: Update factory** — change label TextItem text from `f'{summary.duration_text}  {summary.percent_text}'` to `f'{summary.label}\n{summary.duration_text}  {summary.percent_text}'`. Adjust `y_text` offset upward by `span * 0.02` to fit the extra line.
- [ ] **Step 4: Run test, verify PASS**
- [ ] **Step 5: py_compile + ruff**
- [ ] **Step 6: Commit** `feat(gui): add phase name labels to progress bar text`

---

## Task 5: CurvesDlg "Phase & Style" Tab (D5)

**Files:**
- Modify: `src/Ƀʀartisan/curves.py` (add tab 6 UI + bindings + persistence)
- Modify: `src/Ƀʀartisan/plot_snapshot_extractor.py` (read `background_line_style`, `phase_summary_labels` settings)
- Modify: `src/Ƀʀartisan/plot_pyqtgraph_adapter.py` (read `bt_gradient_enabled`, `phase_summary_labels`, `phase_band_opacity`)
- Test: `src/test/unitary/Ƀʀartisan/test_curves.py`

- [ ] **Step 1: Write failing test** — `test_curves_dlg_has_phase_style_tab` asserting CurvesDlg has a 7th tab with the expected widgets (3 ColorButtons, 1 opacity slider, 1 BT gradient checkbox, 1 BG alpha slider, 1 BG style combo, 1 phase labels checkbox, 1 Restore Defaults button).
- [ ] **Step 2: Run test, verify FAIL**
- [ ] **Step 3: Add tab UI** — in `CurvesDlg.__init__`, add tab 6 "Phase & Style" with QFormLayout containing all 8 widgets. Bind each to the corresponding QSettings key.
- [ ] **Step 4: Add Restore Defaults** — button that resets all 8 settings to spec defaults.
- [ ] **Step 5: Wire settings reading** — in extractor/adapter, read the new QSettings keys with sensible defaults.
- [ ] **Step 6: Run test, verify PASS**
- [ ] **Step 7: py_compile + ruff**
- [ ] **Step 8: Commit** `feat(gui): add CurvesDlg Phase & Style tab for phase band and curve controls`

---

## Task 6: Visual Smoke Screenshots + Verify

**Files:** No code changes — verification only.

- [ ] **Step 1: Capture before/after screenshots** — load `profile1.alog` offscreen, capture with new defaults.
- [ ] **Step 2: Run focused test suite** — `pytest test/unitary/Ƀʀartisan/test_plot_snapshot_extractor.py test/unitary/Ƀʀartisan/test_plot_pyqtgraph_adapter.py test/unitary/Ƀʀartisan/test_curves.py -q`
- [ ] **Step 3: py_compile + ruff on all touched modules**
- [ ] **Step 4: Update roadmap** — append 2026-07-04 visual fixes note to Phase 1.6 section
- [ ] **Step 5: Commit + Push** — `git push origin ArtisanZ` (user pre-authorized)
