from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QCheckBox, QPushButton, QApplication,
    QGroupBox, QGridLayout,
)
from artisanlib.rorflick_manager import RoRFlickManager


class RoRFlickDlg(QDialog):
    """Settings dialog for RoR flick/crash detector. Mutates manager in place."""

    def __init__(self, parent, manager: RoRFlickManager):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle(QApplication.translate('RoRFlickDlg', 'RoR 异常检测设置'))
        self.setup_ui()
        self.load_settings()

    # Machine type presets: (flick, crash, exit, dev_mult)
    _PRESETS = {
        'electric': (3.0, 3.0, 0.5, 1.5),   # 电热鼓式 — 稳定热惯性，低阈值
        'gas': (7.0, 7.0, 1.5, 1.5),         # 燃气大鼓 — 噪声大，高阈值
        'sample': (5.0, 5.0, 1.0, 1.5),       # 样品烘焙机 — 当前默认
    }

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # --- Preset Group ---
        preset_group = QGroupBox(QApplication.translate('RoRFlickDlg', '机器类型预设'))
        preset_layout = QHBoxLayout()

        electric_btn = QPushButton(QApplication.translate('RoRFlickDlg', '电热鼓式'))
        electric_btn.clicked.connect(lambda: self._apply_preset('electric'))
        gas_btn = QPushButton(QApplication.translate('RoRFlickDlg', '燃气大鼓'))
        gas_btn.clicked.connect(lambda: self._apply_preset('gas'))
        sample_btn = QPushButton(QApplication.translate('RoRFlickDlg', '样品烘焙机'))
        sample_btn.clicked.connect(lambda: self._apply_preset('sample'))

        preset_layout.addWidget(electric_btn)
        preset_layout.addWidget(gas_btn)
        preset_layout.addWidget(sample_btn)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # --- Threshold Group ---
        thresh_group = QGroupBox(QApplication.translate('RoRFlickDlg', '检测阈值'))
        thresh_layout = QGridLayout()

        flick_label = QLabel(QApplication.translate('RoRFlickDlg', 'Flick 触发 (°C/min):'))
        self.flick_spinbox = QDoubleSpinBox()
        self.flick_spinbox.setRange(0.5, 30.0)
        self.flick_spinbox.setDecimals(1)
        self.flick_spinbox.setSingleStep(0.5)
        self.flick_spinbox.setSuffix(' /min')
        thresh_layout.addWidget(flick_label, 0, 0)
        thresh_layout.addWidget(self.flick_spinbox, 0, 1)

        crash_label = QLabel(QApplication.translate('RoRFlickDlg', 'Crash 触发 (°C/min):'))
        self.crash_spinbox = QDoubleSpinBox()
        self.crash_spinbox.setRange(0.5, 30.0)
        self.crash_spinbox.setDecimals(1)
        self.crash_spinbox.setSingleStep(0.5)
        self.crash_spinbox.setSuffix(' /min')
        thresh_layout.addWidget(crash_label, 1, 0)
        thresh_layout.addWidget(self.crash_spinbox, 1, 1)

        exit_label = QLabel(QApplication.translate('RoRFlickDlg', '退出阈值 (°C/min):'))
        self.exit_spinbox = QDoubleSpinBox()
        self.exit_spinbox.setRange(0.1, 5.0)
        self.exit_spinbox.setDecimals(1)
        self.exit_spinbox.setSingleStep(0.1)
        self.exit_spinbox.setSuffix(' /min')
        thresh_layout.addWidget(exit_label, 2, 0)
        thresh_layout.addWidget(self.exit_spinbox, 2, 1)

        thresh_group.setLayout(thresh_layout)
        layout.addWidget(thresh_group)

        # --- Dev Phase Group ---
        dev_group = QGroupBox(QApplication.translate('RoRFlickDlg', 'Development 加权'))
        dev_layout = QHBoxLayout()
        dev_label = QLabel(QApplication.translate('RoRFlickDlg', '一爆后严重度倍数:'))
        self.dev_spinbox = QDoubleSpinBox()
        self.dev_spinbox.setRange(1.0, 3.0)
        self.dev_spinbox.setDecimals(1)
        self.dev_spinbox.setSingleStep(0.1)
        dev_layout.addWidget(dev_label)
        dev_layout.addWidget(self.dev_spinbox)
        dev_group.setLayout(dev_layout)
        layout.addWidget(dev_group)

        # Enabled checkbox
        self.enabled_checkbox = QCheckBox(QApplication.translate('RoRFlickDlg', '启用功能'))
        layout.addWidget(self.enabled_checkbox)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(QApplication.translate('RoRFlickDlg', '保存'))
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton(QApplication.translate('RoRFlickDlg', '取消'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _apply_preset(self, preset: str) -> None:
        """Apply a machine-type preset to the threshold spinboxes."""
        values = self._PRESETS.get(preset)
        if values is None:
            return
        flick, crash, exit_val, dev_mult = values
        self.flick_spinbox.setValue(flick)
        self.crash_spinbox.setValue(crash)
        self.exit_spinbox.setValue(exit_val)
        self.dev_spinbox.setValue(dev_mult)

    def load_settings(self) -> None:
        self.flick_spinbox.setValue(self.manager.flick_threshold)
        self.crash_spinbox.setValue(self.manager.crash_threshold)
        self.exit_spinbox.setValue(self.manager.exit_threshold)
        self.dev_spinbox.setValue(self.manager.dev_phase_multiplier)
        self.enabled_checkbox.setChecked(self.manager.enabled)

    def save(self) -> None:
        self.manager.update_settings(
            enabled=self.enabled_checkbox.isChecked(),
            flick_threshold=self.flick_spinbox.value(),
            crash_threshold=self.crash_spinbox.value(),
            exit_threshold=self.exit_spinbox.value(),
            dev_phase_multiplier=self.dev_spinbox.value(),
        )
        self.accept()
