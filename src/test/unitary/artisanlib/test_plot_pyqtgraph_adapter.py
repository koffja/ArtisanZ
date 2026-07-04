from __future__ import annotations

import math
import sys

import pytest

from artisanlib.plot_pyqtgraph_adapter import (
    PyQtGraphSnapshotRenderer,
    _default_pen_factory,
    _event_label_anchor,
    _event_label_y_position,
    _visible_phase_band_opacity,
)
from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    ChargeTargetAnnotationSnapshot,
    CurveSnapshot,
    EventMarkerSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    PhaseBandSnapshot,
    PhaseSummarySnapshot,
    RendererViewState,
    RoastPlotSnapshot,
    TimeRangeSnapshot,
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


class FakeLegend:
    def __init__(self) -> None:
        self.items: list[tuple[FakePlotDataItem, str]] = []
        self.clear_count = 0

    def clear(self) -> None:
        self.clear_count += 1
        self.items.clear()

    def addItem(self, item: FakePlotDataItem, label: str) -> None:  # noqa: N802
        self.items.append((item, label))


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
        event_values: tuple[EventValueSnapshot, ...] = (),
        phase_bands: tuple[PhaseBandSnapshot, ...] = (),
        time_ranges: tuple[TimeRangeSnapshot, ...] = (),
        phase_summaries: tuple[PhaseSummarySnapshot, ...] = (),
        areas: tuple[AreaFillSnapshot, ...] = (),
        guides: tuple[GuideLineSnapshot, ...] = ()) -> RoastPlotSnapshot:
    return RoastPlotSnapshot(
        curves=curves,
        events=events,
        event_values=event_values,
        phase_bands=phase_bands,
        time_ranges=time_ranges,
        phase_summaries=phase_summaries,
        areas=areas,
        guides=guides,
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


def test_set_snapshot_populates_legend_with_temperature_and_ror_curves() -> None:
    temperature_plot = FakePlot()
    ror_plot = FakePlot()
    legend = FakeLegend()
    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        legend_item=legend,
        pen_factory=_fake_pen_factory,
    )

    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(name='ET', x=[0], y=[150], color='#B5644F'),
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        CurveSnapshot.from_sequences(name='Delta ET', x=[0], y=[None], color='#B98A4B', y_axis='ror'),
        CurveSnapshot.from_sequences(name='Delta BT', x=[0], y=[None], color='#78905D', y_axis='ror'),
        CurveSnapshot.from_sequences(name='BT projection', x=[0], y=[140], color='#4E7180'),
    ))

    assert [label for _, label in legend.items] == ['ET', 'BT', 'ΔET', 'ΔBT']


