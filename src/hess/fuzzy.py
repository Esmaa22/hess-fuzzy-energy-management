"""Genel amaçlı Mamdani bulanık çıkarım motoru (plan §4.3).

Adımlar:
  1. Bulanıklaştırma (fuzzification): her girdi için her dilsel terimin üyelik derecesi
  2. Kural ateşleme gücü: öncül terimlerin AND'i  -> min
  3. Çıkarım (implication): sonuç kümesinin ateşleme gücüyle kırpılması -> min
  4. Birleştirme (aggregation): kırpılmış kümelerin birleşimi -> max
  5. Durulaştırma (defuzzification): ağırlık merkezi (centroid), ayrık evren üzerinde

Hazır kütüphane kullanılmadı: her adım açık ve test edilebilir olsun diye.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

MF = Callable[[np.ndarray | float], np.ndarray]


# --------------------------------------------------------------------------- üyelik fonksiyonları
def trapmf(a: float, b: float, c: float, d: float) -> MF:
    """Yamuk üyelik fonksiyonu. a = b (sol omuz) veya c = d (sağ omuz) olabilir.

        μ(x) = 0                 x ≤ a  veya  x ≥ d
               (x − a)/(b − a)   a < x < b
               1                 b ≤ x ≤ c
               (d − x)/(d − c)   c < x < d
    Omuzlarda (a = b veya c = d) evrenin ucundaki değer 1 kabul edilir.
    """
    if not (a <= b <= c <= d):
        raise ValueError(f"trapmf için a ≤ b ≤ c ≤ d olmalı: {(a, b, c, d)}")

    def mu(x):
        x = np.asarray(x, dtype=float)
        y = np.zeros_like(x)
        y = np.where((x >= b) & (x <= c), 1.0, y)
        if b > a:
            m = (x > a) & (x < b)
            y = np.where(m, (x - a) / (b - a), y)
        if d > c:
            m = (x > c) & (x < d)
            y = np.where(m, (d - x) / (d - c), y)
        return y

    mu.params = ("trap", a, b, c, d)
    return mu


def trimf(a: float, b: float, c: float) -> MF:
    """Üçgen üyelik fonksiyonu: tepe b'de, taban [a, c]."""
    return trapmf(a, b, b, c)


# --------------------------------------------------------------------------- değişkenler ve kurallar
@dataclass
class FuzzyVariable:
    name: str
    terms: dict[str, MF]
    universe: np.ndarray | None = None   # yalnızca çıktılar için gerekli (durulaştırma)
    clip: tuple[float, float] | None = None  # girdinin kırpılacağı aralık

    def fuzzify(self, x: float) -> dict[str, float]:
        if self.clip is not None:
            x = min(max(x, self.clip[0]), self.clip[1])
        return {t: float(mf(x)) for t, mf in self.terms.items()}


@dataclass
class Rule:
    """EĞER girdi1 = t1 VE girdi2 = t2 ... İSE çıktı1 = u1, çıktı2 = u2"""
    antecedent: dict[str, str]
    consequent: dict[str, str]


@dataclass
class MamdaniFIS:
    inputs: list[FuzzyVariable]
    outputs: list[FuzzyVariable]
    rules: list[Rule]
    _out_mf: dict = field(init=False, repr=False)

    def __post_init__(self):
        self._in = {v.name: v for v in self.inputs}
        self._out = {v.name: v for v in self.outputs}
        for r in self.rules:  # kural tutarlılığı
            for var, term in r.antecedent.items():
                assert term in self._in[var].terms, (var, term)
            for var, term in r.consequent.items():
                assert term in self._out[var].terms, (var, term)
        # Çıktı üyelik fonksiyonlarını evren üzerinde bir kez hesapla
        self._out_mf = {o.name: {t: mf(o.universe) for t, mf in o.terms.items()}
                        for o in self.outputs}

    def firing_strengths(self, **x: float) -> np.ndarray:
        """Her kuralın ateşleme gücü: öncül üyelik derecelerinin min'i (AND)."""
        mu = {name: self._in[name].fuzzify(val) for name, val in x.items()}
        return np.array([min(mu[v][t] for v, t in r.antecedent.items()) for r in self.rules])

    def aggregate(self, w: np.ndarray) -> dict[str, np.ndarray]:
        """Her çıktı için birleştirilmiş küme: max_r min(w_r, μ_sonuç_r(y))."""
        agg = {}
        for o in self.outputs:
            # Aynı sonuç terimine sahip kurallardan en güçlüsü yeterli (max-min eşdeğeri)
            strength = {t: 0.0 for t in o.terms}
            for wr, r in zip(w, self.rules):
                t = r.consequent[o.name]
                if wr > strength[t]:
                    strength[t] = wr
            y = np.zeros_like(o.universe)
            for t, s in strength.items():
                if s > 0.0:
                    y = np.maximum(y, np.minimum(s, self._out_mf[o.name][t]))
            agg[o.name] = y
        return agg

    def defuzzify(self, name: str, mu: np.ndarray) -> float:
        """Ağırlık merkezi: Σ y·μ(y) / Σ μ(y). Hiç kural ateşlenmezse NaN."""
        s = mu.sum()
        if s <= 0.0:
            return float("nan")
        val = float((self._out[name].universe * mu).sum() / s)
        c = self._out[name].clip
        return min(max(val, c[0]), c[1]) if c else val

    def evaluate(self, **x: float) -> dict[str, float]:
        w = self.firing_strengths(**x)
        agg = self.aggregate(w)
        return {name: self.defuzzify(name, mu) for name, mu in agg.items()}

    def explain(self, **x: float) -> list[tuple[float, Rule]]:
        """Ateşlenen kurallar ve güçleri (canlı demo ve savunma için)."""
        w = self.firing_strengths(**x)
        return sorted([(float(wi), r) for wi, r in zip(w, self.rules) if wi > 0],
                      key=lambda t: -t[0])
