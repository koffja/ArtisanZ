# Post DROP Roast Completion UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the confusing post-DROP Roast Properties confirmation flow with explicit save, upload, finish, and continue-cooling actions.

**Architecture:** Keep the implementation inside the existing ArtisanZ PyQt dialog flow, but add a small pure state/action layer at the top of `roast_properties.py` so the UX semantics can be tested without constructing the full dialog. The Roast Properties dialog will set an explicit completion action from the clicked button, save properties as it does today, queue upload only when requested by the existing eligibility gate, and optionally stop recording/monitoring after the dialog closes.

**Tech Stack:** Python 3.12+, PyQt6, pytest, unittest.mock, ArtisanZ `src/artisanlib/roast_properties.py`, ArtisanZ `src/artisanlib/canvas.py` signals.

---

## Scope

This plan covers one cohesive workflow:

- Clarify post-DROP dialog actions.
- Decouple "save attributes", "upload to Plus/Cotrix", and "finish recording".
- Rename confusing Roast Properties labels.
- Preserve the existing Plus upload gate and queue behavior.
- Preserve the existing ability to continue recording cooling data after DROP.

This plan does not redesign the whole Roast Properties dialog layout, schedule window, Plus queue internals, or translations catalog generation. Translation source strings are changed in Python; compiled `.qm` translation artifacts are not regenerated in this plan.

## Current State Summary

- `DROP` marks the roast end event in `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/canvas.py`; it can open Roast Properties when `roastpropertiesAutoOpenDropFlag` is enabled, but it does not stop monitoring.
- `OK` in `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py` runs `editGraphDlg.close_OK()`, saves dialog fields, and calls `queueConfirmedCompletedRoastUpload(...)`.
- `queueConfirmedCompletedRoastUpload(...)` already returns `True` only when upload was queued. Keep that behavior.
- Red `OFF` means `qmc.flagon` is still active. It is not an upload status.
- Existing focused tests live in `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`.

## File Structure

Modify:

- `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
  - Add pure post-DROP action helpers.
  - Add dialog button configuration.
  - Add explicit completion action handling.
  - Add user-facing save/upload status message.
  - Rename confusing labels and tooltips.

- `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`
  - Extend existing focused tests with pure helper tests and method-level mock tests.
  - Avoid full Qt dialog construction.

Read but do not modify unless implementation reveals a direct need:

- `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/canvas.py`
  - Confirm `toggleMonitorSignal` remains the right way to stop recording/monitoring.

Do not modify:

- `/Users/chengzhe/Projects/ArtisanZ/src/plus/queue.py`
  - Existing queue semantics are enough for this UX change.

## Repository Rules

Before implementation, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git branch --show-current
git status --short
git remote -v
```

Expected:

```text
ArtisanZ
origin   git@github.com:koffja/ArtisanZ.git
upstream https://github.com/artisan-roaster-scope/artisan.git
```

The workspace may already have uncommitted user changes from prior Plus upload work. Do not revert them. AGENTS.md says not to commit unless explicitly asked; each task includes an authorized commit command, but the command must only be run after the user explicitly permits commits for the implementation session.

## Task 1: Add Pure Completion Action State Helpers

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`

- [ ] **Step 1: Write failing tests for completed-roast action state**

Append these tests after the existing upload gate tests in `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`:

```python
def test_is_completed_roast_requires_charge_and_drop() -> None:
    assert roast_properties.isCompletedRoast(charge_index=0, drop_index=60) is True
    assert roast_properties.isCompletedRoast(charge_index=-1, drop_index=60) is False
    assert roast_properties.isCompletedRoast(charge_index=0, drop_index=0) is False


def test_should_offer_finish_roast_action_only_for_active_completed_recording() -> None:
    assert roast_properties.shouldOfferFinishRoastAction(
        flagstart=True,
        flagon=True,
        charge_index=0,
        drop_index=60,
    ) is True
    assert roast_properties.shouldOfferFinishRoastAction(
        flagstart=False,
        flagon=True,
        charge_index=0,
        drop_index=60,
    ) is False
    assert roast_properties.shouldOfferFinishRoastAction(
        flagstart=True,
        flagon=False,
        charge_index=0,
        drop_index=60,
    ) is False
    assert roast_properties.shouldOfferFinishRoastAction(
        flagstart=True,
        flagon=True,
        charge_index=0,
        drop_index=0,
    ) is False


