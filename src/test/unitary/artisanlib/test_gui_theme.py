import sys
from collections.abc import Generator
from pathlib import Path
from types import SimpleNamespace

import pytest

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from artisanlib import gui_theme
from artisanlib.gui_theme import (
    ModernTheme,
    apply_modern_dialog_polish,
    modern_application_stylesheet,
    modern_toolbar_icon_path,
)


@pytest.fixture(scope='session')
def qapp() -> Generator[QApplication, None, None]: # pyright:ignore[reportUnknownParameterType]
    if not QApplication.instance():
        app = QApplication(sys.argv)
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


def test_modern_application_stylesheet_contains_core_surfaces() -> None:
    stylesheet = modern_application_stylesheet()

    assert 'QMainWindow' in stylesheet
    assert 'QToolBar' in stylesheet
    assert 'QToolBar#roastNavigationToolbar' in stylesheet
    assert 'QToolBar#roastNavigationToolbar::separator' in stylesheet
    assert 'QMenuBar' in stylesheet
    assert 'QPushButton' in stylesheet
    assert 'QLCDNumber[lcdValue="true"]' in stylesheet
    assert 'padding: 5px 8px 4px 8px;' in stylesheet
    assert 'QFrame[lcdSurface="true"]' in stylesheet
    assert 'background-color: transparent;' in stylesheet
    assert 'QLabel[lcdLabel="true"]' in stylesheet
    assert 'padding: 3px 6px 2px 6px;' in stylesheet
    assert 'QWidget[mainRoastScreen="true"]' in stylesheet
    assert 'QWidget[mainGraphPanel="true"]' in stylesheet
    assert 'QFrame[telemetryCard="true"]' in stylesheet
    assert 'QFrame[roastEventRail="true"]' in stylesheet
    assert 'QPushButton[mainControlRole="record"]' in stylesheet
    assert '#B4685C' in stylesheet
    assert '#53756F' in stylesheet
    assert 'QDialog QPushButton' in stylesheet
    assert 'QMessageBox, QFileDialog' in stylesheet
    assert 'QDialog[modernDialog="true"] QGroupBox' in stylesheet
    assert 'QDialog[modernDialog="true"] QTabWidget::pane' in stylesheet
    assert 'QDialog[modernDialog="true"] QTableWidget' in stylesheet
    assert 'QWidget[modernDialogViewport="true"]' in stylesheet
    assert 'QPushButton[modernDialogPrimaryButton="true"]' in stylesheet
    assert 'QCheckBox::indicator:checked' in stylesheet
    assert 'QDialog[modernDialogRole="axes"] QTabBar::tab:selected' in stylesheet
    assert 'QDialog[modernDialogRole="events"] QTabBar::tab:selected' in stylesheet
    assert 'QDialog[modernDialogRole="alarms"] QTabBar::tab:selected' in stylesheet
    assert 'QDialog[modernDialogRole="devices"] QTabBar::tab:selected' in stylesheet
    assert 'QDialog[modernDialogRole="roast_properties"] QTabBar::tab:selected' in stylesheet
    assert 'QDialog[modernDenseDialog="true"] QTableView::item' in stylesheet
    assert 'QDialog[modernDialog="true"] QComboBox::drop-down' in stylesheet
    assert 'QDialog[modernDialog="true"] QComboBox QAbstractItemView' in stylesheet
    assert 'QDialog[modernDialog="true"] QComboBox[modernExpandValueControl="true"]' in stylesheet
    assert 'QDialog[modernDialog="true"] QSpinBox::up-button' in stylesheet
    assert 'QDialog[modernDialog="true"] QSpinBox::down-button' in stylesheet
    assert 'QDialog[modernDialog="true"] QTimeEdit[modernExpandValueControl="true"]' in stylesheet
    assert 'padding-right: 32px;' in stylesheet
    assert 'modern-combo-down.svg' in stylesheet
    assert 'modern-spin-up.svg' in stylesheet
    assert 'modern-spin-down.svg' in stylesheet


def test_modern_dialog_value_controls_reserve_indicator_space() -> None:
    stylesheet = modern_application_stylesheet()

    assert stylesheet.count('padding-right: 32px;') >= 2


