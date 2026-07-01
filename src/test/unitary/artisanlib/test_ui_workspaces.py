from __future__ import annotations

import dataclasses
import importlib
from typing import Any, ClassVar

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


class FakeMenuAction:
    def __init__(self, label: str) -> None:
        self.label = label
        self.enabled: bool | None = None

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled


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


class FakeMenu:
    def __init__(self, title: str = '') -> None:
        self.title = title
        self.items: list[str] = []

    def addAction(self, action: object) -> None:
        self.items.append(getattr(action, 'label', action))

    def addMenu(self, menu: str) -> None:
        self.items.append(menu)

    def addSeparator(self) -> None:
        self.items.append('separator')


class FakeSignal:
    def __init__(self) -> None:
        self.connected_to: object | None = None

    def connect(self, slot: object) -> None:
        self.connected_to = slot


class FakeQAction:
    instances: ClassVar[list[FakeQAction]] = []

    def __init__(self, text: str, _parent: object | None = None) -> None:
        self.label = text
        self.triggered = FakeSignal()
        self.instances.append(self)

    def __repr__(self) -> str:
        return repr(self.label)


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


class FakeHelpMenuApplicationWindow:
    def __init__(self) -> None:
        self.helpAboutAction = 'about'
        self.aboutQtAction = 'about-qt'
        self.helpDocumentationAction = 'docs'
        self.KshortCAction = 'shortcuts'
        self.checkUpdateAction = 'check-update'
        self.errorAction = 'error'
        self.messageAction = 'message'
        self.serialAction = 'serial'
        self.platformAction = 'platform'
        self.loadSettingsAction = 'load-settings'
        self.openRecentSettingMenu = 'recent-settings'
        self.saveAsSettingsAction = 'save-settings'
        self.resetAction = 'reset'


class FakeFileMenuApplicationWindow:
    def __init__(self) -> None:
        self.newRoastMenu = 'new'
        self.fileLoadAction = 'load'
        self.openRecentMenu = 'recent'
        self.importMenu = 'import'
        self.convFromMenu = 'convert-from'
        self.fileSaveAction = 'save'
        self.fileSaveAsAction = 'save-as'
        self.fileSaveCopyAsAction = 'save-copy-as'
        self.exportMenu = 'export'
        self.convMenu = 'convert-to'
        self.saveGraphMenu = 'save-graph'
        self.reportMenu = 'report'
        self.saveStatisticsMenu = 'statistics'
        self.printAction = 'print'
        self.quitAction = 'quit'


class FakeConfigMenuApplicationWindow:
    def __init__(self) -> None:
        self.machineMenu = 'machine'
        self.deviceAction = 'device'
        self.commportAction = 'comm-port'
        self.calibrateDelayAction = 'calibrate-delay'
        self.curvesAction = 'curves'
        self.eventsAction = 'events'
        self.alarmAction = 'alarm'
        self.phasesGraphAction = 'phases'
        self.StatisticsAction = 'statistics'
        self.WindowconfigAction = 'window-config'
        self.colorsAction = 'colors'
        self.themeMenu = 'theme'
        self.autosaveAction = 'autosave'
        self.batchAction = 'batch'
        self.temperatureConfMenu = 'temperature'
        self.languageMenu = 'language'
        self.UIModeMenu = 'ui-mode'


class FakeRoastMenuApplicationWindow:
    def __init__(self) -> None:
        self.editGraphAction = 'properties'
        self.backgroundAction = 'background'
        self.flavorAction = 'flavor'
        self.switchAction = 'switch'
        self.switchETBTAction = 'switch-et-bt'
        self.charge_target_dialog_calls = 0

    def showChargeTargetDialog(self) -> None:
        self.charge_target_dialog_calls += 1


class FakeToolsMenuApplicationWindow:
    def __init__(self) -> None:
        self.analyzeMenu = 'analyze'
        self.roastCompareAction = 'compare'
        self.designerAction = 'designer'
        self.simulatorAction = 'simulator'
        self.wheeleditorAction = 'wheel'
        self.transformAction = 'transform'
        self.temperatureMenu = 'temperature'
        self.calculatorAction = 'calculator'


class FakeViewQmc:
    def __init__(self) -> None:
        self.Controlbuttonflag = False
        self.extradevices: list[str] = []
        self.locale_str = 'en_US'


class FakeViewApp:
    def __init__(self) -> None:
        self.artisanviewerMode = False


