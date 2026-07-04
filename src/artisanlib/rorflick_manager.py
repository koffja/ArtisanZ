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
