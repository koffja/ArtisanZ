from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModernTheme:
    window: str = '#f6f7f8'
    surface: str = '#ffffff'
    surface_muted: str = '#eef2f3'
    border: str = '#d4dadd'
    border_strong: str = '#aeb8bd'
    text: str = '#22292f'
    text_muted: str = '#66727a'
    selection: str = '#dbeafe'
    selection_text: str = '#102a43'
    focus: str = '#2f80ed'
    primary: str = '#336b75'
    primary_hover: str = '#3f7f8a'
    accent: str = '#b5644f'
    success: str = '#4f7f58'


def lcd_value_stylesheet(text_color: str, background_color: str) -> str:
    return (
        'QLCDNumber { '
        'border-width: 0px; '
        'border-style: solid; '
        'border-color: transparent; '
        'border-radius: 0px; '
        'border-top-left-radius: 0px; '
        'border-top-right-radius: 0px; '
        'border-bottom-left-radius: 5px; '
        'border-bottom-right-radius: 5px; '
        'padding: 4px 8px 3px 8px; '
        f'color: {text_color}; '
        f'background-color: {background_color};'
        '}'
    )


def lcd_label_stylesheet(text_color: str) -> str:
    return (
        'QLabel { '
        f'color: {text_color}; '
        'padding: 2px 8px 1px 8px;'
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
        QFrame[lcdSurface="true"] {{
            background-color: {t.surface};
            border: 1px solid {t.border};
            border-radius: 6px;
        }}
        QLCDNumber[lcdValue="true"] {{
            border-width: 0px;
            border-style: solid;
            border-color: transparent;
            border-radius: 0px;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 5px;
            padding: 4px 8px 3px 8px;
            margin-bottom: 0px;
        }}
        QLabel[lcdLabel="true"] {{
            color: {t.text_muted};
            font-weight: 600;
            padding: 2px 8px 1px 8px;
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
            padding: 3px 6px;
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
        QPushButton:hover:!pressed {{
            background-color: {t.surface_muted};
            border-color: {t.border_strong};
        }}
        QPushButton:focus {{
            border-color: {t.focus};
        }}
    """
