from __future__ import annotations

from artisanlib.plot_pyqtgraph_smoke import render_snapshot_with_pyqtgraph
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, EventMarkerSnapshot, RendererViewState, RoastPlotSnapshot


def test_render_snapshot_with_pyqtgraph_uses_real_plot_widgets() -> None:
    snapshot = RoastPlotSnapshot(
        curves=(
            CurveSnapshot.from_sequences(
                name='BT',
                x=[0, 1, 2],
                y=[140, 142, 144],
                color='#4E7180',
                line_width=2.0,
            ),
            CurveSnapshot.from_sequences(
                name='Delta BT',
                x=[0, 1, 2],
                y=[None, 5.0, 5.5],
                color='#78905D',
                y_axis='ror',
                line_style='--',
            ),
        ),
        events=(
            EventMarkerSnapshot(time=1.5, label='charge', event_type=0, color='#CC0000', value=55.0),
        ),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )

    result = render_snapshot_with_pyqtgraph(snapshot, use_opengl=True)

    assert result.temperature_item_count == 1
    assert result.ror_item_count == 1
    assert result.event_item_count == 2
    assert result.opengl_requested is True
    assert result.view_state == RendererViewState(
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )
