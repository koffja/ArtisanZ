from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from artisanlib.plot_export_parity_smoke import PlotExportParityResult, render_snapshot_export_parity
from artisanlib.plot_profile_snapshot import load_profile_snapshot
from artisanlib.util import path2url


@dataclass(frozen=True, slots=True)
class ReportGraphAsset:
    backend: str
    path: str
    url: str
    width: int
    height: int
    byte_count: int
    sampled_non_background_pixel_count: int | None


@dataclass(frozen=True, slots=True)
class ReportGraphExportComparison:
    source_kind: str
    source_path: str
    title: str
    sample_count: int
    output_dir: str
    prefix: str
    matplotlib: ReportGraphAsset
    pyqtgraph: ReportGraphAsset
    view_state_matches: bool
    view_state_within_tolerance: bool
    view_state_max_delta: float
    event_count: int
    event_value_count: int
    phase_band_count: int
    guide_count: int
    area_count: int


def export_saved_profile_report_graph_comparison(
        profile_path: str | Path,
        *,
        output_dir: str | Path = '/tmp/artisanz-report-graph-export',
        prefix: str | None = None,
        width: int = 1280,
        height: int = 720,
        dpi: int = 100,
        use_opengl: bool = False,
        cache_buster: int | None = None) -> ReportGraphExportComparison:
    profile_result = load_profile_snapshot(profile_path)
    safe_prefix = prefix or f'{Path(profile_path).stem}-report-graph'
    parity = render_snapshot_export_parity(
        profile_result.snapshot,
        source_kind='profile',
        source_path=profile_result.path,
        sample_count=profile_result.sample_count,
        output_dir=output_dir,
        prefix=safe_prefix,
        width=width,
        height=height,
        dpi=dpi,
        use_opengl=use_opengl,
    )
    return report_graph_comparison_from_parity(
        parity,
        title=profile_result.title,
        width=width,
        height=height,
        cache_buster=cache_buster,
    )


def report_graph_comparison_from_parity(
        parity: PlotExportParityResult,
        *,
        title: str = '',
        width: int,
        height: int,
        cache_buster: int | None = None) -> ReportGraphExportComparison:
    if parity.source_kind != 'profile' or parity.source_path is None:
        raise ValueError('report graph comparison requires a saved profile source')
    return ReportGraphExportComparison(
        source_kind=parity.source_kind,
        source_path=parity.source_path,
        title=title,
        sample_count=parity.sample_count,
        output_dir=parity.output_dir,
        prefix=parity.prefix,
        matplotlib=ReportGraphAsset(
            backend='matplotlib',
            path=parity.matplotlib.path,
            url=report_graph_image_url(parity.matplotlib.path, cache_buster=cache_buster),
            width=width,
            height=height,
            byte_count=parity.matplotlib.byte_count,
            sampled_non_background_pixel_count=None,
        ),
        pyqtgraph=ReportGraphAsset(
            backend='pyqtgraph',
            path=parity.pyqtgraph.path,
            url=report_graph_image_url(parity.pyqtgraph.path, cache_buster=cache_buster),
            width=parity.pyqtgraph.width,
            height=parity.pyqtgraph.height,
            byte_count=parity.pyqtgraph.byte_count,
            sampled_non_background_pixel_count=parity.pyqtgraph.sampled_non_background_pixel_count,
        ),
        view_state_matches=parity.view_state_matches,
        view_state_within_tolerance=parity.view_state_within_tolerance,
        view_state_max_delta=parity.view_state_max_delta,
        event_count=parity.event_count,
        event_value_count=parity.event_value_count,
        phase_band_count=parity.phase_band_count,
        guide_count=parity.guide_count,
        area_count=parity.area_count,
    )


def report_graph_image_url(path: str | Path, *, cache_buster: int | None = None) -> str:
    url = path2url(str(Path(path).resolve()))
    if cache_buster is None:
        return url
    return f'{url}?dummy={cache_buster}'


def comparison_to_dict(comparison: ReportGraphExportComparison) -> dict[str, object]:
    return asdict(comparison)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Compare Matplotlib and PyQtGraph report graph image assets for a saved profile.')
    parser.add_argument('profile_file', help='Saved Artisan .alog profile to compare.')
    parser.add_argument(
        '--output-dir',
        default='/tmp/artisanz-report-graph-export',
        help='Directory for generated report graph image assets.')
    parser.add_argument('--prefix', default=None, help='Optional file prefix for generated assets.')
    parser.add_argument('--width', type=int, default=1280, help='Report graph image width in pixels.')
    parser.add_argument('--height', type=int, default=720, help='Report graph image height in pixels.')
    parser.add_argument('--dpi', type=int, default=100, help='Matplotlib DPI used to match pixel size.')
    parser.add_argument('--opengl', action='store_true', help='Request PyQtGraph OpenGL rendering.')
    parser.add_argument('--cache-buster', type=int, default=None, help='Optional report image URL cache buster.')
    args = parser.parse_args(argv)

    comparison = export_saved_profile_report_graph_comparison(
        args.profile_file,
        output_dir=args.output_dir,
        prefix=args.prefix,
        width=args.width,
        height=args.height,
        dpi=args.dpi,
        use_opengl=args.opengl,
        cache_buster=args.cache_buster,
    )
    print(json.dumps(comparison_to_dict(comparison), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


__all__ = [
    'ReportGraphAsset',
    'ReportGraphExportComparison',
    'comparison_to_dict',
    'export_saved_profile_report_graph_comparison',
    'main',
    'report_graph_comparison_from_parity',
    'report_graph_image_url',
]


if __name__ == '__main__':
    raise SystemExit(main())
