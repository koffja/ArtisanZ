# ArtisanZ Temperature Simulator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone WebSocket server that feeds synthetic BT/ET roast curves to ArtisanZ for testing the charge_target feature without physical hardware.

**Architecture:** A standalone Python package (`src/dev_simulator/`) generates a 7-node parameterized roast profile, reuses the existing `Simulator` class for interpolation, and serves temperature data over WebSocket to ArtisanZ. Events (CHARGE, DRY, FCs, FCe, SCs, DROP) are auto-pushed at configured times.

**Tech Stack:** Python 3.12+, `websockets` (already in project), `numpy` (already in project), `pytest` + `pytest-asyncio` (needs upgrade from 1.3.0 to >=0.23)

**Design Spec:** `docs/superpowers/specs/2026-06-07-artisan-temperature-simulator-design.md`

---

## File Structure

```
src/dev_simulator/
├── __init__.py
├── profile.py
├── event_scheduler.py
├── ws_server.py
└── artisan_simulator.py

src/test/dev_simulator/
├── conftest.py
├── test_profile.py
├── test_event_scheduler.py
└── test_ws_server.py
```

> **No `__init__.py` in `src/test/dev_simulator/`.** If present, pytest registers
> `test/dev_simulator/` as the `dev_simulator` package in `sys.modules`, shadowing
> `src/dev_simulator/` and causing `ModuleNotFoundError` for all source imports.

## Critical: Simulator class contract

The existing `Simulator` at `src/artisanlib/simulator.py`:
- Constructor: `__init__(self, mode:str, profile:dict[str, Any]|None = None)`
- Profile dict keys: `timex` (ms), `temp1` (ET), `temp2` (BT), `mode` ("C")
- `read(self, tx:float) -> tuple[float, float]` returns `(et, bt)` — tx in MILLISECONDS
- `removeEmptyPrefix()` strips leading -1 values and shifts timex to start at 0
- When mode="C", profile temps are used as-is; when mode differs, conversion is applied

---

## Task 0: Upgrade pytest-asyncio and scaffold directories

**Files:**
- Modify: `src/requirements-dev.txt`
- Create: `src/dev_simulator/__init__.py` (empty)
- Create: `src/test/dev_simulator/conftest.py`

> Do **not** create `src/test/dev_simulator/__init__.py` — see note in File Structure above.

- [x] **Step 1: Upgrade pytest-asyncio**

Change `pytest-asyncio==1.3.0` to `pytest-asyncio>=0.23,<1` in `src/requirements-dev.txt`. Then run:
```bash
cd src && pip install 'pytest-asyncio>=0.23,<1'
```

- [x] **Step 2: Create scaffolding**
```bash
mkdir -p src/dev_simulator src/test/dev_simulator
touch src/dev_simulator/__init__.py
```

- [x] **Step 3: Create conftest.py**

Create `src/test/dev_simulator/conftest.py`:
```python
import pytest
from dev_simulator.profile import RoastSpec


@pytest.fixture
def default_spec() -> RoastSpec:
    return RoastSpec()


@pytest.fixture
def no_noise_spec() -> RoastSpec:
    return RoastSpec(noise_model="none", noise_std=0.0)
```

- [x] **Step 4: Commit**
```bash
git add src/requirements-dev.txt src/dev_simulator/__init__.py src/test/dev_simulator/conftest.py
git commit -m "chore: scaffold dev_simulator package and upgrade pytest-asyncio"
```

---

## Task 1: profile.py — RoastSpec and generate_profile

**Files:**
- Create: `src/dev_simulator/profile.py`
- Create: `src/test/dev_simulator/test_profile.py`

**Spec reference:** §5 (Curve Model), §9.5 (RoastSpec API)

- [x] **Step 1: Write failing tests for RoastSpec and generate_profile**

Create `src/test/dev_simulator/test_profile.py` with tests from design spec §10.1:
- `test_default_values` — all 21 fields match spec §5.1 defaults
- `test_frozen` — raises AttributeError on assignment
- `test_profile_has_required_keys` — timex, temp1, temp2, mode
- `test_profile_length` — 10Hz × 780s + 1 = 7801 points
- `test_no_nan_inf` — no NaN/Inf in any array
- `test_charge_dip_monotonic_decrease` — BT strictly decreases 0→90s
- `test_after_turn_monotonic_increase` — BT increases 90s→780s
- `test_event_temperatures_at_nodes` — BT values at 7 anchor points match spec ±0.01
- `test_noise_none_returns_zeros` — noise model "none" returns all zeros
- `test_noise_gaussian_nonzero` — gaussian produces non-zero values
- `test_noise_ar1_correlation` — AR(1) adjacent diffs < IID diffs × 0.5

Run: `cd src && python3 -m pytest test/dev_simulator/test_profile.py -v`
Expected: FAIL (ModuleNotFoundError)

- [x] **Step 2: Implement profile.py**

Create `src/dev_simulator/profile.py` with:
1. `RoastSpec` frozen dataclass — 21 fields (7 nodes × 3: t/bt/et) + sample_hz/noise_std/noise_model
   - **IMPORTANT:** Each field on its own line. `a, b, c: float = (x, y, z)` is INVALID Python syntax.
