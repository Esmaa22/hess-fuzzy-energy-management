"""Adım 7.4: X3 (genelleme), X4 (parametre duyarlılığı), X5 (ölçüm gürültüsü). CP4 §5–6.

X3  30 test çevrimi (src/hess/test_cycles.py: 3 rejim × 10 seed, ayarda hiç kullanılmadı),
    uzun deşarj. Yöntemler: B1, F0, C0, S1, S2 ve ablasyonlar S1-A1, S1-A2, S2-A1, S2-A4, S2-A5.
    Eşleştirilmiş Wilcoxon işaretli sıra testi (aynı 30 çevrim). R0 dahil edilmedi: X1'de F0 ile
    farkı < 1 std; 5 seed × 30 çevrim maliyeti karşılığında yeni bilgi vermiyor (Limitations).
X4  Eğitim çevrimi, ayarlı noktadan tek parametre bozulması: −%20, −%10, +%10, +%20
    (C0: p_th, p_lo, p_ch, target;  S1: k_ch, k_csc, k_p, k_soc;  S2: c_cap, d_cap, k_ch, k_soc).
    C0'ın hedefi 1.0'a kırpılır.
X5  Eğitim çevrimi, EMS'in ölçtüğü girdilere Gauss gürültüsü (fizik gürültüsüz):
    SoC_SC + N(0, σ), P_dem · (1 + N(0, σ)), σ ∈ {0.02, 0.05}, 5 gürültü tohumu. F0, C0, S1, S2.

"Çöken" çalıştırma: en düşük SoC_SC < 0.01 (SC tamamen boşalmış).

Kullanım:  python experiments/proposed/run_robustness.py        (~5 dk, 2 çekirdek)
Önkoşul:   config/tuned.yaml (tune.py)
Çıktılar:  results/tables/X3_cycles.csv, X3_per_cycle.csv, X3_summary.csv, X3_tests.csv,
           X4_sensitivity.csv, X4_summary.csv, X5_noise.csv, X5_summary.csv, K4_K5.csv
           results/figures/X3_generalization.png, X4_sensitivity.png, X5_noise.png
"""

import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from hess import ROOT, load_config
from hess.ablations import FLCRechargeEMS, S2CrispChargeEMS
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.metrics import compute
from hess.simulator import BatteryOnlyEMS, NoisyEMS, Simulator
from hess.test_cycles import cycles_table, make_test_cycles
from hess.tuning import load_tuned, make_ems, metric_args

TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"
COLLAPSE = 0.01
X3_METHODS = ["B1", "F0", "C0", "S1", "S2", "S1-A1", "S1-A2", "S2-A1", "S2-A4", "S2-A5"]
PERTURB = [-0.2, -0.1, 0.1, 0.2]
SIGMAS = [0.02, 0.05]
NOISE_SEEDS = range(5)

C_BASE, C_C0 = "#a3a29b", "#5f5e58"
C_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, MUTED, GRID = "#2b2b29", "#6b6a64", "#e4e3dd"


# --------------------------------------------------------------------------- işçi süreçler
_G = {}


def _init(cfg, tuned, profiles):
    _G.update(cfg=cfg, tuned=tuned, sims={k: Simulator(cfg, p) for k, p in profiles.items()})


def build(code, cfg, tuned, prm=None):
    if code == "B1":
        return BatteryOnlyEMS(True)
    if code == "F0":
        return FLCEMS(cfg)
    if code in ("C0", "S1", "S2"):
        return make_ems(code, cfg, prm or tuned[code])
    base, abl = code.split("-")
    if abl == "A1":
        return make_ems(base, cfg, tuned[base], recharge=False)
    if code == "S1-A2":
        return FLCRechargeEMS(cfg, tuned["S1"])
    if code == "S2-A4":
        return make_ems("S2", cfg, {**tuned["S2"], "d_cap": 0.0})
    if code == "S2-A5":
        return S2CrispChargeEMS(cfg, tuned["S2"], tuned["C0"])
    raise ValueError(code)


def _work(task):
    cfg, tuned = _G["cfg"], _G["tuned"]
    sim = _G["sims"][task["profile"]]
    ems = build(task["method"], cfg, tuned, task.get("prm"))
    if task.get("sigma"):
        ems = NoisyEMS(ems, task["sigma"], task["noise_seed"])
    r = sim.run(ems, max_cycles=30)
    m = compute(r, **metric_args(cfg, sim))
    return {**{k: v for k, v in task.items() if k != "prm"}, **(task.get("prm") or {}),
            "peak_I": m["peak_I"], "p99_I": float(np.percentile(r.log.i_b, 99)),
            "rms_I": m["rms_I"], "dT": m["dT"], "t_dis": m["t_dis"],
            "min_soc_sc": m["socsc_min"], "mean_soc_sc": m["socsc_mean"],
            "collapsed": m["socsc_min"] < COLLAPSE}


