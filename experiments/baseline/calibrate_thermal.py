"""Termal model kalibrasyonu (A-10).

Makale sıcaklığın nasıl hesaplandığını vermiyor. Toplu parametreli hücre modelindeki
ısı atım katsayısı hA, sadece-batarya senaryosunda (rejenerasyonsuz, %100 → %20)
hücre sıcaklık artışı makaledeki 2.1 °C olacak şekilde bisection ile bulunur.
Bulunan değer config/default.yaml'a elle yazılır ve sonra sabit tutulur.

Kullanım:  python experiments/baseline/calibrate_thermal.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.simulator import BatteryOnlyEMS, Simulator

TARGET_DT = 2.1  # [°C] [1] Tablo 8, sadece batarya


def delta_t(cfg, prof, hA: float) -> float:
    cfg["battery"]["thermal"]["hA"] = hA
    sim = Simulator(cfg, prof)
    log = sim.run(BatteryOnlyEMS(False), max_cycles=20).log
    return float(log["temp_b"].max() - cfg["battery"]["thermal"]["t_amb_c"])


def main() -> None:
    cfg = load_config()
    prof = load_profile(ROOT / cfg["drive_cycle"]["file"])
    lo, hi = 1e-4, 10.0          # hA arttıkça ΔT azalır
    for _ in range(50):
        mid = (lo * hi) ** 0.5   # logaritmik bisection
        if delta_t(cfg, prof, mid) > TARGET_DT:
            lo = mid
        else:
            hi = mid
    hA = (lo * hi) ** 0.5
    m_cp = cfg["battery"]["thermal"]["cell_mass_kg"] * cfg["battery"]["thermal"]["cp"]
    print(f"hA = {hA:.5f} W/K  ->  ΔT = {delta_t(cfg, prof, hA):.3f} °C")
    print(f"Termal zaman sabiti τ = m·c_p / hA = {m_cp / hA:.0f} s")


if __name__ == "__main__":
    main()
