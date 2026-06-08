"""Integration tests for the dev simulator WebSocket server."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
import pytest_asyncio
import websockets

from dev_simulator.event_scheduler import EventScheduler
from dev_simulator.profile import RoastSpec, generate_profile
from dev_simulator.ws_server import AsyncServer, ServerState


def _default_events() -> list[tuple[float, dict[str, Any]]]:
    return [
        (0.0, {"pushMessage": "startRoasting"}),
        (300.0, {"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}),
        (570.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}),
        (645.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}),
        (765.0, {"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}),
        (780.0, {"pushMessage": "endRoasting"}),
    ]


@pytest.fixture
def server_port(unused_tcp_port_factory: Any) -> int:
    return int(unused_tcp_port_factory())


@pytest_asyncio.fixture
async def running_server(server_port: int):
    profile = generate_profile(RoastSpec(noise_model="none", noise_std=0.0))
    scheduler = EventScheduler(_default_events(), start_mode="auto")
    server = AsyncServer(
        profile=profile,
        scheduler=scheduler,
        host="127.0.0.1",
        port=server_port,
        noise_model="none",
        noise_std=0.0,
    )
    task = asyncio.create_task(server.run())
    await asyncio.sleep(0.05)
    try:
        yield server, server_port
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def _collect_messages(ws: Any, count: int = 3) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for _ in range(count):
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
        except asyncio.TimeoutError:
            break
        messages.append(json.loads(raw))
    return messages


async def _send_get_data(ws: Any, request_id: int) -> list[dict[str, Any]]:
    await ws.send(json.dumps({"command": "getData", "id": request_id, "roasterID": 0}))
    return await _collect_messages(ws, count=4)


class TestServerState:
    def test_first_advance_starts_at_zero(self) -> None:
        state = ServerState()

        assert state.advance() == 0.0
        assert state.frozen is False

    def test_long_pause_freezes_time_without_jump(self) -> None:
        state = ServerState()
        state.advance()
        state.sim_t_ms = 1234.0
        state.last_request_monotonic -= 31.0

        assert state.advance() == 1234.0
        assert state.frozen is True


class TestAsyncServerIntegration:
    @pytest.mark.asyncio
    async def test_id_echo(self, running_server: tuple[AsyncServer, int]) -> None:
        _, port = running_server
        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            messages = await _send_get_data(ws, request_id=42)

        data_messages = [message for message in messages if message.get("id") == 42]
        assert len(data_messages) == 1
        assert set(data_messages[0]["data"]) == {"BT", "ET"}

    @pytest.mark.asyncio
    async def test_event_push_on_first_request(self, running_server: tuple[AsyncServer, int]) -> None:
        _, port = running_server
        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            messages = await _send_get_data(ws, request_id=1)

        assert {"pushMessage": "startRoasting"} in messages

    @pytest.mark.asyncio
    async def test_bt_et_values_at_start(self, running_server: tuple[AsyncServer, int]) -> None:
        _, port = running_server
        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            messages = await _send_get_data(ws, request_id=7)

        data_message = next(message for message in messages if message.get("id") == 7)
        assert data_message["data"]["BT"] == 180.0
        assert data_message["data"]["ET"] == 190.0

    @pytest.mark.asyncio
    async def test_disconnect_reconnect(self, running_server: tuple[AsyncServer, int]) -> None:
        _, port = running_server
        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            await _send_get_data(ws, request_id=1)

        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            messages = await _send_get_data(ws, request_id=2)

        assert any(message.get("id") == 2 for message in messages)

    @pytest.mark.asyncio
    async def test_malformed_json_does_not_disconnect(self, running_server: tuple[AsyncServer, int]) -> None:
        _, port = running_server
        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            await ws.send("not json {{{")
            messages = await _send_get_data(ws, request_id=99)

        assert any(message.get("id") == 99 for message in messages)

    @pytest.mark.asyncio
    async def test_unknown_command_is_ignored(self, running_server: tuple[AsyncServer, int]) -> None:
        _, port = running_server
        async with websockets.connect(f"ws://127.0.0.1:{port}/WebSocket") as ws:
            await ws.send(json.dumps({"command": "noop", "id": 1}))
            messages = await _collect_messages(ws, count=1)

        assert messages == []
