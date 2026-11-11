"""Boylamsal araç dinamiği ve DC bara güç talebi (plan §2.2).

    P_wheel = v · [ m·δ·a + ½·ρ·C_d·A·v² + m·g·C_r·cosθ + m·g·sinθ ]

Çekişte  : P_dem = min(P_wheel / (η_t·η_m), P_motor_max)
Frenlemede: P_dem = -α_rgb · |P_wheel|        (A-07: kayıplar α_rgb içinde)
"""

from __future__ import annotations

import numpy as np


class Vehicle:
    def __init__(self, cfg: dict):
        c = cfg["vehicle"]
        self.m = c["mass_kg"]
        self.delta = c["rot_mass_factor"]
        self.A = c["frontal_area_m2"]
        self.cd = c["drag_coeff"]
        self.cr = c["rolling_coeff"]
        self.rho = c["air_density"]
        self.theta = c["grade_rad"]
        self.eta_t = c["eta_transmission"]
        self.eta_m = c["eta_motor"]
        self.p_max = c["p_motor_max_w"]
        self.regen = c["regen_ratio"]
        self.g = c["g"]

    def forces(self, v, a):
        """Kuvvet bileşenleri [N]: (eylemsizlik, aerodinamik, yuvarlanma, eğim)."""
        v = np.asarray(v, dtype=float)
        a = np.asarray(a, dtype=float)
        f_inertia = self.m * self.delta * a
        f_aero = 0.5 * self.rho * self.cd * self.A * v**2
        # Yuvarlanma direnci yalnızca araç hareket halindeyken etkir
        f_roll = np.where(v > 0.0, self.m * self.g * self.cr * np.cos(self.theta), 0.0)
        f_grade = self.m * self.g * np.sin(self.theta) * np.ones_like(v)
        return f_inertia, f_aero, f_roll, f_grade

    def wheel_power(self, v, a):
        """Tekerlek gücü [W]. Pozitif: çekiş, negatif: frenleme."""
        return np.asarray(v, dtype=float) * sum(self.forces(v, a))

    def dc_demand(self, v, a):
        """DC baradan istenen güç P_dem [W] ve çekişin motor sınırına takılıp takılmadığı."""
        p_w = self.wheel_power(v, a)
        p_trac = p_w / (self.eta_t * self.eta_m)
        clipped = p_trac > self.p_max
        p_dem = np.where(p_w >= 0.0, np.minimum(p_trac, self.p_max), -self.regen * np.abs(p_w))
        return p_dem, clipped


def demand_from_profile(vehicle: Vehicle, df) -> dict:
    """Profilden adım adım P_dem dizisini üretir.

    Adım k'da araç v_k'dan v_{k+1}'e geçer: a_k = (v_{k+1} − v_k)/Δt. Güç, adımın
    ortalama hızı v̄_k = (v_k + v_{k+1})/2 ile hesaplanır. Böylece Σ m·δ·a_k·v̄_k·Δt
    = ½·m·δ·(v_N² − v_0²) olur ve kinetik enerji ayrıklaştırmada tam korunur.
    """
    v = df["speed_mps"].to_numpy()
    a = df["accel_mps2"].to_numpy()          # a_k = v_{k+1} − v_k (son adım 0)
    v_next = np.append(v[1:], v[-1])
    v_mid = 0.5 * (v + v_next)
    p_wheel = vehicle.wheel_power(v_mid, a)
    p_dem, clipped = vehicle.dc_demand(v_mid, a)
    return {"v_mid": v_mid, "a": a, "p_wheel": p_wheel, "p_dem": p_dem, "clipped": clipped}
