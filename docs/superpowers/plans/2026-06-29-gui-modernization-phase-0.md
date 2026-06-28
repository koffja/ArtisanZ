# GUI Modernization Phase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add disabled-by-default performance instrumentation and a repeatable baseline workflow for ArtisanZ GUI modernization.

**Execution Status:** Implemented and verified on 2026-06-29. Manual GUI baseline runs are still pending and should use `docs/GUI_MODERNIZATION_BASELINE.md`.

**Architecture:** Add a small pure-Python performance probe module under `src/artisanlib/` and wire it into the existing PyQt6/Matplotlib hot paths with minimal behavior impact. Instrumentation is activated only through an environment variable so normal ArtisanZ behavior remains unchanged.

**Tech Stack:** Python 3.12+, PyQt6, Matplotlib QtAgg, pytest, existing `src/pyproject.toml` test configuration.

## Global Constraints

- Work on the `ArtisanZ` branch.
- Run preflight before editing: `git branch --show-current`, `git status --short`, `git remote -v`.
- Commit or push only when explicitly requested. This Phase 0 execution was explicitly authorized for automatic commit; pushing remains out of scope.
- Preserve existing uncommitted/untracked user files.
- Work from `src/` for running, testing, linting, typing, and packaging commands.
- Keep instrumentation disabled by default.
- Do not add PyQtGraph, QML, QtCharts, or any new runtime dependency in Phase 0.
- Do not change roast behavior, device I/O behavior, event timing, alarm semantics, PID behavior, profile serialization, reports, or translations.
- Use `QApplication.translate()` for any new user-facing GUI string. Phase 0 should avoid adding GUI strings.
- Prefer small focused modules instead of expanding `main.py` or `canvas.py` more than necessary.
- Project rules forbid unrequested commits, so the original plan used git status/diff review steps. The 2026-06-29 execution was explicitly authorized for automatic commit after verification.

---

## File Structure

- Create `src/artisanlib/performance.py`: disabled-by-default timing recorder, context manager, environment parsing, summary formatting, and optional JSONL export.
- Create `src/test/unitary/artisanlib/test_performance.py`: unit tests for the recorder, disabled mode, context timing, summary formatting, and JSONL export.
- Modify `src/artisanlib/canvas.py`: add probes around `sample_processing()`, `updategraphics()`, `updateBackground()`, `redraw()`, and skipped-lock branches.
- Create `docs/GUI_MODERNIZATION_BASELINE.md`: operator-facing baseline instructions and report template.
- Update `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`: mark Phase 0 progress after implementation.

## Task 1: Add Performance Probe Module

**Files:**
- Create: `src/artisanlib/performance.py`
- Test: `src/test/unitary/artisanlib/test_performance.py`

**Interfaces:**
- Produces: `GuiPerfRecorder`, `get_gui_perf_recorder()`, `gui_perf_span(name: str)`, `gui_perf_count(name: str, amount: int = 1)`, `gui_perf_tracked(name: str)`, `gui_perf_export_path()`, `gui_perf_enabled()`.
- Consumes: standard library only.

- [x] **Step 1: Write the failing tests**

Add `src/test/unitary/artisanlib/test_performance.py`:

```python
import json
import time

from artisanlib.performance import (
    GuiPerfRecorder,
    gui_perf_count,
    gui_perf_enabled,
    gui_perf_span,
)


def test_recorder_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ARTISANZ_GUI_PERF", raising=False)

    assert gui_perf_enabled() is False


def test_recorder_records_span_when_enabled():
    recorder = GuiPerfRecorder(enabled=True)

    with recorder.span("updategraphics"):
        time.sleep(0.001)

    snapshot = recorder.snapshot()
    assert snapshot["updategraphics"]["count"] == 1
    assert snapshot["updategraphics"]["total_ms"] > 0
    assert snapshot["updategraphics"]["max_ms"] > 0


def test_recorder_counts_events():
    recorder = GuiPerfRecorder(enabled=True)

    recorder.count("updategraphics.lock_skip")
    recorder.count("updategraphics.lock_skip", amount=2)

    snapshot = recorder.snapshot()
    assert snapshot["updategraphics.lock_skip"]["count"] == 3
    assert snapshot["updategraphics.lock_skip"]["total_ms"] == 0


def test_summary_lines_are_stable():
    recorder = GuiPerfRecorder(enabled=True)
    recorder.count("sample_processing.lock_skip")

    lines = recorder.summary_lines()

    assert lines == [
        "sample_processing.lock_skip: count=1 total_ms=0.000 avg_ms=0.000 max_ms=0.000"
    ]


def test_jsonl_export(tmp_path):
    recorder = GuiPerfRecorder(enabled=True)
    recorder.count("redraw.full")
    output = tmp_path / "gui-perf.jsonl"

    recorder.write_jsonl(output)

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows == [
        {
            "name": "redraw.full",
            "count": 1,
            "total_ms": 0,
            "avg_ms": 0,
            "max_ms": 0,
        }
    ]


def test_module_helpers_are_noops_when_disabled(monkeypatch):
    monkeypatch.delenv("ARTISANZ_GUI_PERF", raising=False)

    with gui_perf_span("disabled.span"):
        pass
    gui_perf_count("disabled.count")

    assert gui_perf_enabled() is False
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance.py -q
```

Expected: FAIL because `artisanlib.performance` does not exist.

- [x] **Step 3: Add the minimal implementation**

Create `src/artisanlib/performance.py`:

```python
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import time
from typing import Final


_ENV_FLAG: Final[str] = "ARTISANZ_GUI_PERF"


def _env_enabled() -> bool:
    return os.environ.get(_ENV_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class _Metric:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def add_duration(self, duration_ms: float) -> None:
        self.count += 1
        self.total_ms += duration_ms
        self.max_ms = max(self.max_ms, duration_ms)

    def add_count(self, amount: int) -> None:
        self.count += amount

    def as_dict(self) -> dict[str, float | int]:
        avg_ms = self.total_ms / self.count if self.count else 0.0
        return {
            "count": self.count,
            "total_ms": self.total_ms,
            "avg_ms": avg_ms,
            "max_ms": self.max_ms,
        }


class GuiPerfRecorder:
    def __init__(self, enabled: bool | None = None) -> None:
        self.enabled = _env_enabled() if enabled is None else enabled
        self._metrics: defaultdict[str, _Metric] = defaultdict(_Metric)

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._metrics[name].add_duration(duration_ms)

    def count(self, name: str, amount: int = 1) -> None:
        if self.enabled:
            self._metrics[name].add_count(amount)

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        return {name: metric.as_dict() for name, metric in sorted(self._metrics.items())}

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        for name, metric in self.snapshot().items():
            lines.append(
                f"{name}: count={metric['count']} "
                f"total_ms={metric['total_ms']:.3f} "
                f"avg_ms={metric['avg_ms']:.3f} "
                f"max_ms={metric['max_ms']:.3f}"
            )
        return lines

    def write_jsonl(self, path: str | Path) -> None:
        target = Path(path)
        with target.open("w", encoding="utf-8") as outfile:
            for name, metric in self.snapshot().items():
                outfile.write(json.dumps({"name": name, **metric}, sort_keys=True))
                outfile.write("\n")


_RECORDER = GuiPerfRecorder()


def get_gui_perf_recorder() -> GuiPerfRecorder:
    return _RECORDER


def gui_perf_enabled() -> bool:
    return _env_enabled()


@contextmanager
def gui_perf_span(name: str) -> Iterator[None]:
    with _RECORDER.span(name):
        yield


def gui_perf_count(name: str, amount: int = 1) -> None:
    _RECORDER.count(name, amount)
```

