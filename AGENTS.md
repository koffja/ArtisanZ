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

## ArtisanZ Custom Risk Areas

Be especially careful during edits and upstream merges:

- Charge target feature: `src/artisanlib/charge_manager.py`, `src/artisanlib/charge_dialog.py`, `src/test/unitary/artisanlib/test_charge_manager.py`
- Integration points: `src/artisanlib/main.py`, `src/artisanlib/canvas.py`
- Simplified Chinese customization: `src/translations/artisan_zh_CN.ts`, `src/translations/artisan_zh_CN.qm`
- Windows portable build: `build-win-portable.bat`, `PORTABLE_BUILD_GUIDE.md`, `artisan打包win说明.txt`
- Planning/history docs: `CHARGE_TARGET_SUMMARY.md`, `charge_target_plan.md`, `PROJECT_GOVERNANCE.md`

## Setup and Local Run

Use Python 3.12+; CI currently installs Python 3.14. From `src/`:

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
python3 -m pytest                    # pyproject: testpaths = ["test"], addopts = "-ra -v"
python3 -m ruff check .              # CI ruff checks ./src
python3 -m mypy                      # configured by src/pyproject.toml
python3 -m pyright
python3 -m pylint artisanlib plus    # CI uses PyQt6 extension allow-list and targets these packages
python3 -m codespell                 # skips *.ts/build/dist/htmlcov/spec per pyproject
pre-commit run --all-files           # hooks exclude uic/translations/includes/test data
```

Run the smallest relevant subset first, then broader checks if the change touches shared code. `src/conftest.py` registers platform markers (`darwin`, `linux`, `win32`) and imports `numpy`/`scipy.optimize` globally for pytest.

## Translations and Generated Files

- Translation sources are listed in `src/artisan.pro`; `artisan_zh_CN.ts` is custom-sensitive.
- macOS/Linux derived files:

```bash
cd src
./build-derived.sh linux   # or macos
```

- Windows derived files require `QT_PATH`, `PYTHON_PATH`, and usually `PYUIC=pyuic6.exe`:

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
