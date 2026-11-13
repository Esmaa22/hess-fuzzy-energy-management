"""X3 test çevrimleri (CP4 §5): 3 rejim × 10 seed = 30 çevrim.

Eğitim çevrimiyle aynı üreteç (drive_cycle.generate_urban_profile) ve aynı istatistik
hedefleri (900 s, 12.4 km, v_max, a_max, d_max) kullanılır. Değişenler:
  * seed      : 101–110 (eğitim çevrimi seed 7; ayarda hiç kullanılmadı)
  * rejim     : seyirdeki mikro hız dalgalanmasının genliği (A-17)
                sakin 0.5 m/s, nominal 1.0 m/s (eğitim çevrimiyle aynı), agresif 1.5 m/s
Üreteç bir seed için profili süreye sığdıramazsa o seed atlanır ve sıradaki denenir.
"""

from __future__ import annotations

import copy

import pandas as pd

from .drive_cycle import generate_urban_profile, profile_stats

REGIMES = {"sakin": 0.5, "nominal": 1.0, "agresif": 1.5}
SEEDS = range(101, 111)
TRAIN_SEED = 7


def make_test_cycles(cfg: dict, n_per_regime: int = 10) -> list[dict]:
    """[{regime, seed, micro_amp, profile, stats}, ...] (30 kayıt)."""
    out = []
    for regime, amp in REGIMES.items():
        seed, n = SEEDS.start, 0
        while n < n_per_regime:
            assert seed != TRAIN_SEED
            c = copy.deepcopy(cfg)
            c["drive_cycle"]["seed"] = seed
            try:
                prof = generate_urban_profile(c, micro_amp=amp)
            except RuntimeError:
                seed += 1
                continue
            out.append({"regime": regime, "seed": seed, "micro_amp": amp, "profile": prof,
                        "stats": profile_stats(prof)})
            seed += 1
            n += 1
    return out


def cycles_table(cycles: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{"rejim": c["regime"], "seed": c["seed"], "micro_amp": c["micro_amp"],
                          **c["stats"]} for c in cycles])
