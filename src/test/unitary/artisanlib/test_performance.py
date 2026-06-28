import json
import time

from artisanlib import performance
from artisanlib.performance import (
    GuiPerfRecorder,
    gui_perf_count,
    gui_perf_enabled,
    gui_perf_span,
    gui_perf_tracked,
)


def test_recorder_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv('ARTISANZ_GUI_PERF', raising=False)

    assert gui_perf_enabled() is False


def test_recorder_records_span_when_enabled() -> None:
    recorder = GuiPerfRecorder(enabled=True)

    with recorder.span('updategraphics'):
        time.sleep(0.001)

    snapshot = recorder.snapshot()
    assert snapshot['updategraphics']['count'] == 1
    assert snapshot['updategraphics']['total_ms'] > 0
    assert snapshot['updategraphics']['max_ms'] > 0


def test_recorder_counts_events() -> None:
    recorder = GuiPerfRecorder(enabled=True)

    recorder.count('updategraphics.lock_skip')
    recorder.count('updategraphics.lock_skip', amount=2)

    snapshot = recorder.snapshot()
    assert snapshot['updategraphics.lock_skip']['count'] == 3
    assert snapshot['updategraphics.lock_skip']['total_ms'] == 0


def test_summary_lines_are_stable() -> None:
    recorder = GuiPerfRecorder(enabled=True)
    recorder.count('sample_processing.lock_skip')

    lines = recorder.summary_lines()

    assert lines == [
        'sample_processing.lock_skip: count=1 total_ms=0.000 avg_ms=0.000 max_ms=0.000',
    ]


def test_jsonl_export(tmp_path) -> None:
    recorder = GuiPerfRecorder(enabled=True)
    recorder.count('redraw.full')
    output = tmp_path / 'gui-perf.jsonl'

    recorder.write_jsonl(output)

    rows = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]
    assert rows == [
        {
            'name': 'redraw.full',
            'count': 1,
            'total_ms': 0,
            'avg_ms': 0,
            'max_ms': 0,
        },
    ]


def test_export_path_comes_from_environment(monkeypatch, tmp_path) -> None:
    output = tmp_path / 'artisan-gui-perf.jsonl'
    monkeypatch.setenv('ARTISANZ_GUI_PERF_FILE', str(output))

    from artisanlib.performance import gui_perf_export_path

    assert gui_perf_export_path() == output


def test_module_helpers_are_noops_when_disabled(monkeypatch) -> None:
    monkeypatch.delenv('ARTISANZ_GUI_PERF', raising=False)

    with gui_perf_span('disabled.span'):
        pass
    gui_perf_count('disabled.count')

    assert gui_perf_enabled() is False


def test_tracked_decorator_records_call(monkeypatch) -> None:
    recorder = GuiPerfRecorder(enabled=True)
    monkeypatch.setattr(performance, '_RECORDER', recorder)

    @gui_perf_tracked('decorated.call')
    def decorated() -> str:
        return 'ok'

    assert decorated() == 'ok'
    assert recorder.snapshot()['decorated.call']['count'] == 1
