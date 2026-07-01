from __future__ import annotations

from typing import Final
from urllib.parse import quote

from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtQuickWidgets import QQuickWidget
from PyQt6.QtWidgets import QWidget

from artisanlib.plot_renderer_settings import DEFAULT_RENDERER_ID, RendererSelection
from artisanlib.ui_workspaces import (
    WorkspaceMode,
    workspace_from_setting_value,
    workspace_policy,
    workspace_spec,
)


WORKSPACE_STATUS_PANEL_QML: Final[str] = """
import QtQuick

Item {
    id: root
    property var workspaceModel
    implicitWidth: 320
    implicitHeight: 156
    readonly property color accentColor: !root.workspaceModel
        ? "#0087b3"
        : root.workspaceModel.modeValue === "qc_analysis"
            ? "#0087b3"
            : root.workspaceModel.modeValue === "device_setup"
                ? "#7a8a60"
                : root.workspaceModel.modeValue === "production"
                    ? "#b46a55"
                    : root.workspaceModel.modeValue === "expert"
                        ? "#4f5f66"
                        : "#0087b3"
    readonly property string areaLabel: root.workspaceModel && root.workspaceModel.showAnalysisTools
        ? qsTr("Analysis")
        : root.workspaceModel && root.workspaceModel.showDeviceSetupTools
            ? qsTr("Device setup")
            : qsTr("Roast control")
    readonly property string controlLabel: root.workspaceModel && root.workspaceModel.showAdvancedControls
        ? qsTr("Advanced")
        : qsTr("Focused")

    Rectangle {
        anchors.fill: parent
        color: "#fbfcfa"
        border.color: "#d2dde1"
        border.width: 1
        radius: 8
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 5
        color: root.accentColor
        radius: 8
    }

    Text {
        id: title
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 18
        anchors.rightMargin: 16
        anchors.topMargin: 14
        color: "#2f3a3d"
        font.pixelSize: 17
        font.weight: Font.DemiBold
        text: root.workspaceModel ? root.workspaceModel.label : ""
        elide: Text.ElideRight
    }

    Text {
        id: modeValue
        anchors.left: title.left
        anchors.top: title.bottom
        anchors.topMargin: 4
        color: "#718084"
        font.pixelSize: 12
        text: root.workspaceModel ? root.workspaceModel.modeValue : ""
        elide: Text.ElideRight
    }

    Row {
        id: statusRow
        anchors.left: title.left
        anchors.right: title.right
        anchors.top: modeValue.bottom
        anchors.topMargin: 14
        spacing: 8

        Rectangle {
            width: areaText.implicitWidth + 20
            height: 26
            radius: 13
            color: "#eef4f5"
            border.color: "#d5e0e3"

            Text {
                id: areaText
                anchors.centerIn: parent
                color: root.accentColor
                font.pixelSize: 12
                font.weight: Font.DemiBold
                text: root.areaLabel
                elide: Text.ElideRight
            }
        }

        Rectangle {
            width: controlText.implicitWidth + 20
            height: 26
            radius: 13
            color: root.workspaceModel && root.workspaceModel.compactChrome ? "#f3eee8" : "#f4f5f1"
            border.color: root.workspaceModel && root.workspaceModel.compactChrome ? "#e0d2c8" : "#dce2d3"

            Text {
                id: controlText
                anchors.centerIn: parent
                color: root.workspaceModel && root.workspaceModel.compactChrome ? "#9b5f4f" : "#68765b"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                text: root.controlLabel
                elide: Text.ElideRight
            }
        }
    }

    Text {
        id: controlSummary
        anchors.left: title.left
        anchors.right: title.right
        anchors.top: statusRow.bottom
        anchors.topMargin: 9
        color: "#6f7c80"
        font.pixelSize: 12
        text: root.workspaceModel && root.workspaceModel.showAdvancedControls
            ? qsTr("Full menu access")
            : qsTr("Reduced control surface")
        elide: Text.ElideRight
    }

    Row {
        anchors.left: title.left
        anchors.right: title.right
        anchors.top: controlSummary.bottom
        anchors.topMargin: 9
        spacing: 6

        Rectangle {
            width: 7
            height: 7
            radius: 2
            anchors.verticalCenter: rendererText.verticalCenter
            color: root.workspaceModel && root.workspaceModel.rendererFallbackReason !== ""
                ? "#b46a55"
                : root.accentColor
        }

        Text {
            id: rendererText
            width: parent.width - 13
            color: "#4f5f66"
            font.pixelSize: 12
            text: root.workspaceModel
                ? qsTr("Renderer") + ": " + root.workspaceModel.rendererLabel
                    + " - " + root.workspaceModel.rendererStatusLabel
                : ""
            elide: Text.ElideRight
        }
    }
}
"""


