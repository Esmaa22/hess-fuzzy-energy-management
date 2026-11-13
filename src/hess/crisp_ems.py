"""C0: kesin (crisp) eşikli tepe tıraşlama + bataryadan SC şarjı (bulanık olmayan kontrol grubu).

CP4 ön denemesindeki kuralın (experiments/proposed/probe_crisp_threshold.py) paket hâli.
S1 (SCS-FLC) ile aynı fikir, aynı simülatör yolu (D-20); fark yalnızca kararın keskin
eşiklerle verilmesi. Böylece "bulanıklık" etkisi tek başına ölçülebiliyor (K4).

Kural (P: bara talebi [W], SoC_SC ∈ [0, 1]):
  P > P_th                        -> SC, P − P_th kadarını karşılar (tepe tıraşlama)
  P < 0                           -> frenleme enerjisinin tamamı SC'ye istenir
  0 ≤ P < P_lo  ve  SoC_SC < hedef -> batarya SC'yi P_ch ile şarj eder
"""

from __future__ import annotations

from .simulator import EMS


class CrispEMS(EMS):
    battery_regen = False
    sc_recharge = True

    def __init__(self, p_th: float, p_lo: float, p_ch: float, target: float, name: str = "crisp"):
        self.p_th, self.p_lo, self.p_ch, self.target = p_th, p_lo, p_ch, target
        self.name = name

    @classmethod
    def from_params(cls, prm: dict, name: str = "crisp") -> "CrispEMS":
        return cls(prm["p_th"], prm["p_lo"], prm["p_ch"], prm["target"], name=name)

    def sc_request(self, p, soc_b, soc_sc):
        if p < 0.0:
            return p
        if p > self.p_th:
            return p - self.p_th
        if p < self.p_lo and soc_sc < self.target:
            return -self.p_ch
        return 0.0
