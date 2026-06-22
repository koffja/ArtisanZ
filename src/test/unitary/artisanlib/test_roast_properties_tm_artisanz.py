"""Focused TM-ArtisanZ roast properties behavior tests."""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from artisanlib import roast_properties


def _completed_roast_app_window(**overrides: object) -> SimpleNamespace:
    qmc = SimpleNamespace(
        flagstart=True,
        safesaveflag=True,
        timeindex=[0, 0, 0, 0, 0, 0, 60],
    )
    schedule_window = SimpleNamespace(register_completed_roast=Mock())
    aw = SimpleNamespace(
        qmc=qmc,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        simulator=None,
        schedule_window=schedule_window,
        updatePlusStatus=Mock(),
    )
    for key, value in overrides.items():
        setattr(aw, key, value)
    return aw


def test_has_recording_beans_accepts_manual_beans_text() -> None:
    assert roast_properties.hasRecordingBeans(None, None, '低温日晒') is True


def test_has_recording_beans_accepts_manual_title_when_beans_are_blank() -> None:
    assert roast_properties.hasRecordingBeans(None, None, '', '低温日晒罗布') is True


def test_has_recording_beans_rejects_blank_manual_beans_text() -> None:
    assert roast_properties.hasRecordingBeans(None, None, '   ') is False


def test_has_recording_beans_rejects_default_title_when_details_are_blank() -> None:
    with patch('artisanlib.roast_properties.QApplication.translate', return_value='Roaster Scope'):
        assert roast_properties.hasRecordingBeans(None, None, '', 'Roaster Scope') is False


def test_has_recording_beans_accepts_plus_inventory_selection() -> None:
    assert roast_properties.hasRecordingBeans('coffee-id', None, '') is True
    assert roast_properties.hasRecordingBeans(None, {'hr_id': 'blend-id'}, '') is True


def test_translated_service_message_rebrands_artisan_plus_to_cotrix() -> None:
    with patch(
        'artisanlib.roast_properties.QApplication.translate',
        return_value='artisan.plus needs to know the beans you are roasting',
    ):
        assert (
            roast_properties.translatedServiceMessage(
                'artisan.plus needs to know the beans you are roasting',
                context='Message',
            )
            == 'Cotrix needs to know the beans you are roasting'
        )


def test_beans_edited_waits_until_plus_line_exists_before_refreshing() -> None:
    beansedit = Mock()
    beansedit.toPlainText.return_value = '低温日晒'
    update_plus_selected_line = Mock()
    dialog = SimpleNamespace(
        beansedit=beansedit,
        aw=SimpleNamespace(plus_account='coffja@qq.com'),
        updatePlusSelectedLine=update_plus_selected_line,
    )

    roast_properties.editGraphDlg.beansEdited(dialog)

    assert dialog.modified_beans == '低温日晒'
    update_plus_selected_line.assert_not_called()


def test_beans_edited_refreshes_plus_line_after_plus_line_exists() -> None:
    beansedit = Mock()
    beansedit.toPlainText.return_value = '低温日晒'
    update_plus_selected_line = Mock()
    dialog = SimpleNamespace(
        beansedit=beansedit,
        aw=SimpleNamespace(plus_account='coffja@qq.com'),
        plus_selected_line=Mock(),
        updatePlusSelectedLine=update_plus_selected_line,
    )

    roast_properties.editGraphDlg.beansEdited(dialog)

    assert dialog.modified_beans == '低温日晒'
    update_plus_selected_line.assert_called_once_with()


def test_recent_roast_enabled_refreshes_plus_line_after_title_change() -> None:
    titleedit = Mock()
    titleedit.currentText.return_value = '低温日晒罗布'
    weightinedit = Mock()
    weightinedit.text.return_value = '500'
    update_plus_selected_line = Mock()
    dialog = SimpleNamespace(
        titleedit=titleedit,
        weightinedit=weightinedit,
        addRecentButton=Mock(),
        delRecentButton=Mock(),
        aw=SimpleNamespace(plus_account='coffja@qq.com'),
        plus_selected_line=Mock(),
        updatePlusSelectedLine=update_plus_selected_line,
    )

    with patch('artisanlib.roast_properties.QApplication.translate', return_value='Roaster Scope'):
        roast_properties.editGraphDlg.recentRoastEnabled(dialog)

    update_plus_selected_line.assert_called_once_with()


