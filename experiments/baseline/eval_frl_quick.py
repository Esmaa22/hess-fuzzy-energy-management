"""Eğitilmiş FRL'nin (açgözlü, 5 seed) FLC ve sadece-batarya ile hızlı karşılaştırması.

İki senaryo: ilk çevrim (SC dolu, E2) ve uzun deşarj %100 -> %20 (E1).
Kapsamlı ölçütler 4.6'da metrics.py ile hesaplanacak.

Kullanım:  python experiments/baseline/eval_frl_quick.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pandas as pd

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.frl_ems import FRLEMS
from hess.simulator import BatteryOnlyEMS, Simulator


def stats(r) -> dict:
    L = r.log
    return {"peak_I": L.i_b.max(), "rms_I": float(np.sqrt((L.i_b ** 2).mean())),
            "dT": L.temp_b.max() - 20.0, "t_dis": r.discharge_time_s or np.nan,
            "dist": r.distance_km, "socsc_mean": L.soc_sc.mean(),
            "csc_share": L[L.p_dem > 0].p_sc_bus.sum() / L[L.p_dem > 0].p_dem.sum()}


def main():
    cfg = load_config()
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    out = {}
    for scen, kw in [("ilk_cevrim", dict(max_cycles=1, stop_at_soc_min=False)),
                     ("uzun_desarj", dict(max_cycles=30))]:
        res = {"battery_only": stats(sim.run(BatteryOnlyEMS(False), **kw)),
               "flc": stats(sim.run(FLCEMS(cfg), **kw))}
        frl = []
        for sd in cfg["frl"]["seeds"]:
            e = FRLEMS(cfg, seed=sd)
            e.agent.Q = np.load(ROOT / "results" / "models" / f"frl_q_seed{sd}.npy")
            frl.append(stats(sim.run(e, **kw)))
        F = pd.DataFrame(frl)
        res["frl_mean"] = F.mean().to_dict()
        res["frl_std"] = F.std().to_dict()
        out[scen] = pd.DataFrame(res)
    for scen, df in out.items():
        base = df["battery_only"]
        df["flc_%"] = 100 * (df["flc"] / base - 1)
        df["frl_%"] = 100 * (df["frl_mean"] / base - 1)
        print(f"\n=== {scen} ===")
        print(df.to_string(float_format=lambda x: f"{x:.3f}"))
        df.to_csv(ROOT / "results" / "tables" / f"frl_quick_{scen}.csv", float_format="%.4f")


if __name__ == "__main__":
    main()
