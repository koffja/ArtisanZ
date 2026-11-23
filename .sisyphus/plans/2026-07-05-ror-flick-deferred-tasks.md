# RoR Flick/Crash Detector — 4 Deferred Tasks Plan

> **Status**: Planning document for follow-up work after the initial rorflick feature.
> **Prerequisite**: All code review fixes must be committed first.
> **Execution**: Each task can be executed independently. Recommended order: A → C → D → B.

---

## Task A: Status Bar Widget Wiring

**Goal**: Connect `rorflick_manager.get_status_message()` to ArtisanZ's `messagelabel` widget so users see real-time RoR status text during roasting.

**Effort**: ~30 minutes (1 file, ~10 lines)

**Architecture decision**: Inline the status update inside `draw_rorflick_annotation()` (canvas.py), NOT via a new signal/slot. This co-locates detection with notification.

### Files to Modify

| File | Change |
|---|---|
| `src/artisanlib/canvas.py` | Add status update at end of `draw_rorflick_annotation` (~line 19235, after `self._rorflick_last_len = current_len`) |
| `src/artisanlib/canvas.py` | Add `_rorflick_last_status_text` to `__init__` (~line 548) and pickle whitelist (~line 446) |

### Key Code

**In `__init__` (after `self._rorflick_last_len: int = 0`):**
```python
self._rorflick_last_status_text: str = ''
```

**In pickle whitelist (add `'_rorflick_last_status_text'`):**
```python
# existing: 'rorflick_artists', '_rorflick_last_len',
'rorflick_artists', '_rorflick_last_len', '_rorflick_last_status_text',
```

**In `draw_rorflick_annotation` (after `self._rorflick_last_len = current_len`):**
```python
# Update status bar (guarded to avoid spamming on unchanged state)
text, color = self.rorflick_manager.get_status_message()
if text != self._rorflick_last_status_text:
    self._rorflick_last_status_text = text
    if text:
        self.aw.sendmessage(
            text, append=False,
            style=f"background-color:'transparent'; color:{color};"
        )
    # Note: do NOT clear messagelabel when text is empty —
    # other features (charge_target, PID) may be using it.
```

### Verification
1. `cd src && python3 -m py_compile artisanlib/canvas.py`
2. `cd src && ./.venv/bin/python -m pytest test/unitary/artisanlib/test_canvas.py -q`
3. Manual: run `python3 artisan.py`, enable RoR detector, observe status bar text during simulation

### Notes
- `self.aw` is the `ApplicationWindow` instance, always available on canvas
- `self.aw.sendmessage()` is thread-safe (defers via QTimer.singleShot)
- `append=False` prevents polluting the 100-entry message history log
- The guard `text != self._rorflick_last_status_text` prevents 250ms-cadence thrash
- Charge_target's `get_status_message()` is also currently unwired — consider wiring both in the same pass (would need a combined message like `"RoR: FLICK 8.3 | Charge: 可以投豆"`)

---

## Task B: pyqtgraph Pipeline Parity

**Goal**: Add RoR flick/crash annotations to ArtisanZ's parallel pyqtgraph rendering pipeline, mirroring the existing charge_target annotation handling.

**Effort**: ~1-2 days (3 files, ~200-245 LoC production + ~150-200 LoC tests)

### Architecture

The pyqtgraph pipeline has 3 layers (mirror each):

| Layer | charge_target analog | rorflick equivalent |
|---|---|---|
| **Data contract** | `ChargeTargetAnnotationSnapshot` in `plot_snapshot.py:90-107` | `RoRFlickAnnotationSnapshot` (new dataclass) |
| **Extractor** | `_charge_target_annotations()` in `plot_snapshot_extractor.py:901-1034` | `_rorflick_annotations()` (new function) |
| **Renderer** | `_default_charge_target_annotation_factory()` in `plot_pyqtgraph_adapter.py:797-878` | `_default_rorflick_annotation_factory()` (new function) + 6 wiring touch points |

### Files to Create/Modify

#### 1. `src/artisanlib/plot_snapshot.py` (~30 LoC)

Add after `ChargeTargetAnnotationSnapshot` (~line 107):

