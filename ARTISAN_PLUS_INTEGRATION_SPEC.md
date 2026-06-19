# Artisan ↔ External Platform Integration Spec

> **Type**: AI-readable technical brief for driving downstream planning/implementation agents.
> **Repo**: `/Users/chengzhe/Projects/ArtisanZ` (branch `ArtisanZ`; upstream `artisan-roaster-scope/artisan`).
> **Audience**: AI agents performing reference-server design, ingestion-pipeline implementation, and reverse-engineering validation.
> **Reading guide**: §1–4 are REFERENCE (do not re-derive). §5–7 are DECISION + TASK templates (act on them). §8 is ACCEPTANCE CRITERIA. Appendix A is the canonical schema.

---

## 0. Mission

Build a coffee supply-chain platform that ingests data from Artisan (open-source PyQt6 coffee-roasting desktop app). Two valid end-states:

- **E1 Ingestion-only**: read Artisan's local exports (files / live events) into our platform.
- **E2 Plus-compatible**: wire-compatible drop-in replacement for proprietary `artisan.plus` cloud so unmodified Artisan clients sync to us.

**Hard constraint**: do not fork Artisan unless absolutely required. Treat it as a black box with documented hooks.

---

## 1. Architecture Reference (read-only)

### 1.1 Plus module layout

Location: `src/plus/` — independent sub-package, 17 files, ~13k LOC.

| File | Role |
|---|---|
| `config.py` | URLs, timeouts, runtime globals (`token`, `nickname`, `account_nr`) |
| `connection.py` | HTTP transport: auth closure, `sendData`/`getData`, gzip, 401 re-auth |
| `controller.py` | lifecycle: `connect`/`disconnect`/`toggle`, predicates `is_connected`/`is_on`/`is_synced` |
| `login.py` | login dialog (email/password) |
| `account.py` | local `account_id` ↔ running number (shared via filelock) |
| `sync.py` | sync record build + hash diff + `applyServerUpdates` |
| `queue.py` | SQLite persistent outbox + Worker thread |
| `roast.py` | upload payload assembly (`getRoast`/`getSyncRecord`/`getTemplate`) |
| `stock.py` | local mirror of coffees/blends/schedule (polls `/acoffees`) |
| `schedule.py` | scheduler window (4400 LOC, largest module) |
| `weight.py` | weighing state machines (Green/Roasted) |
| `blend.py` | custom local blend dialog |
| `notifications.py` | cloud → local notification bridge |
| `register.py` | `roastUUID` ↔ local `.alog` filepath map |
| `util.py` | ISO8601/epoch conversions, value sanitizers |
| `countries.py` | static country list |

Four-layer architecture:

| Layer | Modules | Role |
|---|---|---|
| Config | `config.py` | One mutable global module; all runtime state hangs off it |
| Transport | `connection.py` | All HTTP routes through one chokepoint; 401 handled here |
| Orchestration | `controller.py`, `sync.py`, `queue.py` | State machine + diff + persistent queue |
| Domain | `roast.py`, `stock.py`, `schedule.py`, `weight.py` | Build/receive concrete business objects |

### 1.2 Integration points in main app

| File | Lines | Role |
|---|---|---|
| `src/artisanlib/main.py` | 725–735 | `import plus.*` block |
| `src/artisanlib/main.py` | 1209–1284 | `def plus(self)`, `def subscription(self)` — toolbar handlers |
| `src/artisanlib/main.py` | 306, 13860 | profile-open hooks → `plus.sync.getUpdate`, `plus.stock.update` |
| `src/artisanlib/main.py` | 13358, 17335 | save hooks → `updateSyncRecordHashAndSync()` |
| `src/artisanlib/main.py` | 19749 | app startup → `plus.controller.start(self)` |
| `src/artisanlib/main.py` | 25413 | `plus.schedule.ScheduleWindow(...)` construction |
| `src/artisanlib/canvas.py` | 4314, 15502, 14460 | CHARGE/DROP → `addRoast()`; CHARGE → `sendLockSchedule()` |
| `src/artisanlib/roast_properties.py` | 5735 | roast properties save → `plus.queue.addRoast` |

> Note: the package directory is literally named `artisanlib` in the source tree (full path `src/artisanlib/`).

---

## 2. Wire Protocol (Plus)

### 2.1 Endpoints (`src/plus/config.py:44–55`)

```
api_base_url = https://artisan.plus/api/v1
auth_url             = /accounts/users/authenticate    [POST]   login
stock_url            = /acoffees                       [GET]    fetch stock
roast_url            = /aroast                         [POST]   upsert roast
GET /aroast/{uuid}?modified_at={ms_epoch}             [GET]    fetch one roast
lock_schedule_url    = /aschedule/lock?today=YYYY-MM-DD [POST]  lock today's schedule
notifications_url    = /notifications?machine={name}    [GET]    fetch notifications
```

