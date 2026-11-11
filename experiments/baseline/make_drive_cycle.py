"""Sentetik sürüş profilini üretir, CSV ve grafik olarak kaydeder, istatistikleri doğrular.

Kullanım:  python experiments/baseline/make_drive_cycle.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from hess import ROOT, load_config
from hess.drive_cycle import PAPER_STATS, generate_urban_profile, profile_stats


def main() -> None:
    cfg = load_config()
    df = generate_urban_profile(cfg)
    out = ROOT / cfg["drive_cycle"]["file"]
    df.to_csv(out, index=False, float_format="%.4f")

    s = profile_stats(df)
    tol = cfg["drive_cycle"]["tolerance"]
    rows, all_ok = [], True
    print(f"{'İstatistik':<16}{'Makale':>10}{'Üretilen':>12}{'Fark %':>9}  Durum")
    for k, ref in PAPER_STATS.items():
        diff = (s[k] - ref) / ref
        ok = abs(diff) <= tol
        all_ok &= ok
        rows.append((k, ref, s[k], 100 * diff, ok))
        print(f"{k:<16}{ref:>10.2f}{s[k]:>12.2f}{100*diff:>9.2f}  {'OK' if ok else 'HATA'}")
    print(f"Duruşta geçen süre oranı: %{100*s['stop_fraction']:.1f}")

    # Tablo
    tbl = ROOT / "results" / "tables" / "drive_cycle_stats.csv"
    import pandas as pd
    pd.DataFrame(rows, columns=["stat", "paper", "generated", "diff_pct", "within_tol"]).to_csv(
        tbl, index=False, float_format="%.3f"
    )

    # Grafik
    fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    ax[0].plot(df["time_s"], df["speed_kmh"], lw=1.2)
    ax[0].set_ylabel("Hız [km/h]")
    ax[0].set_title(f"Sentetik şehir içi profil: {s['distance_km']:.2f} km, "
                    f"ort. {s['avg_speed_kmh']:.1f} km/h")
    ax[0].grid(alpha=0.3)
    ax[1].plot(df["time_s"], df["accel_mps2"], lw=1.0, color="tab:orange")
    ax[1].set_ylabel("İvme [m/s²]")
    ax[1].set_xlabel("Zaman [s]")
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "drive_cycle.png", dpi=150)

    print(f"\nKaydedildi: {out.relative_to(ROOT)}, results/figures/drive_cycle.png, "
          f"results/tables/drive_cycle_stats.csv")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
