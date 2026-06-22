"""Focused tests for confirmed full roast uploads."""

from typing import Any
from unittest.mock import Mock, patch

with patch('artisanlib.util.getDirectory', return_value='/test/cache/path'):
    from plus import confirmed_upload, queue


def _writable_app_window() -> Mock:
    app_window = Mock()
    app_window.plus_readonly = False
    app_window.sendmessage = Mock()
    return app_window


def _running_queue() -> Mock:
    running_queue = Mock()
    running_queue.qsize.return_value = 1
    return running_queue


def test_build_confirmed_roast_record_keeps_full_payload_and_adds_tm_profile() -> None:
    base_roast: dict[str, Any] = {
        'roast_id': 'abc123',
        'date': '2026-06-21T10:00:00.000Z',
        'amount': 1.2,
        'label': 'Batch 42',
    }
    profile = {'roastUUID': 'abc123', 'timex': [0.0], 'temp1': [160.0], 'temp2': [180.0]}

    with patch('plus.confirmed_upload.roast.getRoast', return_value=base_roast), patch(
        'plus.confirmed_upload.tm_profile.serialize', return_value=profile
    ):
        result = confirmed_upload.build_confirmed_roast_record(Mock())

    assert result is not base_roast
    assert result['roast_id'] == 'abc123'
    assert result['date'] == '2026-06-21T10:00:00.000Z'
    assert result['amount'] == 1.2
    assert result['tm_profile'] == profile


def test_add_confirmed_roast_queues_full_record_without_diffing() -> None:
    record: dict[str, Any] = {
        'roast_id': 'abc123',
        'date': '2026-06-21T10:00:00.000Z',
        'amount': 1.2,
        'tm_profile': {'roastUUID': 'abc123'},
    }

    with patch(
        'plus.confirmed_upload.build_confirmed_roast_record', return_value=record
    ) as mock_build, patch('plus.confirmed_upload.queue.addFullRoastRecord') as mock_add_full:
        confirmed_upload.add_confirmed_roast(Mock(), unsynced=True)

    mock_build.assert_called_once()
    mock_add_full.assert_called_once_with(record, unsynced=True)


def test_add_full_roast_record_bypasses_sync_diff_and_preserves_tm_profile() -> None:
    record: dict[str, Any] = {
        'roast_id': 'abc123',
        'date': '2026-06-21T10:00:00.000Z',
        'amount': 1.2,
        'tm_profile': {'roastUUID': 'abc123', 'timex': [0.0]},
    }
    app_window = _writable_app_window()

    with patch.object(queue.config, 'app_window', app_window), patch.object(
        queue, 'queue', _running_queue()
    ), patch.object(queue.sync, 'diffCachedSyncRecord') as mock_diff, patch.object(
        queue.sync, 'suppress_zero_values', side_effect=lambda r: r
    ) as mock_suppress, patch.object(queue, 'queue_roast_item', return_value=True) as mock_queue:
        queue.addFullRoastRecord(record, unsynced=False)

    mock_diff.assert_not_called()
    mock_suppress.assert_called_once()
    queued_record = mock_queue.call_args.args[0]
    assert queued_record['roast_id'] == 'abc123'
    assert queued_record['date'] == '2026-06-21T10:00:00.000Z'
    assert queued_record['amount'] == 1.2
    assert queued_record['tm_profile'] == {'roastUUID': 'abc123', 'timex': [0.0]}


def test_add_roast_attaches_tm_profile_to_regular_full_upload() -> None:
    base_roast: dict[str, Any] = {
        'roast_id': 'abc123',
        'date': '2026-06-21T10:00:00.000Z',
        'amount': 1.2,
    }
    profile = {
        'roastUUID': 'abc123',
        'timex': [0.0, 1.0],
        'temp1': [160.0, 161.0],
        'temp2': [180.0, 181.0],
        'timeindex': [0, 1],
        'computed': {'bt_ror': [0.0, 1.0]},
    }
    app_window = _writable_app_window()

    with patch.object(queue.config, 'app_window', app_window), patch.object(
        queue, 'queue', _running_queue()
    ), patch.object(queue.roast, 'getRoast', return_value=base_roast), patch.object(
        queue.tm_profile, 'serialize', return_value=profile
    ) as mock_serialize, patch.object(
        queue.sync, 'suppress_zero_values', side_effect=lambda r: r
    ), patch.object(queue, 'queue_roast_item', return_value=True) as mock_queue:
        queued = queue.addRoast(unsynced=False)

    assert queued is True
    mock_serialize.assert_called_once_with(app_window)
    queued_record = mock_queue.call_args.args[0]
    assert queued_record['tm_profile'] == profile
    assert queued_record['tm_profile']['timex'] == [0.0, 1.0]
    assert queued_record['tm_profile']['temp1'] == [160.0, 161.0]
    assert queued_record['tm_profile']['temp2'] == [180.0, 181.0]
    assert queued_record['tm_profile']['timeindex'] == [0, 1]
    assert queued_record['tm_profile']['computed'] == {'bt_ror': [0.0, 1.0]}


