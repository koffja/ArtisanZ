# Sisyphus Workspace Policy — Self-Review

**Date:** 2026-06-30
**Scope:** `src/artisanlib/ui_workspaces.py`, `src/test/unitary/artisanlib/test_ui_workspaces.py`
**Diff size:** additive pure-model/test slice plus new documentation; no runtime integration files were modified.

## Verification Evidence

| Command | Result |
|---|---|
| `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q` | **15 passed**, 2 warnings (pre-existing yoctopuce deprecation, unrelated) |
| `.venv/bin/python -m py_compile artisanlib/ui_workspaces.py` | **PASS** (exit 0) |
| `.venv/bin/python -m ruff check artisanlib/ui_workspaces.py test/unitary/artisanlib/test_ui_workspaces.py` | **PASS** (no findings) |
| `git diff --check` | **PASS** (no whitespace errors) |

TDD cycle observed: RED verified first (9 new tests failed with `AttributeError: module has no attribute 'workspace_policy'`, 6 existing tests still passed), then GREEN after implementation.

## Findings

### Critical
None.

### Important
1. **Type-ignore suppression in the immutability test (resolved).** The first attempt used `policy.show_full_menus = False  # type: ignore[misc]` to attempt an illegal mutation. That suppressed a type check. Switching to `setattr(policy, 'show_full_menus', False)` removed the type-ignore but tripped ruff `[B010]` ("do not call `setattr` with a constant attribute value"). Final fix: assign through a local typed as `Any` and assert `dataclasses.FrozenInstanceError` is raised, which tests real runtime immutability without suppressions.
   - **Fix applied:** immutability test now uses `pytest.raises(dataclasses.FrozenInstanceError)` around assignment through an `Any` alias. No `# type: ignore`, no `# noqa`, no B010.

### Minor
1. **`compact_chrome` is duplicated across `WorkspaceSpec` and `WorkspacePolicy`.** This is a deliberate trade-off (self-contained policy vs. DRY) documented in the plan. Pinned by `test_workspace_policy_compact_chrome_aligns_with_spec`, which asserts equality for every mode. Future editors must update both structures; the test will catch drift.
2. **`import dataclasses` placement.** Initially inside the test function. Moved to module top for consistency with the existing module-level `import importlib`.
3. **No docstring on `WorkspacePolicy`.** Consistent with the existing `WorkspaceSpec` (also docstring-free); field names are self-documenting and the plan doc carries the semantic reference. No change needed.

## Residual Risks

- The policy data is not yet consumed by any runtime code path. If a future slice reads `show_advanced_controls` expecting it to mean *only* advanced navigation (a subset), semantics may diverge. Mitigation: the plan doc records that `show_advanced_controls` is the superset (expert-only tools + advanced nav), and `WorkspaceSpec.show_advanced_navigation` remains the narrow flag.
- `_WORKSPACE_POLICIES` is a second source of truth alongside `_WORKSPACE_SPECS`. The consistency test covers `compact_chrome` only (the single overlapping field). If more overlap is introduced later, expand the consistency test.

## Assessment

The slice satisfies every task requirement: pure-model layer only, existing model byte-for-byte compatible, frozen policy dataclass, all five per-mode policy requirements expressed and tested, TDD red-green cycle verified, all four verification gates green. The single Important finding (type-ignore) was fixed before completion.
