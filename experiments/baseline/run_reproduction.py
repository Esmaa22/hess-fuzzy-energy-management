"""Yeniden üretim deneyleri E1–E3, E6 (plan §8): makale Tablo 7–8 ve Şekil 6–12 karşılığı.

Senaryolar:
  battery_only        : sadece batarya, rejenerasyonsuz (makale, D-07)
  battery_only_regen  : sadece batarya + rejenerasyon (E6, adil baseline)
  flc                 : 36 kurallı FLC
  frl                 : FLC + Q-learning (eğitilmiş Q tabloları, 5 seed, açgözlü)
Koşullar:
  long  : %100/%100'den SoC_B = %20'ye kadar (E1)
  cycle : tek çevrim, SC dolu (E2, E3)

Kullanım:  python experiments/baseline/run_reproduction.py
Önkoşul:   results/models/frl_q_seed*.npy  (train_frl.py ile üretilir)
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
from hess.metrics import LABELS, LOWER_IS_BETTER, PAPER, compute
from hess.simulator import BatteryOnlyEMS, Simulator, TimedEMS

TABLES = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"
NAMES = {"battery_only": "Sadece batarya", "battery_only_regen": "Batarya + rej. (E6)",
         "flc": "FLC", "frl": "FRL"}
COLORS = {"battery_only": "tab:gray", "battery_only_regen": "tab:brown",
          "flc": "tab:blue", "frl": "tab:red"}


# Zamanlama sarmalayıcısı src'ye taşındı (Adım 7.3); sc_recharge bayrağını da iletir.
Timed = TimedEMS


def make_ems(cfg):
    yield "battery_only", [BatteryOnlyEMS(False)]
    yield "battery_only_regen", [BatteryOnlyEMS(True)]
    yield "flc", [FLCEMS(cfg)]
    frls = []
    for sd in cfg["frl"]["seeds"]:
        e = FRLEMS(cfg, seed=sd)
        e.agent.Q = np.load(ROOT / "results" / "models" / f"frl_q_seed{sd}.npy")
        frls.append(e)
    yield "frl", frls


def run_all(cfg, sim):
    kw = {"long": dict(max_cycles=30), "cycle": dict(max_cycles=1, stop_at_soc_min=False)}
    c = cfg["battery"]
    args = dict(i_rated=sim.bat.q_ah, e_nominal_wh=sim.bat.nominal_wh,
                t_amb=c["thermal"]["t_amb_c"], dt=sim.dt)
    metrics, logs = {}, {}
    for cond, k in kw.items():
        for name, emss in make_ems(cfg):
            ms = []
            for j, e in enumerate(emss):
                te = Timed(e)
                r = sim.run(te, **k)
                ms.append(compute(r, decision_us=te.us, **args))
                if j == 0:
                    logs[(cond, name)] = r.log
            df = pd.DataFrame(ms)
            metrics[(cond, name)] = (df.mean(), df.std() if len(df) > 1 else df.mean() * np.nan)
    return metrics, logs


def table_e1(metrics, cond="long") -> pd.DataFrame:
    rows = []
    for key, lbl in LABELS.items():
        row = {"Ölçüt": lbl}
        for n in NAMES:
            m, s = metrics[(cond, n)]
            row[NAMES[n]] = m[key]
            if n == "frl":
                row["FRL std"] = s[key]
            if n in PAPER:
                row[f"Makale {NAMES[n]}"] = PAPER[n].get(key, np.nan)
        rows.append(row)
    return pd.DataFrame(rows).set_index("Ölçüt")


def table_relative(metrics) -> pd.DataFrame:
    """Sadece bataryaya göre % değişim: makale vs bizim (uzun deşarj ve ilk çevrim)."""
    keys = ["peak_I", "rms_I", "i2t", "severeness", "dT", "t_dis", "peak_Pb", "range_paper"]
    rows = []
    for k in keys:
        row = {"Ölçüt": LABELS[k]}
        for n in ("flc", "frl"):
            pb, pn = PAPER["battery_only"][k], PAPER[n][k]
            row[f"Makale {NAMES[n]} %"] = 100 * (pn / pb - 1)
            for cond in ("cycle", "long"):
                b = metrics[(cond, "battery_only")][0][k]
                v = metrics[(cond, n)][0][k]
                row[f"{NAMES[n]} %, {'ilk çevrim' if cond == 'cycle' else 'uzun deşarj'}"] = \
                    100 * (v / b - 1) if b and not np.isnan(b) else np.nan
            # E6: rejenerasyonlu batarya baseline'ına göre (uzun deşarj)
            b6 = metrics[("long", "battery_only_regen")][0][k]
            row[f"{NAMES[n]} % vs E6"] = 100 * (metrics[("long", n)][0][k] / b6 - 1)
        rows.append(row)
    return pd.DataFrame(rows).set_index("Ölçüt")


def ranking_check(metrics) -> pd.DataFrame:
    """Makaledeki sıralama (Sadece batarya kötü < FLC < FRL iyi) korunuyor mu?"""
    rows = []
    for k in ["peak_I", "rms_I", "i2t", "dT", "t_dis", "range_paper"]:
        for cond in ("cycle", "long"):
            v = {n: metrics[(cond, n)][0][k] for n in ("battery_only", "flc", "frl")}
            if any(np.isnan(x) for x in v.values()):
                continue
            sgn = 1 if k in LOWER_IS_BETTER else -1
            order = sorted(v, key=lambda n: sgn * v[n])           # en iyiden kötüye
            s_frl = metrics[(cond, "frl")][1][k]
            rows.append({"Ölçüt": LABELS[k], "Koşul": "ilk çevrim" if cond == "cycle" else "uzun deşarj",
                         "Sıralama (iyi→kötü)": " > ".join(NAMES[n] for n in order),
                         "Makaleyle aynı": order == ["frl", "flc", "battery_only"],
                         "|FRL−FLC| / std(FRL)": abs(v["frl"] - v["flc"]) / s_frl if s_frl else np.nan})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- grafikler
def fig_e1(logs):
    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for n in NAMES:
        L = logs[("long", n)]
        ax[0].plot(L.t, 100 * L.soc_b, c=COLORS[n], label=NAMES[n], lw=1.2)
        ax[1].plot(L.t, L.temp_b, c=COLORS[n], lw=1.0)
        if n in ("flc", "frl"):
            ax[2].plot(L.t, 100 * L.soc_sc, c=COLORS[n], lw=0.8, label=NAMES[n])
    ax[0].axhline(20, ls="--", c="k", lw=0.7)
    ax[0].set_ylabel("SoC$_B$ [%]"); ax[0].legend(ncol=4, fontsize=8)
    ax[1].set_ylabel("Hücre sıcaklığı [°C]")
    ax[2].set_ylabel("SoC$_{SC}$ [%]"); ax[2].legend(fontsize=8); ax[2].set_xlabel("Zaman [s]")
    for a in ax:
        a.grid(alpha=0.3)
    ax[0].set_title("E1: uzun deşarj (%100 → %20), FRL: seed 0")
    fig.tight_layout(); fig.savefig(FIG / "E1_long_discharge.png", dpi=150)


def fig_e1_current(logs):
    """Akım dağılımı ve ilk/son çevrimden yakın görünüm (makale Şekil 6 karşılığı)."""
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
    for n in ("battery_only", "flc", "frl"):
        L = logs[("long", n)]
        ax[0].hist(L.i_b[L.i_b > 1], bins=60, histtype="step", color=COLORS[n], label=NAMES[n], lw=1.2)
        c0 = L[(L.t >= 100) & (L.t < 250)]
        ax[1].plot(c0.t, c0.i_b, c=COLORS[n], lw=1.0, label=NAMES[n])
        last = L[L.cycle == L.cycle.max() - 1]
        w = last[(last.t >= last.t.min() + 100) & (last.t < last.t.min() + 250)]
        ax[2].plot(w.t - w.t.min() + 100, w.i_b, c=COLORS[n], lw=1.0)
    ax[0].set_yscale("log"); ax[0].set_xlabel("$I_B$ [A]"); ax[0].set_ylabel("Adım sayısı")
    ax[0].legend(fontsize=8); ax[0].set_title("Akım dağılımı (uzun deşarj)", fontsize=10)
    ax[1].set_title("İlk çevrim, 100–250 s (SC dolu)", fontsize=10)
    ax[2].set_title("Sondan bir önceki çevrim, aynı pencere (SC boş)", fontsize=10)
    for a in ax[1:]:
        a.set_xlabel("Çevrim içi zaman [s]"); a.set_ylabel("$I_B$ [A]")
    for a in ax:
        a.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "E1_current.png", dpi=150)


def fig_e2(logs):
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for a, n in zip(ax, ("flc", "frl")):
        L = logs[("cycle", n)]
        a.plot(L.t, L.p_dem / 1000, c="k", lw=0.6, alpha=0.5, label="$P_{dem}$")
        a.plot(L.t, L.p_b_bus / 1000, c="tab:green", lw=0.8, label="$P_B$ (bara)")
        a.plot(L.t, L.p_sc_bus / 1000, c="tab:purple", lw=0.8, label="$P_{SC}$ (bara)")
        a.set_ylabel("Güç [kW]"); a.set_title(f"{NAMES[n]}", fontsize=10)
        a.legend(ncol=3, fontsize=8, loc="upper right"); a.grid(alpha=0.3)
    ax[1].set_xlabel("Zaman [s]")
    fig.suptitle("E2: ilk çevrimde güç paylaşımı (makale Şekil 9–11 karşılığı)")
    fig.tight_layout(); fig.savefig(FIG / "E2_power_split.png", dpi=150)


def fig_e3(cfg, sim):
    """SoC_SC seyri: FLC ve FRL'nin 5 seed'i, ilk 3 çevrim."""
    fig, ax = plt.subplots(figsize=(10, 3.6))
    L = sim.run(FLCEMS(cfg), max_cycles=3, stop_at_soc_min=False).log
    ax.plot(L.t, 100 * L.soc_sc, c=COLORS["flc"], lw=1.4, label="FLC")
    for i, sd in enumerate(cfg["frl"]["seeds"]):
        e = FRLEMS(cfg, seed=sd)
        e.agent.Q = np.load(ROOT / "results" / "models" / f"frl_q_seed{sd}.npy")
        L = sim.run(e, max_cycles=3, stop_at_soc_min=False).log
        ax.plot(L.t, 100 * L.soc_sc, c=COLORS["frl"], lw=0.8, alpha=0.7,
                label="FRL (5 seed)" if i == 0 else None)
    for k in (1, 2):
        ax.axvline(900 * k, c="k", ls=":", lw=0.6)
    ax.axhspan(0, 30, color="tab:orange", alpha=0.08, label="SoC$_{SC}$ ≈ Low")
    ax.set_xlabel("Zaman [s]"); ax.set_ylabel("SoC$_{SC}$ [%]"); ax.legend(fontsize=8)
    ax.grid(alpha=0.3); ax.set_title("E3: süperkapasitör SoC seyri (makale Şekil 12 karşılığı)")
    fig.tight_layout(); fig.savefig(FIG / "E3_soc_sc.png", dpi=150)


def fig_summary(rel):
    cols = [("Makale FLC %", "Makale FLC"), ("FLC %, ilk çevrim", "FLC ilk çevrim"),
            ("FLC %, uzun deşarj", "FLC uzun"), ("Makale FRL %", "Makale FRL"),
            ("FRL %, ilk çevrim", "FRL ilk çevrim"), ("FRL %, uzun deşarj", "FRL uzun")]
    keys = [LABELS[k] for k in ("peak_I", "rms_I", "dT", "t_dis")]
    sub = rel.loc[keys, [c for c, _ in cols]]
    fig, ax = plt.subplots(figsize=(11, 4))
    x = np.arange(len(keys))
    w = 0.13
    shades = ["#9ecae1", "#3182bd", "#08519c", "#fcae91", "#de2d26", "#a50f15"]
    for i, ((c, lbl), col) in enumerate(zip(cols, shades)):
        ax.bar(x + (i - 2.5) * w, sub[c], w, label=lbl, color=col)
    ax.axhline(0, c="k", lw=0.7)
    ax.set_xticks(x, ["Tepe akım", "RMS akım", "Sıcaklık artışı", "Deşarj süresi"])
    ax.set_ylabel("Sadece bataryaya göre değişim [%]")
    ax.legend(ncol=2, fontsize=8); ax.grid(axis="y", alpha=0.3)
    ax.set_title("Makale ve yeniden üretim: göreli değişimler")
    fig.tight_layout(); fig.savefig(FIG / "reproduction_summary.png", dpi=150)


def main():
    cfg = load_config()
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    t0 = time.time()
    metrics, logs = run_all(cfg, sim)
    pd.set_option("display.width", 250)
    fmt = lambda x: f"{x:.4g}"

    e1 = table_e1(metrics, "long")
    e2 = table_e1(metrics, "cycle").drop(columns=[c for c in table_e1(metrics, "cycle") if "Makale" in c])
    rel = table_relative(metrics)
    rank = ranking_check(metrics)
    e1.to_csv(TABLES / "E1_long_discharge.csv", float_format="%.5g")
    e2.to_csv(TABLES / "E2_first_cycle.csv", float_format="%.5g")
    rel.to_csv(TABLES / "reproduction_relative.csv", float_format="%.3f")
    rank.to_csv(TABLES / "reproduction_ranking.csv", index=False, float_format="%.2f")

    print("=== E1: uzun deşarj (FRL: 5 seed ortalama, std ayrı sütunda) ===")
    print(e1.to_string(float_format=fmt))
    print("\n=== Sadece bataryaya göre % değişim ===")
    print(rel.to_string(float_format=lambda x: f"{x:+.1f}"))
    print("\n=== Sıralama kontrolü ===")
    print(rank.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    fig_e1(logs); fig_e1_current(logs); fig_e2(logs); fig_e3(cfg, sim); fig_summary(rel)
    print(f"\nToplam süre {time.time()-t0:.0f} s. Tablolar: results/tables/E1_*, E2_*, reproduction_*; "
          "grafikler: results/figures/E1_*, E2_*, E3_*, reproduction_summary.png")


if __name__ == "__main__":
    main()
