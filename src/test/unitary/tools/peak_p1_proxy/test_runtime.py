from tools.peak_p1_proxy.cache import TemperatureCache
from tools.peak_p1_proxy.modbus_rtu import parse_request
from tools.peak_p1_proxy.model import TemperatureSample
from tools.peak_p1_proxy.runtime import (
    ArtisanTc4Responder,
    CropsterModbusResponder,
    CropsterSerialServer,
    P1ModbusPoller,
    P1Poller,
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

    def read(self, size: int = 1) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        data = chunk[:size]
        rest = chunk[size:]
        if rest:
            self.chunks.insert(0, rest)
        return data


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
    responder = CropsterModbusResponder(cache)

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
