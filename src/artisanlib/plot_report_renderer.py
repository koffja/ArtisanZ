"""Guarded renderer selection for the roast report's main graph asset."""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from artisanlib.plot_pyqtgraph_export import PyQtGraphSnapshotPngResult, export_pyqtgraph_snapshot_png
from artisanlib.plot_snapshot_extractor import build_roast_plot_snapshot

ReportGraphRendererId = Literal['matplotlib', 'pyqtgraph']
REPORT_GRAPH_RENDERER_ENV: Final[str] = 'ARTISANZ_REPORT_GRAPH_RENDERER'


@dataclass(frozen=True, slots=True)
class ReportGraphRenderResult:
    backend: ReportGraphRendererId
    path: str
    fallback_reason: str | None = None


def report_graph_renderer_id(
        source: object,
        *,
        env_value: str | None = None) -> ReportGraphRendererId:
    """Resolve the report graph backend without changing the normal default."""
    configured = getattr(source, 'report_graph_renderer', None)
    if configured is None:
        configured = env_value if env_value is not None else os.environ.get(REPORT_GRAPH_RENDERER_ENV)
    normalized = str(configured or '').strip().lower()
    return 'pyqtgraph' if normalized in {'pyqtgraph', 'pyqtgraph-snapshot'} else 'matplotlib'


def export_pyqtgraph_report_graph(
        source: object,
        output_path: str | Path,
        *,
        width: int = 1280,
        height: int = 720,
        use_opengl: bool = False) -> PyQtGraphSnapshotPngResult:
    """Export the current canvas snapshot for embedding in the report."""
    return export_pyqtgraph_snapshot_png(
        build_roast_plot_snapshot(source),
        output_path,
        width=width,
        height=height,
        use_opengl=use_opengl,
    )


def render_report_graph(
        source: object,
        output_dir: str | Path,
        *,
        matplotlib_export: Callable[[str], None],
        width: int = 1280,
        height: int = 720,
        use_opengl: bool = False,
        prefix: str = 'roastlog-graph') -> ReportGraphRenderResult:
    """Render the report graph and keep Matplotlib as the compatibility fallback."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    if report_graph_renderer_id(source) == 'pyqtgraph':
        pyqtgraph_path = output_path / f'{prefix}.png'
        try:
            result = export_pyqtgraph_report_graph(
                source,
                pyqtgraph_path,
                width=width,
                height=height,
                use_opengl=use_opengl,
            )
            if result.byte_count <= 0 or result.sampled_non_background_pixel_count <= 0:
                raise RuntimeError('PyQtGraph report graph export was blank')
            return ReportGraphRenderResult('pyqtgraph', str(pyqtgraph_path))
        except Exception as exc: # pylint: disable=broad-except
            fallback_reason = f'{type(exc).__name__}: {exc}'
    else:
        fallback_reason = None

    matplotlib_path = output_path / f'{prefix}.svg'
    matplotlib_export(str(matplotlib_path))
    return ReportGraphRenderResult('matplotlib', str(matplotlib_path), fallback_reason)


__all__ = [
    'REPORT_GRAPH_RENDERER_ENV',
    'ReportGraphRenderResult',
    'ReportGraphRendererId',
    'export_pyqtgraph_report_graph',
    'render_report_graph',
    'report_graph_renderer_id',
]