def test_modern_application_stylesheet_uses_supplied_theme() -> None:
    theme = ModernTheme(window='#111111', surface='#222222', primary='#123456')

    stylesheet = modern_application_stylesheet(theme)

    assert '#111111' in stylesheet
    assert '#222222' in stylesheet
    assert '#123456' in stylesheet
    assert 'QFrame[roastEventRail="true"] {\n            background-color: #111111;' in stylesheet


def test_lcd_value_stylesheet_uses_self_contained_surface() -> None:
    stylesheet = gui_theme.lcd_value_stylesheet('#123456', '#abcdef')

    assert 'border-radius: 6px' in stylesheet
    assert 'border-top-left-radius' not in stylesheet
    assert 'border-bottom-left-radius' not in stylesheet
    assert 'padding: 5px 8px 4px 8px' in stylesheet
    assert 'color: #123456' in stylesheet
    assert 'background-color: #abcdef' in stylesheet


def test_modern_toolbar_icon_path_prefers_project_svg_icons() -> None:
    icon_path = modern_toolbar_icon_path('zoom_to_rect', white_icons=False, svg_support=True)

    assert icon_path is not None
    assert icon_path.endswith('/Icons/zoom_to_rect.svg')


def test_modern_toolbar_icon_path_handles_png_names() -> None:
    icon_path = modern_toolbar_icon_path('qt4_editor_options.png', white_icons=False, svg_support=True)

    assert icon_path is not None
    assert icon_path.endswith('/Icons/qt4_editor_options.svg')


def test_lines_toolbar_icons_are_full_size_modern_assets() -> None:
    icon_path = modern_toolbar_icon_path('qt4_editor_options.png', white_icons=False, svg_support=True)
    white_icon_path = modern_toolbar_icon_path('qt4_editor_options.png', white_icons=True, svg_support=True)

    assert icon_path is not None
    assert white_icon_path is not None
    icon_svg = Path(icon_path).read_text(encoding='utf-8')
    white_icon_svg = Path(white_icon_path).read_text(encoding='utf-8')

    assert 'viewBox="0 0 32 32"' in icon_svg
    assert 'stroke-width="3.4"' in icon_svg
    assert 'viewBox="0 0 32 32"' in white_icon_svg
    assert 'stroke-width="3.4"' in white_icon_svg


def test_modern_toolbar_icon_path_uses_cotrix_brand_icon() -> None:
    icon_path = modern_toolbar_icon_path('cotrix', white_icons=False, svg_support=True)
    white_icon_path = modern_toolbar_icon_path('cotrix', white_icons=True, svg_support=True)

    assert icon_path is not None
    assert icon_path.endswith('/Icons/cotrix.svg')
    assert white_icon_path is not None
    assert white_icon_path.endswith('/Icons/white_cotrix.svg')


def test_apply_modern_dialog_polish_sets_runtime_visual_roles(qapp: QApplication) -> None: # noqa: ARG001
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    group_box = QGroupBox('Group')
    group_layout = QVBoxLayout()
    group_layout.setContentsMargins(0, 0, 0, 0)
    group_layout.setSpacing(0)
    group_layout.addWidget(QLineEdit())
    group_box.setLayout(group_layout)

    tab_widget = QTabWidget()
    tab_widget.addTab(QWidget(), 'Tab')

    table_widget = QTableWidget(1, 1)
    button_box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

    layout.addWidget(group_box)
    layout.addWidget(tab_widget)
    layout.addWidget(table_widget)
    layout.addWidget(button_box)
    dialog.setLayout(layout)

    apply_modern_dialog_polish(dialog)

    assert dialog.property('modernDialogPolished') is True
    assert layout.contentsMargins().left() >= 14
    assert layout.spacing() >= 10
    assert group_box.property('modernDialogPanel') is True
    assert group_layout.contentsMargins().left() >= 10
    assert tab_widget.property('modernDialogTabs') is True
    assert tab_widget.documentMode()
    assert not tab_widget.tabBar().expanding()
    assert table_widget.property('modernDialogScrollArea') is True
    assert table_widget.viewport().property('modernDialogViewport') is True
    assert table_widget.alternatingRowColors()
    assert table_widget.showGrid()
    ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
    cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
    assert ok_button is not None
    assert cancel_button is not None
    assert ok_button.property('modernDialogPrimaryButton') is True
    assert cancel_button.property('modernDialogSecondaryButton') is True


