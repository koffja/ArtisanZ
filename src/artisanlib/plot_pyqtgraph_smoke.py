from __future__ import annotations

from dataclasses import dataclass

from artisanlib.plot_pyqtgraph_widget import create_pyqtgraph_plot_target
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

    application = QApplication.instance() or QApplication([])
    target = create_pyqtgraph_plot_target(
        use_opengl=use_opengl,
        include_ror=snapshot.ror_axis is not None,
    )
    try:
        target.renderer.set_snapshot(snapshot)
        application.processEvents()
        target.renderer.reset_view(snapshot.export_view_state())
        application.processEvents()
        return PyQtGraphSmokeRenderResult(
            view_state=target.renderer.export_view_state(),
            temperature_item_count=_plot_data_item_count(target.temperature_plot),
            ror_item_count=0 if target.ror_plot is None else _plot_data_item_count(target.ror_plot),
            event_item_count=target.renderer.event_item_count(),
            opengl_requested=use_opengl,
        )
    finally:
        target.close()


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