def test_should_finish_recording_after_properties_only_for_finish_action() -> None:
    assert roast_properties.shouldFinishRecordingAfterRoastProperties(
        roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        flagstart=True,
        flagon=True,
    ) is True
    assert roast_properties.shouldFinishRecordingAfterRoastProperties(
        roast_properties.COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING,
        flagstart=True,
        flagon=True,
    ) is False
    assert roast_properties.shouldFinishRecordingAfterRoastProperties(
        roast_properties.COMPLETION_ACTION_SAVE_ONLY,
        flagstart=True,
        flagon=True,
    ) is False
    assert roast_properties.shouldFinishRecordingAfterRoastProperties(
        roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        flagstart=False,
        flagon=True,
    ) is False
    assert roast_properties.shouldFinishRecordingAfterRoastProperties(
        roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        flagstart=True,
        flagon=False,
    ) is False
```

- [ ] **Step 2: Run tests and verify they fail**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: fail with `AttributeError` for `isCompletedRoast`, `shouldOfferFinishRoastAction`, or `COMPLETION_ACTION_SAVE_AND_FINISH`.

- [ ] **Step 3: Add completion action constants and helpers**

In `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`, add `Literal` to the typing import:

```python
from typing import override, Final, cast, Any, TYPE_CHECKING, Literal
```

Add this block below `_log` and above `hasRecordingBeans(...)`:

```python
CompletionAction = Literal['save_only', 'save_and_finish', 'save_and_continue_cooling']

COMPLETION_ACTION_SAVE_ONLY: Final[CompletionAction] = 'save_only'
COMPLETION_ACTION_SAVE_AND_FINISH: Final[CompletionAction] = 'save_and_finish'
COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING: Final[CompletionAction] = 'save_and_continue_cooling'


def isCompletedRoast(*, charge_index: int, drop_index: int) -> bool:
    return charge_index > -1 and drop_index > 0


def shouldOfferFinishRoastAction(
        *,
        flagstart: bool,
        flagon: bool,
        charge_index: int,
        drop_index: int) -> bool:
    return flagstart and flagon and isCompletedRoast(
        charge_index=charge_index,
        drop_index=drop_index,
    )


def shouldFinishRecordingAfterRoastProperties(
        completion_action: CompletionAction,
        *,
        flagstart: bool,
        flagon: bool) -> bool:
    return (
        completion_action == COMPLETION_ACTION_SAVE_AND_FINISH
        and flagstart
        and flagon
    )
```

- [ ] **Step 4: Run focused tests and verify they pass**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: all tests in that file pass.

- [ ] **Step 5: Authorized checkpoint**

If and only if the user explicitly allowed commits for this implementation session, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git add src/artisanlib/roast_properties.py src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py
git commit -m "feat: model post-drop completion actions"
```

Expected: one commit is created on `ArtisanZ`.

## Task 2: Add Button Text and Status Message Helpers

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`

- [ ] **Step 1: Write failing tests for labels and messages**

Append these tests to `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`:

```python
def test_post_drop_button_texts_for_writable_plus_completed_recording() -> None:
    texts = roast_properties.roastPropertiesButtonTexts(
        offer_finish=True,
        upload_available=True,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    )

    assert texts.primary == 'Save, Upload and Finish'
    assert texts.secondary == 'Save and Continue Cooling'


def test_post_drop_button_texts_for_completed_recording_without_writable_plus() -> None:
    texts = roast_properties.roastPropertiesButtonTexts(
        offer_finish=True,
        upload_available=False,
        plus_account=None,
        plus_readonly=False,
        service_name='Cotrix',
    )

    assert texts.primary == 'Save and Finish'
    assert texts.secondary == 'Save and Continue Cooling'


def test_post_drop_button_texts_for_readonly_plus_completed_recording() -> None:
    texts = roast_properties.roastPropertiesButtonTexts(
        offer_finish=True,
        upload_available=False,
        plus_account='coffja@qq.com',
        plus_readonly=True,
        service_name='Cotrix',
    )

    assert texts.primary == 'Save and Finish'
    assert texts.secondary == 'Save and Continue Cooling'


