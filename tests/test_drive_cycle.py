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


def test_micro_fluctuation_bounded(profile):
    """Seyir dalgalanması ivme uç değerlerini aşmamalı ve gerçekçi düzeyde kalmalı (A-17)."""
    v = profile["speed_kmh"].to_numpy()
    a = profile["accel_mps2"].to_numpy()
    cruise = v > 30
    assert a.max() <= 2.7 + 1e-9 and a.min() >= -2.6 - 1e-9
    assert np.sqrt(np.mean(a[cruise] ** 2)) < 1.0