2. `_cosine_ease(t, t0, t1, v0, v1)` — cosine ease-in-out: `(1 - cos(π·frac))/2`
3. `apply_noise(n, model, std, alpha=0.85)` — gaussian/ar1/none noise generator
   - AR(1): `x[t+1] = 0.85·x[t] + N(0, σ²·(1-α²))`
4. `generate_profile(spec) -> dict` — interpolate 7 nodes → 10Hz profile dict
   - timex in MILLISECONDS (simulator contract requires ms)
   - temp1 = ET, temp2 = BT
   - Clamp noise-perturbed values to [0, 500]
   - Return `{"timex": [...ms], "temp1": [...ET], "temp2": [...BT], "mode": "C"}`

Run: `cd src && python3 -m pytest test/dev_simulator/test_profile.py -v`
Expected: ALL PASS

- [x] **Step 3: Commit**
```bash
git add src/dev_simulator/profile.py src/test/dev_simulator/test_profile.py
git commit -m "feat(dev-simulator): add RoastSpec and generate_profile with cosine interpolation"
```

---

## Task 2: event_scheduler.py — EventScheduler

**Files:**
- Create: `src/dev_simulator/event_scheduler.py`
- Create: `src/test/dev_simulator/test_event_scheduler.py`

**Spec reference:** §5.5 (Event Schedule), §8.1 (Time Model)

- [x] **Step 1: Write failing tests for EventScheduler**

Create `src/test/dev_simulator/test_event_scheduler.py` with tests from §10.1:
- `test_fire_at_exact_time` — t=300 fires CHARGE (t=0) + DRY (t=300)
- `test_dont_fire_early` — t=0 fires only CHARGE
- `test_skip_already_fired` — second call at same t doesn't refire
- `test_fire_all` — t=780 fires all 6 events
- `test_manual_mode_skips_charge` — manual mode suppresses startRoasting
- `test_reset` — reset() allows all events to fire again

Use `asyncio.get_event_loop().run_until_complete()` for sync test wrappers.

Run: `cd src && python3 -m pytest test/dev_simulator/test_event_scheduler.py -v`
Expected: FAIL (ModuleNotFoundError)

- [x] **Step 2: Implement event_scheduler.py**

Create `src/dev_simulator/event_scheduler.py` with:
1. `EventScheduler(events: list[tuple[float, dict]], start_mode: str = "auto")`
2. `async fire_due(t: float, send: Callable[[dict], Awaitable[None]]) -> list[dict]`
   - Iterate events sorted by time, fire all with event_t <= t that haven't been fired
   - Track `fired: set[int]` for exactly-once delivery
   - In manual mode, skip `startRoasting` event (mark as fired without sending)
   - Log each fired event at INFO level
3. `reset()` — clear fired set

Run: `cd src && python3 -m pytest test/dev_simulator/test_event_scheduler.py -v`
Expected: ALL PASS

- [x] **Step 3: Commit**
```bash
git add src/dev_simulator/event_scheduler.py src/test/dev_simulator/test_event_scheduler.py
git commit -m "feat(dev-simulator): add EventScheduler with fire-once and manual mode"
```

---

## Task 3: ws_server.py — AsyncServer with time model

**Files:**
- Create: `src/dev_simulator/ws_server.py`
- Create: `src/test/dev_simulator/test_ws_server.py`

**Spec reference:** §6 (WebSocket Protocol), §8 (Error Handling), §8.1 (Time Model)

- [x] **Step 1: Write failing tests for AsyncServer**

Create `src/test/dev_simulator/test_ws_server.py` with integration tests from §10.2:
- `test_id_echo` — response id matches request id
- `test_event_push_on_first_request` — startRoasting pushed on first getData
- `test_bt_et_values` — BT≈180, ET≈190 at t=0 (within 1°C tolerance)
- `test_disconnect_reconnect` — server survives disconnect; second connection works
- `test_malformed_json` — server doesn't crash; subsequent valid request works

Use `pytest-asyncio` with `@pytest.mark.asyncio`, `websockets.connect` as test client.
Use `unused_tcp_port_factory` fixture for ephemeral port.
Use `RoastSpec(noise_model="none")` for deterministic values.

Run: `cd src && python3 -m pytest test/dev_simulator/test_ws_server.py -v`
Expected: FAIL (ModuleNotFoundError)

- [x] **Step 2: Implement ws_server.py**

Create `src/dev_simulator/ws_server.py` with three components:

**ServerState** — time model per spec §8.1:
```python
class ServerState:
    sim_t_ms: float = 0.0
    last_request_monotonic: float = 0.0
    frozen: bool = True

    def advance(self) -> float:
        now = time.monotonic()
        if self.frozen:
            self.frozen = False
            self.last_request_monotonic = now
            return 0.0
        elapsed_ms = (now - self.last_request_monotonic) * 1000.0
        if elapsed_ms > 30_000:
            self.frozen = True
            return self.sim_t_ms
        self.sim_t_ms += min(elapsed_ms, 3000.0)
        self.last_request_monotonic = now
        return self.sim_t_ms
```

