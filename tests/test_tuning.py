"""Adım 7.2 ayar altyapısı testleri (C0, S1 çarpanları, tasarım, ayarlı değer dosyası)."""

import numpy as np
import pytest

from hess import load_config
from hess.crisp_ems import CrispEMS
from hess.scs_flc import SCSFLCCapEMS, SCSFLCEMS, scs_params
from hess.tuning import (BUDGET, SPACES, START, design, load_tuned, make_ems, s1_overrides,
                         s2_overrides, save_tuned)


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_unit_factors_reproduce_draft(cfg):
    """Bütün çarpanlar 1 iken S1, CP4 §3 taslağıyla birebir aynı karar vermeli."""
    a, b = SCSFLCEMS(cfg), SCSFLCEMS(cfg, overrides=s1_overrides(cfg))
    for p in (-2000, 0, 500, 1500, 2500, 3500, 5000):
        for s in (0.05, 0.3, 0.5, 0.7, 0.95):
            assert a.decide(p, s) == pytest.approx(b.decide(p, s))


@pytest.mark.parametrize("k", [0.75, 0.8, 1.2, 1.3])
def test_scaled_mfs_stay_valid(cfg, k):
    ov = s1_overrides(cfg, k_p=k, k_soc=min(k, 1.2))
    p = scs_params(cfg, ov)
    for terms in (p["p_terms"], p["soc_terms"]):
        for pts in terms.values():
            assert all(x <= y for x, y in zip(pts, pts[1:]))     # a ≤ b ≤ c ≤ d
    # Ruspini: pozitif P_dem ve SoC aralığında üyelikler toplamı 1
    e = SCSFLCEMS(cfg, overrides=ov)
    pd_var, soc_var = e.fis.inputs
    for x in np.linspace(0, 5600, 113):
        assert sum(pd_var.fuzzify(x).values()) == pytest.approx(1.0)
    for x in np.linspace(0, 100, 101):
        assert sum(soc_var.fuzzify(x).values()) == pytest.approx(1.0)


def test_scaling_fixes_end_levels(cfg):
    ov = s1_overrides(cfg, k_csc=1.5, k_ch=2.0)
    assert ov["csc_levels"]["Z"] == 0 and ov["csc_levels"]["Full"] == 100
    assert ov["csc_levels"]["VL"] == pytest.approx(90.0)
    assert ov["pch_levels"]["High"] == pytest.approx(2400.0) and ov["pch_levels"]["Zero"] == 0


def test_design_equal_budget_and_bounds():
    for m, space in SPACES.items():
        pts = design(m)
        assert len(pts) == BUDGET and pts[0] == START[m]
        for prm in pts[1:]:
            for k, (lo, hi) in space.items():
                assert lo <= prm[k] <= hi
        assert design(m) == pts                                   # deterministik


def test_crisp_rules():
    c = CrispEMS(3000, 1500, 1000, 0.8)
    assert c.sc_recharge
    assert c.sc_request(4000, 1, 0.5) == 1000                     # tepe tıraşlama
    assert c.sc_request(-500, 1, 0.5) == -500                     # frenleme
    assert c.sc_request(1000, 1, 0.5) == -1000                    # şarj
    assert c.sc_request(1000, 1, 0.9) == 0                        # hedefin üstünde
    assert c.sc_request(2000, 1, 0.5) == 0                        # ölü bant


def test_tuned_roundtrip(tmp_path, cfg):
    best = {"C0": {"p_th": 2500.0, "p_lo": 1000.0, "p_ch": 1200.0, "target": 0.9},
            "S1": {"k_ch": 1.2, "k_csc": 1.0, "k_p": 1.1, "k_soc": 1.0},
            "S2": {"c_cap": 2800.0, "d_cap": 500.0, "k_ch": 1.1, "k_soc": 1.0}}
    f = tmp_path / "tuned.yaml"
    save_tuned(best, f, meta={"butce": 24})
    assert load_tuned(f) == best
    assert load_tuned(tmp_path / "yok.yaml") == START
    assert make_ems("S1", cfg, best["S1"]).sc_recharge
    assert not make_ems("S1", cfg, best["S1"], recharge=False).sc_recharge


# --------------------------------------------------------------------------- S2 (D-23)
def test_s2_rule_structure(cfg):
    e = SCSFLCCapEMS(cfg)
    assert len(e.fis.rules) == 12
    assert [o.name for o in e.fis.outputs] == ["p_cap", "p_ch"]


