from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class ModernTheme:
    window: str = '#F1F3EE'
    surface: str = '#FCFBF7'
    surface_muted: str = '#E6ECE8'
    surface_alt: str = '#F7F6F0'
    border: str = '#CAD5D0'
    border_strong: str = '#8FA39C'
    text: str = '#20272B'
    text_muted: str = '#637278'
    selection: str = '#D7E5DF'
    selection_text: str = '#18343C'
    focus: str = '#53756F'
    primary: str = '#53756F'
    primary_hover: str = '#63857F'
    accent: str = '#B4685C'
    success: str = '#6F875E'


def apply_modern_dialog_polish(dialog: object) -> None:
    if not modern_dialog_polish_enabled():
        return
    property_getter = getattr(dialog, 'property', None)
    property_setter = getattr(dialog, 'setProperty', None)
    if not callable(property_getter) or not callable(property_setter):
        return
    if property_getter('modernDialogPolished') is True:
        return

    try:
        from PyQt6.QtWidgets import (
            QAbstractScrollArea,
            QDialogButtonBox,
            QGroupBox,
            QHeaderView,
            QLayout,
            QTableView,
            QTabWidget,
        )
    except ImportError:
        return

    property_setter('modernDialogPolished', True)

    root_layout = getattr(dialog, 'layout', lambda: None)()
    if isinstance(root_layout, QLayout):
        _polish_dialog_layout_tree(root_layout, margin=14, spacing=10)

    for group_box in _find_children(dialog, QGroupBox):
        group_box.setProperty('modernDialogPanel', True)
        _refresh_widget_style(group_box)
        group_layout = group_box.layout()
        if isinstance(group_layout, QLayout):
            _polish_dialog_layout_tree(group_layout, margin=10, spacing=8)

    for tab_widget in _find_children(dialog, QTabWidget):
        tab_widget.setProperty('modernDialogTabs', True)
        tab_widget.setDocumentMode(True)
        tab_widget.setUsesScrollButtons(True)
        tab_bar = tab_widget.tabBar()
        tab_bar.setExpanding(False)
        _refresh_widget_style(tab_widget)
        _refresh_widget_style(tab_bar)
        for tab_index in range(tab_widget.count()):
            tab_page = tab_widget.widget(tab_index)
            tab_layout = tab_page.layout() if tab_page is not None else None
            if isinstance(tab_layout, QLayout):
                _polish_dialog_layout_tree(tab_layout, margin=10, spacing=8)

    for scroll_area in _find_children(dialog, QAbstractScrollArea):
        scroll_area.setProperty('modernDialogScrollArea', True)
        viewport = scroll_area.viewport()
        viewport.setProperty('modernDialogViewport', True)
        _refresh_widget_style(scroll_area)
        _refresh_widget_style(viewport)
        if isinstance(scroll_area, QTableView):
            scroll_area.setAlternatingRowColors(True)
            horizontal_header = scroll_area.horizontalHeader()
            vertical_header = scroll_area.verticalHeader()
            for header in (horizontal_header, vertical_header):
                if isinstance(header, QHeaderView):
                    header.setHighlightSections(False)

    for button_box in _find_children(dialog, QDialogButtonBox):
        for button in button_box.buttons():
            _polish_dialog_button(button_box, button)


def modern_dialog_polish_enabled() -> bool:
    legacy_flag = os.environ.get('ARTISANZ_LEGACY_UI', '').strip().lower()
    return legacy_flag not in {'1', 'true', 'yes', 'on'}


def _polish_dialog_layout_tree(layout: Any, *, margin: int, spacing: int) -> None:
    _polish_dialog_layout(layout, margin=margin, spacing=spacing)
    for index in range(layout.count()):
        item = layout.itemAt(index)
        child_layout = item.layout() if item is not None else None
        if child_layout is not None:
            _polish_dialog_layout_tree(child_layout, margin=8, spacing=spacing)


def _polish_dialog_layout(layout: Any, *, margin: int, spacing: int) -> None:
    left, top, right, bottom = layout.getContentsMargins()
    layout.setContentsMargins(
        max(left, margin),
        max(top, margin),
        max(right, margin),
        max(bottom, margin),
    )
    current_spacing = layout.spacing()
    layout.setSpacing(max(current_spacing, spacing))


