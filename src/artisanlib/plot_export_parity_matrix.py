from __future__ import annotations

import argparse
import glob
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from artisanlib.plot_export_parity_smoke import (
    PlotExportParityResult,
    run_profile_export_parity_smoke,
    run_websocket_export_parity_smoke,
)


@dataclass(frozen=True, slots=True)
class ProfileExportMatrixSummary:
    profile_count: int
    profile_paths: tuple[str, ...]
    total_sample_count: int
    total_event_count: int
    total_event_value_count: int
    minimum_phase_band_count: int
    maximum_phase_band_count: int
    maximum_view_state_delta: float
    all_view_states_match: bool
    all_view_states_within_tolerance: bool
    all_pyqtgraph_exports_nonblank: bool
    websocket_regression_included: bool
    websocket_view_state_matches: bool | None


@dataclass(frozen=True, slots=True)
class ProfileExportMatrixResult:
    output_dir: str
    prefix: str
    width: int
    height: int
    dpi: int
    profile_results: tuple[PlotExportParityResult, ...]
    websocket_regression: PlotExportParityResult | None
    summary: ProfileExportMatrixSummary


def run_profile_export_parity_matrix(
        profile_paths: list[str | Path] | tuple[str | Path, ...],
        *,
        output_dir: str | Path = '/tmp/artisanz-profile-export-matrix',
        prefix: str = 'profile-matrix',
        width: int = 1280,
        height: int = 720,
        dpi: int = 100,
        use_opengl: bool = False,
        include_websocket_regression: bool = False,
        websocket_sample_count: int = 24,
        websocket_fixed_step_ms: float = 15_000.0,
        websocket_scenario: str = 'event-heavy') -> ProfileExportMatrixResult:
    if not profile_paths:
        raise ValueError('At least one saved profile path is required for export parity matrix validation')
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    profile_results: list[PlotExportParityResult] = []
    for index, profile_path in enumerate(profile_paths, start=1):
        profile_results.append(run_profile_export_parity_smoke(
            profile_path,
            output_dir=directory,
            prefix=f'{prefix}-{index:02d}-{Path(profile_path).stem}',
            width=width,
            height=height,
            dpi=dpi,
            use_opengl=use_opengl,
        ))

    websocket_regression: PlotExportParityResult | None = None
    if include_websocket_regression:
        websocket_regression = run_websocket_export_parity_smoke(
            sample_count=websocket_sample_count,
            fixed_step_ms=websocket_fixed_step_ms,
            scenario=websocket_scenario,
            output_dir=directory,
            prefix=f'{prefix}-websocket-{websocket_scenario}',
            width=width,
            height=height,
            dpi=dpi,
            use_opengl=use_opengl,
        )

    result_tuple = tuple(profile_results)
    return ProfileExportMatrixResult(
        output_dir=str(directory),
        prefix=prefix,
        width=width,
        height=height,
        dpi=dpi,
        profile_results=result_tuple,
        websocket_regression=websocket_regression,
        summary=_matrix_summary(result_tuple, websocket_regression),
    )


def matrix_result_to_dict(result: ProfileExportMatrixResult) -> dict[str, object]:
    return asdict(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Run Matplotlib/PyQtGraph export parity against a matrix of saved Artisan profiles.')
    parser.add_argument('profile_files', nargs='*', help='Saved Artisan .alog files to compare.')
    parser.add_argument(
        '--profile-glob',
        action='append',
        default=[],
        help='Glob for saved Artisan .alog files. Can be passed more than once.')
    parser.add_argument(
        '--output-dir',
        default='/tmp/artisanz-profile-export-matrix',
        help='Directory for exported PNG files.')
    parser.add_argument('--prefix', default='profile-matrix', help='File prefix for exported PNG files.')
    parser.add_argument('--width', type=int, default=1280, help='Export width in pixels.')
    parser.add_argument('--height', type=int, default=720, help='Export height in pixels.')
    parser.add_argument('--dpi', type=int, default=100, help='Matplotlib export DPI used to match pixel size.')
    parser.add_argument('--opengl', action='store_true', help='Request PyQtGraph OpenGL rendering.')
    parser.add_argument(
        '--include-websocket-regression',
        action='store_true',
        help='Also run the deterministic WebSocket virtual-data parity smoke.')
    parser.add_argument('--websocket-samples', type=int, default=24, help='WebSocket regression sample count.')
    parser.add_argument(
        '--websocket-fixed-step-ms',
        type=float,
        default=15_000.0,
        help='Virtual milliseconds per WebSocket regression request.')
    parser.add_argument(
        '--websocket-scenario',
        choices=('standard', 'event-heavy'),
        default='event-heavy',
        help='Virtual roast event scenario to replay.')
    args = parser.parse_args(argv)

    profile_paths = _collect_profile_paths(args.profile_files, args.profile_glob)
    result = run_profile_export_parity_matrix(
        profile_paths,
        output_dir=args.output_dir,
        prefix=args.prefix,
        width=args.width,
        height=args.height,
        dpi=args.dpi,
        use_opengl=args.opengl,
        include_websocket_regression=args.include_websocket_regression,
        websocket_sample_count=args.websocket_samples,
        websocket_fixed_step_ms=args.websocket_fixed_step_ms,
        websocket_scenario=args.websocket_scenario,
    )
    print(json.dumps(matrix_result_to_dict(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _collect_profile_paths(profile_files: list[str], profile_globs: list[str]) -> tuple[Path, ...]:
    paths = [Path(profile_file) for profile_file in profile_files]
    for pattern in profile_globs:
        matches = [Path(match) for match in sorted(glob.glob(pattern))]
        if not matches:
            raise ValueError(f'No saved profile files matched requested glob: {pattern}')
        paths.extend(matches)
    if not paths and not profile_files and not profile_globs:
        paths.extend(sorted(Path('test/sanity/data/artisan').glob('profile*.alog')))
    unique_paths: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(path)
    if not unique_paths:
        raise ValueError('No saved profile files matched the requested matrix inputs')
    return tuple(unique_paths)


def _matrix_summary(
        profile_results: tuple[PlotExportParityResult, ...],
        websocket_regression: PlotExportParityResult | None) -> ProfileExportMatrixSummary:
    phase_counts = [result.phase_band_count for result in profile_results]
    return ProfileExportMatrixSummary(
        profile_count=len(profile_results),
        profile_paths=tuple(result.source_path or '' for result in profile_results),
        total_sample_count=sum(result.sample_count for result in profile_results),
        total_event_count=sum(result.event_count for result in profile_results),
        total_event_value_count=sum(result.event_value_count for result in profile_results),
        minimum_phase_band_count=min(phase_counts),
        maximum_phase_band_count=max(phase_counts),
        maximum_view_state_delta=max(result.view_state_max_delta for result in profile_results),
        all_view_states_match=all(result.view_state_matches for result in profile_results),
        all_view_states_within_tolerance=all(result.view_state_within_tolerance for result in profile_results),
        all_pyqtgraph_exports_nonblank=all(
            result.pyqtgraph.sampled_non_background_pixel_count > 0
            and result.pyqtgraph.byte_count > 1000
            for result in profile_results
        ),
        websocket_regression_included=websocket_regression is not None,
        websocket_view_state_matches=(
            None if websocket_regression is None else websocket_regression.view_state_matches
        ),
    )


__all__ = [
    'ProfileExportMatrixResult',
    'ProfileExportMatrixSummary',
    'main',
    'matrix_result_to_dict',
    'run_profile_export_parity_matrix',
]


if __name__ == '__main__':
    raise SystemExit(main())
