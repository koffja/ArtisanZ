from __future__ import annotations

import math
import sys

import pytest

from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer
from artisanlib.plot_snapshot import (
    AxisSnapshot,
    CurveSnapshot,
    EventMarkerSnapshot,
    PhaseBandSnapshot,
    RendererViewState,
    RoastPlotSnapshot,
)


class FakePlotDataItem:
    def __init__(self, x: tuple[float, ...], y: tuple[float, ...], pen: object, name: str) -> None:
        self.x = x
        self.y = y
        self.pen = pen
        self.name = name
        self.visible = True

    def setData(self, x: tuple[float, ...], y: tuple[float, ...]) -> None:  # noqa: N802
        self.x = x
        self.y = y

    def setPen(self, pen: object) -> None:  # noqa: N802
        self.pen = pen

    def setVisible(self, visible: bool) -> None:  # noqa: N802
        self.visible = visible


class FakeEventItem:
    def __init__(self, kind: str, label: str, color: str) -> None:
        self.kind = kind
        self.label = label
        self.color = color
        self.position: tuple[float, float] | None = None

    def setPos(self, x: float, y: float) -> None:  # noqa: N802
        self.position = (x, y)


class FakePlot:
    def __init__(self) -> None:
        self.items: list[FakePlotDataItem] = []
        self.added_items: list[FakeEventItem] = []
        self.removed_items: list[FakeEventItem] = []
        self.x_range = (0.0, 1.0)
        self.y_range = (0.0, 1.0)
        self.range_padding: list[float] = []

    def plot(
            self,
            x: tuple[float, ...],
            y: tuple[float, ...],
            *,
            pen: object,
            name: str) -> FakePlotDataItem:
        item = FakePlotDataItem(x, y, pen, name)
        self.items.append(item)
        return item

    def setXRange(self, minimum: float, maximum: float, *, padding: float = 0.0) -> None:  # noqa: N802
        self.x_range = (minimum, maximum)
        self.range_padding.append(padding)

    def setYRange(self, minimum: float, maximum: float, *, padding: float = 0.0) -> None:  # noqa: N802
        self.y_range = (minimum, maximum)
        self.range_padding.append(padding)

    def viewRange(self) -> list[list[float]]:  # noqa: N802
        return [[self.x_range[0], self.x_range[1]], [self.y_range[0], self.y_range[1]]]

    def addItem(self, item: FakeEventItem) -> None:  # noqa: N802
        self.added_items.append(item)

    def removeItem(self, item: FakeEventItem) -> None:  # noqa: N802
        self.removed_items.append(item)


def _snapshot(
        *curves: CurveSnapshot,
        events: tuple[EventMarkerSnapshot, ...] = (),
        phase_bands: tuple[PhaseBandSnapshot, ...] = ()) -> RoastPlotSnapshot:
    return RoastPlotSnapshot(
        curves=curves,
        events=events,
        phase_bands=phase_bands,
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )


def _fake_pen_factory(curve: CurveSnapshot) -> dict[str, object]:
    return {'color': curve.color, 'width': curve.line_width, 'style': curve.line_style}


def test_set_snapshot_creates_curve_items_and_applies_ranges() -> None:
    temperature_plot = FakePlot()
    ror_plot = FakePlot()
    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        pen_factory=_fake_pen_factory,
    )

    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(
            name='BT',
            x=[0, 1],
            y=[140, 142],
            color='#4E7180',
            line_style='--',
            line_width=2.5,
        ),
        CurveSnapshot.from_sequences(
            name='Delta BT',
            x=[0, 1],
            y=[None, 5.5],
            color='#78905D',
            y_axis='ror',
        ),
    ))

    assert len(temperature_plot.items) == 1
    assert len(ror_plot.items) == 1
    assert renderer.item_for('BT') is temperature_plot.items[0]
    assert temperature_plot.items[0].x == (0.0, 1.0)
    assert temperature_plot.items[0].y == (140.0, 142.0)
    assert temperature_plot.items[0].pen == {'color': '#4E7180', 'width': 2.5, 'style': '--'}
    assert math.isnan(ror_plot.items[0].y[0])
    assert ror_plot.items[0].y[1] == 5.5
    assert temperature_plot.x_range == (-1.0, 12.0)
    assert temperature_plot.y_range == (70.0, 270.0)
    assert ror_plot.x_range == (-1.0, 12.0)
    assert ror_plot.y_range == (-15.0, 25.0)
    assert temperature_plot.range_padding == [0.0, 0.0]
    assert ror_plot.range_padding == [0.0, 0.0]


