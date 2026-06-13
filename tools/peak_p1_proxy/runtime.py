from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import serial

from .cache import TemperatureCache
from .modbus_rtu import (
    ModbusRtuError,
    build_exception_response,
    build_read_input_registers_response,
    parse_request,
)
from .model import SerialSettings, TemperatureSample
from .p1_protocol import format_artisan_read_response, parse_p1_group_response

_log = logging.getLogger(__name__)


class SerialLike(Protocol):
    def write(self, data: bytes) -> int: ...
    def flush(self) -> None: ...
    def readline(self) -> bytes: ...


class ByteSerialLike(SerialLike, Protocol):
    def read(self, size: int = 1) -> bytes: ...


class FrameLogger:
    def __init__(self, path: str | None) -> None:
        self._path = Path(path) if path else None
        self._lock = threading.Lock()

    def log(self, channel: str, direction: str, payload: bytes | str) -> None:
        if self._path is None:
            return
        if isinstance(payload, bytes):
            value = payload.hex()
        else:
            value = payload.replace("\r", "\\r").replace("\n", "\\n")
        with self._lock:
            with self._path.open("a", encoding="utf-8") as out:
                out.write(f"{time.time():.3f} {channel} {direction} {value}\n")


class P1Poller:
    def __init__(
        self,
        serial_port: SerialLike,
        cache: TemperatureCache,
        clock: Callable[[], float] | None = None,
        frame_logger: FrameLogger | None = None,
    ) -> None:
        self._serial = serial_port
        self._cache = cache
        self._clock = clock or time.monotonic
        self._frame_logger = frame_logger or FrameLogger(None)

    def _write_line(self, line: str) -> None:
        data = line.encode("ascii")
        self._frame_logger.log("p1", "tx", data)
        self._serial.write(data)
        self._serial.flush()

    def _read_line(self) -> str:
        data = self._serial.readline()
        self._frame_logger.log("p1", "rx", data)
        return data.decode("utf-8", "ignore").strip()

    def _read_group(self, group: str):
        self._write_line(f"CHAN;{group}\n")
        ack = self._read_line()
        if ack and not ack.startswith("#"):
            raise RuntimeError(f"Peak P1 rejected channel group {group}: {ack!r}")
        self._write_line("READ\n")
        return parse_p1_group_response(group, self._read_line())

    def poll_once(self) -> TemperatureSample:
        bt_et = self._read_group("3400")
        exhaust_inlet = self._read_group("1200")
        if bt_et.bt is None or bt_et.et is None:
            raise RuntimeError("Peak P1 3400 response did not include BT/ET")
        if exhaust_inlet.exhaust is None or exhaust_inlet.inlet is None:
            raise RuntimeError("Peak P1 1200 response did not include Exhaust/Inlet")
        sample = TemperatureSample(
            bt=bt_et.bt,
            et=bt_et.et,
            exhaust=exhaust_inlet.exhaust,
            inlet=exhaust_inlet.inlet,
            at=bt_et.at,
            timestamp=self._clock(),
        )
        self._cache.update(sample)
        return sample

    def run(self, stop_event: threading.Event, poll_interval: float) -> None:
        while not stop_event.is_set():
            try:
                sample = self.poll_once()
                _log.info(
                    "P1 BT %.2f ET %.2f Exhaust %.2f Inlet %.2f",
                    sample.bt,
                    sample.et,
                    sample.exhaust,
                    sample.inlet,
                )
            except Exception as exc:  # pylint: disable=broad-except
                _log.warning("Peak P1 poll failed: %s", exc)
            stop_event.wait(poll_interval)


class ArtisanTc4Responder:
    def __init__(self, cache: TemperatureCache) -> None:
        self._cache = cache
        self._group = "3400"

    def handle_line(self, command: str) -> bytes:
        command = command.strip()
        if command.startswith("CHAN;"):
            group = command.split(";", 1)[1]
            if group in {"3400", "1200"}:
                self._group = group
            return b"#\r\n"
        if command == "READ":
            if self._cache.is_stale():
                return format_artisan_read_response(-1.0, -1.0, -1.0).encode("ascii")
            sample = self._cache.get()
            if sample is None:
                return format_artisan_read_response(-1.0, -1.0, -1.0).encode("ascii")
            if self._group == "1200":
                return format_artisan_read_response(sample.at, sample.exhaust, sample.inlet).encode("ascii")
            return format_artisan_read_response(sample.at, sample.bt, sample.et).encode("ascii")
        return b"\r\n"


