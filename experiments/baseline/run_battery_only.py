"""Sadece-batarya senaryosu: uzun deşarj (%100 → %20), ilk akım/SoC/sıcaklık grafikleri.

İki varyant: makaledeki gibi rejenerasyonsuz (D-07) ve rejenerasyonlu (E6, adil baseline).
Kapsamlı ölçütler 4.6'da metrics.py ile hesaplanacak; burada yalnızca ön kontrol yapılır.

Kullanım:  python experiments/baseline/run_battery_only.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.simulator import BatteryOnlyEMS, Simulator

PAPER = {"Tepe akım [A]": 132.0, "Deşarj süresi [s]": 6540.0, "ΔT [°C]": 2.1,
         "ECR, makale tanımı [Wh/km]": 41.59, "Menzil, makale tanımı [km]": 88.95}


def summarize(cfg, sim, r) -> dict:
    L = r.log
    e_nom = sim.bat.nominal_wh
    e_term = L.p_b.sum() * sim.dt / 3600          # bataryanın terminalden verdiği net enerji
    ecr_paper = e_nom / r.distance_km              # makale: E_paket / %20'ye kadar mesafe
    return {
        "Tepe akım [A]": L.i_b.max(),
        "Deşarj süresi [s]": r.discharge_time_s,
        "ΔT [°C]": L.temp_b.max() - cfg["battery"]["thermal"]["t_amb_c"],
        "ECR, makale tanımı [Wh/km]": ecr_paper,
        "Menzil, makale tanımı [km]": e_nom / ecr_paper,
        "ECR, fiziksel [Wh/km]": e_term / r.distance_km,
        "Mesafe [km]": r.distance_km,
    }


def main() -> None:
    cfg = load_config()
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    runs = {ems.name: sim.run(ems, max_cycles=30) for ems in (BatteryOnlyEMS(False), BatteryOnlyEMS(True))}
    tbl = pd.DataFrame({name: summarize(cfg, sim, r) for name, r in runs.items()})
    tbl.insert(0, "Makale (sadece batarya)", pd.Series(PAPER))
    tbl["Fark % (rejsiz vs makale)"] = 100 * (tbl["battery_only"] / tbl["Makale (sadece batarya)"] - 1)
    pd.set_option("display.float_format", "{:.2f}".format)
    print(tbl.to_string())
    tbl.to_csv(ROOT / "results" / "tables" / "battery_only_check.csv", float_format="%.3f")

    # ---- grafikler -------------------------------------------------------
    fig, ax = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True)
    for name, r in runs.items():
        L = r.log
        lbl = "rejenerasyonsuz (makale)" if name == "battery_only" else "rejenerasyonlu (E6)"
        ax[0].plot(L.t, L.soc_b * 100, label=lbl)
        ax[1].plot(L.t, L.temp_b, label=lbl)
    ax[0].axhline(20, ls="--", c="gray", lw=0.8)
    ax[0].set_ylabel("SoC$_B$ [%]")
    ax[0].legend()
    ax[1].set_ylabel("Hücre sıcaklığı [°C]")
    L = runs["battery_only"].log
    ax[2].plot(L.t, L.i_b, lw=0.4, c="tab:red")
    ax[2].set_ylabel("$I_B$ [A]")
    ax[2].set_xlabel("Zaman [s]")
    for a in ax:
        a.grid(alpha=0.3)
    ax[0].set_title("Sadece batarya: uzun deşarj (%100 → %20)")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "battery_only_long.png", dpi=150)

    fig, ax = plt.subplots(2, 1, figsize=(10, 4.5), sharex=True)
    c1 = L[L.cycle == 0]
    ax[0].plot(c1.t, c1.p_dem / 1000, lw=0.8, label="$P_{dem}$")
    ax[0].plot(c1.t, c1.p_mech / 1000, lw=0.8, label="Mekanik fren")
    ax[0].set_ylabel("Güç [kW]")
    ax[0].legend(loc="upper right")
    ax[1].plot(c1.t, c1.i_b, lw=0.8, c="tab:red")
    ax[1].set_ylabel("$I_B$ [A]")
    ax[1].set_xlabel("Zaman [s]")
    for a in ax:
        a.grid(alpha=0.3)
    ax[0].set_title("Sadece batarya (rejenerasyonsuz): ilk çevrim")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "battery_only_cycle1.png", dpi=150)
    print("\nKaydedildi: results/figures/battery_only_long.png, battery_only_cycle1.png, "
          "results/tables/battery_only_check.csv")


if __name__ == "__main__":
    main()
