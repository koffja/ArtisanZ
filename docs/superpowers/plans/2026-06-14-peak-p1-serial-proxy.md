# Peak P1 Serial Proxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform command-line smart serial proxy that lets Artisan and Cropster read one HB Peak P1 at the same time without sharing the physical USB serial port.

**Architecture:** Implement a standalone Python tool under `tools/peak_p1_proxy/`. The tool owns the real Peak P1 serial port, polls TC4-style temperature data into a thread-safe cache, serves Artisan through a TC4-compatible virtual serial endpoint, and serves Cropster through a Modbus RTU slave endpoint.

**Tech Stack:** Python 3.12+, `pyserial`, `pytest`, standard-library `argparse`, `threading`, `logging`, and `dataclasses`.

---

## File Structure

- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/__init__.py`
  - Package marker and version string.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/model.py`
  - Temperature sample and serial configuration dataclasses.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/p1_protocol.py`
  - Peak P1 TC4 response parsing and Artisan TC4 response formatting.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/modbus_rtu.py`
  - Modbus RTU CRC, request parsing, register mapping, normal responses, and exception responses.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/cache.py`
  - Thread-safe latest-temperature cache with stale detection.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/runtime.py`
  - P1 poller, Artisan serial server, Cropster Modbus serial server, and orchestrator.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/cli.py`
  - CLI argument parsing, port listing, dry-run, logging setup, and runtime start.
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/p1_serial_proxy.py`
  - Thin executable wrapper for `python tools/p1_serial_proxy.py`.
- Create: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_p1_protocol.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_modbus_rtu.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_cache.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_runtime.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_cli.py`

## Scope Check

The design covers one standalone utility with protocol parsing, cache behavior,
serial serving, CLI behavior, and simulated tests. It does not require Artisan UI
changes, Cropster configuration changes, kernel drivers, or real hardware access
before implementation verification.

### Task 1: Protocol Foundation

**Files:**
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/__init__.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/model.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/p1_protocol.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_p1_protocol.py`

- [ ] **Step 1: Confirm branch and worktree**

Run:

```bash
git branch --show-current
git status --short
git remote -v
```

Expected branch: `ArtisanZ`. Existing unrelated untracked files may remain. Do
not edit or stage `tools/probe_peak_p1.py`.

- [ ] **Step 2: Write failing TC4 protocol tests**

Create `src/test/unitary/tools/peak_p1_proxy/test_p1_protocol.py` with tests for:

```python
from tools.peak_p1_proxy.p1_protocol import (
    format_artisan_read_response,
    parse_p1_group_response,
)


def test_parse_3400_response_maps_bt_and_et():
    values = parse_p1_group_response("3400", "171.51,159.82,171.51,C")

    assert values.at == 171.51
    assert values.bt == 159.82
    assert values.et == 171.51
    assert values.exhaust is None
    assert values.inlet is None


def test_parse_1200_response_maps_exhaust_and_inlet():
    values = parse_p1_group_response("1200", "171.51,176.10,166.09,C")

    assert values.at == 171.51
    assert values.exhaust == 176.10
    assert values.inlet == 166.09
    assert values.bt is None
    assert values.et is None


def test_format_artisan_read_response_uses_tc4_csv_shape():
    line = format_artisan_read_response(at=171.51, first=159.82, second=171.51)

    assert line == "171.51,159.82,171.51,C\\r\\n"
```

- [ ] **Step 3: Run protocol tests and verify failure**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_p1_protocol.py -q
```

Expected: fails because `tools.peak_p1_proxy.p1_protocol` does not exist.

- [ ] **Step 4: Implement protocol models and parser**

Create:

```python
# tools/peak_p1_proxy/model.py
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
```

Create:

```python
# tools/peak_p1_proxy/p1_protocol.py
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
    return f"{at:.2f},{first:.2f},{second:.2f},C\\r\\n"