class CropsterModbusResponder:
    def __init__(
        self,
        cache: TemperatureCache,
        slave_id: int = 1,
        bt_register: int = 0,
        exhaust_register: int = 3,
        register_3_source: str = "exhaust",
    ) -> None:
        self._cache = cache
        self._slave_id = slave_id
        self._bt_register = bt_register
        self._exhaust_register = exhaust_register
        self._register_3_source = register_3_source

    def _registers_for(self, sample: TemperatureSample) -> dict[int, float]:
        exhaust_value = sample.et if self._register_3_source == "et" else sample.exhaust
        return {
            self._bt_register: sample.bt,
            self._exhaust_register: exhaust_value,
        }

    def handle_frame(self, frame: bytes) -> bytes:
        try:
            request = parse_request(frame)
        except ModbusRtuError as exc:
            _log.debug("ignoring malformed Modbus frame: %s", exc)
            return b""

        if request.slave_id != self._slave_id:
            return build_exception_response(request.slave_id, request.function, 4)
        if request.function != 4:
            return build_exception_response(request.slave_id, request.function, 1)
        if self._cache.is_stale():
            return build_exception_response(request.slave_id, request.function, 4)
        sample = self._cache.get()
        if sample is None:
            return build_exception_response(request.slave_id, request.function, 4)
        return build_read_input_registers_response(request, self._registers_for(sample))


class ArtisanSerialServer:
    def __init__(
        self,
        serial_port: SerialLike,
        responder: ArtisanTc4Responder,
        frame_logger: FrameLogger | None = None,
    ) -> None:
        self._serial = serial_port
        self._responder = responder
        self._frame_logger = frame_logger or FrameLogger(None)

    def run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            line = self._serial.readline()
            if not line:
                continue
            self._frame_logger.log("artisan", "rx", line)
            response = self._responder.handle_line(line.decode("utf-8", "ignore"))
            if response:
                self._frame_logger.log("artisan", "tx", response)
                self._serial.write(response)
                self._serial.flush()


class CropsterSerialServer:
    def __init__(
        self,
        serial_port: ByteSerialLike,
        responder: CropsterModbusResponder,
        frame_logger: FrameLogger | None = None,
    ) -> None:
        self._serial = serial_port
        self._responder = responder
        self._frame_logger = frame_logger or FrameLogger(None)
        self._buffer = bytearray()

    def _read_frame(self) -> bytes | None:
        while len(self._buffer) < 8:
            chunk = self._serial.read(8 - len(self._buffer))
            if not chunk:
                return None
            self._buffer.extend(chunk)
        frame = bytes(self._buffer[:8])
        del self._buffer[:8]
        return frame

    def run_once(self) -> None:
        frame = self._read_frame()
        if frame is None:
            return
        self._frame_logger.log("cropster", "rx", frame)
        response = self._responder.handle_frame(frame)
        if response:
            self._frame_logger.log("cropster", "tx", response)
            self._serial.write(response)
            self._serial.flush()

    def run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            self.run_once()


def open_serial(settings: SerialSettings):
    return serial.serial_for_url(
        settings.port,
        baudrate=settings.baudrate,
        bytesize=settings.bytesize,
        parity=settings.parity,
        stopbits=settings.stopbits,
        timeout=settings.timeout,
    )


class ProxyRuntime:
    def __init__(
        self,
        real_settings: SerialSettings,
        artisan_settings: SerialSettings,
        cropster_settings: SerialSettings,
        poll_interval: float,
        stale_after: float,
        frame_log_path: str | None = None,
        cropster_bt_register: int = 0,
        cropster_exhaust_register: int = 3,
        cropster_register_3_source: str = "exhaust",
    ) -> None:
        self._real_settings = real_settings
        self._artisan_settings = artisan_settings
        self._cropster_settings = cropster_settings
        self._poll_interval = poll_interval
        self._stale_after = stale_after
        self._frame_log_path = frame_log_path
        self._cropster_bt_register = cropster_bt_register
        self._cropster_exhaust_register = cropster_exhaust_register
        self._cropster_register_3_source = cropster_register_3_source
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        frame_logger = FrameLogger(self._frame_log_path)
        cache = TemperatureCache(stale_after=self._stale_after)
        with open_serial(self._real_settings) as real_port, open_serial(
            self._artisan_settings
        ) as artisan_port, open_serial(self._cropster_settings) as cropster_port:
            poller = P1Poller(real_port, cache, frame_logger=frame_logger)
            artisan = ArtisanSerialServer(
                artisan_port,
                ArtisanTc4Responder(cache),
                frame_logger=frame_logger,
            )
            cropster = CropsterSerialServer(
                cropster_port,
                CropsterModbusResponder(
                    cache,
                    bt_register=self._cropster_bt_register,
                    exhaust_register=self._cropster_exhaust_register,
                    register_3_source=self._cropster_register_3_source,
                ),
                frame_logger=frame_logger,
            )
            self._threads = [
                threading.Thread(target=poller.run, args=(self._stop_event, self._poll_interval), daemon=True),
                threading.Thread(target=artisan.run, args=(self._stop_event,), daemon=True),
                threading.Thread(target=cropster.run, args=(self._stop_event,), daemon=True),
            ]
            for thread in self._threads:
                thread.start()
            while not self._stop_event.is_set():
                self._stop_event.wait(0.5)
