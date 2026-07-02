from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer


@dataclass(slots=True)
class PyQtGraphPlotTarget:
    widget: object
    temperature_plot: object
    ror_plot: object | None
    renderer: PyQtGraphSnapshotRenderer
    opengl_requested: bool
    _previous_opengl: bool
    _pyqtgraph: Any

    def close(self) -> None:
        close_widget = getattr(self.widget, 'close', None)
        if callable(close_widget):
            close_widget()
        self._pyqtgraph.setConfigOptions(useOpenGL=self._previous_opengl)


def create_pyqtgraph_plot_target(
        *,
        use_opengl: bool = True,
        include_ror: bool = True) -> PyQtGraphPlotTarget:
    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]

    QApplication.instance() or QApplication([])
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    pg.setConfigOptions(useOpenGL=use_opengl)
    pg.setConfigOptions(antialias=True)

    widget = pg.GraphicsLayoutWidget()
    _call_if_available(widget, 'setBackground', '#F8F7F1')
    temperature_plot = widget.addPlot(row=0, col=0)
    _configure_temperature_plot(temperature_plot, pg)
    ror_plot = None
    if include_ror:
        ror_plot = widget.addPlot(row=1, col=0)
        _configure_ror_plot(ror_plot, temperature_plot, pg)

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
    )
    return PyQtGraphPlotTarget(
        widget=widget,
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        renderer=renderer,
        opengl_requested=use_opengl,
        _previous_opengl=previous_opengl,
        _pyqtgraph=pg,
    )


def _configure_temperature_plot(plot: object, pg: Any) -> None:
    _configure_plot_surface(plot, pg)
    _call_if_available(plot, 'setLabel', 'left', 'Temperature')
    _call_if_available(plot, 'setLabel', 'bottom', 'Time')


def _configure_ror_plot(plot: object, temperature_plot: object, pg: Any) -> None:
    _configure_plot_surface(plot, pg)
    _call_if_available(plot, 'setLabel', 'left', 'RoR')
    _call_if_available(plot, 'setLabel', 'bottom', 'Time')
    _call_if_available(plot, 'setXLink', temperature_plot)


def _configure_plot_surface(plot: object, pg: Any) -> None:
    _call_if_available(plot, 'showGrid', x=True, y=True, alpha=0.16)
    _call_if_available(plot, 'setMenuEnabled', False)
    view_box = getattr(plot, 'getViewBox', lambda: None)()
    _call_if_available(view_box, 'setBackgroundColor', '#F8F7F1')
    axis_pen = pg.mkPen('#C9D2D4', width=1)
    text_pen = pg.mkPen('#5E6B6E', width=1)
    for axis_name in ('left', 'bottom'):
        axis = getattr(plot, 'getAxis', lambda _: None)(axis_name)
        _call_if_available(axis, 'setPen', axis_pen)
        _call_if_available(axis, 'setTextPen', text_pen)


def _call_if_available(target: object, method_name: str, *args: object, **kwargs: object) -> None:
    method = getattr(target, method_name, None)
    if callable(method):
        method(*args, **kwargs)


__all__ = [
    'PyQtGraphPlotTarget',
    'create_pyqtgraph_plot_target',
]
