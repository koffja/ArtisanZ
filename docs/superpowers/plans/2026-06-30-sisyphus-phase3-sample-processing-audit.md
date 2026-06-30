# Sisyphus Phase 3 Sample-Processing Audit & Characterization

> **For agentic workers:** This is an **audit/characterization document**, not an implementation plan. No production code is changed by this slice. REQUIRED SUB-SKILL for any *follow-up* implementation slice: superpowers:test-driven-development and superpowers:verification-before-completion.

**Goal:** Inspect the current state of `tgraphcanvas.sample_processing()` after the prior Phase 3 extraction slices, and produce an actionable checklist of what remains inline. Each remaining inline block is classified into one of five buckets:

1. **Pure-helper extraction candidate** — pure function of inputs, no `self.*` mutation, no Qt, no I/O. Safe to lift into `sample_processing.py` under TDD.
2. **Mutation/orchestration that should stay in `canvas.py`** — writes `self.*` state, calls into `ApplicationWindow`/`pidcontrol`/`fujipid`/matplotlib directly, or relies on `profileDataSemaphore` ordering.
3. **Renderer payload work** — direct matplotlib `Line2D.set_data()` / axes mutation. Belongs to the Phase 2 renderer-boundary follow-up, not Phase 3.
4. **Worker-thread candidate** — could in principle move off the GUI thread *only after* a measurable Phase 0 baseline proves `sample_processing` is a GUI-loop blocker and the renderer-boundary seam is in place.
5. **Defer / no-change** — semaphore discipline, error handlers, signal emissions whose contract is already correct.

**Tech Stack:** Pure-Python characterization; only additive tests use pytest / `py_compile` / ruff.

---

## Scope & Ownership

**In scope (edit):**
- `docs/superpowers/plans/2026-06-30-sisyphus-phase3-sample-processing-audit.md` (this file).
- `docs/superpowers/plans/2026-06-30-sisyphus-phase3-sample-processing-audit-SELF-REVIEW.md`.
- `src/test/unitary/artisanlib/test_sample_processing.py` — additive characterization tests only (dataclass frozen-property + private-helper behavior). Existing behavioral tests stay unchanged.

**Out of scope (do NOT edit):**
- `src/artisanlib/canvas.py`, `src/artisanlib/main.py`, `src/artisanlib/sample_processing.py`, `src/artisanlib/plot_*`, `src/artisanlib/ui_workspaces.py`.
- `.codebase-memory/*`.
- Any unrelated file.

**Branch:** Originally produced on `codex/sisyphus-phase3-audit` as an isolated worktree audit, then reviewed and ported into the `ArtisanZ` branch by Codex. No production code changes are part of this audit slice.

---

## Current State Snapshot

| Layer | Size | Shape |
|---|---|---|
| `tgraphcanvas.sample_processing` | `canvas.py:4621–5286` (666-line body, cognitive ~571, loops depth ≤2) | 22 logical blocks under a single outer `try/except/finally` with `profileDataSemaphore` guard. |
| `artisanlib.sample_processing` | 1178 lines, 57 top-level symbols (45 functions + 10 frozen dataclasses + 1 enum + 1 type alias) | 100% pure: no I/O, no logging, no module-level mutation; only `numpy` / `warnings.catch_warnings` (scoped) / stdlib. |
| Pre-audit test suite | 2294 lines, 122 tests | Directly covered the public behavior but left 10 frozen dataclasses and 3 private helpers without direct characterization tests; the `TemperatureValue` type alias is documented only. |
| canvas.py imports | 29 symbols (`canvas.py:108–138`) | All referenced. No dead code in module (remaining 28 symbols are transitive callees or dataclass return types). |

**Verdict:** the pure-decision surface is largely extracted. What remains inline is dominated by `self.*` mutation, renderer payload, and external-subsystem orchestration — not by extractable math.

---

## Threading Model (verified, corrects a tempting misreading)

