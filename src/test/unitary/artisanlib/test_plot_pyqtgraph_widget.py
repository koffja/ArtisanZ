from __future__ import annotations

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt6.QtWidgets import QApplication

from artisanlib.plot_pyqtgraph_widget import _grid_display_color, _visible_grid_alpha, create_pyqtgraph_plot_target
from artisanlib.plot_snapshot import AreaFillSnapshot, AxisSnapshot, CurveSnapshot, PhaseBandSnapshot, RoastPlotSnapshot

pg = pytest.importorskip('pyqtgraph')
_APPLICATION = QApplication.instance() or QApplication([])


def _snapshot(*, include_ror: bool = True) -> RoastPlotSnapshot:
    curves = [
        CurveSnapshot.from_sequences(
            name='BT',
            x=[0, 1, 2],
            y=[140, 142, 144],
            color='#4E7180',
        ),
    ]
    ror_axis = None
    if include_ror:
        curves.append(CurveSnapshot.from_sequences(
            name='Delta BT',
            x=[0, 1, 2],
            y=[None, 5.0, 5.5],
            color='#78905D',
            y_axis='ror',
        ))
        ror_axis = AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR')
    return RoastPlotSnapshot(
        curves=tuple(curves),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=ror_axis,
    )


def test_create_pyqtgraph_plot_target_renders_temperature_and_ror_curves() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        target.renderer.set_snapshot(_snapshot(include_ror=True))
        _APPLICATION.processEvents()

        assert target.opengl_requested is False
        assert target.ror_plot is not None
        assert target.ror_axis is not None
        assert _plot_data_item_count(target.temperature_plot) == 1
        assert _plot_data_item_count(target.ror_plot) == 1
    finally:
        target.close()


def test_create_pyqtgraph_plot_target_can_skip_ror_plot() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=False)
    try:
        target.renderer.set_snapshot(_snapshot(include_ror=False))
        _APPLICATION.processEvents()

        assert target.ror_plot is None
        assert _plot_data_item_count(target.temperature_plot) == 1
    finally:
        target.close()


def test_create_pyqtgraph_plot_target_renders_phase_band_overlay() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        snapshot = RoastPlotSnapshot(
            curves=(),
            time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
            temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
            ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
            phase_bands=(PhaseBandSnapshot(minimum=100.0, maximum=150.0, color='#E5E5E5'),),
        )
        target.renderer.set_snapshot(snapshot)
        _APPLICATION.processEvents()

        assert target.renderer.phase_item_count() == 1
    finally:
        target.close()


def test_create_pyqtgraph_plot_target_renders_area_fill_overlay() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        snapshot = RoastPlotSnapshot(
            curves=(),
            time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
            temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
            ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
            areas=(AreaFillSnapshot.from_sequences(
                x=[1.0, 2.0, 3.0],
                y=[120.0, 140.0, 160.0],
                baseline=110.0,
                color='#767676',
                label='AUC area',
                kind='auc',
            ),),
        )
        target.renderer.set_snapshot(snapshot)
        _APPLICATION.processEvents()

        assert target.renderer.area_item_count() == 1
    finally:
        target.close()


def test_pyqtgraph_time_axis_can_display_minutes_or_seconds() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        target.configure_axes(
            time_grid=True,
            temperature_grid=True,
            time_tick_step=60.0,
            temperature_tick_step=10.0,
            ror_tick_step=5.0,
            time_label_mode='minutes',
            time_axis_start=60.0,
            grid_alpha=0.2,
            grid_width=1,
            grid_color='#d0d7d8',
            axis_color='#5e6b6e',
        )
        assert target.time_axis.tickStrings([60.0, 120.0, 180.0], 1.0, 60.0) == ['0:00', '1:00', '2:00']
        assert target.grid_item is not None
        assert target.grid_item.isVisible()
        assert target.grid_item.opts['tickSpacing'] == ([60.0], [10.0])

        target.configure_axes(
            time_grid=True,
            temperature_grid=True,
            time_tick_step=60.0,
            temperature_tick_step=10.0,
            ror_tick_step=5.0,
            time_label_mode='seconds',
            time_axis_start=60.0,
            grid_alpha=0.2,
            grid_width=1,
            grid_color='#d0d7d8',
            axis_color='#5e6b6e',
        )
        assert target.time_axis.tickStrings([60.0, 120.0, 180.0], 1.0, 60.0) == ['0', '60', '120']
    finally:
        target.close()


def test_pyqtgraph_grid_overlay_hides_when_grid_settings_are_disabled() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        target.configure_axes(
            time_grid=False,
            temperature_grid=False,
            time_tick_step=60.0,
            temperature_tick_step=10.0,
            ror_tick_step=5.0,
            time_label_mode='minutes',
            time_axis_start=60.0,
            grid_alpha=0.2,
            grid_width=1,
            grid_color='#d0d7d8',
            axis_color='#5e6b6e',
        )

        assert target.grid_item is not None
        assert not target.grid_item.isVisible()
    finally:
        target.close()


def test_pyqtgraph_grid_overlay_can_show_one_axis() -> None:
    target = create_pyqtgraph_plot_target(use_opengl=False, include_ror=True)
    try:
        target.configure_axes(
            time_grid=False,
            temperature_grid=True,
            time_tick_step=60.0,
            temperature_tick_step=10.0,
            ror_tick_step=5.0,
            time_label_mode='minutes',
            time_axis_start=60.0,
            grid_alpha=0.2,
            grid_width=1,
            grid_color='#d0d7d8',
            axis_color='#5e6b6e',
        )

        assert target.grid_item is not None
        assert target.grid_item.isVisible()
        assert target.grid_item.opts['tickSpacing'] == ([None], [10.0])
    finally:
        target.close()


def test_pyqtgraph_grid_display_color_keeps_default_grid_visible() -> None:
    assert _grid_display_color('#d0d7d8') == '#8FA09A'
    assert _grid_display_color('#65736f') == '#65736f'


def test_pyqtgraph_grid_alpha_has_visible_floor_on_light_canvas() -> None:
    assert _visible_grid_alpha(0.05) == 0.78
    assert _visible_grid_alpha(0.25) == 0.8
    assert _visible_grid_alpha(1.0) == 1.0


def test_create_pyqtgraph_plot_target_restores_opengl_config_on_close() -> None:
    previous_opengl = bool(pg.getConfigOption('useOpenGL'))
    target = create_pyqtgraph_plot_target(use_opengl=not previous_opengl, include_ror=False)

    assert bool(pg.getConfigOption('useOpenGL')) is (not previous_opengl)

    target.close()

    assert bool(pg.getConfigOption('useOpenGL')) is previous_opengl


def _plot_data_item_count(plot: object) -> int:
    list_data_items = getattr(plot, 'listDataItems', None)
    if callable(list_data_items):
        return len(list_data_items())
    return 0
