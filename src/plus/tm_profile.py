#
# tm_profile.py
#
# ABOUT
# Build the TM-ArtisanZ profile extension attached to the first roast upload.

import json
from typing import Any, Final


PROFILE_KEYS: Final[tuple[str, ...]] = (
    'roastUUID',
    'title',
    'beans',
    'operator',
    'roastertype',
    'mode',
    'roastepoch',
    'roastbatchnr',
    'roastbatchprefix',
    'roastbatchpos',
    'timex',
    'temp1',
    'temp2',
    'extratimex',
    'extratemp1',
    'extratemp2',
    'timeindex',
    'specialevents',
    'specialeventstype',
    'specialeventsvalue',
    'specialeventsStrings',
    'computed',
)

LIST_KEYS: Final[set[str]] = {
    'timex',
    'temp1',
    'temp2',
    'extratimex',
    'extratemp1',
    'extratemp2',
    'timeindex',
    'specialevents',
    'specialeventstype',
    'specialeventsvalue',
    'specialeventsStrings',
}


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _profile_from(app_window: Any) -> dict[str, Any]:
    if app_window is None or not hasattr(app_window, 'getProfile'):
        return {}
    profile = app_window.getProfile()
    if isinstance(profile, dict):
        return profile
    return {}


def serialize(app_window: Any) -> dict[str, Any]:
    profile = _profile_from(app_window)
    result: dict[str, Any] = {}

    for key in PROFILE_KEYS:
        if key in profile:
            result[key] = _json_safe(profile[key])
        elif key in LIST_KEYS:
            result[key] = []
        elif key == 'computed':
            result[key] = {}

    if not result.get('operator') and app_window is not None:
        qmc = getattr(app_window, 'qmc', None)
        operator = getattr(qmc, 'operator', None)
        if operator:
            result['operator'] = _json_safe(operator)

    return result