**Local-dev override** (critical!): `config.py:40` contains a commented-out line
`api_base_url = 'https://localhost:62602/api/v1'`. Toggling this is the documented mechanism for running a Plus-compatible server locally.

Web UI URLs (browser only, not API): `https://artisan.plus/{register,resetPassword,stores;id=,coffees;id=,blends;id=,roasts;id=}`.

### 2.2 Authentication (`connection.py:154–355`)

**Request**:
```http
POST /api/v1/accounts/users/authenticate
Content-Type: application/json; charset=utf-8

{"email": "<user@example.com>", "password": "<plain passwd>"}
```

**Response** (success):
```json
{
  "success": true,
  "result": {
    "user": {
      "token": "<opaque string>",
      "nickname": "<str>",
      "language": "en",
      "user_id": "<uuid>",
      "readonly": false,
      "account": {
        "_id": "<mongo id>",
        "subscription": "PRO|HOME|HOME TRIAL",
        "paidUntil": "2025-12-31T00:00:00.000Z",
        "limit": {"rlimit": <kg quota int>, "rused": <kg used int>}
      }
    }
  },
  "notifications": {"unqualified": <int>, "machines": ["<machine name>"]},
  "ol": {"rlimit": <int>, "rused": <int>},
  "pu": "<paidUntil ISO8601>"
}
```

**Client state post-auth**:
- `config.token = result.user.token` (QSemaphore-protected)
- `config.account_nr = account.setAccount(result.user.account._id)`
- Password stored in OS keyring (service name `artisan.plus`); fallback: Fernet-encrypted in-memory closure.
- Subscription gate: if `paidUntil` is more than 90 days (`config.expired_subscription_max_days`) in the past, client clears credentials and refuses.

**Failure codes**: `404` = wrong email, `401` = wrong password (per code comment in `connection.py:217`).

### 2.3 Request headers (`connection.py:357–396`)

| Header | Value | Notes |
|---|---|---|
| `User-Agent` | `Artisan/{__version__} ({os}; {os_version}; {os_arch})` | free-form |
| `Accept-Charset` | `utf-8` | |
| `Accept-Language` | `<locale>` (e.g. `zh-cn`) | from UI locale |
| `Accept-Encoding` | `deflate, compress, gzip` | never include `identity` |
| `Authorization` | `Bearer <token>` | if `authorized=True` |
| `Content-Type` | `application/json; charset=utf-8` | request bodies |
| `Idempotency-Key` | `<uuid4 hex>` | POST only |
| `Content-Encoding` | `gzip` | only if body > 500 bytes |

JSON encoding: `json.dumps(data, indent=None, separators=(',', ':'), ensure_ascii=False).encode('utf8')` — compact, non-ASCII passes through as UTF-8.

Timeouts (adaptive): connect 6s, read 12s baseline; on timeout read jumps to 30s, on success read decreases by 2s (floor 12s). SSL verify ON by default.

### 2.4 401 re-auth (`connection.py:433–458`)

On any authorized request returning 401: call `authentify()` once → sleep 300ms → reissue the same request exactly once with the fresh token. Do not loop.

---

## 3. Sync Semantics

### 3.1 Trigger matrix

**Upload (client → server)** — all funnel through `plus.queue.addRoast()` into the SQLite outbox except where noted:

| Trigger | File:line | Behaviour |
|---|---|---|
| User presses CHARGE button | `canvas.py:4314` | `addRoast()` |
| User presses DROP button | `canvas.py:15502` | `addRoast()` |
| User saves profile (manual or autosave) | `main.py:13358, 17335` | `updateSyncRecordHashAndSync()` (queues only if hash changed) |
| Roast Properties edit during recording | `roast_properties.py:5735` | `addRoast()` partial |
| User clicks Plus icon → turn sync on | `controller.py:94` | `addRoast(unsynced=True)` — full upload |
| User edits a Completed Item in Scheduler | `schedule.py:3553–3583` | direct `sendData` (no queue) |
| User weighs green coffee in Scheduler | `schedule.py:3146–3176` | direct `sendData` |
| User presses CHARGE (schedule lock) | `canvas.py:14460` | `sendLockSchedule()` |

**Download (server → client)**:

| Trigger | File:line | Behaviour |
|---|---|---|
| App startup with stored creds | `main.py:19749` | `controller.start` → `authentify` → `queue.start` → `stock.update` (2s later) |
| App raised from background | `main.py:306` | `plus.sync.getUpdate(roastUUID, curFile)` |
| App raised (no recording) | `main.py:311` | `plus.stock.update()` |
| Profile loaded from disk | `main.py:13860` | `QTimer.singleShot(100, plus.sync.sync)` |
| Scheduler opened/filtered | `schedule.py:2497` | `QTimer.singleShot(10, plus.stock.update_schedule)` |
| Auth success | `controller.py:323` | `QTimer.singleShot(2000, stock.update)` |

