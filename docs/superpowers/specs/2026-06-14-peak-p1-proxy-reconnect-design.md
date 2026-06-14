# Peak P1 Proxy Reconnect Design

## Context

The Peak P1 serial proxy can successfully bridge Artisan and Cropster when the real roaster USB serial link is healthy. During a live run, the proxy logged repeated Peak P1 Modbus requests with no matching response:

```text
Peak P1 Modbus poll failed: short Modbus response: expected 3, got 0
```

The frame log showed that Artisan continued talking to the proxy, but the real P1 side only emitted `p1 tx` records and no `p1 rx` records. A later restart failed before polling, while opening the FTDI device through pyserial:

```text
termios.error: (22, 'Invalid argument')
```

This means there are two related failure surfaces:

- The real Peak P1 link can stop responding while the virtual Artisan and Cropster links remain alive.
- macOS can surface FTDI open/configuration failures as `termios.error`, not only `serial.SerialException`.

## Goals

- Keep Artisan and Cropster connected when the real P1 temporarily stops responding.
- Reopen the real P1 serial port automatically after repeated poll failures.
- Report startup/open failures as clear CLI diagnostics instead of Python tracebacks.
- Make automatic reconnect the default, with an escape hatch for manual diagnosis.
- Preserve the existing Artisan TC4 responder and Cropster Modbus responder behavior.

## Non-Goals

- Do not change Peak P1 register mappings.
- Do not change the virtual port setup model on macOS or Windows.
- Do not make the proxy hide stale data as fresh data.
- Do not attempt OS-level USB driver resets; if macOS refuses `tcsetattr`, the proxy should explain the likely hardware/driver recovery step.

## Design

The proxy will keep the current three-role architecture:

- Real P1 poller reads the roaster through Modbus RTU.
- Artisan server answers HB Model S / TC4-style text commands from cache.
- Cropster server answers Modbus RTU requests from cache.

The real P1 side will gain a reconnecting runner. Instead of opening the real serial port once for the entire proxy lifetime, the runtime opens it inside the poller loop. If polling succeeds, cache updates continue as before. If polling fails repeatedly, the runner closes the real port, waits for a short backoff, and tries to reopen it.

The virtual Artisan and Cropster ports stay open during real-port reconnect attempts. While the cache is stale, Artisan continues receiving `-1.00,-1.00,-1.00,C` and Cropster receives a Modbus exception as it does today. This makes data loss visible to both clients without tearing down their sessions.

## CLI Behavior

The default behavior is automatic reconnect:

```text
--auto-reconnect enabled by default
```

Users can disable it for diagnosis:

```text
--no-auto-reconnect
```

New tuning options:

- `--reconnect-after-failures`, default `3`
- `--reconnect-delay`, default `2.0`

Startup and dry-run port failures will catch both pyserial errors and platform serial configuration errors such as `termios.error`. The CLI will print:

- the failed operation
- the exception text
- visible serial ports
- a short hint when the error is likely a macOS FTDI/USB driver state issue

## Error Handling

Single poll failures are logged as warnings and do not immediately reopen the port. Consecutive failures are counted. Once the count reaches `--reconnect-after-failures`, the current real serial handle is closed and the runner waits `--reconnect-delay` seconds before reopening.

Opening failures are also retried in auto-reconnect mode. If auto-reconnect is disabled, the first real-port open failure is raised to the CLI and reported as a friendly fatal error.

The frame log remains useful for diagnosis:

- successful real reads continue to produce `p1 tx` and `p1 rx`
- no-response failures show `p1 tx` without `p1 rx`
- reconnect attempts are logged through normal application logging, not as fake protocol frames

## Testing

Unit tests will cover:

- CLI dry-run catches `termios.error` and reports visible ports.
- CLI runtime startup catches real-port open errors and returns exit code `2`.
- Auto-reconnect reopens the real serial port after repeated Modbus poll failures.
- `--no-auto-reconnect` preserves fail-fast behavior for startup/open failures.
- Existing Artisan TC4 and Cropster Modbus responder tests still pass unchanged.

Manual verification will use:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy -q
src/.venv/bin/python tools/p1_serial_proxy.py --real-port loop:// --artisan-port loop:// --cropster-port loop:// --dry-run
```

Hardware verification, when the Peak P1 FTDI port is healthy again, will use the normal macOS virtual port setup and confirm that transient real-port failures no longer terminate Artisan/Cropster sessions.
