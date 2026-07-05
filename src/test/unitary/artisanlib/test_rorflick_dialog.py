import pytest
from PyQt6.QtWidgets import QApplication
from artisanlib.rorflick_manager import RoRFlickManager
from artisanlib.rorflick_dialog import RoRFlickDlg


@pytest.fixture(scope='module')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_dialog_loads_settings_from_manager(qapp):
    m = RoRFlickManager()
    m.update_settings(
        enabled=True,
        flick_threshold=4.5,
        crash_threshold=6.0,
        exit_threshold=0.8,
        dev_phase_multiplier=1.8,
    )
    dlg = RoRFlickDlg(None, m)
    assert dlg.flick_spinbox.value() == pytest.approx(4.5)
    assert dlg.crash_spinbox.value() == pytest.approx(6.0)
    assert dlg.exit_spinbox.value() == pytest.approx(0.8)
    assert dlg.dev_spinbox.value() == pytest.approx(1.8)
    assert dlg.enabled_checkbox.isChecked() is True


def test_dialog_save_pushes_values_back_to_manager(qapp):
    m = RoRFlickManager()
    dlg = RoRFlickDlg(None, m)
    dlg.flick_spinbox.setValue(7.2)
    dlg.crash_spinbox.setValue(8.1)
    dlg.exit_spinbox.setValue(0.3)
    dlg.dev_spinbox.setValue(2.1)
    dlg.enabled_checkbox.setChecked(True)
    dlg.save()

    assert m.enabled is True
    assert m.flick_threshold == pytest.approx(7.2)
    assert m.crash_threshold == pytest.approx(8.1)
    assert m.exit_threshold == pytest.approx(0.3)
    assert m.dev_phase_multiplier == pytest.approx(2.1)


def test_dialog_preset_buttons_set_thresholds(qapp):
    from artisanlib.rorflick_manager import RoRFlickManager
    from artisanlib.rorflick_dialog import RoRFlickDlg
    m = RoRFlickManager()
    dlg = RoRFlickDlg(None, m)

    # Test electric preset
    dlg._apply_preset('electric')
    assert dlg.flick_spinbox.value() == 3.0
    assert dlg.crash_spinbox.value() == 3.0
    assert dlg.exit_spinbox.value() == 0.5

    # Test gas preset
    dlg._apply_preset('gas')
    assert dlg.flick_spinbox.value() == 7.0
    assert dlg.crash_spinbox.value() == 7.0
    assert dlg.exit_spinbox.value() == 1.5

    # Test sample preset
    dlg._apply_preset('sample')
    assert dlg.flick_spinbox.value() == 5.0
    assert dlg.crash_spinbox.value() == 5.0
    assert dlg.exit_spinbox.value() == 1.0
