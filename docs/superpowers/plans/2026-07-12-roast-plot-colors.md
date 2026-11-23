# Roast Plot Colors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the active PyQtGraph roast plot use solid blue BT, readable background curves, and lighter/thinner phase summary bars.

**Architecture:** Keep the existing snapshot/extractor pipeline. Adjust defaults at the source and renderer boundaries, and make shadow enhancement whitelist actual curve items so overlay bars cannot inherit curve styling.

**Tech Stack:** Python 3.14, PyQt6, PyQtGraph, pytest, Ruff.

## Global Constraints

- Active plot renderer: `pyqtgraph-snapshot`.
- Preserve user-owned translation and `.sisyphus/` changes.
- Do not modify the Matplotlib compatibility renderer.
- Follow test-first development: each behavior gets a failing regression test before production code changes.

---

### Task 1: Lock color, opacity, and phase-bar behavior with tests

**Files:**
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_overlays.py`

- [ ] Add a test proving the default BT pen is solid blue rather than the Morandi gradient.
- [ ] Add a test proving background opacity defaults to `0.35` when the source does not provide a value.
- [ ] Add a test proving shadow enhancement only counts named curve items (`BT`, `ET`, `Delta BT`, `Delta ET`) and skips background/phase items.
- [ ] Add a test proving phase summary bars use width `10` and the revised opacity.
- [ ] Run the focused tests and confirm each new test fails for the current implementation.

### Task 2: Apply the minimal PyQtGraph styling changes

**Files:**
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/artisanlib/plot_snapshot_extractor.py`
- Modify: `src/artisanlib/canvas.py`
- Modify: `src/artisanlib/plot_pyqtgraph_overlays.py`

- [ ] Set the BT gradient default to disabled and retain the configured BT color for the solid pen.
- [ ] Raise the canvas background opacity default to `0.35`.
- [ ] Keep background curve extraction tied to each curve’s own color attribute and use the raised opacity fallback.
- [ ] Whitelist actual curve names in the generic shadow enhancer so phase bars and other overlay items receive no black shadow.
- [ ] Change phase summary bars to a `10`-pixel pen with a light, readable opacity.

### Task 3: Verify the change

**Files:**
- No additional files.

- [ ] Run the focused PyQtGraph, snapshot extractor, and widget tests.
- [ ] Run `py_compile` on changed Python files.
- [ ] Run Ruff on changed production and test files; report any pre-existing warnings separately.
- [ ] Inspect `git diff` and confirm translation files and `.sisyphus/` are not staged.