def test_apply_modern_dialog_polish_expands_compact_value_controls(qapp: QApplication) -> None: # noqa: ARG001
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    layout = QVBoxLayout()
    combo_box = QComboBox()
    combo_box.addItems(['Minutes', 'Seconds'])
    line_edit = QLineEdit('-12:00')
    line_edit.setMaximumWidth(50)
    line_edit.setProperty('modernExpandValueControl', True)
    spin_box = QSpinBox()
    spin_box.setMaximumWidth(40)
    spin_box.setProperty('modernExpandValueControl', True)
    layout.addWidget(combo_box)
    layout.addWidget(line_edit)
    layout.addWidget(spin_box)
    dialog.setLayout(layout)

    apply_modern_dialog_polish(dialog)

    assert combo_box.minimumContentsLength() >= 7
    assert combo_box.minimumWidth() >= 104
    assert line_edit.minimumWidth() >= 110
    assert line_edit.maximumWidth() >= line_edit.minimumWidth()
    assert spin_box.minimumWidth() >= 110
    assert spin_box.maximumWidth() >= spin_box.minimumWidth()


def test_apply_modern_dialog_polish_preserves_table_cell_layouts(qapp: QApplication) -> None: # noqa: ARG001
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    layout = QVBoxLayout()
    table_widget = QTableWidget(1, 1)
    cell_widget = QWidget()
    cell_layout = QVBoxLayout()
    cell_layout.setContentsMargins(0, 0, 0, 0)
    cell_layout.setSpacing(0)
    cell_widget.setLayout(cell_layout)
    table_widget.setCellWidget(0, 0, cell_widget)
    layout.addWidget(table_widget)
    dialog.setLayout(layout)

    apply_modern_dialog_polish(dialog)

    assert cell_layout.contentsMargins().left() == 0
    assert cell_layout.contentsMargins().top() == 0
    assert cell_layout.spacing() == 0


def test_apply_modern_dialog_polish_preserves_nested_row_margins(
        qapp: QApplication, # noqa: ARG001
) -> None:
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    outer_layout = QVBoxLayout(dialog)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    row_layout = QVBoxLayout()
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(3)
    row_layout.addWidget(QLineEdit())
    outer_layout.addLayout(row_layout)

    apply_modern_dialog_polish(dialog)

    assert outer_layout.contentsMargins().left() >= 14
    assert row_layout.contentsMargins().left() == 0
    assert row_layout.contentsMargins().top() == 0
    assert row_layout.spacing() == 3


def test_axes_time_step_combo_expands_for_flat_theme(qapp: QApplication) -> None:
    from artisanlib.axis import WindowsDlg

    qmc = SimpleNamespace(
        time_grid=True,
        temp_grid=True,
        time_axis_label_mode='minutes',
        gridlinestyle=0,
        gridthickness=1,
        gridalpha=0.2,
        step100temp=None,
        xgrid=120,
        ygrid=10,
        zgrid=5,
        zlimit=25,
        zlimit_min=-15,
        legendloc=4,
        resetmaxtime=0,
        chargemintime=-90,
        fixmaxtime=False,
        locktimex=False,
        autotimex=True,
        autotimexMode=0,
        autodeltaxET=False,
        autodeltaxBT=False,
        loadaxisfromprofile=False,
        startofx=-90,
        endofx=600,
        locktimex_start=-90,
        locktimex_end=600,
        ylimit=275,
        ylimit_min=70,
        ylimit_min_max=-999,
        ylimit_max=999,
        zlimit_min_max=-999,
        zlimit_max=999,
        timeindex=[-1],
        timex=[],
        flagon=False,
        backgroundpath=None,
        crossmarker=False,
        endofx_default=600,
        startofx_default=-90,
        xgrid_default=120,
        mode='C',
        ygrid_C_default=10,
        ylimit_C_default=275,
        ylimit_min_C_default=70,
        zlimit_C_default=25,
        zlimit_min_C_default=-15,
        zgrid_C_default=5,
        redraw=lambda **_kwargs: None,
    )
    aw = SimpleNamespace(
        qmc=qmc,
        comparator=None,
        curFile=None,
        app=qapp,
        sendmessage=lambda *_args: None,
    )
    dialog = WindowsDlg(None, aw)
    original_stylesheet = qapp.styleSheet()
    qapp.setStyleSheet(modern_application_stylesheet())
    try:
        dialog.show()
        qapp.processEvents()
        combo = dialog.xaxislencombobox
        assert combo.itemText(2) == '2 minutes'
        assert combo.property('modernExpandValueControl') is True
        assert combo.width() >= combo.fontMetrics().horizontalAdvance('2 minutes') + 40
        assert combo.maximumWidth() > combo.minimumWidth()
    finally:
        dialog.close()
        qapp.setStyleSheet(original_stylesheet)


