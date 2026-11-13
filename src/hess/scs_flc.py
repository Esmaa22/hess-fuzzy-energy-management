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

S2 varyantı (SCSFLCCapEMS, Adım 7.2 bulgusundan sonra, D-23):
  Girdiler, P_ch kuralları ve 12 kurallık yapı aynı. Çıktı 1, C_SC yerine P_cap [W]:
  bataryanın bara gücü tavanı. SC yalnızca tavanın üstünü karşılar (tepe tıraşlama).
  P_cap yalnızca SoC_SC'ye bağlı: Low → Loose (yüksek tavan, SC korunur),
  Medium → Mid, High → Tight (düşük tavan, dolu SC daha çok çalışır).
    çekiş/duruş: istek = max(P_dem − P_cap, 0) − P_ch
    frenleme   : istek = P_dem  (enerjinin tamamı SC'ye)
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


# S2: P_cap terimi yalnızca SoC_SC sütununa bağlı
CAP_BY_SOC = {"Low": "Loose", "Medium": "Mid", "High": "Tight"}

# A3 ablasyonu (SoC_B girdisi, 3 × 12 = 36 kural). SoC_B Medium/High: kurallar aynı.
# SoC_B Low: bataryayı koru → P_ch bir seviye aşağı, SC payı bir seviye yukarı / tavan bir
# seviye sıkı. Z (düşük talepte SC kullanılmaz) ve Full (frenleme) değişmez.
PCH_DOWN = {"High": "Medium", "Medium": "Low", "Low": "Zero", "Zero": "Zero"}
CSC_UP = {"Z": "Z", "VS": "S", "S": "M", "M": "L", "L": "VL", "VL": "VL", "Full": "Full"}
CAP_TIGHTER = {"Loose": "Mid", "Mid": "Tight", "Tight": "Tight"}


def scs_params(cfg: dict, overrides: dict | None = None) -> dict:
    """SCS-FLC parametreleri: cfg['scs_flc'] + eksik MF'ler için cfg['flc'] + overrides."""
    p = copy.deepcopy(cfg["scs_flc"])
    p.setdefault("p_terms", copy.deepcopy(cfg["flc"]["p_terms"]))
    p.setdefault("soc_terms", copy.deepcopy(cfg["flc"]["soc_terms"]))
    p.setdefault("p_range", list(cfg["flc"]["p_range"]))
    p["soc_terms_ref"] = copy.deepcopy(cfg["flc"]["soc_terms"])   # A3: SoC_B MF'leri
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


def build_fis(params: dict, output: str = "share", soc_b: bool = False) -> MamdaniFIS:
    """output = 'share' → S1 (C_SC, P_ch);  'cap' → S2 (P_cap, P_ch).
    soc_b = True → A3 ablasyonu: SoC_B girdisi eklenir (36 kural)."""
    soc_sc = FuzzyVariable("soc_sc", {t: trapmf(*params["soc_terms"][t]) for t in SOC_TERMS},
                           clip=(0.0, 100.0))
    p_dem = FuzzyVariable("p_dem", {t: trapmf(*params["p_terms"][t]) for t in P_TERMS},
                          clip=tuple(params["p_range"]))
    n = params["universe_points"]
    p_ch = _output("p_ch", params["pch_levels"], params["pch_halfwidth"], n,
                   clip=(0.0, float("inf")))
    if output == "share":
        out1 = _output("c_sc", params["csc_levels"], params["csc_halfwidth"], n, clip=(0.0, 100.0))
        cons = lambda st, csc, low_b: {"c_sc": CSC_UP[csc] if low_b else csc}
    elif output == "cap":
        out1 = _output("p_cap", params["pcap_levels"], params["pcap_halfwidth"], n,
                       clip=(0.0, float("inf")))
        cons = lambda st, csc, low_b: {
            "p_cap": CAP_TIGHTER[CAP_BY_SOC[st]] if low_b else CAP_BY_SOC[st]}
    else:
        raise ValueError(output)
    inputs = [p_dem, soc_sc]
    b_terms = [None]
    if soc_b:
        bt = params.get("soc_b_terms", params["soc_terms_ref"])
        inputs.append(FuzzyVariable("soc_b", {t: trapmf(*bt[t]) for t in SOC_TERMS},
                                    clip=(0.0, 100.0)))
        b_terms = list(SOC_TERMS)
    rules = []
    for sb in b_terms:
        low_b = sb == "Low"
        for pt, row in RULES.items():
            for st, (csc, pch) in row.items():
                ante = {"p_dem": pt, "soc_sc": st, **({"soc_b": sb} if sb else {})}
                rules.append(Rule(ante, {**cons(st, csc, low_b),
                                         "p_ch": PCH_DOWN[pch] if low_b else pch}))
    return MamdaniFIS(inputs, [out1, p_ch], rules)


class SCSFLCEMS(EMS):
    """Önerilen yöntem S1. recharge=False → ablasyon A1 (aynı kurallar, P_ch = 0)."""

    battery_regen = False   # bütün HESS yöntemlerinde olduğu gibi (CP4 §5 adil karşılaştırma)
    OUTPUT = "share"
    BASE_NAME = "scs_flc"

    def __init__(self, cfg: dict, overrides: dict | None = None, recharge: bool = True,
                 soc_b: bool = False):
        self.params = scs_params(cfg, overrides)
        self.use_soc_b = soc_b
        self.fis = build_fis(self.params, self.OUTPUT, soc_b=soc_b)
        self.sc_recharge = recharge
        self.name = self.BASE_NAME + ("" if recharge else "_no_recharge") + ("_socb" if soc_b else "")

    def _eval(self, p_dem: float, soc_sc: float, soc_b: float) -> dict:
        x = {"p_dem": p_dem, "soc_sc": 100.0 * soc_sc}
        if self.use_soc_b:
            x["soc_b"] = 100.0 * soc_b
        return self.fis.evaluate(**x)

    def decide(self, p_dem: float, soc_sc: float, soc_b: float = 1.0) -> tuple[float, float]:
        """Ham çıktılar (C_SC [%], P_ch [W]). SoC'ler [0, 1] aralığında verilir."""
        out = self._eval(p_dem, soc_sc, soc_b)
        return out["c_sc"], out["p_ch"]

    def sc_request(self, p_dem, soc_b, soc_sc):
        c_sc, p_ch = self.decide(p_dem, soc_sc, soc_b)
        if p_dem < 0.0:
            return c_sc / 100.0 * p_dem
        req = c_sc / 100.0 * p_dem
        if self.sc_recharge:
            req -= p_ch
        return req


class SCSFLCCapEMS(SCSFLCEMS):
    """S2: bulanık, SoC_SC'ye uyarlanan batarya güç tavanı + bataryadan SC şarjı (D-23)."""

    OUTPUT = "cap"
    BASE_NAME = "scs_flc_cap"

    def decide(self, p_dem: float, soc_sc: float, soc_b: float = 1.0) -> tuple[float, float]:
        """Ham çıktılar (P_cap [W], P_ch [W])."""
        out = self._eval(p_dem, soc_sc, soc_b)
        return out["p_cap"], out["p_ch"]

    def sc_request(self, p_dem, soc_b, soc_sc):
        if p_dem < 0.0:
            return p_dem
        p_cap, p_ch = self.decide(p_dem, soc_sc, soc_b)
        req = max(p_dem - p_cap, 0.0)
        if self.sc_recharge:
            req -= p_ch
        return req
