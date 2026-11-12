"""E4: DC/DC dönüştürücü verim taraması (plan §8, makale Şekil 14 karşılığı).

η_c = 0.91 … 1.00 aralığında, her değer için dört senaryo uzun deşarjda
(%100 → %20) koşturulur: sadece batarya, sadece batarya + rejenerasyon (E6), FLC, FRL.

Notlar:
  * η_c iki dönüştürücüye de aynı anda uygulanır (D-05, D-15).
  * FRL Q tabloları η_c = 0.96'da eğitildi. Taramada yeniden eğitilmez; politika
    sabit tutulup yalnızca tesis (plant) verimi değiştirilir. 5 seed ortalaması ± std.
  * Makale Şekil 14 yalnızca sıralamanın korunduğunu niteliksel olarak gösteriyor.
    Sayısal karşılaştırma bu yüzden sıralama ve eğim üzerinden yapılır.

Kullanım:  python experiments/baseline/run_e4_dcdc.py   (~1.5 dk)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.frl_ems import FRLEMS
from hess.metrics import compute
from hess.simulator import BatteryOnlyEMS, Simulator

TABLES = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"
ETAS = np.round(np.arange(0.91, 1.0001, 0.01), 2)
NAMES = {"battery_only": "Sadece batarya", "battery_only_regen": "Batarya + rej. (E6)",
         "flc": "FLC", "frl": "FRL"}
COLORS = {"battery_only": "tab:gray", "battery_only_regen": "tab:brown",
          "flc": "tab:blue", "frl": "tab:red"}
KEYS = ["t_dis", "range_paper", "ecr_paper", "ecr_phys", "peak_I", "rms_I", "dT"]


def ems_list(cfg):
    yield "battery_only", [BatteryOnlyEMS(False)]
    yield "battery_only_regen", [BatteryOnlyEMS(True)]
    yield "flc", [FLCEMS(cfg)]
    frls = []
    for sd in cfg["frl"]["seeds"]:
        e = FRLEMS(cfg, seed=sd)
        e.agent.Q = np.load(ROOT / "results" / "models" / f"frl_q_seed{sd}.npy")
        frls.append(e)
    yield "frl", frls


def sweep(cfg, sim):
    c = cfg["battery"]
    args = dict(i_rated=sim.bat.q_ah, e_nominal_wh=sim.bat.nominal_wh,
                t_amb=c["thermal"]["t_amb_c"], dt=sim.dt)
    rows = []
    for eta in ETAS:
        sim.eta = float(eta)
        for name, emss in ems_list(cfg):
            df = pd.DataFrame([compute(sim.run(e, max_cycles=30, log=True), **args) for e in emss])
            row = {"eta": eta, "senaryo": name}
            for k in KEYS:
                row[k] = df[k].mean()
                row[f"{k}_std"] = df[k].std() if len(df) > 1 else np.nan
            rows.append(row)
        print(f"η_c = {eta:.2f} tamam")
    sim.eta = cfg["converter"]["eta"]
    return pd.DataFrame(rows)


def ranking(df):
    """Her η_c için deşarj süresi ve menzile göre sıralama ve FRL−FLC farkının anlamlılığı."""
    out = []
    for eta, g in df.groupby("eta"):
        g = g.set_index("senaryo")
        r = {"eta": eta}
        for k in ("t_dis", "range_paper"):
            order = g.loc[["battery_only", "flc", "frl"], k].sort_values(ascending=False).index
            r[f"sıralama_{k}"] = " > ".join(NAMES[n] for n in order)
            r[f"makaleyle_aynı_{k}"] = list(order) == ["frl", "flc", "battery_only"]
            r[f"(FRL−FLC)/std_{k}"] = (g.loc["frl", k] - g.loc["flc", k]) / g.loc["frl", f"{k}_std"]
            r[f"FLC_vs_E6_%_{k}"] = 100 * (g.loc["flc", k] / g.loc["battery_only_regen", k] - 1)
            r[f"FLC_vs_bat_%_{k}"] = 100 * (g.loc["flc", k] / g.loc["battery_only", k] - 1)
        out.append(r)
    return pd.DataFrame(out)


def fig(df):
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for n in NAMES:
        g = df[df.senaryo == n]
        for a, k in zip(ax, ("range_paper", "ecr_paper", "t_dis")):
            a.plot(100 * g.eta, g[k], "o-", ms=3, c=COLORS[n], label=NAMES[n], lw=1.2)
            if n == "frl":
                a.fill_between(100 * g.eta, g[k] - g[f"{k}_std"], g[k] + g[f"{k}_std"],
                               color=COLORS[n], alpha=0.2, lw=0)
    ax[0].set_ylabel("Menzil, makale tanımı [km]")
    ax[1].set_ylabel("ECR, makale tanımı [Wh/km]")
    ax[2].set_ylabel("Deşarj süresi %100→%20 [s]")
    for a in ax:
        a.set_xlabel("DC/DC verimi η$_c$ [%]"); a.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    fig.suptitle("E4: DC/DC verim taraması (makale Şekil 14 karşılığı; FRL: 5 seed ± std)")
    fig.tight_layout(); fig.savefig(FIG / "E4_dcdc_sweep.png", dpi=150)


def main():
    cfg = load_config()
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    t0 = time.time()
    df = sweep(cfg, sim)
    rk = ranking(df)
    df.to_csv(TABLES / "E4_dcdc_sweep.csv", index=False, float_format="%.5g")
    rk.to_csv(TABLES / "E4_ranking.csv", index=False, float_format="%.3f")
    fig(df)
    pd.set_option("display.width", 250)
    piv = df.pivot(index="eta", columns="senaryo", values="range_paper")[list(NAMES)]
    print("\n=== Menzil (makale tanımı, km) ===")
    print(piv.to_string(float_format=lambda x: f"{x:.2f}"))
    print("\n=== Sıralama ===")
    print(rk.to_string(index=False, float_format=lambda x: f"{x:+.2f}"))
    print(f"\nToplam süre {time.time()-t0:.0f} s. results/tables/E4_*.csv, results/figures/E4_dcdc_sweep.png")


if __name__ == "__main__":
    main()
