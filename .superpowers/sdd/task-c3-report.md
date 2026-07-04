# Task C3 Report

1. Status: DONE_WITH_CONCERNS
2. Commit hash: `04c985917`
3. Test results:
   - New factory tests: `2 passed` via `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -k charge_target_annotation_factory -v`
   - Full adapter suite: `16 passed, 1 failed` via `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q`
   - Compile/lint: `.venv/bin/python -m py_compile artisanlib/plot_pyqtgraph_adapter.py` passed; `.venv/bin/python -m ruff check artisanlib/plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py` passed.
   - LSP diagnostics: blocked because configured `basedpyright-langserver` is not installed.
4. `_apply_static_overlays` order preserved: `_apply_guides(snapshot)` remains before `_apply_charge_target_annotations(snapshot)`.
5. Concerns:
   - Full adapter suite has an existing unrelated failure: `test_default_pen_factory_keeps_bt_visibly_stronger_than_secondary_curves` expects `bt_pen.widthF() >= 2.2`, but current pyqtgraph gradient pen returns `2.0`. This task did not modify `_default_pen_factory` per constraint.
   - Existing untracked local directories remain: `.serena/memories/` and `.superpowers/`.
