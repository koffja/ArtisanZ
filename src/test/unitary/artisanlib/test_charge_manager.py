
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

    def test_should_show_annotation_tracks_enabled_flag(self):
        manager = ChargeTargetManager()
        assert manager.should_show_annotation() is False

        manager.update_settings(200.0, 60.0, True)
        assert manager.should_show_annotation() is True

        manager.update_settings(200.0, 60.0, False)
        assert manager.should_show_annotation() is False

    def test_readiness_ready_when_temperature_and_ror_match(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(
            current_temp=200.2,
            current_ror=59.0,
            short_ror=59.5,
            long_ror=59.0,
        )

        assert readiness.status == 'ready'
        assert readiness.color == 'green'
        assert readiness.title == '可以投豆'
        assert readiness.reason == '温度到位，升温稳定'
        assert readiness.prediction_seconds == 0.0
        assert readiness.current_rwt == pytest.approx(600.0 / 59.0)
        assert readiness.target_rwt == pytest.approx(10.0)

    def test_readiness_near_when_prediction_is_short(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(
            current_temp=194.0,
            current_ror=60.0,
            short_ror=60.0,
            long_ror=60.0,
        )

        assert readiness.status == 'near'
        assert readiness.color == 'green'
        assert readiness.title == '接近目标'
        assert readiness.prediction_seconds == pytest.approx(6.0)

    def test_readiness_hot_when_temperature_exceeds_tolerance(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(current_temp=202.0, current_ror=50.0)

        assert readiness.status == 'hot'
        assert readiness.color == 'red'
        assert readiness.title == '偏热'
        assert readiness.reason == '温度超过目标'

    def test_readiness_unstable_when_ror_trend_changes_too_fast(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(
            current_temp=200.0,
            current_ror=60.0,
            short_ror=66.0,
            long_ror=60.0,
        )

        assert readiness.status == 'unstable'
        assert readiness.color == 'blue'
        assert readiness.title == '趋势不稳'
        assert readiness.reason == '升温变化过大'

    def test_readiness_waiting_when_far_from_target(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(current_temp=180.0, current_ror=30.0)

        assert readiness.status == 'waiting'
        assert readiness.color == 'gray'
        assert readiness.title == '等待升温'
        assert readiness.reason == '距离目标还远'

    def test_readiness_insufficient_when_ror_is_invalid(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(current_temp=198.0, current_ror=0.0)

        assert readiness.status == 'insufficient'
        assert readiness.color == 'gray'
        assert readiness.title == '等待数据'
        assert readiness.reason == '升温数据不足'
        assert readiness.prediction_seconds is None