# --------------------------------------------------------------------------- X3
def x3_analysis(df):
    t_b1 = df[df.method == "B1"].set_index("profile").t_dis
    df["t_vs_B1"] = 100 * (df.t_dis / df.profile.map(t_b1) - 1)
    piv = {k: df.pivot(index="profile", columns="method", values=k)
           for k in ("peak_I", "p99_I", "rms_I", "dT", "t_vs_B1", "min_soc_sc")}
    rows = []
    for m in X3_METHODS:
        d = df[df.method == m]
        rows.append({"Yöntem": m, "Tepe I_B ort.": d.peak_I.mean(), "Tepe I_B medyan": d.peak_I.median(),
                     "Tepe I_B en kötü": d.peak_I.max(), "Tepe I_B std": d.peak_I.std(),
                     "%99 I_B ort.": d.p99_I.mean(), "RMS ort.": d.rms_I.mean(), "ΔT ort.": d.dT.mean(),
                     "Süre B1'e göre ort. [%]": d.t_vs_B1.mean(),
                     "Süre B1'e göre en kötü [%]": d.t_vs_B1.min(),
                     "En düşük SoC_SC (30 çevrimin en kötüsü)": d.min_soc_sc.min(),
                     "Çöken çevrim": int(d.collapsed.sum()),
                     **{f"Tepe I_B ort. ({r})": d[d.regime == r].peak_I.mean()
                        for r in ("sakin", "nominal", "agresif")}})
    summary = pd.DataFrame(rows)

    pairs = [("S2", "C0"), ("S1", "C0"), ("S2", "S1"), ("S2", "F0"), ("S1", "F0"), ("C0", "F0"),
             ("S1-A1", "S1"), ("S1-A2", "S1"), ("S2-A1", "S2"), ("S2-A4", "S2"), ("S2-A5", "S2")]
    tests = []
    for a, b in pairs:
        for k, lbl in [("peak_I", "Tepe I_B"), ("p99_I", "%99 I_B"), ("t_vs_B1", "Süre B1'e göre"),
                       ("min_soc_sc", "En düşük SoC_SC")]:
            x, y = piv[k][a], piv[k][b]
            d = x - y
            p = wilcoxon(x, y).pvalue if (d != 0).any() else 1.0
            tests.append({"A": a, "B": b, "Ölçüt": lbl, "medyan(A−B)": d.median(),
                          "ort(A−B)": d.mean(), "A < B (çevrim)": int((d < 0).sum()),
                          "A > B (çevrim)": int((d > 0).sum()), "Wilcoxon p": p})
    return summary, pd.DataFrame(tests), piv


# --------------------------------------------------------------------------- X4 / X5
def x4_tasks(tuned):
    tasks = []
    for m in ("C0", "S1", "S2"):
        tasks.append({"profile": "train", "method": m, "param": "nominal", "delta": 0.0,
                      "prm": dict(tuned[m])})
        for p in tuned[m]:
            for d in PERTURB:
                prm = dict(tuned[m])
                prm[p] = prm[p] * (1 + d)
                if p == "target":
                    prm[p] = min(prm[p], 1.0)
                tasks.append({"profile": "train", "method": m, "param": p, "delta": d, "prm": prm})
    return tasks


def x4_summary(df):
    rows = []
    for m, d in df.groupby("method", sort=False):
        nom = d[d.param == "nominal"].peak_I.iloc[0]
        q = d[d.param != "nominal"].copy()
        q["deg"] = 100 * (q.peak_I / nom - 1)
        q20 = q[q.delta.abs() == 0.2]
        rows.append({"Yöntem": m, "Nominal tepe I_B": nom,
                     "En kötü tepe I_B (±%20)": q20.peak_I.max(),
                     "En büyük kötüleşme ±%20 [%]": q20.deg.max(),
                     "Ort. kötüleşme ±%20 [%]": q20.deg.clip(lower=0).mean(),
                     "En büyük kötüleşme ±%10 [%]": q[q.delta.abs() == 0.1].deg.max(),
                     "Çöken (16 bozulmadan)": int(q.collapsed.sum()),
                     "En kötü parametre": q.loc[q.deg.idxmax(), "param"]
                     + f" {q.loc[q.deg.idxmax(), 'delta']:+.0%}"})
    return pd.DataFrame(rows)


