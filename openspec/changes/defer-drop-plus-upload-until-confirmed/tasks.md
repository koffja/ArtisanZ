## 1. Baseline and Regression Tests

- [x] 1.1 Run the current focused baseline from `src/`: `python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py test/unitary/plus/test_confirmed_upload.py -q`
- [x] 1.2 Add tests in `src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py` for a confirmed upload helper: gate pass calls schedule registration, plus status refresh, and `plus.queue.addRoast()` exactly once.
- [x] 1.3 Add tests in `src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py` proving the confirmed upload helper returns without side effects when simulator mode is active, plus account is missing, plus account is readonly, CHARGE/DROP is missing, or `start_recording_on_exit` is true.
- [x] 1.4 Add a focused regression test under `src/test/unitary/artisanlib/` proving `src/artisanlib/canvas.py` no longer calls `addRoast()` from `markDrop()` or `event_popup_action()`.
- [x] 1.5 Run the new/changed tests and confirm they fail for the current early-DROP upload implementation.

## 2. Confirmed Upload Implementation

- [x] 2.1 Add `queueConfirmedCompletedRoastUpload(aw, *, start_recording_on_exit: bool) -> bool` near `shouldQueueRoastPropertiesUpload()` in `src/artisanlib/roast_properties.py`.
- [x] 2.2 Implement the helper so it reuses `shouldQueueRoastPropertiesUpload()`, emits `aw.schedule_window.register_completed_roast` when present, calls `aw.updatePlusStatus()`, queues `plus.queue.addRoast()`, logs exceptions consistently, and returns whether upload queuing was attempted.
- [x] 2.3 Replace the inline `shouldQueueRoastPropertiesUpload(...): plus.queue.addRoast()` block in `editGraphDlg.close_OK()` with a call to `queueConfirmedCompletedRoastUpload()`.
- [x] 2.4 Remove the immediate artisan.plus upload block from `canvas.py::markDrop()` while preserving local DROP behavior, annotation updates, PID behavior, batch counter behavior, and properties auto-open.
- [x] 2.5 Remove the immediate artisan.plus upload block from `canvas.py::event_popup_action()` for first DROP placement.
- [x] 2.6 Remove the now-unused `addRoast` import from `src/artisanlib/canvas.py` and keep `sendLockSchedule` import behavior unchanged.

## 3. Verification and Documentation

- [x] 3.1 Run `python3 -m py_compile artisanlib/roast_properties.py artisanlib/canvas.py plus/queue.py` from `src/`.
- [x] 3.2 Run `python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py test/unitary/plus/test_confirmed_upload.py -q` from `src/`.
- [x] 3.3 Run `python3 -m pytest test/unitary/plus/ -q` from `src/` if the focused tests pass.
- [x] 3.4 Update `docs/DROP_PLUS_UPLOAD_BUG_REPORT.md` after implementation to mark the verified root cause and chosen long-term fix, without changing unrelated Cropster or charge-target sections.
- [x] 3.5 Manually verify the expected workflow: connected plus user presses DROP, cancels properties, and no upload is queued; connected plus user presses DROP, accepts properties, and exactly one upload is queued.
