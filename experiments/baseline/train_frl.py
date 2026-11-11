"""FRL eğitimi (plan §5.3) ve açgözlü politika değerlendirmesi, 5 seed.

Her seed için:
  - N bölüm; her bölüm profilin bir tam geçişi (A-14), başlangıç SoC'leri U(0.3, 1.0) (A-15)
  - ε her bölüm sonunda ×0.995 (alt sınır 0.01)
  - Çıktılar: results/models/frl_q_seed{n}.npy, results/tables/frl_training_seed{n}.csv
Ardından ortalama ± std öğrenme eğrisi ve öğrenilen politika tablosu çizilir.

Kullanım:  python experiments/baseline/train_frl.py [--episodes N] [--workers K]
"""

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.frl_ems import FRLEMS
from hess.simulator import Simulator

MODELS = ROOT / "results" / "models"
TABLES = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"


def train_seed(args) -> dict:
    seed, episodes = args
    cfg = load_config()
    f = cfg["frl"]
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    ems = FRLEMS(cfg, seed=seed)
    ems.train = True
    rng = np.random.default_rng(1000 + seed)        # başlangıç SoC'leri için ayrı akış
    rows, t0 = [], time.time()
    for ep in range(episodes):
        sb, ssc = rng.uniform(*f["init_soc_range"], size=2)
        r = sim.run(ems, soc_b=sb, soc_sc=ssc, max_cycles=1, log=False)
        rows.append({
            "episode": ep, "return": ems.ep_reward, "mean_reward": ems.ep_reward / ems.ep_steps,
            "mean_csc_traction": ems.ep_csc_sum / max(ems.ep_trac_steps, 1),
            "soc_sc_end": float(r.log.soc_sc.iloc[-1]), "epsilon": ems.agent.eps,
            "soc_b0": sb, "soc_sc0": ssc})
        ems.agent.decay_epsilon()
        if (ep + 1) % 200 == 0:
            print(f"[seed {seed}] bölüm {ep+1}/{episodes}  ort. ödül {np.mean([x['mean_reward'] for x in rows[-50:]]):+.3f}"
                  f"  ε={ems.agent.eps:.3f}  ({time.time()-t0:.0f} s)", flush=True)
    np.save(MODELS / f"frl_q_seed{seed}.npy", ems.agent.Q)
    np.save(MODELS / f"frl_visits_seed{seed}.npy", ems.agent.visits)
    pd.DataFrame(rows).to_csv(TABLES / f"frl_training_seed{seed}.csv", index=False, float_format="%.5f")
    return {"seed": seed, "train_time_s": time.time() - t0}


def policy_table(cfg, seeds) -> pd.DataFrame:
    """Her durumda öğrenilen açgözlü Δ (seed'ler arası çoğunluk) ve ziyaret sayısı."""
    ems = FRLEMS(cfg, seed=0)
    acts = ems.actions
    rows = []
    for s in range(36):
        picks, visits = [], 0
        for sd in seeds:
            ems.agent.Q = np.load(MODELS / f"frl_q_seed{sd}.npy")
            picks.append(acts[ems.agent.greedy(s, explore_ties=False)])
            visits += int(np.load(MODELS / f"frl_visits_seed{sd}.npy")[s].sum())
        vals, cnt = np.unique(picks, return_counts=True)
        sb, ssc, p = ems.state_terms(s)
        rows.append({"SoC_B": sb, "SoC_SC": ssc, "P_dem": p, "delta_mode": vals[cnt.argmax()],
                     "agree": f"{cnt.max()}/{len(seeds)}", "deltas": list(picks),
                     "visits_per_seed": visits // len(seeds)})
    return pd.DataFrame(rows)


def plot_curves(seeds):
    dfs = [pd.read_csv(TABLES / f"frl_training_seed{s}.csv") for s in seeds]
    fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
    for a, col, lbl in [(ax[0], "mean_reward", "Adım başına ortalama ödül"),
                        (ax[1], "mean_csc_traction", "Çekişte ortalama $C_{SC}$ [%]"),
                        (ax[2], "soc_sc_end", "Bölüm sonu SoC$_{SC}$")]:
        M = np.vstack([d[col].rolling(20, min_periods=1).mean().to_numpy() for d in dfs])
        m, s = M.mean(0), M.std(0)
        x = np.arange(len(m))
        a.plot(x, m, lw=1.4)
        a.fill_between(x, m - s, m + s, alpha=0.25)
        a.set_xlabel("Bölüm"); a.set_title(lbl, fontsize=10); a.grid(alpha=0.3)
    ax2 = ax[0].twinx()
    ax2.plot(dfs[0]["epsilon"], c="gray", ls="--", lw=0.8)
    ax2.set_ylabel("ε", color="gray")
    fig.suptitle(f"FRL öğrenme eğrileri ({len(seeds)} seed, ortalama ± std, 20 bölüm kayan ortalama)")
    fig.tight_layout()
    fig.savefig(FIG / "frl_learning_curve.png", dpi=150)


def main():
    ap = argparse.ArgumentParser()
    cfg = load_config()
    ap.add_argument("--episodes", type=int, default=cfg["frl"]["episodes"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    seeds = cfg["frl"]["seeds"]
    with Pool(a.workers) as pool:
        info = pool.map(train_seed, [(s, a.episodes) for s in seeds])
    for i in info:
        print(f"seed {i['seed']}: eğitim süresi {i['train_time_s']:.0f} s")
    plot_curves(seeds)
    pt = policy_table(cfg, seeds)
    pt.to_csv(TABLES / "frl_policy.csv", index=False)
    print(pt.to_string(index=False))
    print("\nKaydedildi: results/models/, results/tables/frl_training_seed*.csv, frl_policy.csv, "
          "results/figures/frl_learning_curve.png")


if __name__ == "__main__":
    main()
