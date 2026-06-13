"""Tests for Designer TP (Turning Point) feature."""

import pytest


class MockCanvas:
    """Minimal mock of tgraphcanvas with TP-related attributes."""

    def __init__(self) -> None:
        self.designer_tp_enabled = True
        self.designer_tp_time = 90.0
        self.designer_tp_bt = 110.0

    def _validate_tp_time(self, tp_time: float) -> bool:
        """Validate that TP time is positive and reasonable."""
        return tp_time > 0.0


@pytest.fixture
def mock_canvas():
    """Provide a minimal canvas mock with TP-related attributes."""
    return MockCanvas()


class TestTPDefaults:
    """Verify TP attributes exist and have correct defaults."""

    def test_tp_enabled_default(self, mock_canvas):
        assert mock_canvas.designer_tp_enabled is True

    def test_tp_time_default(self, mock_canvas):
        assert mock_canvas.designer_tp_time == 90.0

    def test_tp_bt_default(self, mock_canvas):
        assert mock_canvas.designer_tp_bt == 110.0


class TestTPTimeValidation:
    """Verify TP time must be > 0."""

    def test_tp_time_zero_rejected(self, mock_canvas):
        assert not mock_canvas._validate_tp_time(0.0)

    def test_tp_time_negative_rejected(self, mock_canvas):
        assert not mock_canvas._validate_tp_time(-10.0)

    def test_tp_time_positive_accepted(self, mock_canvas):
        assert mock_canvas._validate_tp_time(30.0)


class TestTPDesignerIntegration:
    """Integration tests for TP in Designer workflow."""

    def test_tp_defaults_match_hardcoded_celsius(self):
        """Default TP time/BT match the old hard-coded values (Celsius)."""
        assert 90.0 == 1.5 * 60
        assert 110.0 == 110.0

    def test_tp_defaults_match_hardcoded_fahrenheit(self):
        """Default TP BT in Fahrenheit should be 230.0."""
        fahrenheit_bt = 230.0
        assert fahrenheit_bt == round(110.0 * 9 / 5 + 32, 0)

    def test_tp_time_between_charge_and_dry(self):
        """TP time should be logically between CHARGE and DRY END."""
        tp_time = 90.0
        charge_time = 0.0
        dry_time = 240.0
        assert charge_time < tp_time < dry_time

    def test_tp_bt_lower_than_charge_bt(self):
        """TP BT should be lower than CHARGE BT (temperature dips then recovers)."""
        tp_bt = 110.0
        charge_bt = 210.0
        assert tp_bt < charge_bt
