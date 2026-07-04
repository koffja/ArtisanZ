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


def test_charge_target_annotation_snapshot_charged_state() -> None:
    from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot

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

    assert snap.enabled is True
    assert snap.is_charged is True
    assert snap.target_temp == 200.0
    assert snap.target_ror == 18.0
    assert snap.charged_temp == 198.5
    assert snap.charged_ror == 17.2
    assert snap.color == 'gray'
    assert snap.current_rwt == 34.9
    assert snap.target_rwt == 33.3
    import dataclasses

    try:
        snap.target_temp = 999.0  # type: ignore[misc]
        raise AssertionError('snapshot must be frozen')
    except dataclasses.FrozenInstanceError:
        pass


def test_charge_target_annotation_snapshot_active_state() -> None:
    from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot

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

    assert snap.title == '接近目标'
    assert snap.reason == '接近目标，继续观察'
    assert snap.prediction_seconds == 8.4
    assert snap.color == 'green'
    assert snap.anchor_time == 423.5
    assert snap.anchor_temp == 192.1
