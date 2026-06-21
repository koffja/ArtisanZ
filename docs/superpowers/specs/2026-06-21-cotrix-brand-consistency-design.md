# Cotrix Brand Consistency Design Spec

> **Type**: Implementation-ready design brief
> **Repo**: `/Users/chengzhe/Projects/ArtisanZ` (branch `ArtisanZ`)
> **Audience**: Implementation agents executing the fix
> **Predecessor audit**: see "Cotrix 品牌一致性审计报告" delivered 2026-06-21
> **Reading guide**: §1 problem statement, §2 design decisions, §3 implementation phases, §4 CI rule, §5 test plan, §6 risks, §7 acceptance

---

## 1. Problem Statement

ArtisanZ migrated from `artisan.plus` to `Cotrix` (Taster-Matrix) backend in commits `fd3221dc9` and `13b8c1a30`. The migration introduced a runtime brand-swap mechanism via `translatedServiceMessage()` but **only some call sites use it**. The audit identified:

- **8 unsafe call sites** that bypass the swap and show literal "artisan.plus" to users
- **2 duplicate `translatedServiceMessage()` implementations** that can drift
- **No CI guard** preventing future regressions

User-visible symptoms include the main window title showing "artisan.plus", toolbar tooltips showing "Disconnect artisan.plus", and Help dialog rows with the old brand.

## 2. Goals & Non-Goals

### Goals
1. **G1 — Brand consistency**: All user-facing GUI text shows `Cotrix` (not `artisan.plus`) at runtime, regardless of which code path renders it.
2. **G2 — Single source of truth**: One `translatedServiceMessage()` function, used by all call sites.
3. **G3 — Regression prevention**: CI hook rejects new bare `'artisan.plus'` literals in `src/ដstring/` and `src/plus/` (excluding tests, build artifacts, and the `.replace()` source itself).

### Non-Goals
- Re-translating the 16 existing `.ts` entries. Once call sites use `translatedServiceMessage()`, the `.replace()` post-processes translated text too — `.ts` content becomes harmless.
- Updating test fixtures that mock old `artisan.plus` URLs (separate cleanup, lower priority).
- Updating 16 plus-module file-header comments (handled in Phase 5; user approved inclusion 2026-06-21).
- Changing email recipient `logfile@artisan.plus` in `main.py:5014` (functional dependency, must not change).

## 3. Design Decisions

### 3.1 Unified `translatedServiceMessage()` location: `plus/util.py`

**Rationale**: `plus/util.py` is already imported by `plus.connection`, `plus.controller`, ` artisanlib.main`, ` artisanlib.roast_properties`, ` artisanlib.notifications`, ` artisanlib.canvas`. Adding the function here creates no new import cycles. It also already imports `from plus import config`; we add `service_identity`.

**Rejected alternatives**:
- `plus/service_identity.py` — would couple identity data with i18n logic.
- New module `plus/i18n.py` — over-engineered for one function; breaks existing imports.

### 3.2 Unified signature: `translatedServiceMessage(source, context='Plus')`

```python
# plus/util.py (new addition)
from PyQt6.QtWidgets import QApplication
from plus import service_identity

def translatedServiceMessage(source: str, context: str = 'Plus') -> str:
    """Translate `source` under `context`, then runtime-replace 'artisan.plus'
    with the configured service display name (Cotrix).

    All user-facing strings that mention 'artisan.plus' MUST route through
    this function. CI enforces this via the anti-pattern grep hook.
    """
    return QApplication.translate(context, source).replace(
        'artisan.plus', service_identity.display_name()
    )
```

**Backwards compatibility**:
- `plus/controller.py:45-48` existing 1-arg form `translatedServiceMessage(source)` → continues to work (context defaults to 'Plus', which matches current behavior).
- ` artisanlib/roast_properties.py:67-70` existing 2-arg form `translatedServiceMessage(context, source)` → **BREAKING**. Caller code uses positional args: `translatedServiceMessage('Message', 'artisan.plus needs to know...')`. Under new signature this becomes `source='Message', context='artisan.plus needs to know...'` — completely wrong.