def test_update_live_frame_reuses_items_and_hides_missing_curves_without_resetting_view() -> None:
    temperature_plot = FakePlot()
    ror_plot = FakePlot()
    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        pen_factory=_fake_pen_factory,
    )
    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        CurveSnapshot.from_sequences(name='Delta BT', x=[0], y=[None], color='#78905D', y_axis='ror'),
    ))
    bt_item = renderer.item_for('BT')
    delta_item = renderer.item_for('Delta BT')
    temperature_plot.setXRange(2.0, 4.0)

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1, 2], y=[140, 142, 144], color='#4E7180'),
    ))

    assert renderer.item_for('BT') is bt_item
    assert bt_item.x == (0.0, 1.0, 2.0)
    assert bt_item.y == (140.0, 142.0, 144.0)
    assert delta_item.visible is False
    assert temperature_plot.x_range == (2.0, 4.0)


def test_export_view_state_reads_plot_ranges_when_available() -> None:
    temperature_plot = FakePlot()
    ror_plot = FakePlot()
    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        pen_factory=_fake_pen_factory,
    )

    renderer.reset_view(RendererViewState(
        time_axis=AxisSnapshot(minimum=3.0, maximum=9.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=100.0, maximum=240.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-8.0, maximum=18.0, label='RoR'),
    ))

    assert renderer.export_view_state() == RendererViewState(
        time_axis=AxisSnapshot(minimum=3.0, maximum=9.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=100.0, maximum=240.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-8.0, maximum=18.0, label='RoR'),
    )


def test_set_snapshot_renders_and_replaces_event_items() -> None:
    temperature_plot = FakePlot()

    def event_line_factory(event: EventMarkerSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        item = FakeEventItem('line', event.label, event.color)
        item.setPos(event.time, 0.0)
        return item

    def event_label_factory(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> FakeEventItem:
        item = FakeEventItem('label', event.label, event.color)
        item.setPos(event.time, snapshot.temperature_axis.maximum)
        return item

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        event_line_factory=event_line_factory,
        event_label_factory=event_label_factory,
        pen_factory=_fake_pen_factory,
    )

    renderer.set_snapshot(_snapshot(events=(
        EventMarkerSnapshot(time=4.5, label='charge', event_type=0, color='#CC0000', value=55.0),
    )))

    assert len(temperature_plot.added_items) == 2
    assert temperature_plot.added_items[0].kind == 'line'
    assert temperature_plot.added_items[0].position == (4.5, 0.0)
    assert temperature_plot.added_items[1].kind == 'label'
    assert temperature_plot.added_items[1].position == (4.5, 270.0)
    assert renderer.event_item_count() == 2

    old_items = temperature_plot.added_items[:]

    renderer.set_snapshot(_snapshot())

    assert temperature_plot.removed_items == old_items
    assert renderer.event_item_count() == 0


def test_set_snapshot_renders_phase_bands_and_live_updates_preserve_static_overlays() -> None:
    temperature_plot = FakePlot()

    def phase_item_factory(band: PhaseBandSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('phase', f'{band.minimum}:{band.maximum}', band.color)

    def event_line_factory(event: EventMarkerSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('line', event.label, event.color)

    def event_label_factory(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> FakeEventItem:
        item = FakeEventItem('label', event.label, event.color)
        item.setPos(event.time, snapshot.temperature_axis.maximum)
        return item

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        event_line_factory=event_line_factory,
        event_label_factory=event_label_factory,
        phase_item_factory=phase_item_factory,
        pen_factory=_fake_pen_factory,
    )

    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        events=(EventMarkerSnapshot(time=4.5, label='charge', event_type=100, color='#CC0000', kind='main'),),
        phase_bands=(PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#E5E5E5'),),
    ))

    assert renderer.phase_item_count() == 1
    assert renderer.event_item_count() == 2
    assert [item.kind for item in temperature_plot.added_items] == ['phase', 'line', 'label']

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[140, 142], color='#4E7180'),
    ))

    assert renderer.phase_item_count() == 1
    assert renderer.event_item_count() == 2

    old_items = temperature_plot.added_items[:]
    renderer.set_snapshot(_snapshot())

    assert temperature_plot.removed_items == old_items
    assert renderer.phase_item_count() == 0
    assert renderer.event_item_count() == 0


def test_event_markers_are_optional_when_pyqtgraph_is_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, 'pyqtgraph', None)
    temperature_plot = FakePlot()
    renderer = PyQtGraphSnapshotRenderer(temperature_plot=temperature_plot)

    renderer.set_snapshot(_snapshot(events=(
        EventMarkerSnapshot(time=4.5, label='charge', event_type=0, color='#CC0000', value=55.0),
    )))

    assert temperature_plot.added_items == []
    assert renderer.event_item_count() == 0
