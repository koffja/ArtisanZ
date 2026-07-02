from __future__ import annotations

from pathlib import Path

import pytest

from artisanlib.plot_profile_snapshot import load_profile_snapshot
from artisanlib.util import deserialize


def test_load_profile_snapshot_builds_snapshot_from_saved_alog() -> None:
    profile_path = Path('test/data/profile1.alog')
    profile = deserialize(str(profile_path))

    result = load_profile_snapshot(profile_path)
    snapshot = result.snapshot

    assert result.title == 'Guji Shakiso'
    assert result.sample_count > 1000
    assert result.event_count >= 10
    assert len(snapshot.curves) >= 4
    assert len(snapshot.visible_curves()) >= 4
    assert len(snapshot.phase_bands) == 3
    assert len(snapshot.event_values) >= 5
    assert len(snapshot.areas) == 1
    assert snapshot.time_axis.maximum > snapshot.time_axis.minimum
    assert snapshot.time_axis.minimum == pytest.approx(profile['xmin'])
    assert snapshot.time_axis.maximum == pytest.approx(profile['xmin'] + profile['xmax'])
    assert snapshot.temperature_axis.maximum > snapshot.temperature_axis.minimum
    assert snapshot.ror_axis is not None
    assert snapshot.ror_axis.maximum > snapshot.ror_axis.minimum


def test_load_profile_snapshot_rejects_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_profile_snapshot('/tmp/artisanz-does-not-exist.alog')


def test_load_profile_snapshot_rejects_empty_profile(tmp_path: Path) -> None:
    profile_path = tmp_path / 'empty.alog'
    profile_path.write_text('{}', encoding='utf-8')

    with pytest.raises(ValueError, match='no readable profile data'):
        load_profile_snapshot(profile_path)


def test_load_profile_snapshot_rejects_profile_without_samples(tmp_path: Path) -> None:
    profile_path = tmp_path / 'no-samples.alog'
    profile_path.write_text("{'title': 'No Samples'}", encoding='utf-8')

    with pytest.raises(ValueError, match='no usable time samples'):
        load_profile_snapshot(profile_path)
