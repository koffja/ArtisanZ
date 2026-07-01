from __future__ import annotations

import importlib
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlComponent, QQmlEngine
from PyQt6.QtWidgets import QApplication

from artisanlib.ui_workspaces import WorkspaceMode
from artisanlib.workspace_status_model import (
    WORKSPACE_STATUS_PANEL_QML,
    WorkspaceStatusModel,
    create_workspace_status_widget,
    qml_data_url,
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


def test_workspace_status_widget_factory_loads_qml_with_python_model() -> None:
    _app = QApplication.instance() or QApplication([])
    model = WorkspaceStatusModel(WorkspaceMode.QC_ANALYSIS)

    widget = create_workspace_status_widget(model)

    try:
        assert widget.status() == widget.Status.Ready, [
            error.toString() for error in widget.errors()
        ]
        assert widget.resizeMode() == widget.ResizeMode.SizeRootObjectToView
        root_object = widget.rootObject()
        assert root_object is not None
        assert root_object.property('workspaceModel') is model
        assert widget.sizeHint().width() == 320
        assert widget.sizeHint().height() == 96
    finally:
        widget.deleteLater()


def test_qml_data_url_encodes_inline_qml_source() -> None:
    url = qml_data_url('import QtQuick\nItem { property string label: "QC Analysis" }')

    url_text = url.toString()
    assert url.scheme() == 'data'
    assert url_text.startswith('data:text/plain;charset=utf-8,')
    assert '%0A' in url_text
    assert '%7B' in url_text


def test_qtquick_pyinstaller_hidden_imports_reference_real_pyqt_modules() -> None:
    src_dir = Path(__file__).parents[3]
    hidden_imports = (
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
    )
    phantom_imports = (
        'PyQt6.QtQmlMeta',
        'PyQt6.QtQmlModels',
        'PyQt6.QtQmlWorkerScript',
    )

    for module_name in hidden_imports:
        importlib.import_module(module_name)

    for spec_name in ('artisan-linux.spec', 'artisan-mac.spec', 'artisan-win.spec'):
        spec_text = (src_dir / spec_name).read_text(encoding='utf-8')
        for module_name in hidden_imports:
            assert module_name in spec_text
        for module_name in phantom_imports:
            assert module_name not in spec_text
