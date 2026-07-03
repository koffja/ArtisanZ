"""Visual enhancement overlays for the pyqtgraph roasting curve renderer.

Each overlay is self-contained, gracefully degrades on error, and uses
colors from DEFAULT_GRAPH_PALETTE to stay consistent with the ArtisanZ theme.
"""
from __future__ import annotations

import logging
from typing import Any, Protocol

_log = logging.getLogger(__name__)


class _SupportsAddRemove(Protocol):
    def addItem(self, item: object) -> None: ...
    def removeItem(self, item: object) -> None: ...
    def listDataItems(self) -> list[object]: ...
    def getViewBox(self) -> object: ...


# ---------------------------------------------------------------------------
# Task 5: Curve shadow pen
# ---------------------------------------------------------------------------

_SHADOW_WIDTH_RATIO = 2.0  # shadow pen is 2x the main pen width
_SHADOW_ALPHA = 90          # 0-255; ~35% opacity


def apply_shadow_pens(
    plot: Any,
    pg: Any,
    *,
    shadow_color: str = '#000000',
    shadow_alpha: int = _SHADOW_ALPHA,
) -> int:
    """Apply a shadow pen to every PlotDataItem on *plot* that has a visible pen.

    Returns the number of curves enhanced.
    """
    count = 0
    try:
        data_items = _safe_list_data_items(plot)
    except Exception:
        _log.warning('apply_shadow_pens: failed to enumerate data items')
        return 0

    for item in data_items:
        try:
            opts = getattr(item, 'opts', None)
            if not isinstance(opts, dict):
                continue
            pen = opts.get('pen')
            if pen is None:
                continue
            pen_width = _extract_pen_width(pen)
            if pen_width <= 0:
                continue
            shadow_width = max(int(pen_width * _SHADOW_WIDTH_RATIO), pen_width + 2)
            shadow_pen = pg.mkPen(shadow_color, width=shadow_width)
            # Apply alpha by setting a semi-transparent cosmetic pen
            _set_pen_alpha(shadow_pen, shadow_alpha)
            item.setShadowPen(shadow_pen)
            count += 1
        except Exception:
            _log.debug('apply_shadow_pens: skipped item %r', item, exc_info=True)

    return count


def clear_shadow_pens(plot: Any) -> None:
    """Remove shadow pens from all PlotDataItem children of *plot*."""
    try:
        data_items = _safe_list_data_items(plot)
    except Exception:
        return
    for item in data_items:
        try:
            item.setShadowPen(None)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Task 3: ROR area fill (FillBetweenItem)
# ---------------------------------------------------------------------------

class RORFillOverlay:
    """Manages a FillBetweenItem between the RoR curve and a zero baseline."""

    def __init__(
        self,
        ror_view_box: Any,
        pg: Any,
        *,
        fill_rgba: tuple[int, int, int, int] = (144, 161, 168, 60),
    ) -> None:
        self._ror_view_box = ror_view_box
        self._pg = pg
        self._fill_rgba = fill_rgba
        self._zero_curve: Any | None = None
        self._fill_item: Any | None = None
        self._ror_curve: Any | None = None

    def attach(self, ror_curve: Any) -> None:
        """Attach the fill overlay below *ror_curve*."""
        self.detach()
        try:
            self._ror_curve = ror_curve
            self._zero_curve = self._pg.PlotDataItem([], [], pen=None)
            self._fill_item = self._pg.FillBetweenItem(
                curve1=ror_curve,
                curve2=self._zero_curve,
                brush=self._pg.mkBrush(*self._fill_rgba),
            )
            self._ror_view_box.addItem(self._fill_item)
            self._ror_view_box.addItem(self._zero_curve)
        except Exception:
            _log.warning('RORFillOverlay.attach failed', exc_info=True)
            self._fill_item = None
            self._zero_curve = None
            self._ror_curve = None

    def update_baseline(self, x_data: list[float]) -> None:
        """Sync the zero baseline to the current x range."""
        if self._zero_curve is not None and x_data:
            try:
                self._zero_curve.setData(x_data, [0.0] * len(x_data))
            except Exception:
                _log.debug('RORFillOverlay.update_baseline failed', exc_info=True)

    def detach(self) -> None:
        for attr in ('_fill_item', '_zero_curve'):
            item = getattr(self, attr, None)
            if item is not None:
                try:
                    self._ror_view_box.removeItem(item)
                except Exception:
                    pass
                setattr(self, attr, None)
        self._ror_curve = None


