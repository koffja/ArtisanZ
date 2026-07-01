from __future__ import annotations

from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtWidgets import QApplication

from artisanlib.ui_workspaces import WorkspaceMode
from artisanlib.workspace_status_model import (
    WORKSPACE_STATUS_PANEL_QML,
    WorkspaceStatusModel,
)


def test_workspace_status_model_exposes_policy_properties() -> None:
    model = WorkspaceStatusModel(WorkspaceMode.QC_ANALYSIS)

    assert model.workspace_mode() is WorkspaceMode.QC_ANALYSIS
    assert model.modeValue == 'qc_analysis'
    assert model.label == 'QC Analysis'
    assert model.primaryArea == 'qc_analysis'
    assert model.showAnalysisTools is True
    assert model.showDeviceSetupTools is False
    assert model.showAdvancedControls is False
    assert model.compactChrome is False


def test_workspace_status_model_updates_from_workspace_mode() -> None:
    model = WorkspaceStatusModel()
    notifications: list[None] = []
    model.workspaceChanged.connect(lambda: notifications.append(None))

    model.set_workspace_mode(WorkspaceMode.DEVICE_SETUP)

    assert model.workspace_mode() is WorkspaceMode.DEVICE_SETUP
    assert model.modeValue == 'device_setup'
    assert model.label == 'Device Setup'
    assert model.showDeviceSetupTools is True
    assert model.showAdvancedControls is True
    assert len(notifications) == 1

    model.set_workspace_mode(WorkspaceMode.DEVICE_SETUP)
    assert len(notifications) == 1


def test_workspace_status_model_updates_from_qml_slot_value() -> None:
    model = WorkspaceStatusModel(WorkspaceMode.ROAST_CONTROL)

    model.setWorkspaceModeValue('expert')

    assert model.workspace_mode() is WorkspaceMode.EXPERT
    assert model.showAnalysisTools is True
    assert model.showDeviceSetupTools is True


def test_workspace_status_model_ignores_unknown_qml_slot_value() -> None:
    model = WorkspaceStatusModel(WorkspaceMode.PRODUCTION)

    model.setWorkspaceModeValue('future_workspace')

    assert model.workspace_mode() is WorkspaceMode.PRODUCTION


def test_workspace_status_panel_qml_compiles() -> None:
    _app = QApplication.instance() or QApplication([])
    engine = QQmlEngine()
    component = QQmlComponent(engine)

    component.setData(WORKSPACE_STATUS_PANEL_QML.encode('utf-8'), QUrl())

    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]


def test_workspace_status_panel_qml_accepts_python_model() -> None:
    _app = QApplication.instance() or QApplication([])
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    model = WorkspaceStatusModel(WorkspaceMode.DEVICE_SETUP)

    component.setData(WORKSPACE_STATUS_PANEL_QML.encode('utf-8'), QUrl())
    item = component.create()

    try:
        assert item is not None, [error.toString() for error in component.errors()]
        assert item.setProperty('workspaceModel', model)
        assert item.property('implicitWidth') == 320
        assert item.property('implicitHeight') == 96
    finally:
        if item is not None:
            item.deleteLater()
