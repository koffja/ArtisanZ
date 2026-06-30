from __future__ import annotations

import importlib


def workspace_module():
    return importlib.import_module('artisanlib.ui_workspaces')


def main_module():
    return importlib.import_module('artisanlib.main')


class FakeAction:
    def __init__(self) -> None:
        self.checked: bool | None = None

    def setChecked(self, checked: bool) -> None:
        self.checked = checked


class FakeToolbar:
    def __init__(self) -> None:
        self.actions: list[str] = []

    def add_toolbar_lines_configuration(self) -> None:
        self.actions.append('add')

    def remove_toolbar_lines_configuration(self) -> None:
        self.actions.append('remove')


class FakeApplicationWindow:
    def __init__(self) -> None:
        main = main_module()
        workspaces = workspace_module()

        self.ui_mode = main.UI_MODE.DEFAULT
        self.workspace_mode = workspaces.workspace_for_ui_mode_value(int(self.ui_mode))
        self.productionModeAction = FakeAction()
        self.defaultModeAction = FakeAction()
        self.expertModeAction = FakeAction()
        self.ntb = FakeToolbar()
        self.menus: list[object] = []
        self.announcements = 0

    def set_menu(self, ui_mode: object) -> None:
        self.menus.append(ui_mode)

    def set_toolbar(self, ui_mode: object) -> None:
        main = main_module()
        main.ApplicationWindow.set_toolbar(self, ui_mode)

    def announce_current_ui_mode(self) -> None:
        self.announcements += 1


def test_workspace_for_existing_ui_modes_maps_standard_to_roast_control() -> None:
    workspaces = workspace_module()

    assert workspaces.workspace_for_ui_mode_value(1) is workspaces.WorkspaceMode.EXPERT
    assert workspaces.workspace_for_ui_mode_value(2) is workspaces.WorkspaceMode.ROAST_CONTROL
    assert workspaces.workspace_for_ui_mode_value(3) is workspaces.WorkspaceMode.PRODUCTION


def test_mapper_unknown_ui_mode_falls_back_to_roast_control() -> None:
    workspaces = workspace_module()

    assert workspaces.workspace_for_ui_mode_value(0) is workspaces.WorkspaceMode.ROAST_CONTROL
    assert workspaces.workspace_for_ui_mode_value(999) is workspaces.WorkspaceMode.ROAST_CONTROL


def test_production_workspace_keeps_roast_controls_without_expert_surface() -> None:
    workspaces = workspace_module()

    spec = workspaces.workspace_spec(workspaces.WorkspaceMode.PRODUCTION)

    assert spec.primary_area is workspaces.WorkspaceArea.ROAST_CONTROL
    assert workspaces.WorkspaceArea.PRODUCTION_BATCH in spec.visible_areas
    assert workspaces.WorkspaceArea.EXPERT_TOOLS not in spec.visible_areas
    assert spec.compact_chrome


def test_expert_workspace_keeps_all_task_surfaces_available() -> None:
    workspaces = workspace_module()

    spec = workspaces.workspace_spec(workspaces.WorkspaceMode.EXPERT)

    assert set(spec.visible_areas) == {
        workspaces.WorkspaceArea.ROAST_CONTROL,
        workspaces.WorkspaceArea.QC_ANALYSIS,
        workspaces.WorkspaceArea.DEVICE_SETUP,
        workspaces.WorkspaceArea.PRODUCTION_BATCH,
        workspaces.WorkspaceArea.EXPERT_TOOLS,
    }
    assert not spec.compact_chrome
    assert spec.show_advanced_navigation


def test_all_workspace_specs_have_stable_labels_and_primary_areas() -> None:
    workspaces = workspace_module()

    specs = workspaces.workspace_specs()

    assert tuple(spec.mode for spec in specs) == tuple(workspaces.WorkspaceMode)
    assert all(spec.label_key for spec in specs)
    assert all(spec.primary_area in spec.visible_areas for spec in specs)


def test_application_window_set_ui_mode_syncs_workspace_and_toolbar_policy() -> None:
    main = main_module()
    workspaces = workspace_module()
    window = FakeApplicationWindow()

    main.ApplicationWindow.set_ui_mode(window, main.UI_MODE.EXPERT)

    assert window.workspace_mode is workspaces.WorkspaceMode.EXPERT
    assert window.expertModeAction.checked is True
    assert window.defaultModeAction.checked is False
    assert window.productionModeAction.checked is False
    assert window.ntb.actions[-1] == 'add'

    main.ApplicationWindow.set_ui_mode(window, main.UI_MODE.DEFAULT)
    assert window.workspace_mode is workspaces.WorkspaceMode.ROAST_CONTROL
    assert window.defaultModeAction.checked is True
    assert window.ntb.actions[-1] == 'remove'

    main.ApplicationWindow.set_ui_mode(window, main.UI_MODE.PRODUCTION)
    assert window.workspace_mode is workspaces.WorkspaceMode.PRODUCTION
    assert window.productionModeAction.checked is True
    assert window.ntb.actions[-1] == 'remove'
    assert window.menus == [
        main.UI_MODE.EXPERT,
        main.UI_MODE.DEFAULT,
        main.UI_MODE.PRODUCTION,
    ]
    assert window.announcements == 3