- [x] **Step 4: Run tests to verify they pass**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance.py -q
```

Expected: PASS.

- [x] **Step 5: Review changed files without committing**

Run:

```bash
git status --short
git diff -- src/artisanlib/performance.py src/test/unitary/artisanlib/test_performance.py
```

Expected: only the new performance module and its tests appear.

## Task 2: Instrument Canvas Hot Paths

**Files:**
- Modify: `src/artisanlib/canvas.py`
- Test: `src/test/unitary/artisanlib/test_performance.py`

**Interfaces:**
- Consumes: `gui_perf_tracked(name: str)` and `gui_perf_count(name: str, amount: int = 1)` from `artisanlib.performance`.
- Produces: Timing metrics for `canvas.sample_processing`, `canvas.updategraphics`, `canvas.updateBackground`, `canvas.redraw`, and skip counters.

**Implementation note:** The executed implementation uses `@gui_perf_tracked(...)` decorators around the selected hot-path methods instead of wrapping entire large method bodies in `with gui_perf_span(...)`. This keeps behavior identical while avoiding broad indentation churn in `canvas.py`.

- [x] **Step 1: Add import**

In `src/artisanlib/canvas.py`, add this import near existing `artisanlib` imports:

```python
from artisanlib.performance import gui_perf_count, gui_perf_tracked
```

- [x] **Step 2: Wrap `updateBackground()`**

Decorate `updateBackground()` and count skipped updates:

```python
    @pyqtSlot()
    @gui_perf_tracked("canvas.updateBackground")
    def updateBackground(self) -> None:
        if not self.block_update and self.ax is not None:
            ...
        else:
            gui_perf_count("canvas.updateBackground.skip")
```

- [x] **Step 3: Wrap `sample_processing()`**

Decorate `sample_processing()`:

```python
    @gui_perf_tracked("canvas.sample_processing")
    def sample_processing(self, local_flagstart:bool, temp1_readings:list[float], temp2_readings:list[float], timex_readings:list[float]) -> None:
        ##### (try to) lock resources  #########
```

Keep all existing code inside that `with` block. In the existing branch where `gotlock` is false, add:

```python
            gui_perf_count("canvas.sample_processing.lock_skip")
```

- [x] **Step 4: Wrap `updategraphics()`**

Decorate `updategraphics()`:

```python
    @pyqtSlot()
    @gui_perf_tracked("canvas.updategraphics")
    def updategraphics(self) -> None:
        ...
```

Keep all existing code inside that `with` block. In the existing branch where `gotlock` is false, add:

```python
            gui_perf_count("canvas.updategraphics.lock_skip")
```

- [x] **Step 5: Wrap `redraw()` and `redraw_keep_view()`**

Decorate `redraw_keep_view()`:

```python
    @gui_perf_tracked("canvas.redraw_keep_view")
    def redraw_keep_view(self, *args:bool, **kwargs:bool) -> None:
        ...
```

Decorate `redraw()`:

```python
    @gui_perf_tracked("canvas.redraw")
    def redraw(self, recomputeAllDeltas:bool = True, re_smooth_foreground:bool = True, takelock:bool = True, forceRenewAxis:bool = False, re_smooth_background:bool = False) -> None:
        ...
```

- [x] **Step 6: Run focused syntax and unit checks**

Run:

```bash
cd src
.venv/bin/python -m py_compile artisanlib/performance.py artisanlib/canvas.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance.py test/unitary/artisanlib/test_canvas.py -q
```

Expected: PASS.

- [x] **Step 7: Review changed files without committing**

Run:

```bash
git status --short
git diff -- src/artisanlib/canvas.py
```

Expected: only import additions and timing/counter wrappers in the named hot paths.

## Task 3: Add Baseline Report and Operating Instructions

**Files:**
- Create: `docs/GUI_MODERNIZATION_BASELINE.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

**Interfaces:**
- Consumes: metrics generated by `GuiPerfRecorder`.
- Produces: repeatable instructions for collecting and reviewing Phase 0 results.

- [x] **Step 1: Create baseline document**

Create `docs/GUI_MODERNIZATION_BASELINE.md`:

