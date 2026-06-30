from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import argparse
import json
import math
import time

from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, EventMarkerSnapshot, RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class PlotRendererBenchmarkMeasurement:
    name: str
    iterations: int
    total_seconds: float
    average_seconds: float
    temperature_item_count: int
    ror_item_count: int
    event_item_count: int
    opengl_requested: bool | None = None
    opengl_widget_supported: bool | None = None


@dataclass(frozen=True, slots=True)
class PlotRendererBenchmarkReport:
    snapshot_point_count: int
    snapshot_curve_count: int
    snapshot_event_count: int
    matplotlib: PlotRendererBenchmarkMeasurement
    pyqtgraph: PlotRendererBenchmarkMeasurement


def build_renderer_benchmark_snapshot(point_count: int = 900, event_count: int = 8) -> RoastPlotSnapshot:
    if point_count < 2:
        raise ValueError('point_count must be at least 2')
    if event_count < 0:
        raise ValueError('event_count must not be negative')

    times = tuple(index * 5.0 for index in range(point_count))
    denominator = float(point_count - 1)
    progress = tuple(index / denominator for index in range(point_count))
    bt = tuple(82.0 + 138.0 * value ** 0.72 + math.sin(index / 9.0) * 1.8 for index, value in enumerate(progress))
    et = tuple(120.0 + 148.0 * value ** 0.62 + math.sin(index / 7.0) * 2.4 for index, value in enumerate(progress))
    background_bt = tuple(value - 6.0 + math.sin(index / 17.0) * 1.1 for index, value in enumerate(bt))
    target_curve = tuple(
        None if index < point_count * 0.62 else bt[index] + (index - point_count * 0.62) * 0.11
        for index in range(point_count)
    )
    delta_bt = _rate_curve(times, bt)
    delta_et = _rate_curve(times, et)

    curves = (
        CurveSnapshot.from_sequences(name='BT', x=times, y=bt, color='#4E7180', line_width=2.0),
        CurveSnapshot.from_sequences(name='ET', x=times, y=et, color='#B9685E', line_width=2.0),
        CurveSnapshot.from_sequences(
            name='Background BT',
            x=times,
            y=background_bt,
            color='#9AA0A6',
            line_style='--',
        ),
        CurveSnapshot.from_sequences(
            name='Target Projection',
            x=times,
            y=target_curve,
            color='#008AC5',
            line_style=':',
        ),
        CurveSnapshot.from_sequences(
            name='Delta BT',
            x=times,
            y=delta_bt,
            color='#78905D',
            y_axis='ror',
            line_style='--',
        ),
        CurveSnapshot.from_sequences(
            name='Delta ET',
            x=times,
            y=delta_et,
            color='#AA6F73',
            y_axis='ror',
            line_style='-.',
        ),
    )
    visible_target_values = tuple(value for value in target_curve if value is not None) or (bt[-1],)
    minimum_temperature = min(*bt, *background_bt)
    maximum_temperature = max(*et, *visible_target_values)
    maximum_ror = max(*delta_bt[1:], *delta_et[1:])

    return RoastPlotSnapshot(
        curves=curves,
        events=_benchmark_events(times, bt, event_count),
        time_axis=AxisSnapshot(minimum=times[0], maximum=times[-1], label='Time'),
        temperature_axis=AxisSnapshot(
            minimum=minimum_temperature - 10.0,
            maximum=maximum_temperature + 10.0,
            label='Temperature',
        ),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=maximum_ror + 5.0, label='RoR'),
    )


def benchmark_plot_renderers(
        *,
        snapshot: RoastPlotSnapshot | None = None,
        point_count: int = 900,
        event_count: int = 8,
        iterations: int = 3,
        use_opengl: bool = True,
        pyqtgraph_opengl_probe: Callable[[], bool] | None = None) -> PlotRendererBenchmarkReport:
    if iterations < 1:
        raise ValueError('iterations must be at least 1')
    benchmark_snapshot = snapshot or build_renderer_benchmark_snapshot(
        point_count=point_count,
        event_count=event_count,
    )
    return PlotRendererBenchmarkReport(
        snapshot_point_count=_snapshot_point_count(benchmark_snapshot),
        snapshot_curve_count=len(benchmark_snapshot.curves),
        snapshot_event_count=len(benchmark_snapshot.events),
        matplotlib=_benchmark_matplotlib(benchmark_snapshot, iterations),
        pyqtgraph=_benchmark_pyqtgraph(
            benchmark_snapshot,
            iterations,
            use_opengl,
            pyqtgraph_opengl_probe,
        ),
    )


