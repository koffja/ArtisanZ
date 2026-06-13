# Peak P1 Serial Proxy Design

Date: 2026-06-14
Status: Approved for implementation planning

## Context

The HB Peak P1 is connected over USB serial. Artisan can read the roaster with
the HB Model S profile, which uses the ArduinoTC4-style text protocol rather
than Modbus. The observed Artisan polling pattern is:

- `CHAN;3400`, then `READ` for the BT/ET pair.
- `CHAN;1200`, then `READ` for the Exhaust/Inlet pair.
- Serial settings: 115200 baud, 8 data bits, no parity, 1 stop bit.

Cropster's official Peak P1 setup is Generic Modbus over serial:

- Encoding: RTU.
- Serial settings: 115200 baud, 8 data bits, no parity, 1 stop bit.
- Modbus function: 4, Read Input Registers.
- Temperature format: 16-bit integer, decimal with one digit, Celsius.
- Bean temperature: slave 1, register 0.
- Exhaust temperature: slave 1, register 3.

Both applications cannot safely open and poll the same physical USB serial port
at the same time. The proxy will own the physical port and expose separate
virtual serial ports to Artisan and Cropster.

## Goals

- Let Artisan and Cropster read the Peak P1 at the same time.
- Keep Artisan on the HB Model S text protocol so it can continue receiving BT,
  ET, Exhaust, and Inlet.
- Keep Cropster on its official Generic Modbus RTU setup.
- Support macOS and Windows from the first implementation.
- Implement the first version as a command-line tool.
- Restrict the first version to read-only temperature data.
- Include frame logging so Cropster's exact polling shape can be confirmed
  during normal proxy testing.

## Non-Goals

- Do not implement heater, fan, airflow, pressure, or other control writes.
- Do not install or implement kernel-level virtual serial drivers.
- Do not require changing Cropster's data model.
- Do not require changing Artisan source code for the first version.
- Do not rely on Cropster packet capture as a prerequisite for design.

## Architecture

The proxy is a Python CLI with one real-device poller and two virtual serial
servers.

```text
Peak P1 physical serial port
  -> P1Poller
  -> TemperatureCache
  -> ArtisanTc4Server      -> Artisan virtual serial port
  -> CropsterModbusServer  -> Cropster virtual serial port
```

Only `P1Poller` talks to the physical Peak P1 USB serial port. Artisan and
Cropster never forward requests directly to the real roaster; they only receive
responses based on `TemperatureCache`.

## Components

### P1Poller

Responsibilities:

- Open the physical Peak P1 serial port exclusively.
- Poll on a fixed interval, defaulting to once per second.
- Send `CHAN;3400` and `READ` to collect the BT/ET pair.
- Send `CHAN;1200` and `READ` to collect the Exhaust/Inlet pair.
- Parse CSV responses ending in `C`.
- Publish valid samples to `TemperatureCache`.

The poller serializes all physical-port traffic, so client request timing cannot
change the Peak P1 channel state.

### TemperatureCache

Responsibilities:

- Store the latest BT, ET, Exhaust, and Inlet values.
- Store the timestamp of the latest fully valid sample.
- Track stale and disconnected states.
- Provide a thread-safe read API for both virtual serial servers.

Short read failures do not immediately erase the last known values. A sample is
considered stale only after the configured stale timeout, defaulting to five
seconds.

### ArtisanTc4Server

Responsibilities:

- Open the proxy-side Artisan virtual serial endpoint.
- Accept the HB Model S text command subset used by Artisan:
  - `CHAN;3400`
  - `CHAN;1200`
  - `READ`
- Track the last requested channel group per Artisan connection.
- Return CSV responses compatible with Artisan's ArduinoTC4 parser.

Response shape:

```text
AT,channel_a,channel_b,C
```

The AT field is kept for parser compatibility even though it is not exposed in
the current Artisan configuration. The first implementation will use a stable
compatibility value derived from ET or zero, with the behavior documented in the
runtime log.

### CropsterModbusServer

Responsibilities:

- Open the proxy-side Cropster virtual serial endpoint.
- Parse Modbus RTU frames.
- Validate CRC.
- Support slave ID 1.
- Support function 4, Read Input Registers.
- Return 16-bit register values with one decimal digit.

Default register mapping:

```text
register 0 = BT * 10
register 3 = Exhaust * 10
```

The register mapping will be configurable so register 3 can be remapped to ET
if real-world Cropster comparison shows that is the expected curve.