def test_default_pen_factory_keeps_bt_visibly_stronger_than_secondary_curves() -> None:
    bt_pen = _default_pen_factory(CurveSnapshot.from_sequences(
        name='BT',
        x=[0],
        y=[140],
        color='#4E7180',
        line_width=1.0,
    ))
    et_pen = _default_pen_factory(CurveSnapshot.from_sequences(
        name='ET',
        x=[0],
        y=[150],
        color='#B5644F',
        line_width=1.0,
    ))

    assert bt_pen.widthF() >= 2.2
    assert et_pen.widthF() == 1.0


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
    ror_plot = FakePlot()

    def phase_item_factory(band: PhaseBandSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('phase', f'{band.minimum}:{band.maximum}', band.color)

    def time_range_factory(time_range: TimeRangeSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('time-range', f'{time_range.start}:{time_range.end}', time_range.color)

    def phase_summary_factory(summary: PhaseSummarySnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('phase-summary', summary.percent_text, summary.color)

    def area_item_factory(area: AreaFillSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('area', area.label, area.color)

    def event_line_factory(event: EventMarkerSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('line', event.label, event.color)

    def event_label_factory(event: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> FakeEventItem:
        item = FakeEventItem('label', event.label, event.color)
        item.setPos(event.time, snapshot.temperature_axis.maximum)
        return item

    def event_value_factory(event_value: EventValueSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('event-value', event_value.label, event_value.color)

    def guide_item_factory(guide: GuideLineSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('guide', guide.label, guide.color)

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        event_line_factory=event_line_factory,
        event_label_factory=event_label_factory,
        event_value_factory=event_value_factory,
        guide_item_factory=guide_item_factory,
        phase_item_factory=phase_item_factory,
        time_range_factory=time_range_factory,
        phase_summary_factory=phase_summary_factory,
        area_item_factory=area_item_factory,
        pen_factory=_fake_pen_factory,
    )

    events = (EventMarkerSnapshot(time=4.5, label='charge', event_type=100, color='#CC0000', kind='main'),)
    event_values = (EventValueSnapshot(time=4.5, value=55.0, event_type=1, color='#CC0000', label='power'),)
    phase_bands = (PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#E5E5E5'),)
    time_ranges = (TimeRangeSnapshot(start=8.0, end=10.0, color='#FFF6A8', label='Development'),)
    phase_summaries = (PhaseSummarySnapshot(
        start=8.0,
        end=10.0,
        label='Development',
        duration_text='2:00',
        percent_text='20.0%',
        delta_text='12.0',
        color='#FFF6A8',
    ),)
    areas = (AreaFillSnapshot.from_sequences(
        x=[1.0, 2.0],
        y=[120.0, 150.0],
        baseline=110.0,
        color='#767676',
        label='AUC area',
        kind='auc',
    ),)
    guides = (
        GuideLineSnapshot(position=4.0, label='AUC guide', color='#336677', kind='auc'),
        GuideLineSnapshot(position=6.0, label='RoR guide', color='#78905D', y_axis='ror'),
    )

    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        events=events,
        event_values=event_values,
        phase_bands=phase_bands,
        time_ranges=time_ranges,
        phase_summaries=phase_summaries,
        areas=areas,
        guides=guides,
    ))

    assert renderer.phase_item_count() == 1
    assert renderer.time_range_item_count() == 1
    assert renderer.phase_summary_item_count() == 1
    assert renderer.area_item_count() == 1
    assert renderer.event_item_count() == 2
    assert renderer.event_value_item_count() == 1
    assert renderer.guide_item_count() == 2
    assert [item.kind for item in temperature_plot.added_items] == [
        'phase',
        'time-range',
        'phase-summary',
        'area',
        'event-value',
        'line',
        'label',
        'guide',
    ]
    assert [item.kind for item in ror_plot.added_items] == ['guide']

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[140, 142], color='#4E7180'),
        events=events,
        event_values=event_values,
        phase_bands=phase_bands,
        time_ranges=time_ranges,
        phase_summaries=phase_summaries,
        areas=areas,
        guides=guides,
    ))

    assert renderer.phase_item_count() == 1
    assert renderer.time_range_item_count() == 1
    assert renderer.phase_summary_item_count() == 1
    assert renderer.area_item_count() == 1
    assert renderer.event_item_count() == 2
    assert renderer.event_value_item_count() == 1
    assert renderer.guide_item_count() == 2

    old_items = temperature_plot.added_items[:]
    old_ror_items = ror_plot.added_items[:]
    renderer.set_snapshot(_snapshot())

    assert temperature_plot.removed_items == old_items
    assert ror_plot.removed_items == old_ror_items
    assert renderer.phase_item_count() == 0
    assert renderer.time_range_item_count() == 0
    assert renderer.phase_summary_item_count() == 0
    assert renderer.area_item_count() == 0
    assert renderer.event_item_count() == 0
    assert renderer.event_value_item_count() == 0
    assert renderer.guide_item_count() == 0


def test_update_live_frame_applies_static_overlays_without_prior_snapshot() -> None:
    temperature_plot = FakePlot()
    ror_plot = FakePlot()

    def phase_item_factory(band: PhaseBandSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('phase', f'{band.minimum}:{band.maximum}', band.color)

    def area_item_factory(area: AreaFillSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('area', area.label, area.color)

    def event_line_factory(event: EventMarkerSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('line', event.label, event.color)

    def event_label_factory(event: EventMarkerSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('label', event.label, event.color)

    def event_value_factory(event_value: EventValueSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('event-value', event_value.label, event_value.color)

    def guide_item_factory(guide: GuideLineSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('guide', guide.label, guide.color)

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        ror_plot=ror_plot,
        event_line_factory=event_line_factory,
        event_label_factory=event_label_factory,
        event_value_factory=event_value_factory,
        guide_item_factory=guide_item_factory,
        phase_item_factory=phase_item_factory,
        area_item_factory=area_item_factory,
        pen_factory=_fake_pen_factory,
    )
    snapshot = _snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[140, 142], color='#4E7180'),
        events=(EventMarkerSnapshot(time=4.5, label='charge', event_type=100, color='#CC0000', kind='main'),),
        event_values=(EventValueSnapshot(time=4.5, value=55.0, event_type=1, color='#CC0000', label='power'),),
        phase_bands=(PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#E5E5E5'),),
        areas=(AreaFillSnapshot.from_sequences(
            x=[1.0, 2.0],
            y=[120.0, 150.0],
            baseline=110.0,
            color='#767676',
            label='AUC area',
            kind='auc',
        ),),
        guides=(
            GuideLineSnapshot(position=4.0, label='AUC guide', color='#336677', kind='auc'),
            GuideLineSnapshot(position=6.0, label='RoR guide', color='#78905D', y_axis='ror'),
        ),
    )

    renderer.update_live_frame(snapshot)

    assert renderer.phase_item_count() == 1
    assert renderer.area_item_count() == 1
    assert renderer.event_item_count() == 2
    assert renderer.event_value_item_count() == 1
    assert renderer.guide_item_count() == 2
    assert [item.kind for item in temperature_plot.added_items] == [
        'phase',
        'area',
        'event-value',
        'line',
        'label',
        'guide',
    ]
    assert [item.kind for item in ror_plot.added_items] == ['guide']

    renderer.update_live_frame(snapshot)

    assert temperature_plot.removed_items == []
    assert ror_plot.removed_items == []
    assert [item.kind for item in temperature_plot.added_items] == [
        'phase',
        'area',
        'event-value',
        'line',
        'label',
        'guide',
    ]
    assert [item.kind for item in ror_plot.added_items] == ['guide']


def test_update_live_frame_clears_static_overlays_when_snapshot_has_none() -> None:
    temperature_plot = FakePlot()

    def phase_item_factory(band: PhaseBandSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('phase', f'{band.minimum}:{band.maximum}', band.color)

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        phase_item_factory=phase_item_factory,
        pen_factory=_fake_pen_factory,
    )

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        phase_bands=(PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#E5E5E5'),),
    ))
    first_phase_items = temperature_plot.added_items[:]

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[140, 142], color='#4E7180'),
    ))

    assert renderer.phase_item_count() == 0
    assert temperature_plot.removed_items == first_phase_items


def test_update_live_frame_refreshes_static_overlays_when_axes_change() -> None:
    temperature_plot = FakePlot()

    event = EventMarkerSnapshot(time=4.5, label='charge', event_type=100, color='#CC0000', kind='main')

    def event_line_factory(event_marker: EventMarkerSnapshot, _: RoastPlotSnapshot) -> FakeEventItem:
        return FakeEventItem('line', event_marker.label, event_marker.color)

    def event_label_factory(event_marker: EventMarkerSnapshot, snapshot: RoastPlotSnapshot) -> FakeEventItem:
        item = FakeEventItem('label', event_marker.label, event_marker.color)
        item.setPos(event_marker.time, snapshot.temperature_axis.maximum)
        return item

    renderer = PyQtGraphSnapshotRenderer(
        temperature_plot=temperature_plot,
        event_line_factory=event_line_factory,
        event_label_factory=event_label_factory,
        pen_factory=_fake_pen_factory,
    )

    renderer.update_live_frame(RoastPlotSnapshot(
        curves=(CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),),
        events=(event,),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    ))
    first_items = temperature_plot.added_items[:]

    renderer.update_live_frame(RoastPlotSnapshot(
        curves=(CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[140, 142], color='#4E7180'),),
        events=(event,),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=24.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=320.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    ))

    assert temperature_plot.removed_items == first_items
    assert temperature_plot.added_items[-1].kind == 'label'
    assert temperature_plot.added_items[-1].position == (4.5, 320.0)


def test_event_label_y_position_uses_distinct_rows_for_time_clusters() -> None:
    events = (
        EventMarkerSnapshot(time=10.0, label='Power', event_type=1, color='#CC0000'),
        EventMarkerSnapshot(time=11.0, label='Fan', event_type=2, color='#00AA00'),
        EventMarkerSnapshot(time=12.0, label='Drum', event_type=3, color='#0000CC'),
        EventMarkerSnapshot(time=90.0, label='Far', event_type=4, color='#333333'),
    )
    snapshot = _snapshot(events=events)

    clustered_positions = [_event_label_y_position(event, snapshot) for event in events[:3]]

    assert len(set(clustered_positions)) == 3
    assert _event_label_y_position(events[3], snapshot) == clustered_positions[0]


def test_event_label_y_position_does_not_wrap_dense_clusters() -> None:
    events = tuple(
        EventMarkerSnapshot(time=10.0 + index * 0.5, label=f'Event {index}', event_type=index, color='#333333')
        for index in range(8)
    )
    snapshot = _snapshot(events=events)

    clustered_positions = [_event_label_y_position(event, snapshot) for event in events]

    assert len(set(clustered_positions)) == len(events)


def test_event_label_anchor_protects_axis_edges() -> None:
    snapshot = _snapshot(events=())

    assert _event_label_anchor(
        EventMarkerSnapshot(time=-1.0, label='CHARGE', event_type=100, color='#333333'),
        snapshot,
    ) == (0.0, 1.0)
    assert _event_label_anchor(
        EventMarkerSnapshot(time=12.0, label='DROP', event_type=106, color='#333333'),
        snapshot,
    ) == (1.0, 1.0)
    assert _event_label_anchor(
        EventMarkerSnapshot(time=6.0, label='FCs', event_type=102, color='#333333'),
        snapshot,
    ) == (0.5, 1.0)


def test_phase_band_opacity_has_visible_floor_on_light_canvas() -> None:
    assert _visible_phase_band_opacity(0.05) == 0.10
    assert _visible_phase_band_opacity(0.22) == 0.22
    assert _visible_phase_band_opacity(0.8) == 0.22


def test_charge_target_annotation_factory_charged_state_returns_single_text_item() -> None:
    """Charged state emits one TextItem placed at axes-top-left equivalent."""
    from PyQt6.QtWidgets import QApplication

    from artisanlib.plot_pyqtgraph_adapter import _default_charge_target_annotation_factory

    _app = QApplication.instance() or QApplication([])
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=True,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=198.5,
        charged_ror=17.2,
        title='',
        reason='',
        prediction_seconds=None,
        color='gray',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=0.0,
        anchor_temp=0.0,
        x_limit=600.0,
        y_limit_top=250.0,
    )
    snapshot = RoastPlotSnapshot(
        curves=(),
        time_axis=AxisSnapshot(minimum=0.0, maximum=600.0, label=''),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=250.0, label=''),
    )

    items = _default_charge_target_annotation_factory(snap, snapshot)

    assert items is not None
    item_tuple = items if isinstance(items, tuple) else (items,)
    assert len(item_tuple) == 1, f"charged state should emit exactly 1 item, got {len(item_tuple)}"
    text_item = item_tuple[0]
    assert hasattr(text_item, 'setText') or hasattr(text_item, 'setPlainText'), (
        f"expected TextItem-like object, got {type(text_item).__name__}"
    )


