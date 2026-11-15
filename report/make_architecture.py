"""Rapor Şekil 1: HESS + EMS sistem mimarisi blok diyagramı.

Çıktı: results/figures/system_architecture.png
Kullanım (repo kökünden): python report/make_architecture.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "results" / "figures" / "system_architecture.png"

INK = "#2b2b2b"
MUTED = "#5f5e58"
BLUE = "#2a78d6"     # EMS ve kontrol sinyalleri
ORANGE = "#eb6834"   # önerilen ek (P_ch)
GREEN = "#1baf7a"    # süperkapasitör
GREY = "#a3a29b"     # DC bara
DASH = (0, (3, 2))


def box(ax, x, y, w, h, title, sub="", edge=INK, fill="white", lw=1.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fill, ec=edge, lw=lw))
    if sub:
        ax.text(x + w / 2, y + h * 0.68, title, ha="center", va="center", fontsize=9.5,
                fontweight="bold", color=INK)
        ax.text(x + w / 2, y + h * 0.32, sub, ha="center", va="center", fontsize=7.6,
                color=MUTED, linespacing=1.3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=9.5,
                fontweight="bold", color=INK)


def arrow(ax, p, q, color=INK, ls="-", both=False, lw=1.3):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>", mutation_scale=11,
                                 color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0))


def path(ax, pts, color, ls=DASH, lw=1.1):
    """Kırık çizgi; son parçanın ucunda ok."""
    xs, ys = zip(*pts[:-1])
    ax.plot(xs, ys, color=color, ls=ls, lw=lw)
    arrow(ax, pts[-2], pts[-1], color=color, ls=ls, lw=lw)


def main():
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Kaynaklar ve dönüştürücüler (sol)
    box(ax, 0.3, 3.0, 2.0, 1.05, "Batarya", "14s×22p NMC\n50.4 V, 73.7 Ah, 3.7 kWh")
    box(ax, 0.3, 0.4, 2.0, 1.05, "Süperkapasitör", "18s×15p\n48 V, ≈417 F", edge=GREEN, lw=1.6)
    box(ax, 2.85, 3.1, 1.3, 0.85, "DC/DC", "tek yönlü")
    box(ax, 2.85, 0.5, 1.3, 0.85, "DC/DC", "çift yönlü")
    arrow(ax, (2.3, 3.52), (2.85, 3.52))
    arrow(ax, (2.3, 0.92), (2.85, 0.92), both=True)

    # DC bara, motor, araç
    ax.plot([4.85, 4.85], [0.75, 3.75], color=GREY, lw=4, solid_capstyle="round")
    ax.text(4.68, 2.25, "DC bara", fontsize=7.6, color=MUTED, rotation=90, va="center", ha="center")
    arrow(ax, (4.15, 3.52), (4.85, 3.52))
    arrow(ax, (4.15, 0.92), (4.85, 0.92), both=True)
    box(ax, 5.45, 1.75, 1.55, 1.0, "İnverter +\nmotor")
    arrow(ax, (4.85, 2.25), (5.45, 2.25), both=True)
    box(ax, 7.6, 1.7, 1.95, 1.1, "Araç modeli", "boylamsal dinamik (Denk. 1)\nrejeneratif geri kazanım %20")
    arrow(ax, (7.0, 2.25), (7.6, 2.25), both=True)
    box(ax, 10.1, 1.75, 1.75, 1.0, "Sürüş çevrimi", "hız profili v(t), Δt = 1 s")
    arrow(ax, (10.1, 2.25), (9.55, 2.25))

    # EMS (üst)
    box(ax, 3.4, 4.55, 4.3, 1.3, "EMS (karar katmanı)",
        "F0: FLC (36 kural)   R0: FRL (FLC + Q-learning)\nS1 / S2: SCS-FLC (12 kural, önerilen)   C0: crisp",
        edge=BLUE, fill="#eaf2fc", lw=1.8)

    # Sinyaller
    path(ax, [(8.57, 2.8), (8.57, 5.2), (7.7, 5.2)], BLUE)
    ax.text(8.67, 4.0, "$P_{dem}$", fontsize=9, color=BLUE, va="center")
    path(ax, [(3.5, 4.55), (3.5, 3.95)], BLUE)
    ax.text(3.0, 4.25, "$P_B^{*}$", fontsize=9, color=BLUE, va="center")
    path(ax, [(4.45, 4.55), (4.45, 1.6), (3.95, 1.6), (3.95, 1.35)], BLUE)
    ax.text(4.0, 2.25, "$P_{SC}^{*}$", fontsize=9, color=BLUE, va="center", ha="right")
    path(ax, [(1.3, 4.05), (1.3, 5.2), (3.4, 5.2)], MUTED)
    ax.text(1.4, 5.35, "$SoC_B$, $SoC_{SC}$ ölçümleri", fontsize=8, color=MUTED)

    # Önerilen ek: bataryadan SC şarjı
    arrow(ax, (0.75, 3.0), (0.75, 1.45), color=ORANGE, ls=(0, (4, 2)), lw=1.7)
    ax.text(0.88, 2.22, "$P_{ch}$: bataryadan SC şarjı\n(önerilen, S1/S2)", fontsize=7.8,
            color=ORANGE, va="center")

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    print(f"kaydedildi: {OUT}")


if __name__ == "__main__":
    main()