### 3.2 Delta sync (no ETag, no version)

- **Conflict resolver**: single field `modified_at` (ISO8601 string, ms resolution, UTC `Z` suffix). Last-write-wins.
- **Push diff** (`sync.py:291–394`): client caches SHA-256 of the last sync record; only changed keys are sent.
- **Pull protocol** (`sync.py:746–891`): `GET /aroast/{uuid}?modified_at={ms_epoch}` —
  - `200` = server newer → `applyServerUpdates(r)`
  - `204` = client newer → no-op
  - `404` = server deleted → local `delSync(uuid)`
- **Terminal conflict**: HTTP `409` — drop item, never retry (`queue.py:246–250`).

### 3.3 Outbox queue (`queue.py`)

| Constant | Value | Effect |
|---|---|---|
| `queue_start_delay` | 5 s | Worker startup wait |
| `queue_task_delay` | 2.0 s | Inter-task interval |
| `queue_retries` | 2 | Per-item retry budget |
| `queue_retry_delay` | 30 s | Retry back-off |
| `queue_discard_after` | 3 days | Drop stale items |
| `post_compression_threshold` | 500 bytes | gzip kicks in above this |

Storage: `persistqueue.SQLiteQueue` at `<appdata>/outbox`. Shared with ArtisanViewer (no extra lock).

Retry policy per response class:

| Response | Action |
|---|---|
| 2xx | update sync cache with server `modified_at`; recompute hash; emit `replySignal` |
| 401 | re-auth + retry once |
| 409 | drop, do not retry |
| other 4xx/5xx, timeout | retry up to `queue_retries`, delay `2 * queue_retry_delay` (60s) |
| ConnectionError | disconnect, keep queue running, wait 30s, retry on next cycle |

**Subset dedup** (`queue.py:384–405`): new item that is a subset (modulo `modified_at`) of the last queued item is silently dropped.

---

## 4. Data Export Surface (non-Plus paths)

For ingestion-only integrations that bypass the Plus protocol entirely.

### 4.1 File formats

| Format | Writer | Encoding | Sample |
|---|---|---|---|
| `.alog` (native) | `util.py:1002` `serialize()` | `repr(dict)` (Python literal, single line) | `src/test/data/profile1.alog` |
| `.json` | `main.py:14690` `exportJSON()` | compact JSON, UTF-8, non-ASCII passthrough | `src/test/data/profile1.json` |
| `.csv` | `util.py:1137` `exportProfile2CSV()` | tab-separated, header rows for events + columns | — |
| `.xlsx` | `main.py:15048` `exportExcel()` + `productionExcelReport()` L22140 | openpyxl, two sheets (Profile + Production Report) | — |
| `.pdf` (chart) | `canvas.py:12498` etc. | matplotlib `FigureCanvasPdf` | — |
| `.pdf` (report) | `main.py:692–694` | QWebEngineView HTML→PDF | — |
| `.svg/.png/.jpeg` | matplotlib | — | — |
| Orbiter ROP | `orbiter.py` `saveOrbiterROP()` | Roastime vendor format | — |

**Canonical schema**: `src/artisanlib/atypes.py:128–336` `ProfileData` TypedDict, ~200 fields. Key groups:
- Timeseries: `timex[]`, `temp1[]` (ET), `temp2[]` (BT), `extradevices`, `extratimex[][]`, `extratemp1[][]`, `extratemp2[][]`
- Event indices: `timeindex[0..7]` = `[CHARGE, DRYe, FCs, FCe, SCs, SCe, DROP, COOL]` (-1=unset, 0=auto, >0=index into `timex`)
- Custom events: `specialevents[]`, `specialeventstype[]` (1=manual, 3=percentage), `specialeventsvalue[]`, `specialeventsStrings[]`
- Metadata: `title`, `beans`, `weight[3]`, `roastdate`, `roastisodate`, `roastepoch`, `roastUUID`, `operator`, `roastertype`, `mode`
- Computed: `computed: ComputedProfileInformation` (FCs/DROP temps, RoR, AUC, phase times, weight loss)

See Appendix A for the field index used by Plus sync.

### 4.2 MQTT (outbound via event scripting)

File: `mqttport.py` (class `mqttport`, paho-mqtt). Default `127.0.0.1:1883` TCP or `443` WS transport.

**No automatic outbound channel.** Outbound is triggered only when a user binds an event button/slider to IO Command action with `publish(<topic>, <data>)` — handler at `main.py:9691–9700`:

```python
elif c.startswith('publish'):
    args = c[len('publish'):]
    if args.startswith('(') and args.endswith(')'):
        comma_pos = args.index(',')
        topic = args[1:comma_pos]
        data  = eval(args[comma_pos+1:-1][:eval_limit])
        self.mqtt.publish(topic, data, self.qmc.device_logging)
```

