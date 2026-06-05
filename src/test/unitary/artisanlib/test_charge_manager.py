
import pytest
from typing import Optional
from artisanlib.charge_manager import ChargeTargetManager

class TestChargeTargetManager:
    
    def test_initial_state(self):
        manager = ChargeTargetManager()
        assert manager.enabled is False
        assert manager.active is True
        assert manager.target_temp == 0.0
        assert manager.target_ror == 0.0

    def test_update_settings(self):
        manager = ChargeTargetManager()
        manager.update_settings(180.0, 25.0, True)
        assert manager.target_temp == 180.0
        assert manager.target_ror == 25.0
        assert manager.enabled is True

    def test_charge_event_handling(self):
        manager = ChargeTargetManager()
        manager.on_charge_event()
        assert manager.active is False
        manager.reset()
        assert manager.active is True

    def test_prediction_basic(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True)
        prediction = manager.predict(current_temp=190.0, current_ror=60.0)
        assert prediction == pytest.approx(10.0, 0.1)

    def test_prediction_varying_ror(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True)
        prediction = manager.predict(current_temp=190.0, current_ror=40.0)
        assert prediction == pytest.approx(12.0, 0.1)

    def test_prediction_target_reached(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True)
        prediction = manager.predict(current_temp=205.0, current_ror=60.0)
        assert prediction == 0.0

    def test_prediction_invalid_ror(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True)
        assert manager.predict(190.0, 0.0) is None
        assert manager.predict(190.0, -10.0) is None

    def test_should_show_annotation(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True)
        manager.predict(195.0, 60.0) 
        assert manager.should_show_annotation() is True
        manager.predict(100.0, 60.0)
        assert manager.should_show_annotation() is False
        manager.update_settings(200.0, 60.0, False)
        manager.predict(195.0, 60.0)
        assert manager.should_show_annotation() is False
        manager.update_settings(200.0, 60.0, True)
        manager.on_charge_event()
        manager.predict(195.0, 60.0)
        assert manager.should_show_annotation() is False