def test_should_not_queue_upload_when_properties_opened_to_start_recording() -> None:
    assert roast_properties.shouldQueueRoastPropertiesUpload(
        flagstart=True,
        safesaveflag=True,
        charge_index=0,
        drop_index=60,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        simulator=False,
        start_recording_on_exit=True,
    ) is False


def test_should_not_queue_upload_for_readonly_plus_account() -> None:
    assert roast_properties.shouldQueueRoastPropertiesUpload(
        flagstart=True,
        safesaveflag=True,
        charge_index=0,
        drop_index=60,
        plus_account='coffja@qq.com',
        plus_readonly=True,
        simulator=False,
        start_recording_on_exit=False,
    ) is False


def test_should_queue_upload_for_completed_roast_property_updates() -> None:
    assert roast_properties.shouldQueueRoastPropertiesUpload(
        flagstart=True,
        safesaveflag=True,
        charge_index=0,
        drop_index=60,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        simulator=False,
        start_recording_on_exit=False,
    ) is True


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


def test_confirmed_completed_roast_upload_queues_once_with_plus_side_effects() -> None:
    aw = _completed_roast_app_window()

    with patch('artisanlib.roast_properties.plus.queue.addRoast', return_value=True) as mock_add_roast:
        queued = roast_properties.queueConfirmedCompletedRoastUpload(
            aw,
            start_recording_on_exit=False,
        )

    assert queued is True
    aw.schedule_window.register_completed_roast.emit.assert_called_once_with()
    aw.updatePlusStatus.assert_called_once_with()
    mock_add_roast.assert_called_once_with()


def test_confirmed_completed_roast_upload_reports_not_queued_when_queue_rejects_record() -> None:
    aw = _completed_roast_app_window()

    with patch('artisanlib.roast_properties.plus.queue.addRoast', return_value=False) as mock_add_roast:
        queued = roast_properties.queueConfirmedCompletedRoastUpload(
            aw,
            start_recording_on_exit=False,
        )

    assert queued is False
    aw.schedule_window.register_completed_roast.emit.assert_called_once_with()
    aw.updatePlusStatus.assert_called_once_with()
    mock_add_roast.assert_called_once_with()
    assert 'Upload queued' not in roast_properties.completedRoastSaveMessage(
        upload_queued=queued,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    )


def test_confirmed_completed_roast_upload_reports_not_queued_when_queue_fails() -> None:
    aw = _completed_roast_app_window()

    with patch('artisanlib.roast_properties.plus.queue.addRoast', side_effect=RuntimeError('queue failed')):
        queued = roast_properties.queueConfirmedCompletedRoastUpload(
            aw,
            start_recording_on_exit=False,
        )

    assert queued is False
    aw.schedule_window.register_completed_roast.emit.assert_called_once_with()
    aw.updatePlusStatus.assert_called_once_with()
    assert 'Upload queued' not in roast_properties.completedRoastSaveMessage(
        upload_queued=queued,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    )


@pytest.mark.parametrize(
    ('aw_overrides', 'qmc_overrides', 'start_recording_on_exit'),
    [
        ({'simulator': object()}, {}, False),
        ({'plus_account': None}, {}, False),
        ({'plus_readonly': True}, {}, False),
        ({}, {'timeindex': [-1, 0, 0, 0, 0, 0, 60]}, False),
        ({}, {'timeindex': [0, 0, 0, 0, 0, 0, 0]}, False),
        ({}, {}, True),
    ],
)
def test_confirmed_completed_roast_upload_skips_when_gate_fails(
        aw_overrides: dict[str, object],
        qmc_overrides: dict[str, object],
        start_recording_on_exit: bool) -> None:
    aw = _completed_roast_app_window(**aw_overrides)
    for key, value in qmc_overrides.items():
        setattr(aw.qmc, key, value)

    with patch('artisanlib.roast_properties.plus.queue.addRoast') as mock_add_roast:
        queued = roast_properties.queueConfirmedCompletedRoastUpload(
            aw,
            start_recording_on_exit=start_recording_on_exit,
        )

    assert queued is False
    aw.schedule_window.register_completed_roast.emit.assert_not_called()
    aw.updatePlusStatus.assert_not_called()
    mock_add_roast.assert_not_called()


