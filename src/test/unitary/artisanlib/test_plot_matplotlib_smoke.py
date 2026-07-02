from __future__ import annotations

from artisanlib.plot_matplotlib_smoke import render_snapshot_to_png_bytes
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, EventMarkerSnapshot, RendererViewState, RoastPlotSnapshot


def test_render_snapshot_to_png_bytes_uses_real_matplotlib_axes() -> None:
    snapshot = RoastPlotSnapshot(
        curves=(
            CurveSnapshot.from_sequences(name='BT', x=[0, 1, 2], y=[140, 142, 144], color='#4E7180'),
            CurveSnapshot.from_sequences(
                name='Delta BT',
                x=[0, 1, 2],
                y=[None, 5.0, 5.5],
                color='#78905D',
                y_axis='ror',
            ),
        ),
        events=(
            EventMarkerSnapshot(time=1.5, label='charge', event_type=0, color='#CC0000', value=55.0),
        ),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )

    result = render_snapshot_to_png_bytes(snapshot, width=3.0, height=2.0, dpi=80)

    assert result.png_bytes.startswith(b'\x89PNG\r\n\x1a\n')
    assert len(result.png_bytes) > 1000
    assert result.temperature_line_count == 2
    assert result.ror_line_count == 1
    assert result.event_artist_count == 2
    assert result.phase_artist_count == 0
    assert result.area_artist_count == 0
    assert result.event_value_artist_count == 0
    assert result.guide_artist_count == 0
    assert result.view_state == RendererViewState(
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )
