from __future__ import annotations

from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication

from artisanlib.plot_curve_style_dialog import CurveStyleDialog


def _qmc() -> SimpleNamespace:
    return SimpleNamespace(
        palette={
            'et': '#A76557',
            'bt': '#4E7180',
            'deltaet': '#D4943A',
            'deltabt': '#90A1A8',
        },
        ETlinestyle='-',
        ETlinewidth=2.0,
        BTlinestyle='-',
        BTlinewidth=2.0,
        ETdeltalinestyle='-',
        ETdeltalinewidth=1.0,
        BTdeltalinestyle='-',
        BTdeltalinewidth=1.0,
        linewidth_default=2.0,
        delta_linewidth_default=1.0,
    )


def test_curve_style_dialog_applies_renderer_neutral_core_curve_settings() -> None:
    _app = QApplication.instance() or QApplication([])
    qmc = _qmc()
    applied: list[bool] = []
    dialog = CurveStyleDialog(None, qmc, apply_callback=lambda: applied.append(True))

    dialog.curveComboBox.setCurrentText('BT')
    dialog.styleComboBox.setCurrentIndex(dialog.styleComboBox.findData('--'))
    dialog.widthSpinBox.setValue(3.5)
    dialog.accept()

    assert qmc.BTlinestyle == '--'
    assert qmc.BTlinewidth == 3.5
    assert qmc.palette['bt'] == '#4E7180'
    assert applied == [True]


def test_curve_style_dialog_cancel_does_not_mutate_qmc() -> None:
    _app = QApplication.instance() or QApplication([])
    qmc = _qmc()
    dialog = CurveStyleDialog(None, qmc)
    dialog.curveComboBox.setCurrentText('BT')
    dialog.styleComboBox.setCurrentIndex(dialog.styleComboBox.findData(':'))
    dialog.widthSpinBox.setValue(4.0)
    dialog.reject()

    assert qmc.BTlinestyle == '-'
    assert qmc.BTlinewidth == 2.0


def test_curve_style_dialog_keeps_edits_when_switching_curves() -> None:
    _app = QApplication.instance() or QApplication([])
    qmc = _qmc()
    dialog = CurveStyleDialog(None, qmc)

    dialog.curveComboBox.setCurrentText('BT')
    dialog.styleComboBox.setCurrentIndex(dialog.styleComboBox.findData('--'))
    dialog.widthSpinBox.setValue(3.5)
    dialog.curveComboBox.setCurrentText('ET')
    dialog.accept()

    assert qmc.BTlinestyle == '--'
    assert qmc.BTlinewidth == 3.5


def test_curve_style_dialog_restore_defaults_uses_artisan_palette() -> None:
    _app = QApplication.instance() or QApplication([])
    qmc = _qmc()
    qmc.palette['bt'] = '#123456'
    qmc.BTlinestyle = ':'
    qmc.BTlinewidth = 4.0
    dialog = CurveStyleDialog(None, qmc)

    dialog.curveComboBox.setCurrentText('BT')
    dialog._restore_defaults()
    dialog.accept()

    assert qmc.BTlinestyle == '-'
    assert qmc.BTlinewidth == 2.0
    assert qmc.palette['bt'] == '#3A7CA5'
