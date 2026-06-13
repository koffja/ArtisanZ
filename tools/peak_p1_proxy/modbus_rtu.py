from __future__ import annotations

from dataclasses import dataclass


class ModbusRtuError(ValueError):
    """Raised when a Modbus RTU frame is malformed."""


@dataclass(frozen=True)
class ModbusRequest:
    slave_id: int
    function: int
    start_register: int
    count: int


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def append_crc(body: bytes) -> bytes:
    return body + crc16(body).to_bytes(2, "little")


def parse_request(frame: bytes) -> ModbusRequest:
    if len(frame) != 8:
        raise ModbusRtuError(f"expected 8-byte Modbus request, got {len(frame)} bytes")

    body = frame[:-2]
    expected = crc16(body)
    actual = int.from_bytes(frame[-2:], "little")
    if actual != expected:
        raise ModbusRtuError(f"CRC mismatch: expected 0x{expected:04x}, got 0x{actual:04x}")

    return ModbusRequest(
        slave_id=body[0],
        function=body[1],
        start_register=int.from_bytes(body[2:4], "big"),
        count=int.from_bytes(body[4:6], "big"),
    )


def _scale_register(value: float) -> int:
    return int(round(value * 10)) & 0xFFFF


def build_read_input_registers_response(
    request: ModbusRequest,
    registers: dict[int, float],
) -> bytes:
    if request.count < 1 or request.count > 125:
        return build_exception_response(request.slave_id, request.function, 3)

    payload = bytearray()
    for offset in range(request.count):
        register = request.start_register + offset
        payload.extend(_scale_register(registers.get(register, 0.0)).to_bytes(2, "big"))

    body = bytes([request.slave_id, request.function, len(payload)]) + bytes(payload)
    return append_crc(body)


def build_exception_response(slave_id: int, function: int, exception_code: int) -> bytes:
    return append_crc(bytes([slave_id, function | 0x80, exception_code]))
