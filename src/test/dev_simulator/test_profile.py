"""Tests for dev_simulator.profile — RoastSpec, generate_profile, apply_noise."""

import math
import pytest
from dev_simulator.profile import RoastSpec, generate_profile, apply_noise


# ---------------------------------------------------------------------------
# RoastSpec dataclass
# ---------------------------------------------------------------------------


class TestRoastSpecDefaults:
    """All 21 fields must match spec defaults."""

    def test_default_values(self):
        s = RoastSpec()
        # 7 nodes × 3 fields (t, bt, et) = 21, plus sample_hz, noise_std, noise_model
        assert s.charge_t == 0.0
        assert s.charge_bt == 180.0
        assert s.charge_et == 190.0
        assert s.turn_t == 90.0
        assert s.turn_bt == 95.0
        assert s.turn_et == 180.0
        assert s.dry_t == 300.0
        assert s.dry_bt == 152.0
        assert s.dry_et == 170.0
        assert s.fcs_t == 570.0
        assert s.fcs_bt == 193.0
        assert s.fcs_et == 205.0
        assert s.fce_t == 645.0
        assert s.fce_bt == 202.0
        assert s.fce_et == 212.0
        assert s.scs_t == 765.0
        assert s.scs_bt == 215.0
        assert s.scs_et == 222.0
        assert s.drop_t == 780.0
        assert s.drop_bt == 218.0
        assert s.drop_et == 224.0
        assert s.sample_hz == 10
        assert s.noise_std == 0.3
        assert s.noise_model == "ar1"

    def test_frozen(self):
        s = RoastSpec()
        with pytest.raises(AttributeError):
            s.charge_bt = 999.0  # type: ignore[misc]


class TestRoastSpecValidation:
    """Invalid node values must raise ValueError."""

    def test_nan_rejected(self):
        with pytest.raises(ValueError):
            RoastSpec(charge_bt=float("nan"))

    def test_inf_rejected(self):
        with pytest.raises(ValueError):
            RoastSpec(turn_et=float("inf"))

    def test_negative_inf_rejected(self):
        with pytest.raises(ValueError):
            RoastSpec(dry_t=float("-inf"))


# ---------------------------------------------------------------------------
# generate_profile
# ---------------------------------------------------------------------------


class TestGenerateProfile:
    """Core profile generation with no noise."""

    @pytest.fixture()
    def clean_profile(self):
        """Profile generated with noise disabled."""
        return generate_profile(RoastSpec(noise_model="none", noise_std=0.0))

    def test_profile_has_required_keys(self, clean_profile):
        for key in ("timex", "temp1", "temp2", "mode"):
            assert key in clean_profile

    def test_mode_is_celsius(self, clean_profile):
        assert clean_profile["mode"] == "C"

    def test_profile_length(self, clean_profile):
        # 10 Hz × 780 s + 1 (inclusive both ends) = 7801
        assert len(clean_profile["timex"]) == 7801
        assert len(clean_profile["temp1"]) == 7801
        assert len(clean_profile["temp2"]) == 7801

    def test_timex_in_milliseconds(self, clean_profile):
        assert clean_profile["timex"][0] == 0.0
        assert clean_profile["timex"][-1] == pytest.approx(780_000.0)
        # Step should be 100 ms (= 1/10 Hz)
        step = clean_profile["timex"][1] - clean_profile["timex"][0]
        assert step == pytest.approx(100.0)

    def test_no_nan_inf(self, clean_profile):
        for arr_name in ("timex", "temp1", "temp2"):
            for v in clean_profile[arr_name]:
                assert math.isfinite(v), f"non-finite in {arr_name}"

    def test_charge_dip_monotonic_decrease(self, clean_profile):
        """BT strictly decreases from charge (t=0) to turn (~t=90s)."""
        # Indices 0..900 (= 0..90s at 10Hz)
        bt = clean_profile["temp2"]
        for i in range(1, 901):
            assert bt[i] < bt[i - 1], f"BT not decreasing at idx {i}: {bt[i]} >= {bt[i-1]}"

    def test_after_turn_monotonic_increase(self, clean_profile):
        """BT increases from turn (~90s) through drop (780s)."""
        bt = clean_profile["temp2"]
        # Start checking from index 901 onward (= 90.1s)
        for i in range(901, len(bt)):
            assert bt[i] >= bt[i - 1], f"BT not increasing at idx {i}: {bt[i]} < {bt[i-1]}"

    def test_event_temperatures_at_nodes(self, clean_profile):
        """BT at anchor timestamps must match spec values ±0.01."""
        spec = RoastSpec(noise_model="none", noise_std=0.0)
        nodes = [
            (spec.charge_t, spec.charge_bt),
            (spec.turn_t, spec.turn_bt),
            (spec.dry_t, spec.dry_bt),
            (spec.fcs_t, spec.fcs_bt),
            (spec.fce_t, spec.fce_bt),
            (spec.scs_t, spec.scs_bt),
            (spec.drop_t, spec.drop_bt),
        ]
        bt = clean_profile["temp2"]
        timex = clean_profile["timex"]
        for t_sec, expected_bt in nodes:
            # Find index: t_sec * 10 (at 10Hz)
            idx = int(t_sec * 10)
            assert timex[idx] == pytest.approx(t_sec * 1000.0, abs=1.0)
            assert bt[idx] == pytest.approx(expected_bt, abs=0.01), (
                f"BT at t={t_sec}s: got {bt[idx]}, expected {expected_bt}"
            )


