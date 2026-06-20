#
# confirmed_upload.py
#
# ABOUT
# Helpers for user-confirmed first uploads to TM-ArtisanZ.

from typing import Any

from plus import config, queue, roast, tm_profile


def build_confirmed_roast_record(app_window: Any = None) -> dict[str, Any]:
    record = dict(roast.getRoast())
    record['tm_profile'] = tm_profile.serialize(
        config.app_window if app_window is None else app_window
    )
    return record


def add_confirmed_roast(app_window: Any = None, unsynced: bool = True) -> None:
    record = build_confirmed_roast_record(app_window)
    queue.addFullRoastRecord(record, unsynced=unsynced)
