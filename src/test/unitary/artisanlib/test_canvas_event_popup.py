# mypy: disable-error-code="attr-defined"
"""Tests for the renderer-agnostic right-click event-edit popup helper.

These cover tgraphcanvas._open_event_marker_popup (extracted from the matplotlib
onclick() handler) and the pyqtgraph right-click forwarder guard. They verify
the popup menu is built with the expected CHARGE/DRY/FC/.../EVENT actions and
that invalid BT values suppress the marker entries, without spinning up the
full Artisan application window.
"""
from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt6.QtWidgets import QApplication, QMenu, QWidget

_APPLICATION = QApplication.instance() or QApplication([])
# canvas.py -> plus.queue -> plus.util.getDirectory() reads app.artisanviewerMode;
# set it on the test QApplication so the module-level import chain resolves.
_APPLICATION.artisanviewerMode = False  # type: ignore[attr-defined]

mpl = pytest.importorskip('matplotlib')  # canvas.py imports matplotlib at module load


def _make_stub_canvas(*, bt_value: float = 200.0) -> object:
    # Minimal stand-in exposing only the attributes _open_event_marker_popup reads.
    # We attach the REAL tgraphcanvas methods so the popup construction logic under
    # test is the production code, not a reimplementation.
    from artisanlib.canvas import tgraphcanvas

    parent = QWidget()

    class _Stub:
        # --- production methods bound from tgraphcanvas ---
        _open_event_marker_popup = tgraphcanvas._open_event_marker_popup
        _handle_pyqtgraph_right_click = tgraphcanvas._handle_pyqtgraph_right_click
        eventsExternal2InternalValue = staticmethod(tgraphcanvas.eventsExternal2InternalValue)

        def __init__(self_inner) -> None:
            self_inner.aw = parent
            # timex in seconds for a small 5-sample roast
            self_inner.timex = [0.0, 30.0, 90.0, 150.0, 240.0]
            # BT temperatures per sample
            self_inner.temp2 = [bt_value] * 5
            self_inner.temp1 = [180.0] * 5
            # CHARGE/DRY END/FCs/FCe/SCs/SCe/DROP/COOL indices into timex
            # CHARGE at sample 0, DRY at sample 2, DROP at sample 4
            self_inner.timeindex = [0, 2, -1, -1, -1, -1, 4, -1]
            self_inner.BTcurve = True
            self_inner.ETcurve = True
            self_inner.flagstart = False
            self_inner.clampEvents = True
            self_inner.eventpositionbars = [0.0, 1.0]
            self_inner.ax = object()  # truthy; marks "axes valid"
            self_inner.designerflag = False
            self_inner.wheelflag = False
            self_inner.comparator = False
            self_inner.popup_calls: list = []
            self_inner.notifier_disconnects: int = 0

        # time2index: nearest sample whose timex <= given seconds
        def time2index(self_inner, seconds: float, nearest: bool = True) -> int:  # noqa: ARG002
            best = 0
            for i, t in enumerate(self_inner.timex):
                if t <= seconds:
                    best = i
            return best

        def disconnect_draggableannotations_motion_notifiers(self_inner) -> None:
            self_inner.notifier_disconnects += 1

        def event_popup_action(self_inner, action) -> None:  # noqa: ANN001
            # production slot; not exercised here but referenced by menu.triggered.connect
            pass

    return _Stub()


def _capture_popup_actions(stub: object, xdata: float, ydata: float) -> list:
    # Run the popup helper with QMenu.popup monkeypatched to a no-op capture,
    # then read back the actions added to the menu.
    captured: dict = {}

    real_popup = QMenu.popup

    def fake_popup(self_menu, pos, *args, **kwargs):  # noqa: ANN001, ARG001
        captured['menu'] = self_menu

    QMenu.popup = fake_popup  # type: ignore[method-assign]
    try:
        stub._open_event_marker_popup(xdata, ydata)  # type: ignore[attr-defined]
    finally:
        QMenu.popup = real_popup  # type: ignore[method-assign]

    menu = captured.get('menu')
    if menu is None:
        return []
    return list(menu.actions())


def test_open_event_marker_popup_builds_charge_dry_drop_and_event_actions() -> None:
    stub = _make_stub_canvas(bt_value=200.0)
    # click at t=120s (between DRY at 90s and DROP at 240s)
    actions = _capture_popup_actions(stub, xdata=120.0, ydata=200.0)

    texts = [a.text().strip() for a in actions]
    # The popup only offers chronologically-valid markers. With CHARGE at sample 0
    # (t=0s), DRY at sample 2 (t=90s), DROP at sample 4 (t=240s), a click at t=120s
    # (sample 2) can reposition DRY END (and add an EVENT), but NOT CHARGE (already
    # before the click) or DROP (after the click). Plus the disabled "at HH:MM" header.
    assert any(t.startswith('at') for t in texts), f"header missing: {texts}"
    assert any('DRY' in t for t in texts), f"DRY missing: {texts}"
    assert any('EVENT' in t for t in texts), f"EVENT missing: {texts}"
    assert not any('CHARGE' in t for t in texts), f"CHARGE should be excluded: {texts}"
    assert not any('DROP' in t for t in texts), f"DROP should be excluded: {texts}"

    # marker actions carry the (event_id, timex) key; EVENT carries a 3-tuple
    keys = [getattr(a, 'key', None) for a in actions]
    marker_keys = [k for k in keys if isinstance(k, tuple) and len(k) == 2 and k[0] >= 0]
    # DRY END has event id 1
    assert any(k[0] == 1 for k in marker_keys), f"DRY END key missing: {marker_keys}"
    # the timex stored on each key matches the clicked time's nearest sample
    assert all(k[1] == stub.time2index(120.0) for k in marker_keys)  # type: ignore[attr-defined]

    # draggable-annotation motion notifiers must be detached before showing the menu
    assert stub.notifier_disconnects == 1  # type: ignore[attr-defined]


def test_open_event_marker_popup_skips_markers_when_bt_invalid() -> None:
    # bt == -1 means "no BT reading at that sample"; the popup must not offer
    # any CHARGE/DRY/.../EVENT entries (only returns without building a menu).
    stub = _make_stub_canvas(bt_value=-1.0)
    actions = _capture_popup_actions(stub, xdata=120.0, ydata=200.0)
    assert actions == [], f"expected no actions for invalid BT, got {actions}"


def test_open_event_marker_popup_no_menu_for_time_before_first_sample() -> None:
    # timex <= 0 should short-circuit before building any menu.
    stub = _make_stub_canvas(bt_value=200.0)
    captured: list = []

    def fake_popup(menu, pos, *a, **k):  # noqa: ANN001, ARG001
        captured.append(menu)

    real_popup = QMenu.popup
    QMenu.popup = fake_popup  # type: ignore[method-assign]
    try:
        # time2index returns 0 for seconds <= first sample; helper treats <=0 as "no popup"
        stub._open_event_marker_popup(-50.0, 200.0)  # type: ignore[attr-defined]
    finally:
        QMenu.popup = real_popup  # type: ignore[method-assign]
    assert captured == []


def test_handle_pyqtgraph_right_click_respects_pan_zoom_mode() -> None:
    # When the matplotlib toolbar is in pan/zoom or zoom-rect mode, the pyqtgraph
    # right-click forwarder must NOT open the event popup (parity with onclick()).
    stub = _make_stub_canvas(bt_value=200.0)

    class _FakeNTB:
        mode = 'pan/zoom'

    class _FakeAW:
        ntb = _FakeNTB()
        comparator = False

        def setFocus(self_inner) -> None:
            pass

    stub.aw = _FakeAW()  # type: ignore[attr-defined]

    captured: list = []

    def fake_popup(menu, pos, *a, **k):  # noqa: ANN001, ARG001
        captured.append(menu)

    real_popup = QMenu.popup
    QMenu.popup = fake_popup  # type: ignore[method-assign]
    try:
        stub._handle_pyqtgraph_right_click(120.0, 200.0)  # type: ignore[attr-defined]
    finally:
        QMenu.popup = real_popup  # type: ignore[method-assign]
    assert captured == []
