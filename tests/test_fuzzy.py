"""Mamdani motoru ve FLC testleri."""

import numpy as np
import pytest

from hess import load_config
from hess.flc_ems import P_TERMS, RULES, FLCEMS, build_fis
from hess.fuzzy import trapmf, trimf


# ---------------------------------------------------------------- üyelik fonksiyonları
def test_trapmf_values():
    mu = trapmf(0, 10, 20, 30)
    np.testing.assert_allclose(mu([-1, 0, 5, 10, 15, 20, 25, 30, 31]),
                               [0, 0, 0.5, 1, 1, 1, 0.5, 0, 0])


def test_shoulders():
    left, right = trapmf(0, 0, 20, 40), trapmf(60, 80, 100, 100)
    assert left(0) == 1.0 and right(100) == 1.0
    assert left(30) == pytest.approx(0.5) and right(70) == pytest.approx(0.5)


def test_trimf_peak():
    mu = trimf(35, 40, 45)
    assert mu(40) == 1.0 and mu(37.5) == pytest.approx(0.5) and mu(45) == 0.0


def test_invalid_trap():
    with pytest.raises(ValueError):
        trapmf(0, 20, 10, 30)


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def fis(cfg):
    return build_fis(cfg)


@pytest.mark.parametrize("var,lo,hi", [("soc_b", 0, 100), ("soc_sc", 0, 100), ("p_dem", -5100, 5600)])
def test_ruspini_partition(fis, var, lo, hi):
    """Her girdi noktasında üyelik dereceleri toplamı 1 (plan §4.1)."""
    v = fis._in[var]
    for x in np.linspace(lo, hi, 2001):
        if var == "p_dem" and -100 < x < 0:
            continue  # Regeneration'ın sıfıra iniş bölgesi: P_dem ≈ 0, karar etkisiz
        assert sum(v.fuzzify(x).values()) == pytest.approx(1.0), x


# ---------------------------------------------------------------- kural tabanı
SOC_PT = {"Low": 10.0, "Medium": 50.0, "High": 90.0}
P_PT = {"Low": 500.0, "Medium": 2500.0, "High": 5000.0, "Regeneration": -2000.0}


def test_rule_count(fis):
    assert len(fis.rules) == 36


@pytest.mark.parametrize("sb", list(RULES))
@pytest.mark.parametrize("ss", ["Low", "Medium", "High"])
def test_all_36_rules_exact(fis, sb, ss):
    """Tek bir kuralın tam ateşlendiği noktalarda çıktı Tablo 5'teki değere eşit olmalı (D-17)."""
    for pt, (cb, csc) in zip(P_TERMS, RULES[sb][ss]):
        out = fis.evaluate(soc_b=SOC_PT[sb], soc_sc=SOC_PT[ss], p_dem=P_PT[pt])
        fired = fis.explain(soc_b=SOC_PT[sb], soc_sc=SOC_PT[ss], p_dem=P_PT[pt])
        assert len(fired) == 1 and fired[0][0] == 1.0
        assert out["c_b"] == pytest.approx(cb, abs=1e-6), (sb, ss, pt)
        assert out["c_sc"] == pytest.approx(csc, abs=1e-6), (sb, ss, pt)


def test_interpolation_between_rules(fis):
    """İki kural eşit ateşlendiğinde çıktı iki değerin ortasında olmalı (simetrik üçgenler)."""
    # SoC_SC = 30: Low ve Medium 0.5'er; SoC_B = 50 (Medium), P = 500 (Low) -> C_SC: 25 ve 45
    out = fis.evaluate(soc_b=50, soc_sc=30, p_dem=500)
    assert out["c_sc"] == pytest.approx(35.0, abs=1e-6)
    assert out["c_b"] == pytest.approx(65.0, abs=1e-6)


def test_outputs_bounded_everywhere(fis):
    rng = np.random.default_rng(0)
    for _ in range(500):
        o = fis.evaluate(soc_b=rng.uniform(0, 100), soc_sc=rng.uniform(0, 100),
                         p_dem=rng.uniform(-6000, 7000))
        assert 0 <= o["c_b"] <= 100 and 0 <= o["c_sc"] <= 100


# ---------------------------------------------------------------- güce çevirme
def test_sc_request(cfg):
    ems = FLCEMS(cfg)
    # SoC_B Medium, SoC_SC High, çekiş -> 40/60 -> P_SC = 0.6 · P
    assert ems.sc_request(2500.0, 0.5, 0.9) == pytest.approx(0.6 * 2500.0, rel=1e-6)
    # Frenleme, SoC_SC Low -> C_SC = 20 -> tamamını kabul
    assert ems.sc_request(-2000.0, 0.5, 0.1) == pytest.approx(-2000.0, rel=1e-6)
    # Frenleme, SoC_SC High -> C_SC = 0 -> hiç kabul yok (mekanik fren)
    assert ems.sc_request(-2000.0, 0.5, 0.9) == pytest.approx(0.0, abs=1e-6)