def test_canvas_drop_handlers_do_not_call_add_roast_before_properties_accept() -> None:
    def is_add_roast_call(node: ast.Call) -> bool:
        return (
            isinstance(node.func, ast.Name) and node.func.id == 'addRoast'
        ) or (
            isinstance(node.func, ast.Attribute) and node.func.attr == 'addRoast'
        )

    canvas_path = Path(__file__).parents[3] / 'artisanlib' / 'canvas.py'
    tree = ast.parse(canvas_path.read_text(encoding='utf-8'))

    drop_handlers = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name in {'markDrop', 'event_popup_action'}
    ]

    assert {node.name for node in drop_handlers} == {'markDrop', 'event_popup_action'}
    for handler in drop_handlers:
        add_roast_calls = [
            node for node in ast.walk(handler)
            if isinstance(node, ast.Call) and is_add_roast_call(node)
        ]
        assert add_roast_calls == []


def test_post_drop_button_texts_for_writable_plus_completed_recording() -> None:
    texts = roast_properties.roastPropertiesButtonTexts(
        offer_finish=True,
        upload_available=True,
        plus_account='coffja@qq.com',
        plus_readonly=False,
        service_name='Cotrix',
    )

    assert texts.primary == 'Save, Upload and Finish'
    assert texts.secondary == 'Save, Upload and Continue Cooling'


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


def test_completed_roast_save_message_translates_upload_template_before_formatting() -> None:
    with patch(
        'artisanlib.roast_properties.QApplication.translate',
        return_value='Roast saved. Upload queued to {service_name}.',
    ) as mock_translate:
        message = roast_properties.completedRoastSaveMessage(
            upload_queued=True,
            completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
            plus_account='coffja@qq.com',
            plus_readonly=False,
            service_name='Cotrix',
        )

    assert message == 'Roast saved. Upload queued to Cotrix.'
    mock_translate.assert_called_once_with(
        'Message',
        'Roast saved. Upload queued to {service_name}.',
    )


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


def test_completed_roast_save_message_translates_readonly_template_before_formatting() -> None:
    with patch(
        'artisanlib.roast_properties.QApplication.translate',
        return_value='Roast saved locally. {service_name} is read-only.',
    ) as mock_translate:
        message = roast_properties.completedRoastSaveMessage(
            upload_queued=False,
            completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
            plus_account='coffja@qq.com',
            plus_readonly=True,
            service_name='Cotrix',
        )

    assert message == 'Roast saved locally. Cotrix is read-only.'
    mock_translate.assert_called_once_with(
        'Message',
        'Roast saved locally. {service_name} is read-only.',
    )


def test_roast_properties_dialog_configures_completion_buttons() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    text = source.read_text(encoding='utf-8')

    assert 'def configureCompletionButtons(self) -> None:' in text
    assert 'self.dialogbuttons.clicked.connect(self.roastDialogButtonClicked)' in text
    assert 'Save, Upload and Continue Cooling' in text
    assert 'Save and Continue Cooling' in text
    assert 'COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING' in text
    assert 'upload_available = shouldQueueRoastPropertiesUpload(' in text
    assert 'upload_available=upload_available' in text
    assert "@pyqtSlot('QAbstractButton')" not in text
    assert '@pyqtSlot(QAbstractButton)' in text


