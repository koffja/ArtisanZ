from __future__ import annotations

import os

from artisanlib.plot_renderer_factory_smoke import (
    build_factory_smoke_snapshot,
    result_to_dict,
    smoke_renderer_factory,
)
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