class FakeViewMenuApplicationWindow:
    def __init__(self) -> None:
        # Intentionally no ui_mode attribute: create_view_menu should use its parameter.
        self.controlsAction = 'controls'
        self.readingsAction = 'readings'
        self.eventsEditorAction = 'events-editor'
        self.buttonsAction = 'buttons'
        self.slidersAction = 'sliders'
        self.scheduleAction = FakeMenuAction('schedule')
        self.lcdsAction = 'lcds'
        self.deltalcdsAction = 'delta-lcds'
        self.pidlcdsAction = 'pid-lcds'
        self.extralcdsAction = 'extra-lcds'
        self.phaseslcdsAction = 'phases-lcds'
        self.scalelcdsAction = 'scale-lcds'
        self.fullscreenAction = 'fullscreen'
        self.extraeventslabels: list[str] = []
        self.qmc = FakeViewQmc()
        self.app = FakeViewApp()
        self.scale1_model: object | None = None
        self._sliders_visible = False

    def slidersVisible(self) -> bool:
        return self._sliders_visible


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


def test_application_window_create_help_menu_preserves_current_policy_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)

    expected_items = {
        main.UI_MODE.EXPERT: [
            'about',
            'about-qt',
            'docs',
            'shortcuts',
            'separator',
            'check-update',
            'separator',
            'error',
            'message',
            'serial',
            'platform',
            'separator',
            'load-settings',
            'recent-settings',
            'save-settings',
            'separator',
            'reset',
        ],
        main.UI_MODE.DEFAULT: [
            'about',
            'about-qt',
            'docs',
            'shortcuts',
            'separator',
            'check-update',
            'separator',
            'load-settings',
            'recent-settings',
            'save-settings',
            'separator',
            'reset',
        ],
        main.UI_MODE.PRODUCTION: [
            'about',
            'about-qt',
            'docs',
            'shortcuts',
        ],
    }

    for ui_mode, items in expected_items.items():
        window = FakeHelpMenuApplicationWindow()
        menu = main.ApplicationWindow.create_help_menu(window, ui_mode)

        assert menu.items == items


def test_application_window_create_help_menu_uses_workspace_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    expert_like_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
        show_advanced_controls=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return expert_like_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeHelpMenuApplicationWindow()

    menu = main.ApplicationWindow.create_help_menu(window, main.UI_MODE.PRODUCTION)

    assert 'check-update' in menu.items
    assert 'error' in menu.items
    assert 'load-settings' in menu.items


def test_application_window_create_file_menu_preserves_current_policy_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)

    expected_items = {
        main.UI_MODE.EXPERT: [
            'new',
            'load',
            'recent',
            'import',
            'convert-from',
            'separator',
            'save',
            'save-as',
            'save-copy-as',
            'separator',
            'export',
            'convert-to',
            'separator',
            'save-graph',
            'report',
            'statistics',
            'separator',
            'print',
            'quit',
        ],
        main.UI_MODE.DEFAULT: [
            'new',
            'load',
            'recent',
            'import',
            'convert-from',
            'separator',
            'save',
            'save-as',
            'separator',
            'export',
            'convert-to',
            'separator',
            'save-graph',
            'report',
            'separator',
            'print',
            'quit',
        ],
        main.UI_MODE.PRODUCTION: [
            'new',
            'load',
            'recent',
            'separator',
            'save',
            'save-as',
            'separator',
            'separator',
            'separator',
            'print',
            'quit',
        ],
    }

    for ui_mode, items in expected_items.items():
        window = FakeFileMenuApplicationWindow()
        menu = main.ApplicationWindow.create_file_menu(window, ui_mode)

        assert menu.items == items


def test_application_window_create_file_menu_uses_workspace_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    expert_like_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
        show_advanced_controls=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return expert_like_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeFileMenuApplicationWindow()

    menu = main.ApplicationWindow.create_file_menu(window, main.UI_MODE.PRODUCTION)

    assert 'import' in menu.items
    assert 'save-copy-as' in menu.items
    assert 'export' in menu.items
    assert 'statistics' in menu.items


def test_application_window_create_config_menu_preserves_current_policy_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)

    expected_items = {
        main.UI_MODE.EXPERT: [
            'machine',
            'device',
            'comm-port',
            'separator',
            'calibrate-delay',
            'separator',
            'curves',
            'separator',
            'events',
            'alarm',
            'separator',
            'phases',
            'statistics',
            'window-config',
            'separator',
            'colors',
            'theme',
            'separator',
            'autosave',
            'batch',
            'separator',
            'temperature',
            'language',
            'separator',
            'ui-mode',
        ],
        main.UI_MODE.DEFAULT: [
            'machine',
            'separator',
            'events',
            'alarm',
            'separator',
            'phases',
            'window-config',
            'separator',
            'theme',
            'separator',
            'autosave',
            'batch',
            'separator',
            'temperature',
            'language',
            'separator',
            'ui-mode',
        ],
        main.UI_MODE.PRODUCTION: [
            'separator',
            'separator',
            'ui-mode',
        ],
    }

    for ui_mode, items in expected_items.items():
        window = FakeConfigMenuApplicationWindow()
        menu = main.ApplicationWindow.create_config_menu(window, ui_mode)

        assert menu.items == items


