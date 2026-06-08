# ArtisanZ Temperature Simulator — Design Spec

**Date**: 2026-06-07
**Status**: Draft (awaiting user review)
**Author**: brainstorming session with user
**Branch**: `ArtisanZ`

---

## 1. Background

### 1.1 Problem
The user is developing `charge_target` features in ArtisanZ (see `src/artisanlib/charge_manager.py`, `charge_dialog.py`). Testing these features end-to-end normally requires a physical roaster that produces a realistic BT/ET temperature curve.

The user has no roaster connected that delivers a clean temperature stream. They want a way to feed ArtisanZ synthetic BT/ET data so that:

- `charge_target`'s readiness logic can be exercised through full charge → drop cycles.
- Charge events (`markCHARGE` / `markDRY` / `markFCs` / `markFCe` / `markSCs` / `markDROP`) can be triggered programmatically.
- The ArtisanZ plotting pipeline (RoR smoothing, alarms, profiles) can be observed against a known curve shape.

### 1.2 Prior art in the repo
A pre-existing `Simulator` class lives at `src/artisanlib/simulator.py` (163 lines, Marko Luther 2023). It replays a recorded `.alog` profile dict and exposes `read(tx) → (et, bt)` for the in-process `SampleThread`. It is activated via `Tools → Simulator` (see `main.py:27865` `simulate()`). It is **not** a standalone script and does **not** speak the WebSocket protocol.

No WebSocket-based temperature simulator, fake-device script, or replay harness exists in the repo. Git history (all branches, reflog, deleted-file diff) confirms no prior attempt.

### 1.3 Approach
Build a **standalone Python script** that:

1. Generates a parameterized 6-segment coffee-roast profile (BT/ET as functions of time): charge dip → drying → Maillard → development Ⅰ → development Ⅱ → final.
2. Speaks the Artisan WebSocket protocol (`ws://<host>:<port>/<path>`, JSON over text frames) — making ArtisanZ treat the script as a real roaster.
3. Pushes the 6 charge events at predetermined times.
4. Reuses the existing `Simulator` class for interpolation and unit conversion.

ArtisanZ source code is **not modified**. Configuration is done once in the ArtisanZ WebSocket device dialog.

---

## 2. Goals & Non-Goals

### Goals
- Run a realistic 8–13 minute synthetic roast end-to-end through the ArtisanZ sampling pipeline.
- Fire `markCHARGE / markDRY / markFCs / markFCe / markSCs / markDROP` events at the configured times.
- Allow per-event temperature overrides via CLI flags.
- Allow noise injection (default: `ar1` model, σ=0.3°C) for realism.
- Reuse the existing in-process `Simulator` class for interpolation so we don't reimplement `numpy.interp` + unit conversion.
- Add unit + integration tests.

