# AGENTS.md — ArtisanZ

ArtisanZ is a personal fork of upstream Artisan (`https://github.com/artisan-roaster-scope/artisan`). Treat `master` as the upstream-sync branch and `ArtisanZ` as the product/customization branch.

## Before Editing

Run this preflight and do not skip it:

```bash
git branch --show-current
git status --short
git remote -v
```

Expected remotes:

```text
origin   git@github.com:koffja/ArtisanZ.git
upstream https://github.com/artisan-roaster-scope/artisan.git
```

- Normal development belongs on `ArtisanZ`; switch there before editing unless the task is explicitly about syncing upstream.
- Never commit or push unless explicitly asked. If asked, commit custom work on `ArtisanZ` only.
- Preserve existing uncommitted/untracked user files; this repo may contain local governance/docs changes.

## Branch and Upstream Sync Rules

- `master`: mirror-like official baseline. Only fetch/merge from `upstream/master`; do not add ArtisanZ features here.
- `ArtisanZ`: custom branch for charge-target features, Chinese localization, portable Windows packaging, and local docs.
- Official update flow:

```bash
git checkout master
git fetch upstream
git merge upstream/master
git push origin master
git checkout ArtisanZ
git merge master
```

- Conflict rule: keep upstream bug fixes/new features and re-apply ArtisanZ customizations as small patches; do not overwrite newer upstream files with old local snapshots.
- Do not use old `ZHES-Artisan` snapshots as source of truth except as historical reference for already-known custom code.

## Project Shape

- Work from `src/` for running, testing, linting, typing, and packaging commands.
- Main entrypoint: `src/artisan.py` → `artisanlib.command_utility.handleCommands()` → `artisanlib.main.main()`.
- Core UI/application code is PyQt6-heavy and lives mostly in `src/artisanlib/`; `src/artisanlib/main.py` is very large and imports ArtisanZ charge-target classes near the top.
- Tool configuration is in `src/pyproject.toml`; runtime/dev deps are `src/requirements.txt` and `src/requirements-dev.txt`.
- Generated/derived outputs include `src/uic/*.py`, `src/translations/*.qm`, help outputs, `src/build/`, and `src/dist/`.
- License: upstream Artisan is AGPLv3 since v5 (merged on 2026-11-24). `LICENSE` and the per-file headers follow upstream; ArtisanZ is a derivative of it.

## ArtisanZ Custom Risk Areas

Be especially careful during edits and upstream merges:

