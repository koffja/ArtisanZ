from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from artisanlib.plot_matplotlib_smoke import render_snapshot_to_png_bytes
from artisanlib.plot_pyqtgraph_export import PyQtGraphSnapshotPngResult, export_pyqtgraph_snapshot_png
from artisanlib.plot_snapshot import RendererViewState, RoastPlotSnapshot
from artisanlib.websocket_renderer_smoke import collect_websocket_stream, build_snapshot_from_websocket_stream


@dataclass(frozen=True, slots=True)
class MatplotlibExportEvidence:
    path: str
    byte_count: int
    temperature_line_count: int
    ror_line_count: int
    event_artist_count: int
    phase_artist_count: int
    area_artist_count: int
    event_value_artist_count: int
    guide_artist_count: int
    view_state: RendererViewState


@dataclass(frozen=True, slots=True)
class PlotExportParityResult:
    output_dir: str
    prefix: str
    view_state_matches: bool
    view_state_within_tolerance: bool
    view_state_max_delta: float
    matplotlib: MatplotlibExportEvidence
    pyqtgraph: PyQtGraphSnapshotPngResult
    event_count: int
    event_value_count: int
    phase_band_count: int
    guide_count: int
    area_count: int


def run_websocket_export_parity_smoke(
        *,
        sample_count: int = 24,
        fixed_step_ms: float = 15_000.0,
        scenario: str = 'event-heavy',
        output_dir: str | Path = '/tmp/artisanz-export-parity',
        prefix: str | None = None,
        width: int = 1280,
        height: int = 720,
        dpi: int = 100,
        use_opengl: bool = False) -> PlotExportParityResult:
    capture = asyncio.run(collect_websocket_stream(
        sample_count=sample_count,
        fixed_step_ms=fixed_step_ms,
        scenario=scenario,
    ))
    snapshot = build_snapshot_from_websocket_stream(capture.samples, capture.events)
    export_prefix = prefix or f'websocket-{scenario}'
    return render_snapshot_export_parity(
        snapshot,
        output_dir=output_dir,
        prefix=export_prefix,
        width=width,
        height=height,
        dpi=dpi,
        use_opengl=use_opengl,
    )


def render_snapshot_export_parity(
        snapshot: RoastPlotSnapshot,
        *,
        output_dir: str | Path,
        prefix: str = 'snapshot',
        width: int = 1280,
        height: int = 720,
        dpi: int = 100,
        use_opengl: bool = False) -> PlotExportParityResult:
    if width <= 0 or height <= 0:
        raise ValueError(f'export size must be positive, got {width}x{height}')
    if dpi <= 0:
        raise ValueError(f'dpi must be positive, got {dpi}')

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_prefix = _safe_file_prefix(prefix)
    matplotlib_path = directory / f'{safe_prefix}-matplotlib.png'
    pyqtgraph_path = directory / f'{safe_prefix}-pyqtgraph.png'

    matplotlib_result = render_snapshot_to_png_bytes(
        snapshot,
        width=width / dpi,
        height=height / dpi,
        dpi=dpi,
    )
    matplotlib_path.write_bytes(matplotlib_result.png_bytes)
    pyqtgraph_result = export_pyqtgraph_snapshot_png(
        snapshot,
        pyqtgraph_path,
        width=width,
        height=height,
        use_opengl=use_opengl,
    )

    matplotlib_evidence = MatplotlibExportEvidence(
        path=str(matplotlib_path),
        byte_count=matplotlib_path.stat().st_size,
        temperature_line_count=matplotlib_result.temperature_line_count,
        ror_line_count=matplotlib_result.ror_line_count,
        event_artist_count=matplotlib_result.event_artist_count,
        phase_artist_count=matplotlib_result.phase_artist_count,
        area_artist_count=matplotlib_result.area_artist_count,
        event_value_artist_count=matplotlib_result.event_value_artist_count,
        guide_artist_count=matplotlib_result.guide_artist_count,
        view_state=matplotlib_result.view_state,
    )
    return PlotExportParityResult(
        output_dir=str(directory),
        prefix=safe_prefix,
        view_state_matches=matplotlib_result.view_state == pyqtgraph_result.view_state,
        view_state_within_tolerance=_view_state_within_tolerance(
            matplotlib_result.view_state,
            pyqtgraph_result.view_state,
        ),
        view_state_max_delta=_view_state_max_delta(matplotlib_result.view_state, pyqtgraph_result.view_state),
        matplotlib=matplotlib_evidence,
        pyqtgraph=pyqtgraph_result,
        event_count=len(snapshot.events),
        event_value_count=len(snapshot.event_values),
        phase_band_count=len(snapshot.phase_bands),
        guide_count=len(snapshot.guides),
        area_count=len(snapshot.areas),
    )