def test_add_roast_attaches_tm_profile_to_regular_sync_update() -> None:
    sync_record: dict[str, Any] = {'roast_id': 'abc123', 'label': 'Updated'}
    profile = {'roastUUID': 'abc123', 'timex': [0.0], 'temp1': [160.0]}
    app_window = _writable_app_window()

    with patch.object(queue.config, 'app_window', app_window), patch.object(
        queue, 'queue', _running_queue()
    ), patch.object(
        queue.tm_profile, 'serialize', return_value=profile
    ), patch.object(
        queue.sync, 'diffCachedSyncRecord', side_effect=lambda r: r
    ) as mock_diff, patch.object(
        queue.sync, 'suppress_zero_values', side_effect=lambda r: r
    ), patch.object(queue, 'queue_roast_item', return_value=True) as mock_queue:
        queued = queue.addRoast(sync_record, unsynced=False)

    assert queued is True
    diff_input = mock_diff.call_args.args[0]
    assert diff_input['tm_profile'] == profile
    queued_record = mock_queue.call_args.args[0]
    assert queued_record['tm_profile'] == profile


def test_add_roast_returns_false_when_queue_roast_item_rejects_record() -> None:
    base_roast: dict[str, Any] = {
        'roast_id': 'abc123',
        'date': '2026-06-21T10:00:00.000Z',
        'amount': 1.2,
    }
    app_window = _writable_app_window()

    with patch.object(queue.config, 'app_window', app_window), patch.object(
        queue, 'queue', _running_queue()
    ), patch.object(queue.roast, 'getRoast', return_value=base_roast), patch.object(
        queue.tm_profile, 'serialize', return_value={'roastUUID': 'abc123'}
    ), patch.object(
        queue.sync, 'suppress_zero_values', side_effect=lambda r: r
    ), patch.object(queue, 'queue_roast_item', return_value=False):
        queued = queue.addRoast(unsynced=False)

    assert queued is False


def test_add_roast_returns_false_when_mandatory_full_record_data_is_missing() -> None:
    app_window = _writable_app_window()

    with patch.object(queue.config, 'app_window', app_window), patch.object(
        queue, 'queue', _running_queue()
    ), patch.object(
        queue.roast, 'getRoast', return_value={'roast_id': 'abc123', 'date': '2026-06-21T10:00:00.000Z'}
    ), patch.object(
        queue.tm_profile, 'serialize', return_value={'roastUUID': 'abc123'}
    ), patch.object(queue, 'queue_roast_item') as mock_queue:
        queued = queue.addRoast(unsynced=False)

    assert queued is False
    mock_queue.assert_not_called()


def test_add_roast_returns_false_when_queue_is_stopped() -> None:
    app_window = _writable_app_window()

    with patch.object(queue.config, 'app_window', app_window), patch.object(queue, 'queue', None), patch.object(
        queue, 'queue_roast_item'
    ) as mock_queue:
        queued = queue.addRoast({'roast_id': 'abc123'}, unsynced=False)

    assert queued is False
    mock_queue.assert_not_called()


def test_add_roast_returns_false_for_readonly_account() -> None:
    app_window = _writable_app_window()
    app_window.plus_readonly = True

    with patch.object(queue.config, 'app_window', app_window), patch.object(
        queue, 'queue', _running_queue()
    ), patch.object(queue, 'queue_roast_item') as mock_queue:
        queued = queue.addRoast({'roast_id': 'abc123'}, unsynced=False)

    assert queued is False
    mock_queue.assert_not_called()
