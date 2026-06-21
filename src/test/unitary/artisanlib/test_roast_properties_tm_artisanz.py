"""Focused TM-ArtisanZ roast properties behavior tests."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from artisanlib import roast_properties


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
