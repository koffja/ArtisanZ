# Peak P1 End-To-End Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Keep Cropster and Artisan virtual output ports recoverable and keep Cropster receiving usable data during short Peak P1 source interruptions.

**Architecture:** Add an output-side reconnecting serial server runner that mirrors the existing real P1 runner. Add a bounded Cropster hold-last policy that serves the last valid cache sample during short source outages.

**Tech Stack:** Python 3.14, pyserial-compatible serial objects, pytest.

---

## File Structure

- Modify `tools/peak_p1_proxy/cache.py`
  - Add sample age helpers for hold-last decisions.
- Modify `tools/peak_p1_proxy/runtime.py`
  - Add `ReconnectingSerialServerRunner`.
  - Add Cropster hold-last logic.
  - Move Artisan/Cropster output ports into reconnecting runners.
- Modify `tools/peak_p1_proxy/cli.py`
  - Add `--cropster-hold-last-for`.
  - Add `--virtual-reconnect-delay`.
- Modify `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`
  - Add output runner and Cropster hold-last tests.
- Modify `src/test/unitary/tools/peak_p1_proxy/test_cli.py`
  - Add option passing assertions.

## Task 1: Cropster Hold-Last Tests

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`

- [x] **Step 1: Add hold-last success test**

```python
def test_cropster_responder_returns_held_sample_when_cache_is_stale_within_hold_window() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache, hold_last_for=60.0)

    response = responder.handle_frame(bytes.fromhex("010400000004f1c9"))

    assert response == bytes.fromhex("010408063e0000000006e1b80c")
```

- [x] **Step 2: Add hold-last expiration test**

```python
def test_cropster_responder_returns_exception_when_held_sample_expired() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 80.0)
    cache.update(sample(timestamp=10.0))
    responder = CropsterModbusResponder(cache, hold_last_for=60.0)

    assert responder.handle_frame(bytes.fromhex("01040000000131ca")) == bytes.fromhex("01840442c3")
```

- [x] **Step 3: Verify tests fail**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_cropster_responder_returns_held_sample_when_cache_is_stale_within_hold_window \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_cropster_responder_returns_exception_when_held_sample_expired \
  -q
```

Expected: fail because `hold_last_for` is not supported.

## Task 2: Output Runner Tests

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`

- [x] **Step 1: Add output reconnect runner test**

```python
def test_reconnecting_serial_server_runner_reopens_output_port_after_failure() -> None:
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
```

- [x] **Step 2: Verify test fails**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_reconnecting_serial_server_runner_reopens_output_port_after_failure \
  -q
```

Expected: fail because `ReconnectingSerialServerRunner` does not exist.

## Task 3: Implement Recovery

**Files:**
- Modify: `tools/peak_p1_proxy/cache.py`
- Modify: `tools/peak_p1_proxy/runtime.py`
- Modify: `tools/peak_p1_proxy/cli.py`

- [x] **Step 1: Add cache age helper**

Add `sample_age()` to `TemperatureCache`:

```python
def sample_age(self) -> float | None:
    with self._lock:
        if self._sample is None:
            return None
        return self._clock() - self._sample.timestamp
```

- [x] **Step 2: Add Cropster hold-last behavior**

Add `hold_last_for: float = 60.0` to `CropsterModbusResponder.__init__`. When cache is stale, return held sample if `hold_last_for > 0`, a sample exists, and `cache.sample_age() <= hold_last_for`; otherwise return the existing Modbus exception.

- [x] **Step 3: Add output reconnect runner**

Create `ReconnectingSerialServerRunner` with `run_once(stop_event)` and `run(stop_event)` methods. It opens the configured serial port, constructs the server, runs it, catches exceptions, closes the port, waits, and retries.

- [x] **Step 4: Wire ProxyRuntime**

Add constructor fields for `cropster_hold_last_for` and `virtual_reconnect_delay`. Replace one-shot Artisan/Cropster port opening with reconnecting output runners.

- [x] **Step 5: Add CLI args**

Add:

```python
parser.add_argument("--cropster-hold-last-for", type=float, default=60.0)
parser.add_argument("--virtual-reconnect-delay", type=float, default=2.0)
```

Pass both into `ProxyRuntime`.

## Task 4: CLI and Full Verification

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_cli.py`

- [x] **Step 1: Extend CLI option passing test**

Add the two new arguments to `test_main_passes_cropster_mapping_options_to_runtime` and assert:

```python
assert captured["cropster_hold_last_for"] == 30.0
assert captured["virtual_reconnect_delay"] == 0.5
```

- [x] **Step 2: Run focused tests**

Run:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy -q
```

Expected: all tests pass.

- [x] **Step 3: Run syntax checks**

Run:

```bash
src/.venv/bin/python -m py_compile tools/p1_serial_proxy.py tools/peak_p1_proxy/cli.py tools/peak_p1_proxy/runtime.py tools/peak_p1_proxy/modbus_rtu.py tools/peak_p1_proxy/model.py tools/peak_p1_proxy/cache.py
```

Expected: exit code 0.