@pytest.mark.parametrize("soc, cap", [(0.05, 4000.0), (0.5, 3000.0), (0.95, 2000.0)])
def test_s2_cap_follows_soc(cfg, soc, cap):
    e = SCSFLCCapEMS(cfg)
    assert e.decide(5000.0, soc)[0] == pytest.approx(cap, abs=1.0)
    caps = [e.decide(5000.0, s)[0] for s in np.linspace(0, 1, 41)]
    assert np.all(np.diff(caps) <= 1e-6)                          # SC doldukça tavan düşer


def test_s2_request(cfg):
    e = SCSFLCCapEMS(cfg)
    assert e.sc_request(5000.0, 1, 0.95) == pytest.approx(3000.0, abs=1.0)   # 5000 − 2000
    assert e.sc_request(2500.0, 1, 0.95) == pytest.approx(500.0, abs=1.0)
    assert e.sc_request(-800.0, 1, 0.5) == -800.0
    assert e.sc_request(500.0, 1, 0.05) == pytest.approx(-1200.0, abs=1.0)   # yalnızca şarj
    assert SCSFLCCapEMS(cfg, recharge=False).sc_request(500.0, 1, 0.05) == 0.0


def test_s2_overrides_constant_cap(cfg):
    e = SCSFLCCapEMS(cfg, overrides=s2_overrides(cfg, c_cap=2500.0, d_cap=0.0))
    for s in (0.05, 0.5, 0.95):
        assert e.decide(5000.0, s)[0] == pytest.approx(2500.0, abs=1e-6)


# --------------------------------------------------------------------------- X2 ablasyonları
def test_a3_soc_b_rules(cfg):
    from hess.scs_flc import SCSFLCCapEMS
    for cls in (SCSFLCEMS, SCSFLCCapEMS):
        base, a3 = cls(cfg), cls(cfg, soc_b=True)
        assert len(a3.fis.rules) == 36
        for p in (500.0, 2500.0, 5000.0, -1000.0):          # SoC_B yüksekken S1/S2 ile aynı
            for s in (0.05, 0.5, 0.95):
                assert a3.decide(p, s, 0.9) == pytest.approx(base.decide(p, s))
    a3 = SCSFLCEMS(cfg, soc_b=True)
    assert a3.decide(500.0, 0.05, 0.1)[1] == pytest.approx(700.0, abs=1.0)   # High → Medium
    assert a3.decide(5000.0, 0.95, 0.1)[0] == pytest.approx(60.0, abs=0.1)   # VL kalır
    assert a3.decide(5000.0, 0.5, 0.1)[0] == pytest.approx(60.0, abs=0.1)    # L → VL
    a3c = SCSFLCCapEMS(cfg, soc_b=True)
    assert a3c.decide(5000.0, 0.05, 0.1)[0] == pytest.approx(3000.0, abs=1.0)  # Loose → Mid


def test_a2_a5(cfg):
    from hess.ablations import FLCRechargeEMS, S2CrispChargeEMS
    from hess.flc_ems import FLCEMS
    a2 = FLCRechargeEMS(cfg, START["S1"])
    f = FLCEMS(cfg)
    assert a2.sc_request(500.0, 0.9, 0.05) == pytest.approx(f.sc_request(500.0, 0.9, 0.05) - 1200.0, abs=1.0)
    assert a2.sc_request(-700.0, 0.9, 0.5) == pytest.approx(f.sc_request(-700.0, 0.9, 0.5))
    c0 = {"p_th": 3000.0, "p_lo": 1500.0, "p_ch": 1000.0, "target": 0.8}
    a5 = S2CrispChargeEMS(cfg, START["S2"], c0)
    assert a5.sc_request(500.0, 1, 0.5) == pytest.approx(-1000.0)
    assert a5.sc_request(500.0, 1, 0.9) == pytest.approx(0.0)
    assert a5.sc_request(5000.0, 1, 0.95) == pytest.approx(3000.0, abs=1.0)


def test_timed_forwards_flags(cfg):
    from hess.simulator import TimedEMS
    t = TimedEMS(SCSFLCEMS(cfg))
    assert t.sc_recharge and not t.battery_regen
    t.sc_request(500.0, 1, 0.5)
    assert t.n == 1 and t.us > 0
