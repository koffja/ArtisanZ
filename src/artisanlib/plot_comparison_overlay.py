"""Historical roast curve overlay for pyqtgraph renderer.

Loads .alog files and renders their BT/ET curves as semi-transparent
overlays on the main pyqtgraph temperature plot, enabling visual
comparison between the current roast and past roasts.
"""
from __future__ import annotations

import logging
import os
from typing import Any

_log = logging.getLogger(__name__)

_OVERLAY_BT_COLOR = (144, 161, 168)   # DeltaBT palette
_OVERLAY_ET_COLOR = (193, 138, 107)   # DeltaET palette
_OVERLAY_ALPHA = 70                    # ~27% opacity
_OVERLAY_WIDTH = 1
_OVERLAY_Z = 5                         # behind main curves (z=10)
_MAX_OVERLAYS = 10


class ComparisonOverlay:
    """Manages semi-transparent historical roast curves on a pyqtgraph plot."""

    def __init__(self, temperature_plot: Any, pg: Any) -> None:
        self._plot = temperature_plot
        self._pg = pg
        self._curves: list[dict[str, Any]] = []

    def add_from_file(self, filepath: str) -> bool:
        """Load a .alog file and add its BT/ET curves as overlay.

        Returns True on success, False on failure.
        """
        if len(self._curves) >= _MAX_OVERLAYS:
            _log.warning('ComparisonOverlay: max %d overlays reached', _MAX_OVERLAYS)
            return False
        if not os.path.isfile(filepath):
            _log.warning('ComparisonOverlay: file not found: %s', filepath)
            return False
        try:
            from artisanlib.util import deserialize
            profile = deserialize(filepath)
        except Exception:
            _log.warning('ComparisonOverlay: failed to deserialize %s', filepath, exc_info=True)
            return False

        time_data = profile.get('time', [])
        temp1 = profile.get('temp1', [])
        temp2 = profile.get('temp2', [])
        if not time_data or not temp2:
            _log.warning('ComparisonOverlay: no BT data in %s', filepath)
            return False

        # Normalize time to start at 0
        try:
            t0 = float(time_data[0]) if time_data else 0.0
            time_norm = [float(t) - t0 for t in time_data]
            bt_y = [float(v) for v in temp2[:len(time_norm)]]
            et_y = [float(v) for v in temp1[:len(time_norm)]] if temp1 else []
        except (TypeError, ValueError, IndexError):
            _log.warning('ComparisonOverlay: data conversion failed for %s', filepath)
            return False

        bt_pen = self._pg.mkPen(*_OVERLAY_BT_COLOR, _OVERLAY_ALPHA, width=_OVERLAY_WIDTH)
        bt_item = self._pg.PlotDataItem(time_norm, bt_y, pen=bt_pen)
        _call_if_available(bt_item, 'setZValue', _OVERLAY_Z)
        self._plot.addItem(bt_item)

        et_item = None
        if et_y:
            et_pen = self._pg.mkPen(*_OVERLAY_ET_COLOR, _OVERLAY_ALPHA, width=_OVERLAY_WIDTH)
            et_item = self._pg.PlotDataItem(time_norm, et_y, pen=et_pen)
            _call_if_available(et_item, 'setZValue', _OVERLAY_Z)
            self._plot.addItem(et_item)

        label = os.path.basename(filepath)
        self._curves.append({'bt': bt_item, 'et': et_item, 'label': label})
        _log.info('ComparisonOverlay: added %s (BT=%d pts)', label, len(bt_y))
        return True

    def clear(self) -> None:
        """Remove all overlay curves."""
        for entry in self._curves:
            for key in ('bt', 'et'):
                item = entry.get(key)
                if item is not None:
                    try:
                        self._plot.removeItem(item)
                    except Exception:
                        pass
        self._curves.clear()

    def set_visible(self, visible: bool) -> None:
        """Show or hide all overlay curves without removing them."""
        for entry in self._curves:
            for key in ('bt', 'et'):
                item = entry.get(key)
                if item is not None:
                    _call_if_available(item, 'setVisible', visible)

    @property
    def count(self) -> int:
        return len(self._curves)

    @property
    def labels(self) -> list[str]:
        return [e['label'] for e in self._curves]


def _call_if_available(obj: Any, method_name: str, *args: Any) -> None:
    method = getattr(obj, method_name, None)
    if callable(method):
        try:
            method(*args)
        except Exception:
            pass