def test_configure_completion_buttons_replaces_continue_button_without_duplicates() -> None:
    ok_button = Mock()
    first_continue = object()
    second_continue = object()
    added_buttons = [first_continue, second_continue]
    button_box = SimpleNamespace(
        button=Mock(return_value=ok_button),
        addButton=Mock(side_effect=added_buttons),
        removeButton=Mock(),
    )
    dialog = SimpleNamespace(
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                safesaveflag=True,
                timeindex=[0, 0, 0, 0, 0, 0, 60],
            ),
            plus_account='coffja@qq.com',
            plus_readonly=False,
            simulator=None,
        ),
        start_recording_on_exit=False,
        dialogbuttons=button_box,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_ONLY,
        save_continue_cooling_button=None,
    )

    with patch('artisanlib.roast_properties.plus.service_identity.display_name', return_value='Cotrix'):
        roast_properties.editGraphDlg.configureCompletionButtons(dialog)
        roast_properties.editGraphDlg.configureCompletionButtons(dialog)

    button_box.removeButton.assert_called_once_with(first_continue)
    assert button_box.addButton.call_count == 2
    assert button_box.addButton.call_args_list[0].args[0] == 'Save, Upload and Continue Cooling'
    assert button_box.addButton.call_args_list[1].args[0] == 'Save, Upload and Continue Cooling'
    assert dialog.save_continue_cooling_button is second_continue
    assert dialog.completion_action == roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH


def test_roast_dialog_button_click_sets_completion_action() -> None:
    finish_button = object()
    continue_button = object()
    dialog = SimpleNamespace(
        dialogbuttons=SimpleNamespace(button=Mock(return_value=finish_button)),
        save_continue_cooling_button=continue_button,
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_ONLY,
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                timeindex=[0, 0, 0, 0, 0, 0, 60],
            )
        ),
    )

    roast_properties.editGraphDlg.roastDialogButtonClicked(dialog, continue_button)
    assert dialog.completion_action == roast_properties.COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING

    roast_properties.editGraphDlg.roastDialogButtonClicked(dialog, finish_button)
    assert dialog.completion_action == roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH


def test_finish_completed_roast_schedules_monitor_stop() -> None:
    emit = Mock()
    dialog = SimpleNamespace(
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                timeindex=[0, 0, 0, 0, 0, 0, 60],
                toggleMonitorSignal=SimpleNamespace(emit=emit),
            )
        ),
    )

    with patch('artisanlib.roast_properties.QTimer.singleShot', side_effect=lambda _ms, callback: callback()) as timer:
        roast_properties.editGraphDlg.finishCompletedRoastIfRequested(dialog)

    timer.assert_called_once_with(0, emit)
    emit.assert_called_once_with()


def test_continue_cooling_does_not_stop_monitoring() -> None:
    emit = Mock()
    dialog = SimpleNamespace(
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_CONTINUE_COOLING,
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                timeindex=[0, 0, 0, 0, 0, 0, 60],
                toggleMonitorSignal=SimpleNamespace(emit=emit),
            )
        ),
    )

    with patch('artisanlib.roast_properties.QTimer.singleShot') as timer:
        roast_properties.editGraphDlg.finishCompletedRoastIfRequested(dialog)

    timer.assert_not_called()
    emit.assert_not_called()


def test_stale_finish_action_does_not_stop_when_drop_is_removed() -> None:
    emit = Mock()
    dialog = SimpleNamespace(
        completion_action=roast_properties.COMPLETION_ACTION_SAVE_AND_FINISH,
        aw=SimpleNamespace(
            qmc=SimpleNamespace(
                flagstart=True,
                flagon=True,
                timeindex=[0, 0, 0, 0, 0, 0, 0],
                toggleMonitorSignal=SimpleNamespace(emit=emit),
            )
        ),
    )

    with patch('artisanlib.roast_properties.QTimer.singleShot') as timer:
        roast_properties.editGraphDlg.finishCompletedRoastIfRequested(dialog)

    timer.assert_not_called()
    emit.assert_not_called()


