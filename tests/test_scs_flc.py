"""SCS-FLC (önerilen yöntem S1) ve simülatördeki bataryadan SC şarjı (D-20) testleri."""

import numpy as np
import pytest

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.scs_flc import RULES, SCSFLCEMS, scs_params
from hess.simulator import EMS, Simulator


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def sim(cfg):
    return Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))


@pytest.fixture(scope="module")
def s1(cfg):
    return SCSFLCEMS(cfg)


# --------------------------------------------------------------------------- kural tabanı
def test_rule_base_shape(s1):
    assert len(s1.fis.rules) == 12                              # 4 × 3
    assert {r.antecedent["p_dem"] for r in s1.fis.rules} == set(RULES)
    assert all(set(r.antecedent) == {"p_dem", "soc_sc"} for r in s1.fis.rules)


def test_input_mfs_match_reference_flc(cfg):
    """CP4 §3: girdi MF'leri referans FLC ile aynı (fark yalnızca kurallardan gelsin)."""
    p = scs_params(cfg)
    assert p["p_terms"] == cfg["flc"]["p_terms"]
    assert p["soc_terms"] == cfg["flc"]["soc_terms"]


def test_overrides_do_not_touch_cfg(cfg):
    before = dict(cfg["scs_flc"]["pch_levels"])
    e = SCSFLCEMS(cfg, overrides={"pch_levels": {"High": 1500}})
    assert e.params["pch_levels"]["High"] == 1500 and e.params["pch_levels"]["Low"] == 300
    assert cfg["scs_flc"]["pch_levels"] == before
    assert e.decide(500.0, 0.05)[1] == pytest.approx(1500.0, abs=1.0)


# --------------------------------------------------------------------------- karar yüzeyi
@pytest.mark.parametrize("p, soc, c_sc, p_ch", [
    (500.0, 0.05, 0.0, 1200.0),    # düşük talep, SC boş   -> yalnızca şarj (Yüksek)
    (500.0, 0.50, 0.0, 700.0),     # düşük talep, SC orta  -> şarj (Orta)
    (500.0, 0.95, 0.0, 0.0),       # düşük talep, SC dolu  -> hiçbir şey
    (2500.0, 0.50, 10.0, 0.0),     # orta talep, SC orta   -> küçük SC payı
    (5000.0, 0.95, 60.0, 0.0),     # yüksek talep, SC dolu -> en büyük SC payı
    (5000.0, 0.05, 20.0, 0.0),     # yüksek talep, SC boş  -> küçük pay, şarj yok
    (-2000.0, 0.50, 100.0, 0.0),   # frenleme              -> enerjinin tamamı SC'ye
])
def test_decision_surface_cores(s1, p, soc, c_sc, p_ch):
    """Tek bir kuralın tam ateşlendiği noktalarda çıktı o kuralın seviyesine eşit olmalı."""
    got_c, got_p = s1.decide(p, soc)
    assert got_c == pytest.approx(c_sc, abs=0.05)
    assert got_p == pytest.approx(p_ch, abs=1.0)


def test_pch_decreases_with_soc_sc(s1):
    """Geri besleme: SC doldukça şarj gücü azalmalı (monoton, artmayan)."""
    vals = [s1.decide(500.0, s)[1] for s in np.linspace(0, 1, 41)]
    assert np.all(np.diff(vals) <= 1e-6)
    assert vals[0] > 1000 and vals[-1] < 1.0


def test_csc_increases_with_demand_and_soc(s1):
    for s in (0.1, 0.5, 0.9):
        c = [s1.decide(p, s)[0] for p in np.linspace(0, 5600, 57)]
        assert np.all(np.diff(c) >= -1e-6)
    for p in (2500.0, 5000.0):
        c = [s1.decide(p, s)[0] for s in np.linspace(0, 1, 41)]
        assert np.all(np.diff(c) >= -1e-6)


def test_request_sign(s1):
    assert s1.sc_request(500.0, 0.9, 0.1) < 0           # şarj isteği
    assert s1.sc_request(5000.0, 0.9, 0.9) > 0          # tepe tıraşlama
    assert s1.sc_request(-1000.0, 0.9, 0.5) == pytest.approx(-1000.0, rel=1e-3)


def test_no_recharge_ablation(cfg):
    a1 = SCSFLCEMS(cfg, recharge=False)
    assert not a1.sc_recharge and a1.name == "scs_flc_no_recharge"
    assert a1.sc_request(500.0, 0.9, 0.05) == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------- simülatör (D-20)
class ConstCharge(EMS):
    name = "const_charge"
    sc_recharge = True

    def __init__(self, p_ch):
        self.p_ch = p_ch

    def sc_request(self, p_dem, soc_b, soc_sc):
        return -self.p_ch if p_dem >= 0 else p_dem


class ConstChargeNoFlag(ConstCharge):
    sc_recharge = False


def test_recharge_bus_balance_and_bounds(sim):
    log = sim.run(ConstCharge(1000.0), soc_b=0.9, soc_sc=0.2, max_cycles=2).log
    np.testing.assert_allclose(log.p_b_bus + log.p_sc_bus + log.p_mech - log.p_dem, 0.0, atol=1e-9)
    assert log.soc_sc.min() >= -1e-9 and log.soc_sc.max() <= 1 + 1e-9
    trac = log.p_dem >= 0
    charging = trac & (log.p_sc_bus < 0)
    assert charging.any()
    assert (log.p_b_bus[charging] > log.p_dem[charging]).all()     # batarya fazlasını veriyor
    assert log.soc_sc.iloc[-1] > 0.9                               # SC doldu
    # SC dolunca şarj kendiliğinden kesilmeli (güvenlik katmanı)
    full = trac & (log.soc_sc.shift(1) >= 1 - 1e-9)
    assert (log.p_sc_bus[full] > -1e-6).all()


def test_recharge_needs_flag(sim):
    """Bayrak kapalıysa negatif çekiş isteği eskisi gibi 0'a kırpılır."""
    log = sim.run(ConstChargeNoFlag(1000.0), soc_b=0.9, soc_sc=0.2, max_cycles=1).log
    trac = log.p_dem >= 0
    assert (log.p_sc_bus[trac] == 0).all()


def test_recharge_limit_clips_to_sc_capacity(sim):
    sim.bat.reset(0.9)
    sim.sc.reset(1.0)
    assert sim._recharge_limit(0.0, 1000.0) == pytest.approx(0.0, abs=1e-9)
    sim.sc.reset(0.2)
    assert sim._recharge_limit(0.0, 1000.0) == pytest.approx(1000.0)


def test_baseline_flc_unchanged_by_flag(sim, cfg):
    """FLC'nin sc_recharge'ı kapalı: sonuçları D-20 öncesiyle aynı kalmalı (çekişte SC ≥ 0)."""
    log = sim.run(FLCEMS(cfg), max_cycles=1).log
    assert (log.p_sc_bus[log.p_dem >= 0] >= 0).all()


def test_scs_flc_short_run(sim, s1):
    """İki çevrimlik duman testi: güç dengesi, SC sınırları, şarj gerçekten kullanılıyor."""
    log = sim.run(s1, soc_b=1.0, soc_sc=0.3, max_cycles=2).log
    np.testing.assert_allclose(log.p_b_bus + log.p_sc_bus + log.p_mech - log.p_dem, 0.0, atol=1e-9)
    assert ((log.p_dem >= 0) & (log.p_sc_bus < 0)).any()
    assert log.soc_sc.min() >= -1e-9 and log.soc_sc.max() <= 1 + 1e-9
    assert log.soc_sc.iloc[-1] > 0.3
