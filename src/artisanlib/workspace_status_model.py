from __future__ import annotations

from typing import Final

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

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
    implicitHeight: 96

    Rectangle {
        anchors.fill: parent
        color: "#f7f8f5"
        border.color: "#cfd8dc"
        border.width: 1
        radius: 8
    }

    Text {
        id: title
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 14
        color: "#2f3a3d"
        font.pixelSize: 18
        font.weight: Font.DemiBold
        text: root.workspaceModel ? root.workspaceModel.label : ""
        elide: Text.ElideRight
    }

    Row {
        id: statusRow
        anchors.left: title.left
        anchors.top: title.bottom
        anchors.topMargin: 12
        spacing: 8

        Rectangle {
            width: 10
            height: 10
            radius: 5
            anchors.verticalCenter: parent.verticalCenter
            color: root.workspaceModel && root.workspaceModel.compactChrome ? "#7a8a60" : "#0087b3"
        }

        Text {
            color: "#59686c"
            font.pixelSize: 13
            text: root.workspaceModel && root.workspaceModel.showAnalysisTools
                ? qsTr("Analysis")
                : root.workspaceModel && root.workspaceModel.showDeviceSetupTools
                    ? qsTr("Device setup")
                    : qsTr("Roast control")
        }
    }

    Text {
        anchors.left: title.left
        anchors.right: title.right
        anchors.top: statusRow.bottom
        anchors.topMargin: 8
        color: "#6f7c80"
        font.pixelSize: 12
        text: root.workspaceModel && root.workspaceModel.showAdvancedControls
            ? qsTr("Advanced controls")
            : qsTr("Focused controls")
        elide: Text.ElideRight
    }
}
"""


class WorkspaceStatusModel(QObject):
    workspaceChanged = pyqtSignal()

    def __init__(
            self,
            mode: WorkspaceMode = WorkspaceMode.ROAST_CONTROL,
            parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mode = mode

    def workspace_mode(self) -> WorkspaceMode:
        return self._mode

    def set_workspace_mode(self, mode: WorkspaceMode) -> None:
        if mode is self._mode:
            return
        self._mode = mode
        self.workspaceChanged.emit()

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