- `SampleThread.sample()` (`canvas.py:19912`, runs on the worker QThread) calls `self.sample_processingSignal.emit(...)` at line 19959.
- `createSampleThread()` connects the signal at `canvas.py:20060` with **no `type=` argument**, i.e. Qt `AutoConnection`.
- `AutoConnection` resolves at emit time, based on emitter thread vs. receiver thread affinity. The receiver `self.aw.qmc` (`tgraphcanvas`) lives on the **main/GUI thread**; the emit happens from inside `SampleThread.run()` on the **worker thread**.
- Therefore the slot `sample_processing` is invoked on the **GUI thread via `QueuedConnection`**. The comment at `canvas.py:4619` ("processed in the GUI thread NOT the sample thread") is correct.
- Implications:
  - The 7 emitted `pyqtSignal`s (`markChargeSignal`, `markTPSignal`, `markDropSignal`, `markDRYSignal`, `markFCsSignal`, `processAlarmSignal`, `updategraphicsSignal`) are explicitly `QueuedConnection` (verified around `canvas.py:2612–2644`), so they defer back to the GUI thread event loop. They are effectively *intra-thread asynchronous deferrals*, not cross-thread handoffs.
  - Direct matplotlib `Line2D.set_data()` / `self.updateProjection()` / `self.xaxistosm()` calls inside `sample_processing` are **thread-safe** because the whole method runs on the GUI thread.
  - The real performance concern is **GUI-loop blocking**: `sample_processing` runs synchronously, so its duration delays every other GUI event (redraw, click, scroll). This is the correct framing for any future threading work, not a thread-safety hazard.

---

## Block-by-Block Classification

Body structure: `Block 1` (semaphore guard) → outer `try:` containing `Block 2..20` (device path vs. manual-mode `else:` at `Block 20`) → outer `except:` (`Block 21`) → outer `finally:` (`Block 22`).

