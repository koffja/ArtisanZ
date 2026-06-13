from __future__ import annotations

from .model import PartialP1Read


class P1ProtocolError(ValueError):
    """Raised when a Peak P1 TC4-style response cannot be parsed."""


def _parse_csv_response(line: str) -> list[str]:
    parts = [part.strip() for part in line.strip().split(",")]
    if len(parts) < 4 or parts[-1].upper() not in {"C", "F"}:
        raise P1ProtocolError(f"invalid P1 response: {line!r}")
    return parts


def parse_p1_group_response(group: str, line: str) -> PartialP1Read:
    parts = _parse_csv_response(line)
    try:
        at = float(parts[0])
        first = float(parts[1])
        second = float(parts[2])
    except ValueError as exc:
        raise P1ProtocolError(f"non-numeric P1 response: {line!r}") from exc

    if group == "3400":
        return PartialP1Read(at=at, bt=first, et=second)
    if group == "1200":
        return PartialP1Read(at=at, exhaust=first, inlet=second)
    raise P1ProtocolError(f"unsupported P1 channel group: {group!r}")


def format_artisan_read_response(at: float, first: float, second: float) -> str:
    return f"{at:.2f},{first:.2f},{second:.2f},C\r\n"
