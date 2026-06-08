"""Tests for EventScheduler fire-once semantics."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable

import pytest

from dev_simulator.event_scheduler import EventScheduler


def _default_events() -> list[tuple[float, dict[str, Any]]]:
    """Standard 6-event schedule per design spec section 5.5."""
    return [
        (0.0, {"pushMessage": "startRoasting"}),
        (300.0, {"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}),
        (570.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}),
        (645.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}),
        (765.0, {"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}),
        (780.0, {"pushMessage": "endRoasting"}),
    ]


def _run(coro: Awaitable[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class Recorder:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send(self, message: dict[str, Any]) -> None:
        self.messages.append(message)


class TestFireDueTiming:
    def test_dont_fire_early(self) -> None:
        scheduler = EventScheduler(_default_events())
        recorder = Recorder()

        fired = _run(scheduler.fire_due(0.0, recorder.send))

        assert fired == [{"pushMessage": "startRoasting"}]
        assert recorder.messages == fired

    def test_fire_at_exact_time(self) -> None:
        scheduler = EventScheduler(_default_events())
        recorder = Recorder()

        fired = _run(scheduler.fire_due(300.0, recorder.send))

        assert fired == [
            {"pushMessage": "startRoasting"},
            {"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}},
        ]
        assert recorder.messages == fired

    def test_fire_all(self) -> None:
        scheduler = EventScheduler(_default_events())
        recorder = Recorder()

        fired = _run(scheduler.fire_due(780.0, recorder.send))

        assert len(fired) == 6
        assert recorder.messages == fired
        assert fired[0] == {"pushMessage": "startRoasting"}
        assert fired[-1] == {"pushMessage": "endRoasting"}


class TestExactlyOnce:
    def test_skip_already_fired(self) -> None:
        scheduler = EventScheduler(_default_events())
        recorder = Recorder()

        first = _run(scheduler.fire_due(300.0, recorder.send))
        second = _run(scheduler.fire_due(300.0, recorder.send))

        assert len(first) == 2
        assert second == []
        assert len(recorder.messages) == 2

    def test_partial_fire_then_continue(self) -> None:
        scheduler = EventScheduler(_default_events())
        recorder = Recorder()

        first = _run(scheduler.fire_due(570.0, recorder.send))
        second = _run(scheduler.fire_due(780.0, recorder.send))

        assert len(first) == 3
        assert len(second) == 3
        assert len(recorder.messages) == 6
        assert recorder.messages[1]["data"]["event"] == "colorChangeEvent"
        assert recorder.messages[2]["data"]["event"] == "firstCrackBeginningEvent"
        assert recorder.messages[3]["data"]["event"] == "firstCrackEndEvent"
        assert recorder.messages[4]["data"]["event"] == "secondCrackBeginningEvent"


class TestStartMode:
    def test_manual_mode_skips_charge(self) -> None:
        scheduler = EventScheduler(_default_events(), start_mode="manual")
        recorder = Recorder()

        fired = _run(scheduler.fire_due(0.0, recorder.send))

        assert fired == []
        assert recorder.messages == []

    def test_manual_mode_fires_other_events(self) -> None:
        scheduler = EventScheduler(_default_events(), start_mode="manual")
        recorder = Recorder()

        fired = _run(scheduler.fire_due(780.0, recorder.send))

        assert len(fired) == 5
        assert len(recorder.messages) == 5
        assert all(message.get("pushMessage") != "startRoasting" for message in fired)
        assert fired[0] == {"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}

    def test_manual_mode_reset_keeps_charge_suppressed(self) -> None:
        scheduler = EventScheduler(_default_events(), start_mode="manual")
        recorder = Recorder()

        assert _run(scheduler.fire_due(0.0, recorder.send)) == []
        scheduler.reset()
        assert _run(scheduler.fire_due(0.0, recorder.send)) == []
        assert recorder.messages == []


class TestReset:
    def test_reset_allows_refire(self) -> None:
        scheduler = EventScheduler(_default_events())
        recorder = Recorder()

        first = _run(scheduler.fire_due(780.0, recorder.send))
        scheduler.reset()
        second = _run(scheduler.fire_due(780.0, recorder.send))

        assert len(first) == 6
        assert len(second) == 6
        assert len(recorder.messages) == 12


class TestConstruction:
    def test_events_sorted_by_time(self) -> None:
        unsorted_events = [
            (780.0, {"pushMessage": "endRoasting"}),
            (0.0, {"pushMessage": "startRoasting"}),
            (570.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}),
            (300.0, {"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}),
            (765.0, {"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}),
            (645.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}),
        ]
        scheduler = EventScheduler(unsorted_events)
        recorder = Recorder()

        fired = _run(scheduler.fire_due(780.0, recorder.send))

        assert fired == _default_events_messages()
        assert recorder.messages == fired

    def test_empty_events(self) -> None:
        scheduler = EventScheduler([])
        recorder = Recorder()

        fired = _run(scheduler.fire_due(1000.0, recorder.send))

        assert fired == []
        assert recorder.messages == []

    def test_unknown_start_mode_raises(self) -> None:
        with pytest.raises(ValueError):
            EventScheduler(_default_events(), start_mode="bogus")


def _default_events_messages() -> list[dict[str, Any]]:
    return [message for _, message in _default_events()]
