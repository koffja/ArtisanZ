from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkspaceMode(Enum):
    ROAST_CONTROL = 'roast_control'
    QC_ANALYSIS = 'qc_analysis'
    DEVICE_SETUP = 'device_setup'
    PRODUCTION = 'production'
    EXPERT = 'expert'


class WorkspaceArea(Enum):
    ROAST_CONTROL = 'roast_control'
    QC_ANALYSIS = 'qc_analysis'
    DEVICE_SETUP = 'device_setup'
    PRODUCTION_BATCH = 'production_batch'
    EXPERT_TOOLS = 'expert_tools'


@dataclass(frozen=True)
class WorkspaceSpec:
    mode: WorkspaceMode
    label_key: str
    primary_area: WorkspaceArea
    visible_areas: tuple[WorkspaceArea, ...]
    compact_chrome: bool
    show_advanced_navigation: bool


@dataclass(frozen=True)
class WorkspacePolicy:
    mode: WorkspaceMode
    show_full_menus: bool
    show_full_toolbars: bool
    show_side_panels: bool
    show_advanced_controls: bool
    show_analysis_tools: bool
    show_device_setup_tools: bool
    compact_chrome: bool


_ALL_AREAS: tuple[WorkspaceArea, ...] = tuple(WorkspaceArea)


_WORKSPACE_SPECS: dict[WorkspaceMode, WorkspaceSpec] = {
    WorkspaceMode.ROAST_CONTROL: WorkspaceSpec(
        mode=WorkspaceMode.ROAST_CONTROL,
        label_key='Roast Control',
        primary_area=WorkspaceArea.ROAST_CONTROL,
        visible_areas=(
            WorkspaceArea.ROAST_CONTROL,
            WorkspaceArea.PRODUCTION_BATCH,
        ),
        compact_chrome=False,
        show_advanced_navigation=False,
    ),
    WorkspaceMode.QC_ANALYSIS: WorkspaceSpec(
        mode=WorkspaceMode.QC_ANALYSIS,
        label_key='QC Analysis',
        primary_area=WorkspaceArea.QC_ANALYSIS,
        visible_areas=(
            WorkspaceArea.QC_ANALYSIS,
            WorkspaceArea.ROAST_CONTROL,
            WorkspaceArea.PRODUCTION_BATCH,
        ),
        compact_chrome=False,
        show_advanced_navigation=False,
    ),
    WorkspaceMode.DEVICE_SETUP: WorkspaceSpec(
        mode=WorkspaceMode.DEVICE_SETUP,
        label_key='Device Setup',
        primary_area=WorkspaceArea.DEVICE_SETUP,
        visible_areas=(
            WorkspaceArea.DEVICE_SETUP,
            WorkspaceArea.ROAST_CONTROL,
        ),
        compact_chrome=False,
        show_advanced_navigation=True,
    ),
    WorkspaceMode.PRODUCTION: WorkspaceSpec(
        mode=WorkspaceMode.PRODUCTION,
        label_key='Production',
        primary_area=WorkspaceArea.ROAST_CONTROL,
        visible_areas=(
            WorkspaceArea.ROAST_CONTROL,
            WorkspaceArea.PRODUCTION_BATCH,
        ),
        compact_chrome=True,
        show_advanced_navigation=False,
    ),
    WorkspaceMode.EXPERT: WorkspaceSpec(
        mode=WorkspaceMode.EXPERT,
        label_key='Expert',
        primary_area=WorkspaceArea.ROAST_CONTROL,
        visible_areas=_ALL_AREAS,
        compact_chrome=False,
        show_advanced_navigation=True,
    ),
}


def workspace_spec(mode: WorkspaceMode) -> WorkspaceSpec:
    return _WORKSPACE_SPECS[mode]


def workspace_specs() -> tuple[WorkspaceSpec, ...]:
    return tuple(_WORKSPACE_SPECS[mode] for mode in WorkspaceMode)


_WORKSPACE_POLICIES: dict[WorkspaceMode, WorkspacePolicy] = {
    WorkspaceMode.ROAST_CONTROL: WorkspacePolicy(
        mode=WorkspaceMode.ROAST_CONTROL,
        show_full_menus=True,
        show_full_toolbars=True,
        show_side_panels=True,
        show_advanced_controls=False,
        show_analysis_tools=False,
        show_device_setup_tools=False,
        compact_chrome=False,
    ),
    WorkspaceMode.QC_ANALYSIS: WorkspacePolicy(
        mode=WorkspaceMode.QC_ANALYSIS,
        show_full_menus=True,
        show_full_toolbars=True,
        show_side_panels=True,
        show_advanced_controls=False,
        show_analysis_tools=True,
        show_device_setup_tools=False,
        compact_chrome=False,
    ),
    WorkspaceMode.DEVICE_SETUP: WorkspacePolicy(
        mode=WorkspaceMode.DEVICE_SETUP,
        show_full_menus=True,
        show_full_toolbars=True,
        show_side_panels=True,
        show_advanced_controls=True,
        show_analysis_tools=False,
        show_device_setup_tools=True,
        compact_chrome=False,
    ),
    WorkspaceMode.PRODUCTION: WorkspacePolicy(
        mode=WorkspaceMode.PRODUCTION,
        show_full_menus=False,
        show_full_toolbars=False,
        show_side_panels=False,
        show_advanced_controls=False,
        show_analysis_tools=False,
        show_device_setup_tools=False,
        compact_chrome=True,
    ),
    WorkspaceMode.EXPERT: WorkspacePolicy(
        mode=WorkspaceMode.EXPERT,
        show_full_menus=True,
        show_full_toolbars=True,
        show_side_panels=True,
        show_advanced_controls=True,
        show_analysis_tools=True,
        show_device_setup_tools=True,
        compact_chrome=False,
    ),
}


def workspace_policy(mode: WorkspaceMode) -> WorkspacePolicy:
    return _WORKSPACE_POLICIES[mode]


def workspace_for_ui_mode_value(ui_mode_value: int) -> WorkspaceMode:
    if ui_mode_value == 1:
        return WorkspaceMode.EXPERT
    if ui_mode_value == 3:
        return WorkspaceMode.PRODUCTION
    return WorkspaceMode.ROAST_CONTROL


__all__ = [
    'WorkspaceArea',
    'WorkspaceMode',
    'WorkspacePolicy',
    'WorkspaceSpec',
    'workspace_for_ui_mode_value',
    'workspace_policy',
    'workspace_spec',
    'workspace_specs',
]
