# Peak P1 Modbus Read Hardening Design

## Context

The Peak P1 proxy occasionally logs two different real-port polling failures while otherwise recovering on the next poll:

- `list index out of range`
- `short Modbus response: expected 3, got 0`

Frame logs show that `list index out of range` can happen after a valid CRC Modbus response that returns fewer registers than the request needs. For example, the proxy requests four input registers:

```text
010400000004f1c9
```

but the roaster can occasionally respond with only one register:

```text
01040204abfa4f
```

The current code parses that frame, then fails later while indexing register 3. That produces a generic Python error instead of a useful protocol diagnostic.

## Goals

- Replace `list index out of range` with an explicit short-register response error.
- Avoid using incomplete register responses to update the cache.
- Clear stale input bytes before each real P1 Modbus request when the serial object supports it.
- Preserve the existing register mapping, reconnect behavior, and Artisan/Cropster virtual protocols.

## Non-Goals

- Do not change Peak P1 Modbus register addresses.
- Do not add immediate retry inside a single poll.
- Do not change the cache stale policy.
- Do not change Cropster or Artisan responder behavior.

## Design

`P1ModbusPoller` will calculate the required register count once from the configured register indexes. Before writing each Modbus request, it will call `reset_input_buffer()` if the serial object provides that method. This should reduce the chance of reading stale bytes from an earlier transaction.

After parsing the Modbus response, the poller will check that the response contains at least the required number of registers. If the response is short, it will raise:

```text
short Modbus register response: expected at least 4 registers, got 1
```

The reconnect runner will continue to treat this as a poll failure. If failures are consecutive and reach the configured threshold, it will close and reopen the real serial port as before.

## Testing

Unit tests will cover:

- A one-register response to a four-register request raises the explicit short-register error.
- The poller calls `reset_input_buffer()` before sending a real P1 Modbus request when available.
- Existing successful Modbus polling still updates the cache with the same BT/ET/Exhaust/Inlet values.

Verification:

```bash
src/.venv/bin/python -m pytest src/test/unitary/tools/peak_p1_proxy -q
src/.venv/bin/python -m py_compile tools/p1_serial_proxy.py tools/peak_p1_proxy/cli.py tools/peak_p1_proxy/runtime.py tools/peak_p1_proxy/modbus_rtu.py tools/peak_p1_proxy/model.py tools/peak_p1_proxy/cache.py
```
