from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PartialP1Read:
    at: float
    bt: float | None = None
    et: float | None = None
    exhaust: float | None = None
    inlet: float | None = None


@dataclass(frozen=True)
class TemperatureSample:
    bt: float
    et: float
    exhaust: float
    inlet: float
    at: float
    timestamp: float


@dataclass(frozen=True)
class SerialSettings:
    port: str
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: float = 0.4