```python
RoRFlickSeverity = Literal['soft', 'moderate', 'hard']


@dataclass(frozen=True, slots=True)
class RoRFlickAnnotationSnapshot:
    """A single RoR flick/crash event for pyqtgraph rendering."""
    enabled: bool
    start_time: float       # resolved from start_idx via timex
    end_time: float         # resolved from end_idx via timex
    peak_time: float        # resolved from peak_idx via timex
    peak_value: float       # delta2 value at peak_idx
    event_type: Literal['flick', 'crash']
    severity: RoRFlickSeverity
    peak_magnitude: float   # °C/min divergence
    in_development: bool
```

Add field to `RoastPlotSnapshot` (~line 210):
```python
rorflick_annotations: tuple[RoRFlickAnnotationSnapshot, ...] = ()
```

Add to `__all__` (~line 242):
```python
'RoRFlickAnnotationSnapshot',
'RoRFlickSeverity',
```

#### 2. `src/artisanlib/plot_snapshot_extractor.py` (~60-80 LoC)

Add after `_charge_target_annotations` (~line 1034):

```python
def _rorflick_annotations(
        source: object,
        *,
        time_axis: AxisSnapshot | None = None,
        temperature_axis: AxisSnapshot | None = None,
) -> tuple[RoRFlickAnnotationSnapshot, ...]:
    """Extract RoR flick/crash events from the source's rorflick_manager."""
    manager = getattr(source, 'rorflick_manager', None)
    if manager is None or not manager.enabled:
        return ()

    timex = _sequence(source, 'timex')
    delta2 = _sequence(source, 'delta2')
    if not timex or not delta2:
        return ()

    snapshots: list[RoRFlickAnnotationSnapshot] = []
    for event in manager.events:
        # Skip events whose indices are out of bounds
        if (event.start_idx >= len(timex)
                or event.end_idx >= len(timex)
                or event.peak_idx >= len(timex)
                or event.peak_idx >= len(delta2)):
            continue

        start_time = _finite_numeric_value(timex[event.start_idx])
        end_time = _finite_numeric_value(timex[event.end_idx])
        peak_time = _finite_numeric_value(timex[event.peak_idx])
        peak_value = _finite_numeric_value(delta2[event.peak_idx])

        snapshots.append(RoRFlickAnnotationSnapshot(
            enabled=True,
            start_time=start_time,
            end_time=end_time,
            peak_time=peak_time,
            peak_value=peak_value,
            event_type=event.event_type,
            severity=event.severity,
            peak_magnitude=event.peak_magnitude,
            in_development=event.in_development,
        ))

    return tuple(snapshots)
```

Add call sites at the two `extract_*` functions (~lines 120 and 147):
```python
rorflick_annotations=_rorflick_annotations(source, time_axis=time_axis, temperature_axis=temperature_axis),
```

#### 3. `src/artisanlib/plot_pyqtgraph_adapter.py` (~110-125 LoC)

**Constants** (mirror `_CHARGE_*` with `_RORFLICK_*` prefix, ~line 777):

```python
_RORFLICK_SEVERITY_COLORS: dict[str, str] = {
    'soft': '#FFCC00',
    'moderate': '#FF8800',
    'hard': '#CC0000',
}
_RORFLICK_SEVERITY_ALPHA: dict[str, float] = {
    'soft': 0.20,
    'moderate': 0.30,
    'hard': 0.40,
}
_RORFLICK_Z = 35
```

**Factory function** (after `_default_charge_target_annotation_factory`, ~line 878):

```python
def _default_rorflick_annotation_factory(
        annotation: RoRFlickAnnotationSnapshot,
        snapshot: RoastPlotSnapshot) -> tuple[object, ...] | None:
    """Render a single RoR flick/crash event as pyqtgraph items."""
    if not annotation.enabled:
        return None

    items: list[object] = []
    color = _RORFLICK_SEVERITY_COLORS.get(annotation.severity, '#FFCC00')
    alpha = _RORFLICK_SEVERITY_ALPHA.get(annotation.severity, 0.20)

    # Highlight band (LinearRegionItem)
    band = pg.LinearRegionItem(
        values=[annotation.start_time, annotation.end_time],
        orientation='vertical',
        brush=pg.mkBrush(color, alpha=alpha),
        movable=False,
    )
    band.setZValue(_RORFLICK_Z - 1)
    items.append(band)

    # Peak label (TextItem)
    sign = '-' if annotation.event_type == 'crash' else '+'
    dev_tag = ' (DEV)' if annotation.in_development else ''
    label = f"{annotation.event_type.upper()}\n{sign}{annotation.peak_magnitude:.1f}°/min{dev_tag}"
    text_item = pg.TextItem(
        text=label,
        color='#333333',
        fill=pg.mkBrush(color + 'CC'),  # semi-transparent background
    )
    text_item.setPos(annotation.peak_time, annotation.peak_value + 5)
    text_item.setZValue(_RORFLICK_Z)
    items.append(text_item)

    return tuple(items)
```

**Wiring** (6 touch points in `PyQtGraphSnapshotRenderer`, mirroring charge_target):

| Touch point | Line (approx) | What to add |
|---|---|---|
| Import | ~12 | Add `RoRFlickAnnotationSnapshot` to imports |
| Type alias | ~31-34 | `RoRFlickAnnotationItemFactory = Callable[[RoRFlickAnnotationSnapshot, RoastPlotSnapshot], ...]` |
| Constructor kwarg | ~77 | `rorflick_annotation_factory: RoRFlickAnnotationItemFactory \| None = None` |
| Storage | ~90-92 | `self._rorflick_annotation_factory = rorflick_annotation_factory or _default_rorflick_annotation_factory` |
| Item list | ~102 | `self._rorflick_annotation_items: list[object] = []` |
| Count method | ~156-157 | `def rorflick_annotation_item_count(self) -> int` |
| Apply call | ~170 | `self._apply_rorflick_annotations(snapshot)` inside `_apply_static_overlays` |
| Apply method | ~328-338 | `_apply_rorflick_annotations(self, snapshot)` + `_clear_rorflick_annotation_items(self)` |
| Cache key | ~367 | `snapshot.rorflick_annotations,` in `_static_overlay_signature` |

### Tests to Create

| File | Tests | What they verify |
|---|---|---|
| `test_plot_snapshot.py` | 2 | disabled→empty, active event with resolved time/value |
| `test_plot_snapshot_extractor.py` | 4 | disabled→empty, single flick event, out-of-bounds index skipped, None timex handled |
| `test_plot_pyqtgraph_adapter.py` | 2 | factory returns 2 items (band+text), severity color mapping correct |

### Critical Caveats

1. **Indexes → time**: `RoRFlickEvent` stores sample indices. The extractor MUST resolve to time/value coordinates (the snapshot is renderer-agnostic).
2. **Multi-event**: Unlike charge_target (0 or 1 snapshot), rorflick returns 0-N snapshots. Factory runs per-event.
3. **Cache invalidation**: Adding `snapshot.rorflick_annotations` to `_static_overlay_signature` causes re-render when events list changes. Since events are append-only during a roast, consider using `(len(events), last_severity)` fingerprint instead.
4. **QApplication required**: pyqtgraph adapter tests need `QApplication.instance() or QApplication([])`.

---

## Task C: Translation .ts Entries

**Goal**: Add Chinese translation entries for the `'RoRFlickDlg'` context so the dialog strings appear in `pylupdate6` output and can be translated in Linguist.

**Effort**: ~30 minutes

### Current State

All user-facing strings in `rorflick_dialog.py` already use `QApplication.translate('RoRFlickDlg', '...')`:
- `'RoR 异常检测设置'` (window title)
- `'检测阈值'`, `'Development 加权'`
- `'Flick 触发 (°C/min):'`, `'Crash 触发 (°C/min):'`, `'退出阈值 (°C/min):'`
- `'一爆后严重度倍数:'`, `'启用功能'`, `'保存'`, `'取消'`

Menu entry in `main.py` uses `QApplication.translate('Menu', 'RoR 异常检测...')`.

### Steps