```markdown
# GUI Modernization Baseline

**Status:** Phase 0 instrumentation ready; manual GUI baseline pending.

## Purpose

This document records the performance evidence used to guide ArtisanZ GUI modernization. Update it whenever instrumentation is run against a representative profile, simulator session, or device session.

## How To Enable Probes

From the repository root:

```bash
cd src
ARTISANZ_GUI_PERF=1 .venv/bin/python artisan.py
```

The probes are disabled unless `ARTISANZ_GUI_PERF` is set to `1`, `true`, `yes`, or `on`.

## Hot Paths

- `canvas.sample_processing`: GUI-thread post-processing after samples are read.
- `canvas.updategraphics`: GUI-thread live LCD and Matplotlib blit/update path.
- `canvas.updateBackground`: full background draw and Matplotlib background cache refresh.
- `canvas.redraw`: full graph redraw path.
- `canvas.redraw_keep_view`: redraw path preserving current graph view.

## Baseline Scenario

Run each scenario for at least five minutes where possible:

1. OFF -> ON monitoring with simulator or a safe test device.
2. OFF -> START recording with ET, BT, Delta ET, and Delta BT visible.
3. START recording with a background profile loaded.
4. START recording with extra event buttons visible.
5. Load a representative historical profile and trigger a full redraw.

## Results Template

| Date | Branch | Scenario | Sampling Interval | Visible Curves | Key Metrics | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-29 | ArtisanZ | Not yet run | Not recorded | Not recorded | Not recorded | Instrumentation implemented and verified; capture hardened before real GUI baseline |

## Decision Log

Record decisions after benchmark runs:

- If `canvas.updategraphics` dominates, prioritize renderer boundary and PyQtGraph POC.
- If `canvas.sample_processing` dominates, prioritize processing decoupling before renderer replacement.
- If `canvas.redraw` dominates only during settings/profile actions, prioritize full-redraw reduction but keep live renderer scope narrow.
- If lock skip counters rise under normal sampling, prioritize signal scheduling and critical-section reduction.
```

- [x] **Step 2: Update roadmap Phase 0 status after implementation**

In `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`, change the Phase 0 row status to `Instrumentation ready` after Tasks 1-5 are implemented and verified.

- [x] **Step 3: Review docs without committing**

Run:

```bash
git status --short
git diff -- docs/GUI_MODERNIZATION_BASELINE.md docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md
```

Expected: baseline document created, roadmap status updated only if implementation has started.

## Task 4: Add Optional JSONL Export Hook

**Files:**
- Modify: `src/artisanlib/performance.py`
- Modify: `src/artisanlib/main.py`
- Test: `src/test/unitary/artisanlib/test_performance.py`

**Interfaces:**
- Consumes: `ARTISANZ_GUI_PERF_FILE`.
- Produces: optional JSONL metrics file when Artisan exits.

- [x] **Step 1: Extend tests for env export path**

Add this test to `src/test/unitary/artisanlib/test_performance.py`:

```python
def test_export_path_comes_from_environment(monkeypatch, tmp_path):
    output = tmp_path / "artisan-gui-perf.jsonl"
    monkeypatch.setenv("ARTISANZ_GUI_PERF_FILE", str(output))

    from artisanlib.performance import gui_perf_export_path

    assert gui_perf_export_path() == output
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance.py::test_export_path_comes_from_environment -q
```

Expected: FAIL because `gui_perf_export_path` does not exist.

- [x] **Step 3: Implement export path helper**

Add to `src/artisanlib/performance.py`:

```python
def gui_perf_export_path() -> Path | None:
    raw_path = os.environ.get("ARTISANZ_GUI_PERF_FILE", "").strip()
    if not raw_path:
        return None
    return Path(raw_path)
```

- [x] **Step 4: Export on app shutdown**

In `src/artisanlib/main.py`, import:

```python
from artisanlib.performance import get_gui_perf_recorder, gui_perf_export_path
```

Near the end of `ApplicationWindow.stopActivities()`, after activities have stopped and before returning, add:

```python
        perf_path = gui_perf_export_path()
        if perf_path is not None:
            try:
                get_gui_perf_recorder().write_jsonl(perf_path)
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)
```

- [x] **Step 5: Run focused verification**

