import pytest
from dev_simulator.profile import RoastSpec


@pytest.fixture
def default_spec() -> RoastSpec:
    return RoastSpec()


@pytest.fixture
def no_noise_spec() -> RoastSpec:
    return RoastSpec(noise_model="none", noise_std=0.0)
