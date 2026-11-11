"""Batarya paketi: R_int eşdeğer devre + birinci dereceden termal model (plan §2.3–2.4).

Paket: n_s seri × n_p paralel hücre.
    V_oc(SoC) = n_s · OCV_cell(SoC)            (A-08, doğrusal ara değerleme)
    R         = R_cell · n_s / n_p              (A-09)
    P_b = V_oc·I − R·I²   ⇒   I = (V_oc − √(V_oc² − 4·R·P_b)) / (2R)
    SoC ← SoC − I·Δt / (3600·Q)
Termal (A-10), hücre başına:
    m_c·c_p·dT/dt = I_cell²·R_cell − hA·(T − T_amb)
İşaret kuralı: P_b > 0 deşarj, P_b < 0 şarj.
"""

from __future__ import annotations

import numpy as np


class Battery:
    def __init__(self, cfg: dict):
        c = cfg["battery"]
        self.ns, self.np_ = c["n_series"], c["n_parallel"]
        self.q_ah = c["cell_capacity_ah"] * self.np_
        self.r_cell = c["cell_r_ohm"]
        self.r = self.r_cell * self.ns / self.np_
        self.soc_min = c["soc_min"]
        self.v_nom_cell = c["nominal_cell_v"]
        self._ocv_soc = np.asarray(c["ocv_soc"], dtype=float)
        self._ocv_v = np.asarray(c["ocv_v"], dtype=float)
        th = c["thermal"]
        self.m_c, self.cp = th["cell_mass_kg"], th["cp"]
        self.t_amb, self.hA = th["t_amb_c"], th["hA"]
        self.reset(c["soc_init"])

    # ---- durum -------------------------------------------------------------
    def reset(self, soc: float, temp_c: float | None = None) -> None:
        self.soc = float(soc)
        self.temp = self.t_amb if temp_c is None else float(temp_c)

    @property
    def nominal_wh(self) -> float:
        """Makalenin tanımıyla paket enerjisi: Q · n_s · V_nom (≈ 3.71 kWh). Menzil için."""
        return self.q_ah * self.ns * self.v_nom_cell

    @property
    def capacity_wh(self) -> float:
        """OCV eğrisinden fiziksel enerji: Q · ortalama V_oc (≈ 3.87 kWh)."""
        s = np.linspace(0, 1, 201)
        return self.q_ah * float(np.mean(self.ocv(s)))

    def ocv(self, soc):
        return self.ns * np.interp(soc, self._ocv_soc, self._ocv_v)

    def max_power(self) -> float:
        """Devrenin verebileceği en büyük güç V_oc²/(4R) (kök altı sıfır)."""
        v = self.ocv(self.soc)
        return v * v / (4.0 * self.r)

    # ---- bir zaman adımı ---------------------------------------------------
    def current(self, p_b: float) -> float:
        v = self.ocv(self.soc)
        disc = v * v - 4.0 * self.r * p_b
        if disc < 0:
            raise ValueError(f"Batarya {p_b:.0f} W veremez (sınır {self.max_power():.0f} W)")
        return (v - np.sqrt(disc)) / (2.0 * self.r)

    def step(self, p_b: float, dt: float) -> dict:
        """P_b gücünü dt boyunca uygular, durumu günceller, adım bilgilerini döndürür."""
        v_oc = float(self.ocv(self.soc))
        i = float(self.current(p_b))
        p_loss = i * i * self.r

        self.soc -= i * dt / (3600.0 * self.q_ah)

        i_cell = i / self.np_
        q_gen = i_cell * i_cell * self.r_cell
        self.temp += (q_gen - self.hA * (self.temp - self.t_amb)) / (self.m_c * self.cp) * dt

        return {
            "i": i,
            "v_oc": v_oc,
            "v_term": v_oc - i * self.r,
            "p_term": p_b,
            "p_loss": p_loss,
            "e_chem": v_oc * i * dt,   # kimyasal enerjideki azalma [J]
            "soc": self.soc,
            "temp": self.temp,
        }
