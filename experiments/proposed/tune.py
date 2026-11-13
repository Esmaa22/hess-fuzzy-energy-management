"""Adım 7.2: C0 (crisp), S1 (SCS-FLC) ve S2 (SCS-FLC, bulanık tavan) için eşit bütçeli ayar,
yalnızca eğitim çevriminde.

Yöntem ve amaç fonksiyonu: src/hess/tuning.py başındaki açıklama.
Her yöntem için 24 değerlendirme (başlangıç noktası + 23 Latin hiperküp noktası, aynı tohum).

Kullanım:  python experiments/proposed/tune.py        (~1 dk)
Çıktılar:  results/tables/tuning_{C0,S1,S2}.csv,
           results/tables/tuning_summary.csv, config/tuned.yaml
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.simulator import BatteryOnlyEMS, Simulator
from hess.tuning import BUDGET, design, evaluate, make_ems, metric_args, save_tuned

TAB = ROOT / "results" / "tables"


def main():
    t0 = time.time()
    cfg = load_config()
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    margs = metric_args(cfg, sim)
    t_b1 = sim.run(BatteryOnlyEMS(True), max_cycles=30).discharge_time_s
    print(f"Eğitim çevrimi: {cfg['drive_cycle']['file']} (seed {cfg['drive_cycle']['seed']}), "
          f"B1 deşarj süresi {t_b1:.0f} s, bütçe {BUDGET}/yöntem\n")

    best, summary = {}, []
    for method in ("C0", "S1", "S2"):
        rows = []
        for i, prm in enumerate(design(method)):
            res = evaluate(sim, make_ems(method, cfg, prm), margs, t_b1)
            rows.append({"i": i, **prm, **res})
        df = pd.DataFrame(rows)
        df.to_csv(TAB / f"tuning_{method}.csv", index=False, float_format="%.4f")
        b = df.loc[df.J.idxmin()]
        start = df.iloc[0]
        best[method] = {p: b[p] for p in design(method)[0]}
        summary += [{"Yöntem": method, "Nokta": "başlangıç", **start.to_dict()},
                    {"Yöntem": method, "Nokta": "en iyi", **b.to_dict()}]
        print(f"{method}: uygun {int(df.feasible.sum())}/{len(df)} | en iyi (i={int(b.i)}) "
              + ", ".join(f"{p}={b[p]:.3g}" for p in best[method])
              + f" | tepe I_B {b.peak_I:.1f} A, t/t_B1 {b.t_rel_B1:.3f}, min SoC_SC {b.min_soc_sc:.2f}")

    pd.DataFrame(summary).drop(columns=["i"]).to_csv(TAB / "tuning_summary.csv", index=False,
                                                      float_format="%.4f")
    save_tuned(best, meta={"egitim_cevrimi_seed": cfg["drive_cycle"]["seed"],
                           "butce": BUDGET, "t_B1_s": float(t_b1)})
    print(f"\nconfig/tuned.yaml yazıldı. Toplam süre {time.time() - t0:.0f} s.")


if __name__ == "__main__":
    main()