**AsyncServer** — WebSocket handler:
1. `__init__(profile, scheduler, host, port, noise_model, noise_std)` — build interpolation arrays from profile
2. `_interp(tx_ms) -> (et, bt)` — binary search + linear interpolation (own impl, not numpy, to avoid importing artisanlib at runtime)
3. `_add_noise(val) -> float` — gaussian/ar1/none noise per sample
4. `async handle(websocket)` — per-connection handler:
   - Parse JSON request
   - If command != "getData": skip
   - Advance sim_t via ServerState
   - Check EventScheduler.fire_due(sim_t_s, send_fn) — push events
   - Interpolate ET/BT, add noise, clamp to [0,500], round to 2dp
   - Send response: `{"id": msg_id, "data": {"BT": bt, "ET": et}}`
5. `async run()` — start `websockets.server.serve(handle, host, port)`, run forever
6. Error handling: catch json.JSONDecodeError (log, continue), ConnectionClosed (log), Exception (log)

Run: `cd src && python3 -m pytest test/dev_simulator/test_ws_server.py -v`
Expected: ALL PASS

- [x] **Step 3: Commit**
```bash
git add src/dev_simulator/ws_server.py src/test/dev_simulator/test_ws_server.py
git commit -m "feat(dev-simulator): add AsyncServer with time model and WebSocket protocol"
```

---

## Task 4: artisan_simulator.py — CLI entry point

**Files:**
- Create: `src/dev_simulator/artisan_simulator.py`

**Spec reference:** §9.6 (CLI Surface), §8.5 (Logging), §8.6 (Resources & Exit)

- [x] **Step 1: Implement CLI entry point**

Create `src/dev_simulator/artisan_simulator.py` with:
1. `parse_args(argv) -> Namespace` — argparse with all flags from spec §9.6:
   - `--preset {light,medium,dark,custom}` (default: medium)
   - `--host` (default: 127.0.0.1), `--port` (default: 80), `--path` (default: WebSocket)
   - `--start-mode {auto,manual}` (default: auto)
   - `--noise-std` (default: 0.3), `--noise-model {gaussian,ar1,none}` (default: ar1)
   - `--log-level {debug,info,warning,error}` (default: info)
   - `--charge-bt`, `--turn-bt`, `--dry-bt`, `--fcs-bt`, `--fce-bt`, `--scs-bt`, `--drop-bt`
   - `--charge-t`, `--turn-t`, `--dry-t`, `--fcs-t`, `--fce-t`, `--scs-t`, `--drop-t`
2. `build_spec(args) -> RoastSpec` — merge preset defaults with CLI overrides
3. `main()` — configure logging per §8.5, build spec, generate profile, create EventScheduler, create AsyncServer, `asyncio.run(server.run())`
4. Port fallback: if port 80 fails with OSError, try port 8080 with warning
5. KeyboardInterrupt → clean shutdown, exit 0

Verify: `cd src && python3 -m dev_simulator.artisan_simulator --help`

- [x] **Step 2: Commit**
```bash
git add src/dev_simulator/artisan_simulator.py
git commit -m "feat(dev-simulator): add CLI entry point with argparse"
```

---

## Task 5: README.md

**Files:**
- Create: `src/dev_simulator/README.md`

**Spec reference:** §3 (User Scenario), §7 (UI Configuration), §10.3 (Manual E2E Checklist)

- [x] **Step 1: Write README**

Create `src/dev_simulator/README.md` covering:
1. What it is — one paragraph
2. Quick Start — 3 steps: install deps, run simulator, configure ArtisanZ
3. ArtisanZ WebSocket Configuration — step-by-step per spec §7
4. Channel Mapping Warning — the swap trap from §6.2 (prominent callout)
5. CLI Reference — all flags from §9.6
6. Manual E2E Checklist — 10 steps from §10.3
7. Troubleshooting — port conflicts, connection issues

- [ ] **Step 2: Commit**
```bash
git add src/dev_simulator/README.md
git commit -m "docs(dev-simulator): add usage guide and ArtisanZ configuration instructions"
```

Pending explicit user request to commit; `AGENTS.md` forbids committing without an explicit request.

---

## Self-Review Checklist

Before marking this plan complete, verify:

- [x] Spec coverage: Every section in the design spec has a corresponding task
  - §5 Curve Model → Task 1
  - §5.5 Event Schedule → Task 2
  - §6 WebSocket Protocol → Task 3
  - §8 Error Handling → Task 3 (ws_server) + Task 4 (CLI)
  - §9.4 Phases → Tasks 0-5
  - §10 Testing → Tasks 1-3
- [x] No placeholders: No TBD, TODO, "implement later", "similar to above"
- [x] Type consistency: RoastSpec fields match between profile.py and artisan_simulator.py
- [x] Profile dict format: `timex` in ms, `temp1`=ET, `temp2`=BT, `mode`="C"
- [x] Simulator.read() contract: tx in ms, returns (et, bt)
- [x] WebSocket channel swap: data keys are "BT" and "ET" (not "temp1"/"temp2")
- [x] Event messages match spec §5.5 exactly
