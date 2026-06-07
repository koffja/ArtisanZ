from artisanlib.charge_manager import ChargeTargetManager


def test_readiness_user_facing_text_is_short():
    manager = ChargeTargetManager()
    manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

    readiness = manager.evaluate_readiness(200.0, 60.0, short_ror=60.0, long_ror=60.0)

    assert readiness.title == '可以投豆'
    assert len(readiness.title) <= 6
    assert readiness.reason == '温度到位，升温稳定'
    assert len(readiness.reason) <= 12


def test_legacy_status_message_uses_readiness_reason_and_color():
    manager = ChargeTargetManager()
    manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

    message, color = manager.get_status_message(current_ror=60.0, current_temp=200.0)

    assert message == '温度到位，升温稳定'
    assert color == 'green'