def _polish_dialog_button(button_box: Any, button: Any) -> None:
    try:
        from PyQt6.QtWidgets import QDialogButtonBox
    except ImportError:
        return
    standard_button = button_box.standardButton(button)
    primary_buttons = {
        QDialogButtonBox.StandardButton.Ok,
        QDialogButtonBox.StandardButton.Apply,
        QDialogButtonBox.StandardButton.Save,
        QDialogButtonBox.StandardButton.Yes,
    }
    secondary_buttons = {
        QDialogButtonBox.StandardButton.Cancel,
        QDialogButtonBox.StandardButton.Close,
        QDialogButtonBox.StandardButton.Reset,
        QDialogButtonBox.StandardButton.No,
    }
    if standard_button in primary_buttons:
        button.setProperty('modernDialogPrimaryButton', True)
    elif standard_button in secondary_buttons:
        button.setProperty('modernDialogSecondaryButton', True)
    _refresh_widget_style(button)


def _find_children(parent: object, widget_type: type[Any]) -> list[Any]:
    find_children = getattr(parent, 'findChildren', None)
    if not callable(find_children):
        return []
    return list(find_children(widget_type))


def _refresh_widget_style(widget: object) -> None:
    style = getattr(widget, 'style', lambda: None)()
    if style is None:
        return
    unpolish = getattr(style, 'unpolish', None)
    polish = getattr(style, 'polish', None)
    if callable(unpolish):
        unpolish(widget)
    if callable(polish):
        polish(widget)


def lcd_value_stylesheet(text_color: str, background_color: str) -> str:
    return (
        'QLCDNumber { '
        'border-width: 0px; '
        'border-style: solid; '
        'border-color: transparent; '
        'border-radius: 6px; '
        'padding: 5px 8px 4px 8px; '
        f'color: {text_color}; '
        f'background-color: {background_color};'
        '}'
    )


def lcd_label_stylesheet(text_color: str) -> str:
    return (
        'QLabel { '
        f'color: {text_color}; '
        'padding: 3px 6px 2px 6px;'
        '}'
    )


