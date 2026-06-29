from __future__ import annotations

from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RendererViewState, RoastPlotSnapshot


class FakeCanvas:
    def __init__(self) -> None:
        self.draw_idle_count = 0

    def draw_idle(self) -> None:
        self.draw_idle_count += 1


class FakeFigure:
    def __init__(self) -> None:
        self.canvas = FakeCanvas()


class FakeLine:
    def __init__(self) -> None:
        self.x: tuple[float, ...] = ()
        self.y: tuple[float | None, ...] = ()
        self.color = ''
        self.label = ''
        self.line_style = ''
        self.line_width = 0.0
        self.visible = True

    def set_data(self, x: tuple[float, ...], y: tuple[float | None, ...]) -> None:
        self.x = x
        self.y = y

    def set_color(self, color: str) -> None:
        self.color = color

    def set_linestyle(self, line_style: str) -> None:
        self.line_style = line_style

    def set_linewidth(self, line_width: float) -> None:
        self.line_width = line_width

    def set_visible(self, visible: bool) -> None:
        self.visible = visible


class FakeAxis:
    def __init__(self) -> None:
        self.figure = FakeFigure()
        self.lines: list[FakeLine] = []
        self.xlim = (0.0, 1.0)
        self.ylim = (0.0, 1.0)

    def plot(
            self,
            x: tuple[float, ...],
            y: tuple[float | None, ...],
            *,
            label: str,
            color: str,
            linestyle: str,
            linewidth: float) -> list[FakeLine]:
        line = FakeLine()
        line.set_data(x, y)
        line.set_color(color)
        line.label = label
        line.set_linestyle(linestyle)
        line.set_linewidth(linewidth)
        self.lines.append(line)
        return [line]

    def set_xlim(self, minimum: float, maximum: float) -> None:
        self.xlim = (minimum, maximum)

    def set_ylim(self, minimum: float, maximum: float) -> None:
        self.ylim = (minimum, maximum)

    def get_xlim(self) -> tuple[float, float]:
        return self.xlim

    def get_ylim(self) -> tuple[float, float]:
        return self.ylim


def _snapshot(*curves: CurveSnapshot) -> RoastPlotSnapshot:
    return RoastPlotSnapshot(
        curves=curves,
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )


def test_set_snapshot_creates_lines_and_applies_axes() -> None:
    temperature_axis = FakeAxis()
    ror_axis = FakeAxis()
    renderer = MatplotlibSnapshotRenderer(temperature_axis=temperature_axis, ror_axis=ror_axis)

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

    assert len(temperature_axis.lines) == 1
    assert len(ror_axis.lines) == 1
    assert renderer.line_for('BT') is temperature_axis.lines[0]
    assert temperature_axis.lines[0].x == (0.0, 1.0)
    assert temperature_axis.lines[0].y == (140.0, 142.0)
    assert temperature_axis.lines[0].color == '#4E7180'
    assert temperature_axis.lines[0].label == 'BT'
    assert temperature_axis.lines[0].line_style == '--'
    assert temperature_axis.lines[0].line_width == 2.5
    assert ror_axis.lines[0].y == (None, 5.5)
    assert temperature_axis.xlim == (-1.0, 12.0)
    assert temperature_axis.ylim == (70.0, 270.0)
    assert ror_axis.xlim == (-1.0, 12.0)
    assert ror_axis.ylim == (-15.0, 25.0)
    assert temperature_axis.figure.canvas.draw_idle_count == 1


def test_update_live_frame_reuses_lines_and_hides_missing_curves_without_resetting_view() -> None:
    temperature_axis = FakeAxis()
    ror_axis = FakeAxis()
    renderer = MatplotlibSnapshotRenderer(temperature_axis=temperature_axis, ror_axis=ror_axis)
    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        CurveSnapshot.from_sequences(name='Delta BT', x=[0], y=[None], color='#78905D', y_axis='ror'),
    ))
    bt_line = renderer.line_for('BT')
    delta_line = renderer.line_for('Delta BT')
    temperature_axis.set_xlim(2.0, 4.0)

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1, 2], y=[140, 142, 144], color='#4E7180'),
    ))

    assert renderer.line_for('BT') is bt_line
    assert bt_line.x == (0.0, 1.0, 2.0)
    assert bt_line.y == (140.0, 142.0, 144.0)
    assert delta_line.visible is False
    assert temperature_axis.xlim == (2.0, 4.0)


def test_reset_and_export_view_state_round_trip_axes() -> None:
    temperature_axis = FakeAxis()
    ror_axis = FakeAxis()
    renderer = MatplotlibSnapshotRenderer(temperature_axis=temperature_axis, ror_axis=ror_axis)

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