1. **Verify strings are detected by pylupdate6**:
   ```bash
   cd src
   # Check if artisan.pro lists the source files
   grep "rorflick" artisan.pro
   # If not listed, add:
   #   artisanlib/rorflick_manager.py
   #   artisanlib/rorflick_dialog.py
   ```

2. **Run pylupdate6 to regenerate .ts**:
   ```bash
   cd src
   python3 pylupdate6pro.py artisan.pro
   # Or directly:
   pylupdate6 artisan.pro -ts translations/artisan_zh_CN.ts
   ```

3. **Add translations in Linguist or manually in `translations/artisan_zh_CN.ts`**:
   - The Chinese strings are already written in the source code (they're the default text)
   - For the `'RoRFlickDlg'` context, the source text IS the Chinese text, so the `<translation>` should be the same (or refined)
   - For the `'Menu'` context entry `'RoR 异常检测...'`, same treatment

4. **Compile .ts to .qm**:
   ```bash
   cd src
   lrelease translations/artisan_zh_CN.ts -qm translations/artisan_zh_CN.qm
   ```

5. **Verify**:
   ```bash
   cd src && python3 -m py_compile artisanlib/rorflick_dialog.py
   ```

### Notes
- Since the source strings are already in Chinese, the `.ts` file entries will have `<type="unfinished">` with identical source and translation. Mark them as `<type="finished">` or `<type="obsolete">` depending on whether you want to keep them as-is.
- The `'Menu'` context for `'RoR 异常检测...'` is shared with all other menu items, so it goes into the existing `<context><name>Menu</name>` block.
- English fallback: if you want English UI support, add `<translation>RoR Anomaly Detection...</translation>` as the English version.

---

## Task D: Live/Replay Averaging Unification

**Goal**: Eliminate the semantic difference between live-mode averaging (`_charge_window_average_delta`) and replay-mode averaging (`_window_average`) so the same roast produces identical detection results whether recording live or loaded from disk.

**Effort**: ~2-4 hours

### Current Problem

| Aspect | Live mode (`_charge_window_average_delta`) | Replay mode (`_window_average`) |
|---|---|---|
| **Windowing** | Time-based (walks `timex` backward, breaks when `> window_seconds`) | Index-based (sample count = `seconds × sample_rate_hz`) |
| **None filtering** | Yes (`value is not None`) | Yes (after Fix 1) |
| **Negative filtering** | Yes (`value > 0` — excludes cooling/negative RoR) | No (includes all non-None values) |
| **Early samples** | Returns `None` if <2 samples | Returns partial-window average (could be 1 sample) |
| **Return on empty** | `None` | `0.0` |

### Design Decision

Two options:

**Option A (simpler)**: Make `_window_average` replicate `_charge_window_average_delta`'s filtering rules.
- Pros: Manager stays self-contained, no callback dependency
- Cons: Manager needs to know about time-based windowing (currently index-based)

**Option B (cleaner)**: Have `process_roast` receive a callback or pre-computed averages from the canvas.
- Pros: Single source of truth for averaging semantics
- Cons: Changes the manager's API; `process_roast` is no longer self-contained

**Recommended**: Option A — modify `_window_average` to filter non-positive values AND use time-based windowing when `timex` is available.

### Implementation Plan (Option A)

#### Step 1: Add time-aware windowing to the manager

Add a new method that mirrors `_charge_window_average_delta` exactly:

```python
@staticmethod
def _time_window_average(
    delta2: list[float],
    timex: list[float],
    end_idx: int,
    window_seconds: float,
) -> float | None:
    """Time-based window average, mirroring canvas._charge_window_average_delta."""
    if not delta2 or not timex or end_idx < 0 or end_idx >= len(delta2) or end_idx >= len(timex):
        return None
    if len(timex) < 2 or len(delta2) < 2:
        return None

    latest_time = timex[end_idx]
    values: list[float] = []
    for idx in range(end_idx, -1, -1):
        if idx >= len(timex):
            continue
        if latest_time - timex[idx] > window_seconds:
            break
        value = delta2[idx]
        if value is not None and value > 0:  # match _charge_window_average_delta exactly
            values.append(value)

    if not values:
        return None
    return sum(values) / len(values)
```

#### Step 2: Update `process_roast` to use time-based windowing

Change `process_roast` to accept `timex` as a parameter and use `_time_window_average`:

```python
def process_roast(
    self,
    delta2: list[float],
    timex: list[float],           # NEW PARAMETER
    fcs_idx: int = -1,
) -> list[RoRFlickEvent]:
    """Process a complete roast from raw delta2 + timex (replay mode)."""
    self.reset()
    if not delta2 or not timex:
        return []

    for i in range(len(delta2)):
        short_avg = self._time_window_average(delta2, timex, i, 9.0)
        long_avg = self._time_window_average(delta2, timex, i, 30.0)
        in_dev = fcs_idx > -1 and i >= fcs_idx
        self.process_sample(i, short_avg, long_avg, in_dev)

    # Close any open event at end (same as before)
    ...
```

Note: `sample_rate_hz` parameter is no longer needed (time-based windowing doesn't use it).

#### Step 3: Update canvas.py call site

In `draw_rorflick_annotation`, change the replay branch:

```python
elif current_len != self._rorflick_last_len:
    # --- Replay mode ---
    self.rorflick_manager.process_roast(
        self.delta2,
        self.timex,              # NEW: pass timex
        fcs_idx=self.timeindex[2],
        # sample_rate_hz removed — no longer needed
    )
```

#### Step 4: Update existing tests

Update `test_rorflick_manager.py`:
- `TestRoRFlickProcessRoast` tests need to pass `timex` instead of `sample_rate_hz`
- Generate synthetic `timex` arrays matching the delta2 length (e.g., `timex = list(range(len(delta2)))` for 1Hz)
- Add a new test: `test_process_roast_with_none_and_negative_values_filters_correctly`

#### Step 5: Verify parity

Add a parity test that proves live and replay produce the same events for the same data:

```python
def test_live_and_replay_produce_identical_events():
    """Verify that processing the same data live vs replay gives the same events."""
    delta2 = [5.0, 5.0, 5.0, 15.0, 15.0, 15.0, 6.0, 6.0]
    timex = [float(i) for i in range(len(delta2))]

    # Live: simulate one-sample-at-a-time processing
    m_live = RoRFlickManager()
    m_live.enabled = True
    m_live.flick_threshold = 3.0
    m_live.exit_threshold = 1.0
    for i in range(len(delta2)):
        short = RoRFlickManager._time_window_average(delta2, timex, i, 9.0)
        long_ = RoRFlickManager._time_window_average(delta2, timex, i, 30.0)
        m_live.process_sample(i, short, long_, False)

    # Close any open event
    if m_live._current_start is not None:
        m_live._finalize_event(len(delta2) - 1, False)

    # Replay
    m_replay = RoRFlickManager()
    m_replay.enabled = True
    m_replay.flick_threshold = 3.0
    m_replay.exit_threshold = 1.0
    m_replay.process_roast(delta2, timex, fcs_idx=-1)

    # Both should detect the same events
    assert len(m_live.events) == len(m_replay.events)
    for live_evt, replay_evt in zip(m_live.events, m_replay.events):
        assert live_evt.event_type == replay_evt.event_type
        assert live_evt.peak_magnitude == replay_evt.peak_magnitude
```

### Migration Notes
- `process_batch` (the test-only method that takes pre-computed averages) remains unchanged — it's for unit testing the state machine, not for production replay
- `_window_average` (the old index-based method) can be kept for backward compatibility or removed if no callers remain after the migration
- The `sample_rate_hz` parameter on `process_roast` is removed — this is a breaking API change, but `process_roast` only has one caller (canvas.py)

---

## Execution Priority

| Task | Effort | Dependency | Value |
|---|---|---|---|
| **A (status bar)** | 30 min | None | High — completes Spec 4 (status bar alerts) |
| **C (translations)** | 30 min | None | Low — strings already work in Chinese; only needed for i18n completeness |
| **D (averaging unification)** | 2-4 hrs | None | Medium — fixes consistency; not user-visible unless comparing live vs replay |
| **B (pyqtgraph parity)** | 1-2 days | None | Low for MVP — matplotlib path already works; pyqtgraph is a secondary renderer |

**Recommended order**: A → C → D → B