class WorkspaceStatusModel(QObject):
    workspaceChanged = pyqtSignal()
    rendererChanged = pyqtSignal()

    def __init__(
            self,
            mode: WorkspaceMode = WorkspaceMode.ROAST_CONTROL,
            parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mode = mode
        self._renderer_id = DEFAULT_RENDERER_ID
        self._renderer_label = 'Matplotlib Snapshot'
        self._renderer_fallback_reason = ''

    def workspace_mode(self) -> WorkspaceMode:
        return self._mode

    def set_workspace_mode(self, mode: WorkspaceMode) -> None:
        if mode is self._mode:
            return
        self._mode = mode
        self.workspaceChanged.emit()

    def set_renderer_selection(self, selection: RendererSelection | None) -> None:
        renderer_id = selection.renderer_id if selection is not None else DEFAULT_RENDERER_ID
        renderer_label = selection.plugin.label if selection is not None else 'Matplotlib Snapshot'
        fallback_reason = (selection.fallback_reason or '') if selection is not None else ''
        if (
                renderer_id == self._renderer_id and
                renderer_label == self._renderer_label and
                fallback_reason == self._renderer_fallback_reason):
            return
        self._renderer_id = renderer_id
        self._renderer_label = renderer_label
        self._renderer_fallback_reason = fallback_reason
        self.rendererChanged.emit()

    @pyqtSlot(str)
    def setWorkspaceModeValue(self, value: str) -> None:
        self.set_workspace_mode(workspace_from_setting_value(value, self._mode))

    @pyqtProperty(str, notify=workspaceChanged)
    def modeValue(self) -> str:
        return self._mode.value

    @pyqtProperty(str, notify=workspaceChanged)
    def label(self) -> str:
        return workspace_spec(self._mode).label_key

    @pyqtProperty(str, notify=workspaceChanged)
    def primaryArea(self) -> str:
        return workspace_spec(self._mode).primary_area.value

    @pyqtProperty(bool, notify=workspaceChanged)
    def compactChrome(self) -> bool:
        return workspace_policy(self._mode).compact_chrome

    @pyqtProperty(bool, notify=workspaceChanged)
    def showAdvancedControls(self) -> bool:
        return workspace_policy(self._mode).show_advanced_controls

    @pyqtProperty(bool, notify=workspaceChanged)
    def showAnalysisTools(self) -> bool:
        return workspace_policy(self._mode).show_analysis_tools

    @pyqtProperty(bool, notify=workspaceChanged)
    def showDeviceSetupTools(self) -> bool:
        return workspace_policy(self._mode).show_device_setup_tools

    @pyqtProperty(str, notify=rendererChanged)
    def rendererId(self) -> str:
        return self._renderer_id

    @pyqtProperty(str, notify=rendererChanged)
    def rendererLabel(self) -> str:
        return self._renderer_label

    @pyqtProperty(str, notify=rendererChanged)
    def rendererFallbackReason(self) -> str:
        return self._renderer_fallback_reason

    @pyqtProperty(str, notify=rendererChanged)
    def rendererStatusLabel(self) -> str:
        if not self._renderer_fallback_reason:
            return 'Selected'
        if self._renderer_fallback_reason == 'selection_error':
            return 'Fallback active'
        if self._renderer_fallback_reason == 'unavailable':
            return 'Dependency fallback'
        if self._renderer_fallback_reason == 'default_unavailable':
            return 'Default fallback'
        return 'Fallback active'


def qml_data_url(qml_source: str) -> QUrl:
    return QUrl(f"data:text/plain;charset=utf-8,{quote(qml_source)}")


def create_workspace_status_widget(
        model: WorkspaceStatusModel,
        parent: QWidget | None = None) -> QQuickWidget:
    widget = QQuickWidget(parent)
    widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
    widget.setInitialProperties({'workspaceModel': model})
    widget.setSource(qml_data_url(WORKSPACE_STATUS_PANEL_QML))
    widget.setMinimumSize(widget.sizeHint())
    return widget