| # | Lines | Block name | Reads (key) | Mutates / Side effects | Bucket |
|---|---|---|---|---|---|
| 1 | 4622–4629 | Semaphore guard (`profileDataSemaphore.tryAcquire`) | `self.delay`, `self.profileDataSemaphore` | `gui_perf_count('canvas.sample_processing.lock_skip')` perf counter; `_log.debug` | **(5) Defer / no-change** — worker-GUI coordination |
| 2 | 4635–4687 | Snapshot state — recording vs. on-mode rolling buffers | `local_flagstart`, all `self.timex/temp1/temp2/ctimex*/ctemp*/tstemp*/unfiltereddelta*/delta*/extratimex/extratemp*/extractimex*/extractemp*` + `on_*` variants, `self.extradevices` | Truncates `self.on_*` to `[-m_len:]`; aliases chosen buffer into `sample_*` locals | **(2) Mutation** (small pure-helper for the *choice* is possible — see §"Small pure-helper leftovers") |
| 3 | 4690–4787 | Extra-devices loop (RT symbolic eval → inputFilter → backfill → append → matplotlib set_data) | `self.extradevices`, `self.aw.extraser`, `self.extramathexpression{1,2}[i]`, `self.minmaxLimits`/`dropSpikes`/`dropDuplicates`, `self.interpolatemax`, `self.aw.extraCurveVisibility{1,2}[i]` | `self.RTtemp{1,2}`, `self.RTextratemp{1,2}[i]`, `self.RTextratx[i]`, `sample_extratemp*` / `sample_extractemp*` lists, **`self.extratemp{1,2}lines[…].set_data(...)`** (Line2D), raises on length mismatch | **(3) Renderer payload** for the matplotlib set_data step; **(2) Mutation** for buffer work. Sub-blocks 4692–4727 (RT eval), 4735–4757 (inputFilter + backfill), 4759–4771 (append + connected_curve_point) are *already* calling extracted helpers; remaining inline glue is small. |
| 4 | 4791–4833 | ET/BT symbolic transforms + inputFilter + backfill | `self.eval_math_expression`, `self.ETfunction`/`BTfunction`, `self.inputFilter`, `self.minmaxLimits`/`dropSpikes`/`dropDuplicates` | Destructive on `sample_temp1/temp2`, mutates `sample_ctemp1/ctemp2` via `input_filter_backfill_updates` | **(2) Mutation** — calls into `self.inputFilter` (stateful canvas method) and `self.eval_math_expression` (stateful). |
| 5 | 4837–4849 | Main-channel append + connected-curve merge | `connected_curve_point`, `self.interpolatemax` | `sample_temp1/2/timex`, `sample_ctimex*/ctemp*` lists | **(2) Mutation** — only list mutations; logic already delegates to extracted helper. |
| 6 | 4853–4871 | Smoothing weights + smoothed temperature values | `self.curvefilter`, `self.temp_decay_weights`, `sample_temp1/2`, `self.delay` | Caches `self.temp_decay_weights` | **(2) Mutation** — cache write to `self.temp_decay_weights`; the math itself is already extracted (`smoothing_weights_for_recent_readings`, `smoothed_temperature_value`). |
| 7 | 4881–4890 | Smoothed append + matplotlib updates for ET/BT | `full_curve_data`, `local_flagstart` | `sample_tstemp1/2`, **`self.l_temp1.set_data(...)`**, **`self.l_temp2.set_data(...)`** | **(3) Renderer payload** — same pattern as Block 3. |
| 8 | 4892–4907 | Software PID integration | `self.Controlbuttonflag`, `self.aw.pidcontrol.externalPIDControl()`, `self.aw.pidcontrol.pidSource`, `st1`, `st2`, `sample_extratemp*` | **`self.pid.update(process_value)`** (mutates PID loop state) | **(2) Mutation** — external subsystem; decisions already extracted (`pid_process_value_update_enabled`, `pid_process_value`). |
| 9 | 4909–4975 | RoR computation (`compute_ror` + math formula + decay smoothing) | `self.compute_ror` (sibling method, `canvas.py:4602`), `self.DeltaETfunction`/`DeltaBTfunction`, `self.deltaETfilter`/`deltaBTfilter`, `self.deltaETsamples`/`deltaBTsamples`, `self.polyfitRoRcalc`, `self.delay` | `self.rateofchange1/2`, `self.unfiltereddelta1_pure/2_pure`, `self.decay_weights`, `sample_unfiltereddelta1/2` lists | **(2) Mutation** — heavy state writes; pure helpers (`rate_of_rise_per_minute`, `simple_rate_of_rise_per_minute`, `delta_smoothing_filter_size`, `smoothed_rate_of_change_value`) are already wired through `self.compute_ror`. |
| 10 | 4977–5014 | `build_live_processed_sample_frame` orchestrator + consume frame | 29 args from `self.*` + freshly computed locals | Returns pure `ProcessedSampleFrame`; canvas extracts `.displayed_delta_et/bt` here | **(1) Already extracted** — this is the seam. |
| 11 | 5016–5018 | Append displayed deltas to delta arrays | `processed_frame.displayed_delta_*` | `sample_delta1/2` lists | **(2) Mutation** — pure list append; trivial. |
| 12 | 5020–5042 | Delta-curve matplotlib updates + xlim + projection | `windowed_curve_data`, `processed_frame.live_x_axis_extension_end` | **`self.l_delta1.set_data(...)`**, **`self.l_delta2.set_data(...)`**, `self.endofx`, **`self.xaxistosm()`** (axes ticks), **`self.updateProjection()`** (~200-line canvas method) | **(3) Renderer payload** — all four sub-blocks mutate matplotlib artists directly. |
| 13 | 5044–5070 | autoCHARGE / TP-timeout / TP detection | `processed_frame.events.{charge_candidate, turning_point_timeout_index, turning_point_check_candidate}`, `turning_point_temperature_is_valid`, `self.checkTPalarmtime`, `self.aw.BTbreak`, `self.aw.findTP` | `self.autoChargeIdx`, `self.TPalarmtimeindex`, **emits `markChargeSignal`**, **emits `markTPSignal`** | **(2) Mutation + signal emission** — event state writes belong in canvas; signals are already queued. |
| 14 | 5072–5101 | autoDROP / autoDRY / autoFCs | `processed_frame.events.drop_candidate`, `phase_event_candidates_after_turning_point` | `self.autoDropIdx`, **emits `markDropSignal`**, **emits `markDRYSignal`**, **emits `markFCsSignal`** | **(2) Mutation + signal emission** — same shape as Block 13. |
| 15 | 5103–5107 | Active quantifiers hook | `self.aw.process_active_quantifiers()` | External side-effect on `ApplicationWindow` (plus-style hook) | **(2) Mutation** — opaque delegate; leave inline. |
| 16 | 5109–5141 | Fuji / Software PID set-value update | `self.flagon`, `self.device`, `self.aw.fujipid.followBackground`, `self.flagstart`, `self.aw.pidcontrol.pidActive`, `self.aw.pidcontrol.svMode` | **`self.aw.fujipid.setsv(...)`** (Fuji branch), **`self.aw.pidcontrol.setSV(...)`** (Software branch) — both trigger slider moves on the GUI thread | **(2) Mutation** — decisions already extracted (`pid_sv_update_target`, `pid_set_value_update`); remaining inline work is the side-effecting call dispatch. |
| 17 | 5143–5164 | AUC / BBP metrics update | `post_sample_update_decisions` | **`self.aw.updateAUC()`**, **`self.aw.updateAUCguide()`**, **`self.aw.calcBBPMetrics(checkCache=True)`** | **(2) Mutation** — external subsystem; decision already extracted. |
| 18 | 5167–5195 | External output program (subprocess call) | `self.aw.ser.externaloutprogramFlag`, `self.aw.ser.externaloutprogram`, `self.background`, `self.timeindex[0]`, `tx`, `sample_timex`, `self.temp1B/temp2B`, `sample_temp1[-1]/temp2[-1]`, `self.backgroundtime2index` | **`self.aw.call_prog_with_args(cmd)`** — invokes an external subprocess | **(2) Mutation** — payload already extracted (`external_program_background_lookup_time`, `external_program_output_command`); remaining inline work reads background profile state and dispatches the subprocess. |
| 19 | 5197–5236 | Alarms | `evaluate_alarm_triggers`, `self.alarmSemaphore`, `self.alarmbeep/action/strings[i]` | `self.alarmstate[i]`, **emits `processAlarmSignal`** (QueuedConnection) | **(2) Mutation + signal emission** — decision already extracted; remaining inline is per-trigger side-effect dispatch. |
| 20 | 5238–5267 | Manual-mode else branch (`device == 18`) | `self.timeclock`, `self.fixmaxtime`, `self.locktimex`, `self.timeindex[0]`, `self.endofx`, `self.startofx`, `manual_x_axis_extension_end`, `manual_turning_point_check_candidate`, `self.checkTPalarmtime`, `self.aw.findTP` | `self.endofx`, **`self.ax.set_xlim(...)`**, **`self.xaxistosm()`**, `self.TPalarmtimeindex`, **emits `markTPSignal`** | **(3) Renderer payload** + **(2) Mutation** — manual-mode mirror of Block 12 + Block 13. |
| 21 | 5268–5271 | Outer exception handler | caught `Exception` | `_log.exception(e)`, `self.adderror("Exception: sample() {0}", tb_lineno)` | **(5) Defer / no-change** — note: error string says `"sample() {0}"` not `"sample_processing() {0}"`; see SELF-REVIEW. |
| 22 | 5272–5286 | `finally` cleanup + background playback + redraw kick | `self.profileDataSemaphore`, `local_flagstart`, `self.backgroundprofile`, `self.timeindex[0]`, `self.backgroundPlaybackEvent/DROP` | `self.profileDataSemaphore.release(1)`, `self.playbackevent()` / `self.playbackdrop()`, `self.adderror("Exception: sample_processing() {0}", ...)`, **emits `updategraphicsSignal`** | **(5) Defer / no-change** — orchestration is correct. |

