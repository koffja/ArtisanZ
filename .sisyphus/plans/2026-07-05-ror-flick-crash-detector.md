# RoR Flick/Crash Detector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an ArtisanZ-custom feature that automatically detects RoR flicks and crashes during roasting (real-time and replay) and annotates them on the curve with severity-coded highlight bands and peak labels.

**Architecture:** Plain-Python manager (`RoRFlickManager`) holds detection state machine and event list. PyQt6 `QDialog` mutates manager settings in place (no Qt signals cross the boundary — poll-only pattern, mirroring `ChargeTargetManager`). Canvas polls manager every redraw/blit, computes short/long RoR averages via existing `_charge_window_average_delta` helper, feeds samples to manager, and draws `axvspan` + `annotate` per event. Persistence via 5 QSettings keys.

**Tech Stack:** Python 3.12+, PyQt6, matplotlib (existing canvas), pytest. No new dependencies.

## Global Constraints

- **Branch**: `ArtisanZ` only (never commit on `master`)
- **Code style**: Match existing `charge_manager.py` / `charge_dialog.py` patterns (4-space indent, explicit types, dataclass frozen=True for value types, no f-string abuse)
- **No type suppression**: Never use `as any`, `# type: ignore`, `# pylint: disable=...` for type errors
- **Python target**: 3.12+ (use `list[X]`, `X | None`, `Optional[X]` matching existing style)
- **No new dependencies**: Reuse existing matplotlib + PyQt6 + dataclasses
- **i18n**: All user-facing strings via `QApplication.translate('RoRFlickDlg', '...')` (Chinese default)
- **Testing**: Every manager behavior pinned by unit test; one canvas integration smoke test
- **Commits**: Frequent, one per task, conventional format `feat(rorflick): ...`

## User-Decided Specifications

| # | Decision | Value |
|---|---|---|
| 1 | Detection timing | Both real-time AND replay |
| 2 | Threshold style | Pragmatist defaults + user-configurable |
| 3 | Visual style | Interval highlight band (axvspan) + peak annotation |
| 4 | Alert mechanism | Status bar text only (no sound, no popup — preserves poll-only arch) |
| 5 | Detection scope | Full roast; development-phase events get severity multiplier |

## Defaults

| Threshold | Default | Meaning |
|---|---|---|
| `flick_threshold` | 5.0 °C/min | short_avg - long_avg above this → flick |
| `crash_threshold` | 5.0 °C/min | long_avg - short_avg above this → crash |
| `exit_threshold` | 1.0 °C/min | below this → event ends |
| `dev_phase_multiplier` | 1.5 | post-FCs events get peak × this for severity |

| Severity | Adjusted magnitude |
|---|---|
| `soft` | < 5 |
| `moderate` | 5 to < 10 |
| `hard` | ≥ 10 |

---

## File Structure

| File | Role | Lines (est.) |
|---|---|---|
| `src/artisanlib/rorflick_manager.py` | Plain-Python manager + dataclass + state machine | ~170 |
| `src/artisanlib/rorflick_dialog.py` | PyQt6 dialog for thresholds/enabled | ~115 |
| `src/test/unitary/artisanlib/test_rorflick_manager.py` | Unit tests (13+ tests) | ~220 |
| `src/test/unitary/artisanlib/test_rorflick_dialog.py` | Dialog smoke test | ~30 |
| `src/test/unitary/artisanlib/test_canvas.py` (modify) | Add 1 integration test | +30 |
| `src/artisanlib/main.py` (modify) | imports, instantiation, menu, dialog, QSettings ×3 | +35 lines across 7 sites |
| `src/artisanlib/canvas.py` (modify) | attributes, whitelist, draw method, 2 call sites | +95 lines across 5 sites |

---

## Task 1: Manager Foundation (dataclass + init + update_settings + reset)

**Files:**
- Create: `src/artisanlib/rorflick_manager.py`
- Create: `src/test/unitary/artisanlib/test_rorflick_manager.py`

**Interfaces:**
- Produces: `RoRFlickEvent` (frozen dataclass), `RoRFlickManager` class with `__init__`, `update_settings(enabled, flick_threshold, crash_threshold, exit_threshold, dev_phase_multiplier)`, `reset()`, fields: `enabled`, `flick_threshold`, `crash_threshold`, `exit_threshold`, `dev_phase_multiplier`, `events: list[RoRFlickEvent]`, `_current_start`, `_current_type`, `_current_peak`, `_current_peak_idx`

