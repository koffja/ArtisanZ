import sys
import os
import pytest

_src_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_test_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path = [p for p in sys.path if p != _test_abs]
if _src_abs not in sys.path:
    sys.path.insert(0, _src_abs)

# Clear stale dev_simulator entries (pytest may have loaded test/dev_simulator
# as the package), but keep our own module alive.
_me = sys.modules.get(__name__)
for key in list(sys.modules):
    if "dev_simulator" in key.split(".")[0]:
        del sys.modules[key]
if _me is not None:
    sys.modules[__name__] = _me

from dev_simulator.profile import RoastSpec


@pytest.fixture
def default_spec() -> RoastSpec:
    return RoastSpec()


@pytest.fixture
def no_noise_spec() -> RoastSpec:
    return RoastSpec(noise_model="none", noise_std=0.0)
