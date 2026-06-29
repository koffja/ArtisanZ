from artisanlib.gui_theme import ModernTheme, modern_application_stylesheet


def test_modern_application_stylesheet_contains_core_surfaces() -> None:
    stylesheet = modern_application_stylesheet()

    assert 'QMainWindow' in stylesheet
    assert 'QToolBar' in stylesheet
    assert 'QMenuBar' in stylesheet
    assert 'QPushButton' in stylesheet
    assert 'QLCDNumber[lcdSurface="true"]' in stylesheet
    assert 'QFrame[lcdSurface="true"]' in stylesheet
    assert 'QLabel[lcdLabel="true"]' in stylesheet


def test_modern_application_stylesheet_uses_supplied_theme() -> None:
    theme = ModernTheme(window='#111111', surface='#222222', primary='#123456')

    stylesheet = modern_application_stylesheet(theme)

    assert '#111111' in stylesheet
    assert '#222222' in stylesheet
    assert '#123456' in stylesheet