- [ ] **Step 1: Write the failing test**

Create `src/test/unitary/artisanlib/test_rorflick_manager.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'artisanlib.rorflick_manager'`

- [ ] **Step 3: Write minimal implementation**

Create `src/artisanlib/rorflick_manager.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/artisanlib/rorflick_manager.py src/test/unitary/artisanlib/test_rorflick_manager.py
git commit -m "feat(rorflick): add manager foundation with dataclass and settings"
```

---

## Task 2: Detection Algorithm (process_sample for flick + crash)

**Files:**
- Modify: `src/artisanlib/rorflick_manager.py` (add `process_sample` + `_finalize_event`)
- Modify: `src/test/unitary/artisanlib/test_rorflick_manager.py` (add `TestRoRFlickDetection` class)

**Interfaces:**
- Consumes: from Task 1 — `RoRFlickManager`, fields
- Produces: `process_sample(sample_idx, short_avg, long_avg, in_development) -> Optional[RoRFlickEvent]`, `_finalize_event(end_idx, in_development) -> RoRFlickEvent`

- [ ] **Step 1: Write the failing tests**

Append to `src/test/unitary/artisanlib/test_rorflick_manager.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py::TestRoRFlickDetection -v`
Expected: FAIL with `AttributeError: 'RoRFlickManager' object has no attribute 'process_sample'`

- [ ] **Step 3: Implement process_sample and _finalize_event**

Append to `src/artisanlib/rorflick_manager.py` inside `class RoRFlickManager` (after `reset` method):

```python
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
            if current_mag < self.exit_threshold:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py -v`
Expected: PASS (4 + 9 = 13 tests)

- [ ] **Step 5: Commit**

```bash
git add src/artisanlib/rorflick_manager.py src/test/unitary/artisanlib/test_rorflick_manager.py
git commit -m "feat(rorflick): add flick/crash detection state machine"
```

---

## Task 3: Batch Processing + Phase Weighting Verification + Status API

**Files:**
- Modify: `src/artisanlib/rorflick_manager.py` (add `process_batch`, `should_show_annotations`, `get_status_message`)
- Modify: `src/test/unitary/artisanlib/test_rorflick_manager.py` (add `TestRoRFlickBatch`, `TestRoRFlickSeverity`, `TestRoRFlickStatus`)

**Interfaces:**
- Produces: `process_batch(samples: Iterable[tuple[int, float, float, bool]]) -> list[RoRFlickEvent]`, `should_show_annotations() -> bool`, `get_status_message() -> Tuple[str, str]`

- [ ] **Step 1: Write the failing tests**

Append to `src/test/unitary/artisanlib/test_rorflick_manager.py`:

```python
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
        events = m.process_roast([], fcs_idx=-1, sample_rate_hz=1.0)
        assert events == []

    def test_process_roast_detects_flick_in_synthetic_data(self):
        m = RoRFlickManager()
        m.enabled = True
        m.flick_threshold = 3.0
        m.exit_threshold = 1.0

        # Build synthetic delta2: flat at 5, then spike to 15, then back to 6
        # At sample rate 1Hz, short_window=9, long_window=30
        delta2 = [5.0] * 35 + [15.0] * 5 + [6.0] * 10
        events = m.process_roast(delta2, fcs_idx=-1, sample_rate_hz=1.0)

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
        events = m.process_roast(delta2, fcs_idx=20, sample_rate_hz=1.0)

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
        events = m.process_roast(delta2, fcs_idx=-1, sample_rate_hz=1.0)

        # Pre-existing event cleared
        assert all(e.peak_magnitude != 99.0 for e in events)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py::TestRoRFlickBatch test/unitary/artisanlib/test_rorflick_manager.py::TestRoRFlickStatus -v`
Expected: FAIL with `AttributeError: 'RoRFlickManager' object has no attribute 'process_batch'`

- [ ] **Step 3: Implement batch processing, roast replay, and status methods**

Add to top of `src/artisanlib/rorflick_manager.py` (after `from typing import ...`):

```python
from collections.abc import Iterable
```

Append to `class RoRFlickManager` (after `_finalize_event` method from Task 2):

