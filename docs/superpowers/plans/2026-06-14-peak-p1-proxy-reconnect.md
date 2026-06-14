# Peak P1 Proxy Reconnect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the Peak P1 serial proxy survive transient real-port failures and report macOS FTDI open failures without tracebacks.

**Architecture:** Keep Artisan and Cropster virtual ports open for the process lifetime. Move real Peak P1 serial ownership into a reconnecting poller runner that can close, wait, reopen, and resume cache updates. Centralize serial-open error formatting in the CLI so dry-run and runtime startup failures share friendly diagnostics.

**Tech Stack:** Python 3.14, pyserial, pytest, existing `tools/peak_p1_proxy` modules.

---

## File Structure

- Modify `tools/peak_p1_proxy/cli.py`
  - Add CLI options for reconnect behavior.
  - Catch platform serial setup errors such as `termios.error`.
  - Print visible ports and a macOS FTDI recovery hint.
- Modify `tools/peak_p1_proxy/runtime.py`
  - Add a reconnecting real-port runner.
  - Let virtual Artisan/Cropster ports stay open while real P1 reconnects.
  - Preserve the existing `P1Poller`, `P1ModbusPoller`, `ArtisanSerialServer`, and `CropsterSerialServer` responder behavior.
- Modify `src/test/unitary/tools/peak_p1_proxy/test_cli.py`
  - Cover friendly dry-run and runtime startup failures.
  - Cover parsing and passing reconnect options into `ProxyRuntime`.
- Modify `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`
  - Cover real-port reopen after repeated poll failures.
  - Cover fail-fast behavior when auto reconnect is disabled.

## Task 1: Friendly Serial Error Reporting

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_cli.py`
- Modify: `tools/peak_p1_proxy/cli.py`

- [x] **Step 1: Write failing CLI tests**

Add tests to `src/test/unitary/tools/peak_p1_proxy/test_cli.py`:

def test_dry_run_reports_termios_errors_without_traceback(monkeypatch, capsys) -> None:
    def fail_open(port: str, baudrate: int, timeout: float) -> None:
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr("tools.peak_p1_proxy.cli.check_serial_port", fail_open)
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 FT232R"])

    exit_code = main(
        [
            "--real-port",
            "/dev/cu.usbserial-AV0LY3SU",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "dry run failed" in output
    assert "Invalid argument" in output
    assert "visible ports:" in output
    assert "COM5 FT232R" in output
    assert "USB serial driver" in output


def test_runtime_reports_serial_startup_errors_without_traceback(monkeypatch, capsys) -> None:
    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            return None

        def run(self) -> None:
            raise OSError(22, "Invalid argument")

        def stop(self) -> None:
            return None

    monkeypatch.setattr(cli, "ProxyRuntime", FakeRuntime)
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 FT232R"])

    exit_code = main(
        [
            "--real-port",
            "/dev/cu.usbserial-AV0LY3SU",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--no-auto-reconnect",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "proxy startup failed" in output
    assert "Invalid argument" in output
    assert "COM5 FT232R" in output
```

- [x] **Step 2: Run tests to verify RED**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_cli.py::test_dry_run_reports_termios_errors_without_traceback \
  src/test/unitary/tools/peak_p1_proxy/test_cli.py::test_runtime_reports_serial_startup_errors_without_traceback \
  -q
```

Expected: both tests fail because `termios.error` is not caught.

- [x] **Step 3: Implement CLI error helpers**

In `tools/peak_p1_proxy/cli.py`, add:

```python
try:
    import termios
except ImportError:
    TERMIOS_ERROR_TYPES = ()
else:
    TERMIOS_ERROR_TYPES = (termios.error,)

SERIAL_OPEN_ERRORS = (serial.SerialException, OSError, *TERMIOS_ERROR_TYPES)


def print_serial_error(prefix: str, exc: BaseException) -> None:
    print(f"{prefix}: {exc}")
    print("visible ports:")
    for description in iter_port_descriptions():
        print(description)
    if getattr(exc, "errno", None) == 22 or "Invalid argument" in str(exc):
        print(
            "hint: macOS reported a USB serial driver configuration error. "
            "Close Artisan/Cropster/proxy processes, unplug the Peak P1 USB cable, "
            "wait a few seconds, then plug it back in."
        )
```

Change dry-run and runtime exception handling to use `SERIAL_OPEN_ERRORS` and `print_serial_error()`.

- [x] **Step 4: Run tests to verify GREEN**

Run:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy/test_cli.py -q
```

Expected: all CLI tests pass.

## Task 2: Reconnecting Real P1 Runner

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`
- Modify: `tools/peak_p1_proxy/runtime.py`

- [x] **Step 1: Write failing reconnect test**

Add a test to `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`:

```python
import pytest

from tools.peak_p1_proxy.model import SerialSettings
from tools.peak_p1_proxy.runtime import ReconnectingP1Runner


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


class ClosableFakeSerial:
    def __init__(self, should_fail: bool) -> None:
        self.should_fail = should_fail
        self.closed = False

    def close(self) -> None:
        self.closed = True


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
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_reconnecting_runner_reopens_real_port_after_repeated_poll_failures \
  -q