The `data` argument is `eval()`-evaluated Python literal — must be JSON-serializable.

Runtime substitutions: `{BT}` (bean temp), `{ET}` (environment temp), `{t}` (seconds since CHARGE), `{BTB}`, `{ETB}`, `{WEIGHTin}`.

### 4.3 WebSocket — client mode (Artisan connects OUT)

File: `wsport.py` (class `wsport`). Default `ws://127.0.0.1:80/WebSocket`, `deflate` compression.

**Envelope** (`wsport.py:86–105`):
```json
{"id": <int>, "roasterID": <int>, "command": "getData", "data": {...}}
```

**Server → Artisan push messages**:
```json
{"pushMessage": "startRoasting"}
{"pushMessage": "endRoasting"}
{"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}            // DRY
{"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}    // FCs
{"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}          // FCe
{"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}   // SCs
{"pushMessage": "addEvent", "data": {"event": "secondCrackEndEvent"}}         // SCe
{"pushMessage": "setBurnerCapacity", "data": {"burnercapacity": 51}}
{"pushMessage": "setRoastingProcessName", "data": {"name": "..."}}
{"pushMessage": "setRoastingProcessFillWeight", "data": {"fillWeight": 12}}
```

**Artisan → server** via WebSocket Command (action 22) at `main.py:11224–11318`: `send(<json>)`, `read(<json>)`, `button(b)`, `sleep(s)`. Same `{BT}/{ET}/{t}` substitutions.

Reference impl: `src/dev_simulator/ws_server.py` is a working minimal server.

### 4.4 WebSocket — server mode (WebLCDs)

File: `weblcds.py`. aiohttp-based server, binds `0.0.0.0:8080` (configurable via `WebLCDsPort`). Classes: `WebView`, `WebLCDs`, `WebGreen`, `WebRoasted`.

**Pushed payload** (built in `canvas.py:4361–4384`):
```json
{"data": {"bt": "200", "et": "210", "time": "00:05:32"},
 "alert": {"text": "FCs reached", "title": "Notice", "timeout": 5}}
```
Rate-limited to ~30ms minimum interval; broadcast to all connected clients (WeakSet).

**Limitation**: streams only BT/ET/time + alerts. No profile data, no events. Suitable for live dashboards, not for ingestion.

### 4.5 Event-action scripting DSL

23 action types dispatched in `main.py:8993` `eventaction_internal()`:

```
0=None | 1=Serial | 2=CallProgram | 3=MultipleEvent | 4=Modbus | 5=DTA |
6=IO (Phidgets/Yocto/Shelly/MQTT — incl. publish) | 7=CallProg+Arg | 8–10=Hottop |
11=PID | 12=Fuji | 13=PWM | 14=VOUT | 15=S7 | 16–19=Aillio |
20=Artisan Command (alarm/notify/setweight/...) | 21=RC | 22=WebSocket | 23=Stepper
```

Users configure these via GUI (Config → Events). No programmatic Python subscription API.

**Not present** (verified by recursive grep): OSC, generic HTTP REST server (other than WebLCDs), Flask/BaseHTTPRequestHandler, programmable plugin API.

### 4.6 Device-side TCP listeners (informational only)

When Modbus-TCP or S7 device mode is enabled, Artisan opens outbound connections only (does not listen). Useless for ingestion.

---

## 5. Decision Matrix

| Need | Recommended path | Effort | Real-time? | Bidirectional? |
|---|---|---|---|---|
| Batch ingest of completed roasts | **Plan A** (file watcher) | Low | No | No |
| Live event stream (CHARGE/DRY/FCs/DROP) | **Plan B** (MQTT publish) | Low | Yes | No |
| Live dashboard of BT/ET | WebLCDs browser (§4.4) | Low | Yes | No |
| Cloud-side control of Artisan (remote start/stop) | **Plan C** (WebSocket server) | Medium | Yes | Yes |
| Full SaaS replacement of artisan.plus | **Plan D** (Plus-compatible server) | High | Yes (polled) | Yes |

**Default recommendation for a supply-chain platform**: Plan A + Plan B (A for historical curves, B for live milestones). Upgrade to Plan D only if seamless UX (zero user config in Artisan) is a product requirement.

---

## 6. Implementation Plans

### Plan A — File Directory Watcher (ingestion-only)

**Goal**: ingest every roast Artisan saves, with full temperature curves.

**User-side config** (one-time):
1. Artisan → Config → Autosave → enable autosave, target dir `~/ArtisanExports/`
2. Choose JSON format (recommended over `.alog` for cross-language parsing).

**Implementation tasks**:

- [ ] A1. Define internal roast schema (Postgres tables or JSON document store). Fields per Appendix A.
- [ ] A2. Build watcher service (Python `watchdog` / Node `chokidar` / Go `fsnotify`) on `~/ArtisanExports/`.
- [ ] A3. JSON parser → canonical roast record. Reference: `src/test/data/profile1.json`.
- [ ] A4. `.alog` parser fallback (Python `ast.literal_eval`, since format is `repr(dict)`).
- [ ] A5. Idempotency: dedupe on `roastUUID`. Treat `roastepoch` + `roastUUID` as the natural key.
- [ ] A6. POST parsed record to platform API `/v1/roasts`.
- [ ] A7. Retry queue (use platform's existing mechanism; mimicking Plus semantics — 2 retries, 30s back-off — is sufficient).
- [ ] A8. Optional: time-series storage for BT/ET curves (TimescaleDB / InfluxDB).

**MUST NOT**:
- Re-implement profile serialization — use the field names from `atypes.py:128` verbatim.
- Assume field presence — many fields are optional; treat missing as null.

**Verification**: round-trip a real `.alog` from `src/test/data/profile1.alog` through your parser and assert equality with the source dict on a defined subset of fields (curves, timeindex, weight, metadata).

### Plan B — MQTT Event Stream (live milestones)

**Goal**: stream CHARGE/DRY/FCs/FCe/SCs/SCe/DROP events to a broker in real time.

**User-side config** (per roast machine):
1. Artisan → Config → MQTT → set broker host/port (your EMQX/Mosquitto).
2. Artisan → Events → bind each milestone button to IO Command action with:
   ```
   publish("roaster/{ROASTER_ID}/charge", {"t": {t}, "BT": {BT}, "ET": {ET}, "weight_in": {WEIGHTin}})
   publish("roaster/{ROASTER_ID}/dry",    {"t": {t}, "BT": {BT}})
   publish("roaster/{ROASTER_ID}/fcs",    {"t": {t}, "BT": {BT}})
   publish("roaster/{ROASTER_ID}/fce",    {"t": {t}, "BT": {BT}})
   publish("roaster/{ROASTER_ID}/drop",   {"t": {t}, "BT": {BT}, "ET": {ET}})
   ```
   Replace `{ROASTER_ID}` with the machine's stable identifier.

**Implementation tasks**:

- [ ] B1. Deploy MQTT broker (EMQX recommended; Mosquitto for low-traffic).
- [ ] B2. Backend subscriber on topic `roaster/+/+` → forward to platform API.
- [ ] B3. Topic → event-type mapping (`charge` → `CHARGE`, etc.).
- [ ] B4. Correlate with Plan A's batch ingest: live event uses `roastUUID` if you add it to the payload (via custom field — see "Limitations" below).
- [ ] B5. Dashboard consumer for live roasts (SSE/WebSocket from platform → frontend).

**Limitations**:
- Event payloads contain only the snapshot at event time, not full curves. Pair with Plan A.
- No built-in `roastUUID` substitution. Workaround: have user include `"uuid": "<static-uuid-per-roaster>"` in each `publish` call, OR have backend correlate by roaster + active time window.

**Verification**: capture a real roast end-to-end; assert the platform received exactly 6 events (CHARGE/DRY/FCs/FCe/SCs+SCe optional/DROP) per roast in order.

### Plan C — WebSocket Server (bidirectional cloud control)

**Goal**: platform pushes work orders to Artisan; Artisan streams back live state.

**User-side config**:
1. Artisan → Config → WebSocket → set URL to `ws://your-server.example.com:80/ws`.
2. Enable `STARTonCHARGE` and `OFFonDROP` flags so server-initiated `startRoasting` / `endRoasting` actually trigger CHARGE/DROP.
3. Optional: bind event buttons with action 22 `send({...})` for richer telemetry.

**Implementation tasks**:

- [ ] C1. WebSocket server (Node `ws` / Python `websockets` / Go `gorilla`). Reference: `src/dev_simulator/ws_server.py`.
- [ ] C2. Implement message handlers per §4.3 envelope (`id`, `roasterID`, `command`, `data`, `pushMessage`).
- [ ] C3. Work-order dispatch: `{"pushMessage": "setRoastingProcessName", "data": {"name": "<batch id>"}}` → `{"pushMessage": "setRoastingProcessFillWeight", "data": {"fillWeight": <kg>}}` → `{"pushMessage": "startRoasting"}`.
- [ ] C4. Telemetry ingestion (Artisan-initiated `send` messages from event buttons).
- [ ] C5. Connection lifecycle: handle reconnect, heartbeat (Artisan does not send one — implement server-side timeout + reconnect grace).
- [ ] C6. Multi-tenant routing by `roasterID`.

**MUST NOT**:
- Deviate from the exact `pushMessage` enum strings — Artisan's parser is strict.
- Expect Artisan to authenticate — there is no auth in the WS protocol; rely on network isolation or a per-roaster secret in the URL path.

**Verification**: round-trip `startRoasting` → observe CHARGE event in Artisan → Artisan sends `endRoasting` from server → observe DROP.

### Plan D — Plus-Compatible Server (full drop-in)

**Goal**: unmodified Artisan (single config toggle) syncs to your platform as if it were `artisan.plus`.

**Critical config switch** (`src/plus/config.py:40`): change `api_base_url` to your domain. Two deployment options:
- D-fast: patch the source and ship a custom Artisan build.
- D-clean: transparent proxy — intercept DNS / use mitmproxy CA on user machines.

**Implementation tasks** (each endpoint is independently testable):

- [ ] D1. `POST /api/v1/accounts/users/authenticate` — accept `{email, password}`, return the §2.2 response envelope. Issue opaque tokens (JWT or random — Artisan does not validate format).
- [ ] D2. `POST /api/v1/aroast` — accept the §A.2 roast payload. Idempotent upsert on `roast_id`. Honor `Idempotency-Key` header. Apply `modified_at` last-write-wins. Return 409 only on a hard conflict you want the client to drop.
- [ ] D3. `GET /api/v1/aroast/{uuid}?modified_at={ms_epoch}` — return 200 with sync record (only `sync_record_attributes` keys + `roast_id` + `modified_at`), 204 if not newer, 404 if deleted.
- [ ] D4. `GET /api/v1/acoffees?today=YYYY-MM-DD[&lsrt={ms}]` — return stock JSON. With `lsrt`, return 204 if schedule unchanged since `lsrt`.
- [ ] D5. `POST /api/v1/aschedule/lock?today=YYYY-MM-DD` — body-less; record the lock; idempotent per (account, date).
- [ ] D6. `GET /api/v1/notifications?machine={name}` — return list of notification objects.
- [ ] D7. HTTP middleware: gzip decode, `Idempotency-Key` replay protection, `User-Agent` logging, Bearer auth.
- [ ] D8. Stock shape (`stock.py` consumer expects):
  ```json
  {
    "coffees": [...], "blends": [...], "replBlends": [...], "schedule": [...],
    "retrieved": <epoch>, "serverTime": <epoch>
  }
  ```
- [ ] D9. Value suppression round-trip — re-apply defaults for suppressed keys (zeros, 50, empty strings) per `roast.py:442–501` lists.
- [ ] D10. Outbox-compatible retry behavior — client will retry on 5xx/timeout; ensure your server is idempotent on `(roast_id, modified_at)`.

**MUST NOT**:
- Reject the `Idempotency-Key` header — Artisan adds it to every POST and expects 2xx on safe replay.
- Compress responses with anything other than `gzip`/`deflate`/`compress` (the `Accept-Encoding` client header excludes `identity` deliberately).
- Strip `Bearer ` prefix when reading `Authorization`.
- Use ETag/If-Match — protocol is timestamp-only.

**Verification**: capture real traffic via `mitmproxy --mode reverse:https://artisan.plus:443` to compare against your server's responses field-by-field.

---

## 7. Task Templates for Downstream AI Agents

When dispatching implementation sub-agents, structure the prompt as follows (replace placeholders before delegating):

```
TASK: Implement {Plan X, task Y}.
REFERENCE: Section {§} of ARTISAN_PLUS_INTEGRATION_SPEC.md.
INPUTS:
  - Schema: Appendix A.{sub}
  - Sample data: src/test/data/{file}
  - Artisan source-of-truth: {file:line}
EXPECTED OUTPUT:
  - {deliverable: file path, function signature, schema}
ACCEPTANCE:
  - {verbatim criterion from §8}
CONSTRAINTS:
  - MUST NOT {list from the relevant plan}
  - MUST follow field names from atypes.py:128 verbatim
  - Do not introduce type assertions or @ts-ignore equivalents
```

Suggested parallelizable work units (one sub-agent each, no shared state):

1. **Schema designer** — produce platform's internal roast data model from Appendix A.
2. **Plan A watcher** — file-ingestion service.
3. **Plan B broker+subscriber** — MQTT pipeline.
4. **Plan D stub server** — six endpoints with mock data, no business logic.
5. **Plan D business logic** — upsert semantics, delta resolution, stock fetcher.
6. **Test data curator** — convert `src/test/data/*.alog|*.json` into a fixture corpus.

---

## 8. Acceptance Criteria

For each plan, completion requires evidence (not assertion).

### Plan A
- [ ] Parser handles `src/test/data/profile1.alog` AND `profile1.json` without error.
- [ ] Round-trip: parsed dict contains expected `roastUUID`, `timex`, `temp1`, `temp2`, `timeindex`, `weight`, `operator`, `roastertype`.
- [ ] Idempotent re-ingest of the same file does not create duplicates.
- [ ] At least 95% field coverage against `ProfileData` schema (Appendix A.1).

### Plan B
- [ ] Live roast produces events on broker within 1s of the actual Artisan event.
- [ ] Event payloads contain valid numeric `BT/ET/t` (not template strings).
- [ ] Reconnect after broker restart does not lose subsequent events.

### Plan C
- [ ] Server-initiated `startRoasting` triggers Artisan CHARGE within 2s.
- [ ] Reconnect after WS disconnect is automatic and silent from user perspective.
- [ ] Multiple concurrent roasters route by `roasterID` without cross-talk.

### Plan D
- [ ] Artisan client configured against your server completes full login → CHARGE → DROP → save → reload cycle without errors.
- [ ] Reload after server push correctly applies `applyServerUpdates` (verify weight/color/notes changes appear in Artisan UI).
- [ ] No 5xx errors during normal operation; 409 returns only on genuine conflicts.
- [ ] `Idempotency-Key` replay returns the original 2xx, not a duplicate write.
- [ ] Outbox queue drains on reconnect after >24h offline (within `queue_discard_after=3d` window).

### Universal
- [ ] No use of `as any`, `@ts-ignore`, `eval()`, or untyped JSON in implementation code.
- [ ] LSP diagnostics clean on all new files.
- [ ] End-to-end test using real Artisan build (or mitmproxy capture) passes.

---

## Appendix A — Field Reference

### A.1 ProfileData key fields (from `src/artisanlib/atypes.py:128–336`)

```
Identification:   roastUUID, title, beans, operator, roasterdate, roastisodate, roastepoch
Machine:          roastertype, mode (C/F)
Weights:          weight[3]  (0=in, 1=out, 2=defects)
Timeseries:       timex[], temp1[] (ET), temp2[] (BT)
                  extradevices, extratimex[][], extratemp1[][], extratemp2[][]
Event indices:    timeindex[0..7] = [CHARGE, DRYe, FCs, FCe, SCs, SCe, DROP, COOL]
                  (-1 = unset, 0 = auto-detect, >0 = index into timex)
Custom events:    specialevents[], specialeventstype[] (1=manual, 3=percentage),
                  specialeventsvalue[], specialeventsStrings[]
Computed block:   computed.{FCs_temp, FCs_RoR, DROP_temp, DEV_time, DEV_ratio,
                          AUC, AUC_base, CM_ETD, CM_BTD, weight_loss, ...}
Plus linkage:     plus_sync_record_hash, s_item_id, s_item_date
```

### A.2 Roast upload payload (POST /aroast) — full schema

Built by `src/plus/roast.py:285–428`. Required fields for a "full" record (per `queue.py:374–375`): `date`, `amount`, `roast_id`. All other fields optional.

```json
{
  "roast_id":      "<32-char hex UUID>",
  "date":          "2018-10-12T12:55:12.999Z",
  "GMT_offset":    <seconds>,
  "amount":        <kg float, 4 dp>,
  "end_weight":    <kg float, 4 dp>,
  "defects_weight":<kg float, 4 dp>,
  "density_roasted": <g/L float, 1 dp>,
  "batch_number":  <int 0-65534>,
  "batch_prefix":  "<str <=50>",
  "batch_pos":     <int 0-255>,
  "label":         "<str <=255>",
  "machine":       "<str <=50>",
  "setup":         "<str <=50>",
  "roastersize":   <int 0-999>,
  "roasterheating":<int 0-999>,
  "whole_color":   <float 0-255, 1 dp>,
  "ground_color":  <float 0-255, 1 dp>,
  "color_system":  "<str <=25>",
  "moisture":      <% 0-100, 1 dp>,
  "temperature":   <°C ambient>,
  "pressure":      <hPa 800-1200>,
  "humidity":      <% 0-100>,
  "charge_temp_ET":<°C>, "charge_temp":<°C>, "TP_temp":<°C>,
  "DRY_temp":<°C>, "FCs_temp":<°C>, "FCe_temp":<°C>,
  "drop_temp":<°C>, "drop_temp_ET":<°C>,
  "TP_time":<s>, "DRY_time":<s>, "FCs_time":<s>,
  "FCe_time":<s>, "drop_time":<s>,
  "FCs_RoR":   <°C/min>,
  "DEV_time":   <s>,
  "DEV_ratio":  <% 0-100, 1 dp>,
  "AUC":        <int 0-10000>,
  "AUC_base":   <°C>,
  "CM_ETD":     <°C diff>,
  "CM_BTD":     <°C diff>,
  "BTU_ELEC":<BTU>, "BTU_LPG":<BTU>, "BTU_NG":<BTU>,
  "BTU_roast":<BTU>, "BTU_preheat":<BTU>, "BTU_bbp":<BTU>,
  "BTU_cooling":<BTU>, "BTU_batch":<BTU>,
  "CO2_roast":<kg>, "CO2_preheat":<kg>, "CO2_bbp":<kg>,
  "CO2_cooling":<kg>, "CO2_batch":<kg>,
  "location": "<store hr_id>" | null,
  "coffee":   "<coffee hr_id>" | null,
  "blend": {
    "label": "<str>",
    "ingredients": [
      {"coffee": "<hr_id>", "ratio": <float>, "ratio_num": <int>, "ratio_denom": <int>}
    ]
  } | null,
  "notes":         "<str <=1023>",
  "cupping_notes": "<str <=1023>",
  "cupping_score": <float>,
  "s_item_id":     "<schedule item uuid>" | null,
  "s_item_date":   "YYYY-MM-DD" | null,
  "template":      { ...same schema for background profile... } | null,
  "modified_at":   "2018-10-12T12:55:12.999Z"
}
```

### A.3 Value suppression rules (`roast.py:442–501`)

| Suppressed value | Field groups |
|---|---|
| `0` (bidirectional) | `density_roasted, batch_number, batch_pos, whole_color, ground_color, moisture` |
| `0` (push only) | `temperature, pressure, humidity, roastersize, roasterheating, BTU_*, CO2_*` |
| `50` | `cupping_score` |
| `""` (empty string) | `label, batch_prefix, color_system, machine, notes, cupping_notes` |
| Never suppressed | `roast_id, location, coffee, blend, amount, end_weight, defects_weight, s_item_id` |

### A.4 HTTP timeout adaptation (`connection.py:56–66`)

```
request_read_timeout       = 12 s   (baseline)
request_read_timeout_step  = 2 s    (decrement per success, floor at baseline)
request_read_timeout_max   = 30 s   (jump here on timeout)
```

### A.5 Local state files (under app data dir)

| File | Purpose | Concurrency |
|---|---|---|
| `cache` | stock mirror | QSemaphore |
| `completed` | completed roasts with weights/colors | QSemaphore |
| `prepared` / `hidden` | prepared / hidden schedule items | — |
| `uuids` | roastUUID → local .alog path | portalocker + QSemaphore |
| `account` | account_id ↔ local account_nr | portalocker (shared with ArtisanViewer) |
| `sync` | roastUUID → last-known modified_at | portalocker + QSemaphore (shared) |
| `outbox` | `persistqueue.SQLiteQueue` of pending POSTs | unprotected (shared) |

---

## Appendix B — Source-of-truth index

| Topic | File:line |
|---|---|
| Plus URLs | `src/plus/config.py:44–55` |
| Auth closure | `src/plus/connection.py:154–355` |
| Headers / gzip / Idempotency-Key | `src/plus/connection.py:357–396` |
| `sendData` / `getData` | `src/plus/connection.py:399–518` |
| Plus predicates | `src/plus/controller.py:42–67` |
| Outbox queue | `src/plus/queue.py:62–505` |
| Sync diff + applyServerUpdates | `src/plus/sync.py:291–891` |
| Roast payload assembly | `src/plus/roast.py:40–542` |
| Stock fetcher | `src/plus/stock.py:184–304` |
| `.alog` serializer | `src/artisanlib/util.py:1002` |
| `.alog` deserializer | `src/artisanlib/util.py:1009` (`ast.literal_eval`) |
| `.json` exporter | `src/artisanlib/main.py:14690` |
| ProfileData schema | `src/artisanlib/atypes.py:128–336` |
| MQTT client | `src/artisanlib/mqttport.py:39` |
| MQTT `publish` call site | `src/artisanlib/main.py:9691–9700` |
| WebSocket client | `src/artisanlib/wsport.py:41` |
| WebSocket server (WebLCDs) | `src/artisanlib/weblcds.py:36` |
| Event-action dispatcher | `src/artisanlib/main.py:8993` |
| Sample `.alog` | `src/test/data/profile1.alog` |
| Sample `.json` | `src/test/data/profile1.json` |
| Reference WS server | `src/dev_simulator/ws_server.py` |

---

## Appendix C — Glossary

| Term | Meaning |
|---|---|
| `.alog` | Artisan native profile format (Python `repr(dict)`, single line) |
| BBP | Between Batch Protocol — data between DROP and next CHARGE |
| CHARGE | Event marking beans loaded into roaster (start of roast) |
| DROP | Event marking beans unloaded (end of roast) |
| DRY | End-of-drying phase marker (visible on RoR turning up) |
| FCs/FCe | First crack start / end |
| SCs/SCe | Second crack start / end |
| RoR | Rate of Rise (°C/min) |
| `roastUUID` | UUID hex identifying a roast — primary key across client and server |
| Plus | Artisan's paid cloud service at `artisan.plus` |
| ArtisanViewer | Read-only companion app sharing account/sync/outbox caches |

---

**End of spec.** For clarifications or additions, edit this file in place. Downstream agents should treat this document as the source of truth over any verbally-provided context.
