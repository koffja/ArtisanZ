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
_MAX_OVERLAYS = 15


class ComparisonOverlay:
    """Manages semi-transparent historical roast curves on a pyqtgraph plot."""

    def __init__(self, temperature_plot: Any, pg: Any) -> None:
        self._plot = temperature_plot
        self._pg = pg
        self._curves: list[dict[str, Any]] = []
        self._distribution_item: Any | None = None

    def add_from_file(self, filepath: str) -> bool:
        """Load a .alog file and add its BT/ET curves as overlay.

        Returns True on success, False on failure.
        """
        if len(self._curves) >= _MAX_OVERLAYS:
            _log.warning('ComparisonOverlay: max %d overlays reached', _MAX_OVERLAYS)
            return False
        # Deduplicate: skip if already loaded
        filepath_abs = os.path.abspath(filepath)
        for entry in self._curves:
            if entry.get('filepath') == filepath_abs:
                _log.info('ComparisonOverlay: already loaded %s, skipping', filepath)
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

        # Normalize time to start at 0, using min length to avoid misalignment
        try:
            n = min(len(time_data), len(temp2), len(temp1) if temp1 else len(time_data))
            if n == 0:
                _log.warning('ComparisonOverlay: empty data in %s', filepath)
                return False
            t0 = float(time_data[0])
            time_norm = [float(time_data[i]) - t0 for i in range(n)]
            bt_y = [float(temp2[i]) for i in range(n)]
            et_y = [float(temp1[i]) for i in range(n)] if temp1 and len(temp1) >= n else []
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
        self._curves.append({'bt': bt_item, 'et': et_item, 'label': label, 'filepath': filepath_abs})
        _log.info('ComparisonOverlay: added %s (BT=%d pts)', label, len(bt_y))
        return True

    def clear(self) -> None:
        """Remove all overlay curves and distribution."""
        self.hide_distribution()
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

    def show_distribution(self) -> bool:
        """Compute and display a BoxplotItem distribution from loaded roasts.

        Requires at least 2 loaded roasts. Returns True on success.
        """
        self.hide_distribution()
        if self.count < 2:
            _log.info('ComparisonOverlay: need >= 2 roasts for distribution')
            return False
        try:
            import numpy as np
        except ImportError:
            return False

        # Collect BT data arrays from overlay curves
        all_bt: list[tuple[list[float], list[float]]] = []
        max_time = 0.0
        for entry in self._curves:
            bt_item = entry.get('bt')
            if bt_item is None:
                continue
            x_data, y_data = self._extract_data(bt_item)
            if not x_data or not y_data:
                continue
            all_bt.append((x_data, y_data))
            max_time = max(max_time, max(x_data))

        if len(all_bt) < 2:
            return False

        # Common time points: every 30 seconds from 0 to max_time
        step = 30.0
        time_points = list(range(0, int(max_time) + int(step), int(step)))
        if len(time_points) < 3:
            return False

        # Interpolate each roast's BT to common time points
        y_values: list[np.ndarray] = []
        for t in time_points:
            values: list[float] = []
            for x_data, y_data in all_bt:
                try:
                    v = float(np.interp(float(t), x_data, y_data))
                    values.append(v)
                except Exception:
                    pass
            if len(values) >= 2:
                y_values.append(np.array(values))
            else:
                y_values.append(np.array([]))

        # Filter out empty entries
        valid_x = [time_points[i] for i in range(len(y_values)) if len(y_values[i]) >= 2]
        valid_y = [y_values[i] for i in range(len(y_values)) if len(y_values[i]) >= 2]
        if len(valid_x) < 3:
            return False

        try:
            bp = self._pg.BoxplotItem(
                x=valid_x,
                y=valid_y,
                pen=self._pg.mkPen(100, 120, 130, 60, width=0.5),
                brush=self._pg.mkBrush(144, 161, 168, 25),
            )
            _call_if_available(bp, 'setZValue', 3)
            self._plot.addItem(bp)
            self._distribution_item = bp
            _log.info('ComparisonOverlay: distribution shown (%d boxes from %d roasts)', len(valid_x), len(all_bt))
            return True
        except Exception:
            _log.warning('ComparisonOverlay: BoxplotItem creation failed', exc_info=True)
            return False

    def hide_distribution(self) -> None:
        """Remove the distribution BoxplotItem if present."""
        if self._distribution_item is not None:
            try:
                self._plot.removeItem(self._distribution_item)
            except Exception:
                pass
            self._distribution_item = None

    @staticmethod
    def _extract_data(item: Any) -> tuple[list[float], list[float]]:
        """Extract x/y data arrays from a PlotDataItem."""
        try:
            result = item.getData()
            if result and len(result) >= 2:
                return list(result[0]), list(result[1])
        except Exception:
            pass
        return [], []

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
