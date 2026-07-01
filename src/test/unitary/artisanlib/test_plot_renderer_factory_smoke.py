from __future__ import annotations

import json
import os
from pathlib import Path

from artisanlib.plot_renderer_factory_smoke import (
    build_factory_smoke_snapshot,
    main,
    result_to_dict,
    smoke_renderer_factory,
)
from artisanlib.plot_renderer_plugin_loader import ARTISANZ_RENDERER_PLUGIN_PATH
from artisanlib.plot_renderer_registry import RendererPluginRegistry, RendererPluginSpec
from artisanlib.plot_snapshot import AxisSnapshot, RendererViewState

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def test_build_factory_smoke_snapshot_uses_renderer_benchmark_workload() -> None:
    snapshot = build_factory_smoke_snapshot(point_count=24, event_count=3)

    assert len(snapshot.curves) >= 5
    assert len(snapshot.events) == 3
    assert snapshot.ror_axis is not None
    assert all(len(curve.x) == 24 for curve in snapshot.curves)


def test_smoke_renderer_factory_renders_matplotlib_backend_by_id() -> None:
    snapshot = build_factory_smoke_snapshot(point_count=24, event_count=3)

    result = smoke_renderer_factory('matplotlib-snapshot', snapshot=snapshot)

    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.temperature_item_count == 4
    assert result.ror_item_count == 2
    assert result.event_item_count == 6
    assert result.png_byte_count > 1000
    assert result.view_state == RendererViewState(
        time_axis=AxisSnapshot(minimum=snapshot.time_axis.minimum, maximum=snapshot.time_axis.maximum, label='Time'),
        temperature_axis=AxisSnapshot(
            minimum=snapshot.temperature_axis.minimum,
            maximum=snapshot.temperature_axis.maximum,
            label='Temperature',
        ),
        ror_axis=AxisSnapshot(
            minimum=snapshot.ror_axis.minimum,
            maximum=snapshot.ror_axis.maximum,
            label='RoR',
        ),
    )


def test_smoke_renderer_factory_renders_pyqtgraph_backend_by_id() -> None:
    snapshot = build_factory_smoke_snapshot(point_count=24, event_count=3)

    result = smoke_renderer_factory('pyqtgraph-snapshot', snapshot=snapshot, use_opengl=False)

    assert result.renderer_id == 'pyqtgraph-snapshot'
    assert result.temperature_item_count == 4
    assert result.ror_item_count == 2
    assert result.event_item_count == 6
    assert result.png_byte_count == 0
    assert result.opengl_requested is False
    assert result.view_state == RendererViewState(
        time_axis=AxisSnapshot(minimum=snapshot.time_axis.minimum, maximum=snapshot.time_axis.maximum, label='Time'),
        temperature_axis=AxisSnapshot(
            minimum=snapshot.temperature_axis.minimum,
            maximum=snapshot.temperature_axis.maximum,
            label='Temperature',
        ),
        ror_axis=AxisSnapshot(
            minimum=snapshot.ror_axis.minimum,
            maximum=snapshot.ror_axis.maximum,
            label='RoR',
        ),
    )


def test_renderer_factory_smoke_results_share_backend_neutral_shape() -> None:
    snapshot = build_factory_smoke_snapshot(point_count=12, event_count=1)
    matplotlib_result = result_to_dict(smoke_renderer_factory('matplotlib-snapshot', snapshot=snapshot))
    pyqtgraph_result = result_to_dict(smoke_renderer_factory(
        'pyqtgraph-snapshot',
        snapshot=snapshot,
        use_opengl=False,
    ))

    assert set(matplotlib_result) == set(pyqtgraph_result)
    assert matplotlib_result['renderer_id'] == 'matplotlib-snapshot'
    assert pyqtgraph_result['renderer_id'] == 'pyqtgraph-snapshot'


def test_smoke_renderer_factory_supports_external_registry_plugin_id() -> None:
    snapshot = build_factory_smoke_snapshot(point_count=16, event_count=2)
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='external-matplotlib-smoke',
            label='External Matplotlib Smoke',
            description='External renderer id using a Matplotlib-compatible surface.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('matplotlib',),
        ),
    ))

    result = smoke_renderer_factory(
        'external-matplotlib-smoke',
        snapshot=snapshot,
        registry=registry,
    )

    assert result.renderer_id == 'external-matplotlib-smoke'
    assert result.temperature_item_count == 4
    assert result.ror_item_count == 2
    assert result.event_item_count == 4
    assert result.png_byte_count > 1000


def test_renderer_factory_smoke_cli_uses_runtime_registry_for_external_id(
        tmp_path: Path,
        monkeypatch,
        capsys) -> None:
    _write_plugin(
        tmp_path,
        'cli_matplotlib.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='cli-filesystem-matplotlib',
        label='CLI Filesystem Matplotlib',
        description='Filesystem plugin selected through the smoke CLI.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
    ),)
""",
    )
    monkeypatch.setenv(ARTISANZ_RENDERER_PLUGIN_PATH, str(tmp_path))

    assert main(['--renderer', 'cli-filesystem-matplotlib', '--points', '16', '--events', '2']) == 0

    output = json.loads(capsys.readouterr().out)
    assert output['renderer_id'] == 'cli-filesystem-matplotlib'
    assert output['temperature_item_count'] == 4
    assert output['ror_item_count'] == 2
    assert output['event_item_count'] == 4
    assert output['png_byte_count'] > 1000


def test_smoke_renderer_factory_default_registry_ignores_ambient_external_plugins(
        tmp_path: Path,
        monkeypatch) -> None:
    _write_plugin(
        tmp_path,
        'ambient_duplicate.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='matplotlib-snapshot',
        label='Ambient Duplicate',
        description='Should not affect direct smoke calls.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
    ),)
""",
    )
    monkeypatch.setenv(ARTISANZ_RENDERER_PLUGIN_PATH, str(tmp_path))
    snapshot = build_factory_smoke_snapshot(point_count=16, event_count=2)

    result = smoke_renderer_factory('matplotlib-snapshot', snapshot=snapshot)

    assert result.renderer_id == 'matplotlib-snapshot'
    assert result.temperature_item_count == 4
    assert result.event_item_count == 4


def test_renderer_factory_smoke_cli_reports_unknown_renderer_cleanly(capsys) -> None:
    try:
        main(['--renderer', 'unknown-renderer'])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError('expected argparse SystemExit for unknown renderer id')

    captured = capsys.readouterr()
    assert 'unknown renderer plugin: unknown-renderer' in captured.err


def _write_plugin(directory: Path, filename: str, body: str) -> Path:
    plugin_file = directory / filename
    plugin_file.write_text(body.lstrip(), encoding='utf-8')
    return plugin_file
