import pytest

from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RoastPlotSnapshot


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