```

Create:

```python
# tools/peak_p1_proxy/__init__.py
"""Smart serial proxy for HB Peak P1."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Run protocol tests and verify pass**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_p1_protocol.py -q
```

Expected: all tests pass.

### Task 2: Modbus RTU Foundation

**Files:**
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/modbus_rtu.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_modbus_rtu.py`

- [ ] **Step 1: Write failing Modbus RTU tests**

Create `test_modbus_rtu.py` with:

```python
from tools.peak_p1_proxy.modbus_rtu import (
    ModbusRequest,
    build_exception_response,
    build_read_input_registers_response,
    crc16,
    parse_request,
)


def test_crc16_known_cropster_read_frame():
    body = bytes.fromhex("010400000001")

    assert crc16(body) == 0xCA31
    assert body + crc16(body).to_bytes(2, "little") == bytes.fromhex("01040000000131ca")


def test_parse_function_4_request():
    request = parse_request(bytes.fromhex("010400030001c1ca"))

    assert request == ModbusRequest(slave_id=1, function=4, start_register=3, count=1)


def test_build_single_register_response_scales_by_10():
    response = build_read_input_registers_response(
        ModbusRequest(slave_id=1, function=4, start_register=0, count=1),
        {0: 159.8},
    )

    assert response == bytes.fromhex("010402063e3b40")


def test_build_register_block_response_fills_undefined_with_zero():
    response = build_read_input_registers_response(
        ModbusRequest(slave_id=1, function=4, start_register=0, count=4),
        {0: 159.8, 3: 176.1},
    )

    assert response == bytes.fromhex("010408063e0000000006e1b80c")


def test_build_exception_response():
    assert build_exception_response(1, 4, 4) == bytes.fromhex("01840442c3")
```

- [ ] **Step 2: Run Modbus tests and verify failure**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_modbus_rtu.py -q
```

Expected: fails because `modbus_rtu.py` does not exist.

- [ ] **Step 3: Implement Modbus RTU helpers**

Create `tools/peak_p1_proxy/modbus_rtu.py` with dataclass `ModbusRequest`,
`crc16`, `parse_request`, `build_read_input_registers_response`, and
`build_exception_response`. The CRC uses initial value `0xFFFF`, polynomial
`0xA001`, and appends little-endian CRC bytes. `parse_request` accepts exactly
8-byte function 4 request frames and validates CRC before returning
`ModbusRequest`.

- [ ] **Step 4: Run Modbus tests and verify pass**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_modbus_rtu.py -q
```

Expected: all tests pass.

### Task 3: Temperature Cache

**Files:**
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/cache.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_cache.py`

- [ ] **Step 1: Write failing cache tests**

Create `test_cache.py` with:

```python
from tools.peak_p1_proxy.cache import TemperatureCache
from tools.peak_p1_proxy.model import TemperatureSample


def sample(timestamp: float = 10.0) -> TemperatureSample:
    return TemperatureSample(bt=159.8, et=171.5, exhaust=176.1, inlet=166.1, at=171.5, timestamp=timestamp)


def test_cache_starts_empty_and_stale():
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 100.0)

    assert cache.get() is None
    assert cache.is_stale()


def test_cache_returns_latest_sample_before_stale_timeout():
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 12.0)
    cache.update(sample(timestamp=10.0))

    assert cache.get() == sample(timestamp=10.0)
    assert not cache.is_stale()


def test_cache_marks_sample_stale_after_timeout():
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 16.0)
    cache.update(sample(timestamp=10.0))

    assert cache.is_stale()
```

- [ ] **Step 2: Run cache tests and verify failure**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_cache.py -q
```

Expected: fails because `cache.py` does not exist.

- [ ] **Step 3: Implement thread-safe cache**

Create `tools/peak_p1_proxy/cache.py` with `TemperatureCache` using
`threading.RLock`. Constructor accepts `stale_after: float` and optional
`clock: Callable[[], float]`. `update()` stores a `TemperatureSample`; `get()`
returns the latest sample or `None`; `is_stale()` returns `True` when no sample
exists or `clock() - sample.timestamp > stale_after`.

- [ ] **Step 4: Run cache tests and verify pass**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_cache.py -q
```

Expected: all tests pass.

### Task 4: Runtime Poller and Virtual Serial Servers

**Files:**
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/runtime.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_runtime.py`

- [ ] **Step 1: Write failing runtime tests**

Create tests using a small fake serial object. Cover:

```python
from tools.peak_p1_proxy.cache import TemperatureCache
from tools.peak_p1_proxy.modbus_rtu import parse_request
from tools.peak_p1_proxy.runtime import ArtisanTc4Responder, CropsterModbusResponder, P1Poller


class FakeSerial:
    def __init__(self, lines: list[bytes]):
        self.lines = list(lines)
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def flush(self) -> None:
        return None

    def readline(self) -> bytes:
        return self.lines.pop(0)


def test_poller_reads_both_groups_and_updates_cache():
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

    sample = poller.poll_once()

    assert serial_port.writes == [b"CHAN;3400\n", b"READ\n", b"CHAN;1200\n", b"READ\n"]
    assert sample.bt == 159.82
    assert sample.et == 171.51
    assert sample.exhaust == 176.10
    assert sample.inlet == 166.09
    assert cache.get() == sample

def test_artisan_server_returns_3400_cache_as_tc4_line():
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = ArtisanTc4Responder(cache)

    assert responder.handle_line("CHAN;3400") == b"#\r\n"
    assert responder.handle_line("READ") == b"171.50,159.80,171.50,C\r\n"

def test_cropster_server_returns_modbus_registers_from_cache():
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 11.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache)
    request = bytes.fromhex("010400000004f1c9")

    response = responder.handle_frame(request)

    parsed_request = parse_request(request)
    assert parsed_request.start_register == 0
    assert response == bytes.fromhex("010408063e0000000006e1b80c")
```

The fake P1 serial must return `#` after `CHAN;3400`, then
`171.51,159.82,171.51,C`, then `#` after `CHAN;1200`, then
`171.51,176.10,166.09,C`.

- [ ] **Step 2: Run runtime tests and verify failure**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_runtime.py -q
```

Expected: fails because `runtime.py` does not exist.

- [ ] **Step 3: Implement runtime classes**

Implement:

- `P1Poller.poll_once()` that writes `CHAN;3400\n`, reads optional ACK, writes
  `READ\n`, parses the response, repeats for `CHAN;1200`, then updates cache
  with one complete `TemperatureSample`.
- `ArtisanTc4Responder.handle_line(command: str) -> bytes` for deterministic
  line-level tests. It returns `b"#\r\n"` for supported `CHAN` commands and
  TC4 CSV bytes for `READ`.
- `CropsterModbusResponder.handle_frame(frame: bytes) -> bytes` for
  deterministic frame-level tests. It returns function 4 register responses
  from cache, or exception code 4 when the cache is stale.
- Threaded serial-loop wrappers around the responders for real runtime use.

- [ ] **Step 4: Run runtime tests and verify pass**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_runtime.py -q
```

Expected: all tests pass.

### Task 5: CLI

**Files:**
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/peak_p1_proxy/cli.py`
- Create: `/Users/chengzhe/Projects/ArtisanZ/tools/p1_serial_proxy.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/tools/peak_p1_proxy/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create tests for:

```python
from tools.peak_p1_proxy.cli import build_parser, main


def test_parser_accepts_required_ports():
    parser = build_parser()

    args = parser.parse_args(
        [
            "--real-port",
            "COM5",
            "--artisan-port",
            "COM10",
            "--cropster-port",
            "COM12",
        ]
    )

    assert args.real_port == "COM5"
    assert args.artisan_port == "COM10"
    assert args.cropster_port == "COM12"

def test_list_ports_returns_zero_without_required_ports(monkeypatch, capsys):
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 Peak P1"])

    exit_code = main(["--list-ports"])

    assert exit_code == 0
    assert "COM5 Peak P1" in capsys.readouterr().out

def test_dry_run_calls_port_checker(monkeypatch):
    checked: list[str] = []
    monkeypatch.setattr(
        "tools.peak_p1_proxy.cli.check_serial_port",
        lambda port, baudrate, timeout: checked.append(port),
    )

    exit_code = main(
        [
            "--real-port",
            "COM5",
            "--artisan-port",
            "COM10",
            "--cropster-port",
            "COM12",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert checked == ["COM5", "COM10", "COM12"]
```

- [ ] **Step 2: Run CLI tests and verify failure**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_cli.py -q
```

Expected: fails because `cli.py` does not exist.

- [ ] **Step 3: Implement CLI**

Implement argparse options:

```text
--real-port
--artisan-port
--cropster-port
--real-baud
--poll-interval
--stale-after
--cropster-register-bt
--cropster-register-exhaust
--cropster-register-3-source
--list-ports
--dry-run
--verbose
--log-frames
```

`--list-ports` prints ports from `serial.tools.list_ports.comports()` and exits
0. `--dry-run` opens and closes the configured ports with the selected settings,
prints `dry run ok`, and exits 0. Normal mode constructs the cache, poller, and
two serial servers, then runs until `KeyboardInterrupt`.

- [ ] **Step 4: Run CLI tests and verify pass**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy/test_cli.py -q
```

Expected: all tests pass.

### Task 6: Verification and Review

**Files:**
- Review all created proxy files.
- Review all created tests.

- [ ] **Step 1: Run focused test suite**

Run:

```bash
python3 -m pytest src/test/unitary/tools/peak_p1_proxy -q
```

Expected: all proxy tests pass.

- [ ] **Step 2: Run syntax check**

Run:

```bash
python3 -m py_compile \
  tools/peak_p1_proxy/__init__.py \
  tools/peak_p1_proxy/model.py \
  tools/peak_p1_proxy/p1_protocol.py \
  tools/peak_p1_proxy/modbus_rtu.py \
  tools/peak_p1_proxy/cache.py \
  tools/peak_p1_proxy/runtime.py \
  tools/peak_p1_proxy/cli.py \
  tools/p1_serial_proxy.py
```

Expected: no output and exit code 0.

- [ ] **Step 3: Run CLI smoke checks**

Run:

```bash
python3 tools/p1_serial_proxy.py --help
python3 tools/p1_serial_proxy.py --list-ports
```

Expected: help text prints usage and list-ports exits 0.

- [ ] **Step 4: Inspect staged scope before any commit**

Run:

```bash
git status --short
git diff -- tools/peak_p1_proxy tools/p1_serial_proxy.py src/test/unitary/tools/peak_p1_proxy docs/superpowers/plans/2026-06-14-peak-p1-serial-proxy.md
```

Expected: only the proxy implementation, proxy tests, and this plan changed.
Do not stage unrelated pre-existing untracked files such as
`tools/probe_peak_p1.py`.

- [ ] **Step 5: Code-review checklist**

Verify manually:

- The physical Peak P1 serial port is only touched by `P1Poller`.
- Artisan and Cropster responders only read from `TemperatureCache`.
- Modbus CRC is validated before any response is generated.
- Unsupported Cropster function codes return Modbus exceptions.
- Stale cache behavior is deterministic and tested.
- Cropster register 3 can be mapped to Exhaust by default and changed to ET.
- No heater, fan, airflow, pressure, or control-write behavior exists.
