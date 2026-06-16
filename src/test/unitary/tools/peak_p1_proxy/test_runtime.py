import threading

import pytest
import serial

from tools.peak_p1_proxy.cache import TemperatureCache
from tools.peak_p1_proxy.modbus_rtu import parse_request
from tools.peak_p1_proxy.model import SerialSettings, TemperatureSample
from tools.peak_p1_proxy.runtime import (
    ArtisanTc4Responder,
    CropsterModbusResponder,
    CropsterSerialServer,
    P1ModbusPoller,
    P1Poller,
    ReconnectingP1Runner,
)


class FakeSerial:
    def __init__(self, lines: list[bytes]) -> None:
        self.lines = list(lines)
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def flush(self) -> None:
        return None

    def readline(self) -> bytes:
        return self.lines.pop(0)


class FakeByteSerial(FakeSerial):
    def __init__(self, chunks: list[bytes]) -> None:
        super().__init__([])
        self.chunks = list(chunks)
        self.reset_input_buffer_calls = 0

    def reset_input_buffer(self) -> None:
        self.reset_input_buffer_calls += 1

    def read(self, size: int = 1) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        data = chunk[:size]
        rest = chunk[size:]
        if rest:
            self.chunks.insert(0, rest)
        return data


class ClosableFakeSerial:
    def __init__(self, should_fail: bool) -> None:
        self.should_fail = should_fail
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakePoller:
    def __init__(self, serial_port, cache, clock=None, frame_logger=None, **kwargs) -> None:
        self.serial_port = serial_port
        self.cache = cache
        self.calls = 0

    def poll_once(self):
        self.calls += 1
        if self.serial_port.should_fail:
            raise RuntimeError("short Modbus response: expected 3, got 0")
        current = sample(timestamp=10.0 + self.calls)
        self.cache.update(current)
        return current


def sample(timestamp: float = 10.0) -> TemperatureSample:
    return TemperatureSample(
        bt=159.8,
        et=171.5,
        exhaust=176.1,
        inlet=166.1,
        at=171.5,
        timestamp=timestamp,
    )


def test_poller_reads_both_groups_and_updates_cache() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    serial_port = FakeSerial(
        [
            b"#\r\n",
            b"171.51,159.82,171.51,C\r\n",
            b"#\r\n",
            b"171.51,176.10,166.09,C\r\n",
        ]
    )
    poller = P1Poller(serial_port=serial_port, cache=cache, clock=lambda: 10.0)

    current = poller.poll_once()

    assert serial_port.writes == [b"CHAN;3400\n", b"READ\n", b"CHAN;1200\n", b"READ\n"]
    assert current.bt == 159.82
    assert current.et == 171.51
    assert current.exhaust == 176.10
    assert current.inlet == 166.09
    assert cache.get() == current


def test_modbus_poller_reads_register_block_and_updates_cache() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    serial_port = FakeByteSerial([bytes.fromhex("010408063c0692064c06b022d4")])
    poller = P1ModbusPoller(serial_port=serial_port, cache=cache, clock=lambda: 10.0)

    current = poller.poll_once()

    assert serial_port.writes == [bytes.fromhex("010400000004f1c9")]
    assert current.bt == 159.6
    assert current.et == 171.2
    assert current.exhaust == 171.2
    assert current.inlet == 168.2
    assert current.at == 171.2
    assert cache.get() == current


def test_modbus_poller_rejects_short_register_response_before_indexing() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    serial_port = FakeByteSerial([bytes.fromhex("01040204abfa4f")])
    poller = P1ModbusPoller(serial_port=serial_port, cache=cache, clock=lambda: 10.0)

    with pytest.raises(
        RuntimeError,
        match="short Modbus register response: expected at least 4 registers, got 1",
    ):
        poller.poll_once()

    assert cache.get() is None


def test_modbus_poller_clears_input_buffer_before_request_when_supported() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    serial_port = FakeByteSerial([bytes.fromhex("010408063c0692064c06b022d4")])
    poller = P1ModbusPoller(serial_port=serial_port, cache=cache, clock=lambda: 10.0)

    poller.poll_once()

    assert serial_port.reset_input_buffer_calls == 1