def test_application_window_create_config_menu_uses_workspace_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    expert_like_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
        show_advanced_controls=True,
        show_device_setup_tools=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return expert_like_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeConfigMenuApplicationWindow()

    menu = main.ApplicationWindow.create_config_menu(window, main.UI_MODE.PRODUCTION)

    assert 'machine' in menu.items
    assert 'device' in menu.items
    assert 'statistics' in menu.items
    assert 'colors' in menu.items
    assert 'language' in menu.items


def test_application_window_create_config_menu_separates_device_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    device_only_policy = dataclasses.replace(
        production_policy,
        show_device_setup_tools=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return device_only_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeConfigMenuApplicationWindow()

    menu = main.ApplicationWindow.create_config_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'device',
        'comm-port',
        'separator',
        'calibrate-delay',
        'separator',
        'curves',
        'separator',
        'separator',
        'ui-mode',
    ]


def test_application_window_create_roast_menu_preserves_current_policy_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main, 'QAction', FakeQAction)

    expected_items = {
        main.UI_MODE.EXPERT: [
            'properties',
            'background',
            'flavor',
            '投豆目标...',
            'separator',
            'switch',
            'switch-et-bt',
        ],
        main.UI_MODE.DEFAULT: [
            'properties',
            'background',
            'flavor',
            '投豆目标...',
            'separator',
            'switch',
        ],
        main.UI_MODE.PRODUCTION: [
            'properties',
            'background',
            'flavor',
            '投豆目标...',
        ],
    }

    for ui_mode, items in expected_items.items():
        window = FakeRoastMenuApplicationWindow()
        menu = main.ApplicationWindow.create_roast_menu(window, ui_mode)

        assert menu.items == items


def test_application_window_create_roast_menu_connects_charge_target_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main, 'QAction', FakeQAction)
    FakeQAction.instances.clear()
    window = FakeRoastMenuApplicationWindow()

    main.ApplicationWindow.create_roast_menu(window, main.UI_MODE.PRODUCTION)

    charge_target_action = FakeQAction.instances[-1]
    assert charge_target_action.label == '投豆目标...'
    assert charge_target_action.triggered.connected_to == window.showChargeTargetDialog


def test_application_window_create_roast_menu_separates_full_menu_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main, 'QAction', FakeQAction)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    full_menu_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return full_menu_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeRoastMenuApplicationWindow()

    menu = main.ApplicationWindow.create_roast_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'properties',
        'background',
        'flavor',
        '投豆目标...',
        'separator',
        'switch',
    ]


def test_application_window_create_roast_menu_separates_advanced_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main, 'QAction', FakeQAction)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    advanced_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
        show_advanced_controls=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return advanced_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeRoastMenuApplicationWindow()

    menu = main.ApplicationWindow.create_roast_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'properties',
        'background',
        'flavor',
        '投豆目标...',
        'separator',
        'switch',
        'switch-et-bt',
    ]


def test_application_window_create_tools_menu_preserves_current_policy_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)

    expected_items = {
        main.UI_MODE.EXPERT: [
            'analyze',
            'compare',
            'designer',
            'simulator',
            'wheel',
            'separator',
            'transform',
            'temperature',
            'separator',
            'calculator',
        ],
        main.UI_MODE.DEFAULT: [
            'compare',
            'designer',
            'separator',
            'temperature',
            'separator',
            'calculator',
        ],
        main.UI_MODE.PRODUCTION: [],
    }

    for ui_mode, items in expected_items.items():
        window = FakeToolsMenuApplicationWindow()
        menu = main.ApplicationWindow.create_tools_menu(window, ui_mode)

        assert menu.items == items


def test_application_window_create_tools_menu_separates_analysis_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    analysis_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
        show_analysis_tools=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return analysis_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeToolsMenuApplicationWindow()

    menu = main.ApplicationWindow.create_tools_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'analyze',
        'compare',
        'designer',
        'separator',
        'temperature',
        'separator',
        'calculator',
    ]


def test_application_window_create_tools_menu_separates_advanced_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    advanced_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
        show_advanced_controls=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return advanced_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeToolsMenuApplicationWindow()

    menu = main.ApplicationWindow.create_tools_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'compare',
        'designer',
        'simulator',
        'wheel',
        'separator',
        'transform',
        'temperature',
        'separator',
        'calculator',
    ]