def test_post_drop_button_texts_require_upload_available_for_upload_copy() -> None:
    texts = roast_properties.roastPropertiesButtonTexts(
        offer_finish=True,
        upload_available=False,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    )

    assert texts.primary == 'Save and Finish'
    assert texts.secondary == 'Save and Continue Cooling'


def test_button_texts_do_not_promise_upload_when_finish_is_not_offered() -> None:
    texts = roast_properties.roastPropertiesButtonTexts(
        offer_finish=False,
        upload_available=False,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    )

    assert texts.primary == 'Save'
    assert texts.secondary is None


def test_completed_roast_save_message_reports_queued_upload() -> None:
    assert roast_properties.completedRoastSaveMessage(
        upload_queued=True,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    ) == 'Roast saved. Upload queued to Cotrix.'


def test_completed_roast_save_message_reports_local_save_when_plus_unavailable() -> None:
    assert roast_properties.completedRoastSaveMessage(
        upload_queued=False,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        plus_account=None,
        plus_readonly=False,
        service_name='Cotrix',
    ) == 'Roast saved locally.'


def test_completed_roast_save_message_reports_readonly_plus() -> None:
    assert roast_properties.completedRoastSaveMessage(
        upload_queued=False,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        plus_account='coffja@qq.com',
        plus_readonly=True,
        service_name='Cotrix',
    ) == 'Roast saved locally. Cotrix is read-only.'
```

- [ ] **Step 2: Run tests and verify they fail**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: fail with `AttributeError` for `roastPropertiesButtonTexts` or `completedRoastSaveMessage`.

- [ ] **Step 3: Add dataclass import and helper implementations**

In `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`, add the dataclass import near the other imports:

```python
from dataclasses import dataclass
```

Add this block below the completion action helpers from Task 1:

```python
@dataclass(frozen=True)
class RoastPropertiesButtonTexts:
    primary: str
    secondary: str|None


def roastPropertiesButtonTexts(
        *,
        offer_finish: bool,
        upload_available: bool,
        plus_account: str|None,
        plus_readonly: bool,
        service_name: str) -> RoastPropertiesButtonTexts:
    del plus_account, plus_readonly, service_name
    if offer_finish:
        primary = (
            QApplication.translate('Button', 'Save, Upload and Finish')
            if upload_available else
            QApplication.translate('Button', 'Save and Finish')
        )
        return RoastPropertiesButtonTexts(
            primary=primary,
            secondary=QApplication.translate('Button', 'Save and Continue Cooling'),
        )
    return RoastPropertiesButtonTexts(
        primary=QApplication.translate('Button', 'Save'),
        secondary=None,
    )


def completedRoastSaveMessage(
        *,
        upload_queued: bool,
        completion_action: CompletionAction,
        plus_account: str|None,
        plus_readonly: bool,
        service_name: str) -> str:
    del completion_action
    if upload_queued:
        return QApplication.translate(
            'Message',
            'Roast saved. Upload queued to {service_name}.',
        ).format(service_name=service_name)
    if plus_account is not None and plus_readonly:
        return QApplication.translate(
            'Message',
            'Roast saved locally. {service_name} is read-only.',
        ).format(service_name=service_name)
    return QApplication.translate('Message', 'Roast saved locally.')
```

The `upload_available` argument is intentionally explicit so button copy cannot promise an upload unless the caller has checked the same completion/Plus/simulator/start-recording conditions used by the queue gate. The other keyword arguments stay in the signature for caller symmetry and future copy without changing the public helper shape.

- [ ] **Step 4: Run focused tests and verify they pass**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: all tests in that file pass.

- [ ] **Step 5: Authorized checkpoint**

If and only if the user explicitly allowed commits for this implementation session, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git add src/artisanlib/roast_properties.py src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py
git commit -m "feat: describe post-drop roast actions"
```

Expected: one commit is created on `ArtisanZ`.

## Task 3: Wire Explicit Dialog Buttons

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`

- [ ] **Step 1: Write failing tests for button wiring by source inspection**

Append these tests to `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`:

```python
def test_roast_properties_dialog_configures_completion_buttons() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    text = source.read_text(encoding='utf-8')

    assert 'def configureCompletionButtons(self) -> None:' in text
    assert 'self.dialogbuttons.clicked.connect(self.roastDialogButtonClicked)' in text
    assert 'Save and Continue Cooling' in text
    assert 'COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING' in text


def test_roast_dialog_button_click_sets_completion_action() -> None:
    finish_button = object()
    continue_button = object()
    dialog = SimpleNamespace(
        dialogbuttons=SimpleNamespace(button=Mock(return_value=finish_button)),
        save_continue_cooling_button=continue_button,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_ONLY,
    )

    roast_properties.editGraphDlg.roastDialogButtonClicked(dialog, continue_button)
    assert dialog.completion_action == roast_properties.COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING

    roast_properties.editGraphDlg.roastDialogButtonClicked(dialog, finish_button)
    assert dialog.completion_action == roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH
```

- [ ] **Step 2: Run tests and verify they fail**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: fail because `configureCompletionButtons` and `roastDialogButtonClicked` do not exist.

- [ ] **Step 3: Add QAbstractButton import**

In `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`, extend the `PyQt6.QtWidgets` import list:

```python
from PyQt6.QtWidgets import (QApplication, QWidget, QCheckBox, QComboBox, QDialogButtonBox, QGridLayout,
                             QHBoxLayout, QVBoxLayout, QHeaderView, QLabel, QLineEdit, QTextEdit, QListView,
                             QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QSizePolicy,
                             QGroupBox, QToolButton, QFrame, QAbstractButton)
```

- [ ] **Step 4: Initialize and configure completion buttons**

In `editGraphDlg.__init__`, directly after the existing lines:

```python
        # connect the ArtisanDialog standard OK/Cancel buttons
        self.dialogbuttons.accepted.connect(self.close_OK)
        self.dialogbuttons.rejected.connect(self.closeEvent)
```

add:

```python
        self.completion_action: CompletionAction = COMPLETION_ACTION_SAVE_ONLY
        self.save_continue_cooling_button: QPushButton|None = None
        self.dialogbuttons.clicked.connect(self.roastDialogButtonClicked)
        self.configureCompletionButtons()
```

- [ ] **Step 5: Add dialog button methods**

Add these methods inside `class editGraphDlg`, near `close_OK` and before `getMeasuredvalues(...)`:

```python
    def configureCompletionButtons(self) -> None:
        offer_finish = shouldOfferFinishRoastAction(
            flagstart=self.aw.qmc.flagstart,
            flagon=self.aw.qmc.flagon,
            charge_index=self.aw.qmc.timeindex[0],
            drop_index=self.aw.qmc.timeindex[6],
        )
        upload_available = shouldQueueRoastPropertiesUpload(
            flagstart=self.aw.qmc.flagstart,
            safesaveflag=self.aw.qmc.safesaveflag,
            charge_index=self.aw.qmc.timeindex[0],
            drop_index=self.aw.qmc.timeindex[6],
            plus_account=self.aw.plus_account,
            plus_readonly=bool(self.aw.plus_readonly),
            simulator=bool(self.aw.simulator),
            start_recording_on_exit=self.start_recording_on_exit,
        )
        texts = roastPropertiesButtonTexts(
            offer_finish=offer_finish,
            upload_available=upload_available,
            plus_account=self.aw.plus_account,
            plus_readonly=bool(self.aw.plus_readonly),
            service_name=plus.service_identity.display_name(),
        )
        ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setText(texts.primary)
            self.completion_action = (
                COMPLETION_ACTION_SAVE_AND_FINISH
                if offer_finish else
                COMPLETION_ACTION_SAVE_ONLY
            )
        if texts.secondary is not None:
            self.save_continue_cooling_button = self.dialogbuttons.addButton(
                texts.secondary,
                QDialogButtonBox.ButtonRole.AcceptRole,
            )

    @pyqtSlot('QAbstractButton')
    def roastDialogButtonClicked(self, button: QAbstractButton) -> None:
        if self.save_continue_cooling_button is not None and button is self.save_continue_cooling_button:
            self.completion_action = COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING
            return
        ok_button = self.dialogbuttons.button(QDialogButtonBox.StandardButton.Ok)
        if button is ok_button and self.completion_action != COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING:
            if shouldOfferFinishRoastAction(
                    flagstart=self.aw.qmc.flagstart,
                    flagon=self.aw.qmc.flagon,
                    charge_index=self.aw.qmc.timeindex[0],
                    drop_index=self.aw.qmc.timeindex[6]):
                self.completion_action = COMPLETION_ACTION_SAVE_AND_FINISH
            else:
                self.completion_action = COMPLETION_ACTION_SAVE_ONLY