def result_to_dict(result: PlotExportParityResult) -> dict[str, object]:
    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Export the same roast snapshot through Matplotlib and PyQtGraph for parity evidence.')
    parser.add_argument('--samples', type=int, default=24, help='Number of WebSocket getData samples to request.')
    parser.add_argument('--fixed-step-ms', type=float, default=15_000.0, help='Virtual milliseconds per request.')
    parser.add_argument(
        '--scenario',
        choices=('standard', 'event-heavy'),
        default='event-heavy',
        help='Virtual roast event scenario to replay.')
    parser.add_argument('--output-dir', default='/tmp/artisanz-export-parity', help='Directory for exported PNG files.')
    parser.add_argument('--prefix', default=None, help='Optional file prefix for exported PNG files.')
    parser.add_argument('--width', type=int, default=1280, help='Export width in pixels.')
    parser.add_argument('--height', type=int, default=720, help='Export height in pixels.')
    parser.add_argument('--dpi', type=int, default=100, help='Matplotlib export DPI used to match pixel size.')
    parser.add_argument('--opengl', action='store_true', help='Request PyQtGraph OpenGL rendering.')
    args = parser.parse_args(argv)

    result = run_websocket_export_parity_smoke(
        sample_count=args.samples,
        fixed_step_ms=args.fixed_step_ms,
        scenario=args.scenario,
        output_dir=args.output_dir,
        prefix=args.prefix,
        width=args.width,
        height=args.height,
        dpi=args.dpi,
        use_opengl=args.opengl,
    )
    print(json.dumps(result_to_dict(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _safe_file_prefix(prefix: str) -> str:
    safe = ''.join(character if character.isalnum() or character in {'-', '_'} else '-' for character in prefix)
    return safe.strip('-_') or 'snapshot'


def _view_state_within_tolerance(
        left: RendererViewState,
        right: RendererViewState,
        *,
        tolerance: float = 2.0) -> bool:
    return _view_state_max_delta(left, right) <= tolerance


def _view_state_max_delta(left: RendererViewState, right: RendererViewState) -> float:
    deltas = [
        abs(left.time_axis.minimum - right.time_axis.minimum),
        abs(left.time_axis.maximum - right.time_axis.maximum),
        abs(left.temperature_axis.minimum - right.temperature_axis.minimum),
        abs(left.temperature_axis.maximum - right.temperature_axis.maximum),
    ]
    if left.ror_axis is None and right.ror_axis is None:
        return max(deltas)
    if left.ror_axis is None or right.ror_axis is None:
        return float('inf')
    deltas.extend((
        abs(left.ror_axis.minimum - right.ror_axis.minimum),
        abs(left.ror_axis.maximum - right.ror_axis.maximum),
    ))
    return max(deltas)


__all__ = [
    'MatplotlibExportEvidence',
    'PlotExportParityResult',
    'main',
    'render_snapshot_export_parity',
    'result_to_dict',
    'run_websocket_export_parity_smoke',
]


if __name__ == '__main__':
    raise SystemExit(main())