@pytest.mark.parametrize('dialog_role', ['devices', 'roast_properties'])
def test_apply_modern_dialog_polish_marks_dense_dialog_tables(
        qapp: QApplication, # noqa: ARG001
        dialog_role: str) -> None:
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    dialog.setProperty('modernDialogRole', dialog_role)
    layout = QVBoxLayout()
    table_widget = QTableWidget(1, 1)
    table_widget.setShowGrid(True)
    combo_box = QComboBox()
    combo_box.addItem('Very long translated device option')
    spin_box = QSpinBox()
    spin_box.setSuffix(' %')
    layout.addWidget(table_widget)
    layout.addWidget(combo_box)
    layout.addWidget(spin_box)
    dialog.setLayout(layout)

    apply_modern_dialog_polish(dialog)

    assert dialog.property('modernDenseDialog') is True
    assert table_widget.property('modernDenseTable') is True
    assert table_widget.horizontalHeader().property('modernDenseHeader') is True
    assert table_widget.verticalHeader().property('modernDenseHeader') is True
    assert table_widget.showGrid()
    assert combo_box.minimumContentsLength() >= len(combo_box.itemText(0))
    assert combo_box.minimumWidth() >= 104
    assert spin_box.minimumWidth() >= 110


def test_apply_modern_dialog_polish_preserves_explicit_narrow_widths(qapp: QApplication) -> None: # noqa: ARG001
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    layout = QVBoxLayout(dialog)
    combo_box = QComboBox()
    combo_box.addItem('一段很长的中文选项')
    combo_box.setMaximumWidth(80)
    line_edit = QLineEdit('long value')
    line_edit.setMaximumWidth(90)
    spin_box = QSpinBox()
    spin_box.setMaximumWidth(96)
    layout.addWidget(combo_box)
    layout.addWidget(line_edit)
    layout.addWidget(spin_box)

    apply_modern_dialog_polish(dialog)

    assert combo_box.maximumWidth() == 80
    assert combo_box.minimumWidth() <= combo_box.maximumWidth()
    assert combo_box.view().minimumWidth() >= combo_box.fontMetrics().horizontalAdvance(
        combo_box.itemText(0)) + 40
    assert line_edit.maximumWidth() == 90
    assert line_edit.minimumWidth() <= line_edit.maximumWidth()
    assert spin_box.maximumWidth() == 96
    assert spin_box.minimumWidth() <= spin_box.maximumWidth()


def test_apply_modern_dialog_polish_respects_widths_with_application_stylesheet(
        qapp: QApplication) -> None:
    original_stylesheet = qapp.styleSheet()
    qapp.setStyleSheet(modern_application_stylesheet())
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    layout = QVBoxLayout(dialog)
    combo_box = QComboBox()
    combo_box.addItem('Port')
    combo_box.setMaximumWidth(80)
    spin_box = QSpinBox()
    spin_box.setMaximumWidth(90)
    layout.addWidget(combo_box)
    layout.addWidget(spin_box)

    apply_modern_dialog_polish(dialog)
    dialog.show()
    qapp.processEvents()

    assert combo_box.minimumWidth() <= combo_box.maximumWidth()
    assert spin_box.minimumWidth() <= spin_box.maximumWidth()
    assert combo_box.width() <= combo_box.maximumWidth()
    assert spin_box.width() <= spin_box.maximumWidth()

    dialog.close()
    qapp.setStyleSheet(original_stylesheet)


def test_apply_modern_dialog_polish_respects_legacy_ui_flag(
        qapp: QApplication, # noqa: ARG001
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('ARTISANZ_LEGACY_UI', '1')
    dialog = QDialog()
    dialog.setProperty('modernDialog', True)
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    dialog.setLayout(layout)

    apply_modern_dialog_polish(dialog)

    assert dialog.property('modernDialogPolished') is not True
    assert layout.contentsMargins().left() == 0
    assert layout.spacing() == 0