def test_charge_target_annotation_factory_active_state_returns_text_and_connector() -> None:
    """Active state emits a TextItem plus a connector line back to (anchor_time, anchor_temp)."""
    from PyQt6.QtWidgets import QApplication

    from artisanlib.plot_pyqtgraph_adapter import _default_charge_target_annotation_factory

    _app = QApplication.instance() or QApplication([])
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=False,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=0.0,
        charged_ror=0.0,
        title='接近目标',
        reason='接近目标，继续观察',
        prediction_seconds=8.4,
        color='green',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=423.5,
        anchor_temp=192.1,
        x_limit=600.0,
        y_limit_top=250.0,
    )
    snapshot = RoastPlotSnapshot(
        curves=(),
        time_axis=AxisSnapshot(minimum=0.0, maximum=600.0, label=''),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=250.0, label=''),
    )

    items = _default_charge_target_annotation_factory(snap, snapshot)

    assert items is not None
    item_tuple = items if isinstance(items, tuple) else (items,)
    assert len(item_tuple) >= 2, f"active state should emit >=2 items, got {len(item_tuple)}"


def test_event_markers_are_optional_when_pyqtgraph_is_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, 'pyqtgraph', None)
    temperature_plot = FakePlot()
    renderer = PyQtGraphSnapshotRenderer(temperature_plot=temperature_plot)

    renderer.set_snapshot(_snapshot(events=(
        EventMarkerSnapshot(time=4.5, label='charge', event_type=0, color='#CC0000', value=55.0),
    )))

    assert temperature_plot.added_items == []
    assert renderer.event_item_count() == 0