**Migration approach for roast_properties.py call site**:
- Change the single call at `roast_properties.py:1704-1707` to keyword form: `translatedServiceMessage('artisan.plus needs to know the beans you are roasting', context='Message')`.
- Delete the local `translatedServiceMessage` definition at `roast_properties.py:67-70`.
- Add `from plus.util import translatedServiceMessage` to imports.

### 3.3 `__release_sponsor_*` strategy: hardcode literals + sync comment

**Constraint**: ` artisanlib/__init__.py` is imported by `plus/connection.py:26` (`from artisanlib import __version__`). Therefore ` artisanlib/__init__.py` CANNOT import from `plus.*` — would cause circular import.

**Three options considered**:

| Option | Pros | Cons |
|---|---|---|
| **A. Hardcode `'Cotrix'` literals** | Simple, no import cycle | Duplicates `DISPLAY_NAME` constant; requires manual sync |
| **B. Empty strings (remove sponsor)** | Removes attribution entirely | Loses sponsor recognition; changes upstream semantics |
| **C. Lazy lookup via `__getattr__`** | Single source of truth | Module-level `__getattr__` is Python 3.7+ feature, complicates tooling (pylint, mypy); brittle |

**Recommendation: Option A** with explicit cross-reference comment:

```python
# src/ artisanlib/__init__.py
__version__ = '4.0.3'
__revision__ = ''
__build__ = '0'
__artisan_os__ = 'Linux'

# NOTE: Keep these literals in sync with plus.service_identity.DISPLAY_NAME
# and plus.service_identity.WEB_BASE_URL. We cannot import from plus.* here
# because plus.connection imports from artisanlib (__version__) — circular.
# If service_identity values change, update these literals too.
__release_sponsor_name__ = 'Cotrix'
__release_sponsor_domain__ = 'tastermatrix.com'
__release_sponsor_url__ = 'https://tastermatrix.com/'
__signature__ = '...'
```

**Decision locked 2026-06-21 (user choice)**: Option A — brand consistency. `__release_sponsor_name__ = 'Cotrix'`, `__release_sponsor_domain__ = 'tastermatrix.com'`, `__release_sponsor_url__ = 'https://tastermatrix.com/'`.

### 3.4 Unsafe call-site refactor pattern

For every unsafe call site, the transformation is:

```python
# BEFORE
tooltip = QApplication.translate('Tooltip', 'Syncing with artisan.plus')

# AFTER
from plus.util import translatedServiceMessage
tooltip = translatedServiceMessage('Syncing with artisan.plus', context='Tooltip')
```

Files requiring this refactor (8 call sites in 4 files):

| File | Line | String | New context arg |
|---|---|---|---|
| `src/ artisanlib/main.py` | 5136 | `'...subscribe to artisan.plus...'` | `'Message'` |
| `src/ artisanlib/main.py` | 5404 | `'Syncing with artisan.plus'` | `'Tooltip'` |
| `src/ artisanlib/main.py` | 5407 | `'Disconnect artisan.plus'` | `'Tooltip'` |
| `src/ artisanlib/main.py` | 5410 | `'Upload to artisan.plus'` | `'Tooltip'` |
| `src/ artisanlib/main.py` | 5441 | `'Disconnect artisan.plus'` | `'Tooltip'` |
| `src/ artisanlib/main.py` | 5444 | `'Connect artisan.plus'` | `'Tooltip'` |
| `src/help/keyboardshortcuts_help.py` | 59 | `'Open the roast in artisan.plus'` + `'Requires an artisan.plus account'` | `'HelpDlg'` |
| `src/help/keyboardshortcuts_help.py` | 66 | `'Sync the roast with artisan.plus'` | `'HelpDlg'` |
| `src/plus/sync.py` | 730 | `'Updated data received from artisan.plus'` | `'Plus'` (default, can omit) |

