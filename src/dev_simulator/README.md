# ArtisanZ Temperature Simulator

The ArtisanZ temperature simulator is a standalone development WebSocket server that streams synthetic BT and ET roast curves into ArtisanZ. It is intended for testing charge-target behavior, event handling, RoR plotting, and roast-cycle workflows when no physical roaster or temperature device is available.

## Quick Start

1. Install dependencies from the project `src/` directory:

   ```bash
   cd src
   python3 -m pip install -r requirements.txt
   python3 -m pip install -r requirements-dev.txt
   ```

2. Start the simulator:

   ```bash
   cd src
   python3 -m dev_simulator.artisan_simulator
   ```

   By default, the simulator listens at `ws://127.0.0.1:80/WebSocket`. If binding to port 80 fails, the CLI retries on port 8080 and logs a warning.

3. Configure ArtisanZ to use the WebSocket device, then click **ON**. In automatic start mode, the simulator pushes CHARGE on the first `getData` request and then fires DRY, FCs, FCe, SCs, and DROP on the default event schedule shown below.

## ArtisanZ WebSocket Configuration

Open ArtisanZ and configure the WebSocket device once:

1. Open **Config -> Device...**.
2. Select the **WebSocket** device tab.
3. Set **Host** to `127.0.0.1`.
4. Set **Port** to `80` by default, or `8080` if the simulator logged a port-80 fallback.
5. Set **Path** to `WebSocket`.
6. Set **Request data command** to `getData`.
7. Configure channel 0:
   - Node: `BT`
   - Mode: `C`
8. Configure channel 1:
   - Node: `ET`
   - Mode: `C`
9. Save the device configuration.
10. Click **ON** to start sampling from the simulator.

## Channel Mapping Warning

> **Important:** Configure channel 0 as `BT` and channel 1 as `ET`.

ArtisanZ's WebSocket reader maps the returned readings in a swapped order. The simulator sends data as:

```json
{"data": {"BT": 180.0, "ET": 190.0}}
```

Using channel 0 = `BT` and channel 1 = `ET` makes the values land in the correct BT and ET slots. Reversing these node names is a silent failure: ArtisanZ will still draw curves, but BT and ET will be swapped and RoR/charge-target behavior will be misleading.

## CLI Reference

Run `python3 -m dev_simulator.artisan_simulator --help` for the live argparse output.

### Connection flags

- `--host HOST` — bind host. Default: `127.0.0.1`.
- `--port PORT` — bind port. Default: `80`; falls back to `8080` on port-80 bind errors.
- `--path PATH` — WebSocket path. Default: `WebSocket`.

### Profile flags

- `--preset {light,medium,dark,custom}` — starting curve preset. Default: `medium`.
- `--charge-t SECONDS` — CHARGE time; must be non-negative and earlier than `--turn-t`.
- `--charge-bt VALUE` — CHARGE BT in degrees C.
- `--turn-bt VALUE` — turn-point BT in degrees C.
- `--dry-bt VALUE` — dry-end BT in degrees C.
- `--fcs-bt VALUE` — first-crack-start BT in degrees C.
- `--fce-bt VALUE` — first-crack-end BT in degrees C.
- `--scs-bt VALUE` — second-crack-start BT in degrees C.
- `--drop-bt VALUE` — DROP BT in degrees C.
- `--turn-t SECONDS` — turn-point time.
- `--dry-t SECONDS` — dry-end time.
- `--fcs-t SECONDS` — first-crack-start time.
- `--fce-t SECONDS` — first-crack-end time.
- `--scs-t SECONDS` — second-crack-start time.
- `--drop-t SECONDS` — DROP time.

### Runtime flags

- `--start-mode {auto,manual}` — automatic CHARGE push or manual CHARGE in ArtisanZ. Default: `auto`.
- `--noise-std VALUE` — temperature noise standard deviation in degrees C. Default: `0.3`.
- `--noise-model {gaussian,ar1,none}` — noise model. Default: `ar1`.
- `--log-level {debug,info,warning,error}` — log verbosity. Default: `info`.

### Examples

Run on the fallback port explicitly:

```bash
python3 -m dev_simulator.artisan_simulator --port 8080
```

Run a deterministic clean curve for repeatable manual testing:

```bash
python3 -m dev_simulator.artisan_simulator --noise-model none --noise-std 0
```

Run a custom temperature curve with a later DROP temperature/time. This changes the generated BT/ET curve; the pushed event schedule remains fixed unless the simulator code is changed.

```bash
python3 -m dev_simulator.artisan_simulator --preset custom --drop-t 840 --drop-bt 220
```

Use manual CHARGE mode:

```bash
python3 -m dev_simulator.artisan_simulator --start-mode manual
```

## Default Event Schedule

The simulator currently uses these fixed server-pushed event times for every preset and CLI timing override:

| Time | Message | ArtisanZ effect |
|---:|---|---|
| 0:00 | `{"pushMessage": "startRoasting"}` | CHARGE |
| 5:00 | `{"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}` | DRY |
| 9:30 | `{"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}` | FCs |
| 10:45 | `{"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}` | FCe |
| 12:45 | `{"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}` | SCs |
| 13:00 | `{"pushMessage": "endRoasting"}` | DROP |

Timing flags such as `--dry-t`, `--fcs-t`, and `--drop-t` adjust the generated temperature curve only. They do not move the pushed DRY/FCs/FCe/SCs/DROP events.

## Manual E2E Checklist

1. From `src/`, start the simulator with `python3 -m dev_simulator.artisan_simulator`.
2. Confirm the log shows the expected WebSocket endpoint.
3. Open ArtisanZ.
4. Confirm the WebSocket device host, port, and path match the simulator endpoint.
5. Confirm channel 0 is `BT` and channel 1 is `ET`.
6. Click **ON** in ArtisanZ.
7. Confirm CHARGE is created automatically in `auto` mode, or click CHARGE manually in `manual` mode.
8. Watch BT dip from about 180°C to 95°C around 1:30, then rise through the remaining roast.
9. Confirm DRY, FCs, FCe, SCs, and DROP appear at the scheduled times.
10. Stop ArtisanZ sampling and stop the simulator with `Ctrl+C`.

## Troubleshooting

### Port 80 is unavailable

Port 80 may require elevated privileges or already be used by another process. The CLI automatically retries port 8080 only when the requested port is 80. If you see a fallback warning, update ArtisanZ's WebSocket port to `8080`, or start the simulator with `--port 8080`.

### ArtisanZ does not connect

Check that the simulator is still running, ArtisanZ uses the same host/port/path, and the path is `WebSocket` without a leading slash in the UI. If using another host, make sure the server is bound to an address ArtisanZ can reach.

### Curves appear swapped

Recheck the channel node names. Channel 0 must be `BT` and channel 1 must be `ET` for ArtisanZ's WebSocket reader to place the data correctly.

### Events do not appear

In `auto` mode, CHARGE is pushed on the first `getData` request, so ArtisanZ must be sampling. In `manual` mode, CHARGE is intentionally not pushed; click CHARGE in ArtisanZ yourself.

### The curve jumps after pausing

The server advances simulated time only when ArtisanZ sends requests and caps catch-up jumps after pauses. If you need a fresh timeline, stop and restart the simulator.
