from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
import argparse
import json
import os

from artisanlib.plot_renderer_benchmark import build_renderer_benchmark_snapshot
from artisanlib.plot_renderer_factory import create_renderer
from artisanlib.plot_renderer_registry import RendererPluginRegistry
from artisanlib.plot_snapshot import RendererViewState, RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class RendererFactorySmokeResult:
    renderer_id: str
    view_state: RendererViewState
    temperature_item_count: int
    ror_item_count: int
    event_item_count: int
    png_byte_count: int = 0
    opengl_requested: bool | None = None


def build_factory_smoke_snapshot(point_count: int = 120, event_count: int = 4) -> RoastPlotSnapshot:
    return build_renderer_benchmark_snapshot(point_count=point_count, event_count=event_count)


def smoke_renderer_factory(
        renderer_id: str,
        *,
        snapshot: RoastPlotSnapshot | None = None,
        registry: RendererPluginRegistry | None = None,
        point_count: int = 120,
        event_count: int = 4,
        use_opengl: bool = False) -> RendererFactorySmokeResult:
    smoke_snapshot = snapshot or build_factory_smoke_snapshot(
        point_count=point_count,
        event_count=event_count,
    )
    if renderer_id == 'matplotlib-snapshot':
        return _smoke_matplotlib_renderer(renderer_id, smoke_snapshot, registry)
    if renderer_id == 'pyqtgraph-snapshot':
        return _smoke_pyqtgraph_renderer(renderer_id, smoke_snapshot, registry, use_opengl)
    raise KeyError(f'unsupported renderer factory smoke id: {renderer_id}')


def result_to_dict(result: RendererFactorySmokeResult) -> dict[str, object]:
    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Smoke-test ArtisanZ renderer factory backends.')
    parser.add_argument(
        '--renderer',
        choices=('matplotlib-snapshot', 'pyqtgraph-snapshot'),
        required=True,
        help='Renderer plugin id to instantiate through the factory.')
    parser.add_argument('--points', type=int, default=120, help='Synthetic sample count.')
    parser.add_argument('--events', type=int, default=4, help='Synthetic event count.')
    parser.add_argument('--opengl', action='store_true', help='Request PyQtGraph OpenGL rendering.')
    parser.add_argument('--no-opengl', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = smoke_renderer_factory(
        args.renderer,
        point_count=args.points,
        event_count=args.events,
        use_opengl=args.opengl and not args.no_opengl,
    )
    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _smoke_matplotlib_renderer(
        renderer_id: str,
        snapshot: RoastPlotSnapshot,
        registry: RendererPluginRegistry | None) -> RendererFactorySmokeResult:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(4.0, 3.0), dpi=100)
    FigureCanvasAgg(figure)
    temperature_axis = figure.add_subplot(111)
    ror_axis = temperature_axis.twinx() if snapshot.ror_axis is not None else None
    renderer = create_renderer(
        renderer_id,
        registry=registry,
        temperature_axis=temperature_axis,
        ror_axis=ror_axis,
        draw_idle=False,
    )
    renderer.set_snapshot(snapshot)
    buffer = BytesIO()
    figure.savefig(buffer, format='png')
    return RendererFactorySmokeResult(
        renderer_id=renderer_id,
        view_state=renderer.export_view_state(),
        temperature_item_count=_renderer_curve_count(renderer, snapshot, 'temperature'),
        ror_item_count=_renderer_curve_count(renderer, snapshot, 'ror'),
        event_item_count=_event_count(renderer, 'event_artist_count'),
        png_byte_count=len(buffer.getvalue()),
    )


def _smoke_pyqtgraph_renderer(
        renderer_id: str,
        snapshot: RoastPlotSnapshot,
        registry: RendererPluginRegistry | None,
        use_opengl: bool) -> RendererFactorySmokeResult:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]

    application = QApplication.instance() or QApplication([])
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    pg.setConfigOptions(useOpenGL=use_opengl)
    temperature_plot = pg.PlotWidget()
    ror_plot = pg.PlotWidget() if snapshot.ror_axis is not None else None
    try:
        renderer = create_renderer(
            renderer_id,
            registry=registry,
            temperature_plot=temperature_plot,
            ror_plot=ror_plot,
        )
        renderer.set_snapshot(snapshot)
        application.processEvents()
        return RendererFactorySmokeResult(
            renderer_id=renderer_id,
            view_state=renderer.export_view_state(),
            temperature_item_count=_plot_data_item_count(temperature_plot),
            ror_item_count=0 if ror_plot is None else _plot_data_item_count(ror_plot),
            event_item_count=_event_count(renderer, 'event_item_count'),
            opengl_requested=use_opengl,
        )
    finally:
        temperature_plot.close()
        if ror_plot is not None:
            ror_plot.close()
        pg.setConfigOptions(useOpenGL=previous_opengl)


def _event_count(renderer: object, method_name: str) -> int:
    method = getattr(renderer, method_name, None)
    if not callable(method):
        return 0
    return int(method())


def _renderer_curve_count(renderer: object, snapshot: RoastPlotSnapshot, y_axis: str) -> int:
    line_for = getattr(renderer, 'line_for', None)
    if not callable(line_for):
        return 0
    return sum(
        1 for curve in snapshot.curves
        if curve.y_axis == y_axis and line_for(curve.name) is not None
    )


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
    'RendererFactorySmokeResult',
    'build_factory_smoke_snapshot',
    'main',
    'result_to_dict',
    'smoke_renderer_factory',
]


if __name__ == '__main__':
    raise SystemExit(main())