def test_visible_phase_band_opacity_uses_lower_cap() -> None:
    assert _visible_phase_band_opacity(0.30) == 0.22
    assert _visible_phase_band_opacity(0.05) == 0.10
    assert abs(_visible_phase_band_opacity(0.15) - 0.18) < 0.01
    assert _visible_phase_band_opacity(0.22) == 0.22


def test_bt_gradient_disabled_by_default_returns_solid_pen(qapp=None) -> None:
    from artisanlib.plot_pyqtgraph_adapter import (
        _default_pen_factory,
        set_bt_gradient_enabled,
        _BT_GRADIENT_ENABLED_DEFAULT,
    )
    set_bt_gradient_enabled(False)
    curve = CurveSnapshot(
        name='BT',
        x=(0.0,),
        y=(200.0,),
        color='#4f5f66',
        line_width=2.0,
    )
    pen = _default_pen_factory(curve)
    assert hasattr(pen, 'color'), f'expected solid pen, got {type(pen).__name__}'
    set_bt_gradient_enabled(_BT_GRADIENT_ENABLED_DEFAULT)


def test_phase_summary_includes_phase_label_in_text(qapp=None) -> None:
    from PyQt6.QtWidgets import QApplication
    from artisanlib.plot_pyqtgraph_adapter import _default_phase_summary_item_factory

    _app = QApplication.instance() or QApplication([])
    summary = PhaseSummarySnapshot(
        start=100.0,
        end=300.0,
        label='Drying',
        duration_text='3:20',
        percent_text='45.5%',
        delta_text='+52',
        color='#F5F5F0',
        opacity=0.18,
    )
    snapshot = RoastPlotSnapshot(
        curves=(),
        time_axis=TimeRangeSnapshot(start=0.0, end=600.0, color='#000000'),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=250.0, label=''),
    )
    items = _default_phase_summary_item_factory(summary, snapshot)
    assert items is not None
    item_tuple = items if isinstance(items, tuple) else (items,)
    label_item = item_tuple[1]
    text = label_item.toPlainText() if hasattr(label_item, 'toPlainText') else label_item.text
    assert 'Drying' in text, f'phase label missing from text: {text!r}'