### Non-Goals
- Replicating a real roaster's exact electrical protocol.
- Multi-client support beyond a single ArtisanZ instance (multi-client works because `websockets.serve` is multi-conn, but state is shared and untested).
- Persistence of state across server restarts (a server restart = a new roast).
- Production-grade authentication / TLS / compression tuning (ArtisanZ's `wsport` already negotiates `deflate`, our server supports it via the `websockets` library).
- A GUI for the simulator. CLI only.

---

## 3. User Scenario

> A user developing ArtisanZ charge_target features wants to verify the readiness logic without a physical roaster. They run `python3 -m dev_simulator.artisan_simulator` in a terminal, point ArtisanZ at the WebSocket device at `ws://127.0.0.1:80/WebSocket`, and click ON. The simulator immediately pushes `startRoasting` (triggering CHARGE), then returns synthetic BT/ET every 2 seconds and fires DRY/FCs/FCe/SCs/DROP at the configured times. The user watches ArtisanZ plot the curve and react to the events, exercising charge_target against a known-good input.

---

## 4. Architecture

```
┌────────────────────────────────────────────┐         ┌──────────────────────────────┐
│  artisan_simulator.py（独立 Python 进程）    │  ws://  │  ArtisanZ                    │
│                                            │ 127.0.0.1 │  选设备 = WebSocket         │
│  ┌──────────────┐   ┌──────────────┐       │ :80/    │  配置 channel_nodes[0]      │
│  │ RoastSpec    │──→│ generate_    │       │ WebSocket│  = "BT", [1] = "ET"（顺序）  │
│  │ （5 阶段参数）│   │ profile()    │       │◄────────┤  channel_modes = C          │
│  └──────────────┘   └──────┬───────┘       │ getData │                              │
│         │  7 anchor points  │              │  数据  │  ON → SampleThread 每 2s   │
│         ▼                   ▼              │────────►│  调用 WSread(0)             │
│  ┌──────────────┐   ┌──────────────┐        │         │  wsport.send(getData)        │
│  │  10 Hz       │   │  Simulator   │        │         │                              │
│  │  高分辨率曲线 │──→│ （复用自     │        │         │  收到 pushMessage           │
│  │  + 噪声      │   │  simulator.py）│       │         │  → markCHARGE / markDRY     │
│  └──────────────┘   └──────┬───────┘        │         │  → markFCs / markFCe        │
│                            │ read(tx)        │         │  → markSCs / markDROP       │
│  ┌─────────────────────────▼──────────────┐ │         │                              │
│  │ AsyncServer                            │ │         │  charge_target 实时算就绪度  │
│  │  - 时间模型 (frozen / sim_t)            │─┼─事件───►│  BT/ET 曲线实时绘制         │
│  │  - EventScheduler                      │ │         │                              │
│  │  - WebSocket 协议收发                   │ │         │                              │
│  └────────────────────────────────────────┘ │         └──────────────────────────────┘
└────────────────────────────────────────────┘
```

### 4.1 Data Flow
1. `artisan_simulator.py` builds a `RoastSpec` from CLI args / preset.
2. `generate_profile(spec)` interpolates 7 key points (with cosine ease-in-out) into a 10 Hz profile dict.
3. The dict is passed to the existing `Simulator` class (`artisanlib.simulator.Simulator`).
4. `AsyncServer.handle(ws)` runs per connection:
   - On each `getData` request: advance `sim_t`, call `simulator.read(sim_t) + noise`, return as JSON.
   - On every tick: check `EventScheduler.fire_due(sim_t)`; for each due event, send the appropriate `pushMessage`.
5. `time.monotonic()` drives `sim_t`. `sim_t` advances **only on incoming requests** (frozen between requests; capped at 3s per request to avoid catch-up jumps after long pauses; frozen — `sim_t` preserved — if no request for >30s). See §8.1 for the exact algorithm.

### 4.2 Reused Components
| Component | Source | How reused |
|---|---|---|
| `Simulator` class | `src/artisanlib/simulator.py:32` | Direct `import`; used for `numpy.interp` + F/C unit conversion |
| WebSocket protocol constants | `src/artisanlib/wsport.py:86-105` | Constants `id_node='id'`, `command_node='command'`, `data_node='data'`, `pushMessage_node='pushMessage'` (86–90) and event push message strings (92–105) |
| Test fixture pattern | `src/test/unitary/artisanlib/test_wsport.py:24-56` | Style reference for integration test mocks |
| Real profile fixtures | `src/test/data/profile1.alog` | NOT used — this is a synthetic generator, not a replayer |

### 4.3 Zero-Modification Boundary
The simulator script does **not** import any ArtisanZ runtime code. It only imports `artisanlib.simulator.Simulator` for the data engine. ArtisanZ is configured entirely through its existing WebSocket device dialog.

---

## 5. Curve Model

### 5.1 Key Nodes (7 anchor points, 6 fired events)

| # | Event | t (s) | t (mm:ss) | BT (°C) | ET (°C) | ET-BT gap |
|---|---|---:|:---:|---:|---:|---:|
| 1 | **CHARGE** | 0 | 0:00 | 180 | 190 | 10 |
| 2 | turn point | 90 | 1:30 | 95 | 180 | 85 |
| 3 | **DRY END** | 300 | 5:00 | 152 | 170 | 18 |
| 4 | **FCs** | 570 | 9:30 | 193 | 205 | 12 |
| 5 | **FCe** | 645 | 10:45 | 202 | 212 | 10 |
| 6 | **SCs** | 765 | 12:45 | 215 | 222 | 7 |
| 7 | **DROP** | 780 | 13:00 | 218 | 224 | 6 |

> **turn point** is an internal curve feature (lowest BT after charge dip). It is **not** fired as a WebSocket event — the WS protocol has no "turn point" event type.

### 5.2 Segment Rates

| Segment | Δt (s) | ΔBT (°C) | RoR (°C/min) | Phase |
|---|---:|---:|---:|---|
| 1→2 | 90 | -85 | -56.7 | Charge dip |
| 2→3 | 210 | +57 | +16.3 | Drying |
| 3→4 | 270 | +41 | +9.1 | Maillard |
| 4→5 | 75 | +9 | +7.2 | Development Ⅰ (FCs → FCe) |
| 5→6 | 120 | +13 | +6.5 | Development Ⅱ (FCe → SCs) |
| 6→7 | 15 | +3 | +12.0 | Final (SCs → DROP) |

### 5.3 Interpolation
- Cosine ease-in-out between consecutive key nodes.
- Profile dict sampled at 10 Hz → 7,800 points for 780s.
- Format: `{"timex": [...], "temp1": [...], "temp2": [...], "mode": "C"}` (matches `Simulator` constructor contract).

### 5.4 Noise Models

| Model | Behavior | Default σ | Use case |
|---|---|---:|---|
| `gaussian` | IID `N(0, σ)` per sample | 0.3°C | Quick tests |
| `ar1` | AR(1) process with mean reversion | 0.3°C | Realistic; default |
| `none` | No noise (clean curve) | — | Unit tests |

The `ar1` model: `x[t+1] = α * x[t] + N(0, σ² * (1 - α²))` with `α = 0.85`. This produces temporally correlated noise that better matches real thermocouple probe behavior than IID Gaussian.

### 5.5 Event Schedule

| t (mm:ss) | WebSocket message | Artisan effect |
|:---:|---|---|
| 0:00 | `{"pushMessage": "startRoasting"}` | `markCHARGE` |
| 5:00 | `{"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}` | `markDRY` |
| 9:30 | `{"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}` | `markFCs` |
| 10:45 | `{"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}` | `markFCe` |
| 12:45 | `{"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}` | `markSCs` |
| 13:00 | `{"pushMessage": "endRoasting"}` | `markDROP` |

`EventScheduler` tracks a `fired: set[int]` to ensure each event is sent exactly once. Multiple events firing at the same `sim_t` are sent in order with 50ms spacing.

---

## 6. WebSocket Protocol

### 6.1 Wire Format

**Request** (Artisan → Server, per `wsport.py:365-403`):
```json
{
  "command": "getData",
  "id": 42871,
  "roasterID": 0
}
```
Node names (`"command"`, `"id"`, `"roasterID"`) are configurable in ArtisanZ; defaults are used here.

**Response** (Server → Artisan):
```json
{
  "id": 42871,
  "data": {
    "BT": 178.42,
    "ET": 188.41
  }
}
```
The `id` MUST echo back the request id so `wsport.registerRequest` can match the response (`wsport.py:117-141`).

**Server-pushed events** (no request):
```json
{"pushMessage": "startRoasting"}
{"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}
{"pushMessage": "endRoasting"}
```

### 6.2 Channel Mapping Trap ⚠️

`WSread` returns `(tx, readings[mode*2+1], readings[mode*2])` — i.e., the second and third positions are swapped from the usual `(ET, BT)` convention (`comm.py:1954`). To make the data land in the correct slots (temp1=ET, temp2=BT), the user MUST configure ArtisanZ as follows:

| Channel index | Node name (in UI) | Server `data` key | Lands in |
|:---:|:---:|:---:|---|
| 0 | `BT` | `"BT"` | BT |
| 1 | `ET` | `"ET"` | ET |

Swapping the names puts BT in the ET slot and vice versa, and the RoR computation will use the wrong curve. This is a **silent** failure — ArtisanZ will draw a curve, just the wrong one.

### 6.3 Default Runtime Flow

```
1. Terminal: python3 -m dev_simulator.artisan_simulator
2. Server starts on ws://127.0.0.1:80/WebSocket (frozen, t=0 not yet advancing)
3. User opens ArtisanZ (already configured for WebSocket device)
4. User clicks ON
5. Artisan starts SampleThread; first getData request arrives
6. Server:
   - First request arrives; `sim_t` un-freezes at 0
   - Server pushes `startRoasting` → Artisan `markCHARGE` at `sim_t=0`
   - Server responds with `{id, data: {BT:180, ET:190}}`
7. Server continues: every 2s, advance t, respond with BT/ET at that t + noise
8. At t=300s: server pushes addEvent(colorChangeEvent) → Artisan markDRY
9. At t=570s: server pushes addEvent(FCs) → Artisan markFCs
10. At t=645s: server pushes addEvent(FCe) → Artisan markFCe
11. At t=765s: server pushes addEvent(SCs) → Artisan markSCs
12. At t=780s: server pushes endRoasting → Artisan markDROP
13. Server continues responding to getData (BT held at 218, ET held at 224) until user clicks OFF
```

### 6.4 Optional: Manual CHARGE Mode

`--start-mode manual` flag:
- Server does **not** push `startRoasting`.
- User clicks CHARGE in ArtisanZ manually (ideally within a few seconds of the first `getData` response).
- The server's `sim_t` is anchored to the first `getData` request after server start, same as auto mode. The server cannot detect Artisan's `qmc.flagstart` state — it just doesn't push the start event.

Default is `auto` (server pushes CHARGE) — recommended for fresh roasts. Use `manual` when reproducing / replaying / debugging without an automatic CHARGE event.

---

## 7. ArtisanZ UI Configuration

The user configures ArtisanZ once. The steps are:

1. Open ArtisanZ.
2. Menu `Config → Device...` (or equivalent in localized version).
3. Select the `WebSocket` device tab.
4. Fill in:
   - `Host`: `127.0.0.1`
   - `Port`: `80`
   - `Path`: `WebSocket`
   - `Request data command`: `getData`
   - Channel 0 — Node: **`BT`** (note the swap; see §6.2)
   - Channel 0 — Mode: `C` (or `F`, matching desired unit)
   - Channel 1 — Node: **`ET`**
   - Channel 1 — Mode: `C`
   - Channels 2-9: leave empty
5. Save.
6. **Restart ArtisanZ** (settings are read at startup).

---

## 8. Error Handling & Edge Cases

### 8.1 Time Model

```python
class ServerState:
    sim_t_ms: float = 0.0       # simulated time, advances only on request
    last_request_ms: float = 0.0
    frozen: bool = True         # true until first request

    def advance(self) -> float:
        now = time.monotonic()
        if self.frozen:
            self.frozen = False
            self.last_request_ms = now
            return 0.0
        elapsed_ms = (now - self.last_request_ms) * 1000
        if elapsed_ms > 30_000:           # long pause → freeze
            self.frozen = True
            return self.sim_t_ms
        self.sim_t_ms += min(elapsed_ms, 3000)  # cap at 3s to avoid jumps
        self.last_request_ms = now
        return self.sim_t_ms
```

- `sim_t` advances **only on incoming requests** — Artisan pausing ON doesn't advance time.
- Long pauses (>30s) freeze `sim_t` to avoid playing "catch up" when Artisan resumes.
- `time.monotonic()` (not `time.time()`) — immune to wall-clock adjustments.

### 8.2 Connection Errors

| Situation | Behavior |
|---|---|
| Port 80 in use | `OSError: [Errno 48]`. Auto-fallback to 8080 with prominent warning. User must update ArtisanZ Port field. |
| Bind to port <1024 without root (Linux) | Error message: "use `--port 8080`". (macOS allows non-root <1024.) |
| Client sends malformed JSON | `json.JSONDecodeError` caught; log warning; do not disconnect. |
| Client disconnects mid-roast | `ConnectionClosed` caught; log info; server keeps running. `sim_t` and `fired` events are preserved. |
| Same client reconnects | State preserved: events do not refire, `sim_t` does not reset. |
| Unknown `command` value | Log debug; do not respond; do not error. |
| Request timeout | Server responds within 50ms; ArtisanZ's 0.5s timeout is generous. |

### 8.3 Data Errors

| Situation | Behavior |
|---|---|
| `t < 0` (custom spec with non-zero pre-heat period) | Clamp `t` to 0; return CHARGE values (BT=180, ET=190). |
| `t > 780s` (past DROP) | Hold at DROP values (BT=218, ET=224). |
| Noise pushes temperature < 0 or > 500 | Clamp to `[0, 500]`. |
| RoR negative in charge dip | Real behavior; do not clamp. `charge_target.predict()` returns None for `RoR <= 0` (see `charge_manager.py:75`). |
| NaN/Inf in profile | Validated at startup; `ValueError` exits before opening the server. |
| `json.dumps(float('nan'))` would crash | All numeric outputs are `round()`-ed to 2 decimals first. |

### 8.4 State Persistence

Server does **not** persist any state. Restart = new roast. ArtisanZ's existing curve is unaffected (the user must `Clear` it manually if they want a clean slate).

### 8.5 Logging

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
```

- `DEBUG`: per-request response (verbose, 0.5/s, off by default).
- `INFO`: connection, disconnect, event fired, server start/stop.
- `WARNING`: port conflict, JSON parse error, t freeze.
- `ERROR`: unhandled exceptions.
- `CRITICAL`: profile validation failure.

### 8.6 Resources & Exit

- `Ctrl-C` (`SIGINT`): close server, flush logs, exit 0.
- Unhandled exception: log traceback, exit 1.
- Server never auto-shuts-down on its own (always listening until user kills it).
- Post-DROP behavior: server continues responding to `getData` (held at DROP values) until user clicks Artisan OFF.

---

## 9. Implementation Plan

### 9.1 File Layout

```
src/dev_simulator/
├── __init__.py                       # empty
├── artisan_simulator.py              # CLI entry, asyncio main
├── profile.py                        # RoastSpec + generate_profile()
├── event_scheduler.py                # EventScheduler
├── ws_server.py                      # AsyncServer
└── README.md                         # usage + ArtisanZ config + troubleshooting

src/test/dev_simulator/
├── conftest.py                       # pytest fixtures; no __init__.py to avoid shadowing src/dev_simulator
├── test_profile.py                   # profile generation unit tests
├── test_event_scheduler.py           # event scheduling unit tests
└── test_ws_server.py                 # integration tests (websockets client)
```

### 9.2 Run / Test

```bash
# Run simulator
cd src
python3 -m dev_simulator.artisan_simulator [args...]

# Run tests
cd src
python3 -m pytest test/dev_simulator/ -q
```

### 9.3 Dependencies

| Package | Status |
|---|---|
| `websockets` | already in project (used by `wsport.py`) |
| `numpy` | already in project |
| `pytest` | already in project |
| `pytest-asyncio` | in `requirements-dev.txt` but pinned to **1.3.0** (2021). Modern async fixtures require 0.21+. Unpin or upgrade to `>=0.23` for `@pytest.mark.asyncio` + `mode="auto"` support. |

**No new runtime dependencies. Test dependency `pytest-asyncio` needs version bump.**

### 9.4 Implementation Phases

| Phase | Output | Test | Estimate |
|:---:|---|---|:---:|
| 0 | package `__init__.py` + test directory scaffolding (no test package `__init__.py`) | — | 5 min |
| 1 | `profile.py`: `RoastSpec` + `generate_profile()` | `test_profile.py` | 30 min |
| 2 | `event_scheduler.py`: `EventScheduler` | `test_event_scheduler.py` | 20 min |
| 3 | `ws_server.py`: `AsyncServer` with time model | `test_ws_server.py` | 45 min |
| 4 | `artisan_simulator.py`: argparse + main | manual E2E | 30 min |
| 5 | `README.md` | — | 20 min |

Total MVP: ~2.5h. Minimum viable (skipping README polish and full noise models): ~1.5h.

### 9.5 Public API (key types)

```python
# profile.py
@dataclass(frozen=True)
class RoastSpec:
    # Per-node anchor parameters (time in seconds, temperatures in °C)
    charge_t: float = 0.0
    charge_bt: float = 180.0
    charge_et: float = 190.0
    turn_t: float = 90.0
    turn_bt: float = 95.0
    turn_et: float = 180.0
    dry_t: float = 300.0
    dry_bt: float = 152.0
    dry_et: float = 170.0
    fcs_t: float = 570.0
    fcs_bt: float = 193.0
    fcs_et: float = 205.0
    fce_t: float = 645.0
    fce_bt: float = 202.0
    fce_et: float = 212.0
    scs_t: float = 765.0
    scs_bt: float = 215.0
    scs_et: float = 222.0
    drop_t: float = 780.0
    drop_bt: float = 218.0
    drop_et: float = 224.0
    # Generation parameters
    sample_hz: int = 10
    noise_std: float = 0.3
    noise_model: Literal["gaussian", "ar1", "none"] = "ar1"

def generate_profile(spec: RoastSpec) -> dict: ...

# event_scheduler.py
class EventScheduler:
    def __init__(self, events: list[tuple[float, dict]]) -> None: ...
    async def fire_due(self, t: float, send: Callable[[dict], Awaitable[None]]) -> list[dict]: ...
    def reset(self) -> None: ...

# ws_server.py
class AsyncServer:
    def __init__(self, profile: dict, scheduler: EventScheduler,
                 host: str = "127.0.0.1", port: int = 80,
                 noise_model: str = "ar1", noise_std: float = 0.3) -> None: ...
    async def handle(self, ws) -> None: ...
    async def run(self) -> None: ...

# artisan_simulator.py
def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...
def build_spec(args) -> RoastSpec: ...
def main() -> None: ...
```

### 9.6 CLI Surface

```
python3 -m dev_simulator.artisan_simulator [--preset {light,medium,dark,custom}]
                                            [--host 127.0.0.1] [--port 80] [--path WebSocket]
                                            [--start-mode {auto,manual}]
                                            [--noise-std 0.3] [--noise-model {gaussian,ar1,none}]
                                            [--log-level {debug,info,warning,error}]
                                            [--charge-bt 180] [--turn-bt 95] [--dry-bt 152]
                                            [--fcs-bt 193] [--fce-bt 202] [--scs-bt 215]
                                            [--drop-bt 218]
                                            [--turn-t 90] [--dry-t 300] [--fcs-t 570]
                                            [--fce-t 645] [--scs-t 765] [--drop-t 780]
```

`--preset`:
- `medium` (default): the values in §5.1
- `light`: shorter roast, lower DROP
- `dark`: longer Maillard, higher DROP
- `custom`: ignore preset, use all CLI overrides

---

## 10. Testing Strategy

### 10.1 Unit Tests

`test_profile.py`:
- `test_charge_dip_monotonic_decrease` — BT strictly decreases 0→90s
- `test_after_turn_monotonic_increase` — BT strictly increases 90s onward
- `test_event_times_match_spec` — DRY/FCs/FCe/SCs/DROP times match `RoastSpec`
- `test_no_nan_inf` — no NaN/Inf in any value
- `test_clamping_within_bounds` — all values in [0, 500]
- `test_noise_model_ar1_correlation` — adjacent samples correlated, not IID
- `test_noise_model_none_is_zero` — `none` model produces exact curve

`test_event_scheduler.py`:
- `test_fire_at_exact_time` — fires when `t >= event_t`
- `test_skip_already_fired` — second call does not refire
- `test_dont_fire_early` — `t < event_t` → no fire
- `test_reconnect_does_not_refire` — fresh EventScheduler state, then reconnect
- `test_multiple_events_same_t` — fired in order, 50ms apart

### 10.2 Integration Tests

`test_ws_server.py` (uses `pytest-asyncio` + `websockets.connect`):
- `test_handshake_and_get_data` — connect, send `getData`, receive valid response
- `test_id_echo` — response `id` matches request `id`
- `test_event_push_sequence` — drive `sim_t` manually, verify push messages
- `test_disconnect_keepalive` — disconnect, reconnect, server still works
- `test_freeze_on_long_pause` — wait > 30s, verify `sim_t` doesn't advance past last value
- `test_time_advance_with_request` — multiple requests, `sim_t` advances correctly
- `test_data_clamps_extreme_noise` — high σ + many samples, all in [0, 500]

### 10.3 Manual E2E Checklist (in README)

1. Start simulator; confirm log line "server listening on ws://127.0.0.1:80/WebSocket"
2. Open ArtisanZ (already configured for WebSocket device)
3. Click ON; confirm first `getData` response arrives and ArtisanZ begins drawing
4. Confirm `markCHARGE` event fires at t=0
5. Watch curve; confirm BT/ET shapes match §5
6. Confirm DRY/FCs/FCe/SCs/DROP events fire at correct times
7. Click OFF; confirm ArtisanZ stops drawing
8. Click ON again; confirm server resumes from where it left off (no event refire)
9. `Ctrl-C` server; confirm clean shutdown
10. Restart server, repeat — fresh `sim_t=0`, fresh events

---

## 11. Open Questions / Future Work

- **Start-mode manual detection**: server cannot detect Artisan's `qmc.flagstart`; using first request as t=0 is a heuristic. Could be improved by sending a no-op `getData` ping and waiting for Artisan's response, but this adds complexity.
- **Extra devices (2-9 channels)**: out of scope. RoR delta (channel 2) and ET-BT gap (channel 3) could be added later.
- **Bidirectional commands**: Artisan can send custom slider/button actions. We accept and log them but don't act on them. Could echo back `setBurnerCapacity` events to test Artisan's slider sync.
- **Compression**: `websockets` library supports `deflate`; matches ArtisanZ's `wsport` default.
- **TLS**: not in scope; would need a self-signed cert + ArtisanZ TLS config.
- **Performance under high load**: 0.5 req/s is trivial. No need to optimize.
- **Charge target specific tuning**: real-world testing may reveal that the FCe→SCs rate of +13°C/min (or +6.5 with our 2-min extension) is still too fast/slow. The CLI flags allow per-segment tuning.

---

## 12. References

- `src/artisanlib/simulator.py:32-149` — `Simulator` class, profile interpolation contract
- `src/artisanlib/canvas.py:19950-20125` — `SampleThread`, sampling loop
- `src/artisanlib/canvas.py:19965-19975` — `sample_main_device()` integration with simulator
- `src/artisanlib/comm.py:1904-1974` — `WSextractData` + `WSread` (the swap trap)
- `src/artisanlib/wsport.py:41-406` — `wsport` client class, protocol reference
- `src/artisanlib/wsport.py:86-105` — protocol constants (node names, command names, event types)
- `src/artisanlib/main.py:27865-27929` — `simulate()` action (Tools → Simulator)
- `src/artisanlib/charge_manager.py:67-91` — `predict()` (consumes BT/RoR)
- `src/artisanlib/charge_manager.py:93-192` — `evaluate_readiness` (status logic)
- `src/test/unitary/artisanlib/test_wsport.py:24-56` — `mock_application_window` fixture
- `src/test/unitary/artisanlib/test_atypes.py:140-174` — sample profile dict pattern
