"""SCS-FLC: süperkapasitör enerjisini koruyan bulanık EMS (önerilen yöntem S1, CP4 §3).

Referans FLC'den (flc_ems.py, Tablo 5) farkları:
  * Girdiler : P_dem [W], SoC_SC [%]. SoC_B kaldırıldı (gerekliliği A3 ablasyonunda sınanır).
               Üyelik fonksiyonları referans FLC ile aynı (yamuk, Ruspini), config'de
               geçersiz kılınabilir.
  * Çıktı 1  : C_SC [%]. P_dem'in doğrudan SC'ye giden yüzdesi (D-21). Kurallar yeni:
               SC yalnızca talep yüksekse ve SC doluysa devreye giriyor (tepe tıraşlama).
  * Çıktı 2  : P_ch [W], yeni. Talep düşükken SC boşalmışsa bataryadan SC'ye şarj (D-22).
  * 4 × 3 = 12 kural, Mamdani (min-max, centroid). Motor: fuzzy.py.

Kural tabanı (C_SC / P_ch):

    P_dem \\ SoC_SC |  Low         |  Medium      |  High
    ---------------+--------------+--------------+------------
    Low            |  Z  / High   |  Z  / Medium |  Z  / Zero
    Medium         |  Z  / Low    |  VS / Zero   |  M  / Zero
    High           |  S  / Zero   |  L  / Zero   |  VL / Zero
    Regeneration   |  Full / Zero |  Full / Zero |  Full / Zero

Seviyeler (config, varsayılan): Z=0, VS=10, S=20, M=25, L=45, VL=60, Full=100 [%];
P_ch: Zero=0, Low=300, Medium=700, High=1200 [W].

Güce çevirme (bara tarafı):
  çekiş/duruş (P_dem ≥ 0): istek = C_SC/100 · P_dem − P_ch
                            (negatifse simülatör bataryadan SC'yi şarj eder, D-20)
  frenleme   (P_dem < 0) : istek = C_SC/100 · P_dem  (Full → frenleme gücünün tamamı SC'ye)
"""

from __future__ import annotations

import copy

import numpy as np

from .fuzzy import FuzzyVariable, MamdaniFIS, Rule, trapmf, trimf
from .simulator import EMS

P_TERMS = ("Low", "Medium", "High", "Regeneration")
SOC_TERMS = ("Low", "Medium", "High")

# RULES[P_dem][SoC_SC] = (C_SC terimi, P_ch terimi)
RULES = {
    "Low":          {"Low": ("Z", "High"),  "Medium": ("Z", "Medium"), "High": ("Z", "Zero")},
    "Medium":       {"Low": ("Z", "Low"),   "Medium": ("VS", "Zero"),  "High": ("M", "Zero")},
    "High":         {"Low": ("S", "Zero"),  "Medium": ("L", "Zero"),   "High": ("VL", "Zero")},
    "Regeneration": {"Low": ("Full", "Zero"), "Medium": ("Full", "Zero"), "High": ("Full", "Zero")},
}


def scs_params(cfg: dict, overrides: dict | None = None) -> dict:
    """SCS-FLC parametreleri: cfg['scs_flc'] + eksik MF'ler için cfg['flc'] + overrides."""
    p = copy.deepcopy(cfg["scs_flc"])
    p.setdefault("p_terms", copy.deepcopy(cfg["flc"]["p_terms"]))
    p.setdefault("soc_terms", copy.deepcopy(cfg["flc"]["soc_terms"]))
    p.setdefault("p_range", list(cfg["flc"]["p_range"]))
    for k, v in (overrides or {}).items():
        if isinstance(v, dict) and isinstance(p.get(k), dict):
            p[k] = {**p[k], **copy.deepcopy(v)}
        else:
            p[k] = copy.deepcopy(v)
    return p


def _output(name: str, levels: dict, hw: float, n: int, clip=None) -> FuzzyVariable:
    vals = list(levels.values())
    uni = np.linspace(min(vals) - hw, max(vals) + hw, n)   # D-17: uçlarda yanlılık yok
    terms = {t: trimf(v - hw, v, v + hw) for t, v in levels.items()}
    return FuzzyVariable(name, terms, universe=uni, clip=clip)


def build_fis(params: dict) -> MamdaniFIS:
    soc_sc = FuzzyVariable("soc_sc", {t: trapmf(*params["soc_terms"][t]) for t in SOC_TERMS},
                           clip=(0.0, 100.0))
    p_dem = FuzzyVariable("p_dem", {t: trapmf(*params["p_terms"][t]) for t in P_TERMS},
                          clip=tuple(params["p_range"]))
    n = params["universe_points"]
    c_sc = _output("c_sc", params["csc_levels"], params["csc_halfwidth"], n, clip=(0.0, 100.0))
    p_ch = _output("p_ch", params["pch_levels"], params["pch_halfwidth"], n,
                   clip=(0.0, float("inf")))
    rules = [Rule({"p_dem": pt, "soc_sc": st}, {"c_sc": csc, "p_ch": pch})
             for pt, row in RULES.items() for st, (csc, pch) in row.items()]
    return MamdaniFIS([p_dem, soc_sc], [c_sc, p_ch], rules)


class SCSFLCEMS(EMS):
    """Önerilen yöntem S1. recharge=False → ablasyon A1 (aynı kurallar, P_ch = 0)."""

    battery_regen = False   # bütün HESS yöntemlerinde olduğu gibi (CP4 §5 adil karşılaştırma)

    def __init__(self, cfg: dict, overrides: dict | None = None, recharge: bool = True):
        self.params = scs_params(cfg, overrides)
        self.fis = build_fis(self.params)
        self.sc_recharge = recharge
        self.name = "scs_flc" if recharge else "scs_flc_no_recharge"

    def decide(self, p_dem: float, soc_sc: float) -> tuple[float, float]:
        """Ham çıktılar (C_SC [%], P_ch [W]). soc_sc [0, 1] aralığında verilir."""
        out = self.fis.evaluate(p_dem=p_dem, soc_sc=100.0 * soc_sc)
        return out["c_sc"], out["p_ch"]

    def sc_request(self, p_dem, soc_b, soc_sc):
        c_sc, p_ch = self.decide(p_dem, soc_sc)
        if p_dem < 0.0:
            return c_sc / 100.0 * p_dem
        req = c_sc / 100.0 * p_dem
        if self.sc_recharge:
            req -= p_ch
        return req