- Charge target feature: `src/artisanlib/charge_manager.py`, `src/artisanlib/charge_dialog.py`, `src/test/unitary/artisanlib/test_charge_manager.py`
- Integration points: `src/artisanlib/main.py`, `src/artisanlib/canvas.py`
- Button palette: `src/artisanlib/gui_theme.py` recolours the styles upstream generates in `src/artisanlib/styles.py` (wrappers on `push_button_style()` and the SV +/- styles); the event-button template is `gui_theme.artisan_event_button_style()`
- Workspace policy: `src/artisanlib/ui_workspaces.py` (`WorkspacePolicy.show_dashboard` keeps upstream's dashboard an EXPERT-workspace feature), with gates in `main.py` (`workspace_allows_dashboard`, `workspace_allows_dashboard_toggle`) and `dashboard.py`
- Cotrix brand swap: `plus/service_identity.brand_substitutions()` and `plus/util.translatedServiceMessage()`; the pre-commit hook `tools/check_no_bare_artisan_plus.sh` flags bare service names
- Worker sampling path: `sample_processing` in `canvas.py` runs ArtisanZ's worker chain and constructs the PID lazily in `_continue_thermal_result()`, where upstream does so in its own `sample_processing`
- Simplified Chinese customization: `src/translations/artisan_zh_CN.ts`, `src/translations/artisan_zh_CN.qm`
- Windows portable build: `build-win-portable.bat`, `PORTABLE_BUILD_GUIDE.md`, `artisan打包win说明.txt`
- Planning/history docs: `CHARGE_TARGET_SUMMARY.md`, `charge_target_plan.md`, `PROJECT_GOVERNANCE.md`

## Setup and Local Run

Use Python 3.13+ (`src/pyproject.toml` sets `requires-python = '>=3.13'`); CI currently installs Python 3.14. From `src/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python3 artisan.py
```

`PyQt6`/Qt dependencies are required for many imports and tests. If dependency installation is unavailable, report that clearly instead of claiming tests passed.

## Verification Commands

Focused ArtisanZ custom-feature check:

```bash
cd src
python3 -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

General checks from executable config/docs:

```bash
cd src
python3 -m pytest --continue-on-collection-errors   # pyproject: testpaths = ["test"], addopts = "-ra -v"
python3 -m ruff check .              # CI ruff checks ./src
python3 -m mypy                      # configured by src/pyproject.toml
python3 -m pyright
python3 -m pylint artisanlib plus    # CI uses PyQt6 extension allow-list and targets these packages
python3 -m codespell                 # skips *.ts/build/dist/htmlcov/spec per pyproject
pre-commit run --all-files           # hooks exclude uic/translations/includes/test data
```

The flag is needed because `test/unitary/tools/peak_p1_proxy/` imports the repo-root `tools` package, which is not importable from `src/`: those five files error at collection and abort the whole run without it.

Run the smallest relevant subset first, then broader checks if the change touches shared code. `src/conftest.py` registers platform markers (`darwin`, `linux`, `win32`) and imports `numpy`/`scipy.optimize` globally for pytest.

## Translations and Generated Files

- Translation sources are listed in `src/artisan.pro`; `artisan_zh_CN.ts` is custom-sensitive.
- Only `artisan_zh_CN.ts` / `.qm` are maintained on ArtisanZ. The other 31 languages are upstream's files byte for byte: do not run the full `pylupdate6pro.py` or the translation step of `build-derived.sh` on ArtisanZ. They rewrite all 32 `.ts` files, and every later upstream sync then conflicts on them.
- Regenerate zh_CN only, from `src/`: `pylupdate6 artisanlib help plus --ts translations/artisan_zh_CN.ts`, then `lrelease translations/artisan_zh_CN.ts` (`lrelease` is in the venv under `qt6_applications/Qt/bin/`).
- macOS/Linux derived files:

```bash
cd src
./build-derived.sh linux   # or macos
```

- Windows derived files require `PYTHONPATH`, `PYUIC` (default `pyuic6.exe`) and `LRELEASE_PATH`; the shell script reads `QT_SRC_PATH`, `QTTOOLS` or `QT_SRC_PATH_QTTOOLS`, `PYUIC`, `PYTHON_PATH` and `PYLUPDATE`:

```cmd
cd src
build-derived-win.bat
```

These scripts regenerate help files, `uic/*.py`, and compile `translations/*.ts` to `*.qm` via `pylupdate6pro.py`/`lrelease`.

## Packaging Notes

- Official package builds are AppVeyor-driven via `.appveyor.yml` and only run on `master`.
- Platform specs live in `src/artisan-win.spec`, `src/artisan-mac.spec`, and `src/artisan-linux.spec`.
- Portable Windows build is an ArtisanZ addition and must be run from the repo root:

```cmd
build-win-portable.bat
```

It changes into `src/`, runs `python -m PyInstaller artisan-win.spec --clean --noconfirm`, and expects `src\dist\artisan\artisan.exe` plus VC++ runtime DLLs.

## CI Reality

- GitHub Actions workflows (`pytest`, `pylint`, `ruff`, `mypy`, `codespell`) target `master` in `.github/workflows/`.
- AppVeyor package builds also target `master` and patch `src/artisanlib/__init__.py` revision/signature during build; avoid unnecessary custom edits there.

## Codebase-Memory-MCP Notes

ArtisanZ is indexed by codebase-memory-mcp v0.8.1 (binary at `~/.local/bin/codebase-memory-mcp`, configured in `~/.config/opencode/opencode.json` as a local MCP). The persistent artifact `.codebase-memory/graph.db.zst` (~7.6 MB) is generated by the indexer and may be committed to the ArtisanZ branch for team-wide fast restore. Backups before reindex live at `~/.local/bin/cbm-backup-v0.6.0/` and `~/.cache/codebase-memory-mcp/Users-chengzhe-Projects-ArtisanZ.db.pre-reindex-v0.6.0.bak`.

### Known bugs and workarounds (verified 2026-06-20, cbm v0.8.1)

1. **`search_graph` `name_pattern` does not match the `Class.method` dotted form.**
   - Symptom: `search_graph(name_pattern="ChargeTargetManager.evaluate_readiness", label="Method")` returns `total: 0` even though the method exists.
   - Workaround: use a regex pattern like `.*evaluate_readiness.*`, or skip `search_graph` and call `trace_path(qualified_name="Users-chengzhe-Projects-ArtisanZ.src.artisanlib.charge_manager.ChargeTargetManager.evaluate_readiness")` directly.

2. **`EMITS` edges are not extracted from PyQt6 code.**
   - Symptom: ArtisanZ has 267 `.emit()` call sites (159 in `main.py` + 108 in `canvas.py`) but only 1 EMITS edge is produced, and it is a false positive (`test_ws_server.py` with `transport="websocket"`). The extractor does not recognise `pyqtSignal().emit(...)`.
   - Workaround: do not rely on EMITS for signal-flow analysis. Use `search_code(query="\\.emit\\(", file_pattern="*.py")` plus manual reading of `pyqtSignal` declarations.

3. **`HANDLES` edges are dominated by false positives on a desktop project.**
   - Symptom: all 38 HANDLES edges point at pytest test methods with `handler="/"`. The route extractor treats each test method as a route handler. ArtisanZ is a PyQt6 desktop app with no inbound HTTP server, so HANDLES carries no signal here.
   - Workaround: ignore HANDLES unless ArtisanZ gains a real HTTP layer (e.g., `plus/connection.py`). For actual outbound HTTP, use `HTTP_CALLS` edges (10 detected, e.g. `https://api.roestcoffee.com/o/token/`).

### Working capabilities (safe to rely on)

- `INHERITS` edges are accurate (verified on `Artisan(QtSingleApplication)`, `LargeLCDs(ArtisanDialog)`, `Login(ArtisanDialog)`, `Worker(QObject)`, `SantokerR(ClientBLE)` and ~95 others).
- `Method.cognitive`, `Method.recursive`, `Method.loop_depth` fields align with source-code complexity.
- `Method.signature`, `Method.return_type`, `Method.parent_class` are populated by the Hybrid Python LSP.
- `File.change_count` and `File.last_modified` match `git log --name-only` exactly (e.g., `main.py change_count=82, last_modified=1781580145` equals the 2026-06-16 commit timestamp).
- `trace_path` with `risk_labels=true` produces correct inbound/outbound impact radii (verified on `ChargeTargetManager.evaluate_readiness` reaching `canvas.tgraphcanvas.updategraphics/redraw`).
- `DECORATES` (2017 edges) and `Decorator` nodes (34) cover real decorators: `pyqtSlot`, `dataclass`, `staticmethod`, `classmethod`, `property`, `override`, `pytest.mark.parametrize`, `pytest.fixture`, `patch`, `pytest.mark.linux`.
- `Channel` nodes are unreliable on this project (1 detected, content is a misread comment).

### Useful Cypher recipes for ArtisanZ

```cypher
// Hot spot files by git activity
MATCH (f:File) WHERE f.change_count > 10
RETURN f.file_path, f.change_count, f.last_modified
ORDER BY f.change_count DESC LIMIT 20

// Methods with high cognitive complexity in main.py
MATCH (m:Method) WHERE m.file_path CONTAINS 'main.py' AND m.cognitive > 10
RETURN m.name, m.parent_class, m.cognitive, m.start_line
ORDER BY m.cognitive DESC LIMIT 20

// PyQt6 inheritance tree filtered to ArtisanDialog subclasses
MATCH (child:Class)-[:INHERITS]->(parent:Class {name: 'ArtisanDialog'})
RETURN child.name, child.file_path

// ChargeTargetManager public surface and their callers
MATCH (caller)-[:CALLS]->(m:Method)
WHERE m.parent_class CONTAINS 'ChargeTargetManager'
RETURN m.name, count(caller) AS fan_in
ORDER BY fan_in DESC
```

For full inbound/outbound impact use `trace_path(qualified_name=..., direction=..., depth=..., risk_labels=true)`; do not try to express multi-hop traversal in Cypher (list comprehensions and sub-queries are not supported by the bundled engine).

### Re-index procedure

`mode=full` alone is NOT enough to force a rebuild — the indexer skips on hash match (`incremental.noop reason=no_changes`). To force a full reindex after upgrading `codebase-memory-mcp` or after a major upstream merge:

```bash
# 1. Backup current index (rollback safety)
cp /Users/chengzhe/.cache/codebase-memory-mcp/Users-chengzhe-Projects-ArtisanZ.db \
   /Users/chengzhe/.cache/codebase-memory-mcp/Users-chengzhe-Projects-ArtisanZ.db.bak

# 2. Delete project so incremental cache does not skip rebuild
~/.local/bin/codebase-memory-mcp cli delete_project \
  '{"project":"Users-chengzhe-Projects-ArtisanZ"}'

# 3. Fresh full index
~/.local/bin/codebase-memory-mcp cli index_repository \
  '{"repo_path":"/Users/chengzhe/Projects/ArtisanZ","mode":"full","persistence":true}'
# Expected on ArtisanZ (442 files): ~25s, ~27100 nodes, ~73500 edges, artifact ~7.6 MB
```

The fresh artifact at `.codebase-memory/graph.db.zst` can be committed on the ArtisanZ branch so teammates skip the reindex. The bundled `.gitattributes` uses `merge=ours` to avoid conflicts.

### Rollback procedure

If a newer cbm version regresses on PyQt6 extraction:

```bash
# Restore the v0.6.0-era binary and index snapshot
cp /Users/chengzhe/.local/bin/cbm-backup-v0.6.0/codebase-memory-mcp \
   /Users/chengzhe/.local/bin/codebase-memory-mcp
cp /Users/chengzhe/.cache/codebase-memory-mcp/Users-chengzhe-Projects-ArtisanZ.db.pre-reindex-v0.6.0.bak \
   /Users/chengzhe/.cache/codebase-memory-mcp/Users-chengzhe-Projects-ArtisanZ.db
# Then restart opencode / MCP client to pick up the old binary.
```
