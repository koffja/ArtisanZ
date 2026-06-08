"""Roast event scheduler for the ArtisanZ temperature simulator."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

_log = logging.getLogger(__name__)

EventMessage = dict[str, Any]
SendFunc = Callable[[EventMessage], Awaitable[None]]


class EventScheduler:
    """Fire configured roast events exactly once when simulated time reaches them."""

    _VALID_START_MODES = {"auto", "manual"}

    def __init__(
        self,
        events: list[tuple[float, EventMessage]],
        start_mode: str = "auto",
    ) -> None:
        if start_mode not in self._VALID_START_MODES:
            raise ValueError(f"Unknown start_mode: {start_mode!r}")
        self._events = sorted(events, key=lambda item: item[0])
        self._start_mode = start_mode
        self._fired: set[int] = set()

    async def fire_due(self, t: float, send: SendFunc) -> list[EventMessage]:
        """Send all events due at or before ``t`` that have not fired yet."""
        fired_messages: list[EventMessage] = []
        for index, (event_t, message) in enumerate(self._events):
            if index in self._fired:
                continue
            if t < event_t:
                continue
            self._fired.add(index)
            if self._start_mode == "manual" and message.get("pushMessage") == "startRoasting":
                _log.info("Suppressed automatic CHARGE event in manual mode")
                continue
            await send(message)
            fired_messages.append(message)
            _log.info("Fired event at %.1fs: %s", event_t, message)
        return fired_messages

    def reset(self) -> None:
        """Clear fired state so the same schedule can be replayed."""
        self._fired.clear()
