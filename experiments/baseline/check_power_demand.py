"""Sürüş profilinden DC bara güç talebini hesaplar, özetler ve çizer.

Kullanım:  python experiments/baseline/check_power_demand.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hess import ROOT, load_config
from hess.battery import Battery
from hess.drive_cycle import load_profile
from hess.supercap import Supercap
from hess.vehicle import Vehicle, demand_from_profile


def main() -> None:
    cfg = load_config()
    dt = cfg["simulation"]["dt"]
    df = load_profile(ROOT / cfg["drive_cycle"]["file"])
    veh = Vehicle(cfg)
    d = demand_from_profile(veh, df)
    p = d["p_dem"]
    dist_km = d["v_mid"].sum() * dt / 1000

    e_trac = p[p > 0].sum() * dt / 3600
    e_regen = -p[p < 0].sum() * dt / 3600
    bat, sc = Battery(cfg), Supercap(cfg)
    summary = {
        "Tepe çekiş gücü [W]": p.max(),
        "Tepe rejenerasyon gücü [W]": p.min(),
        "Motor sınırına takılan adım sayısı": int(d["clipped"].sum()),
        "Çekiş enerjisi / çevrim [Wh]": e_trac,
        "Geri kazanılan enerji / çevrim [Wh]": e_regen,
        "Net DC enerji tüketimi [Wh/km]": (e_trac - e_regen) / dist_km,
        "Rejenerasyonsuz tüketim [Wh/km]": e_trac / dist_km,
        "Batarya nominal enerjisi [Wh]": bat.nominal_wh,
        "SC kullanılabilir enerjisi [Wh]": sc.usable_wh,
        "Kaba menzil, rejenerasyonsuz [km]": bat.nominal_wh / (e_trac / dist_km),
        "FLC evreni dışında kalan adım (P>5600 W)": int((p > 5600).sum()),
    }
    w = max(len(k) for k in summary)
    for k, v in summary.items():
        print(f"{k:<{w}}  {v:10.1f}")
    pd.Series(summary).to_csv(ROOT / "results" / "tables" / "power_demand_summary.csv",
                              header=["value"], float_format="%.2f")

    fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    t = df["time_s"]
    ax[0].plot(t, df["speed_kmh"], lw=1.1)
    ax[0].set_ylabel("Hız [km/h]")
    ax[0].grid(alpha=0.3)
    ax[1].plot(t, p / 1000, lw=1.0, color="tab:red")
    ax[1].axhline(veh.p_max / 1000, ls="--", lw=0.8, color="gray")
    ax[1].text(5, veh.p_max / 1000 + 0.15, "Motor sınırı 6.2 kW", fontsize=8, color="gray")
    ax[1].set_ylabel("$P_{dem}$ [kW]")
    ax[1].set_xlabel("Zaman [s]")
    ax[1].grid(alpha=0.3)
    ax[0].set_title("Sürüş profili ve DC bara güç talebi")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "power_demand.png", dpi=150)
    print("\nKaydedildi: results/figures/power_demand.png, results/tables/power_demand_summary.csv")


if __name__ == "__main__":
    main()
