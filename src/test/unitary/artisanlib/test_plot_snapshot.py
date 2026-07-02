import pytest

from artisanlib.plot_snapshot import (
    AreaFillSnapshot,
    AxisSnapshot,
    CurveSnapshot,
    EventValueSnapshot,
    GuideLineSnapshot,
    RoastPlotSnapshot,
)


def test_curve_snapshot_from_sequences_normalizes_to_immutable_tuples() -> None:
    curve = CurveSnapshot.from_sequences(
        name='BT',
        x=[0, 1.5, 3],
        y=[120, None, 145.5],
        color='#4E7180',
        y_axis='temperature',
    )

    assert curve.x == (0.0, 1.5, 3.0)
    assert curve.y == (120.0, None, 145.5)
    assert curve.visible is True
    assert curve.y_axis == 'temperature'


def test_curve_snapshot_rejects_mismatched_sequence_lengths() -> None:
    with pytest.raises(ValueError, match='same length'):
        CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[120], color='#4E7180')


def test_area_fill_snapshot_from_sequences_normalizes_to_immutable_tuples() -> None:
    area = AreaFillSnapshot.from_sequences(
        x=[1, 2, 3],
        y=[120, None, 140],
        baseline=110,
        color='#767676',
        label='AUC area',
        opacity=0.28,
        kind='auc',
    )

    assert area.x == (1.0, 2.0, 3.0)
    assert area.y == (120.0, None, 140.0)
    assert area.baseline == 110.0
    assert area.opacity == 0.28
    assert area.kind == 'auc'


def test_area_fill_snapshot_rejects_mismatched_sequence_lengths() -> None:
    with pytest.raises(ValueError, match='same length'):
        AreaFillSnapshot.from_sequences(x=[0, 1], y=[120], baseline=100, color='#767676')


def test_roast_plot_snapshot_filters_visible_curves_and_exports_view_state() -> None:
    visible = CurveSnapshot.from_sequences(name='BT', x=[0], y=[120], color='#4E7180')
    hidden = CurveSnapshot.from_sequences(name='ET', x=[0], y=[130], color='#B5644F', visible=False)
    snapshot = RoastPlotSnapshot(
        curves=(visible, hidden),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0),
    )

    assert snapshot.visible_curves() == (visible,)
    assert snapshot.export_view_state().time_axis == AxisSnapshot(minimum=-1.0, maximum=12.0)


def test_roast_plot_snapshot_carries_overlay_contracts() -> None:
    event_value = EventValueSnapshot(
        time=3.0,
        value=55.0,
        event_type=1,
        color='#4E7180',
        label='Power',
    )
    guide = GuideLineSnapshot(
        position=180.0,
        label='Charge target',
        color='#B4685C',
        orientation='horizontal',
        kind='charge_target',
    )
    area = AreaFillSnapshot.from_sequences(
        x=[1, 2],
        y=[120, 140],
        baseline=110,
        color='#767676',
        label='AUC area',
        kind='auc',
    )
    snapshot = RoastPlotSnapshot(
        curves=(),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0),
        event_values=(event_value,),
        guides=(guide,),
        areas=(area,),
    )

    assert snapshot.event_values == (event_value,)
    assert snapshot.guides == (guide,)
    assert snapshot.areas == (area,)
