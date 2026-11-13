"""Adım 7.2: C0 ve S1 için eşit bütçeli ayar (CP4 §5, adil karşılaştırma kuralları).

Her iki yöntem de 4 parametreyle tanımlanır ve aynı yöntemle aranır:
  * örnekleyici : Latin hiperküp (scipy.stats.qmc, seed 0), 23 nokta + başlangıç noktası = 24
  * çevrim      : yalnızca eğitim çevrimi (drive_cycle.seed = 7). Test çevrimleri kullanılmaz.
  * deney       : uzun deşarj (%100 / %100 → SoC_B = %20), X1 ile aynı koşul
  * amaç        : uygun (feasible) çözümler arasında en düşük tepe I_B (K1 ölçütü)
  * uygunluk    : deşarj süresi ≥ 0.99 · t(B1)  (K3)  ve  en düşük SoC_SC ≥ 0.10  (K1)
                  uygun değilse J = tepe I_B + 1000 (her uygun çözüm her uygunsuzdan iyi)

S1'in parametreleri ölçek çarpanlarıdır (1.0 = CP4 §3 taslağı):
  k_ch  : P_ch seviyeleri (Low/Medium/High) × k_ch
  k_csc : çekişteki C_SC seviyeleri (VS…VL) × k_csc   (Z = 0 ve Full = 100 sabit)
  k_p   : P_dem MF kırılma noktaları (Low/Medium/High, p_max hariç) × k_p
  k_soc : SoC_SC MF iç kırılma noktaları (0 ve 100 hariç) × k_soc
Çarpanlar Ruspini bölümlemesini ve terim sırasını korur. X4'te (±%10, ±%20) aynı
çarpanlar bozulur.

S2'nin parametreleri (D-23; P_cap aralığı C0'ın P_th aralığıyla aynı):
  c_cap : orta tavan (Mid) [W]
  d_cap : tavan yayılımı [W]. Tight = c − d, Loose = c + d. d = 0 → sabit tavan
  k_ch, k_soc : S1'deki gibi
"""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import yaml

from . import ROOT
from .crisp_ems import CrispEMS
from .metrics import compute
from .scs_flc import SCSFLCCapEMS, SCSFLCEMS, scs_params

TUNED_FILE = ROOT / "config" / "tuned.yaml"

# Arama aralıkları (alt, üst) ve başlangıç noktaları
SPACES = {
    "C0": {"p_th": (2000.0, 4500.0), "p_lo": (500.0, 2500.0),
           "p_ch": (300.0, 1800.0), "target": (0.50, 0.95)},
    "S1": {"k_ch": (0.4, 1.6), "k_csc": (0.5, 1.5), "k_p": (0.8, 1.3), "k_soc": (0.75, 1.2)},
    "S2": {"c_cap": (2000.0, 4500.0), "d_cap": (0.0, 1500.0),
           "k_ch": (0.4, 1.6), "k_soc": (0.75, 1.2)},
}
# C0: CP4 ön denemesinin en iyisi; S1: CP4 §3 taslağı
START = {
    "C0": {"p_th": 3000.0, "p_lo": 1500.0, "p_ch": 1000.0, "target": 0.8},
    "S1": {"k_ch": 1.0, "k_csc": 1.0, "k_p": 1.0, "k_soc": 1.0},
    "S2": {"c_cap": 3000.0, "d_cap": 1000.0, "k_ch": 1.0, "k_soc": 1.0},
}
BUDGET = 24
SOC_SC_MIN = 0.10
T_DIS_REL_MIN = 0.99
PENALTY = 1000.0


# --------------------------------------------------------------------------- S1 çarpanları
def s1_overrides(cfg: dict, k_ch=1.0, k_csc=1.0, k_p=1.0, k_soc=1.0) -> dict:
    """Ölçek çarpanlarını SCSFLCEMS(overrides=...) sözlüğüne çevirir."""
    base = scs_params(cfg)
    p_max = base["p_range"][1]
    ov = {
        "pch_levels": {t: v * k_ch for t, v in base["pch_levels"].items()},
        "csc_levels": {t: (v if t in ("Z", "Full") else min(v * k_csc, 100.0))
                       for t, v in base["csc_levels"].items()},
        "p_terms": {t: ([min(x * k_p, p_max) if x < p_max else x for x in pts]
                        if t != "Regeneration" else list(pts))
                    for t, pts in base["p_terms"].items()},
        "soc_terms": {t: [x if x in (0, 100) else min(x * k_soc, 100.0) for x in pts]
                      for t, pts in base["soc_terms"].items()},
    }
    return ov