# ---------------------------------------------------------------------------
# apply_noise
# ---------------------------------------------------------------------------


class TestApplyNoise:
    """Noise helpers."""

    def test_noise_none_returns_zeros(self):
        result = apply_noise(100, "none", 0.3)
        assert len(result) == 100
        assert all(v == 0.0 for v in result)

    def test_noise_gaussian_nonzero(self):
        result = apply_noise(1000, "gaussian", 0.3)
        assert len(result) == 1000
        # Statistically very unlikely to be all zeros with std=0.3
        nonzero = sum(1 for v in result if abs(v) > 1e-9)
        assert nonzero > 0

    def test_noise_ar1_correlation(self):
        """AR(1) adjacent diffs should be smaller than IID diffs."""
        n = 5000
        ar1 = apply_noise(n, "ar1", 0.3, alpha=0.85)
        gauss = apply_noise(n, "gaussian", 0.3)
        assert len(ar1) == n
        assert len(gauss) == n

        # Mean absolute adjacent diff
        ar1_diffs = [abs(ar1[i] - ar1[i - 1]) for i in range(1, n)]
        gauss_diffs = [abs(gauss[i] - gauss[i - 1]) for i in range(1, n)]
        ar1_mad = sum(ar1_diffs) / len(ar1_diffs)
        gauss_mad = sum(gauss_diffs) / len(gauss_diffs)
        # AR1 should have smoother transitions (smaller diffs)
        assert ar1_mad < gauss_mad * 0.5, (
            f"AR1 MAD={ar1_mad:.4f} not < 0.5×gauss MAD={gauss_mad:.4f}"
        )

    def test_noise_invalid_model_raises(self):
        with pytest.raises(ValueError):
            apply_noise(100, "unknown", 0.3)


# ---------------------------------------------------------------------------
# Integration: profile with noise
# ---------------------------------------------------------------------------


class TestProfileWithNoise:
    """Ensure noise is applied and clamped correctly."""

    def test_profile_with_ar1_noise(self):
        prof = generate_profile(RoastSpec())  # default ar1 noise
        for arr_name in ("temp1", "temp2"):
            for v in prof[arr_name]:
                assert 0.0 <= v <= 500.0, f"out of range in {arr_name}: {v}"

    def test_profile_with_gaussian_noise(self):
        prof = generate_profile(RoastSpec(noise_model="gaussian"))
        for arr_name in ("temp1", "temp2"):
            for v in prof[arr_name]:
                assert 0.0 <= v <= 500.0, f"out of range in {arr_name}: {v}"
