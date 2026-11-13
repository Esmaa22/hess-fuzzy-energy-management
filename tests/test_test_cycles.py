"""X3 test çevrimleri: eğitim çevriminden ayrı, deterministik, istatistikleri kalibre."""

import numpy as np

from hess import load_config
from hess.test_cycles import REGIMES, TRAIN_SEED, make_test_cycles


def test_test_cycles_basic():
    cfg = load_config()
    cyc = make_test_cycles(cfg, n_per_regime=1)
    assert [c["regime"] for c in cyc] == list(REGIMES)
    assert all(c["seed"] != TRAIN_SEED for c in cyc)
    for c in cyc:
        assert abs(c["stats"]["distance_km"] - cfg["drive_cycle"]["distance_km"]) < 0.05 * 12.4
        assert len(c["profile"]) == cfg["drive_cycle"]["duration_s"]
    again = make_test_cycles(cfg, n_per_regime=1)
    np.testing.assert_array_equal(cyc[0]["profile"].speed_mps, again[0]["profile"].speed_mps)
    # Agresif rejim sakin rejimden daha "dalgalı" olmalı
    s = lambda d: np.abs(np.diff(d["profile"].speed_mps)).mean()
    assert s(cyc[2]) > s(cyc[0])
