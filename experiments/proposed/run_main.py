"""Adım 7.3: X1 (ana karşılaştırma) ve X2 (ablasyonlar), eğitim çevrimi.

X1  Yöntemler: B0, B1, F0, R0 (5 seed ort. ± std), C0, S1, S2 (ayarlı, config/tuned.yaml)
    Koşullar : uzun deşarj (%100/%100 → SoC_B = %20; K1–K3 bu koşulda) ve ilk çevrim (SC dolu)
X2  S1 ailesi: S1, A1 (P_ch = 0), A2 (Tablo 5 + P_ch), A3 (+SoC_B, 36 kural)
    S2 ailesi: S2, A1 (P_ch = 0), A3 (+SoC_B), A4 (d_cap = 0), A5 (crisp şarj kuralı)
    Koşul    : uzun deşarj. Ablasyonlar yeniden ayarlanmaz.

Not: Bu çevrim ayarda kullanılan çevrimdir; genelleme X3'te (30 test çevrimi) sınanır.

Kullanım:  python experiments/proposed/run_main.py      (~1 dk)
Önkoşul:   config/tuned.yaml (tune.py), results/models/frl_q_seed*.npy (train_frl.py)
Çıktılar:  results/tables/X1_long_discharge.csv, X1_first_cycle.csv, X1_criteria.csv,
           X2_ablation.csv;  results/figures/X1_summary.png, X1_soc_current.png, X2_ablation.png
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
from hess.ablations import FLCRechargeEMS, S2CrispChargeEMS
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.frl_ems import FRLEMS
from hess.metrics import compute
from hess.simulator import BatteryOnlyEMS, Simulator, TimedEMS
from hess.tuning import load_tuned, make_ems, metric_args

TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"

COLS = {  # ölçüt anahtarı -> tablo başlığı
    "peak_I": "Tepe I_B [A]", "p99_I": "%99 I_B [A]", "rms_I": "RMS I_B [A]",
    "i2t": "I²t [A²s]", "dT": "ΔT [°C]", "t_dis": "Deşarj süresi [s]",
    "t_vs_B0": "Süre, B0'a göre [%]", "t_vs_B1": "Süre, B1'e göre [%]",
    "socsc_min": "En düşük SoC_SC", "socsc_mean": "Ort. SoC_SC",
    "e_mech": "Mek. frende kayıp [Wh]", "decision_us": "Karar süresi [µs/adım]",
}

# Dataviz referans paleti (kategorik, sabit sıra) + baseline'lar için nötr gri
C_BASE, C_C0 = "#a3a29b", "#5f5e58"
C_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, MUTED = "#2b2b29", "#6b6a64"


def frl_agents(cfg):
    out = []
    for sd in cfg["frl"]["seeds"]:
        e = FRLEMS(cfg, seed=sd)
        e.agent.Q = np.load(ROOT / "results" / "models" / f"frl_q_seed{sd}.npy")
        out.append(e)
    return out


def x1_methods(cfg, tuned):
    yield "B0", "Sadece batarya", [BatteryOnlyEMS(False)]
    yield "B1", "Batarya + rej. (E6)", [BatteryOnlyEMS(True)]
    yield "F0", "FLC (Tablo 5)", [FLCEMS(cfg)]
    yield "R0", "FRL (5 seed)", frl_agents(cfg)
    yield "C0", "Crisp (ayarlı)", [make_ems("C0", cfg, tuned["C0"])]
    yield "S1", "SCS-FLC pay (ayarlı)", [make_ems("S1", cfg, tuned["S1"])]
    yield "S2", "SCS-FLC tavan (ayarlı)", [make_ems("S2", cfg, tuned["S2"])]


def x2_methods(cfg, tuned):
    s1, s2, c0 = tuned["S1"], tuned["S2"], tuned["C0"]
    yield "S1", "tam yöntem", make_ems("S1", cfg, s1)
    yield "S1-A1", "S1, P_ch = 0", make_ems("S1", cfg, s1, recharge=False)
    yield "S1-A2", "Tablo 5 + P_ch", FLCRechargeEMS(cfg, s1)
    yield "S1-A3", "S1 + SoC_B (36 kural)", make_ems("S1", cfg, s1, soc_b=True)
    yield "S2", "tam yöntem", make_ems("S2", cfg, s2)
    yield "S2-A1", "S2, P_ch = 0", make_ems("S2", cfg, s2, recharge=False)
    yield "S2-A3", "S2 + SoC_B (36 kural)", make_ems("S2", cfg, s2, soc_b=True)
    yield "S2-A4", "S2, sabit tavan (d_cap = 0)", make_ems("S2", cfg, {**s2, "d_cap": 0.0})
    yield "S2-A5", "S2 tavan + crisp şarj (C0)", S2CrispChargeEMS(cfg, s2, c0)


def run_one(sim, ems, margs, **kw):
    te = TimedEMS(ems)
    r = sim.run(te, **kw)
    m = compute(r, decision_us=te.us, **margs)
    m["p99_I"] = float(np.percentile(r.log.i_b, 99))
    return m, r.log


def add_relative(df, t_b0, t_b1):
    df["t_vs_B0"] = 100 * (df["t_dis"] / t_b0 - 1)
    df["t_vs_B1"] = 100 * (df["t_dis"] / t_b1 - 1)
    return df


def x1(cfg, sim, margs, tuned):
    conds = {"long": dict(max_cycles=30), "cycle": dict(max_cycles=1, stop_at_soc_min=False)}
    tables, logs = {}, {}
    for cond, kw in conds.items():
        rows = []
        for code, label, emss in x1_methods(cfg, tuned):
            ms = []
            for j, e in enumerate(emss):
                m, log = run_one(sim, e, margs, **kw)
                ms.append(m)
                if j == 0 and cond == "long":
                    logs[code] = log
            d = pd.DataFrame(ms)
            row = {"Kod": code, "Yöntem": label, **d.mean().to_dict()}
            if len(d) > 1:
                row.update({f"{k}_std": v for k, v in d.std().items()})
            rows.append(row)
        df = pd.DataFrame(rows).set_index("Kod")
        if cond == "long":
            df = add_relative(df, df.loc["B0", "t_dis"], df.loc["B1", "t_dis"])
        tables[cond] = df
    return tables, logs


def criteria(t):
    """K1–K3 (CP4 §6), uzun deşarj, eğitim çevrimi. K4 → X3/X4, K5 → X2 + X3."""
    f0, r0, b1 = t.loc["F0"], t.loc["R0"], t.loc["B1"]
    rows = []
    for c in ("S1", "S2", "C0"):
        m = t.loc[c]
        red = 100 * (1 - m.peak_I / f0.peak_I)
        rows += [
            {"Yöntem": c, "Ölçüt": "K1", "Koşul": "Tepe I_B, F0'a göre ≥ %30 düşük",
             "Değer": f"−%{red:.1f}", "Sağlandı": red >= 30},
            {"Yöntem": c, "Ölçüt": "K1", "Koşul": "En düşük SoC_SC ≥ 0.10",
             "Değer": f"{m.socsc_min:.3f}", "Sağlandı": m.socsc_min >= 0.10},
            {"Yöntem": c, "Ölçüt": "K2", "Koşul": "RMS, I²t, ΔT hem F0'dan hem R0'dan düşük",
             "Değer": f"RMS {m.rms_I:.2f}, I²t {m.i2t:.3g}, ΔT {m.dT:.2f}",
             "Sağlandı": all(m[k] < f0[k] and m[k] < r0[k] for k in ("rms_I", "i2t", "dT"))},
            {"Yöntem": c, "Ölçüt": "K3", "Koşul": "Deşarj süresi B1'e göre ≥ −%1",
             "Değer": f"{m.t_vs_B1:+.2f}% (F0'a göre {100 * (m.t_dis / f0.t_dis - 1):+.2f}%)",
             "Sağlandı": m.t_vs_B1 >= -1.0},
        ]
    return pd.DataFrame(rows)


def x2(cfg, sim, margs, tuned, t_b0, t_b1):
    rows = []
    for code, label, e in x2_methods(cfg, tuned):
        m, _ = run_one(sim, e, margs, max_cycles=30)
        rows.append({"Kod": code, "Varyant": label, **m})
    return add_relative(pd.DataFrame(rows).set_index("Kod"), t_b0, t_b1)


# --------------------------------------------------------------------------- grafikler
def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.xaxis.grid(True, color="#e4e3dd", lw=0.6)
    ax.set_axisbelow(True)


def _hbars(ax, labels, vals, colors, fmt, title, errs=None):
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, height=0.62, color=colors, edgecolor="white", linewidth=1)
    errs = np.zeros(len(vals)) if errs is None else np.asarray(errs, dtype=float)
    for yi, v, e in zip(y, vals, errs):
        if e > 0:
            ax.errorbar(v, yi, xerr=e, color=INK, lw=1, capsize=2.5)
    ax.set_yticks(y, labels, fontsize=8, color=INK)
    ax.set_title(title, fontsize=9.5, color=INK, loc="left")
    lo, hi = min(0, np.nanmin(vals)), np.nanmax(vals)
    span = hi - lo
    for yi, v, e in zip(y, vals, errs):
        off = 0.015 * span + (e if v >= 0 else -e)
        ax.text(v + (off if v >= 0 else -off), yi, fmt.format(v), va="center",
                ha="left" if v >= 0 else "right", fontsize=7.5, color=INK)
    ax.set_xlim(lo - (0.15 * span if lo < 0 else 0), hi + 0.2 * span + np.nanmax(errs))
    _style(ax)


def _colors(codes):
    return [C_SERIES[0] if c in ("S1", "S2") else C_C0 if c == "C0" else C_BASE for c in codes]


def fig_x1_summary(t):
    codes = list(t.index)
    labels = [f"{c}  {t.loc[c, 'Yöntem']}" for c in codes]
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.6), sharey=True)
    specs = [("peak_I", "Tepe I_B [A]", "{:.1f}"), ("rms_I", "RMS I_B [A]", "{:.1f}"),
             ("dT", "Sıcaklık artışı ΔT [°C]", "{:.2f}"),
             ("t_vs_B1", "Deşarj süresi, B1'e göre [%]", "{:+.1f}")]
    for ax, (k, title, fmt) in zip(axs, specs):
        err = [t.loc[c].get(f"{k}_std", np.nan) if c == "R0" else 0 for c in codes]
        if k == "t_vs_B1":
            err = [100 * t.loc[c].get("t_dis_std", 0) / t.loc["B1", "t_dis"] if c == "R0" else 0
                   for c in codes]
        _hbars(ax, labels, t[k].to_numpy(), _colors(codes), fmt, title, errs=np.nan_to_num(err))
    fig.suptitle("X1 · Uzun deşarj (%100 → %20), eğitim çevrimi · mavi: önerilen, koyu gri: crisp "
                 "kontrol, açık gri: baseline · R0 hata çubuğu: 5 seed std",
                 fontsize=9, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG / "X1_summary.png", dpi=150)
    plt.close(fig)


def fig_x1_soc_current(logs):
    order = [("F0", "F0 FLC"), ("C0", "C0 crisp"), ("S1", "S1 SCS-FLC pay"), ("S2", "S2 SCS-FLC tavan")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 3.9), gridspec_kw=dict(width_ratios=[1.6, 1]))
    for (c, lbl), col in zip(order, C_SERIES):
        L = logs[c]
        a1.plot(L.t / 3600, L.soc_sc.rolling(60, min_periods=1).mean(), color=col, lw=1.6, label=lbl)
        top = np.sort(L.i_b.to_numpy())[::-1][:400]
        a2.plot(np.arange(len(top)), top, color=col, lw=1.8, label=lbl)
    b1 = np.sort(logs["B1"].i_b.to_numpy())[::-1][:400]
    a2.plot(np.arange(len(b1)), b1, color=C_BASE, lw=1.6, ls="--", label="B1 sadece batarya + rej.")
    a1.axhline(0.10, color=MUTED, lw=0.8, ls=":")
    a1.text(logs["S2"].t.iloc[-1] / 3600, 0.12, "K1 alt sınırı 0.10",
            fontsize=7.5, color=MUTED, ha="right")
    a1.set(xlabel="Zaman [saat]", ylabel="SoC_SC (60 s ortalama)", ylim=(-0.03, 1.03))
    a1.set_title("Süperkapasitörün doluluk durumu", fontsize=9.5, color=INK, loc="left")
    a2.set(xlabel="Sıra (en yüksek 400 adım)", ylabel="I_B [A]")
    a2.set_title("Batarya akımı süre eğrisi (en yüksek değerler)", fontsize=9.5, color=INK, loc="left")
    for a in (a1, a2):
        _style(a)
        a.yaxis.grid(True, color="#e4e3dd", lw=0.6)
        a.xaxis.label.set_color(MUTED); a.yaxis.label.set_color(MUTED)
    a1.legend(fontsize=7.5, frameon=False, loc="upper right", ncol=2)
    a2.legend(fontsize=7.5, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "X1_soc_current.png", dpi=150)
    plt.close(fig)


def fig_x2(t):
    codes = list(t.index)
    labels = [f"{c}  {t.loc[c, 'Varyant']}" for c in codes]
    cols = [C_SERIES[0] if c in ("S1", "S2") else C_SERIES[1] if c.startswith("S1") else C_SERIES[2]
            for c in codes]
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, (k, title, fmt) in zip(axs, [("peak_I", "Tepe I_B [A]", "{:.1f}"),
                                          ("t_vs_B1", "Deşarj süresi, B1'e göre [%]", "{:+.2f}"),
                                          ("socsc_min", "En düşük SoC_SC", "{:.2f}")]):
        _hbars(ax, labels, t[k].to_numpy(), cols, fmt, title)
    fig.suptitle("X2 · Ablasyonlar, uzun deşarj, eğitim çevrimi · mavi: tam yöntem, turuncu: S1 "
                 "ablasyonları, yeşil: S2 ablasyonları", fontsize=9, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG / "X2_ablation.png", dpi=150)
    plt.close(fig)


def _save(df, name, cols):
    keep = [c for c in cols if c in df.columns]
    out = df[keep].rename(columns=COLS)
    out.to_csv(TAB / name, float_format="%.4g")
    return out


def main():
    t0 = time.time()
    cfg = load_config()
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    margs = metric_args(cfg, sim)
    tuned = load_tuned()

    tabs, logs = x1(cfg, sim, margs, tuned)
    long_cols = ["Yöntem"] + list(COLS) + [f"{k}_std" for k in ("peak_I", "rms_I", "dT", "t_dis")]
    pd.set_option("display.width", 220)
    print("X1 · uzun deşarj\n", _save(tabs["long"], "X1_long_discharge.csv", long_cols)
          .to_string(float_format=lambda x: f"{x:.3g}"))
    _save(tabs["cycle"], "X1_first_cycle.csv",
          ["Yöntem", "peak_I", "p99_I", "rms_I", "dT", "socsc_min", "socsc_mean", "decision_us"])
    crit = criteria(tabs["long"])
    crit.to_csv(TAB / "X1_criteria.csv", index=False)
    print("\nK1–K3\n", crit.to_string(index=False))

    t_b0, t_b1 = tabs["long"].loc["B0", "t_dis"], tabs["long"].loc["B1", "t_dis"]
    t2 = x2(cfg, sim, margs, tuned, t_b0, t_b1)
    print("\nX2 · ablasyonlar\n", _save(t2, "X2_ablation.csv",
          ["Varyant", "peak_I", "p99_I", "rms_I", "dT", "t_dis", "t_vs_B1", "socsc_min", "socsc_mean"])
          .to_string(float_format=lambda x: f"{x:.3g}"))

    fig_x1_summary(tabs["long"])
    fig_x1_soc_current(logs)
    fig_x2(t2)
    print(f"\nToplam süre {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
