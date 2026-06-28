## Why

Pressing DROP while connected to artisan.plus currently queues a roast upload before the user accepts the roast properties dialog. A mistaken DROP, a canceled properties dialog, or an immediate Undo DROP can therefore create a remote artisan.plus roast that the local UI can no longer retract.

This should be fixed at the workflow boundary, not with an extra warning prompt: a completed roast upload should be queued only after the user confirms the completed roast state.

## What Changes

- Move the initial artisan.plus completed-roast upload trigger out of immediate DROP event handlers and into the existing roast properties acceptance path.
- Treat DROP as a local roast-state event only; it may mark the roast complete, update the UI, and open properties, but it must not enqueue the first full artisan.plus roast record.
- Keep later confirmed roast property updates uploading through the existing `shouldQueueRoastPropertiesUpload()` gate.
- Prevent alternate DROP-setting paths, including the canvas event popup path, from bypassing the confirmed upload gate.
- Preserve existing no-upload behavior for simulator mode, readonly plus accounts, missing CHARGE/DROP data, missing plus login, and properties dialogs opened only to start recording.
- Add regression coverage proving canceled properties and Undo DROP do not queue artisan.plus uploads, while accepted completed roast properties queue exactly one upload.

## Capabilities

### New Capabilities
- `confirmed-plus-roast-upload`: Defines when a completed roast may be queued for artisan.plus upload after DROP and roast properties confirmation.

### Modified Capabilities
- None.

## Impact

- Affected UI workflow: DROP, Undo DROP, auto-DROP, canvas event popup DROP placement, roast properties acceptance, and artisan.plus status/schedule completion hooks.
- Affected code: `src/artisanlib/canvas.py`, `src/artisanlib/roast_properties.py`, `src/plus/queue.py` tests/mocks as needed, plus focused unit tests under `src/test/unitary/artisanlib/` and `src/test/unitary/plus/`.
- No public API or dependency changes are expected.
- The externally visible behavior changes from "DROP immediately queues a roast upload" to "accepting completed roast properties queues the first roast upload."
