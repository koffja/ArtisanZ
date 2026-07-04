from __future__ import annotations

from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication, QTabWidget


def test_curves_dlg_has_phase_style_tab() -> None:
    """CurvesDlg must add a 7th Phase & Style tab with expected widgets."""
    _app = QApplication.instance() or QApplication([])
    _app.artisanviewerMode = False

    from artisanlib.curves import CurvesDlg

    dlg = SimpleNamespace()
    dlg.TabWidget = QTabWidget()
    for index in range(6):
        dlg.TabWidget.addTab(QTabWidget(), f'Tab {index}')
    dlg.aw = SimpleNamespace(
        qmc=SimpleNamespace(
            palette={
                'rect1': '#E8DDD2',
                'rect2': '#D8C5B0',
                'rect3': '#C7D1C2',
            },
            backgroundalpha=0.35,
        ),
        labelBorW=lambda _color: '#000000',
    )

    CurvesDlg._add_phase_style_tab(dlg)

    assert dlg.TabWidget.count() >= 7
    assert 'Phase' in dlg.TabWidget.tabText(6) or 'Style' in dlg.TabWidget.tabText(6)
    tab = dlg.TabWidget.widget(6)
    for name in (
        'rect1ColorButton',
        'rect2ColorButton',
        'rect3ColorButton',
        'phaseBandOpacitySlider',
        'btGradientCheckBox',
        'bgAlphaSlider',
        'bgStyleComboBox',
        'phaseLabelsCheckBox',
        'restoreDefaultsButton',
    ):
        assert tab.findChild(object, name) is not None