def x5_tasks():
    tasks = [{"profile": "train", "method": m, "sigma": 0.0, "noise_seed": -1}
             for m in ("F0", "C0", "S1", "S2")]
    tasks += [{"profile": "train", "method": m, "sigma": s, "noise_seed": k}
              for m in ("F0", "C0", "S1", "S2") for s in SIGMAS for k in NOISE_SEEDS]
    return tasks


def x5_summary(df):
    rows = []
    for (m, s), d in df.groupby(["method", "sigma"], sort=False):
        nom = df[(df.method == m) & (df.sigma == 0)].peak_I.iloc[0]
        rows.append({"Yöntem": m, "σ": s, "Tepe I_B ort.": d.peak_I.mean(), "Tepe I_B std": d.peak_I.std(),
                     "Tepe I_B en kötü": d.peak_I.max(), "Nominale göre [%]": 100 * (d.peak_I.mean() / nom - 1),
                     "En düşük SoC_SC": d.min_soc_sc.min(), "Çöken": int(d.collapsed.sum()), "n": len(d)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- K4 / K5
def k4_k5(summary, tests, x4s):
    s = summary.set_index("Yöntem")
    t = tests.set_index(["A", "B", "Ölçüt"])
    x4 = x4s.set_index("Yöntem")
    rows = []
    for m in ("S1", "S2"):
        p = t.loc[(m, "C0", "Tepe I_B"), "Wilcoxon p"]
        med = t.loc[(m, "C0", "Tepe I_B"), "medyan(A−B)"]
        rows += [
            {"Ölçüt": "K4", "Yöntem": m, "Koşul": "X3: 30 çevrim ort. tepe I_B ≤ C0",
             "Değer": f"{s.loc[m, 'Tepe I_B ort.']:.1f} / C0 {s.loc['C0', 'Tepe I_B ort.']:.1f} A",
             "Sağlandı": s.loc[m, "Tepe I_B ort."] <= s.loc["C0", "Tepe I_B ort."]},
            {"Ölçüt": "K4", "Yöntem": m, "Koşul": "X3: en kötü durum C0'dan iyi ve eşleştirilmiş fark p < 0.05",
             "Değer": f"en kötü {s.loc[m, 'Tepe I_B en kötü']:.1f} / C0 {s.loc['C0', 'Tepe I_B en kötü']:.1f} A;"
                      f" medyan fark {med:+.1f} A, p = {p:.3g}",
             "Sağlandı": bool(s.loc[m, "Tepe I_B en kötü"] < s.loc["C0", "Tepe I_B en kötü"] and p < 0.05
                              and med < 0)},
            {"Ölçüt": "K4", "Yöntem": m, "Koşul": "X4: ±%20 bozulmada en büyük kötüleşme C0'dan küçük",
             "Değer": f"%{x4.loc[m, 'En büyük kötüleşme ±%20 [%]']:.1f} / C0 "
                      f"%{x4.loc['C0', 'En büyük kötüleşme ±%20 [%]']:.1f}",
             "Sağlandı": x4.loc[m, "En büyük kötüleşme ±%20 [%]"] < x4.loc["C0", "En büyük kötüleşme ±%20 [%]"]},
        ]
    for a, base in [("S1-A1", "S1"), ("S1-A2", "S1"), ("S2-A1", "S2"), ("S2-A4", "S2"), ("S2-A5", "S2")]:
        r = t.loc[(a, base, "Tepe I_B")]
        rows.append({"Ölçüt": "K5", "Yöntem": a, "Koşul": f"X3: {a}, {base}'den anlamlı kötü (tepe I_B)",
                     "Değer": f"medyan fark {r['medyan(A−B)']:+.1f} A, p = {r['Wilcoxon p']:.3g}",
                     "Sağlandı": bool(r["medyan(A−B)"] > 0 and r["Wilcoxon p"] < 0.05)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- grafikler
def _style(ax, grid="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    getattr(ax, f"{grid}axis").grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def fig_x3(df):
    methods = ["B1", "F0", "C0", "S1", "S2"]
    names = {"B1": "B1 batarya + rej.", "F0": "F0 FLC", "C0": "C0 crisp", "S1": "S1 bulanık pay",
             "S2": "S2 bulanık tavan"}
    regimes = [("sakin", C_SERIES[0]), ("nominal", C_SERIES[1]), ("agresif", C_SERIES[2])]
    fig, axs = plt.subplots(1, 3, figsize=(15, 3.9), sharey=True)
    specs = [("peak_I", "Tepe I_B [A]"), ("min_soc_sc", "En düşük SoC_SC"), ("t_vs_B1", "Deşarj süresi, B1'e göre [%]")]
    rng = np.random.default_rng(0)
    for ax, (k, title) in zip(axs, specs):
        for i, m in enumerate(methods):
            y0 = len(methods) - 1 - i
            d = df[df.method == m]
            for j, (r, col) in enumerate(regimes):
                v = d[d.regime == r][k].to_numpy()
                ax.scatter(v, y0 + (j - 1) * 0.18 + rng.uniform(-0.05, 0.05, len(v)), s=16, color=col,
                           edgecolor="white", linewidth=0.6, zorder=3, label=r if (i == 0 and k == "peak_I") else None)
            med = d[k].median()
            ax.plot([med, med], [y0 - 0.38, y0 + 0.38], color=INK, lw=1.6, zorder=4)
        ax.set_yticks(range(len(methods))[::-1], [names[m] for m in methods], fontsize=8, color=INK)
        ax.set_title(title, fontsize=9.5, color=INK, loc="left")
        _style(ax)
    axs[1].axvline(0.10, color=MUTED, lw=0.8, ls=":")
    axs[0].legend(title="rejim", fontsize=7.5, title_fontsize=7.5, frameon=False, loc="lower right")
    fig.suptitle("X3 · 30 test çevrimi (ayarda kullanılmadı), uzun deşarj · her nokta bir çevrim · "
                 "siyah çizgi: medyan", fontsize=9, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG / "X3_generalization.png", dpi=150)
    plt.close(fig)


def fig_x4(df):
    fig, axs = plt.subplots(1, 3, figsize=(14, 3.6), sharey=True)
    titles = {"C0": "C0 crisp", "S1": "S1 bulanık pay", "S2": "S2 bulanık tavan"}
    for ax, m in zip(axs, ("C0", "S1", "S2")):
        d = df[df.method == m]
        nom = d[d.param == "nominal"].peak_I.iloc[0]
        params = [p for p in d.param.unique() if p != "nominal"]
        for p, col in zip(params, C_SERIES):
            q = pd.concat([d[d.param == p], pd.DataFrame([{"delta": 0.0, "peak_I": nom, "collapsed": False}])])
            q = q.sort_values("delta")
            ax.plot(100 * q.delta, q.peak_I, color=col, lw=2, marker="o", ms=5, label=p,
                    markeredgecolor="white", markeredgewidth=1)
            c = q[q.collapsed.astype(bool)]
            ax.scatter(100 * c.delta, c.peak_I, s=70, facecolor="none", edgecolor=INK, lw=1.2, zorder=5)
        ax.set_title(titles[m], fontsize=9.5, color=INK, loc="left")
        ax.set_xticks([-20, -10, 0, 10, 20])
        ax.set_xlabel("Parametre bozulması [%]", fontsize=8, color=MUTED)
        _style(ax, "y")
        ax.legend(fontsize=7.5, frameon=False, loc="upper center", ncol=2)
    axs[0].set_ylabel("Tepe I_B [A]", fontsize=8, color=MUTED)
    fig.suptitle("X4 · Eğitim çevrimi, tek parametre bozulması · içi boş halka: SC boşaldı (çöktü)",
                 fontsize=9, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIG / "X4_sensitivity.png", dpi=150)
    plt.close(fig)


def fig_x5(df):
    methods = ["F0", "C0", "S1", "S2"]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    w = 0.26
    for j, (s, col) in enumerate(zip([0.0] + SIGMAS, [C_BASE, C_SERIES[0], C_SERIES[1]])):
        vals = [df[(df.method == m) & (df.sigma == s)].peak_I for m in methods]
        x = np.arange(len(methods)) + (j - 1) * w
        ax.bar(x, [v.mean() for v in vals], width=w - 0.03, color=col, label=f"σ = {s:g}",
               edgecolor="white", linewidth=1)
        errs = [v.std() if len(v) > 1 else 0 for v in vals]
        for xi, v, e in zip(x, vals, errs):
            if e > 0:
                ax.errorbar(xi, v.mean(), yerr=e, color=INK, lw=1, capsize=2.5)
            ax.text(xi, v.mean() + e + 2, f"{v.mean():.0f}", ha="center", fontsize=7, color=INK)
    ax.set_xticks(range(len(methods)), ["F0 FLC", "C0 crisp", "S1 bulanık pay", "S2 bulanık tavan"],
                  fontsize=8, color=INK)
    ax.set_ylabel("Tepe I_B [A]", fontsize=8, color=MUTED)
    _style(ax, "y")
    ax.legend(fontsize=7.5, frameon=False, ncol=3, loc="upper right")
    ax.set_title("X5 · Ölçüm gürültüsü (SoC_SC, P_dem), eğitim çevrimi · 5 tohum ort. ± std",
                 fontsize=9, color=MUTED, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "X5_noise.png", dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- ana akış
def main():
    t0 = time.time()
    cfg = load_config()
    tuned = load_tuned()
    cycles = make_test_cycles(cfg)
    ct = cycles_table(cycles)
    profiles = {f"{c['regime']}_{c['seed']}": c["profile"] for c in cycles}
    profiles["train"] = load_profile(ROOT / cfg["drive_cycle"]["file"])
    # Rejimlerin talep gücü açısından farkı (çevrim istatistikleri kalibrasyon gereği aynı)
    pstats = []
    for k, prof in profiles.items():
        p = Simulator(cfg, prof).p_dem
        pstats.append({"profile": k, "P_dem pozitif ort. [W]": p[p > 0].mean(),
                       "P_dem %99 [W]": np.percentile(p, 99), "P_dem > 3 kW süre payı": (p > 3000).mean(),
                       "Frenleme enerjisi [Wh]": -p[p < 0].sum() / 3600})
    ps = pd.DataFrame(pstats).set_index("profile")
    ct.index = [f"{r}_{s}" for r, s in zip(ct.rejim, ct.seed)]
    ct = ct.join(ps)
    ct.to_csv(TAB / "X3_cycles.csv", float_format="%.4g")
    print("Rejimlere göre talep:\n", ct.groupby("rejim", sort=False)[list(ps.columns)].mean().round(1), "\n")

    tasks = [{"profile": k, "method": m, "regime": k.split("_")[0]}
             for k in profiles if k != "train" for m in X3_METHODS]
    n3, t4, t5 = len(tasks), x4_tasks(tuned), x5_tasks()
    tasks += t4 + t5
    print(f"{len(tasks)} çalıştırma (X3 {n3}, X4 {len(t4)}, X5 {len(t5)}), 2 süreç...")
    with mp.get_context("fork").Pool(2, initializer=_init, initargs=(cfg, tuned, profiles)) as pool:
        res = pool.map(_work, tasks, chunksize=2)
    x3 = pd.DataFrame(res[:n3])
    x4 = pd.DataFrame(res[n3:n3 + len(t4)])
    x5 = pd.DataFrame(res[n3 + len(t4):])

    summary, tests, _ = x3_analysis(x3)
    x3.to_csv(TAB / "X3_per_cycle.csv", index=False, float_format="%.4g")
    summary.to_csv(TAB / "X3_summary.csv", index=False, float_format="%.4g")
    tests.to_csv(TAB / "X3_tests.csv", index=False, float_format="%.4g")
    x4.to_csv(TAB / "X4_sensitivity.csv", index=False, float_format="%.4g")
    x4s = x4_summary(x4)
    x4s.to_csv(TAB / "X4_summary.csv", index=False, float_format="%.4g")
    x5.to_csv(TAB / "X5_noise.csv", index=False, float_format="%.4g")
    x5s = x5_summary(x5)
    x5s.to_csv(TAB / "X5_summary.csv", index=False, float_format="%.4g")
    k = k4_k5(summary, tests, x4s)
    k.to_csv(TAB / "K4_K5.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    f = lambda x: f"{x:.3g}"
    print("\nX3 özet\n", summary.to_string(index=False, float_format=f))
    print("\nX3 testler (tepe I_B)\n", tests[tests.Ölçüt == "Tepe I_B"].to_string(index=False, float_format=f))
    print("\nX4 özet\n", x4s.to_string(index=False, float_format=f))
    print("\nX5 özet\n", x5s.to_string(index=False, float_format=f))
    print("\nK4 / K5\n", k.to_string(index=False))

    fig_x3(x3)
    fig_x4(x4)
    fig_x5(x5)
    print(f"\nToplam süre {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
