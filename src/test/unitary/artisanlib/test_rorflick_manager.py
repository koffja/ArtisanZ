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


class TestRoRFlickBatch:
    def test_process_batch_resets_state_first(self):
        m = RoRFlickManager()
        m.enabled = True
        # pre-existing event from previous roast
        m.events.append(RoRFlickEvent(
            start_idx=0, peak_idx=0, end_idx=0,
            event_type='flick', peak_magnitude=99.0,
            severity='hard', in_development=False,
        ))

        samples = [
            (0, 10.0, 5.0, False),  # enter flick
            (1, 5.5, 5.0, False),   # exit
        ]
        events = m.process_batch(samples)

        # pre-existing event was cleared
        assert all(e.peak_magnitude != 99.0 for e in events)
        assert len(events) == 1
        assert events[0].event_type == 'flick'
        assert events == m.events  # batch result equals internal state

    def test_process_batch_closes_open_event_at_end(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 3.0
        m.exit_threshold = 1.0

        samples = [
            (0, 8.0, 5.0, False),  # enter flick (mag=3), no exit
        ]
        events = m.process_batch(samples)

        # event force-closed at end of batch
        assert len(events) == 1
        assert events[0].start_idx == 0
        assert events[0].end_idx == 0
        # state cleared after close
        assert m._current_start is None

    def test_process_batch_handles_empty_samples(self):
        m = RoRFlickManager()
        m.enabled = True
        events = m.process_batch([])
        assert events == []


class TestRoRFlickProcessRoast:
    def test_process_roast_with_empty_delta2(self):
        m = RoRFlickManager()
        m.enabled = True
        events = m.process_roast([], [], fcs_idx=-1)
        assert events == []

    def test_process_roast_detects_flick_in_synthetic_data(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 3.0
        m.exit_threshold = 1.0

        # Build synthetic delta2: flat at 5, then spike to 15, then back to 6
        # At sample rate 1Hz, short_window=9, long_window=30
        delta2 = [5.0] * 35 + [15.0] * 5 + [6.0] * 10
        timex = [float(i) for i in range(len(delta2))]
        events = m.process_roast(delta2, timex, fcs_idx=-1)

        # A flick should be detected when the spike diverges from the long avg
        assert len(events) >= 1
        assert any(e.event_type == 'flick' for e in events)

    def test_process_roast_respects_fcs_index_for_dev_phase(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 3.0
        m.exit_threshold = 1.0
        m.dev_phase_multiplier = 2.0

        # Flick happens after FCs (index 20)
        delta2 = [5.0] * 20 + [15.0] * 5 + [6.0] * 10
        timex = [float(i) for i in range(len(delta2))]
        events = m.process_roast(delta2, timex, fcs_idx=20)

        flick_events = [e for e in events if e.event_type == 'flick']
        if flick_events:
            # The flick started after index 20, so in_development should be True
            assert any(e.in_development for e in flick_events)

    def test_process_roast_resets_previous_events(self):
        m = RoRFlickManager()
        m.enabled = True
        # Pre-existing event
        m.events.append(RoRFlickEvent(
            start_idx=0, peak_idx=0, end_idx=0,
            event_type='flick', peak_magnitude=99.0,
            severity='hard', in_development=False,
        ))

        delta2 = [5.0] * 40
        timex = [float(i) for i in range(len(delta2))]
        events = m.process_roast(delta2, timex, fcs_idx=-1)

        # Pre-existing event cleared
        assert all(e.peak_magnitude != 99.0 for e in events)


class TestRoRFlickNoneHandling:
    def test_window_average_handles_none_values(self):
        data = [5.0, None, 10.0, None, 15.0]
        assert RoRFlickManager._window_average(data, 4, 5) == 10.0  # avg of [5,10,15]
        assert RoRFlickManager._window_average(data, 4, 3) == 12.5  # avg of [10,15]
        assert RoRFlickManager._window_average([None, None, None], 2, 3) == 0.0

    def test_process_roast_with_none_in_delta2_does_not_crash(self):
        m = RoRFlickManager()
        m.enabled = True
        delta2 = [5.0, None, 5.0, 15.0, None, 15.0, 6.0, 6.0]
        timex = [float(i) for i in range(len(delta2))]
        events = m.process_roast(delta2, timex, fcs_idx=-1)
        assert isinstance(events, list)  # did not crash


class TestRoRFlickSeverity:
    def test_soft_severity_when_magnitude_below_5(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 1.0
        m.exit_threshold = 0.5

        # mag = 2 (< 5)
        m.process_sample(0, 3.0, 1.0, False)
        result = m.process_sample(1, 1.4, 1.0, False)
        assert result.severity == 'soft'
        assert result.in_development is False

    def test_moderate_severity_at_5(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 1.0
        m.exit_threshold = 0.5

        # mag = 5
        m.process_sample(0, 6.0, 1.0, False)
        result = m.process_sample(1, 1.4, 1.0, False)
        assert result.severity == 'moderate'

    def test_hard_severity_at_10(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 1.0
        m.exit_threshold = 0.5

        # mag = 10
        m.process_sample(0, 11.0, 1.0, False)
        result = m.process_sample(1, 1.4, 1.0, False)
        assert result.severity == 'hard'

    def test_dev_phase_multiplier_upgrades_severity(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 1.0
        m.exit_threshold = 0.5
        m.dev_phase_multiplier = 2.0

        # mag=3, in dev: 3 * 2 = 6 -> moderate (would be soft without boost)
        m.process_sample(0, 4.0, 1.0, True)
        result = m.process_sample(1, 1.4, 1.0, True)
        assert result.severity == 'moderate'
        assert result.in_development is True
        # peak_magnitude is the raw magnitude (not multiplied) — boost only affects severity
        assert result.peak_magnitude == 3.0


class TestRoRFlickStatus:
    def test_status_disabled_returns_empty(self):
        m = RoRFlickManager()
        text, color = m.get_status_message()
        assert text == ''
        assert color == ''

    def test_status_enabled_no_events_says_normal(self):
        m = RoRFlickManager()
        m.enabled = True
        text, color = m.get_status_message()
        assert '正常' in text

    def test_status_with_last_event_hard_is_red(self):
        m = RoRFlickManager()
        m.enabled = True
        m.events.append(RoRFlickEvent(
            start_idx=0, peak_idx=0, end_idx=1,
            event_type='flick', peak_magnitude=12.0,
            severity='hard', in_development=False,
        ))
        text, color = m.get_status_message()
        assert 'FLICK' in text.upper()
        assert color == '#CC0000'

    def test_should_show_annotations_requires_enabled_and_events(self):
        m = RoRFlickManager()
        assert m.should_show_annotations() is False
        m.enabled = True
        assert m.should_show_annotations() is False
        m.events.append(RoRFlickEvent(
            start_idx=0, peak_idx=0, end_idx=0,
            event_type='flick', peak_magnitude=5.0,
            severity='moderate', in_development=False,
        ))
        assert m.should_show_annotations() is True


class TestRoRFlickLiveReplayParity:
    """Verify that live and replay processing produce identical events."""

    def test_parity_with_synthetic_flick(self):
        delta2 = [5.0] * 35 + [15.0] * 5 + [6.0] * 10
        timex = [float(i) for i in range(len(delta2))]

        # Live: one sample at a time using _time_window_average
        m_live = RoRFlickManager()
        m_live.enabled = True
        m_live.flick_threshold = 3.0
        m_live.exit_threshold = 1.0
        for i in range(len(delta2)):
            short = RoRFlickManager._time_window_average(delta2, timex, i, 9.0)
            long_ = RoRFlickManager._time_window_average(delta2, timex, i, 30.0)
            m_live.process_sample(i, short, long_, False)
        if m_live._current_start is not None:
            m_live._finalize_event(len(delta2) - 1, False)

        # Replay
        m_replay = RoRFlickManager()
        m_replay.enabled = True
        m_replay.flick_threshold = 3.0
        m_replay.exit_threshold = 1.0
        m_replay.process_roast(delta2, timex, fcs_idx=-1)

        assert len(m_live.events) == len(m_replay.events), (
            f"Live={len(m_live.events)}, Replay={len(m_replay.events)}"
        )
        for live_evt, replay_evt in zip(m_live.events, m_replay.events):
            assert live_evt.event_type == replay_evt.event_type
            assert live_evt.peak_magnitude == pytest.approx(replay_evt.peak_magnitude)
            assert live_evt.start_idx == replay_evt.start_idx