def test_application_window_create_view_menu_preserves_current_policy_visibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main.platform, 'system', lambda: 'Linux')

    full_menu_items = [
        'controls',
        'readings',
        'events-editor',
        'buttons',
        'sliders',
        'separator',
        'schedule',
        'separator',
        'lcds',
        'delta-lcds',
        'pid-lcds',
        'extra-lcds',
        'phases-lcds',
        'scale-lcds',
        'separator',
        'fullscreen',
    ]
    expected_items = {
        main.UI_MODE.EXPERT: full_menu_items,
        main.UI_MODE.DEFAULT: full_menu_items,
        main.UI_MODE.PRODUCTION: [
            'controls',
            'readings',
            'events-editor',
            'separator',
            'schedule',
            'separator',
            'lcds',
            'delta-lcds',
            'phases-lcds',
            'separator',
            'fullscreen',
        ],
    }

    for ui_mode, items in expected_items.items():
        window = FakeViewMenuApplicationWindow()
        menu = main.ApplicationWindow.create_view_menu(window, ui_mode)

        assert menu.items == items


def test_application_window_create_view_menu_preserves_production_runtime_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main.platform, 'system', lambda: 'Linux')
    window = FakeViewMenuApplicationWindow()
    window.extraeventslabels = ['fan']
    window._sliders_visible = True
    window.qmc.Controlbuttonflag = True
    window.qmc.extradevices = ['extra-device']
    window.scale1_model = object()

    menu = main.ApplicationWindow.create_view_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'controls',
        'readings',
        'events-editor',
        'buttons',
        'sliders',
        'separator',
        'schedule',
        'separator',
        'lcds',
        'delta-lcds',
        'pid-lcds',
        'extra-lcds',
        'phases-lcds',
        'scale-lcds',
        'separator',
        'fullscreen',
    ]


@pytest.mark.parametrize(
    ('field', 'expected_item'),
    (
        ('extraeventslabels', 'buttons'),
        ('sliders', 'sliders'),
        ('control_button', 'pid-lcds'),
        ('extra_device', 'extra-lcds'),
        ('scale', 'scale-lcds'),
    ),
)
def test_application_window_create_view_menu_keeps_each_production_fallback_independent(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    expected_item: str,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main.platform, 'system', lambda: 'Linux')
    window = FakeViewMenuApplicationWindow()
    if field == 'extraeventslabels':
        window.extraeventslabels = ['fan']
    elif field == 'sliders':
        window._sliders_visible = True
    elif field == 'control_button':
        window.qmc.Controlbuttonflag = True
    elif field == 'extra_device':
        window.qmc.extradevices = ['extra-device']
    elif field == 'scale':
        window.scale1_model = object()

    menu = main.ApplicationWindow.create_view_menu(window, main.UI_MODE.PRODUCTION)

    runtime_items = {'buttons', 'sliders', 'pid-lcds', 'extra-lcds', 'scale-lcds'}
    assert expected_item in menu.items
    assert runtime_items.intersection(menu.items) == {expected_item}


def test_application_window_create_view_menu_disables_schedule_in_viewer_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main.platform, 'system', lambda: 'Linux')
    window = FakeViewMenuApplicationWindow()
    window.app.artisanviewerMode = True

    main.ApplicationWindow.create_view_menu(window, main.UI_MODE.DEFAULT)

    assert window.scheduleAction.enabled is False


def test_application_window_create_view_menu_omits_macos_english_fullscreen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main.platform, 'system', lambda: 'Darwin')
    window = FakeViewMenuApplicationWindow()
    window.qmc.locale_str = 'en'

    menu = main.ApplicationWindow.create_view_menu(window, main.UI_MODE.DEFAULT)

    assert 'fullscreen' not in menu.items


def test_application_window_create_view_menu_uses_workspace_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = main_module()
    workspaces = workspace_module()
    monkeypatch.setattr(main, 'QMenu', FakeMenu)
    monkeypatch.setattr(main.platform, 'system', lambda: 'Linux')
    production_policy = workspaces.workspace_policy(workspaces.WorkspaceMode.PRODUCTION)
    full_menu_policy = dataclasses.replace(
        production_policy,
        show_full_menus=True,
    )

    def fake_workspace_policy(_mode: object) -> object:
        return full_menu_policy

    monkeypatch.setattr(main, 'workspace_policy_for_mode', fake_workspace_policy)
    window = FakeViewMenuApplicationWindow()

    menu = main.ApplicationWindow.create_view_menu(window, main.UI_MODE.PRODUCTION)

    assert menu.items == [
        'controls',
        'readings',
        'events-editor',
        'buttons',
        'sliders',
        'separator',
        'schedule',
        'separator',
        'lcds',
        'delta-lcds',
        'pid-lcds',
        'extra-lcds',
        'phases-lcds',
        'scale-lcds',
        'separator',
        'fullscreen',
    ]


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
