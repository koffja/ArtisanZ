from __future__ import annotations

from dataclasses import dataclass

from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer
from artisanlib.plot_snapshot import RendererViewState, RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class PyQtGraphSmokeRenderResult:
    view_state: RendererViewState
    temperature_item_count: int
    ror_item_count: int
    event_item_count: int
    opengl_requested: bool


def render_snapshot_with_pyqtgraph(
        snapshot: RoastPlotSnapshot,
        *,
        use_opengl: bool = True) -> PyQtGraphSmokeRenderResult:
    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]

    application = QApplication.instance() or QApplication([])
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    pg.setConfigOptions(useOpenGL=use_opengl)
    temperature_plot = pg.PlotWidget()
    ror_plot = pg.PlotWidget() if snapshot.ror_axis is not None else None
    try:
        renderer = PyQtGraphSnapshotRenderer(
            temperature_plot=temperature_plot,
            ror_plot=ror_plot,
        )
        renderer.set_snapshot(snapshot)
        application.processEvents()
        return PyQtGraphSmokeRenderResult(
            view_state=renderer.export_view_state(),
            temperature_item_count=_plot_data_item_count(temperature_plot),
            ror_item_count=0 if ror_plot is None else _plot_data_item_count(ror_plot),
            event_item_count=renderer.event_item_count(),
            opengl_requested=use_opengl,
        )
    finally:
        temperature_plot.close()
        if ror_plot is not None:
            ror_plot.close()
        pg.setConfigOptions(useOpenGL=previous_opengl)


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


__all__ = ['PyQtGraphSmokeRenderResult', 'render_snapshot_with_pyqtgraph']