Run:

```bash
cd src
.venv/bin/python -m py_compile artisanlib/performance.py artisanlib/main.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance.py -q
```

Expected: PASS.

- [x] **Step 6: Review changed files without committing**

Run:

```bash
git status --short
git diff -- src/artisanlib/performance.py src/artisanlib/main.py src/test/unitary/artisanlib/test_performance.py
```

Expected: optional export helper and shutdown export hook only.

## Task 5: Phase 0 Verification Bundle

**Files:**
- Verify: `src/artisanlib/performance.py`
- Verify: `src/artisanlib/canvas.py`
- Verify: `src/artisanlib/main.py`
- Verify: `docs/GUI_MODERNIZATION_BASELINE.md`

**Interfaces:**
- Consumes: implementation from Tasks 1-4.
- Produces: a verified Phase 0 baseline-ready branch state.

- [x] **Step 1: Run focused ArtisanZ custom-feature check**

Run:

```bash
cd src
.venv/bin/python -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py artisanlib/performance.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_performance.py test/unitary/artisanlib/test_canvas.py -q
```

Expected: PASS.

- [x] **Step 2: Run style check for touched Python files**

Run:

```bash
cd src
.venv/bin/python -m ruff check artisanlib/performance.py artisanlib/canvas.py artisanlib/main.py test/unitary/artisanlib/test_performance.py
```

Expected: PASS.

- [x] **Step 3: Confirm disabled-by-default behavior**

Run:

```bash
cd src
.venv/bin/python - <<'PY'
from artisanlib.performance import gui_perf_enabled
print(gui_perf_enabled())
PY
```

Expected:

```text
False
```

- [x] **Step 4: Confirm enabled behavior**

Run:

```bash
cd src
ARTISANZ_GUI_PERF=1 .venv/bin/python - <<'PY'
from artisanlib.performance import get_gui_perf_recorder, gui_perf_enabled, gui_perf_count
print(gui_perf_enabled())
gui_perf_count("probe.enabled")
print(get_gui_perf_recorder().summary_lines()[0])
PY
```

Expected:

```text
True
probe.enabled: count=1 total_ms=0.000 avg_ms=0.000 max_ms=0.000
```

- [x] **Step 5: Review final diff without committing**

Run:

```bash
git status --short
git diff --stat
```

Expected: only Phase 0 performance instrumentation, tests, and docs are changed.

## Self-Review Notes

- Spec coverage: Phase 0 covers disabled-by-default probes, hot path timings, lock skip counters, optional export, baseline instructions, and focused verification.
- Placeholder scan: This plan intentionally avoids open placeholders. Future benchmark result rows are represented as an initial "Not yet run" row in the baseline document.
- Type consistency: Public helper names are defined in Task 1 and reused consistently in later tasks.
- Project rule override: The writing-plans skill normally includes commit steps, but ArtisanZ AGENTS requires no commits unless explicitly requested. The original plan used git status/diff review steps; this execution was explicitly authorized for automatic commit.

## Phase 0 Execution Result

- Implemented disabled-by-default GUI performance instrumentation in `src/artisanlib/performance.py`.
- Added timing probes to `canvas.updateBackground`, `canvas.sample_processing`, `canvas.updategraphics`, `canvas.redraw_keep_view`, and `canvas.redraw`.
- Added skip counters for `canvas.updateBackground.skip`, `canvas.sample_processing.lock_skip`, and `canvas.updategraphics.lock_skip`.
- Added automatic/default JSONL export from `ApplicationWindow.stopActivities()` plus `atexit` fallback.
- Added follow-up JSONL summary utility in `src/artisanlib/performance_report.py`.
- Added automated profile redraw autorun for repeatable local GUI performance checks.
- Added unit coverage in `src/test/unitary/artisanlib/test_performance.py`.
- Verified focused ArtisanZ charge-target and canvas tests on Python 3.14.5 from `src/.venv`.
- Automated profile redraw data supports starting Phase 1. Live sampling scenarios remain required before approving renderer or threading changes.