### 3.5 CI anti-pattern hook: local pre-commit hook

Add to `.pre-commit-config.yaml`:

```yaml
-   repo: local
    hooks:
    -   id: no-bare-artisan-plus-literal
        name: Forbid bare 'artisan.plus' literal in plus/ or  artisanlib/
        description: >-
            User-facing strings mentioning artisan.plus must route through
            plus.util.translatedServiceMessage. Update the source string
            inside translatedServiceMessage(...) to keep the literal in
            context, OR replace the call site with config.app_name format.
        language: system
        entry: bash -c 'bash tools/check_no_bare_artisan_plus.sh "$@"' --
        pass_filenames: false
        always_run: true
```

New script `tools/check_no_bare_artisan_plus.sh`:

```bash
#!/usr/bin/env bash
# Fails if any .py file under src/plus/ or src/ artisanlib/ contains a bare
# 'artisan.plus' literal that is NOT inside a translatedServiceMessage(...)
# call or .replace('artisan.plus', ...) post-processor.
#
# Allowed locations (whitelist):
#   - src/plus/util.py          (defines translatedServiceMessage with the .replace)
#   - src/plus/controller.py    (legacy impl, will be removed in P2)
#   - src/ artisanlib/__init__.py (hardcoded sponsor literals, documented)
#   - Comments and module docstrings (not user-facing)
#
# The check uses ripgrep with negative lookahead via Perl regex.
set -euo pipefail

if ! command -v rg >/dev/null 2>&1; then
    echo "[skip] ripgrep not installed" >&2
    exit 0
fi

# Pattern: a line containing 'artisan.plus' inside a single/double-quoted
# string, where the line does NOT contain 'translatedServiceMessage(',
# '.replace(', or '#', or '//'
violations=$(rg -n --no-heading \
    --type py \
    -g '!src/test/**' \
    -g '!src/build/**' \
    -g '!src/dist/**' \
    -g '!src/uic/**' \
    "['\"]([^\"]*artisan\.plus[^\"]*)['\"]" \
    src/plus/ src/ artisanlib/ src/help/ \
    2>/dev/null \
    | rg -v 'translatedServiceMessage' \
    | rg -v '\.replace\(' \
    | rg -v '^\s*#' \
    | rg -v '__release_sponsor_' \
    || true)

if [[ -n "$violations" ]]; then
    echo "ERROR: Found bare 'artisan.plus' literal(s) that bypass translatedServiceMessage:" >&2
    echo "$violations" >&2
    echo "" >&2
    echo "Fix: wrap the call site in translatedServiceMessage(source, context=...)" >&2
    echo "     or use config.app_name format string for dynamic brand." >&2
    exit 1
fi

echo "[ok] no bare 'artisan.plus' literals in plus/ or  artisanlib/"
```

**Why local hook, not ruff custom rule**: ruff custom rules require Python plugin code; local bash hook is portable, has zero dependencies beyond ripgrep (already in CI), and the failure message can explain the fix directly.

### 3.6 Removal of duplicate `translatedServiceMessage` in `plus/controller.py`

After `plus/util.py` version is in place and all callers use it:

```python
# plus/controller.py — DELETE lines 45-48
def translatedServiceMessage(source: str) -> str:
    return QApplication.translate('Plus', source).replace(
        'artisan.plus', service_identity.display_name()
    )

# REPLACE WITH:
from plus.util import translatedServiceMessage  # noqa: F401  (re-exported for backwards compat)
```

Existing callers of `plus.controller.translatedServiceMessage` continue to work via the re-export. This preserves backwards compatibility while consolidating logic in `plus/util.py`.

## 4. Implementation Phases

Each phase is a separate atomic commit, smallest-first to enable bisect.

### Phase 1 — P0 fixes (user-visible brand consistency)

**Scope**: `__release_sponsor_*` + 5 toolbar tooltips in `main.py`. Minimum user-facing fix.