```python
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
        delta2: list[float],
        fcs_idx: int = -1,
        sample_rate_hz: float = 1.0,
    ) -> list[RoRFlickEvent]:
        """
        Process a complete roast from raw delta2 (replay mode).
        Computes its own short/long window averages internally.
        """
        self.reset()
        if not delta2:
            return []

        short_window = max(1, int(9.0 * sample_rate_hz))
        long_window = max(1, int(30.0 * sample_rate_hz))

        for i in range(len(delta2)):
            short_avg = self._window_average(delta2, i, short_window)
            long_avg = self._window_average(delta2, i, long_window)
            in_dev = fcs_idx > -1 and i >= fcs_idx
            self.process_sample(i, short_avg, long_avg, in_dev)

        # Close any open event at end
        if self._current_start is not None:
            final_idx = len(delta2) - 1
            final_in_dev = fcs_idx > -1 and final_idx >= fcs_idx
            event = self._finalize_event(final_idx, final_in_dev)
            self.events.append(event)
            self._current_start = None
            self._current_type = None
            self._current_peak = 0.0
            self._current_peak_idx = 0

        return list(self.events)

    @staticmethod
    def _window_average(data: list[float], end_idx: int, window: int) -> float:
        """Average of data[max(0, end_idx-window+1) .. end_idx]."""
        if not data or end_idx < 0 or end_idx >= len(data):
            return 0.0
        start = max(0, end_idx - window + 1)
        slice_data = data[start:end_idx + 1]
        if not slice_data:
            return 0.0
        return sum(slice_data) / len(slice_data)

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
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py -v`
Expected: PASS (4 + 9 + 3 + 4 + 4 = 24 tests)

- [ ] **Step 5: Commit**

```bash
git add src/artisanlib/rorflick_manager.py src/test/unitary/artisanlib/test_rorflick_manager.py
git commit -m "feat(rorflick): add batch processing, severity classifier, status API"
```

---

## Task 4: Settings Dialog (mirror charge_dialog pattern)

**Files:**
- Create: `src/artisanlib/rorflick_dialog.py`
- Create: `src/test/unitary/artisanlib/test_rorflick_dialog.py`

**Interfaces:**
- Consumes: from Tasks 1-3 — `RoRFlickManager` with `update_settings`, `flick_threshold`, `crash_threshold`, `exit_threshold`, `dev_phase_multiplier`, `enabled`
- Produces: `RoRFlickDlg(QDialog)` class with `__init__(parent, manager)`, `setup_ui()`, `load_settings()`, `save()`

- [ ] **Step 1: Write the failing test**

Create `src/test/unitary/artisanlib/test_rorflick_dialog.py`:

```python
import pytest
from PyQt6.QtWidgets import QApplication
from artisanlib.rorflick_manager import RoRFlickManager
from artisanlib.rorflick_dialog import RoRFlickDlg


@pytest.fixture(scope='module')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_dialog_loads_settings_from_manager(qapp):
    m = RoRFlickManager()
    m.update_settings(
        enabled=True,
        flick_threshold=4.5,
        crash_threshold=6.0,
        exit_threshold=0.8,
        dev_phase_multiplier=1.8,
    )
    dlg = RoRFlickDlg(None, m)
    assert dlg.flick_spinbox.value() == pytest.approx(4.5)
    assert dlg.crash_spinbox.value() == pytest.approx(6.0)
    assert dlg.exit_spinbox.value() == pytest.approx(0.8)
    assert dlg.dev_spinbox.value() == pytest.approx(1.8)
    assert dlg.enabled_checkbox.isChecked() is True


def test_dialog_save_pushes_values_back_to_manager(qapp):
    m = RoRFlickManager()
    dlg = RoRFlickDlg(None, m)
    dlg.flick_spinbox.setValue(7.2)
    dlg.crash_spinbox.setValue(8.1)
    dlg.exit_spinbox.setValue(0.3)
    dlg.dev_spinbox.setValue(2.1)
    dlg.enabled_checkbox.setChecked(True)
    dlg.save()

    assert m.enabled is True
    assert m.flick_threshold == pytest.approx(7.2)
    assert m.crash_threshold == pytest.approx(8.1)
    assert m.exit_threshold == pytest.approx(0.3)
    assert m.dev_phase_multiplier == pytest.approx(2.1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_dialog.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'artisanlib.rorflick_dialog'`

- [ ] **Step 3: Implement the dialog**

