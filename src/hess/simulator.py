"""Zaman adımı simülatörü, DC/DC dönüştürücüler ve ortak güvenlik katmanı (plan §2.6–2.7).

Güç akışı (bara tarafı):   P_dem = P_B,bus + P_SC,bus + P_mek   (P_mek ≤ 0, yalnızca frenlemede)
Dönüştürücü (D-05, η_c):   deşarj: P_kaynak = P_bus / η_c,  şarj: P_kaynak = P_bus · η_c
D-15: Sadece-batarya durumunda da batarya aynı dönüştürücüden geçer (adil karşılaştırma).

Her EMS yalnızca süperkapasitörden istenen bara gücünü söyler (`sc_request`). Güvenlik
katmanı (D-06) bu isteği fiziksel sınırlara kırpar; kalan çekiş gücünü bataryaya,
kalan fren gücünü (izin varsa) bataryaya, yoksa mekanik frene verir. Katman bütün
EMS'ler için aynıdır.

D-20 (Adım 7.1): `sc_recharge = True` olan bir EMS çekişte/duruşta (P_dem ≥ 0) negatif
istek verebilir. Bu, bataryadan SC'ye şarj demektir: P_B,bus = P_dem + P_ch, P_SC,bus = −P_ch.
P_ch, SC'nin şarj sınırına ve bataryanın güç sınırına kırpılır. Bayrak kapalıysa (bütün
baseline'lar) negatif istek eskisi gibi 0'a kırpılır; baseline sonuçları değişmez.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .battery import Battery
from .supercap import Supercap
from .vehicle import Vehicle, demand_from_profile


# ---------------------------------------------------------------------------
class EMS:
    """EMS arayüzü. Alt sınıflar `sc_request` metodunu doldurur."""

    name = "base"
    battery_regen = False   # frenlemede batarya şarj edilebilir mi
    sc_recharge = False     # D-20: çekişte bataryadan SC'ye şarj istenebilir mi

    def reset(self) -> None:  # bölüm başında çağrılır (FRL için)
        pass

    def finish(self, soc_b: float, soc_sc: float) -> None:  # bölüm sonunda çağrılır (FRL için)
        pass

    def sc_request(self, p_dem: float, soc_b: float, soc_sc: float) -> float:
        """Süperkapasitörden istenen bara gücü [W] (çekişte ≥ 0, frenlemede ≤ 0).

        sc_recharge = True ise çekişte negatif değer = bataryadan SC'ye şarj gücü.
        """
        raise NotImplementedError


class BatteryOnlyEMS(EMS):
    """Sadece batarya. D-07: makaledeki gibi rejenerasyon yok; E6 için regen=True."""

    def __init__(self, regen: bool = False):
        self.battery_regen = regen
        self.name = "battery_only_regen" if regen else "battery_only"

    def sc_request(self, p_dem, soc_b, soc_sc):
        return 0.0


class TimedEMS(EMS):
    """Bir EMS'i sarar ve sc_request'in adım başına süresini ölçer (X6, E1 karar süresi).

    Bayrakları (battery_regen, sc_recharge) iç EMS'ten aynen alır.
    """

    def __init__(self, inner: EMS):
        self.inner, self.name = inner, inner.name
        self.battery_regen, self.sc_recharge = inner.battery_regen, inner.sc_recharge
        self.t, self.n = 0.0, 0

    def reset(self):
        self.t, self.n = 0.0, 0
        self.inner.reset()

    def finish(self, soc_b, soc_sc):
        self.inner.finish(soc_b, soc_sc)

    def sc_request(self, p, sb, ss):
        t0 = time.perf_counter()
        r = self.inner.sc_request(p, sb, ss)
        self.t += time.perf_counter() - t0
        self.n += 1
        return r

    @property
    def us(self) -> float:
        return 1e6 * self.t / max(self.n, 1)


# ---------------------------------------------------------------------------
@dataclass
class SimResult:
    ems: str
    log: pd.DataFrame
    discharge_time_s: float | None   # SoC_B min. sınıra inene kadar geçen süre
    distance_km: float


class Simulator:
    def __init__(self, cfg: dict, profile: pd.DataFrame):
        self.cfg = cfg
        self.dt = cfg["simulation"]["dt"]
        self.eta = cfg["converter"]["eta"]
        self.bat = Battery(cfg)
        self.sc = Supercap(cfg)
        d = demand_from_profile(Vehicle(cfg), profile)
        self.p_dem = d["p_dem"]
        self.v = d["v_mid"]
        self.n = len(self.p_dem)

    # ---- dönüştürücü ------------------------------------------------------
    def _to_source(self, p_bus: float) -> float:
        return p_bus / self.eta if p_bus >= 0 else p_bus * self.eta

    # ---- güvenlik katmanı (D-06) -----------------------------------------
    BAT_POWER_MARGIN = 0.9   # D-20: şarj sırasında batarya gücü V_oc²/(4R)'nin en çok %90'ı

    def _recharge_limit(self, p: float, p_ch: float) -> float:
        """İstenen şarj gücünü (bara tarafı, ≥ 0) SC ve batarya sınırlarına kırpar."""
        p_ch = min(p_ch, self.sc.max_charge_power(self.dt) / self.eta)
        p_bat_max = self.BAT_POWER_MARGIN * self.bat.max_power() * self.eta   # bara tarafı
        return max(min(p_ch, p_bat_max - p), 0.0)

    def _arbitrate(self, ems: EMS, p: float) -> tuple[float, float, float]:
        """(P_B,bus, P_SC,bus, P_mek) döndürür."""
        req = ems.sc_request(p, self.bat.soc, self.sc.soc)
        if p >= 0.0 and req < 0.0 and ems.sc_recharge:  # D-20: bataryadan SC şarjı
            p_ch = self._recharge_limit(p, -req)
            return p + p_ch, -p_ch, 0.0
        if p >= 0.0:  # çekiş
            req = min(max(req, 0.0), p)
            p_sc = min(req, self.sc.max_discharge_power(self.dt) * self.eta)
            return p - p_sc, p_sc, 0.0
        # frenleme: regen = bara tarafındaki geri kazanılabilir güç
        regen = -p
        acc = min(max(-req, 0.0), regen)
        acc = min(acc, self.sc.max_charge_power(self.dt) / self.eta)
        rest = regen - acc
        b_acc = 0.0
        if ems.battery_regen and rest > 0.0:
            headroom_wh = max(1.0 - self.bat.soc, 0.0) * self.bat.q_ah * self.bat.ocv(self.bat.soc)
            b_acc = min(rest, headroom_wh * 3600.0 / self.dt / self.eta)
        return -b_acc, -acc, -(rest - b_acc)   # P_mek ≤ 0: mekanik frende harcanan

    # ---- çalıştırma --------------------------------------------------------
    def run(self, ems: EMS, soc_b: float = 1.0, soc_sc: float = 1.0,
            max_cycles: int = 1, stop_at_soc_min: bool = True, log: bool = True) -> SimResult:
        """Profili en fazla `max_cycles` kez arka arkaya sürer.

        stop_at_soc_min=True ise SoC_B, soc_min'e inince durur (uzun deşarj testi, D-02).
        log=False: adım kaydı tutulmaz (FRL eğitiminde hız için); log yalnızca son adımı içerir.
        """
        self.bat.reset(soc_b)
        self.sc.reset(soc_sc)
        ems.reset()
        rows, t_end, dist_m = [], None, 0.0
        soc_min = self.bat.soc_min
        for cyc in range(max_cycles):
            for k in range(self.n):
                p = float(self.p_dem[k])
                dist_m += self.v[k] * self.dt
                p_b_bus, p_sc_bus, p_mech = self._arbitrate(ems, p)
                rb = self.bat.step(self._to_source(p_b_bus), self.dt)
                rs = self.sc.step(self._to_source(p_sc_bus), self.dt)
                row = (cyc * self.n + k, cyc, self.v[k], p, p_b_bus, p_sc_bus, p_mech,
                       rb["p_term"], rs["p_term"], rb["i"], rs["i"], rb["v_term"], rs["v"],
                       rb["soc"], rs["soc"], rb["temp"], rb["p_loss"], rs["p_loss"])
                if log or not rows:
                    rows.append(row)
                else:
                    rows[0] = row
                if stop_at_soc_min and self.bat.soc <= soc_min:
                    t_end = (cyc * self.n + k + 1) * self.dt
                    break
            if t_end is not None:
                break
        ems.finish(self.bat.soc, self.sc.soc)
        df = pd.DataFrame(rows, columns=[
            "t", "cycle", "v", "p_dem", "p_b_bus", "p_sc_bus", "p_mech",
            "p_b", "p_sc", "i_b", "i_sc", "v_b", "v_sc", "soc_b", "soc_sc", "temp_b",
            "loss_b", "loss_sc"])
        df["t"] = df["t"] * self.dt
        return SimResult(ems.name, df, t_end, dist_m / 1000.0)