**Files touched**:
- `src/ artisanlib/__init__.py` — update 3 sponsor literals (per Option A in §3.3)
- `src/ artisanlib/main.py` — refactor 5 tooltip call sites (per §3.4 table)

**Verification**:
- Launch app, hover on plus toolbar icon in each state (off/on/syncing/dirty), confirm tooltip shows "Cotrix" not "artisan.plus"
- Check main window title bar shows "... – Cotrix (Release Sponsor)" (if sponsor non-empty)
- Check About dialog shows "sponsored by tastermatrix.com"
- `python3 -m py_compile src/ artisanlib/__init__.py src/ artisanlib/main.py`
- `python3 -m pytest test/unitary/ artisanlib/test_roast_properties_tm_artisanz.py -q` (existing test still passes)

**Commit message**: `fix(branding): show Cotrix in window title and plus toolbar tooltips`

### Phase 2 — P1 fixes (remaining unsafe call sites)

**Scope**: Help dialog + donation dialog + sync.py status message.

**Files touched**:
- `src/help/keyboardshortcuts_help.py` — refactor 2 lines (3 translate calls)
- `src/ artisanlib/main.py:5136` — refactor donation dialog
- `src/plus/sync.py:730` — refactor status message

**Verification**:
- Open Help → Additional Shortcuts, confirm rows show "Open the roast in Cotrix", "Sync the roast with Cotrix"
- Trigger donation dialog, confirm text says "subscribe to Cotrix"
- (Hard to verify sync message without live server) Run unit tests covering sync.py to ensure no string format breakage

**Commit message**: `fix(branding): route help, donation, sync strings through translatedServiceMessage`

### Phase 3 — P2 refactor (unify translatedServiceMessage)

**Scope**: Single source of truth + remove duplicate.

**Order of operations** (critical to avoid breakage):
1. Add unified `translatedServiceMessage(source, context='Plus')` to `src/plus/util.py`.
2. In `src/ artisanlib/roast_properties.py`:
   - Add `from plus.util import translatedServiceMessage` to imports.
   - Change call at line 1704-1707 to `translatedServiceMessage('artisan.plus needs to know the beans you are roasting', context='Message')`.
   - Delete local definition at lines 67-70.
3. In `src/plus/controller.py`:
   - Add `from plus.util import translatedServiceMessage` re-export.
   - Delete local definition at lines 45-48.
4. Run all plus tests to confirm no regressions.

**Verification**:
- `python3 -c "from plus.util import translatedServiceMessage; from plus.controller import translatedServiceMessage as t2; assert translatedServiceMessage is t2; print('unified OK')"`
- `python3 -m pytest test/unitary/plus/ test/unitary/ artisanlib/test_roast_properties_tm_artisanz.py -q`
- `python3 -m py_compile src/plus/util.py src/plus/controller.py src/ artisanlib/roast_properties.py`

**Commit message**: `refactor(i18n): unify translatedServiceMessage in plus.util, remove duplicates`

### Phase 4 — P2 CI guard (prevent future regressions)

**Scope**: Pre-commit hook + bash checker script.

**Files touched**:
- `tools/check_no_bare_artisan_plus.sh` — new script (executable)
- `.pre-commit-config.yaml` — add local hook entry

**Verification**:
- Manually add a bare `'artisan.plus'` literal somewhere in `src/plus/*.py`, run `pre-commit run no-bare-artisan-plus-literal --all-files`, confirm it fails with the expected error message.
- Remove the violation, confirm hook passes.
- Confirm hook skips `src/test/`, `src/build/`, `src/uic/`, and the whitelisted files.

**Commit message**: `ci(pre-commit): add grep hook to forbid bare 'artisan.plus' literals`

### Phase 5 — Documentation (INCLUDED per user decision 2026-06-21)

