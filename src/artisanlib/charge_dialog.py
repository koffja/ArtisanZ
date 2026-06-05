
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QCheckBox, QPushButton, QApplication,
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from artisanlib.charge_manager import ChargeTargetManager

class ChargeTempRorDlg(QDialog):
    def __init__(self, parent, charge_manager: ChargeTargetManager):
        super().__init__(parent)
        self.charge_manager = charge_manager
        self.setWindowTitle(QApplication.translate('ChargeTempRorDlg', '投豆目标设置'))
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Target Group ---
        target_group = QGroupBox(QApplication.translate('ChargeTempRorDlg', '目标参数'))
        target_layout = QGridLayout()
        
        # Temp
        temp_label = QLabel(QApplication.translate('ChargeTempRorDlg', '目标豆温:'))
        self.temp_spinbox = QDoubleSpinBox()
        self.temp_spinbox.setRange(0, 500)
        self.temp_spinbox.setDecimals(1)
        self.temp_spinbox.setSuffix(" °") 
        
        target_layout.addWidget(temp_label, 0, 0)
        target_layout.addWidget(self.temp_spinbox, 0, 1)

        # Temp Tolerance
        temp_tol_label = QLabel(QApplication.translate('ChargeTempRorDlg', '允许误差 (±):'))
        self.temp_tol_spinbox = QDoubleSpinBox()
        self.temp_tol_spinbox.setRange(0, 50)
        self.temp_tol_spinbox.setDecimals(1)
        self.temp_tol_spinbox.setSuffix(" °")
        
        target_layout.addWidget(temp_tol_label, 0, 2)
        target_layout.addWidget(self.temp_tol_spinbox, 0, 3)

        # RoR
        ror_label = QLabel(QApplication.translate('ChargeTempRorDlg', '目标升温率 (RoR):'))
        self.ror_spinbox = QDoubleSpinBox()
        self.ror_spinbox.setRange(0.1, 100) # RoR shouldn't be 0
        self.ror_spinbox.setDecimals(1)
        self.ror_spinbox.setSuffix(" /min")
        
        target_layout.addWidget(ror_label, 1, 0)
        target_layout.addWidget(self.ror_spinbox, 1, 1)

        # RoR Tolerance
        ror_tol_label = QLabel(QApplication.translate('ChargeTempRorDlg', '允许误差 (±):'))
        self.ror_tol_spinbox = QDoubleSpinBox()
        self.ror_tol_spinbox.setRange(0, 50)
        self.ror_tol_spinbox.setDecimals(1)
        self.ror_tol_spinbox.setSuffix(" /min")
        
        target_layout.addWidget(ror_tol_label, 1, 2)
        target_layout.addWidget(self.ror_tol_spinbox, 1, 3)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # --- Calculator Group ---
        calc_group = QGroupBox(QApplication.translate('ChargeTempRorDlg', '暖机效率换算 (RWT)'))
        calc_layout = QHBoxLayout()
        
        rwt_label = QLabel(QApplication.translate('ChargeTempRorDlg', '升温10°所需时间:'))
        self.rwt_spinbox = QDoubleSpinBox()
        self.rwt_spinbox.setRange(0, 600)
        self.rwt_spinbox.setDecimals(1)
        self.rwt_spinbox.setSuffix(" 秒")
        
        calc_layout.addWidget(rwt_label)
        calc_layout.addWidget(self.rwt_spinbox)
        
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)

        # Enabled
        self.enabled_checkbox = QCheckBox(QApplication.translate('ChargeTempRorDlg', '启用功能'))
        layout.addWidget(self.enabled_checkbox)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(QApplication.translate('ChargeTempRorDlg', '保存'))
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton(QApplication.translate('ChargeTempRorDlg', '取消'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # --- Signals ---
        self.ror_spinbox.valueChanged.connect(self.sync_rwt)
        self.rwt_spinbox.valueChanged.connect(self.sync_ror)

    def load_settings(self):
        self.charge_manager.update_settings(
            self.charge_manager.target_temp,
            self.charge_manager.target_ror,
            self.charge_manager.enabled,
            self.charge_manager.temp_tolerance,
            self.charge_manager.ror_tolerance
        )
        self.temp_spinbox.setValue(self.charge_manager.target_temp)
        self.temp_tol_spinbox.setValue(self.charge_manager.temp_tolerance)
        
        self.ror_spinbox.setValue(self.charge_manager.target_ror)
        self.ror_tol_spinbox.setValue(self.charge_manager.ror_tolerance)
        
        # Calculate initial RWT
        rwt = ChargeTargetManager.calculate_rwt(self.charge_manager.target_ror)
        self.rwt_spinbox.blockSignals(True)
        self.rwt_spinbox.setValue(rwt)
        self.rwt_spinbox.blockSignals(False)
        
        self.enabled_checkbox.setChecked(self.charge_manager.enabled)

    def sync_rwt(self, ror_value):
        if ror_value <= 0: return
        rwt = ChargeTargetManager.calculate_rwt(ror_value)
        self.rwt_spinbox.blockSignals(True)
        self.rwt_spinbox.setValue(rwt)
        self.rwt_spinbox.blockSignals(False)

    def sync_ror(self, rwt_value):
        if rwt_value <= 0: return
        ror = ChargeTargetManager.calculate_ror(rwt_value)
        self.ror_spinbox.blockSignals(True)
        self.ror_spinbox.setValue(ror)
        self.ror_spinbox.blockSignals(False)

    def save(self):
        self.charge_manager.update_settings(
            self.temp_spinbox.value(),
            self.ror_spinbox.value(),
            self.enabled_checkbox.isChecked(),
            self.temp_tol_spinbox.value(),
            self.ror_tol_spinbox.value()
        )
        self.accept()