def report_to_dict(report: PlotRendererBenchmarkReport) -> dict[str, object]:
    return asdict(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Benchmark ArtisanZ plot renderer snapshot adapters.')
    parser.add_argument('--points', type=int, default=900, help='Synthetic sample count.')
    parser.add_argument('--events', type=int, default=8, help='Synthetic foreground event count.')
    parser.add_argument('--iterations', type=int, default=3, help='Render iterations per backend.')
    parser.add_argument('--no-opengl', action='store_true', help='Disable PyQtGraph OpenGL request.')
    args = parser.parse_args(argv)

    report = benchmark_plot_renderers(
        point_count=args.points,
        event_count=args.events,
        iterations=args.iterations,
        use_opengl=not args.no_opengl,
    )
    print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _rate_curve(times: tuple[float, ...], values: tuple[float, ...]) -> tuple[float | None, ...]:
    rates: list[float | None] = [None]
    for index in range(1, len(values)):
        timed = times[index] - times[index - 1]
        rates.append(((values[index] - values[index - 1]) / timed) * 60.0)
    return tuple(rates)


def _benchmark_events(
        times: tuple[float, ...],
        bt: tuple[float, ...],
        event_count: int) -> tuple[EventMarkerSnapshot, ...]:
    labels = ('CHARGE', 'TP', 'DRY', 'FCs', 'DROP', 'FCe', 'SCs', 'SCe')
    events: list[EventMarkerSnapshot] = []
    for event_index in range(event_count):
        point_index = min(
            len(times) - 1,
            max(0, round(((event_index + 1) / (event_count + 1)) * (len(times) - 1))),
        )
        events.append(EventMarkerSnapshot(
            time=times[point_index],
            label=labels[event_index % len(labels)],
            event_type=event_index,
            color='#CC0000',
            value=bt[point_index],
        ))
    return tuple(events)


def _benchmark_matplotlib(
        snapshot: RoastPlotSnapshot,
        iterations: int) -> PlotRendererBenchmarkMeasurement:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(4.0, 3.0), dpi=100)
    canvas = FigureCanvasAgg(figure)
    temperature_axis = figure.add_subplot(111)
    ror_axis = temperature_axis.twinx() if snapshot.ror_axis is not None else None
    renderer = MatplotlibSnapshotRenderer(
        temperature_axis=temperature_axis,
        ror_axis=ror_axis,
        draw_idle=False,
    )

    total_seconds = _time_iterations(lambda: _render_matplotlib(renderer, snapshot, canvas.draw), iterations)
    return PlotRendererBenchmarkMeasurement(
        name='matplotlib',
        iterations=iterations,
        total_seconds=total_seconds,
        average_seconds=total_seconds / iterations,
        temperature_item_count=len(temperature_axis.lines),
        ror_item_count=0 if ror_axis is None else len(ror_axis.lines),
        event_item_count=renderer.event_artist_count(),
    )


def _benchmark_pyqtgraph(
        snapshot: RoastPlotSnapshot,
        iterations: int,
        use_opengl: bool,
        opengl_probe: Callable[[], bool] | None) -> PlotRendererBenchmarkMeasurement:
    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]

    application = QApplication.instance() or QApplication([])
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    pg.setConfigOptions(useOpenGL=use_opengl)
    temperature_plot = pg.PlotWidget()
    ror_plot = pg.PlotWidget() if snapshot.ror_axis is not None else None
    try:
        opengl_widget_supported = _detect_opengl_widget_support(
            application,
            use_opengl,
            opengl_probe,
        )
        renderer = PyQtGraphSnapshotRenderer(
            temperature_plot=temperature_plot,
            ror_plot=ror_plot,
        )
        total_seconds = _time_iterations(
            lambda: _render_pyqtgraph(renderer, snapshot, application.processEvents),
            iterations,
        )
        return PlotRendererBenchmarkMeasurement(
            name='pyqtgraph',
            iterations=iterations,
            total_seconds=total_seconds,
            average_seconds=total_seconds / iterations,
            temperature_item_count=_plot_data_item_count(temperature_plot),
            ror_item_count=0 if ror_plot is None else _plot_data_item_count(ror_plot),
            event_item_count=renderer.event_item_count(),
            opengl_requested=use_opengl,
            opengl_widget_supported=opengl_widget_supported,
        )
    finally:
        temperature_plot.close()
        if ror_plot is not None:
            ror_plot.close()
        pg.setConfigOptions(useOpenGL=previous_opengl)


def _render_matplotlib(
        renderer: MatplotlibSnapshotRenderer,
        snapshot: RoastPlotSnapshot,
        draw: Callable[[], object]) -> None:
    renderer.set_snapshot(snapshot)
    draw()


def _render_pyqtgraph(
        renderer: PyQtGraphSnapshotRenderer,
        snapshot: RoastPlotSnapshot,
        process_events: Callable[[], object]) -> None:
    renderer.set_snapshot(snapshot)
    process_events()


def _detect_opengl_widget_support(
        application: object,
        use_opengl: bool,
        opengl_probe: Callable[[], bool] | None) -> bool | None:
    if not use_opengl:
        return None
    probe = opengl_probe or (lambda: _qopenglwidget_supported(application))
    try:
        return bool(probe())
    except Exception:
        return False


def _qopenglwidget_supported(application: object) -> bool:
    try:
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    except ImportError:
        return False
    widget = QOpenGLWidget()
    try:
        widget.resize(1, 1)
        widget.show()
        process_events = getattr(application, 'processEvents', None)
        if callable(process_events):
            process_events()
        return bool(widget.isValid())
    finally:
        widget.close()


def _time_iterations(render: Callable[[], None], iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        render()
    return time.perf_counter() - start


def _snapshot_point_count(snapshot: RoastPlotSnapshot) -> int:
    if not snapshot.curves:
        return 0
    return max(len(curve.x) for curve in snapshot.curves)


def _plot_data_item_count(plot: object) -> int:
    list_data_items = getattr(plot, 'listDataItems', None)
    if callable(list_data_items):
        return len(list_data_items())
    get_plot_item = getattr(plot, 'getPlotItem', None)
    if callable(get_plot_item):
        plot_item = get_plot_item()
        list_data_items = getattr(plot_item, 'listDataItems', None)
        if callable(list_data_items):
            return len(list_data_items())
    return 0


__all__ = [
    'PlotRendererBenchmarkMeasurement',
    'PlotRendererBenchmarkReport',
    'benchmark_plot_renderers',
    'build_renderer_benchmark_snapshot',
    'main',
    'report_to_dict',
]


if __name__ == '__main__':
    raise SystemExit(main())