If Cropster requests a continuous block that includes undefined registers, the
proxy returns defined values for known registers and zero for undefined
registers. If Cropster requests unsupported function codes or slave IDs, the
proxy returns a Modbus exception.

## Cross-Platform Virtual Serial Strategy

The proxy does not create virtual serial drivers itself. The user creates paired
virtual serial ports with platform tools, then passes the proxy-side endpoints
to the CLI.

### macOS

Use `socat` to create PTY pairs. Artisan and Cropster connect to one side of
each pair; the proxy opens the paired side.

### Windows

Use a virtual COM pair tool such as com0com. Artisan and Cropster connect to one
COM port in each pair; the proxy opens the paired COM ports.

This keeps the first implementation portable and avoids driver development.

## CLI

Required runtime options:

```text
p1-serial-proxy \
  --real-port <physical-port> \
  --artisan-port <proxy-artisan-port> \
  --cropster-port <proxy-cropster-port>
```

Useful options:

```text
--real-baud 115200
--poll-interval 1.0
--stale-after 5.0
--cropster-register-bt 0
--cropster-register-exhaust 3
--cropster-register-3-source exhaust
--list-ports
--dry-run
--verbose
--log-frames <path>
```

`--list-ports` prints currently visible serial ports. `--dry-run` verifies that
configured ports can be opened and that the settings are internally consistent,
then exits without starting the poll loop.

## Error Handling

- If the physical Peak P1 port cannot be opened, exit with a clear error and
  show visible serial ports.
- If either virtual serial port cannot be opened, exit and identify the failed
  side.
- If one P1 polling round fails, log a warning and keep the last valid sample.
- If the cache becomes stale:
  - Artisan returns invalid temperatures by default.
  - Cropster returns a Modbus exception by default.
- If Cropster sends a bad CRC, ignore the frame and log it in verbose mode.
- If Cropster sends unsupported Modbus requests, return Modbus exceptions.

## Logging

Default logging:

- Startup configuration.
- Connected port names.
- Periodic BT, ET, Exhaust, Inlet status.
- State transitions such as connected, stale, and disconnected.

Verbose logging:

- Each P1 polling step.
- Parsed temperature values.
- Artisan command summaries.
- Cropster request summaries.

Frame logging:

- Raw P1 text TX/RX.
- Raw Artisan text TX/RX.
- Raw Cropster Modbus RTU TX/RX as hex.

Frame logging is the built-in way to confirm Cropster's exact polling behavior
without building a separate capture utility first.

## Validation Plan

### Unit Tests

- Parse valid and invalid Peak P1 CSV responses.
- Verify BT/ET and Exhaust/Inlet channel assignment.
- Encode Artisan TC4-compatible responses.
- Decode Modbus RTU request frames.
- Validate Modbus CRC behavior.
- Encode Modbus function 4 responses.
- Verify register scaling by 10.
- Verify stale-cache behavior.

### Simulation Tests

- Run a fake P1 serial endpoint returning deterministic values.
- Connect fake Artisan and fake Cropster clients to virtual endpoints.
- Verify both clients can read from the same cached sample.
- Verify client polling frequency does not change physical poll frequency.

### macOS Hardware Test

- Create virtual serial pairs with `socat`.
- Start the proxy against the real Peak P1 port.
- Configure Artisan to use its virtual port with HB Model S behavior.
- Configure Cropster to use its virtual port with official Modbus settings.
- Enable `--log-frames` and confirm Cropster's actual request pattern.

### Windows Hardware Test

- Create virtual COM pairs with com0com.
- Start the same CLI against the real Peak P1 COM port.
- Configure Artisan and Cropster against their paired COM ports.
- Confirm both applications receive stable curves at the same time.

## Implementation Boundaries

The first implementation should live outside Artisan's main runtime path so it
can be developed and tested as a small standalone tool. It can be added under a
repository `tools/` or similar utility location, with tests colocated or under
the existing test tree depending on the project conventions selected during
implementation planning.

The first release is successful when:

- The proxy starts from the command line on macOS and Windows.
- Artisan reads BT, ET, Exhaust, and Inlet through the proxy.
- Cropster reads BT and Exhaust through the proxy.
- Both applications can run at the same time without opening the physical Peak
  P1 serial port directly.
- Logs provide enough raw frame evidence to adjust Cropster register behavior if
  needed.
