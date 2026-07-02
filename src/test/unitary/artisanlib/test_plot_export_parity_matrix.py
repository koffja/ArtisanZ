from __future__ import annotations

from pathlib import Path

import pytest

from artisanlib.plot_export_parity_matrix import (
    _collect_profile_paths,
    run_profile_export_parity_matrix,
)


def test_run_profile_export_parity_matrix_covers_saved_profiles_and_websocket(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setenv('QT_QPA_PLATFORM', 'offscreen')
    profile_paths = (
        Path('test/sanity/data/artisan/profile1.alog'),
        Path('test/sanity/data/artisan/profile2.alog'),
        Path('test/sanity/data/artisan/profile3.alog'),
        Path('test/sanity/data/artisan/profile4.alog'),
    )

    result = run_profile_export_parity_matrix(
        profile_paths,
        output_dir=tmp_path,
        prefix='matrix',
        width=640,
        height=360,
        dpi=100,
        use_opengl=False,
        include_websocket_regression=True,
        websocket_sample_count=12,
        websocket_fixed_step_ms=30_000.0,
        websocket_scenario='event-heavy',
    )

    assert result.summary.profile_count == 4
    assert len(result.profile_results) == 4
    assert result.summary.profile_paths == tuple(str(path) for path in profile_paths)
    assert result.summary.total_sample_count > 2800
    assert result.summary.total_event_count >= 70
    assert result.summary.total_event_value_count >= 20
    assert result.summary.minimum_phase_band_count >= 2
    assert result.summary.maximum_phase_band_count >= 3
    assert result.summary.all_view_states_match is True
    assert result.summary.all_view_states_within_tolerance is True
    assert result.summary.maximum_view_state_delta == 0.0
    assert result.summary.all_pyqtgraph_exports_nonblank is True
    assert result.summary.websocket_regression_included is True
    assert result.summary.websocket_view_state_matches is True
    assert result.websocket_regression is not None
    assert result.websocket_regression.source_kind == 'websocket'
    assert result.websocket_regression.guide_count == 3
    assert result.websocket_regression.pyqtgraph.sampled_non_background_pixel_count > 0

    for index, profile_result in enumerate(result.profile_results, start=1):
        assert profile_result.source_kind == 'profile'
        assert profile_result.prefix.startswith(f'matrix-{index:02d}-profile')
        assert profile_result.view_state_matches is True
        assert profile_result.view_state_within_tolerance is True
        assert profile_result.pyqtgraph.sampled_non_background_pixel_count > 0
        assert Path(profile_result.matplotlib.path).exists()
        assert Path(profile_result.pyqtgraph.path).exists()


def test_run_profile_export_parity_matrix_requires_profiles(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='At least one saved profile path'):
        run_profile_export_parity_matrix((), output_dir=tmp_path)


def test_collect_profile_paths_defaults_to_sanity_fixtures() -> None:
    paths = _collect_profile_paths([], [])

    assert paths == tuple(sorted(Path('test/sanity/data/artisan').glob('profile*.alog')))
    assert len(paths) == 4


def test_collect_profile_paths_deduplicates_explicit_and_glob_inputs() -> None:
    paths = _collect_profile_paths(
        ['test/sanity/data/artisan/profile1.alog'],
        ['test/sanity/data/artisan/profile1.alog'],
    )

    assert paths == (Path('test/sanity/data/artisan/profile1.alog'),)


def test_collect_profile_paths_rejects_unmatched_requested_glob() -> None:
    with pytest.raises(ValueError, match='No saved profile files matched requested glob'):
        _collect_profile_paths([], ['test/sanity/data/artisan/not-a-profile-*.alog'])


def test_collect_profile_paths_rejects_unmatched_glob_even_with_explicit_file() -> None:
    with pytest.raises(ValueError, match='No saved profile files matched requested glob'):
        _collect_profile_paths(
            ['test/sanity/data/artisan/profile1.alog'],
            ['test/sanity/data/artisan/not-a-profile-*.alog'],
        )
