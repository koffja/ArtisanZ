"""Tests for the threaded dev-simulator WebSocket wrapper."""

from __future__ import annotations

import asyncio
import json

from websockets.asyncio.client import connect

from dev_simulator.threaded_ws_server import build_threaded_artisan_simulator


def test_threaded_artisan_simulator_serves_get_data_and_stops() -> None:
    asyncio.run(_exercise_threaded_artisan_simulator())


async def _exercise_threaded_artisan_simulator() -> None:
    server = build_threaded_artisan_simulator(port=0, fixed_step_ms=30_000.0)

    try:
        server.start()
        assert server.is_running
        assert server.server.port > 0

        async with connect(f'ws://127.0.0.1:{server.server.port}/WebSocket') as websocket:
            await websocket.send(json.dumps({'command': 'getData', 'id': 7, 'roasterID': 0}))
            messages = []
            for _ in range(3):
                try:
                    raw = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                except TimeoutError:
                    break
                messages.append(json.loads(raw))

        data_message = next(message for message in messages if message.get('id') == 7)
        assert set(data_message['data']) == {'BT', 'ET'}
        assert {'pushMessage': 'startRoasting'} in messages
    finally:
        server.stop()

    assert server._stopped.wait(0.1)
    assert not server.is_running