### Five-bucket totals

| Bucket | Blocks | Approx. inline LoC remaining |
|---|---|---|
| (1) Pure-helper extraction candidate | none new (Block 10 is the already-built seam) | 0 |
| (2) Mutation / orchestration that should stay | 2, 3 (buffer parts), 4, 5, 6 (cache), 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20 (mutation parts) | ~370 |
| (3) Renderer payload (Phase 2 follow-up) | 3, 7, 12, 20 (matplotlib parts) | ~80 |
| (4) Worker-thread candidate | none until Phase 0 baseline says so | 0 |
| (5) Defer / no-change | 1, 21, 22 | ~40 |

**Conclusion:** the remaining ~490 inline lines are mostly **mutation and orchestration that legitimately belongs in `canvas.py`**, plus ~80 lines of **renderer payload** that the Phase 2 renderer-boundary slice should eventually own. There is no obvious new pure-helper extraction left at this layer; the extraction surface is **functionally complete** for Phase 3's stated goal.

---

## Small pure-helper leftovers (optional, low-priority)

These are the only remaining candidates for additional pure-helper extraction. Each is small and should only be pursued if it materially helps the Phase 2 renderer-boundary slice or a future worker-thread migration:

| Candidate | Location | Why it might help |
|---|---|---|
| `bind_rolling_buffer_choice(local_flagstart)` returning the chosen buffer alias tuple | Block 2 (4635–4687) | The *decision* (which buffer to alias) is pure; only the `self.on_*` truncation must stay in canvas. Could simplify future testability of the buffer aliasing. |
| Shared `apply_input_filter_with_backfill` helper unifying the extra-device (4735–4757) and main-channel (4808–4833) blocks | Blocks 3 & 4 | The two blocks have identical control flow. Extracting a shared helper that takes the relevant `inputFilter` invocation + backfill dispatch as a callback would dedupe ~30 lines. But the helper would still call into `self.inputFilter` (stateful), so it stays in canvas — *internal* refactor only. |
| `compute_ror` (sibling method at `canvas.py:4602`) | Already partly extracted; reads `self.polyfitRoRcalc`, `self.DeltaETfunction`/`BTfunction`, writes `self.rateofchange*`. | Its pure math is already in `sample_processing.rate_of_rise_per_minute` / `simple_rate_of_rise_per_minute`. Further extraction is unlikely to add value. |

