"""X2 ablasyonları (CP4 §4 ve §10 bulgu 5). Ayarlı parametreler config/tuned.yaml'dan gelir;
ablasyonlar yeniden ayarlanmaz (her biri tek bir bileşeni çıkarır ya da değiştirir).

  A1  S1/S2, P_ch = 0           → yeniden şarjın katkısı          (tuning.make_ems(recharge=False))
  A2  Tablo 5 FLC + S1'in P_ch'si → kural tabanı değişikliğinin katkısı   (FLCRechargeEMS)
  A3  S1/S2 + SoC_B girdisi (36 kural) → SoC_B gerekli mi?        (tuning.make_ems(soc_b=True))
  A4  S2, d_cap = 0 (sabit tavan) → SoC'ye uyarlanan tavanın katkısı  (tuning.make_ems, d_cap=0)
  A5  S2'nin tavanı + C0'ın crisp şarj kuralı → bulanık şarj yasasının katkısı (S2CrispChargeEMS)
"""

from __future__ import annotations

from .flc_ems import FLCEMS
from .scs_flc import SCSFLCCapEMS, SCSFLCEMS
from .simulator import EMS
from .tuning import s1_overrides, s2_overrides


class FLCRechargeEMS(EMS):
    """A2: referans FLC'nin (Tablo 5) çekiş/frenleme kararı + S1'in P_ch çıktısı."""

    battery_regen = False
    sc_recharge = True

    def __init__(self, cfg: dict, s1_prm: dict, name: str = "A2"):
        self.flc = FLCEMS(cfg)
        self.s1 = SCSFLCEMS(cfg, overrides=s1_overrides(cfg, **s1_prm))
        self.name = name

    def sc_request(self, p_dem, soc_b, soc_sc):
        req = self.flc.sc_request(p_dem, soc_b, soc_sc)
        if p_dem >= 0.0:
            req -= self.s1.decide(p_dem, soc_sc)[1]
        return req


class S2CrispChargeEMS(EMS):
    """A5: S2'nin bulanık tavanı + C0'ın keskin şarj kuralı (P < P_lo ve SoC_SC < hedef → P_ch)."""

    battery_regen = False
    sc_recharge = True

    def __init__(self, cfg: dict, s2_prm: dict, c0_prm: dict, name: str = "A5"):
        self.s2 = SCSFLCCapEMS(cfg, overrides=s2_overrides(cfg, **s2_prm))
        self.c0 = c0_prm
        self.name = name

    def sc_request(self, p_dem, soc_b, soc_sc):
        if p_dem < 0.0:
            return p_dem
        req = max(p_dem - self.s2.decide(p_dem, soc_sc)[0], 0.0)
        if p_dem < self.c0["p_lo"] and soc_sc < self.c0["target"]:
            req -= self.c0["p_ch"]
        return req
