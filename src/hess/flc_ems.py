"""Bulanık mantık tabanlı EMS (FLC) — referans makale [1] Tablo 4–5 (plan §4).

Girdiler : SoC_B [%], SoC_SC [%], P_dem [W]
Çıktılar : C_B [%] (batarya güç katsayısı), C_SC [%] (süperkapasitör güç katsayısı)
Kural tabanı: 3 × 3 × 4 = 36 kural, Tablo 5'ten birebir.

Çıktının güce çevrilmesi:
  D-08 çekişte  : c_sc = C_SC / (C_B + C_SC),   P_SC = c_sc · P_dem
  D-09 frenlemede: kabul = C_SC / 20,           P_SC = kabul · P_dem   (P_dem < 0)
"""

from __future__ import annotations

import numpy as np

from .fuzzy import FuzzyVariable, MamdaniFIS, Rule, trapmf, trimf
from .simulator import EMS

# Tablo 5: RULES[SoC_B][SoC_SC][P_dem] = (C_B, C_SC)
P_TERMS = ("Low", "Medium", "High", "Regeneration")
RULES = {
    "Low": {
        "Low":    ((100, 0), (100, 0), (75, 25), (0, 20)),
        "Medium": ((70, 30), (70, 30), (65, 35), (0, 20)),
        "High":   ((40, 60), (40, 60), (40, 60), (0, 0)),
    },
    "Medium": {
        "Low":    ((75, 25), (75, 25), (75, 25), (0, 20)),
        "Medium": ((55, 45), (55, 45), (55, 45), (0, 20)),
        "High":   ((40, 60), (40, 60), (40, 60), (0, 0)),
    },
    "High": {
        "Low":    ((100, 0), (100, 0), (75, 25), (0, 20)),
        "Medium": ((65, 35), (65, 35), (65, 35), (0, 20)),
        "High":   ((40, 60), (40, 60), (40, 60), (0, 0)),
    },
}


def build_fis(cfg: dict) -> MamdaniFIS:
    c = cfg["flc"]
    soc_terms = {t: trapmf(*v) for t, v in c["soc_terms"].items()}
    soc_b = FuzzyVariable("soc_b", dict(soc_terms), clip=(0.0, 100.0))
    soc_sc = FuzzyVariable("soc_sc", dict(soc_terms), clip=(0.0, 100.0))
    p_dem = FuzzyVariable("p_dem", {t: trapmf(*v) for t, v in c["p_terms"].items()},
                          clip=tuple(c["p_range"]))

    uni = np.linspace(*c["out_universe"], c["universe_points"])
    hw = c["out_halfwidth"]
    lvl = lambda L: {f"{v}": trimf(v - hw, v, v + hw) for v in L}
    c_b = FuzzyVariable("c_b", lvl(c["cb_levels"]), universe=uni, clip=(0.0, 100.0))
    c_sc = FuzzyVariable("c_sc", lvl(c["csc_levels"]), universe=uni, clip=(0.0, 100.0))

    rules = []
    for sb, row in RULES.items():
        for ss, cells in row.items():
            for pt, (cb, csc) in zip(P_TERMS, cells):
                rules.append(Rule({"soc_b": sb, "soc_sc": ss, "p_dem": pt},
                                  {"c_b": f"{cb}", "c_sc": f"{csc}"}))
    return MamdaniFIS([soc_b, soc_sc, p_dem], [c_b, c_sc], rules)


class FLCEMS(EMS):
    name = "flc"
    battery_regen = False   # makale: frenlemede batarya şarj edilmez (C_B = 0)

    def __init__(self, cfg: dict):
        self.fis = build_fis(cfg)
        self.regen_ref = cfg["flc"]["regen_csc_ref"]

    def decide(self, p_dem: float, soc_b: float, soc_sc: float) -> tuple[float, float]:
        """Ham FLC çıktısı (C_B, C_SC) [%]. SoC'ler [0, 1] aralığında verilir."""
        out = self.fis.evaluate(soc_b=100.0 * soc_b, soc_sc=100.0 * soc_sc, p_dem=p_dem)
        return out["c_b"], out["c_sc"]

    @staticmethod
    def sc_share(p_dem: float, c_b: float, c_sc: float, regen_ref: float) -> float:
        """(C_B, C_SC) -> P_dem'in süperkapasitöre giden oranı (D-08 / D-09)."""
        if p_dem >= 0.0:
            tot = c_b + c_sc
            return c_sc / tot if tot > 0 else 0.0
        return min(max(c_sc / regen_ref, 0.0), 1.0)

    def sc_request(self, p_dem, soc_b, soc_sc):
        if p_dem == 0.0:
            return 0.0
        c_b, c_sc = self.decide(p_dem, soc_b, soc_sc)
        return self.sc_share(p_dem, c_b, c_sc, self.regen_ref) * p_dem