# ---------------------------------------------------------------------------
# Task 1: Roasting phase bands (LinearRegionItem)
# ---------------------------------------------------------------------------

_PHASE_COLORS: dict[str, tuple[int, int, int, int]] = {
    'drying':      (255, 220, 100, 35),
    'maillard':    (255, 150, 80, 35),
    'development': (255, 80, 80, 35),
}


class PhaseBandOverlay:
    """Manages translucent LinearRegionItem bands for roasting phases."""

    def __init__(self, temperature_plot: Any, pg: Any) -> None:
        self._plot = temperature_plot
        self._pg = pg
        self._regions: list[Any] = []

    def update_phases(
        self,
        phase_bounds: dict[str, tuple[float, float] | None],
    ) -> None:
        """Update or recreate phase bands.

        ``phase_bounds`` example::

            {'drying': (0.0, 300.0), 'maillard': (300.0, 480.0), 'development': (480.0, 720.0)}

            Pass ``None`` for a phase that does not exist yet.
        """
        self.clear()
        for name, bounds in phase_bounds.items():
            if bounds is None:
                continue
            t0, t1 = bounds
            if t0 is None or t1 is None or t1 <= t0:
                continue
            rgba = _PHASE_COLORS.get(name, (200, 200, 200, 30))
            try:
                region = self._pg.LinearRegionItem(
                    values=[float(t0), float(t1)],
                    orientation='vertical',
                    brush=self._pg.mkBrush(*rgba),
                    pen=self._pg.mkPen(rgba[0], rgba[1], rgba[2], 100, width=1),
                    movable=True,
                    swapMode='block',
                )
                self._plot.addItem(region)
                self._regions.append(region)
            except Exception:
                _log.debug('PhaseBandOverlay: failed to add %s band', name, exc_info=True)

    def clear(self) -> None:
        for region in self._regions:
            try:
                self._plot.removeItem(region)
            except Exception:
                pass
        self._regions.clear()


# ---------------------------------------------------------------------------
# Task 4: Draggable event markers (InfiniteLine)
# ---------------------------------------------------------------------------

_EVENT_COLORS: dict[str, str] = {
    'CHARGE': '#4CAF50',
    'DRY':    '#FF9800',
    'FCs':    '#F44336',
    'FCe':    '#E91E63',
    'SCs':    '#9C27B0',
    'SCe':    '#673AB7',
    'DROP':   '#795548',
}


class EventMarkerOverlay:
    """Manages draggable InfiniteLine markers for roasting events."""

    def __init__(self, temperature_plot: Any, pg: Any) -> None:
        self._plot = temperature_plot
        self._pg = pg
        self._lines: dict[str, Any] = {}

    def update_events(
        self,
        events: list[dict[str, Any]],
    ) -> None:
        """Synchronise event markers.

        Each event dict should have keys ``code`` (str), ``time`` (float|None),
        and optionally ``temp`` (float|None).
        """
        current_codes = {e['code'] for e in events if 'code' in e}
        for code in list(self._lines):
            if code not in current_codes:
                self._remove(code)

        for event in events:
            code = event.get('code')
            if not code:
                continue
            time_val = event.get('time')
            if time_val is None:
                continue
            temp_val = event.get('temp')
            color = _EVENT_COLORS.get(code, '#888888')
            label_text = code
            if temp_val is not None:
                label_text += f' {temp_val:.0f}\u00b0C'

            existing = self._lines.get(code)
            if existing is not None:
                try:
                    existing.setValue(float(time_val))
                except Exception:
                    pass
                continue

            try:
                from PyQt6.QtCore import Qt
                line = self._pg.InfiniteLine(
                    pos=float(time_val),
                    angle=90,
                    pen=self._pg.mkPen(color, width=2, style=Qt.PenStyle.DashLine),
                    movable=True,
                    labelOpts={
                        'position': 0.95,
                        'color': color,
                        'fill': (0xFF, 0xFF, 0xFF, 0xC8),
                        'movable': True,
                    },
                )
                self._plot.addItem(line)
                self._lines[code] = line
            except Exception:
                _log.debug('EventMarkerOverlay: failed to add %s', code, exc_info=True)

    def _remove(self, code: str) -> None:
        line = self._lines.pop(code, None)
        if line is not None:
            try:
                self._plot.removeItem(line)
            except Exception:
                pass

    def clear(self) -> None:
        for code in list(self._lines):
            self._remove(code)




# ---------------------------------------------------------------------------
# Task 2: BT curve gradient coloring (ColorMap.getPen)
# ---------------------------------------------------------------------------

def create_gradient_pen(
    pg: Any,
    *,
    temp_min: float = 150.0,
    temp_max: float = 250.0,
    width: int = 2,
    cmap_name: str = 'CET-L17',
) -> Any:
    """Create a QPen whose colour varies along the Y-axis by temperature.

    Falls back to a solid pen if the colour map cannot be loaded.
    """
    try:
        cm = pg.colormap.get(cmap_name)
        cm.reverse()
        return cm.getPen(span=(temp_min, temp_max), width=width, orientation='vertical')
    except Exception:
        _log.debug('create_gradient_pen: fallback to solid pen', exc_info=True)
        return pg.mkPen('#4E7180', width=width)


def apply_gradient_to_curves(
    plot: Any,
    pg: Any,
    *,
    temp_min: float = 150.0,
    temp_max: float = 250.0,
    cmap_name: str = 'CET-L17',
) -> int:
    """Apply gradient pens to all PlotDataItem children of *plot*.

    Returns the number of curves enhanced.
    """
    gradient_pen = create_gradient_pen(
        pg, temp_min=temp_min, temp_max=temp_max, width=2, cmap_name=cmap_name,
    )
    count = 0
    try:
        data_items = _safe_list_data_items(plot)
    except Exception:
        return 0
    for item in data_items:
        try:
            opts = getattr(item, 'opts', None)
            if isinstance(opts, dict) and opts.get('pen') is not None:
                item.setPen(gradient_pen)
                count += 1
        except Exception:
            _log.debug('apply_gradient_to_curves: skipped item', exc_info=True)
    return count


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_list_data_items(plot: Any) -> list[Any]:
    """Return ``plot.listDataItems()`` if available, else walk ``plot.items()``."""
    list_data_items = getattr(plot, 'listDataItems', None)
    if callable(list_data_items):
        return list(list_data_items())
    items_method = getattr(plot, 'items', None)
    if callable(items_method):
        return [item for item in items_method() if hasattr(item, 'setShadowPen')]
    return []


def _extract_pen_width(pen: Any) -> int:
    """Best-effort extraction of pen width from a QPen or dict."""
    width_fn = getattr(pen, 'width', None)
    if callable(width_fn):
        try:
            return int(width_fn())
        except (TypeError, ValueError):
            return 1
    if isinstance(pen, dict):
        return int(pen.get('width', 1))
    if isinstance(pen, (int, float)):
        return int(pen)
    return 1


def _set_pen_alpha(pen: Any, alpha: int) -> None:
    """Set the alpha channel of *pen* colour to *alpha* (0-255)."""
    try:
        color = getattr(pen, 'color', None)
        if color is not None:
            color.setAlpha(max(0, min(255, alpha)))
    except Exception:
        pass