**Scope**: Update file-header comments in plus/*.py for cosmetic cleanliness. User chose to include this in the same change set.

**Files touched**:
- 16 files in `src/plus/*.py` — change line 9 from `# This module connects to the artisan.plus inventory management service` to `# This module connects to the Cotrix inventory management service`.

**Commit message**: `docs(plus): refresh module header comments to reflect Cotrix brand`

## 5. Test Plan

### 5.1 New tests

Add `src/test/unitary/plus/test_util_translated_service_message.py`:

```python
"""Tests for the unified plus.util.translatedServiceMessage."""
import pytest
from unittest.mock import patch
from plus.util import translatedServiceMessage


def test_replaces_artisan_plus_with_display_name() -> None:
    """The literal 'artisan.plus' in source is replaced at runtime."""
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'Connect artisan.plus'
        result = translatedServiceMessage('Connect artisan.plus')
        assert result == 'Connect Cotrix'
        mock_qapp.translate.assert_called_once_with('Plus', 'Connect artisan.plus')


def test_preserves_context_default() -> None:
    """Default context is 'Plus' (matches plus.controller legacy behavior)."""
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'x'
        translatedServiceMessage('x')
        mock_qapp.translate.assert_called_once_with('Plus', 'x')


def test_accepts_explicit_context() -> None:
    """Explicit context kwarg overrides default."""
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'x'
        translatedServiceMessage('x', context='Tooltip')
        mock_qapp.translate.assert_called_once_with('Tooltip', 'x')


def test_handles_translated_string_with_brand() -> None:
    """Replace operates on the TRANSLATED string, not just source."""
    with patch('plus.util.QApplication') as mock_qapp:
        # Simulate zh_CN translation
        mock_qapp.translate.return_value = '已连接到artisan.plus'
        result = translatedServiceMessage('Connected to artisan.plus')
        assert result == '已连接到Cotrix'


def test_no_artisan_plus_in_source_passes_through() -> None:
    """Strings without 'artisan.plus' are returned unchanged after translate."""
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'Hello World'
        assert translatedServiceMessage('Hello World') == 'Hello World'
```

### 5.2 Existing tests to verify

- `src/test/unitary/ artisanlib/test_roast_properties_tm_artisanz.py` — must still pass after Phase 3 refactor. Verifies `'artisan.plus needs to know the beans you are roasting'` → `'Cotrix needs to know the beans you are roasting'`.
- `src/test/unitary/plus/test_controller.py` — must still pass after Phase 3 (re-export keeps `plus.controller.translatedServiceMessage` importable).
- `src/test/unitary/plus/test_config.py` — verify `config.app_name` still equals `service_identity.display_name()`.

### 5.3 Manual smoke test (post-Phase 3)

```bash
cd src
python3 -c "
from plus.util import translatedServiceMessage
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
# Simulate the user's screenshot scenario
print(repr(translatedServiceMessage('artisan.plus needs to know the beans you are roasting', context='Message')))
# Expected: 'Cotrix needs to know the beans you are roasting'
print(repr(translatedServiceMessage('Syncing with artisan.plus', context='Tooltip')))
# Expected: 'Syncing with Cotrix'
print(repr(translatedServiceMessage('Disconnect artisan.plus?')))
# Expected: 'Disconnect Cotrix?'
"
```

## 6. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Circular import** when adding `service_identity` to `plus/util.py` | Low | `service_identity.py` has no plus-internal imports, only `typing.Final`. No cycle. |
| **Breaking change** for `translatedServiceMessage(context, source)` callers | Medium | Phase 3 step 2 explicitly updates the only known caller (roast_properties.py:1704). Grep for other callers before deleting. |
| **Pre-commit hook false positives** on legitimate code (URLs, comments) | Medium | Whitelist via `rg -v` filters: `__release_sponsor_`, `#`, `.replace(`, `translatedServiceMessage`. |
| **`__release_sponsor_*` semantics debate** (sponsor attribution vs brand) | High | Spec defaults to brand consistency. User decision point in §3.3. |
| **Test fixture staleness** — `test_controller.py:171` patches `app_name` to old value | Low | Existing tests mock at URL level, not at brand string. Will still pass. |
| **`.ts` translation file** retains 16 "artisan.plus" entries | None | Safe call sites use `.replace()` which operates on translated text. No action needed. |

## 7. Acceptance Criteria

For each phase, completion requires evidence (not assertion).

### Phase 1 (P0)
- [ ] `git diff HEAD~1 -- src/ artisanlib/__init__.py` shows 3 sponsor literals updated.
- [ ] `git diff HEAD~1 -- src/ artisanlib/main.py` shows 5 tooltip call sites refactored to use `translatedServiceMessage`.
- [ ] `python3 -m py_compile src/ artisanlib/__init__.py src/ artisanlib/main.py` exits 0.
- [ ] `python3 -m pytest test/unitary/ artisanlib/test_roast_properties_tm_artisanz.py -q` passes.
- [ ] Manual smoke: launch app, hover plus icon in 4 states, confirm "Cotrix" in tooltip.

### Phase 2 (P1)
- [ ] `git diff HEAD~1 -- src/help/keyboardshortcuts_help.py src/ artisanlib/main.py src/plus/sync.py` shows 4 call sites refactored.
- [ ] `python3 -m py_compile` exits 0 on all touched files.
- [ ] Existing plus tests still pass.

### Phase 3 (P2 refactor)
- [ ] `plus/util.py` contains the unified `translatedServiceMessage(source, context='Plus')` function.
- [ ] `plus/controller.py` re-exports it (no local definition).
- [ ] ` artisanlib/roast_properties.py` has no local definition; imports from `plus.util`.
- [ ] New test file `test_util_translated_service_message.py` passes with 5 tests.
- [ ] `python3 -c "from plus.util import translatedServiceMessage; from plus.controller import translatedServiceMessage as t2; assert translatedServiceMessage is t2"` exits 0.

### Phase 4 (P2 CI guard)
- [ ] `tools/check_no_bare_artisan_plus.sh` exists, is executable, and is referenced in `.pre-commit-config.yaml`.
- [ ] `pre-commit run no-bare-artisan-plus-literal --all-files` exits 0 on current codebase.
- [ ] Manually inserting a violation (e.g., `x = 'artisan.plus test'` in `src/plus/util.py`) causes the hook to fail.
- [ ] Removing the violation restores passing state.

### Phase 5 (cosmetic docs)
- [ ] All 16 plus-module files have updated line-9 comment.
- [ ] No functional change; `git diff` shows only comment lines.

### Universal
- [ ] No use of `as any`, `@ts-ignore`, or type-unsafe suppressions.
- [ ] No deletion or modification of existing passing tests.
- [ ] Pre-existing lint errors unrelated to this change are not "fixed" silently.

## 8. Out of Scope (explicitly deferred)

- Updating 7 test fixture files (`test/unitary/plus/*.py`) that mock old `artisan.plus` URLs.
- Re-translating `.ts` file entries.
- Adding brand identity tests for non-English locales.
- Investigating why Cotrix `/acoffees` returns empty (Phase 2 of Cotrix backend migration — separate effort).
- Migrating `logfile@artisan.plus` email recipient (functional dependency, deferred indefinitely).

## 9. Resolved Decisions (locked 2026-06-21)

| ID | Decision | Choice | Rationale |
|---|---|---|---|
| **D1** | `__release_sponsor_name__` value | `'Cotrix'` | Brand consistency — main window title and About dialog align with the rest of the GUI |
| **D2** | `__release_sponsor_url__` value | `'https://tastermatrix.com/'` | Browser opens Cotrix homepage on sponsor click, not the legacy artisan.plus site |
| **D3** | Phase 5 (cosmetic comment update) | **Included** | One-shot cleanup; 16 lines changed; no functional risk; keeps the codebase internally consistent |

All decisions resolved. Implementation can proceed without further user input.

**End of spec.** Implementation agents should treat §4 (phases) as the work breakdown and §7 (acceptance) as the definition of done. Decisions in §9 must be resolved before Phase 1 starts.
