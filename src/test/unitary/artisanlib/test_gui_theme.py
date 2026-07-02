from artisanlib import gui_theme
from artisanlib.gui_theme import ModernTheme, modern_application_stylesheet


def test_modern_application_stylesheet_contains_core_surfaces() -> None:
    stylesheet = modern_application_stylesheet()

    assert 'QMainWindow' in stylesheet
    assert 'QToolBar' in stylesheet
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


def test_modern_application_stylesheet_uses_supplied_theme() -> None:
    theme = ModernTheme(window='#111111', surface='#222222', primary='#123456')

    stylesheet = modern_application_stylesheet(theme)

    assert '#111111' in stylesheet
    assert '#222222' in stylesheet
    assert '#123456' in stylesheet


def test_lcd_value_stylesheet_uses_self_contained_surface() -> None:
    stylesheet = gui_theme.lcd_value_stylesheet('#123456', '#abcdef')

    assert 'border-radius: 6px' in stylesheet
    assert 'border-top-left-radius' not in stylesheet
    assert 'border-bottom-left-radius' not in stylesheet
    assert 'padding: 5px 8px 4px 8px' in stylesheet
    assert 'color: #123456' in stylesheet
    assert 'background-color: #abcdef' in stylesheet
