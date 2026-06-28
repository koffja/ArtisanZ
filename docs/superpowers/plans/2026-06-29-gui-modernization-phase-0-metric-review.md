# GUI Modernization Phase 0 Metric Review Follow-Up

**Status:** Implemented and verified on 2026-06-29.

## Reason

Phase 0 instrumentation can write JSONL metrics at Artisan shutdown. The next practical need is a repeatable way to inspect those metrics without opening a notebook or writing ad hoc parsing commands.

## Scope

- Add a pure-Python JSONL summary module.
- Keep it independent from PyQt6 and Matplotlib.
- Sort metrics by `max_ms`, `avg_ms`, `total_ms`, or `count`.
- Document the command in `docs/GUI_MODERNIZATION_BASELINE.md`.

## Tasks

- [x] Add tests for JSONL loading, sorting, limiting, empty output, and CLI printing.
- [x] Add `src/artisanlib/performance_report.py`.
- [x] Update baseline instructions with the summary command.
- [x] Run focused tests and lint for the new module.

## Verification

```bash
cd src
.venv/bin/python -m py_compile artisanlib/performance_report.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance_report.py -q
.venv/bin/python -m ruff check artisanlib/performance_report.py test/unitary/artisanlib/test_performance_report.py
```

## Next Gate

Run Artisan with:

```bash
cd src
ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-gui-perf.jsonl .venv/bin/python artisan.py
```

Then summarize:

```bash
cd src
.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf.jsonl --sort-by max_ms --limit 10
```

Record results in `docs/GUI_MODERNIZATION_BASELINE.md` before approving renderer or GUI-thread processing changes.