```

- [ ] **Step 6: Run focused tests and verify they pass**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: all tests in that file pass.

- [ ] **Step 7: Authorized checkpoint**

If and only if the user explicitly allowed commits for this implementation session, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git add src/artisanlib/roast_properties.py src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py
git commit -m "feat: add explicit roast completion buttons"
```

Expected: one commit is created on `ArtisanZ`.

## Task 4: Stop Recording Only When the User Chooses Finish

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`

- [ ] **Step 1: Write failing tests for finish dispatch**

Append these tests to `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`:

```python
def test_finish_completed_roast_schedules_monitor_stop() -> None:
    emit = Mock()
    dialog = SimpleNamespace(
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                toggleMonitorSignal=SimpleNamespace(emit=emit),
            )
        ),
    )

    with patch('artisanlib.roast_properties.QTimer.singleShot', side_effect=lambda _ms, callback: callback()) as timer:
        roast_properties.editGraphDlg.finishCompletedRoastIfRequested(dialog)

    timer.assert_called_once()
    emit.assert_called_once_with()


def test_continue_cooling_does_not_stop_monitoring() -> None:
    emit = Mock()
    dialog = SimpleNamespace(
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING,
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                toggleMonitorSignal=SimpleNamespace(emit=emit),
            )
        ),
    )

    with patch('artisanlib.roast_properties.QTimer.singleShot') as timer:
        roast_properties.editGraphDlg.finishCompletedRoastIfRequested(dialog)

    timer.assert_not_called()
    emit.assert_not_called()


def test_close_ok_calls_finish_after_cleanup() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))

    close_ok = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == 'close_OK'
    )
    call_names = [
        node.func.attr
        for node in ast.walk(close_ok)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]

    assert 'finishCompletedRoastIfRequested' in call_names
```

- [ ] **Step 2: Run tests and verify they fail**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: fail because `finishCompletedRoastIfRequested` does not exist and `close_OK` does not call it.

- [ ] **Step 3: Add finish dispatch method**

Add this method inside `class editGraphDlg`, directly after `roastDialogButtonClicked(...)`:

```python
    def finishCompletedRoastIfRequested(self) -> None:
        if shouldFinishRecordingAfterRoastProperties(
                self.completion_action,
                flagstart=self.aw.qmc.flagstart,
                flagon=self.aw.qmc.flagon):
            QTimer.singleShot(0, self.aw.qmc.toggleMonitorSignal.emit)
```

- [ ] **Step 4: Wire `close_OK()` to message and finish dispatch**

In `close_OK()`, replace the existing upload call:

```python
        queueConfirmedCompletedRoastUpload(
            self.aw,
            start_recording_on_exit=self.start_recording_on_exit,
        )
```

with:

```python
        upload_queued = queueConfirmedCompletedRoastUpload(
            self.aw,
            start_recording_on_exit=self.start_recording_on_exit,
        )
        if isCompletedRoast(
                charge_index=self.aw.qmc.timeindex[0],
                drop_index=self.aw.qmc.timeindex[6]):
            self.aw.sendmessage(completedRoastSaveMessage(
                upload_queued=upload_queued,
                completion_action=self.completion_action,
                plus_account=self.aw.plus_account,
                plus_readonly=bool(self.aw.plus_readonly),
                service_name=plus.service_identity.display_name(),
            ))
```

Then, near the bottom of `close_OK()`, keep `self.clean_up()` and add the finish call before `super().accept()`:

```python
        self.clean_up()
        self.finishCompletedRoastIfRequested()
```

The resulting bottom section must keep this order:

```python
        self.clean_up()
        self.finishCompletedRoastIfRequested()

        has_recording_details = hasRecordingBeans(
            self.aw.qmc.plus_coffee,
            self.aw.qmc.plus_blend_spec,
            self.aw.qmc.beans,
            self.aw.qmc.title,
        )
