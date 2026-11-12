"""CP4 ön denemesi: kesin (crisp) eşikli tepe tıraşlama + bataryadan SC yeniden şarjı.

Amaç: "SC enerjisini koruyan" stratejinin bu modelde uzun deşarjda tepe akımını gerçekten
azaltıp azaltmadığını ve parametrelere ne kadar duyarlı olduğunu görmek
(docs/contribution_proposal.md §2.3). Bu betik katkının kendisi değildir; bulanık sürüm
Adım 7'de yazılacak.

Kural (P: bara talebi):
  P > P_th                    -> SC, P − P_th kadarını karşılar (tepe tıraşlama)
  P < 0                       -> frenleme enerjisinin tamamı SC'ye istenir
  0 ≤ P < P_lo ve SoC_SC < hedef -> batarya SC'yi P_ch ile şarj eder
Uzun deşarj (%100 → %20), FLC ile aynı simülatör ve güvenlik katmanı.

Kullanım:  python experiments/proposed/probe_crisp_threshold.py   (~1 dk)
Çıktı:     results/tables/probe_crisp_threshold.csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import pandas as pd

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.metrics import compute
from hess.simulator import EMS, BatteryOnlyEMS, Simulator


class _Fixed(EMS):
    """Önceden hesaplanmış isteği temel güvenlik katmanına geçirmek için."""

    def __init__(self, ems, req):
        self.req, self.battery_regen = req, ems.battery_regen

    def sc_request(self, *_):
        return self.req


class ProbeSimulator(Simulator):
    """Çekişte negatif SC isteğine (bataryadan SC şarjı) izin veren simülatör."""

    def _arbitrate(self, ems, p):
        req = ems.sc_request(p, self.bat.soc, self.sc.soc)
        if p >= 0.0 and req < 0.0:
            acc = min(-req, self.sc.max_charge_power(self.dt) / self.eta)
            return p + acc, -acc, 0.0
        return super()._arbitrate(_Fixed(ems, req), p)


class CrispThreshold(EMS):
    def __init__(self, p_th, p_lo, p_ch, target):
        self.p_th, self.p_lo, self.p_ch, self.target = p_th, p_lo, p_ch, target
        self.name = f"crisp th={p_th} ch={p_ch} hedef={target}"

    def sc_request(self, p, soc_b, soc_sc):
        if p > self.p_th:
            return p - self.p_th
        if p < 0.0:
            return p
        if p < self.p_lo and soc_sc < self.target:
            return -self.p_ch
        return 0.0


def main():
    cfg = load_config()
    sim = ProbeSimulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    args = dict(i_rated=sim.bat.q_ah, e_nominal_wh=sim.bat.nominal_wh,
                t_amb=cfg["battery"]["thermal"]["t_amb_c"], dt=sim.dt)
    cases = [("Sadece batarya", BatteryOnlyEMS(False)), ("Batarya + rej. (E6)", BatteryOnlyEMS(True)),
             ("FLC (literal)", FLCEMS(cfg))]
    cases += [(None, CrispThreshold(t, 1500, c, g))
              for t in (2500, 3000, 3500) for c in (500, 1000) for g in (0.6, 0.8)]
    rows, base = [], None
    for name, e in cases:
        r = sim.run(e, max_cycles=30)
        m = compute(r, **args)
        base = base or m
        rows.append({"EMS": name or e.name,
                     "Tepe I_B [A]": m["peak_I"], "Tepe I_B %": 100 * (m["peak_I"] / base["peak_I"] - 1),
                     "%99 I_B [A]": np.percentile(r.log.i_b, 99),
                     "RMS I_B %": 100 * (m["rms_I"] / base["rms_I"] - 1),
                     "ΔT [°C]": m["dT"],
                     "Deşarj süresi %": 100 * (m["t_dis"] / base["t_dis"] - 1),
                     "En düşük SoC_SC": r.log.soc_sc.min()})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results" / "tables" / "probe_crisp_threshold.csv", index=False, float_format="%.3f")
    pd.set_option("display.width", 200)
    print(df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


if __name__ == "__main__":
    main()
