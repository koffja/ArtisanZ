from __future__ import annotations

from artisanlib.plot_renderer_benchmark import benchmark_plot_renderers, build_renderer_benchmark_snapshot


def test_build_renderer_benchmark_snapshot_contains_roast_workload() -> None:
    snapshot = build_renderer_benchmark_snapshot(point_count=30, event_count=4)

    assert len(snapshot.curves) >= 5
    assert len(snapshot.events) == 4
    assert snapshot.ror_axis is not None
    assert snapshot.time_axis.maximum > snapshot.time_axis.minimum
    assert snapshot.temperature_axis.maximum > snapshot.temperature_axis.minimum
    assert all(len(curve.x) == 30 for curve in snapshot.curves)


def test_build_renderer_benchmark_snapshot_handles_minimum_point_count() -> None:
    snapshot = build_renderer_benchmark_snapshot(point_count=2, event_count=0)

    assert snapshot.events == ()
    assert all(len(curve.x) == 2 for curve in snapshot.curves)
    assert snapshot.temperature_axis.maximum > snapshot.temperature_axis.minimum


def test_benchmark_plot_renderers_reports_backend_timings() -> None:
    snapshot = build_renderer_benchmark_snapshot(point_count=24, event_count=3)

    report = benchmark_plot_renderers(snapshot=snapshot, iterations=1, use_opengl=True)

    assert report.snapshot_point_count == 24
    assert report.snapshot_curve_count == len(snapshot.curves)
    assert report.snapshot_event_count == 3
    assert report.matplotlib.name == 'matplotlib'
    assert report.matplotlib.iterations == 1
    assert report.matplotlib.total_seconds >= 0.0
    assert report.matplotlib.event_item_count == 6
    assert report.pyqtgraph.name == 'pyqtgraph'
    assert report.pyqtgraph.iterations == 1
    assert report.pyqtgraph.total_seconds >= 0.0
    assert report.pyqtgraph.opengl_requested is True
    assert report.pyqtgraph.event_item_count == 6
