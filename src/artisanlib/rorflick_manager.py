from dataclasses import dataclass
from typing import Literal, Optional, Tuple


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
