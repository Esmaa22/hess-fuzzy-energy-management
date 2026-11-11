"""Süperkapasitör paketi: ideal kapasitör + seri direnç (ESR) (plan §2.5).

    V_c = √(2E/C),  P_sc = V_c·I − ESR·I²  ⇒  I = (V_c − √(V_c² − 4·ESR·P_sc)) / (2·ESR)
    E ← E − V_c·I·Δt                     (kapasitörde depolanan enerji)
SoC (D-04, enerji tabanlı, V_min = V_max/2):
    SoC = (V² − V_min²) / (V_max² − V_min²)  =  (E − E_min) / (E_max − E_min)
İşaret kuralı: P_sc > 0 deşarj, P_sc < 0 şarj.
"""

from __future__ import annotations

import numpy as np


class Supercap:
    def __init__(self, cfg: dict):
        c = cfg["supercap"]
        self.C = c["capacitance_f"]
        self.v_max = c["v_max"]
        self.v_min = self.v_max / 2.0
        self.esr = c["esr_ohm"]
        self.e_max = 0.5 * self.C * self.v_max**2
        self.e_min = 0.5 * self.C * self.v_min**2
        self.reset(c["soc_init"])

    # ---- durum -------------------------------------------------------------
    def reset(self, soc: float) -> None:
        self.energy = self.e_min + float(soc) * (self.e_max - self.e_min)

    @property
    def soc(self) -> float:
        return (self.energy - self.e_min) / (self.e_max - self.e_min)

    @property
    def voltage(self) -> float:
        return float(np.sqrt(2.0 * self.energy / self.C))

    @property
    def usable_wh(self) -> float:
        return (self.e_max - self.e_min) / 3600.0

    # ---- güç sınırları (güvenlik katmanı D-06 bunları kullanır) ------------
    def max_discharge_power(self, dt: float) -> float:
        """SoC = 0'ın altına inmeden dt boyunca verilebilecek en büyük terminal gücü."""
        p_int = max(self.energy - self.e_min, 0.0) / dt     # enerjiden gelen iç güç sınırı
        v = self.voltage
        # Akım hem enerji sınırıyla hem de maksimum güç aktarım noktası I = V/(2·ESR) ile
        # sınırlıdır. Bu noktanın ötesinde akım artarsa terminal gücü azalır.
        i = min(p_int / v, v / (2.0 * self.esr))
        return max(0.0, v * i - self.esr * i * i)

    def max_charge_power(self, dt: float) -> float:
        """SoC = 1'i aşmadan dt boyunca kabul edilebilecek en büyük şarj gücü (pozitif değer)."""
        p_int = max(self.e_max - self.energy, 0.0) / dt
        v = self.voltage
        i = p_int / v
        return p_int + self.esr * i * i   # terminalden daha fazlası gelmeli (ESR kaybı)

    # ---- bir zaman adımı ---------------------------------------------------
    def current(self, p_sc: float) -> float:
        v = self.voltage
        disc = v * v - 4.0 * self.esr * p_sc
        if disc < 0:
            raise ValueError(f"Süperkapasitör {p_sc:.0f} W veremez")
        return (v - np.sqrt(disc)) / (2.0 * self.esr)

    def step(self, p_sc: float, dt: float) -> dict:
        v = self.voltage
        i = float(self.current(p_sc))
        e_int = v * i * dt
        self.energy -= e_int
        # Sayısal yuvarlamayla sınırların hafifçe aşılmasını engelle
        self.energy = min(max(self.energy, self.e_min), self.e_max)
        return {
            "i": i,
            "v": v,
            "p_term": p_sc,
            "p_loss": self.esr * i * i,
            "e_int": e_int,
            "soc": self.soc,
        }