None of these are blocking. **Recommend: defer.**

---

## Additive Test Coverage Plan

The audit identified 13 symbols in `sample_processing.py` with no direct test (see SELF-REVIEW for full breakdown). Of these:

- **10 frozen dataclasses** (`ConnectedCurvePoint`, `BackfillUpdate`, `PreviousReadings`, `InputFilterResult`, `AlarmTrigger`, `AutoEventDecisions`, `PhaseEventDecisions`, `ProcessedSampleFrame`, `CurveWindowData`, `PostSampleUpdateDecisions`) → safe to add **frozen-property + equality** characterization tests.
- **3 private helpers** (`_alarm_row_is_complete`, `_bt_above_event_threshold`, `_relative_latest_value`) → safe to add **behavior characterization** tests (already exercised transitively through their public wrappers).
- **1 type alias** (`TemperatureValue`) → not testable as a unit.

These tests document existing behavior and protect any future Phase 3 cleanup (e.g., if a helper is inlined back or signature is tightened, the test breaks loudly). They do **not** require touching production code.

**Implementation note:** The additive tests are intentionally minimal: each dataclass gets a single equality + frozen test; each private helper gets 2-3 behavior tests. The goal is documentation, not 100% line coverage.

---

## Verification Plan

The audit doc itself is read-only documentation. The additive tests in `test_sample_processing.py` are the only artifacts that need command-level verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen /Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m pytest \
  test/unitary/artisanlib/test_sample_processing.py -q
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m ruff check \
  test/unitary/artisanlib/test_sample_processing.py
git diff --check
```

Expected:
- pytest: pre-existing 122 tests + 13 new additive tests all pass.
- ruff: clean.
- `git diff --check`: no whitespace errors.

---

## Residual Risks

1. **Stale comment drift.** `canvas.py:4619` is currently correct, but if a future slice switches the connection at `canvas.py:20060` to explicit `Qt.ConnectionType.DirectConnection`, the comment will silently mislead. A follow-up could replace the comment with a link to the connect site, or pin the connection type with an explicit `type=Qt.ConnectionType.QueuedConnection`.
2. **`compute_ror` (sibling at `canvas.py:4602`) is not under `sample_processing.py`'s test surface.** It still owns its own mutation of `self.rateofchange*`. Future Phase 3 slices should decide whether to fold its pure math fully into the module or leave it as a sibling.
3. **Phase 0 baseline is short-window only.** The 20-second simulator smoke reported in the roadmap (`sample_processing max=0.574ms avg=0.500ms`) does not prove the method is non-blocking under real device load. Before any Phase 3 → worker-thread migration, a longer simulator/device baseline is required.
4. **Block 21 error string** (`"Exception: sample() {0}"` at `canvas.py:5271`) says `sample()` instead of `sample_processing()`. The sibling handler at `canvas.py:5284` is correct. Cosmetic but should be fixed in a separate trivial slice.
5. **Block 2 cache write** (`self.temp_decay_weights`) and Block 6 (`self.decay_weights`) are still inline. If a future slice moves `sample_processing` off the GUI thread, these cache writes will need explicit synchronization or hoisting into a per-frame payload.

---

## Hand-off

- **Next recommended slice (Phase 3 follow-up):** none at this layer. The pure-helper extraction surface is functionally complete.
- **Alternative next slice (Phase 2 follow-up):** wrap the matplotlib `Line2D.set_data` / `set_xlim` / `xaxistosm` / `updateProjection` sites (Blocks 3, 7, 12, 20) behind the Phase 2 `LivePlotRenderer` adapter so a PyQtGraph backend can be swapped in.
- **Alternative next slice (Phase 0 follow-up):** capture a 60-second simulator baseline and a 60-second real-device baseline before reconsidering threading migration.
