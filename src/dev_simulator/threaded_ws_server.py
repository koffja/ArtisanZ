"""Threaded WebSocket simulator helpers for GUI autorun validation."""

from __future__ import annotations

import asyncio
import logging
from threading import Event, Thread
from typing import Any

from websockets.asyncio.server import serve

from dev_simulator.event_scheduler import EventScheduler
from dev_simulator.profile import RoastSpec, generate_profile
from dev_simulator.ws_server import AsyncServer

_log = logging.getLogger(__name__)


class ThreadedWebSocketServer:
    """Run an AsyncServer in a daemon thread with an explicit stop hook."""

    def __init__(self, server: AsyncServer, *, startup_timeout: float = 4.0) -> None:
        self.server = server
        self.startup_timeout = startup_timeout
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None
        self._thread: Thread | None = None
        self._ready = Event()
        self._stopped = Event()
        self._exception: BaseException | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and self._exception is None

    def start(self) -> None:
        if self.is_running:
            return

        self._ready.clear()
        self._stopped.clear()
        self._exception = None
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(
            target=self._run_loop,
            name='ArtisanZWebSocketSimulator',
            daemon=True,
        )
        self._thread.start()

        if not self._ready.wait(self.startup_timeout):
            self.stop()
            raise TimeoutError('Timed out starting threaded WebSocket simulator')
        if self._exception is not None:
            raise RuntimeError('Could not start threaded WebSocket simulator') from self._exception

    def stop(self, timeout: float = 3.0) -> None:
        loop = self._loop
        stop_event = self._stop_event
        if loop is not None and stop_event is not None and loop.is_running():
            loop.call_soon_threadsafe(stop_event.set)

        thread = self._thread
        if thread is not None:
            thread.join(timeout)
            if thread.is_alive() and loop is not None and loop.is_running():
                loop.call_soon_threadsafe(loop.stop)
                thread.join(timeout)
            if thread.is_alive():
                raise TimeoutError('Timed out stopping threaded WebSocket simulator')

        self._thread = None
        self._loop = None
        self._stop_event = None

    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.create_task(self._run_server())
            self._loop.run_forever()
        finally:
            pending = [task for task in asyncio.all_tasks(self._loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._loop.close()
            self._stopped.set()

    async def _run_server(self) -> None:
        try:
            self._stop_event = asyncio.Event()
            async with serve(self.server.handle, self.server.host, self.server.port) as websocket_server:
                sockets = websocket_server.sockets or ()
                if sockets:
                    sockname = sockets[0].getsockname()
                    if isinstance(sockname, tuple) and len(sockname) >= 2:
                        self.server.port = int(sockname[1])
                _log.info(
                    'Threaded simulator listening on ws://%s:%s/%s',
                    self.server.host,
                    self.server.port,
                    self.server.path,
                )
                self._ready.set()
                await self._stop_event.wait()
        except BaseException as exc:  # pylint: disable=broad-except
            self._exception = exc
            self._ready.set()
        finally:
            loop = asyncio.get_running_loop()
            loop.call_soon(loop.stop)


def build_threaded_artisan_simulator(
        *,
        host: str = '127.0.0.1',
        port: int = 0,
        path: str = 'WebSocket',
        fixed_step_ms: float | None = 30_000.0,
        noise_model: str = 'none',
        noise_std: float = 0.0) -> ThreadedWebSocketServer:
    """Build a deterministic medium-roast WebSocket simulator for GUI tests."""
    profile = generate_profile(RoastSpec(noise_model=noise_model, noise_std=noise_std))
    server = AsyncServer(
        profile=profile,
        scheduler=EventScheduler(_default_events(), start_mode='auto'),
        host=host,
        port=port,
        path=path,
        noise_model=noise_model,
        noise_std=noise_std,
        fixed_step_ms=fixed_step_ms,
    )
    return ThreadedWebSocketServer(server)


def _default_events() -> list[tuple[float, dict[str, Any]]]:
    return [
        (0.0, {'pushMessage': 'startRoasting'}),
        (300.0, {'pushMessage': 'addEvent', 'data': {'event': 'colorChangeEvent'}}),
        (570.0, {'pushMessage': 'addEvent', 'data': {'event': 'firstCrackBeginningEvent'}}),
        (645.0, {'pushMessage': 'addEvent', 'data': {'event': 'firstCrackEndEvent'}}),
        (765.0, {'pushMessage': 'addEvent', 'data': {'event': 'secondCrackBeginningEvent'}}),
        (780.0, {'pushMessage': 'endRoasting'}),
    ]


__all__ = [
    'ThreadedWebSocketServer',
    'build_threaded_artisan_simulator',
]
