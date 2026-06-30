from __future__ import annotations

import dataclasses
import importlib
from typing import Any

import pytest


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


class FakeMenuBar:
    def __init__(self) -> None:
        self.menus: list[str] = []
        self.clear_count = 0

    def clear(self) -> None:
        self.menus.clear()
        self.clear_count += 1

    def addMenu(self, menu: str) -> None:
        self.menus.append(menu)


class FakeApplicationWindow:
    def __init__(self) -> None:
        main = main_module()
        workspaces = workspace_module()

        self.ui_mode = main.UI_MODE.DEFAULT
        self.workspace_mode = workspaces.workspace_for_ui_mode_value(int(self.ui_mode))
        self.workspace_policy = workspaces.workspace_policy(self.workspace_mode)
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


class FakeMenuApplicationWindow:
    def __init__(self) -> None:
        self.menu_bar = FakeMenuBar()

    def menuBar(self) -> FakeMenuBar:
        return self.menu_bar

    def create_file_menu(self, _ui_mode: object) -> str:
        return 'file'

    def create_edit_menu(self, _ui_mode: object) -> str:
        return 'edit'

    def create_roast_menu(self, _ui_mode: object) -> str:
        return 'roast'

    def create_config_menu(self, _ui_mode: object) -> str:
        return 'config'

    def create_tools_menu(self, _ui_mode: object) -> str:
        return 'tools'

    def create_view_menu(self, _ui_mode: object) -> str:
        return 'view'

    def create_help_menu(self, _ui_mode: object) -> str:
        return 'help'


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
    assert window.workspace_policy is workspaces.workspace_policy(workspaces.WorkspaceMode.EXPERT)
    assert window.expertModeAction.checked is True
    assert window.defaultModeAction.checked is False
    assert window.productionModeAction.checked is False
    assert window.ntb.actions[-1] == 'add'

    main.ApplicationWindow.set_ui_mode(window, main.UI_MODE.DEFAULT)
    assert window.workspace_mode is workspaces.WorkspaceMode.ROAST_CONTROL
    assert window.workspace_policy is workspaces.workspace_policy(workspaces.WorkspaceMode.ROAST_CONTROL)
    assert window.defaultModeAction.checked is True
    assert window.ntb.actions[-1] == 'remove'

    main.ApplicationWindow.set_ui_mode(window, main.UI_MODE.PRODUCTION)
    assert window.workspace_mode is workspaces.WorkspaceMode.PRODUCTION
    assert window.workspace_policy is workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    assert window.productionModeAction.checked is True
    assert window.ntb.actions[-1] == 'remove'
    assert window.menus == [
        main.UI_MODE.EXPERT,
        main.UI_MODE.DEFAULT,
        main.UI_MODE.PRODUCTION,
    ]
    assert window.announcements == 3


def test_application_window_set_toolbar_uses_workspace_policy() -> None:
    main = main_module()
    window = FakeApplicationWindow()

    main.ApplicationWindow.set_toolbar(window, main.UI_MODE.EXPERT)
    main.ApplicationWindow.set_toolbar(window, main.UI_MODE.DEFAULT)
    main.ApplicationWindow.set_toolbar(window, main.UI_MODE.PRODUCTION)

    assert window.ntb.actions == ['add', 'remove', 'remove']


def test_application_window_set_menu_preserves_current_tools_visibility() -> None:
    main = main_module()

    expected_tools_visibility = {
        main.UI_MODE.EXPERT: True,
        main.UI_MODE.DEFAULT: True,
        main.UI_MODE.PRODUCTION: False,
    }
    for ui_mode, should_show_tools in expected_tools_visibility.items():
        window = FakeMenuApplicationWindow()
        main.ApplicationWindow.set_menu(window, ui_mode)

        assert window.menu_bar.clear_count == 1
        assert ('tools' in window.menu_bar.menus) is should_show_tools


def test_application_window_set_menu_uses_workspace_policy_for_tools_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    window = FakeMenuApplicationWindow()
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    full_menu_policy = dataclasses.replace(production_policy, show_full_menus=True)

    def fake_workspace_policy(_mode: object) -> object:
        return full_menu_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)

    main.ApplicationWindow.set_menu(window, main.UI_MODE.PRODUCTION)

    assert window.menu_bar.menus == ['file', 'edit', 'roast', 'config', 'tools', 'view', 'help']


def test_workspace_policy_is_frozen_and_immutable() -> None:
    workspaces = workspace_module()

    policy = workspaces.workspace_policy(workspaces.WorkspaceMode.EXPERT)
    mutable_policy: Any = policy

    assert dataclasses.is_dataclass(policy)
    with pytest.raises(dataclasses.FrozenInstanceError):
        mutable_policy.show_full_menus = False


def test_workspace_policy_returns_policy_for_every_mode() -> None:
    workspaces = workspace_module()

    for mode in workspaces.WorkspaceMode:
        policy = workspaces.workspace_policy(mode)
        assert policy.mode is mode


def test_roast_control_policy_hides_expert_tools_and_analysis() -> None:
    workspaces = workspace_module()

    policy = workspaces.workspace_policy(workspaces.WorkspaceMode.ROAST_CONTROL)

    assert not policy.show_advanced_controls
    assert not policy.show_analysis_tools
    assert not policy.show_device_setup_tools
    assert not policy.compact_chrome
    assert policy.show_full_menus
    assert policy.show_full_toolbars
    assert policy.show_side_panels


def test_qc_analysis_policy_includes_analysis_without_expert_tools() -> None:
    workspaces = workspace_module()

    policy = workspaces.workspace_policy(workspaces.WorkspaceMode.QC_ANALYSIS)

    assert policy.show_analysis_tools
    assert not policy.show_advanced_controls
    assert not policy.show_device_setup_tools
    assert not policy.compact_chrome


def test_device_setup_policy_exposes_device_setup_and_advanced_navigation() -> None:
    workspaces = workspace_module()

    policy = workspaces.workspace_policy(workspaces.WorkspaceMode.DEVICE_SETUP)

    assert policy.show_device_setup_tools
    assert policy.show_advanced_controls
    assert not policy.compact_chrome


def test_production_policy_uses_compact_chrome_without_expert_tools() -> None:
    workspaces = workspace_module()

    policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)

    assert policy.compact_chrome
    assert not policy.show_advanced_controls
    assert not policy.show_analysis_tools
    assert not policy.show_device_setup_tools
    assert not policy.show_full_menus
    assert not policy.show_full_toolbars
    assert not policy.show_side_panels


def test_expert_policy_exposes_all_tools_and_surfaces() -> None:
    workspaces = workspace_module()

    policy = workspaces.workspace_policy(workspaces.WorkspaceMode.EXPERT)

    assert policy.show_advanced_controls
    assert policy.show_analysis_tools
    assert policy.show_device_setup_tools
    assert policy.show_full_menus
    assert policy.show_full_toolbars
    assert policy.show_side_panels
    assert not policy.compact_chrome


def test_workspace_policy_compact_chrome_aligns_with_spec() -> None:
    workspaces = workspace_module()

    for mode in workspaces.WorkspaceMode:
        spec = workspaces.workspace_spec(mode)
        policy = workspaces.workspace_policy(mode)
        assert policy.compact_chrome is spec.compact_chrome, mode


def test_workspace_policy_exports_in_all() -> None:
    workspaces = workspace_module()

    assert 'WorkspacePolicy' in workspaces.__all__
    assert 'workspace_policy' in workspaces.__all__
