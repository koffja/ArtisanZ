# Peak P1 End-To-End Recovery Design

## Context

The proxy already reconnects the real Peak P1 input port. However, Cropster can still stop receiving fresh data until the proxy or Cropster is restarted. The likely failure modes are:

- The real P1 input recovers, but Cropster has already treated Modbus exception responses as a device failure.
- The Cropster virtual serial server thread exits after a virtual port read/write error and is not restarted.
- The Artisan virtual serial server has the same one-shot lifecycle risk.

The goal is to keep the proxy process alive and keep both output endpoints recoverable without requiring `Ctrl-C` and a manual restart.

## Goals

- Reopen Artisan and Cropster virtual serial ports after read/write/open failures.
- Keep the proxy process alive while output ports reconnect.
- Let Cropster receive the last valid sample for a short configurable hold window while the P1 source is temporarily stale.
- Keep default behavior biased toward avoiding Cropster offline state.
- Preserve existing Modbus register mapping and HB/TC4 text protocol behavior.

## Non-Goals

- Do not invent new Peak P1 registers.
- Do not change Cropster's configured Modbus function or register addresses.
- Do not hide long source outages forever.
- Do not replace the user's existing `socat`/virtual COM setup.

## Design

Add a generic `ReconnectingSerialServerRunner` for output-side serial servers. It owns one virtual serial port, opens it, creates the matching server, runs it, and catches failures. On failure it closes the port, waits a reconnect delay, and tries to open the same configured port again. This mirrors the real P1 reconnect runner, but wraps `ArtisanSerialServer` and `CropsterSerialServer`.

`ProxyRuntime` will no longer open Artisan and Cropster ports once in the main thread. Instead, it will start:

- one real P1 runner thread
- one reconnecting Artisan virtual serial runner thread
- one reconnecting Cropster virtual serial runner thread

Add a `--virtual-reconnect-delay` CLI option, default `2.0`, for output port retries.

For Cropster, add `--cropster-hold-last-for`, default `60.0`. When the cache is stale but still has a last sample whose age is within this window, Cropster returns normal Modbus register values from that held sample instead of a Modbus exception. If no sample exists, or the sample is older than the hold window, Cropster keeps returning the current Modbus exception. Setting `--cropster-hold-last-for 0` disables this behavior.

Artisan keeps strict stale behavior and continues returning `-1.00` when the cache is stale.

## Error Handling

- Real P1 failures remain logged by `ReconnectingP1Runner`.
- Output port failures are logged as `<name> serial server failed: ...`.
- Output open failures are logged as `<name> serial open failed: ...`.
- Server threads keep retrying until the proxy receives stop.

## Testing

Unit tests will cover:

- Cropster returns held last values while a stale sample is within the hold window.
- Cropster returns a Modbus exception when held last is disabled or expired.
- The reconnecting output server runner closes a failed serial handle and reopens a new one.
- `ProxyRuntime` passes the Cropster hold option and virtual reconnect delay from CLI arguments.

Verification:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy -q
src/.venv/bin/python -m py_compile tools/p1_serial_proxy.py tools/peak_p1_proxy/cli.py tools/peak_p1_proxy/runtime.py tools/peak_p1_proxy/modbus_rtu.py tools/peak_p1_proxy/model.py tools/peak_p1_proxy/cache.py
```
