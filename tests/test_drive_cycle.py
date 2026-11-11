import numpy as np
import pytest

from hess import load_config
from hess.drive_cycle import PAPER_STATS, generate_urban_profile, profile_stats


@pytest.fixture(scope="module")
def profile():
    return generate_urban_profile(load_config())


def test_stats_within_tolerance(profile):
    s = profile_stats(profile)
    for k, ref in PAPER_STATS.items():
        assert abs(s[k] - ref) / ref <= 0.03, k


def test_starts_and_ends_at_rest(profile):
    v = profile["speed_mps"].to_numpy()
    assert v[0] == 0.0 and v[-1] == 0.0
    assert (v >= 0).all()


def test_deterministic():
    cfg = load_config()
    a = generate_urban_profile(cfg)["speed_mps"].to_numpy()
    b = generate_urban_profile(cfg)["speed_mps"].to_numpy()
    np.testing.assert_array_equal(a, b)


def test_no_accel_spikes_in_cruise(profile):
    # Rampalar dışında |a| küçük olmalı: ivme ya rampa değeri ya da < 0.2 m/s²
    a = profile["accel_mps2"].to_numpy()
    small = np.abs(a) < 0.2
    ramp = np.abs(a) >= 1.0
    # ara değerler yalnızca rampanın son (kısmi) adımında görülebilir
    assert (small | ramp).mean() > 0.97
