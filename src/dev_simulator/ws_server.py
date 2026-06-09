"""WebSocket server for the ArtisanZ temperature simulator."""

from __future__ import annotations

import json
import logging
import math
import random
import time
from typing import Any

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

from dev_simulator.event_scheduler import EventScheduler

_log = logging.getLogger(__name__)


class ServerState:
    """Simulated time state advanced only by incoming requests."""

    def __init__(self) -> None:
        self.sim_t_ms = 0.0
        self.last_request_monotonic = 0.0
        self.frozen = True

    def advance(self) -> float:
        """Advance simulated time and return the current time in milliseconds."""
        now = time.monotonic()
        if self.frozen:
            self.frozen = False
            self.last_request_monotonic = now
            return self.sim_t_ms

        elapsed_ms = (now - self.last_request_monotonic) * 1000.0
        if elapsed_ms > 30_000.0:
            self.frozen = True
            return self.sim_t_ms

        self.sim_t_ms += min(elapsed_ms, 3000.0)
        self.last_request_monotonic = now
        return self.sim_t_ms


class AsyncServer:
    """Serve synthetic BT/ET values over Artisan's WebSocket protocol."""

    def __init__(
        self,
        profile: dict[str, Any],
        scheduler: EventScheduler,
        host: str = "127.0.0.1",
        port: int = 80,
        path: str = "WebSocket",
        noise_model: str = "ar1",
        noise_std: float = 0.3,
    ) -> None:
        self.profile = profile
        self.scheduler = scheduler
        self.host = host
        self.port = port
        self.path = path.strip("/")
        self.noise_model = noise_model
        self.noise_std = noise_std
        self.state = ServerState()
        self._noise_state_et = 0.0
        self._noise_state_bt = 0.0

        self._timex = [float(v) for v in profile["timex"]]
        self._et = [float(v) for v in profile["temp1"]]
        self._bt = [float(v) for v in profile["temp2"]]
        if not (len(self._timex) == len(self._et) == len(self._bt)):
            raise ValueError("Profile arrays timex/temp1/temp2 must have equal length")
        if not self._timex:
            raise ValueError("Profile must contain at least one sample")

    async def handle(self, websocket: Any) -> None:
        """Handle a single WebSocket connection."""
        _log.info("WebSocket client connected")
        try:
            async for raw_message in websocket:
                await self._handle_message(websocket, raw_message)
        except ConnectionClosed:
            _log.info("WebSocket client disconnected")

    async def _handle_message(self, websocket: Any, raw_message: str | bytes) -> None:
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            _log.warning("Ignoring malformed JSON message: %r", raw_message)
            return

        if not isinstance(message, dict):
            _log.warning("Ignoring non-object JSON message: %r", message)
            return

        if message.get("command") != "getData":
            _log.debug("Ignoring unknown command: %r", message.get("command"))
            return

        sim_t_ms = self.state.advance()

        async def send_event(event_message: dict[str, Any]) -> None:
            await websocket.send(json.dumps(event_message))

        await self.scheduler.fire_due(sim_t_ms / 1000.0, send_event)

        et, bt = self._read_temperatures(sim_t_ms)
        response = {
            "id": message.get("id"),
            "data": {
                "BT": self._round_temperature(bt),
                "ET": self._round_temperature(et),
            },
        }
        await websocket.send(json.dumps(response, allow_nan=False))

    def _read_temperatures(self, tx_ms: float) -> tuple[float, float]:
        et = self._interp(tx_ms, self._et)
        bt = self._interp(tx_ms, self._bt)
        et = self._add_noise(et, channel="et")
        bt = self._add_noise(bt, channel="bt")
        return et, bt

    def _interp(self, tx_ms: float, values: list[float]) -> float:
        if tx_ms <= self._timex[0]:
            return values[0]
        if tx_ms >= self._timex[-1]:
            return values[-1]

        lo = 0
        hi = len(self._timex) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self._timex[mid] <= tx_ms:
                lo = mid
            else:
                hi = mid

        t0 = self._timex[lo]
        t1 = self._timex[hi]
        if t1 == t0:
            return values[lo]
        frac = (tx_ms - t0) / (t1 - t0)
        return values[lo] + (values[hi] - values[lo]) * frac

    def _add_noise(self, value: float, channel: str) -> float:
        if self.noise_model == "none" or self.noise_std == 0.0:
            return value
        if self.noise_model == "gaussian":
            return value + random.gauss(0.0, self.noise_std)
        if self.noise_model == "ar1":
            alpha = 0.85
            innovation_std = self.noise_std * math.sqrt(1.0 - alpha * alpha)
            if channel == "et":
                self._noise_state_et = alpha * self._noise_state_et + random.gauss(0.0, innovation_std)
                return value + self._noise_state_et
            self._noise_state_bt = alpha * self._noise_state_bt + random.gauss(0.0, innovation_std)
            return value + self._noise_state_bt
        raise ValueError(f"Unknown noise model: {self.noise_model!r}")

    @staticmethod
    def _round_temperature(value: float) -> float:
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Invalid temperature value: {value!r}")
        return round(max(0.0, min(500.0, value)), 2)

    async def run(self) -> None:
        """Run the server until cancelled."""
        _log.info("Server listening on ws://%s:%s/%s", self.host, self.port, self.path)
        async with serve(self.handle, self.host, self.port):
            await self._wait_forever()

    @staticmethod
    async def _wait_forever() -> None:
        import asyncio

        await asyncio.Future()