```

Expected: fails because `ReconnectingP1Runner` does not exist.

- [x] **Step 3: Implement reconnecting runner**

Add `ReconnectingP1Runner` to `tools/peak_p1_proxy/runtime.py`:

```python
class ReconnectingP1Runner:
    def __init__(
        self,
        real_settings: SerialSettings,
        cache: TemperatureCache,
        poller_factory,
        open_serial_fn=open_serial,
        poll_interval: float = 1.0,
        reconnect_after_failures: int = 3,
        reconnect_delay: float = 2.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        frame_logger: FrameLogger | None = None,
        poller_kwargs: dict[str, object] | None = None,
    ) -> None:
        self._real_settings = real_settings
        self._cache = cache
        self._poller_factory = poller_factory
        self._open_serial_fn = open_serial_fn
        self._poll_interval = poll_interval
        self._reconnect_after_failures = max(1, reconnect_after_failures)
        self._reconnect_delay = reconnect_delay
        self._sleep = sleep_fn
        self._frame_logger = frame_logger or FrameLogger(None)
        self._poller_kwargs = poller_kwargs or {}
        self._serial_port = None
        self._poller = None
        self._failures = 0

    def close(self) -> None:
        if self._serial_port is not None:
            close = getattr(self._serial_port, "close", None)
            if close is not None:
                close()
        self._serial_port = None
        self._poller = None

    def _ensure_open(self) -> None:
        if self._serial_port is not None and self._poller is not None:
            return
        self._serial_port = self._open_serial_fn(self._real_settings)
        self._poller = self._poller_factory(
            self._serial_port,
            self._cache,
            frame_logger=self._frame_logger,
            **self._poller_kwargs,
        )

    def run_once(self) -> TemperatureSample | None:
        self._ensure_open()
        try:
            sample = self._poller.poll_once()
        except Exception:
            self._failures += 1
            if self._failures >= self._reconnect_after_failures:
                self.close()
                self._sleep(self._reconnect_delay)
                self._failures = 0
            raise
        self._failures = 0
        return sample

    def run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            try:
                sample = self.run_once()
                if sample is not None:
                    _log.info(
                        "P1 BT %.2f ET %.2f Exhaust %.2f Inlet %.2f",
                        sample.bt,
                        sample.et,
                        sample.exhaust,
                        sample.inlet,
                    )
            except Exception as exc:
                _log.warning("Peak P1 reconnecting poll failed: %s", exc)
            stop_event.wait(self._poll_interval)
```

- [x] **Step 4: Run reconnect test to verify GREEN**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py::test_reconnecting_runner_reopens_real_port_after_repeated_poll_failures \
  -q
```

Expected: test passes.

## Task 3: Wire Runtime Options

**Files:**
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_cli.py`
- Modify: `tools/peak_p1_proxy/cli.py`
- Modify: `tools/peak_p1_proxy/runtime.py`

- [x] **Step 1: Write failing option-passing test**

Extend `test_main_passes_cropster_mapping_options_to_runtime` in `src/test/unitary/tools/peak_p1_proxy/test_cli.py` with:

```python
"--no-auto-reconnect",
"--reconnect-after-failures",
"5",
"--reconnect-delay",
"0.75",
```

Add assertions:

```python
assert captured["auto_reconnect"] is False
assert captured["reconnect_after_failures"] == 5
assert captured["reconnect_delay"] == 0.75
```

- [x] **Step 2: Run test to verify RED**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_cli.py::test_main_passes_cropster_mapping_options_to_runtime \
  -q
```

Expected: fails because the parser does not know the reconnect options.

- [x] **Step 3: Add CLI options and runtime fields**

In `tools/peak_p1_proxy/cli.py`, add parser arguments:

```python
parser.add_argument("--no-auto-reconnect", dest="auto_reconnect", action="store_false")
parser.set_defaults(auto_reconnect=True)
parser.add_argument("--reconnect-after-failures", type=int, default=3)
parser.add_argument("--reconnect-delay", type=float, default=2.0)
```

Pass the new args to `ProxyRuntime`.

In `tools/peak_p1_proxy/runtime.py`, add constructor parameters and store them:

```python
auto_reconnect: bool = True,
reconnect_after_failures: int = 3,
reconnect_delay: float = 2.0,
```

When `auto_reconnect` is true, create `ReconnectingP1Runner` for the poller thread. When false, preserve current behavior by opening the real port once and running `P1Poller` or `P1ModbusPoller` directly.

- [x] **Step 4: Run option and runtime tests**

Run:

```bash
src/.venv/bin/python -m pytest \
  src/test/unitary/tools/peak_p1_proxy/test_cli.py \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py \
  -q
```

Expected: tests pass.

## Task 4: Verification and Commit

**Files:**
- Modify: `tools/peak_p1_proxy/cli.py`
- Modify: `tools/peak_p1_proxy/runtime.py`
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_cli.py`
- Modify: `src/test/unitary/tools/peak_p1_proxy/test_runtime.py`

- [x] **Step 1: Run focused tests**

Run:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy -q
```

Expected: all proxy tests pass.

- [x] **Step 2: Run syntax checks**

Run:

```bash
src/.venv/bin/python -m py_compile \
  tools/p1_serial_proxy.py \
  tools/peak_p1_proxy/cli.py \
  tools/peak_p1_proxy/runtime.py \
  tools/peak_p1_proxy/modbus_rtu.py \
  tools/peak_p1_proxy/model.py \
  tools/peak_p1_proxy/cache.py
```

Expected: no output and exit code `0`.

- [x] **Step 3: Run loop dry-run**

Run:

```bash
src/.venv/bin/python tools/p1_serial_proxy.py \
  --real-port loop:// \
  --artisan-port loop:// \
  --cropster-port loop:// \
  --dry-run
```

Expected:

```text
dry run ok
```

- [x] **Step 4: Commit implementation**

Run:

```bash
git add \
  tools/peak_p1_proxy/cli.py \
  tools/peak_p1_proxy/runtime.py \
  src/test/unitary/tools/peak_p1_proxy/test_cli.py \
  src/test/unitary/tools/peak_p1_proxy/test_runtime.py \
  docs/superpowers/plans/2026-06-14-peak-p1-proxy-reconnect.md
git commit -m "fix: reconnect peak p1 serial polling"
```

Expected: one implementation commit containing only the proxy reconnect fix, tests, and this plan.
