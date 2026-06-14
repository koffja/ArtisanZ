import pytest

from tools.peak_p1_proxy.modbus_rtu import (
    ModbusRequest,
    ModbusRtuError,
    build_exception_response,
    build_read_input_registers_request,
    build_read_input_registers_response,
    crc16,
    parse_read_input_registers_response,
    parse_request,
)


def test_crc16_known_cropster_read_frame() -> None:
    body = bytes.fromhex("010400000001")

    assert crc16(body) == 0xCA31
    assert body + crc16(body).to_bytes(2, "little") == bytes.fromhex("01040000000131ca")


def test_parse_function_4_request() -> None:
    request = parse_request(bytes.fromhex("010400030001c1ca"))

    assert request == ModbusRequest(slave_id=1, function=4, start_register=3, count=1)


def test_build_read_input_registers_request() -> None:
    assert build_read_input_registers_request(1, 0, 4) == bytes.fromhex("010400000004f1c9")


def test_parse_read_input_registers_response() -> None:
    registers = parse_read_input_registers_response(bytes.fromhex("010408063c0692064c06b022d4"))

    assert registers == [1596, 1682, 1612, 1712]


def test_parse_rejects_bad_crc() -> None:
    with pytest.raises(ModbusRtuError, match="CRC"):
        parse_request(bytes.fromhex("0104000300010000"))


def test_build_single_register_response_scales_by_10() -> None:
    response = build_read_input_registers_response(
        ModbusRequest(slave_id=1, function=4, start_register=0, count=1),
        {0: 159.8},
    )

    assert response == bytes.fromhex("010402063e3b40")


def test_build_register_block_response_fills_undefined_with_zero() -> None:
    response = build_read_input_registers_response(
        ModbusRequest(slave_id=1, function=4, start_register=0, count=4),
        {0: 159.8, 3: 176.1},
    )

    assert response == bytes.fromhex("010408063e0000000006e1b80c")


def test_build_exception_response() -> None:
    assert build_exception_response(1, 4, 4) == bytes.fromhex("01840442c3")