def test_close_ok_gates_completed_roast_message_for_inactive_profiles() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))

    close_ok = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == 'close_OK'
    )
    parents = {
        child: parent
        for parent in ast.walk(close_ok)
        for child in ast.iter_child_nodes(parent)
    }

    completed_message_call = next(
        node for node in ast.walk(close_ok)
        if (
            isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and
            node.func.attr == 'sendmessage' and
            node.args and
            isinstance(node.args[0], ast.Call) and
            isinstance(node.args[0].func, ast.Name) and
            node.args[0].func.id == 'completedRoastSaveMessage'
        )
    )
    guards = []
    parent = completed_message_call
    while parent in parents:
        parent = parents[parent]
        if isinstance(parent, ast.If):
            guards.append(ast.unparse(parent.test))

    assert 'Roast properties updated but profile not saved to disk' in source.read_text(encoding='utf-8')
    assert any('flagon' in guard and 'upload_queued' in guard for guard in guards)


def test_close_ok_calls_finish_after_cleanup() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))

    close_ok = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == 'close_OK'
    )
    call_lines = {}
    for node in ast.walk(close_ok):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        else:
            continue
        if name in {'clean_up', 'finishCompletedRoastIfRequested', 'hasRecordingBeans'}:
            call_lines[name] = node.lineno

    assert (
        call_lines['clean_up'] <
        call_lines['finishCompletedRoastIfRequested'] <
        call_lines['hasRecordingBeans']
    )


def test_roast_properties_uses_clear_manual_beans_and_temperature_labels() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    text = source.read_text(encoding='utf-8')
    title_tooltip = "QApplication.translate('Tooltip', 'Short name shown on the roast profile and lists')"
    beans_tooltip = (
        "QApplication.translate('Tooltip', "
        "'Manual green coffee description, origin, lot, or blend recipe')"
    )

    assert "QApplication.translate('Label', 'Roast Title')" in text
    assert f'titlelabel.setToolTip({title_tooltip})' in text
    assert f'self.titleedit.setToolTip({title_tooltip})' in text
    assert "QApplication.translate('Label', 'Title')" not in text
    assert "QApplication.translate('Label', 'Bean Description')" in text
    assert f'beanslabel.setToolTip({beans_tooltip})' in text
    assert f'self.beansedit.setToolTip({beans_tooltip})' in text
    assert "QApplication.translate('Label', 'Green Bean Temp')" in text
    assert 'temperature of the green coffee before CHARGE' in text


def test_roast_properties_uses_clear_inventory_and_template_labels() -> None:
    source = Path(__file__).parents[3] / 'artisanlib' / 'roast_properties.py'
    text = source.read_text(encoding='utf-8')
    no_inventory_link = "QApplication.translate('ComboBox', 'No inventory link')"

    assert "QApplication.translate('Label', 'Inventory')" in text
    assert "QApplication.translate('Label', 'Stock')" not in text
    assert text.count(no_inventory_link) == 4
    assert (
        "self.plus_coffees_combo.addItems("
        "[QApplication.translate('ComboBox', 'No inventory link')] + coffee_items)"
    ) in text
    assert (
        "self.plus_blends_combo.addItems("
        "[QApplication.translate('ComboBox', 'No inventory link')] + blend_items)"
    ) in text
    assert (
        "return [QApplication.translate('ComboBox', 'No inventory link')] + "
        "plus.stock.getCoffeesLabels(plus_coffees)"
    ) in text
    assert (
        "return [QApplication.translate('ComboBox', 'No inventory link')] + blend_items"
    ) in text
    assert "self.plus_stores_combo.addItems([''] + store_items)" in text
    assert "etypes = [''] +" in text
    assert "QApplication.translate('Button', 'Save Template')" in text
    assert "QApplication.translate('Button', 'Remove Template')" in text
    assert "QPushButton('+')" not in text
    assert "QPushButton('-')" not in text
    assert "QApplication.translate('CheckBox', 'Inventory label order')" in text
    assert 'Standard bean labels' not in text