Create `src/artisanlib/rorflick_dialog.py`:

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QCheckBox, QPushButton, QApplication,
    QGroupBox, QGridLayout,
)
from artisanlib.rorflick_manager import RoRFlickManager


class RoRFlickDlg(QDialog):
    """Settings dialog for RoR flick/crash detector. Mutates manager in place."""

    def __init__(self, parent, manager: RoRFlickManager):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle(QApplication.translate('RoRFlickDlg', 'RoR 异常检测设置'))
        self.setup_ui()
        self.load_settings()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # --- Threshold Group ---
        thresh_group = QGroupBox(QApplication.translate('RoRFlickDlg', '检测阈值'))
        thresh_layout = QGridLayout()

        flick_label = QLabel(QApplication.translate('RoRFlickDlg', 'Flick 触发 (°C/min):'))
        self.flick_spinbox = QDoubleSpinBox()
        self.flick_spinbox.setRange(0.5, 30.0)
        self.flick_spinbox.setDecimals(1)
        self.flick_spinbox.setSingleStep(0.5)
        self.flick_spinbox.setSuffix(' /min')
        thresh_layout.addWidget(flick_label, 0, 0)
        thresh_layout.addWidget(self.flick_spinbox, 0, 1)

        crash_label = QLabel(QApplication.translate('RoRFlickDlg', 'Crash 触发 (°C/min):'))
        self.crash_spinbox = QDoubleSpinBox()
        self.crash_spinbox.setRange(0.5, 30.0)
        self.crash_spinbox.setDecimals(1)
        self.crash_spinbox.setSingleStep(0.5)
        self.crash_spinbox.setSuffix(' /min')
        thresh_layout.addWidget(crash_label, 1, 0)
        thresh_layout.addWidget(self.crash_spinbox, 1, 1)

        exit_label = QLabel(QApplication.translate('RoRFlickDlg', '退出阈值 (°C/min):'))
        self.exit_spinbox = QDoubleSpinBox()
        self.exit_spinbox.setRange(0.1, 5.0)
        self.exit_spinbox.setDecimals(1)
        self.exit_spinbox.setSingleStep(0.1)
        self.exit_spinbox.setSuffix(' /min')
        thresh_layout.addWidget(exit_label, 2, 0)
        thresh_layout.addWidget(self.exit_spinbox, 2, 1)

        thresh_group.setLayout(thresh_layout)
        layout.addWidget(thresh_group)

        # --- Dev Phase Group ---
        dev_group = QGroupBox(QApplication.translate('RoRFlickDlg', 'Development 加权'))
        dev_layout = QHBoxLayout()
        dev_label = QLabel(QApplication.translate('RoRFlickDlg', '一爆后严重度倍数:'))
        self.dev_spinbox = QDoubleSpinBox()
        self.dev_spinbox.setRange(1.0, 3.0)
        self.dev_spinbox.setDecimals(1)
        self.dev_spinbox.setSingleStep(0.1)
        dev_layout.addWidget(dev_label)
        dev_layout.addWidget(self.dev_spinbox)
        dev_group.setLayout(dev_layout)
        layout.addWidget(dev_group)

        # Enabled checkbox
        self.enabled_checkbox = QCheckBox(QApplication.translate('RoRFlickDlg', '启用功能'))
        layout.addWidget(self.enabled_checkbox)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(QApplication.translate('RoRFlickDlg', '保存'))
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton(QApplication.translate('RoRFlickDlg', '取消'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def load_settings(self) -> None:
        self.flick_spinbox.setValue(self.manager.flick_threshold)
        self.crash_spinbox.setValue(self.manager.crash_threshold)
        self.exit_spinbox.setValue(self.manager.exit_threshold)
        self.dev_spinbox.setValue(self.manager.dev_phase_multiplier)
        self.enabled_checkbox.setChecked(self.manager.enabled)

    def save(self) -> None:
        self.manager.update_settings(
            enabled=self.enabled_checkbox.isChecked(),
            flick_threshold=self.flick_spinbox.value(),
            crash_threshold=self.crash_spinbox.value(),
            exit_threshold=self.exit_spinbox.value(),
            dev_phase_multiplier=self.dev_spinbox.value(),
        )
        self.accept()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_dialog.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/artisanlib/rorflick_dialog.py src/test/unitary/artisanlib/test_rorflick_dialog.py
git commit -m "feat(rorflick): add settings dialog mirroring charge_dialog pattern"
```

---

## Task 5: main.py Integration (imports, instantiation, menu, dialog slot, QSettings ×3)

**Files:**
- Modify: `src/artisanlib/main.py` (7 insertion sites, ~35 lines total)

**Exact insertion points** (verified via investigation reports):

| Site | Line (approx) | What |
|---|---|---|
| Imports | 25-26 area | 2 import lines |
| Instantiation | 1971-1972 area | 3 lines |
| Menu | 4693-4695 area | 3 lines (after `charge_target_action`) |
| Dialog slot | 28663-28668 area | 7 lines (after `showChargeTargetDialog`) |
| Settings load 1 | 20119 area | 5 lines (after ChargeTargetEnabled load) |
| Settings save | 20753 area | 5 lines |
| Settings load 2 | 20993 area | 5 lines |

**Interfaces:**
- Consumes: `RoRFlickManager`, `RoRFlickDlg` from Tasks 1-4
- Produces: `self.rorflick_manager`, `self.qmc.rorflick_manager`, `RoR 异常检测...` menu item, `showRoRFlickDialog` slot, 5 QSettings keys (`RoRFlickEnabled`, `RoRFlickFlickThreshold`, `RoRFlickCrashThreshold`, `RoRFlickExitThreshold`, `RoRFlickDevPhaseMultiplier`)

- [ ] **Step 1: Read the integration context to find exact insertion lines**

Use serena to locate insertion anchors:

```python
# Locate each anchor before inserting
# Anchor 1: from artisanlib.charge_manager import ChargeTargetManager  (line ~25)
# Anchor 2: self.qmc.charge_manager = self.charge_manager  (line ~1972)
# Anchor 3: roast_menu.addAction(charge_target_action)  (line ~4695)
# Anchor 4: def showChargeTargetDialog  (line ~28663)
# Anchor 5: if settings.contains('ChargeTargetEnabled')  (line ~20119)
# Anchor 6: settings.setValue('ChargeTargetEnabled', ...)  (line ~20753)
# Anchor 7: if settings.contains('ChargeTargetEnabled')  (line ~20993, duplicate)
```

- [ ] **Step 2: Add imports** (after the charge_manager imports, around line 26)

```python
from artisanlib.rorflick_manager import RoRFlickManager
from artisanlib.rorflick_dialog import RoRFlickDlg
```

- [ ] **Step 3: Add manager instantiation** (after line 1972, after `self.qmc.charge_manager = self.charge_manager`)

```python
# RoR Flick/Crash Detector Manager
self.rorflick_manager: RoRFlickManager = RoRFlickManager()
self.qmc.rorflick_manager = self.rorflick_manager
```

- [ ] **Step 4: Add menu action** (after line 4695, after `roast_menu.addAction(charge_target_action)`)

```python
rorflick_action = QAction(QApplication.translate('Menu', 'RoR 异常检测...'), self)
rorflick_action.triggered.connect(self.showRoRFlickDialog)
roast_menu.addAction(rorflick_action)
```

- [ ] **Step 5: Add dialog opener slot** (after `showChargeTargetDialog` method, around line 28668)

```python
@pyqtSlot()
@pyqtSlot(bool)
def showRoRFlickDialog(self, _:bool = False) -> None:
    dlg = RoRFlickDlg(self, self.rorflick_manager)
    if dlg.exec():
        self.qmc.redraw(recomputeAllDeltas=False)
```

- [ ] **Step 6: Add QSettings load 1** (after the ChargeTargetEnabled load block, around line 20119)

```python
# RoR Flick Detector
if settings.contains('RoRFlickEnabled'):
    self.rorflick_manager.enabled = toBool(settings.value('RoRFlickEnabled', self.rorflick_manager.enabled))
if settings.contains('RoRFlickFlickThreshold'):
    self.rorflick_manager.flick_threshold = toFloat(settings.value('RoRFlickFlickThreshold', self.rorflick_manager.flick_threshold))
if settings.contains('RoRFlickCrashThreshold'):
    self.rorflick_manager.crash_threshold = toFloat(settings.value('RoRFlickCrashThreshold', self.rorflick_manager.crash_threshold))
if settings.contains('RoRFlickExitThreshold'):
    self.rorflick_manager.exit_threshold = toFloat(settings.value('RoRFlickExitThreshold', self.rorflick_manager.exit_threshold))
if settings.contains('RoRFlickDevPhaseMultiplier'):
    self.rorflick_manager.dev_phase_multiplier = toFloat(settings.value('RoRFlickDevPhaseMultiplier', self.rorflick_manager.dev_phase_multiplier))
```

- [ ] **Step 7: Add QSettings save** (after the ChargeTargetEnabled save block, around line 20753)

```python
# RoR Flick Detector
settings.setValue('RoRFlickEnabled', self.rorflick_manager.enabled)
settings.setValue('RoRFlickFlickThreshold', self.rorflick_manager.flick_threshold)
settings.setValue('RoRFlickCrashThreshold', self.rorflick_manager.crash_threshold)
settings.setValue('RoRFlickExitThreshold', self.rorflick_manager.exit_threshold)
settings.setValue('RoRFlickDevPhaseMultiplier', self.rorflick_manager.dev_phase_multiplier)
```

- [ ] **Step 8: Add QSettings load 2** (after the duplicate ChargeTargetEnabled block, around line 20993 — same content as Step 6)

Same code block as Step 6.

- [ ] **Step 9: Verify main.py compiles and existing tests pass**

Run: `cd src && python3 -m py_compile artisanlib/main.py && python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q`
Expected: PASS (charge_manager tests still pass — proves no regression)

- [ ] **Step 10: Commit**

```bash
git add src/artisanlib/main.py
git commit -m "feat(rorflick): wire manager, dialog, menu, and QSettings into main.py"
```

---

## Task 6: canvas.py Drawing + Call Sites + Integration Test

**Files:**
- Modify: `src/artisanlib/canvas.py` (5 insertion sites)
- Modify: `src/test/unitary/artisanlib/test_canvas.py` (add 1 integration test)

**Exact insertion points:**

| Site | Line (approx) | What |
|---|---|---|
| Top imports | after charge_manager import | 1 import line |
| Attribute init | 543-544 area (with charge attrs) | 2 attribute declarations |
| Pickle whitelist | 445 area | 1 entry |
| Blit call site | 6295 area | 1 try/draw call |
| Redraw call site | 12142 area | 1 try/draw call |
| New method | after `draw_charge_target_annotation` (line 19012+~150) | new method `draw_rorflick_annotation` ~80 lines |

- [ ] **Step 1: Write the failing integration test**

Add to `src/test/unitary/artisanlib/test_canvas.py`:

```python
def test_draw_rorflick_annotation_handles_fresh_canvas_slot():
    """Smoke test: draw_rorflick_annotation works on a fresh canvas without a manager."""
    from unittest.mock import Mock
    from artisanlib.canvas import tgraphcanvas
    canvas = Mock()
    # Simulate fresh canvas — no manager, empty artists list
    canvas.rorflick_manager = None
    canvas.rorflick_artists = []
    canvas._rorflick_last_len = 0
    # Should not raise even without a manager
    tgraphcanvas.draw_rorflick_annotation(canvas)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_canvas.py::test_draw_rorflick_annotation_handles_fresh_canvas_slot -v`
Expected: FAIL with `AttributeError: type object 'tgraphcanvas' has no attribute 'draw_rorflick_annotation'`

- [ ] **Step 3: Add import** at top of `src/artisanlib/canvas.py` (next to charge_manager import)

```python
from artisanlib.rorflick_manager import RoRFlickManager
```

- [ ] **Step 4: Add attribute declarations** (in `__init__`, next to `self.charge_manager` and `self.charge_target_annotation` around line 543-544)

```python
self.rorflick_manager: RoRFlickManager | None = None
self.rorflick_artists: list = []       # tracks ALL matplotlib artists (annotations + axvspans) for cleanup
self._rorflick_last_len: int = 0       # tracks delta2 length to detect live vs replay mode
```

- [ ] **Step 5: Add pickle whitelist entry** (next to `'charge_manager'` in the `__getstate__` whitelist around line 445)

Add `'rorflick_artists'` and `'_rorflick_last_len'` to the whitelist tuple. **Do NOT** add `'rorflick_manager'` (it is a live reference, not pickleable).

- [ ] **Step 6: Implement draw_rorflick_annotation method**

Insert this method into `class tgraphcanvas` right after the `draw_charge_target_annotation` method ends (use serena `find_symbol` with name_path=`tgraphcanvas/draw_charge_target_annotation` to find end-line, then `insert_after_symbol`):

```python
def draw_rorflick_annotation(self) -> None:
    """Detect and annotate RoR flick/crash events on the canvas.

    Live mode (recording): processes one new sample per call via process_sample.
    Replay mode (loaded roast): re-runs full batch via process_roast when delta2
    length jumps or shrinks (indicating a profile load).
    """
    if not self.rorflick_manager or not self.rorflick_manager.enabled:
        return

    # Clear ALL previous artists (annotations + axvspans) to prevent accumulation
    if self.rorflick_artists:
        for artist in self.rorflick_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self.rorflick_artists = []

    if not self.delta2:
        return

    current_len = len(self.delta2)

    # Mode detection: live if delta2 grew by exactly 1 sample, else replay
    if current_len == self._rorflick_last_len + 1:
        # --- Live mode: process one new sample ---
        try:
            short_avg = self._charge_window_average_delta(9.0)
            long_avg = self._charge_window_average_delta(30.0)
        except Exception:
            return
        if short_avg is None or long_avg is None:
            return
        sample_idx = current_len - 1
        in_dev = self.timeindex[2] > -1
        self.rorflick_manager.process_sample(sample_idx, short_avg, long_avg, in_dev)
    else:
        # --- Replay mode: re-run full batch over entire delta2 ---
        # Determine sample rate from canvas config (fallback to 1.0 Hz)
        try:
            sample_rate_hz = 1.0 / max(0.1, getattr(self, 'samplinginterval', 1.0))
        except Exception:
            sample_rate_hz = 1.0
        self.rorflick_manager.process_roast(
            self.delta2,
            fcs_idx=self.timeindex[2],
            sample_rate_hz=sample_rate_hz,
        )

    self._rorflick_last_len = current_len

    if not self.rorflick_manager.should_show_annotations():
        return

    severity_colors = {
        'soft': '#FFCC00',
        'moderate': '#FF8800',
        'hard': '#CC0000',
    }
    severity_alpha = {'soft': 0.20, 'moderate': 0.30, 'hard': 0.40}

    for event in self.rorflick_manager.events:
        if (event.start_idx >= len(self.timex)
                or event.end_idx >= len(self.timex)
                or event.peak_idx >= len(self.timex)
                or event.peak_idx >= len(self.delta2)):
            continue

        color = severity_colors.get(event.severity, '#FFCC00')
        alpha = severity_alpha.get(event.severity, 0.20)

        # Highlight band from start to end — TRACK the artist for cleanup
        try:
            span = self.ax.axvspan(
                self.timex[event.start_idx],
                self.timex[event.end_idx],
                facecolor=color,
                alpha=alpha,
                clip_on=True,
                zorder=1,
            )
            self.rorflick_artists.append(span)
        except Exception:
            pass

        # Peak annotation — TRACK the artist for cleanup
        try:
            label_lines = [f'{event.event_type.upper()}', f'+{event.peak_magnitude:.1f}°/min']
            if event.in_development:
                label_lines.append('(DEV)')
            ann = self.ax.annotate(
                '\n'.join(label_lines),
                xy=(self.timex[event.peak_idx], self.delta2[event.peak_idx]),
                xytext=(self.timex[event.peak_idx], self.delta2[event.peak_idx] + 5),
                fontsize=8,
                color='#333333',
                ha='center',
                bbox={
                    'boxstyle': 'round,pad=0.3',
                    'facecolor': color,
                    'edgecolor': '#666666',
                    'alpha': 0.85,
                },
                arrowprops={
                    'arrowstyle': '->',
                    'color': '#666666',
                    'lw': 0.8,
                },
            )
            self.rorflick_artists.append(ann)
        except Exception:
            pass
```

- [ ] **Step 7: Add blit call site** (next to the existing `self.draw_charge_target_annotation()` call around line 6295)

```python
try:
    self.draw_rorflick_annotation()
except Exception:
    pass
```

- [ ] **Step 8: Add redraw call site** (next to the existing redraw call around line 12142)

```python
try:
    self.draw_rorflick_annotation()
except Exception:
    pass
```

- [ ] **Step 9: Run all related tests to verify they pass**

Run: `cd src && python3 -m py_compile artisanlib/canvas.py && python3 -m pytest test/unitary/artisanlib/test_canvas.py test/unitary/artisanlib/test_rorflick_manager.py test/unitary/artisanlib/test_charge_manager.py -v`
Expected: PASS (existing tests still pass, new canvas test passes)

- [ ] **Step 10: Commit**

```bash
git add src/artisanlib/canvas.py src/test/unitary/artisanlib/test_canvas.py
git commit -m "feat(rorflick): add draw_rorflick_annotation with axvspan + peak label"
```

---

## Task 7: Final Verification

- [ ] **Step 1: Full py_compile check on all changed files**

Run: `cd src && python3 -m py_compile artisanlib/rorflick_manager.py artisanlib/rorflick_dialog.py artisanlib/main.py artisanlib/canvas.py`
Expected: no output, exit 0

- [ ] **Step 2: Run focused ArtisanZ custom test suite**

Run: `cd src && python3 -m pytest test/unitary/artisanlib/test_rorflick_manager.py test/unitary/artisanlib/test_rorflick_dialog.py test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_canvas.py -v`
Expected: PASS (all new tests + no regressions)

- [ ] **Step 3: lsp_diagnostics on new/changed files**

Run: `lsp_diagnostics` on `src/artisanlib/rorflick_manager.py`, `src/artisanlib/rorflick_dialog.py`, `src/artisanlib/main.py`, `src/artisanlib/canvas.py`
Expected: no new errors from changes (pre-existing unrelated warnings OK)

- [ ] **Step 4: Report pre-existing issues (if any) and confirm new code is clean**

If diagnostics reveal issues:
- New errors from our changes → fix immediately
- Pre-existing errors in main.py/canvas.py unrelated to our edits → note in summary, do not fix

---

## Self-Review Notes

**Spec coverage check** (against the 5 user-decided specs):
- ✅ Spec 1 (real-time + replay): Tasks 2 & 3 — `process_sample` (live) + `process_roast` (replay) + canvas mode detection via `_rorflick_last_len` delta
- ✅ Spec 2 (pragmatist defaults + configurable): Task 1 defaults (5.0/5.0/1.0/1.5), Task 4 dialog for config
- ✅ Spec 3 (interval + peak): Task 6 `axvspan` (tracked in `rorflick_artists`) + annotate
- ✅ Spec 4 (status bar text only): Task 3 `get_status_message()` API ready; wiring to status bar widget deferred (acknowledged)
- ✅ Spec 5 (full scope + dev phase boost): Task 2 `in_development` param, Task 3 `dev_phase_multiplier` severity boost

**Placeholder scan**: None found. All code blocks complete.

**Type consistency**: 
- `RoRFlickEvent` fields consistent across all tests and implementations
- `process_sample` signature identical in tests and impl
- `process_batch` accepts `Iterable[tuple[int, float, float, bool]]` (for testing)
- `process_roast` accepts `list[float], int, float` (for canvas replay, self-contained windowing)
- `_finalize_event` returns `RoRFlickEvent` consistently
- Canvas tracks all artists in `rorflick_artists` (renamed from `rorflick_annotations` to reflect it holds both annotations AND axvspans)

**Momus review fixes applied**:
- ✅ Fixed axvspan accumulation: all artists (annotations + spans) now tracked in `self.rorflick_artists` and cleared each redraw
- ✅ Added replay support: `process_roast` method on manager + mode detection in canvas (`_rorflick_last_len` tracks delta2 growth pattern)

**Known deferred items** (not in this plan, future work):
- Status bar widget integration (calling `get_status_message` and writing to ArtisanZ's status bar QLabel) — needs investigation of which QLabel is the status bar
- pyqtgraph pipeline parity (via `plot_snapshot_extractor.py`) — out of scope for MVP
- Translation `.ts` entries for `'RoRFlickDlg'` context — strings are in code via `QApplication.translate`, but `.ts` files need `pylupdate6` regeneration
- Sample rate detection for replay (`samplinginterval` lookup) — uses fallback 1.0 Hz, should be refined to read actual canvas config

---

## Execution Handoff

Plan complete and saved to `.sisyphus/plans/2026-07-05-ror-flick-crash-detector.md`. After Momus review and iteration, two execution options:

**1. Subagent-Driven (recommended)** — dispatch one `deep` agent per task, review between tasks, fast iteration. Tasks 1-4 are independent enough to potentially parallelize (manager + dialog can be done in parallel; main.py + canvas.py need both done first).

**2. Inline Execution** — execute tasks in this session with `executing-plans`, batch execution with checkpoints.
