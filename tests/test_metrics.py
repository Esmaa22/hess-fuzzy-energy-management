import numpy as np
import pandas as pd
import pytest

from hess.metrics import compute
from hess.simulator import SimResult


def _res(i, discharge=None):
    n = len(i)
    log = pd.DataFrame({"i_b": i, "p_b": np.asarray(i) * 50.0, "p_sc": np.zeros(n),
                        "p_sc_bus": np.zeros(n), "p_mech": np.zeros(n), "p_dem": np.ones(n),
                        "temp_b": np.linspace(20, 21, n), "soc_sc": np.ones(n)})
    return SimResult("x", log, discharge, distance_km=1.0)


def test_current_metrics():
    m = compute(_res([3.0, -4.0, 0.0, 5.0]), i_rated=10.0, e_nominal_wh=100.0, t_amb=20.0)
    assert m["peak_I"] == 5.0
    assert m["mean_I"] == pytest.approx(3.0)
    assert m["rms_I"] == pytest.approx(np.sqrt(50 / 4))
    assert m["i2t"] == pytest.approx(50.0)
    assert m["severeness"] == pytest.approx(0.3)
    assert m["dT"] == pytest.approx(1.0)


def test_rms_ge_mean_abs():
    """Makaledeki tutarsızlığın tersine RMS her zaman ortalama |I|'dan büyük ya da eşit."""
    rng = np.random.default_rng(0)
    m = compute(_res(rng.normal(30, 40, 1000)), 73.7, 3700.0, 20.0)
    assert m["rms_I"] >= m["mean_I"]


def test_range_definitions():
    m = compute(_res([10.0] * 3600, discharge=3600), 73.7, 1000.0, 20.0)
    # terminal enerjisi 500 Wh, mesafe 1 km
    assert m["ecr_phys"] == pytest.approx(500.0)
    assert m["range_phys"] == pytest.approx(0.8 * 1000 / 500)
    assert m["range_paper"] == pytest.approx(1.0)          # makale tanımı = gidilen mesafe
    assert np.isnan(compute(_res([1.0]), 73.7, 1.0, 20.0)["ecr_paper"])