def modern_application_stylesheet(theme: ModernTheme | None = None) -> str:
    t = ModernTheme() if theme is None else theme
    return f"""
        QWidget {{
            color: {t.text};
            selection-background-color: {t.selection};
            selection-color: {t.selection_text};
        }}
        QMainWindow, QDialog {{
            background-color: {t.window};
        }}
        QDialog QWidget {{
            selection-background-color: {t.selection};
            selection-color: {t.selection_text};
        }}
        QDialog QLabel {{
            color: {t.text};
        }}
        QDialog[modernDialog="true"] {{
            background-color: {t.window};
        }}
        QDialog[modernDialog="true"] QGroupBox {{
            background-color: {t.surface};
            border: 1px solid {t.border};
            border-radius: 7px;
            margin-top: 14px;
            padding: 10px 8px 8px 8px;
        }}
        QDialog[modernDialog="true"] QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: {t.text_muted};
            font-weight: 600;
        }}
        QDialog[modernDialog="true"] QTabWidget::pane {{
            border: 1px solid {t.border};
            border-radius: 7px;
            background-color: {t.surface};
            top: -1px;
        }}
        QDialog[modernDialog="true"] QTabBar::tab {{
            background-color: {t.surface_alt};
            border: 1px solid {t.border};
            border-bottom: 0;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 6px 10px;
            margin-right: 2px;
        }}
        QDialog[modernDialog="true"] QTabBar::tab:selected {{
            background-color: {t.surface};
            color: {t.primary};
            font-weight: 600;
        }}
        QDialog[modernDialog="true"] QAbstractScrollArea {{
            background-color: {t.surface};
            border: 1px solid {t.border};
            border-radius: 7px;
        }}
        QDialog[modernDialog="true"] QWidget[modernDialogViewport="true"] {{
            background-color: {t.surface};
        }}
        QDialog[modernDialog="true"] QDialogButtonBox {{
            background-color: transparent;
            padding-top: 4px;
        }}
        QDialog[modernDialog="true"] QCheckBox {{
            spacing: 7px;
            min-height: 24px;
            color: {t.text};
        }}
        QDialog[modernDialog="true"] QCheckBox::indicator {{
            width: 15px;
            height: 15px;
            border: 1px solid {t.border_strong};
            border-radius: 4px;
            background-color: {t.surface};
        }}
        QDialog[modernDialog="true"] QCheckBox::indicator:checked {{
            background-color: {t.primary};
            border-color: {t.primary};
        }}
        QDialog[modernDialog="true"] QTableWidget,
        QDialog[modernDialog="true"] QTableView,
        QDialog[modernDialog="true"] QTreeView,
        QDialog[modernDialog="true"] QListView {{
            background-color: {t.surface};
            alternate-background-color: {t.surface_alt};
            border: 1px solid {t.border};
            border-radius: 7px;
            gridline-color: {t.border};
        }}
        QDialog[modernDialog="true"] QHeaderView::section {{
            background-color: {t.surface_muted};
            border: 0;
            border-right: 1px solid {t.border};
            border-bottom: 1px solid {t.border};
            padding: 5px 7px;
            color: {t.text_muted};
            font-weight: 600;
        }}
        QDialog[modernDialog="true"] QLineEdit,
        QDialog[modernDialog="true"] QTextEdit,
        QDialog[modernDialog="true"] QPlainTextEdit,
        QDialog[modernDialog="true"] QComboBox,
        QDialog[modernDialog="true"] QSpinBox,
        QDialog[modernDialog="true"] QDoubleSpinBox,
        QDialog[modernDialog="true"] QTimeEdit,
        QDialog[modernDialog="true"] QDateEdit {{
            background-color: {t.surface};
            border: 1px solid {t.border};
            border-radius: 6px;
            padding: 5px 8px;
            min-height: 23px;
        }}
        QDialog[modernDialog="true"] QPushButton {{
            background-color: {t.surface_alt};
            border: 1px solid {t.border};
            border-radius: 6px;
            padding: 6px 12px;
            min-height: 24px;
        }}
        QDialog[modernDialog="true"] QPushButton[modernDialogPrimaryButton="true"] {{
            background-color: {t.primary};
            border-color: {t.primary};
            color: white;
            font-weight: 600;
        }}
        QDialog[modernDialog="true"] QPushButton[modernDialogSecondaryButton="true"] {{
            background-color: transparent;
            color: {t.text_muted};
        }}
        QDialog[modernDialog="true"] QPushButton[modernDialogPrimaryButton="true"]:hover:!pressed {{
            background-color: {t.primary_hover};
            border-color: {t.primary_hover};
        }}
        QDialog[modernDialogRole="axes"] QTabBar::tab:selected,
        QDialog[modernDialogRole="curves"] QTabBar::tab:selected {{
            color: {t.primary};
        }}
        QDialog[modernDialogRole="events"] QTabBar::tab:selected {{
            color: #3C7A88;
        }}
        QDialog[modernDialogRole="alarms"] QTabBar::tab:selected {{
            color: {t.accent};
        }}
        QMessageBox, QFileDialog {{
            background-color: {t.window};
        }}
        QWidget[mainRoastScreen="true"] {{
            background-color: {t.window};
        }}
        QMenuBar {{
            background-color: {t.surface};
            border-bottom: 1px solid {t.border};
            padding: 2px;
        }}
        QMenuBar::item {{
            background: transparent;
            border-radius: 5px;
            padding: 4px 8px;
        }}
        QMenuBar::item:selected {{
            background-color: {t.surface_muted};
        }}
        QMenu {{
            background-color: {t.surface};
            border: 1px solid {t.border};
            padding: 4px;
        }}
        QMenu::item {{
            border-radius: 5px;
            padding: 5px 22px 5px 22px;
        }}
        QMenu::item:selected {{
            background-color: {t.selection};
            color: {t.selection_text};
        }}
        QToolBar {{
            background-color: {t.surface};
            border: 0;
            border-bottom: 1px solid {t.border};
            spacing: 4px;
            padding: 3px;
        }}
        QStatusBar {{
            background-color: {t.surface};
            border-top: 1px solid {t.border};
            color: {t.text_muted};
        }}
        QWidget[mainGraphPanel="true"] {{
            background-color: #F8F7F1;
            border: 1px solid {t.border};
            border-radius: 8px;
        }}
        QFrame[lcdSurface="true"] {{
            background-color: transparent;
            border: 0;
            border-radius: 0;
        }}
        QFrame[telemetryCard="true"] {{
            background-color: transparent;
            border: 0;
            border-radius: 0;
        }}
        QLCDNumber[lcdValue="true"] {{
            border-width: 0px;
            border-style: solid;
            border-color: transparent;
            border-radius: 6px;
            padding: 5px 8px 4px 8px;
            margin-top: 2px;
            margin-bottom: 0px;
        }}
        QLabel[lcdLabel="true"] {{
            color: {t.text_muted};
            font-weight: 600;
            padding: 3px 6px 2px 6px;
        }}
        QFrame[roastEventRail="true"] {{
            background-color: #E6ECEB;
            border-top: 1px solid {t.border};
            border-bottom: 1px solid {t.border};
        }}
        QGroupBox {{
            border: 1px solid {t.border};
            border-radius: 6px;
            margin-top: 10px;
            padding: 8px 6px 6px 6px;
            background-color: {t.surface};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            color: {t.text_muted};
        }}
        QTabWidget::pane {{
            border: 1px solid {t.border};
            border-radius: 6px;
            background-color: {t.surface};
        }}
        QTabBar::tab {{
            background-color: {t.surface_muted};
            border: 1px solid {t.border};
            border-bottom: 0;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 5px 10px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {t.surface};
            color: {t.primary};
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTimeEdit, QDateEdit {{
            background-color: {t.surface};
            border: 1px solid {t.border};
            border-radius: 5px;
            padding: 4px 7px;
            min-height: 22px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {t.focus};
        }}
        QTableView, QTreeView, QListView {{
            background-color: {t.surface};
            alternate-background-color: {t.window};
            border: 1px solid {t.border};
            border-radius: 6px;
            gridline-color: {t.border};
        }}
        QHeaderView::section {{
            background-color: {t.surface_muted};
            border: 0;
            border-right: 1px solid {t.border};
            border-bottom: 1px solid {t.border};
            padding: 4px 6px;
            color: {t.text_muted};
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background-color: {t.window};
            border: 0;
            margin: 0;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background-color: {t.border_strong};
            border-radius: 4px;
            min-height: 24px;
            min-width: 24px;
        }}
        QPushButton {{
            border: 1px solid {t.border};
            border-radius: 6px;
            padding: 4px 9px;
            background-color: {t.surface};
        }}
        QDialog QPushButton {{
            min-height: 24px;
            padding: 5px 12px;
            background-color: {t.surface_alt};
        }}
        QPushButton[mainControlRole="monitor"],
        QPushButton[mainControlRole="record"],
        QPushButton[mainControlRole="reset"],
        QPushButton[mainControlRole="control"] {{
            border-radius: 8px;
            padding: 7px 16px;
            font-weight: 700;
            background-color: {t.surface};
            border: 1px solid {t.border};
            color: {t.primary};
        }}
        QPushButton[mainControlRole="monitor"],
        QPushButton[mainControlRole="control"] {{
            background-color: {t.primary};
            border-color: {t.primary};
            color: white;
        }}
        QPushButton[mainControlRole="record"] {{
            background-color: {t.accent};
            border-color: {t.accent};
            color: white;
        }}
        QPushButton[mainControlRole="reset"] {{
            background-color: {t.surface};
            border-color: {t.border_strong};
            color: {t.primary};
        }}
        QPushButton[mainControlRole="monitor"]:hover:!pressed,
        QPushButton[mainControlRole="reset"]:hover:!pressed,
        QPushButton[mainControlRole="control"]:hover:!pressed {{
            background-color: {t.primary_hover};
            border-color: {t.primary_hover};
            color: white;
        }}
        QPushButton[mainControlRole="record"]:hover:!pressed {{
            background-color: #C47A6F;
            border-color: #C47A6F;
            color: white;
        }}
        QPushButton:hover:!pressed {{
            background-color: {t.surface_muted};
            border-color: {t.border_strong};
        }}
        QPushButton:focus {{
            border-color: {t.focus};
        }}
    """
