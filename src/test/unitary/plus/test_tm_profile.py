"""Focused tests for TM-ArtisanZ profile serialization."""

import json
from typing import Any
from unittest.mock import Mock

from plus import tm_profile


def test_serialize_returns_json_serializable_profile_with_curves_and_events() -> None:
    profile: dict[str, Any] = {
        'roastUUID': 'abc123',
        'title': 'Colombia Test',
        'beans': 'Colombia Supremo',
        'operator': 'Ada',
        'roastertype': 'Sample Roaster',
        'mode': 'C',
        'roastepoch': 1782000000.0,
        'roastbatchnr': 42,
        'roastbatchprefix': 'TM',
        'roastbatchpos': 3,
        'timex': [0.0, 30.0, 60.0],
        'temp1': [160.0, 165.0, 170.0],
        'temp2': [180.0, 185.0, 190.0],
        'extratimex': [[0.0, 30.0]],
        'extratemp1': [[30.0, 31.0]],
        'extratemp2': [[40.0, 41.0]],
        'timeindex': [0, -1, -1, -1, -1, -1, 60, -1],
        'specialevents': [15.0],
        'specialeventstype': [1],
        'specialeventsvalue': [50],
        'specialeventsStrings': ['Gas +5'],
        'computed': {'DROP_time': 60.0},
    }
    app_window = Mock()
    app_window.getProfile.return_value = profile
    app_window.qmc = Mock()
    app_window.qmc.operator = 'Ada'

    result = tm_profile.serialize(app_window)

    assert result['roastUUID'] == 'abc123'
    assert result['timex'] == [0.0, 30.0, 60.0]
    assert result['temp1'] == [160.0, 165.0, 170.0]
    assert result['temp2'] == [180.0, 185.0, 190.0]
    assert result['timeindex'][6] == 60
    assert result['computed'] == {'DROP_time': 60.0}
    json.dumps(result)


def test_serialize_uses_qmc_operator_when_profile_operator_is_missing() -> None:
    app_window = Mock()
    app_window.getProfile.return_value = {'roastUUID': 'abc123'}
    app_window.qmc = Mock()
    app_window.qmc.operator = 'Grace'

    result = tm_profile.serialize(app_window)

    assert result['operator'] == 'Grace'