```

If the code already has `self.clean_up()` immediately before `has_recording_details`, insert `self.finishCompletedRoastIfRequested()` between those two statements.

- [ ] **Step 5: Run focused tests and verify they pass**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: all tests in that file pass.

- [ ] **Step 6: Authorized checkpoint**

If and only if the user explicitly allowed commits for this implementation session, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git add src/artisanlib/roast_properties.py src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py
git commit -m "feat: finish roast from post-drop dialog"
```

Expected: one commit is created on `ArtisanZ`.

## Task 5: Rename Confusing Roast Properties Labels

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`

- [ ] **Step 1: Write failing source-inspection tests for UX copy**

Append these tests to `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`:

```python
def test_roast_properties_uses_clear_manual_beans_and_temperature_labels() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    text = source.read_text(encoding='utf-8')

    assert "QApplication.translate('Label', 'Roast Title')" in text
    assert "QApplication.translate('Label', 'Bean Description')" in text
    assert "QApplication.translate('Label', 'Green Bean Temp')" in text
    assert 'temperature of the green coffee before CHARGE' in text


def test_roast_properties_uses_clear_inventory_and_template_labels() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    text = source.read_text(encoding='utf-8')

    assert "QApplication.translate('Label', 'Inventory')" in text
    assert "QApplication.translate('ComboBox', 'No inventory link')" in text
    assert "QApplication.translate('Button', 'Save Template')" in text
    assert "QApplication.translate('Button', 'Remove Template')" in text
    assert "QApplication.translate('CheckBox', 'Inventory label order')" in text
```

- [ ] **Step 2: Run tests and verify they fail**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: fail because the old source strings are still present.

- [ ] **Step 3: Update title and bean labels**

In `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`, change:

```python
        titlelabel = QLabel('<b>' + QApplication.translate('Label', 'Title') + '</b>')
```

to:

```python
        titlelabel = QLabel('<b>' + QApplication.translate('Label', 'Roast Title') + '</b>')
        titlelabel.setToolTip(QApplication.translate('Tooltip', 'Short name shown on the roast profile and lists'))
```

Change:

```python
        beanslabel = QLabel('<b>' + QApplication.translate('Label', 'Beans') + '</b>')
```

to:

```python
        beanslabel = QLabel('<b>' + QApplication.translate('Label', 'Bean Description') + '</b>')
        beanslabel.setToolTip(QApplication.translate('Tooltip', 'Manual green coffee description, origin, lot, or blend recipe'))
```

- [ ] **Step 4: Update green coffee temperature label**

Change:

```python
        greens_temp_label = QLabel('<b>' + QApplication.translate('Label', 'Beans') + '</b>')
```

to:

```python
        greens_temp_label = QLabel('<b>' + QApplication.translate('Label', 'Green Bean Temp') + '</b>')
```

Change:

```python
        self.greens_temp_edit.setToolTip(QApplication.translate('Tooltip', 'temperature of the green coffee'))
```

to:

```python
        self.greens_temp_edit.setToolTip(QApplication.translate('Tooltip', 'temperature of the green coffee before CHARGE'))
```

- [ ] **Step 5: Update recent template button labels**

Change:

```python
        self.addRecentButton = QPushButton('+')
```

to:

```python
        self.addRecentButton = QPushButton(QApplication.translate('Button', 'Save Template'))
```

Change:

```python
        self.delRecentButton = QPushButton('-')
```

to:

```python
        self.delRecentButton = QPushButton(QApplication.translate('Button', 'Remove Template'))
```

Keep the existing tooltips for add/remove recent roasts because they already explain the action.

- [ ] **Step 6: Update inventory labels and empty selection copy**

Change:

```python
            plusCoffeeslabel = QLabel('<b>' + QApplication.translate('Label', 'Stock') + '</b>')
```

to:

```python
            plusCoffeeslabel = QLabel('<b>' + QApplication.translate('Label', 'Inventory') + '</b>')
```

In `populatePlusCoffeeBlendCombos(...)`, replace each `[''] + ...` item prefix used for stock coffee and blend combo items with:

```python
[QApplication.translate('ComboBox', 'No inventory link')] + coffee_items
```

for coffee items, and:

```python
[QApplication.translate('ComboBox', 'No inventory link')] + blend_items
```

for blend items.

In `CoffeesComboBox.getItems(...)`, change:

```python
        return [''] + plus.stock.getCoffeesLabels(plus_coffees)
