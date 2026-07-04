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


class TestRoRFlickDetection:
    def test_disabled_manager_returns_no_event(self):
        m = RoRFlickManager()
        # enabled=False
        result = m.process_sample(0, 10.0, 5.0, False)
        assert result is None

    def test_flick_starts_but_does_not_complete_immediately(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 5.0
        m.exit_threshold = 1.0

        # short=10, long=5, divergence=5 >= flick_threshold
        result = m.process_sample(0, 10.0, 5.0, False)
        assert result is None  # event starts, not completes
        assert m._current_type == 'flick'
        assert m._current_start == 0
        assert m._current_peak == 5.0
        assert m._current_peak_idx == 0

    def test_flick_completes_when_divergence_drops_below_exit(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 5.0
        m.exit_threshold = 1.0

        m.process_sample(0, 10.0, 5.0, False)  # enter flick
        result = m.process_sample(1, 5.5, 5.0, False)  # divergence=0.5 < exit

        assert result is not None
        assert result.event_type == 'flick'
        assert result.start_idx == 0
        assert result.end_idx == 1
        assert result.peak_magnitude == 5.0
        assert result.peak_idx == 0
        assert result.in_development is False
        # state reset
        assert m._current_start is None
        assert m.events == [result]

    def test_crash_detected_when_long_above_short(self):
        m = RoRFlickManager()
        m.enabled = True
        m.crash_threshold = 5.0
        m.exit_threshold = 1.0

        # short=5, long=10, divergence=-5, -divergence=5 >= crash_threshold
        result = m.process_sample(0, 5.0, 10.0, False)
        assert result is None
        assert m._current_type == 'crash'

        result = m.process_sample(1, 9.5, 10.0, False)
        assert result is not None
        assert result.event_type == 'crash'
        assert result.peak_magnitude == 5.0

    def test_peak_is_tracked_through_event(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 3.0
        m.exit_threshold = 1.0

        m.process_sample(0, 8.0, 5.0, False)   # mag=3
        m.process_sample(1, 10.0, 5.0, False)  # mag=5 -> peak
        m.process_sample(2, 12.0, 5.0, False)  # mag=7 -> new peak
        result = m.process_sample(3, 5.5, 5.0, False)  # mag=0.5 -> exit

        assert result.peak_magnitude == 7.0
        assert result.peak_idx == 2

    def test_below_threshold_does_not_trigger(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 5.0

        # divergence 4.9 < 5.0
        result = m.process_sample(0, 9.9, 5.0, False)
        assert result is None
        assert m._current_type is None

    def test_boundary_equal_to_threshold_triggers(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 5.0

        # divergence exactly 5.0
        m.process_sample(0, 10.0, 5.0, False)
        assert m._current_type == 'flick'

    def test_none_averages_are_safely_ignored(self):
        m = RoRFlickManager()
        m.enabled = True
        result = m.process_sample(0, None, 5.0, False)
        assert result is None
        result = m.process_sample(0, 5.0, None, False)
        assert result is None

    def test_flick_does_not_trigger_when_already_in_crash(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 5.0
        m.crash_threshold = 5.0
        m.exit_threshold = 1.0

        # Enter crash
        m.process_sample(0, 5.0, 10.0, False)
        assert m._current_type == 'crash'

        # While in crash, even if flick conditions arise, ignore
        m.process_sample(1, 10.0, 5.0, False)
        assert m._current_type == 'crash'  # still in crash
