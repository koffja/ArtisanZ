from dataclasses import dataclass
from typing import Literal, Optional, Tuple
from collections.abc import Iterable


FlickEventType = Literal['flick', 'crash']
FlickSeverity = Literal['soft', 'moderate', 'hard']


@dataclass(frozen=True)
class RoRFlickEvent:
    """A detected RoR flick or crash event."""
    start_idx: int
    peak_idx: int
    end_idx: int
    event_type: FlickEventType
    peak_magnitude: float  # °C/min divergence, always positive
    severity: FlickSeverity
    in_development: bool  # True if post-FCs


class RoRFlickManager:
    """
    Detects RoR flicks and crashes by comparing short-window and long-window
    RoR averages. State-machine based: IDLE -> IN_EVENT -> IDLE.

    Mirrors the ChargeTargetManager pattern: plain Python, no Qt signals,
    poll-only from canvas during redraw/blit.
    """

    def __init__(self) -> None:
        # Configuration
        self.enabled: bool = False
        self.flick_threshold: float = 5.0  # °C/min short-long divergence
        self.crash_threshold: float = 5.0
        self.exit_threshold: float = 1.0
        self.dev_phase_multiplier: float = 1.5

        # Detected events (read by canvas during redraw)
        self.events: list[RoRFlickEvent] = []

        # Internal state machine
        self._current_start: Optional[int] = None
        self._current_type: Optional[FlickEventType] = None
        self._current_peak: float = 0.0
        self._current_peak_idx: int = 0

    def update_settings(
        self,
        enabled: bool,
        flick_threshold: float = 5.0,
        crash_threshold: float = 5.0,
        exit_threshold: float = 1.0,
        dev_phase_multiplier: float = 1.5,
    ) -> None:
        self.enabled = enabled
        self.flick_threshold = flick_threshold
        self.crash_threshold = crash_threshold
        self.exit_threshold = exit_threshold
        self.dev_phase_multiplier = dev_phase_multiplier

    def reset(self) -> None:
        """Clear all state. Call on new roast or load."""
        self.events.clear()
        self._current_start = None
        self._current_type = None
        self._current_peak = 0.0
        self._current_peak_idx = 0

    def process_sample(
        self,
        sample_idx: int,
        short_avg: Optional[float],
        long_avg: Optional[float],
        in_development: bool,
    ) -> Optional[RoRFlickEvent]:
        """Process one sample. Returns an RoRFlickEvent if one just completed."""
        if not self.enabled:
            return None

        if short_avg is None or long_avg is None:
            return None

        divergence = short_avg - long_avg  # +flick tendency, -crash tendency

        if self._current_start is None:
            # IDLE: check for event entry
            if divergence >= self.flick_threshold:
                self._current_start = sample_idx
                self._current_type = 'flick'
                self._current_peak = divergence
                self._current_peak_idx = sample_idx
            elif -divergence >= self.crash_threshold:
                self._current_start = sample_idx
                self._current_type = 'crash'
                self._current_peak = -divergence
                self._current_peak_idx = sample_idx
        else:
            # IN_EVENT: track peak and check for exit
            if self._current_type == 'flick':
                current_mag = divergence
            else:  # crash
                current_mag = -divergence

            # Update peak if current magnitude is higher
            if current_mag > self._current_peak:
                self._current_peak = current_mag
                self._current_peak_idx = sample_idx

            # Exit when magnitude drops below exit threshold
            if 0 <= current_mag < self.exit_threshold:
                event = self._finalize_event(sample_idx, in_development)
                self.events.append(event)
                self._current_start = None
                self._current_type = None
                self._current_peak = 0.0
                self._current_peak_idx = 0
                return event

        return None

    def _finalize_event(self, end_idx: int, in_development: bool) -> RoRFlickEvent:
        """Create an RoRFlickEvent from current state."""
        severity_mult = self.dev_phase_multiplier if in_development else 1.0
        adjusted = self._current_peak * severity_mult

        if adjusted >= 10.0:
            severity: FlickSeverity = 'hard'
        elif adjusted >= 5.0:
            severity = 'moderate'
        else:
            severity = 'soft'

        return RoRFlickEvent(
            start_idx=self._current_start if self._current_start is not None else 0,
            peak_idx=self._current_peak_idx,
            end_idx=end_idx,
            event_type=self._current_type if self._current_type is not None else 'flick',
            peak_magnitude=self._current_peak,
            severity=severity,
            in_development=in_development,
        )

    def process_batch(
        self,
        samples: Iterable[tuple[int, float, float, bool]],
    ) -> list[RoRFlickEvent]:
        """Process pre-computed samples for a complete roast. Resets first."""
        self.reset()
        completed: list[RoRFlickEvent] = []
        last_idx = 0
        last_in_dev = False
        for sample in samples:
            sample_idx, short_avg, long_avg, in_dev = sample
            last_idx = sample_idx
            last_in_dev = in_dev
            event = self.process_sample(sample_idx, short_avg, long_avg, in_dev)
            if event is not None:
                completed.append(event)

        # Close any open event at end of batch
        if self._current_start is not None:
            event = self._finalize_event(last_idx, last_in_dev)
            self.events.append(event)
            completed.append(event)
            self._current_start = None
            self._current_type = None
            self._current_peak = 0.0
            self._current_peak_idx = 0

        return completed

    def process_roast(
        self,
        delta2: list[float | None],
        timex: list[float],
        fcs_idx: int = -1,
    ) -> list[RoRFlickEvent]:
        """
        Process a complete roast from raw delta2 + timex (replay mode).
        Uses time-based windowing identical to canvas._charge_window_average_delta
        to ensure live and replay produce identical results.
        """
        self.reset()
        if not delta2 or not timex:
            return []

        n = min(len(delta2), len(timex))
        for i in range(n):
            short_avg = self._time_window_average(delta2, timex, i, 9.0)
            long_avg = self._time_window_average(delta2, timex, i, 30.0)
            in_dev = fcs_idx > -1 and i >= fcs_idx
            self.process_sample(i, short_avg, long_avg, in_dev)

        # Close any open event at end
        if self._current_start is not None:
            final_idx = n - 1
            final_in_dev = fcs_idx > -1 and final_idx >= fcs_idx
            event = self._finalize_event(final_idx, final_in_dev)
            self.events.append(event)
            self._current_start = None
            self._current_type = None
            self._current_peak = 0.0
            self._current_peak_idx = 0

        return list(self.events)

    @staticmethod
    def _window_average(data: list[float | None], end_idx: int, window: int) -> float:
        """Average of data[max(0, end_idx-window+1) .. end_idx], ignoring None."""
        if not data or end_idx < 0 or end_idx >= len(data):
            return 0.0
        start = max(0, end_idx - window + 1)
        slice_data = [v for v in data[start:end_idx + 1] if v is not None]
        if not slice_data:
            return 0.0
        return sum(slice_data) / len(slice_data)

    @staticmethod
    def _time_window_average(
        delta2: list[float | None],
        timex: list[float],
        end_idx: int,
        window_seconds: float,
    ) -> float | None:
        """Time-based window average mirroring canvas._charge_window_average_delta."""
        if not delta2 or not timex:
            return None
        if end_idx < 0 or end_idx >= len(delta2) or end_idx >= len(timex):
            return None
        if len(timex) < 2 or len(delta2) < 2:
            return None
        latest_time = timex[end_idx]
        values: list[float] = []
        for idx in range(end_idx, -1, -1):
            if idx >= len(timex):
                continue
            if latest_time - timex[idx] > window_seconds:
                break
            value = delta2[idx]
            if value is not None and value > 0:
                values.append(value)
        if not values:
            return None
        return sum(values) / len(values)

    def should_show_annotations(self) -> bool:
        return self.enabled and len(self.events) > 0

    def get_status_message(self) -> Tuple[str, str]:
        """For status bar: returns (text, color)."""
        if not self.enabled:
            return ('', '')
        if not self.events:
            return ('RoR 监测: 正常', '#888888')
        last = self.events[-1]
        if last.severity == 'hard':
            color = '#CC0000'
        elif last.severity == 'moderate':
            color = '#FF8800'
        else:
            color = '#FFCC00'
        text = f'RoR {last.event_type.upper()}: {last.peak_magnitude:.1f}°C/min ({last.severity})'
        return (text, color)
