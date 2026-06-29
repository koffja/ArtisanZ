from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_snapshot import RendererViewState, RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class MatplotlibSmokeRenderResult:
    png_bytes: bytes
    view_state: RendererViewState
    temperature_line_count: int
    ror_line_count: int


def render_snapshot_to_png_bytes(
        snapshot: RoastPlotSnapshot,
        *,
        width: float = 4.0,
        height: float = 3.0,
        dpi: int = 100) -> MatplotlibSmokeRenderResult:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(width, height), dpi=dpi)
    FigureCanvasAgg(figure)
    temperature_axis = figure.add_subplot(111)
    ror_axis = temperature_axis.twinx() if snapshot.ror_axis is not None else None
    renderer = MatplotlibSnapshotRenderer(
        temperature_axis=temperature_axis,
        ror_axis=ror_axis,
        draw_idle=False,
    )

    renderer.set_snapshot(snapshot)
    buffer = BytesIO()
    figure.savefig(buffer, format='png')

    return MatplotlibSmokeRenderResult(
        png_bytes=buffer.getvalue(),
        view_state=renderer.export_view_state(),
        temperature_line_count=len(temperature_axis.lines),
        ror_line_count=0 if ror_axis is None else len(ror_axis.lines),
    )


__all__ = ['MatplotlibSmokeRenderResult', 'render_snapshot_to_png_bytes']
