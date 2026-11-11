"""FLC görselleri ve ön kontrol: üyelik fonksiyonları, kontrol yüzeyleri, örnek çıkarım,
sadece-batarya ile hızlı karşılaştırma.

Kullanım:  python experiments/baseline/plot_flc.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS, build_fis
from hess.simulator import BatteryOnlyEMS, Simulator

FIG = ROOT / "results" / "figures"


def plot_membership(fis):
    fig, ax = plt.subplots(2, 3, figsize=(13, 6))
    specs = [("soc_b", np.linspace(0, 100, 501), "SoC$_B$ [%]"),
             ("soc_sc", np.linspace(0, 100, 501), "SoC$_{SC}$ [%]"),
             ("p_dem", np.linspace(-5100, 5600, 1001), "$P_{dem}$ [W]")]
    for a, (name, x, lbl) in zip(ax[0], specs):
        for t, mf in fis._in[name].terms.items():
            a.plot(x, mf(x), label=t)
        a.set_xlabel(lbl); a.set_ylabel("μ"); a.legend(fontsize=8); a.grid(alpha=0.3)
    for a, name, lbl in [(ax[1][0], "c_b", "$C_B$ [%]"), (ax[1][1], "c_sc", "$C_{SC}$ [%]")]:
        o = fis._out[name]
        for t, mf in o.terms.items():
            a.plot(o.universe, mf(o.universe), label=t)
        a.set_xlabel(lbl); a.set_ylabel("μ"); a.legend(fontsize=7, ncol=2); a.grid(alpha=0.3)
    # örnek çıkarım: birleştirilmiş küme ve centroid
    x = dict(soc_b=50.0, soc_sc=30.0, p_dem=3500.0)
    w = fis.firing_strengths(**x)
    agg = fis.aggregate(w)
    o = fis._out["c_sc"]
    a = ax[1][2]
    a.fill_between(o.universe, agg["c_sc"], alpha=0.4, label="birleştirilmiş küme")
    c = fis.defuzzify("c_sc", agg["c_sc"])
    a.axvline(c, c="k", ls="--", label=f"centroid = {c:.1f}")
    a.set_xlim(0, 70); a.set_xlabel("$C_{SC}$ [%]"); a.legend(fontsize=8); a.grid(alpha=0.3)
    a.set_title("SoC$_B$=50, SoC$_{SC}$=30, $P_{dem}$=3500 W", fontsize=9)
    fig.suptitle("FLC üyelik fonksiyonları (girdiler: yamuk, çıktılar: üçgen) ve örnek çıkarım")
    fig.tight_layout()
    fig.savefig(FIG / "flc_membership.png", dpi=150)
    return x


def plot_surfaces(cfg, fis):
    ems = FLCEMS(cfg)
    ssc = np.linspace(0, 100, 51)
    p = np.linspace(100, 5600, 56)
    fig = plt.figure(figsize=(13, 4.2))
    for i, sb in enumerate([10, 50, 90]):
        Z = np.array([[100 * ems.sc_share(pp, *ems.decide(pp, sb / 100, s / 100), ems.regen_ref)
                       for pp in p] for s in ssc])
        a = fig.add_subplot(1, 3, i + 1, projection="3d")
        P, S = np.meshgrid(p, ssc)
        a.plot_surface(P / 1000, S, Z, cmap="viridis", linewidth=0)
        a.set_xlabel("$P_{dem}$ [kW]"); a.set_ylabel("SoC$_{SC}$ [%]"); a.set_zlabel("SC payı [%]")
        a.set_zlim(0, 65); a.set_title(f"SoC$_B$ = {sb}%")
        a.view_init(elev=25, azim=-130)
    fig.suptitle("FLC kontrol yüzeyi: çekişte süperkapasitör payı  $C_{SC}/(C_B+C_{SC})$")
    fig.tight_layout()
    fig.savefig(FIG / "flc_surface.png", dpi=150)


def quick_compare(cfg):
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    res = {e.name: sim.run(e, max_cycles=30) for e in (BatteryOnlyEMS(False), FLCEMS(cfg))}
    print(f"\n{'':24}{'Sadece batarya':>16}{'FLC':>10}{'Değişim':>10}{'Makale':>10}")
    rows = [("Tepe I_B [A]", lambda r: r.log.i_b.max(), "−%22.7"),
            ("RMS I_B [A]", lambda r: np.sqrt((r.log.i_b ** 2).mean()), "−%1.8"),
            ("Deşarj süresi [s]", lambda r: r.discharge_time_s, "+%6.3"),
            ("ΔT [°C]", lambda r: r.log.temp_b.max() - 20, "−%7.1"),
            ("Mesafe [km]", lambda r: r.distance_km, "+%6.1"),
            ("Tepe P_SC [W]", lambda r: r.log.p_sc.max(), "1850 W")]
    for name, f, paper in rows:
        a, b = f(res["battery_only"]), f(res["flc"])
        print(f"{name:<24}{a:>16.1f}{b:>10.1f}{100*(b/a-1) if a else 0:>+9.1f}%{paper:>10}")
    L = res["flc"].log
    print(f"SoC_SC aralığı: {L.soc_sc.min():.2f}–{L.soc_sc.max():.2f}, "
          f"ortalama {L.soc_sc.mean():.2f}")
    return res


def main():
    cfg = load_config()
    fis = build_fis(cfg)
    x = plot_membership(fis)
    print("Örnek çıkarım", x, "->", {k: round(v, 2) for k, v in fis.evaluate(**x).items()})
    for w, r in fis.explain(**x):
        print(f"  w={w:.2f}  EĞER {r.antecedent} İSE {r.consequent}")
    plot_surfaces(cfg, fis)
    quick_compare(cfg)
    print("\nKaydedildi: results/figures/flc_membership.png, flc_surface.png")


if __name__ == "__main__":
    main()
