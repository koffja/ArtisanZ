"""Renderer-neutral curve style editor used by the modern plot toolbar."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QPushButton,
    QVBoxLayout,
)

from artisanlib.plot_style_defaults import CANONICAL_CURVE_COLORS
from artisanlib.util import (
    argb_colorname2rgba_colorname,
    deltaLabelUTF8,
    rgba_colorname2argb_colorname,
)


@dataclass(frozen=True, slots=True)
class CurveStyleBinding:
    label: str
    style_attr: str
    width_attr: str
    color_key: str
    default_color: str


CURVE_STYLE_BINDINGS: tuple[CurveStyleBinding, ...] = (
    CurveStyleBinding('ET', 'ETlinestyle', 'ETlinewidth', 'et', CANONICAL_CURVE_COLORS['et']),
    CurveStyleBinding('BT', 'BTlinestyle', 'BTlinewidth', 'bt', CANONICAL_CURVE_COLORS['bt']),
    CurveStyleBinding('Delta ET', 'ETdeltalinestyle', 'ETdeltalinewidth', 'deltaet', CANONICAL_CURVE_COLORS['deltaet']),
    CurveStyleBinding('Delta BT', 'BTdeltalinestyle', 'BTdeltalinewidth', 'deltabt', CANONICAL_CURVE_COLORS['deltabt']),
)

_LINE_STYLE_VALUES: tuple[tuple[str, str], ...] = (
    ('-', '-'),
    ('--', '--'),
    (':', ':'),
    ('-.', '-.'),
)


class CurveStyleDialog(QDialog):
    """Edit core roast curve styles without depending on Matplotlib objects."""

    def __init__(
            self,
            parent: Any,
            qmc: Any,
            apply_callback: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self.setObjectName('plotCurveStyleDialog')
        self.setWindowTitle(QApplication.translate('Toolbar', 'Lines'))
        self.setModal(True)
        self._qmc = qmc
        self._apply_callback = apply_callback
        self._last_binding: CurveStyleBinding | None = None
        self._pending: dict[CurveStyleBinding, tuple[str, float, str]] = {
            binding: self._read_binding(binding)
            for binding in CURVE_STYLE_BINDINGS
        }

        self.curveComboBox = QComboBox()
        self.curveComboBox.setObjectName('curveComboBox')
        for binding in CURVE_STYLE_BINDINGS:
            self.curveComboBox.addItem(self._translated_curve_label(binding), binding)
        self.curveComboBox.currentIndexChanged.connect(self._load_selected)

        self.styleComboBox = QComboBox()
        self.styleComboBox.setObjectName('styleComboBox')
        for label, value in _LINE_STYLE_VALUES:
            self.styleComboBox.addItem(QApplication.translate('Label', label), value)

        self.widthSpinBox = QDoubleSpinBox()
        self.widthSpinBox.setObjectName('widthSpinBox')
        self.widthSpinBox.setRange(0.1, 12.0)
        self.widthSpinBox.setSingleStep(0.1)
        self.widthSpinBox.setDecimals(1)
        self.widthSpinBox.setSuffix(' px')
        self.widthSpinBox.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.colorButton = QPushButton()
        self.colorButton.setObjectName('colorButton')
        self.colorButton.clicked.connect(self._select_color)

        self.restoreDefaultsButton = QPushButton(
            QApplication.translate('Curves', 'Restore Defaults'))
        self.restoreDefaultsButton.setObjectName('restoreDefaultsButton')
        self.restoreDefaultsButton.clicked.connect(self._restore_defaults)

        form = QFormLayout()
        form.addRow(QApplication.translate('Tab', 'Curves'), self.curveComboBox)
        form.addRow(QApplication.translate('Label', 'Line style'), self.styleComboBox)
        form.addRow(QApplication.translate('Label', 'Width'), self.widthSpinBox)
        form.addRow(QApplication.translate('Button', 'Line Color'), self.colorButton)
        form.addRow('', self.restoreDefaultsButton)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self._load_selected()

    @staticmethod
    def _translated_curve_label(binding: CurveStyleBinding) -> str:
        if binding.label in {'ET', 'BT'}:
            return QApplication.translate('Label', binding.label)
        base = binding.label.removeprefix('Delta ')
        return deltaLabelUTF8 + QApplication.translate('Label', base)

    def _read_binding(self, binding: CurveStyleBinding) -> tuple[str, float, str]:
        style = getattr(self._qmc, binding.style_attr, '-')
        if not isinstance(style, str) or not style:
            style = '-'
        try:
            width = max(0.1, float(getattr(self._qmc, binding.width_attr, 1.0)))
        except (TypeError, ValueError):
            width = 1.0
        palette = getattr(self._qmc, 'palette', {})
        color = palette.get(binding.color_key, binding.default_color) if isinstance(palette, dict) else binding.default_color
        if not isinstance(color, str) or not QColor(rgba_colorname2argb_colorname(color)).isValid():
            color = binding.default_color
        return style, width, color

    def _selected_binding(self) -> CurveStyleBinding:
        binding = self.curveComboBox.currentData()
        if isinstance(binding, CurveStyleBinding):
            return binding
        return CURVE_STYLE_BINDINGS[0]

    def _capture_current(self) -> None:
        self._capture_binding(self._selected_binding())

    def _capture_binding(self, binding: CurveStyleBinding) -> None:
        self._pending[binding] = (
            str(self.styleComboBox.currentData() or '-'),
            float(self.widthSpinBox.value()),
            self.colorButton.text(),
        )

    def _load_selected(self, _index: int = -1) -> None:
        binding = self._selected_binding()
        if self._last_binding is not None and self._last_binding != binding:
            self._capture_binding(self._last_binding)
        self._last_binding = binding
        style, width, color = self._pending[binding]
        self.styleComboBox.blockSignals(True)
        style_index = self.styleComboBox.findData(style)
        self.styleComboBox.setCurrentIndex(max(0, style_index))
        self.styleComboBox.blockSignals(False)
        self.widthSpinBox.setValue(width)
        self._set_color_button(color)

    def _set_color_button(self, color: str) -> None:
        self.colorButton.setText(color)
        self.colorButton.setStyleSheet(
            'QPushButton { background-color: ' + rgba_colorname2argb_colorname(color) + '; }')

    def _select_color(self) -> None:
        self._capture_current()
        binding = self._selected_binding()
        current = QColor(rgba_colorname2argb_colorname(self._pending[binding][2]))
        selected = QColorDialog.getColor(current, self, QApplication.translate('Button', 'Line Color'))
        if not selected.isValid():
            return
        color = argb_colorname2rgba_colorname(selected.name(QColor.NameFormat.HexArgb))
        style, width, _ = self._pending[binding]
        self._pending[binding] = (style, width, color)
        self._set_color_button(color)

    def _restore_defaults(self) -> None:
        for binding in CURVE_STYLE_BINDINGS:
            width_default = (
                getattr(self._qmc, 'delta_linewidth_default', 1.0)
                if 'Delta' in binding.label
                else getattr(self._qmc, 'linewidth_default', 2.0)
            )
            self._pending[binding] = (
                '-',
                max(0.1, float(width_default)),
                binding.default_color,
            )
        self._load_selected()

    def accept(self) -> None:
        self._capture_current()
        palette = getattr(self._qmc, 'palette', None)
        if not isinstance(palette, dict):
            palette = {}
            self._qmc.palette = palette
        for binding, (style, width, color) in self._pending.items():
            setattr(self._qmc, binding.style_attr, style)
            setattr(self._qmc, binding.width_attr, width)
            palette[binding.color_key] = color
        if self._apply_callback is not None:
            self._apply_callback()
        super().accept()


__all__ = ['CURVE_STYLE_BINDINGS', 'CurveStyleBinding', 'CurveStyleDialog']
