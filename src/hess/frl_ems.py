"""Bulanık pekiştirmeli öğrenme EMS'i (FRL): FLC + Q-learning düzeltmesi (plan §5).

Durum (D-10)  : (SoC_B, SoC_SC, P_dem) dilsel kategorileri, argmax üyelik -> 3·3·4 = 36
Eylem (D-11)  : Δ ∈ {−20, −10, 0, +10, +20} yüzde puan
                C_SC = clip(100·c_sc,FLC + Δ, 0, 100),  C_B = 100 − C_SC
                (c_sc,FLC: FLC'nin normalize SC payı, D-08)
Rejenerasyon  : RL devreye girmez, FLC kararı uygulanır (D-12; yalnızca Δ = 0 izinli)
Ödül (D-13)   : makale Denklem 5, ilk eşleşen koşul geçerli
Q güncellemesi: bir sonraki adımda (s' ve SoC_B(t+1) bilindiğinde) yapılır (D-19)
"""

from __future__ import annotations

import numpy as np

from .flc_ems import FLCEMS
from .qlearning import QLearningAgent

SOC_TERMS = ("Low", "Medium", "High")
P_TERMS = ("Low", "Medium", "High", "Regeneration")


def reward_paper(p: float, c_b: float, c_sc: float, soc_b_next: float, soc_min: float) -> float:
    """Makale Denklem 5 (D-13). Koşullar birbirini dışlamadığı için sıra önemli.

    Not: 4. koşul (C_SC = C_B) hiçbir zaman tetiklenmez; C_SC = C_B = 50 zaten 3. koşula girer.
    """
    if soc_b_next < soc_min:
        return -1.5
    if p < 0 and c_b == 0 and c_sc > 0:
        return 1.0
    if p > 0:
        if c_sc >= 50:
            return 0.5
        if c_sc == c_b:
            return 0.0
        if c_b >= 75:
            return -0.5
        if c_b > 0:
            return -1.0
    return 0.0


class FRLEMS(FLCEMS):
    name = "frl"

    def __init__(self, cfg: dict, seed: int | None = None, reward_fn=reward_paper):
        super().__init__(cfg)
        f = cfg["frl"]
        self.actions = np.asarray(f["actions"], dtype=float)
        self.a0 = int(np.flatnonzero(self.actions == 0)[0])
        self.soc_min = cfg["battery"]["soc_min"]
        self.reward_fn = reward_fn
        n_s, n_a = 36, len(self.actions)
        allowed = np.ones((n_s, n_a), bool)
        for s in range(n_s):
            if self.state_terms(s)[2] == "Regeneration":
                allowed[s] = False
                allowed[s, self.a0] = True
        self.agent = QLearningAgent(n_s, n_a, f["alpha"], f["gamma"], f["eps_start"],
                                    f["eps_decay"], f["eps_min"], allowed, self.a0, seed)
        self.train = False
        self.reset()

    # ---- durum ----------------------------------------------------------
    def state(self, p: float, soc_b: float, soc_sc: float) -> int:
        """Her girdi için üyelik derecesi en yüksek terim (argmax), tek indekse çevrilir."""
        mb = self.fis._in["soc_b"].fuzzify(100 * soc_b)
        ms = self.fis._in["soc_sc"].fuzzify(100 * soc_sc)
        mp = self.fis._in["p_dem"].fuzzify(p)
        ib = SOC_TERMS.index(max(mb, key=mb.get))
        isc = SOC_TERMS.index(max(ms, key=ms.get))
        ip = P_TERMS.index(max(mp, key=mp.get))
        return (ib * 3 + isc) * 4 + ip

    @staticmethod
    def state_terms(s: int) -> tuple[str, str, str]:
        return SOC_TERMS[s // 12], SOC_TERMS[(s // 4) % 3], P_TERMS[s % 4]

    # ---- bölüm yönetimi -------------------------------------------------
    def reset(self) -> None:
        self._prev = None            # (s, a, p, c_b, c_sc)
        self.ep_reward = 0.0
        self.ep_steps = 0
        self.ep_csc_sum = 0.0
        self.ep_trac_steps = 0

    def _learn(self, soc_b_now: float, s_next: int | None) -> None:
        if self._prev is None:
            return
        s, a, p, c_b, c_sc = self._prev
        r = self.reward_fn(p, c_b, c_sc, soc_b_now, self.soc_min)
        self.ep_reward += r
        if self.train:
            self.agent.update(s, a, r, s_next)

    def finish(self, soc_b, soc_sc) -> None:
        self._learn(soc_b, None)     # bölüm sonu: bootstrap yok
        self._prev = None

    # ---- karar ------------------------------------------------------------
    def sc_request(self, p_dem, soc_b, soc_sc):
        s = self.state(p_dem, soc_b, soc_sc)
        self._learn(soc_b, s)        # önceki adımın ödülü ve Q güncellemesi
        c_b_f, c_sc_f = self.decide(p_dem, soc_b, soc_sc)
        a = self.agent.act(s, self.train)
        if p_dem > 0:
            base = 100.0 * self.sc_share(p_dem, c_b_f, c_sc_f, self.regen_ref)
            c_sc = float(np.clip(base + self.actions[a], 0.0, 100.0))
            c_b = 100.0 - c_sc
            share = c_sc / 100.0
            self.ep_csc_sum += c_sc
            self.ep_trac_steps += 1
        else:                        # frenleme veya duruş: FLC kararı (D-12)
            c_b, c_sc = c_b_f, c_sc_f
            share = self.sc_share(p_dem, c_b, c_sc, self.regen_ref) if p_dem < 0 else 0.0
        self._prev = (s, a, p_dem, c_b, c_sc)
        self.ep_steps += 1
        return share * p_dem
