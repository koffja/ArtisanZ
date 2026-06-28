## Context

`docs/DROP_PLUS_UPLOAD_BUG_REPORT.md` describes a real defect in the current ArtisanZ HEAD. The evidence in code is:

- `src/artisanlib/main.py` wires `buttonDROP.clicked` directly to `self.qmc.markDrop`.
- `src/artisanlib/canvas.py::markDrop()` queues `plus.queue.addRoast()` inside the DROP handler before `openPropertiesSignal.emit()` opens roast properties.
- `src/artisanlib/canvas.py::event_popup_action()` has a second DROP path that can also call `addRoast()` when a DROP mark is first set from the canvas popup.
- `src/artisanlib/roast_properties.py::close_OK()` already queues `plus.queue.addRoast()` after `shouldQueueRoastPropertiesUpload()` passes, which means the repository already has a user-confirmed upload boundary.
- `src/plus/queue.py` has last-item subset dedupe but no general cancel/remove-by-roast-id API for unsent queue items, and no way to retract a roast once the queue worker has posted it.

The root cause is that the same conceptual event, "completed roast is ready for artisan.plus", is triggered from two different lifecycle points: local DROP state mutation and accepted roast properties. The first point is too early because it is not user confirmation and cannot be undone after enqueue/send.

## Goals / Non-Goals

**Goals:**
- Make accepted completed roast properties the single authoritative trigger for initial artisan.plus completed-roast upload.
- Ensure DROP, Undo DROP, and canvas popup DROP placement never enqueue a full roast upload by themselves.
- Preserve existing guards in `shouldQueueRoastPropertiesUpload()`: recording started, safe-save dirty state, CHARGE and DROP set, plus account present, readonly plus access disabled, simulator disabled, and not opening properties only to start recording.
- Keep schedule completion registration and plus status refresh behavior, but execute them only on the same confirmed path as upload.
- Add focused regression tests for the upload gate and the removed early DROP upload paths.

**Non-Goals:**
- Do not add a recurring confirmation popup before upload.
- Do not implement server-side deletion or a general queue cancellation feature.
- Do not change Cropster import code or ArtisanZ charge-target code.
- Do not redesign the artisan.plus queue worker, sync cache, or remote API.

## Decisions

1. Use roast properties acceptance as the upload boundary.

   `editGraphDlg.close_OK()` is the correct boundary because it only runs when the user accepts the properties dialog. Cancel and window close call `closeEvent()` instead, which restores dialog-local state and does not queue plus uploads. Keeping this boundary avoids a prompt-driven workflow and aligns upload with the user's final completed-roast data.

   Alternative considered: add a `QMessageBox` before `addRoast()` inside `markDrop()`. This is lower effort but keeps the upload attached to the wrong lifecycle event, interrupts every normal roast, and leaves the canvas popup path easy to miss.

2. Remove immediate upload side effects from both DROP entry points.

   `markDrop()` and `event_popup_action()` should continue to update local roast state, annotations, timers, batch counters, PID behavior, and property dialog opening. They must not call `addRoast()`, `register_completed_roast.emit()`, or `updatePlusStatus()` as part of first DROP handling. This prevents accidental uploads and avoids needing an unreliable queue retraction feature.

   Alternative considered: keep early upload and add Undo DROP cleanup. `plus.queue` cannot reliably remove already-sent records, so cleanup would only work for a narrow offline-window case and would not solve the remote pollution problem.

3. Centralize confirmed plus completion side effects in a small helper.

   Add a helper near `shouldQueueRoastPropertiesUpload()` in `src/artisanlib/roast_properties.py`, for example `queueConfirmedCompletedRoastUpload(aw, *, start_recording_on_exit: bool) -> bool`. The helper should:

   - call `shouldQueueRoastPropertiesUpload()` with the current `aw.qmc` state,
   - return `False` without side effects when the gate fails,
   - emit `aw.schedule_window.register_completed_roast` when a schedule window is present,
   - call `aw.updatePlusStatus()`,
   - call `plus.queue.addRoast()`,
   - catch/log exceptions consistently with the current code,
   - return whether queuing was attempted.

   This keeps `close_OK()` readable and gives tests a small surface that does not require constructing the full PyQt canvas.

   Alternative considered: leave the existing `close_OK()` inline `if shouldQueue... addRoast()` block and simply delete canvas calls. That would fix the main bug, but schedule/status behavior would be either lost or scattered; the helper makes the confirmed lifecycle explicit.

4. Preserve queue-level dedupe as defense in depth, not as correctness.

   `queue_roast_item()` may suppress a consecutive subset duplicate, but correctness must not depend on it. The fix should ensure accidental DROP and canceled properties create zero upload attempts before dedupe is involved.

5. Treat auto-DROP consistently with manual DROP.

   Auto-DROP can still mark DROP automatically. The upload occurs when the completed roast properties are accepted, or on the next confirmed properties save if the auto-open properties preference is disabled. This changes the upload timing but not the ability to upload a completed roast.

## Risks / Trade-offs

- Users who relied on immediate DROP upload will see upload delayed until they accept roast properties. Mitigation: the delay is intentional and should be documented in release notes or a short user-facing note.
- If a workflow disables auto-open roast properties after DROP, upload will wait for the next accepted properties save. Mitigation: this is safer than remote pollution and matches the confirmed-upload contract.
- Moving schedule completion registration could subtly affect artisan.plus schedule UI timing. Mitigation: move it into the confirmed helper and test that it fires exactly when upload is attempted.
- Canvas tests are expensive because `canvas.py` is PyQt-heavy. Mitigation: keep most behavior in the helper and add lightweight static or focused monkeypatch tests proving `canvas.py` no longer imports/calls `addRoast`.
- Existing uncommitted plus/upload work in the tree may overlap. Mitigation: implement in small patches and avoid reverting user changes.
