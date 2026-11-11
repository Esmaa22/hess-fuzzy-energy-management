"""Tablo tabanlı Q-learning ajanı (plan §5.3).

    Q[s,a] ← Q[s,a] + α · (r + γ · max_{a'∈A(s')} Q[s',a'] − Q[s,a])

Her durum için izinli eylem maskesi desteklenir (rejenerasyon durumlarında yalnızca
Δ = 0 izinli, D-12). Eşitlik bozma (D-18): eğitimde rastgele, değerlendirmede tercih
edilen eylem (Δ = 0, yani FLC kararı).
"""

from __future__ import annotations

import numpy as np


class QLearningAgent:
    def __init__(self, n_states: int, n_actions: int, alpha: float, gamma: float,
                 eps_start: float, eps_decay: float, eps_min: float,
                 allowed: np.ndarray | None = None, preferred_action: int = 0,
                 seed: int | None = None):
        self.Q = np.zeros((n_states, n_actions))
        self.alpha, self.gamma = alpha, gamma
        self.eps, self.eps_decay, self.eps_min = eps_start, eps_decay, eps_min
        self.allowed = np.ones((n_states, n_actions), bool) if allowed is None else allowed
        self.preferred = preferred_action
        self.rng = np.random.default_rng(seed)
        self.visits = np.zeros((n_states, n_actions), dtype=np.int64)

    def greedy(self, s: int, explore_ties: bool) -> int:
        acts = np.flatnonzero(self.allowed[s])
        q = self.Q[s, acts]
        best = acts[np.isclose(q, q.max(), rtol=0, atol=1e-12)]
        if len(best) == 1:
            return int(best[0])
        if explore_ties:
            return int(self.rng.choice(best))
        return self.preferred if self.preferred in best else int(best[0])

    def act(self, s: int, train: bool) -> int:
        """ε-greedy (train=True) veya açgözlü (train=False) eylem seçimi."""
        if train and self.rng.random() < self.eps:
            return int(self.rng.choice(np.flatnonzero(self.allowed[s])))
        return self.greedy(s, explore_ties=train)

    def update(self, s: int, a: int, r: float, s_next: int | None) -> float:
        """Q güncellemesi. s_next=None: bölüm sonu (bootstrap yok). TD hatasını döndürür."""
        target = r
        if s_next is not None:
            target += self.gamma * self.Q[s_next, self.allowed[s_next]].max()
        td = target - self.Q[s, a]
        self.Q[s, a] += self.alpha * td
        self.visits[s, a] += 1
        return td

    def decay_epsilon(self) -> None:
        self.eps = max(self.eps * self.eps_decay, self.eps_min)
