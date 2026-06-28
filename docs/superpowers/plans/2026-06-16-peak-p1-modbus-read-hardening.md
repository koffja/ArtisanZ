# Peak P1 Modbus Read Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make Peak P1 Modbus polling reject short register responses with clear diagnostics and clear stale input bytes before each request.

**Architecture:** Keep the existing `P1ModbusPoller` and reconnect runner. Add a small register-count guard in the poller and a best-effort serial input buffer reset before request writes.

**Tech Stack:** Python 3.14, pyserial-compatible serial objects, pytest.

---

## File Structure

- Modify `tools/peak_p1_proxy/runtime.py`
  - Add helper methods on `P1ModbusPoller` for required register count, input buffer reset, and response length validation.
- Modify `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`
  - Add fake serial support for `reset_input_buffer()`.
  - Add regression tests for short register responses and buffer clearing.

## Task 1: Add Failing Tests

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`

- [x] **Step 1: Add a fake resettable serial**

Update `FakeByteSerial` so tests can observe buffer resets:

```python
class FakeByteSerial(FakeSerial):
    def __init__(self, chunks: list[bytes]) -> None:
        super().__init__([])
        self.chunks = list(chunks)
        self.reset_input_buffer_calls = 0

    def reset_input_buffer(self) -> None:
        self.reset_input_buffer_calls += 1
```

- [x] **Step 2: Add short register response regression test**

```python
def test_modbus_poller_rejects_short_register_response_before_indexing() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    serial_port = FakeByteSerial([bytes.fromhex("01040204abfa4f")])
    poller = P1ModbusPoller(serial_port=serial_port, cache=cache, clock=lambda: 10.0)

    with pytest.raises(RuntimeError, match="short Modbus register response: expected at least 4 registers, got 1"):
        poller.poll_once()

    assert cache.get() is None
```

- [x] **Step 3: Add input-buffer reset test**

```python
def test_modbus_poller_clears_input_buffer_before_request_when_supported() -> None:
    cache = TemperatureCache(stale_after=5.0, clock=lambda: 20.0)
    serial_port = FakeByteSerial([bytes.fromhex("010408063c0692064c06b022d4")])
    poller = P1ModbusPoller(serial_port=serial_port, cache=cache, clock=lambda: 10.0)

    poller.poll_once()

    assert serial_port.reset_input_buffer_calls == 1
```

- [x] **Step 4: Verify tests fail**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_modbus_poller_rejects_short_register_response_before_indexing \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_modbus_poller_clears_input_buffer_before_request_when_supported \
  -q
```

Expected: tests fail because the poller still raises `list index out of range` and does not reset the input buffer.

## Task 2: Implement Poller Hardening

**Files:**
- Modify: `tools/peak_p1_proxy/runtime.py`

- [x] **Step 1: Add helper methods to `P1ModbusPoller`**

Add:

```python
def _required_register_count(self) -> int:
    return max(
        self._bt_register,
        self._et_register,
        self._exhaust_register,
        self._inlet_register,
    ) + 1

def _reset_input_buffer(self) -> None:
    reset = getattr(self._serial, "reset_input_buffer", None)
    if reset is not None:
        reset()

def _validate_register_count(self, registers: list[int]) -> None:
    expected = self._required_register_count()
    actual = len(registers)
    if actual < expected:
        raise RuntimeError(
            f"short Modbus register response: expected at least {expected} registers, got {actual}"
        )
```

- [x] **Step 2: Use helpers in `_read_registers()` and `poll_once()`**

`_read_registers()` should call `_reset_input_buffer()` before writing the request and use `_required_register_count()` for `count`.

`poll_once()` should call `_validate_register_count(registers)` before indexing register values.

- [x] **Step 3: Verify focused tests pass**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_modbus_poller_rejects_short_register_response_before_indexing \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_modbus_poller_clears_input_buffer_before_request_when_supported \
  -q
```

Expected: both tests pass.

## Task 3: Verify Proxy Suite

**Files:**
- Modify: `tools/peak_p1_proxy/runtime.py`
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`

- [x] **Step 1: Run focused proxy tests**

Run:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy -q
```

Expected: all proxy tests pass.

- [x] **Step 2: Run syntax checks**

Run:

```bash
src/.venv/bin/python -m py_compile tools/p1_serial_proxy.py tools/peak_p1_proxy/cli.py tools/peak_p1_proxy/runtime.py tools/peak_p1_proxy/modbus_rtu.py tools/peak_p1_proxy/model.py tools/peak_p1_proxy/cache.py
```

Expected: exit code 0.