```

to:

```python
        return [QApplication.translate('ComboBox', 'No inventory link')] + plus.stock.getCoffeesLabels(plus_coffees)
```

In `BlendsComboBox.getItems(...)`, change:

```python
        return [''] + blend_items
```

to:

```python
        return [QApplication.translate('ComboBox', 'No inventory link')] + blend_items
```

- [ ] **Step 7: Rename inventory label-order checkbox**

Change:

```python
            self.label_origin_flag = QCheckBox(QApplication.translate('CheckBox','Standard bean labels'))
            self.label_origin_flag.setToolTip(QApplication.translate('Tooltip',"Beans are listed as 'origin, name' if ticked, otherwise as 'name, origin'"))
```

to:

```python
            self.label_origin_flag = QCheckBox(QApplication.translate('CheckBox','Inventory label order'))
            self.label_origin_flag.setToolTip(QApplication.translate('Tooltip',"Show inventory beans as 'origin, name' when checked, otherwise as 'name, origin'"))
```

- [ ] **Step 8: Run focused tests and verify they pass**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: all tests in that file pass.

- [ ] **Step 9: Authorized checkpoint**

If and only if the user explicitly allowed commits for this implementation session, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git add src/artisanlib/roast_properties.py src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py
git commit -m "fix: clarify roast properties labels"
```

Expected: one commit is created on `ArtisanZ`.

## Task 6: Regression Verification

**Files:**
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/roast_properties.py`
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_roast_properties_tm_artisanz.py`
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/plus/test_confirmed_upload.py`

- [ ] **Step 1: Run the focused Roast Properties tests**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/artisanlib/test_roast_properties_tm_artisanz.py -q
```

Expected: pass.

- [ ] **Step 2: Run confirmed upload tests**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/plus/test_confirmed_upload.py -q
```

Expected: pass.

- [ ] **Step 3: Run Plus unitary tests touched by previous upload work**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m pytest test/unitary/plus/ -q
```

Expected: pass or preserve the current known baseline if unrelated pre-existing failures are present. If any test fails, inspect whether the failure references `roast_properties.py`, `queue.py`, upload gating, or service identity before declaring it unrelated.

- [ ] **Step 4: Compile modified Python modules**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 -m py_compile artisanlib/roast_properties.py artisanlib/canvas.py
```

Expected: no output and exit code 0.

- [ ] **Step 5: Manual UX verification**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
python3 artisan.py
```

Expected manual checks:

- After marking DROP with Roast Properties auto-open enabled, the dialog primary button reads `Save, Upload and Finish` when Plus is writable.
- The secondary action reads `Save and Continue Cooling`.
- Choosing the primary action saves, queues upload when eligible, closes the dialog, and the main window stops recording/monitoring through the existing OFF path.
- Choosing `Save and Continue Cooling` saves, queues upload when eligible, closes the dialog, and keeps the main window in active monitoring/recording state so cooling can continue.
- The message line clearly says upload was queued to Cotrix or that the roast was saved locally.
- `Roast Title`, `Bean Description`, `Green Bean Temp`, `Inventory`, `No inventory link`, `Save Template`, `Remove Template`, and `Inventory label order` appear in the relevant dialog areas.

- [ ] **Step 6: Authorized final checkpoint**

If and only if the user explicitly allowed commits for this implementation session, run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git status --short
```

Expected: only files from this UX change are staged or modified for the implementation branch. If unrelated dirty files exist, leave them untouched.

## Self-Review

Spec coverage:

- Confusing `OK` upload semantics are covered by Tasks 2, 3, and 4.
- Red `OFF` after post-DROP save is covered by Task 4 and manual verification.
- `+/-` meaning is covered by Task 5.
- `Standard bean labels` meaning is covered by Task 5.
- No-inventory workflow is covered by Task 5.
- Title versus bean description is covered by Task 5.
- Green bean temperature field is covered by Task 5.

Red-flag scan:

- The plan contains concrete file paths, code snippets, and commands.
- The plan avoids deferred requirements.
- Commit commands are present only as authorized checkpoints because AGENTS.md forbids unapproved commits.

Type consistency:

- `CompletionAction` is defined before it is used.
- Constants use the same names across tests and implementation snippets.
- `finishCompletedRoastIfRequested()` uses the existing `toggleMonitorSignal.emit` path from `canvas.py`.