def test_reconnecting_runner_reopens_real_port_after_repeated_poll_failures() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    opened = [ClosableFakeSerial(True), ClosableFakeSerial(True), ClosableFakeSerial(False)]
    sleeps: list[float] = []

    def opener(settings: SerialSettings):
        return opened.pop(0)

    runner = ReconnectingP1Runner(
        real_settings=SerialSettings("COM5"),
        cache=cache,
        poller_factory=FakePoller,
        open_serial_fn=opener,
        poll_interval=0.0,
        reconnect_after_failures=1,
        reconnect_delay=0.25,
        sleep_fn=sleeps.append,
    )

    runner.run_once()
    runner.run_once()
    current = runner.run_once()

    assert current is not None
    assert current.bt == 159.8
    assert sleeps == [0.25, 0.25]
    assert cache.get() == current


def test_artisan_responder_returns_3400_cache_as_tc4_line() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = ArtisanTc4Responder(cache)

    assert responder.handle_line("CHAN;3400") == b"#\r\n"
    assert responder.handle_line("READ") == b"171.50,159.80,171.50,C\r\n"


def test_artisan_responder_returns_invalid_values_when_cache_is_stale() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    cache.update(sample(timestamp=10.0))
    responder = ArtisanTc4Responder(cache)

    assert responder.handle_line("CHAN;1200") == b"#\r\n"
    assert responder.handle_line("READ") == b"-1.00,-1.00,-1.00,C\r\n"


def test_cropster_responder_returns_modbus_registers_from_cache() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache)
    request = bytes.fromhex("010400000004f1c9")

    response = responder.handle_frame(request)

    parsed_request = parse_request(request)
    assert parsed_request.start_register == 0
    assert response == bytes.fromhex("010408063e0000000006e1b80c")


def test_cropster_responder_returns_held_sample_when_cache_is_stale_within_hold_window() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache, hold_last_for=60.0)

    response = responder.handle_frame(bytes.fromhex("010400000004f1c9"))

    assert response == bytes.fromhex("010408063e0000000006e1b80c")


def test_cropster_responder_returns_exception_when_held_sample_expired() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 80.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache, hold_last_for=60.0)

    assert responder.handle_frame(bytes.fromhex("01040000000131ca")) == bytes.fromhex("01840442c3")


def test_cropster_responder_uses_custom_registers_and_et_mapping() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(
        cache,
        bt_register=2,
        exhaust_register=5,
        register_3_source="et",
    )

    response = responder.handle_frame(bytes.fromhex("01040005000121cb"))

    assert response == bytes.fromhex("01040206b3fb25")


def test_cropster_responder_returns_exception_when_cache_is_stale() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache, hold_last_for=0)

    assert responder.handle_frame(bytes.fromhex("01040000000131ca")) == bytes.fromhex("01840442c3")


def test_cropster_responder_returns_exception_for_unsupported_function() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache)

    assert responder.handle_frame(bytes.fromhex("010300000001840a")) == bytes.fromhex("01830180f0")


def test_cropster_responder_returns_exception_for_unsupported_slave() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache)

    assert responder.handle_frame(bytes.fromhex("02040000000131f9")) == bytes.fromhex("028404b2c3")


def test_cropster_serial_server_buffers_partial_modbus_frame() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    serial_port = FakeByteSerial([bytes.fromhex("010400"), bytes.fromhex("000004f1c9")])
    server = CropsterSerialServer(serial_port, CropsterModbusResponder(cache))

    server.run_once()

    assert serial_port.writes == [bytes.fromhex("010408063e0000000006e1b80c")]


def test_reconnecting_serial_server_runner_reopens_output_port_after_failure() -> None:
    from tools.peak_p1_proxy.runtime import ReconnectingSerialServerRunner

    opened = [ClosableFakeSerial(False), ClosableFakeSerial(False)]
    sleeps: list[float] = []
    runs: list[object] = []

    class FailingServer:
        def __init__(self, serial_port) -> None:
            self.serial_port = serial_port

        def run(self, stop_event) -> None:
            runs.append(self.serial_port)
            raise serial.SerialException("output disconnected")

    def opener(settings: SerialSettings):
        return opened.pop(0)

    runner = ReconnectingSerialServerRunner(
        name="cropster",
        serial_settings=SerialSettings("COM12"),
        server_factory=FailingServer,
        open_serial_fn=opener,
        reconnect_delay=0.25,
        sleep_fn=sleeps.append,
    )

    stop_event = threading.Event()
    runner.run_once(stop_event)
    runner.run_once(stop_event)

    assert len(runs) == 2
    assert sleeps == [0.25, 0.25]