def s2_overrides(cfg: dict, c_cap=3000.0, d_cap=1000.0, k_ch=1.0, k_soc=1.0) -> dict:
    ov = s1_overrides(cfg, k_ch=k_ch, k_soc=k_soc)
    del ov["csc_levels"], ov["p_terms"]
    ov["pcap_levels"] = {"Tight": max(c_cap - d_cap, 0.0), "Mid": c_cap, "Loose": c_cap + d_cap}
    return ov


def make_ems(method: str, cfg: dict, prm: dict, **kw):
    if method == "C0":
        return CrispEMS.from_params(prm, name=kw.get("name", "C0"))
    if method == "S1":
        e = SCSFLCEMS(cfg, overrides=s1_overrides(cfg, **prm), recharge=kw.get("recharge", True),
                      soc_b=kw.get("soc_b", False))
        e.name = kw.get("name", e.name)
        return e
    if method == "S2":
        e = SCSFLCCapEMS(cfg, overrides=s2_overrides(cfg, **prm), recharge=kw.get("recharge", True),
                         soc_b=kw.get("soc_b", False))
        e.name = kw.get("name", e.name)
        return e
    raise ValueError(method)


# --------------------------------------------------------------------------- değerlendirme
def metric_args(cfg: dict, sim) -> dict:
    return dict(i_rated=sim.bat.q_ah, e_nominal_wh=sim.bat.nominal_wh,
                t_amb=cfg["battery"]["thermal"]["t_amb_c"], dt=sim.dt)


def evaluate(sim, ems, margs: dict, t_ref: float) -> dict:
    """Uzun deşarj + amaç fonksiyonu. t_ref: B1'in deşarj süresi."""
    r = sim.run(ems, max_cycles=30)
    m = compute(r, **margs)
    out = {"peak_I": m["peak_I"], "p99_I": float(np.percentile(r.log.i_b, 99)),
           "rms_I": m["rms_I"], "dT": m["dT"], "t_dis": m["t_dis"],
           "t_rel_B1": m["t_dis"] / t_ref, "min_soc_sc": float(r.log.soc_sc.min())}
    out["feasible"] = bool(out["t_rel_B1"] >= T_DIS_REL_MIN and out["min_soc_sc"] >= SOC_SC_MIN)
    out["J"] = out["peak_I"] + (0.0 if out["feasible"] else PENALTY)
    return out


def design(method: str, n: int = BUDGET, seed: int = 0) -> list[dict]:
    """Başlangıç noktası + (n − 1) Latin hiperküp noktası. Aynı tohum iki yöntem için de."""
    from scipy.stats import qmc

    space = SPACES[method]
    u = qmc.LatinHypercube(d=len(space), seed=seed).random(n - 1)
    lo = np.array([a for a, _ in space.values()])
    hi = np.array([b for _, b in space.values()])
    pts = [dict(START[method])]
    pts += [dict(zip(space, map(float, row))) for row in lo + u * (hi - lo)]
    return pts


# --------------------------------------------------------------------------- ayarlı değerler
def save_tuned(best: dict, path: Path = TUNED_FILE, meta: dict | None = None) -> None:
    doc = {"_aciklama": "experiments/proposed/tune.py tarafından üretildi; elle düzenlemeyin.",
           **(meta or {}), **{k: {p: round(float(v), 4) for p, v in prm.items()}
                              for k, prm in best.items()}}
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False)


def load_tuned(path: Path = TUNED_FILE) -> dict:
    """{'C0': {...}, 'S1': {...}}. Dosya yoksa başlangıç noktaları döner."""
    if not Path(path).exists():
        return copy.deepcopy(START)
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return {k: doc[k] for k in START}
