# Sisyphus Workspace Policy Model Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Phase 4 pure-model layer (`src/artisanlib/ui_workspaces.py`) with a tested, immutable **workspace policy** that future `main.py` integration can consume to decide which menus, toolbars, panels, and advanced controls are visible per workspace mode. This slice changes **no runtime UI behavior** — it only adds pure data and tests.

**Architecture:** Keep existing `WorkspaceMode`, `WorkspaceArea`, and `WorkspaceSpec` byte-for-byte compatible. Add a parallel frozen dataclass `WorkspacePolicy` and a `_WORKSPACE_POLICIES` lookup keyed by `WorkspaceMode`, exposed via `workspace_policy(mode)`. The policy describes **UI chrome visibility** (menus / toolbars / panels / advanced controls); the existing spec describes **logical task areas**. They are two views of the same workspace and are kept consistent by a regression test.

**Tech Stack:** Pure Python (stdlib only — `dataclasses`, `enum`), pytest, py_compile, ruff.

---

## Scope & Ownership

**In scope (edit):**

- `src/artisanlib/ui_workspaces.py` — add `WorkspacePolicy`, `_WORKSPACE_POLICIES`, `workspace_policy()`, update `__all__`.
- `src/test/unitary/artisanlib/test_ui_workspaces.py` — add policy tests; leave existing tests unchanged.
- `docs/superpowers/plans/2026-06-30-sisyphus-workspace-policy.md` (this file).
- `docs/superpowers/plans/2026-06-30-sisyphus-workspace-policy-SELF-REVIEW.md`.

**Out of scope (do NOT edit):**

- `src/artisanlib/main.py`, `src/artisanlib/canvas.py`, `src/artisanlib/sample_processing.py`, `src/artisanlib/plot_*`.
- `.codebase-memory/*`.
- Any unrelated file.

**Branch:** `codex/sisyphus-workspace-policy` (worktree of `ArtisanZ`). No commit; leave changes for review.

---

## Design

### Why a parallel policy (not embedded in `WorkspaceSpec`)?

- Keeps `WorkspaceSpec` construction unchanged → existing spec tests and any future `main.py` reads stay valid.
- Separation of concerns: spec = *which task areas are visible*; policy = *which chrome elements are visible*.
- Self-contained: future `main.py` integration calls `workspace_policy(mode)` and gets every chrome decision in one structure, without cross-referencing the spec.
- `compact_chrome` intentionally appears in both spec and policy (self-contained policy); a consistency test pins them equal.

### `WorkspacePolicy` fields

| Field | Type | Semantics |
|---|---|---|
| `mode` | `WorkspaceMode` | The mode this policy applies to. |
| `show_full_menus` | `bool` | Full menu bar visible (Production hides non-essential menus). |
| `show_full_toolbars` | `bool` | Full toolbar set visible (Production hides non-essential toolbars). |
| `show_side_panels` | `bool` | Side / dock panels visible. |
| `show_advanced_controls` | `bool` | Expert-only tools + advanced controls visible (the expert differentiator). |
| `show_analysis_tools` | `bool` | QC analysis surface / tools visible. |
| `show_device_setup_tools` | `bool` | Device setup surface / tools visible. |
| `compact_chrome` | `bool` | Compact chrome mode active (Production only). |

### Per-mode policy table

| Mode | menus | toolbars | panels | advanced | analysis | device_setup | compact |
|---|---|---|---|---|---|---|---|
| `ROAST_CONTROL` | T | T | T | **F** | F | F | F |
| `QC_ANALYSIS` | T | T | T | **F** | **T** | F | F |
| `DEVICE_SETUP` | T | T | T | **T** | F | **T** | F |
| `PRODUCTION` | **F** | **F** | **F** | **F** | F | F | **T** |
| `EXPERT` | T | T | T | **T** | **T** | **T** | F |

This satisfies the task's five policy requirements verbatim:

- Roast Control hides expert tools → `show_advanced_controls = False`.
- QC Analysis includes analysis surface but not expert-only tools → `show_analysis_tools = True`, `show_advanced_controls = False`.
- Device Setup exposes device setup plus advanced navigation → `show_device_setup_tools = True`, `show_advanced_controls = True`.
- Production uses compact chrome and no expert tools → `compact_chrome = True`, `show_advanced_controls = False`.
- Expert exposes all areas/tools → every `show_* = True`.

---

## Files

- **Modify:** `src/artisanlib/ui_workspaces.py`
  - Add `WorkspacePolicy` frozen dataclass.
  - Add `_WORKSPACE_POLICIES: dict[WorkspaceMode, WorkspacePolicy]`.
  - Add `workspace_policy(mode: WorkspaceMode) -> WorkspacePolicy`.
  - Extend `__all__` with `WorkspacePolicy` and `workspace_policy`.
- **Modify:** `src/test/unitary/artisanlib/test_ui_workspaces.py`
  - Add policy tests (immutability, all five modes, spec/policy consistency, exports).
  - Leave existing tests byte-for-byte unchanged.

## Task 1: TDD the policy model

- [ ] **Step 1: Write failing tests (RED)**

Append policy tests to `test_ui_workspaces.py`. Expected failure reason: `WorkspacePolicy` / `workspace_policy` do not exist yet (`AttributeError` on import-time access via `importlib`).

- [ ] **Step 2: Verify RED**

```bash
cd src
QT_QPA_PLATFORM=offscreen /Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
```

Expect: new policy tests fail (collection OK, assertions fail with `AttributeError`); existing six tests still pass.

- [ ] **Step 3: Implement (GREEN)**

Add `WorkspacePolicy`, `_WORKSPACE_POLICIES`, `workspace_policy()`, update `__all__`. No other production change.

- [ ] **Step 4: Verify GREEN**

Re-run the focused pytest command. Expect all tests pass.

## Task 2: Full verification

- [ ] **Step 1: Focused suite**

```bash
cd src
QT_QPA_PLATFORM=offscreen /Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m py_compile artisanlib/ui_workspaces.py
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m ruff check artisanlib/ui_workspaces.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

- [ ] **Step 2: Self-review**

Inspect own diff; write `2026-06-30-sisyphus-workspace-policy-SELF-REVIEW.md` with Critical / Important / Minor findings; fix all Critical and Important.

## Residual Risks (to flag in SELF-REVIEW)

- `compact_chrome` is duplicated across spec and policy — pinned by a consistency test, but future editors must update both.
- The policy is not yet consumed by `main.py`; it is inert data until a follow-up slice wires it into `ApplicationWindow.set_ui_mode()`.
- `show_advanced_controls` is broader than the spec's `show_advanced_navigation`; future integration must decide whether advanced navigation is a subset of advanced controls (expected: yes).
