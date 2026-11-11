"""Sentetik şehir içi sürüş profili (A-01).

Makalenin [1] gerçek sürüş verisi paylaşılmadığı için, raporlanan istatistiklere
(900 s, 12.4 km, ort. 49.6 km/h, maks. 83 km/h, +2.7 / -2.6 m/s²) uyan bir profil
mikro-yolculuklardan üretilir:

    hızlan (a) -> seyret (v_c + mikro dalgalanma) -> yavaşla (d) -> dur (t_s)

Mikro dalgalanma (A-17): gerçek trafikteki gaz/fren salınımlarını temsil eden AR(1)
gürültüsü  x_k = φ·x_{k-1} + ε_k  (birim standart sapmaya normalize). Genlik
`micro_amp_mps`, tüketim makalenin sadece-batarya değerine (41.59 Wh/km) eşleşecek
şekilde bir kez kalibre edilmiştir (experiments/baseline/make_drive_cycle.py --calibrate).

Üç yolculuk uç değerleri birebir taşır (v=83 km/h, a=2.7, d=2.6). Diğer
yolculukların seyir hızları tek bir ölçek katsayısıyla çarpılır ve bu katsayı
bisection ile toplam mesafe hedefe eşit olacak şekilde bulunur. Seyir süreleri,
toplam süre hedefe eşit olacak şekilde yolculuklara ağırlıklarıyla dağıtılır.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

KMH = 1 / 3.6  # km/h -> m/s


@dataclass
class Trip:
    v_cruise: float      # [m/s]
    accel: float         # [m/s²]
    decel: float         # [m/s²] (pozitif)
    stop_s: int          # duruş süresi [s]
    cruise_weight: float # seyir süresinin paylaştırılmasında ağırlık
    fixed_speed: bool    # True ise hız kalibrasyonda ölçeklenmez (83 km/h yolculuğu)
    noise: np.ndarray | None = None  # birim std AR(1) dizisi (seyir için)


def _ar1(rng: np.random.Generator, n: int, phi: float) -> np.ndarray:
    """Birim standart sapmalı, durağan AR(1) dizisi."""
    x = np.empty(n)
    x[0] = rng.standard_normal()
    eps = rng.standard_normal(n) * np.sqrt(1.0 - phi * phi)
    for k in range(1, n):
        x[k] = phi * x[k - 1] + eps[k]
    return x


def _ramp(v_from: float, v_to: float, rate: float) -> list[float]:
    """v_from'dan v_to'ya her adımda en fazla `rate` değişerek giden hız dizisi (uç hariç)."""
    out, v = [], v_from
    step = rate if v_to > v_from else -rate
    while (v_to - v) * np.sign(step) > 1e-9:
        out.append(v)
        v = min(v + step, v_to) if step > 0 else max(v + step, v_to)
    return out


def _build(trips: list[Trip], scale: float, duration: int, v_cap: float,
           amp: float = 0.0, a_lim: float = 1.8, dt: float = 1.0):
    """Verilen ölçek katsayısıyla hız dizisini kurar. (hız dizisi, yeterli_süre_var) döndürür."""
    speeds = [min(t.v_cruise * (1.0 if t.fixed_speed else scale), v_cap) for t in trips]

    # Seyir dışındaki sabit süreler (hızlanma + yavaşlama + duruş)
    ramps_up = [_ramp(0.0, v, t.accel * dt) for t, v in zip(trips, speeds)]
    ramps_dn = [_ramp(v, 0.0, t.decel * dt) for t, v in zip(trips, speeds)]
    fixed = sum(len(u) + len(d) + t.stop_s for u, d, t in zip(ramps_up, ramps_dn, trips))
    free = duration - fixed
    if free < 5 * len(trips):
        return None, False

    # Seyir sürelerini ağırlıklarla dağıt; tam sayıya yuvarlama artığını sona ekle
    w = np.array([t.cruise_weight for t in trips])
    cruise = np.floor(free * w / w.sum()).astype(int)
    cruise[-1] += free - cruise.sum()

    v_series: list[float] = []
    for t, v, up, dn, n_c in zip(trips, speeds, ramps_up, ramps_dn, cruise):
        v_series += up
        # Seyirde mikro dalgalanma: amp · AR(1). sin(πk/n_c) zarfı dalgalanmayı seyrin
        # başında ve sonunda sıfıra indirir (rampalara geçişte sıçrama olmaz).
        # Ardışık hız farkı ±a_lim ile sınırlanır, tepe hız aşılmaz.
        k = np.arange(n_c)
        env = np.sin(np.pi * k / max(n_c, 1))
        target = np.minimum(v + amp * env * t.noise[:n_c], v_cap)
        cruise_v = np.empty(n_c)
        prev = v
        for j in range(n_c):
            prev = prev + np.clip(target[j] - prev, -a_lim * dt, a_lim * dt)
            cruise_v[j] = prev
        # son adımda seyir hızına dönüş (yavaşlama rampası v'den başlar)
        if n_c:
            cruise_v[-1] = prev + np.clip(v - prev, -a_lim * dt, a_lim * dt)
        v_series += list(cruise_v)
        v_series += dn
        v_series += [0.0] * t.stop_s
    return np.asarray(v_series[:duration]), True


def generate_urban_profile(cfg: dict, micro_amp: float | None = None) -> pd.DataFrame:
    """Config'teki `drive_cycle` bölümüne göre sentetik profili üretir.

    micro_amp verilirse config'teki `micro_amp_mps` yerine o kullanılır (kalibrasyon için).
    """
    c = cfg["drive_cycle"]
    amp = c["micro_amp_mps"] if micro_amp is None else micro_amp
    a_lim = c["micro_a_lim"]
    rng = np.random.default_rng(c["seed"])
    n = c["n_trips"]
    duration = int(c["duration_s"])
    v_cap = c["v_max_kmh"] * KMH

    trips = [
        Trip(
            v_cruise=rng.uniform(*c["cruise_kmh"]) * KMH,
            accel=rng.uniform(*c["accel_range"]),
            decel=rng.uniform(*c["decel_range"]),
            stop_s=int(rng.integers(c["stop_s"][0], c["stop_s"][1] + 1)),
            cruise_weight=rng.uniform(0.5, 1.5),
            fixed_speed=False,
        )
        for _ in range(n)
    ]
    # Uç değerleri taşıyan yolculuklar (farklı yolculuklara dağıtılır)
    i_v, i_a, i_d = rng.choice(n, size=3, replace=False)
    trips[i_v].v_cruise, trips[i_v].fixed_speed = v_cap, True
    trips[i_a].accel = c["a_max"]
    trips[i_d].decel = c["d_max"]
    for t in trips:
        t.noise = _ar1(rng, duration, c["micro_phi"])

    # Mesafe ölçek katsayısının bisection ile bulunması
    target_m = c["distance_km"] * 1000.0
    lo, hi = 0.5, 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        v, ok = _build(trips, mid, duration, v_cap, amp, a_lim)
        if not ok:          # süre yetmiyor -> hızlar çok yüksek
            hi = mid
            continue
        if v.sum() * 1.0 < target_m:
            lo = mid
        else:
            hi = mid
    v, ok = _build(trips, lo, duration, v_cap, amp, a_lim)
    if not ok:
        raise RuntimeError("Profil hedef süreye sığmıyor; n_trips veya stop_s küçültülmeli.")

    a = np.append(np.diff(v), 0.0)  # a_k = v_{k+1} - v_k  (Δt = 1 s)
    t = np.arange(len(v), dtype=float)
    return pd.DataFrame({"time_s": t, "speed_mps": v, "speed_kmh": v / KMH, "accel_mps2": a})


def profile_stats(df: pd.DataFrame, dt: float = 1.0) -> dict:
    """Makaledeki istatistiklerle karşılaştırılacak özet değerler."""
    v = df["speed_mps"].to_numpy()
    a = df["accel_mps2"].to_numpy()
    dist_km = v.sum() * dt / 1000.0
    dur = len(v) * dt
    return {
        "duration_s": dur,
        "distance_km": dist_km,
        "avg_speed_kmh": dist_km / (dur / 3600.0),
        "max_speed_kmh": v.max() / KMH,
        "max_accel_mps2": a.max(),
        "max_decel_mps2": -a.min(),
        "stop_fraction": float((v < 0.1).mean()),
    }


PAPER_STATS = {
    "duration_s": 900.0,
    "distance_km": 12.4,
    "avg_speed_kmh": 49.6,
    "max_speed_kmh": 83.0,
    "max_accel_mps2": 2.7,
    "max_decel_mps2": 2.6,
}


def load_profile(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)
