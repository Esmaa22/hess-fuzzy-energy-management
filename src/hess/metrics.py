"""Performans ölçütleri (plan §6, makale [1] Tablo 7–8).

Akım ölçütleri yalnızca deşarj yönünü değil |I_B|'yi kullanır (rejenerasyonlu varyantta
batarya şarj da edilir). Makaledeki "ortalama akım > RMS akım" tutarsızlığı (§8, madde 1)
nedeniyle iki ölçüt ayrı ayrı ve doğru tanımlarıyla raporlanır.

ECR ve menzil iki tanımla verilir:
  - makale tanımı : ECR = E_nominal / mesafe(%100 → %20),  menzil = E_nominal / ECR (= mesafe)
  - fiziksel      : ECR = bataryanın terminal enerjisi / mesafe,  menzil = 0.8·E_nominal / ECR
"""

from __future__ import annotations

import numpy as np

from .simulator import SimResult

PAPER = {  # [1] Tablo 7–8; sadece batarya / FLC / FRL
    "battery_only": {"peak_I": 132.0, "mean_I": 84.8, "rms_I": 40.40, "i2t": 1.14e7,
                     "severeness": 0.455, "dT": 2.1, "t_dis": 6540.0, "peak_Pb": 5930.0,
                     "peak_Psc": np.nan, "range_paper": 88.95, "ecr_paper": 41.59},
    "flc": {"peak_I": 102.0, "mean_I": 54.0, "rms_I": 39.69, "i2t": 1.03e7,
            "severeness": 0.427, "dT": 1.95, "t_dis": 6950.0, "peak_Pb": 4385.0,
            "peak_Psc": 1850.0, "range_paper": 94.34, "ecr_paper": 39.21},
    "frl": {"peak_I": 97.9, "mean_I": 52.4, "rms_I": 36.10, "i2t": 9.12e6,
            "severeness": 0.401, "dT": 1.9, "t_dis": 6990.0, "peak_Pb": 4535.0,
            "peak_Psc": 2050.0, "range_paper": 95.06, "ecr_paper": 38.93},
}

LABELS = {
    "peak_I": "Tepe I_B [A]", "mean_I": "Ortalama |I_B| [A]", "rms_I": "RMS I_B [A]",
    "i2t": "I²t [A²s]", "severeness": "Severeness index [-]", "dT": "Sıcaklık artışı [°C]",
    "t_dis": "Deşarj süresi %100→%20 [s]", "dist": "Mesafe [km]",
    "ecr_paper": "ECR, makale tanımı [Wh/km]", "range_paper": "Menzil, makale tanımı [km]",
    "ecr_phys": "ECR, fiziksel [Wh/km]", "range_phys": "Menzil, fiziksel (0.8·E) [km]",
    "peak_Pb": "Tepe P_B [W]", "peak_Psc": "Tepe P_SC [W]", "socsc_mean": "Ortalama SoC_SC [-]",
    "socsc_min": "En düşük SoC_SC [-]", "e_regen_sc": "SC'ye geri kazanılan [Wh]",
    "e_mech": "Mekanik frende kaybolan [Wh]", "sc_share": "Çekişte SC enerji payı [-]",
    "decision_us": "EMS karar süresi [µs/adım]",
}

# Daha küçük olanın daha iyi olduğu ölçütler (karşılaştırma tablolarında yön için)
LOWER_IS_BETTER = {"peak_I", "mean_I", "rms_I", "i2t", "severeness", "dT", "ecr_paper",
                   "ecr_phys", "peak_Pb", "e_mech", "decision_us"}


def compute(res: SimResult, i_rated: float, e_nominal_wh: float, t_amb: float,
            dt: float = 1.0, decision_us: float = np.nan) -> dict:
    L = res.log
    i = L["i_b"].to_numpy()
    ai = np.abs(i)
    dist = res.distance_km
    e_term_wh = L["p_b"].sum() * dt / 3600.0
    ecr_paper = e_nominal_wh / dist if res.discharge_time_s else np.nan
    ecr_phys = e_term_wh / dist
    trac = L["p_dem"] > 0
    return {
        "peak_I": float(i.max()),
        "mean_I": float(ai.mean()),
        "rms_I": float(np.sqrt(np.mean(i * i))),
        "i2t": float(np.sum(i * i) * dt),
        "severeness": float(np.mean(ai / i_rated)),   # A-16: I_rated = 1C
        "dT": float(L["temp_b"].max() - t_amb),
        "t_dis": float(res.discharge_time_s) if res.discharge_time_s else np.nan,
        "dist": dist,
        "ecr_paper": ecr_paper,
        "range_paper": e_nominal_wh / ecr_paper if res.discharge_time_s else np.nan,
        "ecr_phys": ecr_phys,
        "range_phys": 0.8 * e_nominal_wh / ecr_phys,
        "peak_Pb": float(L["p_b"].max()),
        "peak_Psc": float(L["p_sc"].max()),
        "socsc_mean": float(L["soc_sc"].mean()),
        "socsc_min": float(L["soc_sc"].min()),
        "e_regen_sc": float(-L["p_sc_bus"].clip(upper=0).sum() * dt / 3600.0),
        "e_mech": float(-L["p_mech"].sum() * dt / 3600.0),
        "sc_share": float(L.loc[trac, "p_sc_bus"].sum() / L.loc[trac, "p_dem"].sum()),
        "decision_us": decision_us,
    }
