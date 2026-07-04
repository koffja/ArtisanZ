import pytest
from artisanlib.rorflick_manager import RoRFlickManager, RoRFlickEvent


class TestRoRFlickManagerInit:
    def test_initial_state_disabled_with_defaults(self):
        m = RoRFlickManager()
        assert m.enabled is False
        assert m.flick_threshold == 5.0
        assert m.crash_threshold == 5.0
        assert m.exit_threshold == 1.0
        assert m.dev_phase_multiplier == 1.5
        assert m.events == []
        assert m._current_start is None
        assert m._current_type is None
        assert m._current_peak == 0.0
        assert m._current_peak_idx == 0

    def test_update_settings_mutates_all_fields(self):
        m = RoRFlickManager()
        m.update_settings(
            enabled=True,
            flick_threshold=3.0,
            crash_threshold=4.0,
            exit_threshold=0.5,
            dev_phase_multiplier=2.0,
        )
        assert m.enabled is True
        assert m.flick_threshold == 3.0
        assert m.crash_threshold == 4.0
        assert m.exit_threshold == 0.5
        assert m.dev_phase_multiplier == 2.0

    def test_update_settings_uses_defaults_when_omitted(self):
        m = RoRFlickManager()
        m.update_settings(enabled=True)
        assert m.flick_threshold == 5.0
        assert m.crash_threshold == 5.0
        assert m.exit_threshold == 1.0
        assert m.dev_phase_multiplier == 1.5

    def test_reset_clears_events_and_state(self):
        m = RoRFlickManager()
        m.events.append(RoRFlickEvent(
            start_idx=0, peak_idx=0, end_idx=0,
            event_type='flick', peak_magnitude=5.0,
            severity='moderate', in_development=False,
        ))
        m._current_start = 5
        m._current_type = 'flick'
        m._current_peak = 7.0
        m._current_peak_idx = 8

        m.reset()

        assert m.events == []
        assert m._current_start is None
        assert m._current_type is None
        assert m._current_peak == 0.0
        assert m._current_peak_idx == 0
