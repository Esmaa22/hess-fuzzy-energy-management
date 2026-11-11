"""Araç, batarya ve süperkapasitör modelleri için enerji korunumu ve sınır testleri."""

import numpy as np
import pytest

from hess import load_config
from hess.battery import Battery
from hess.drive_cycle import generate_urban_profile
from hess.supercap import Supercap
from hess.vehicle import Vehicle, demand_from_profile

DT = 1.0


@pytest.fixture(scope="module")
def cfg():
    return load_config()


# ---------------------------------------------------------------- araç
def test_vehicle_zero_at_rest(cfg):
    veh = Vehicle(cfg)
    assert veh.wheel_power(0.0, 0.0) == 0.0


def test_vehicle_kinetic_energy_closes_over_cycle(cfg):
    """Çevrim durarak başlayıp bittiği için eylemsizlik enerjisinin toplamı sıfır olmalı."""
    veh = Vehicle(cfg)
    df = generate_urban_profile(cfg)
    d = demand_from_profile(veh, df)
    f_in, f_aero, f_roll, _ = veh.forces(d["v_mid"], d["a"])
    e_inertia = np.sum(f_in * d["v_mid"]) * DT
    e_wheel = np.sum(d["p_wheel"]) * DT
    e_resist = np.sum((f_aero + f_roll) * d["v_mid"]) * DT
    assert abs(e_inertia) < 1e-6 * e_resist
    assert e_wheel == pytest.approx(e_resist, rel=1e-9)


def test_vehicle_regen_and_limit(cfg):
    veh = Vehicle(cfg)
    p, clipped = veh.dc_demand(np.array([15.0, 15.0]), np.array([3.0, -2.0]))
    assert p[0] == veh.p_max and clipped[0]
    assert p[1] == pytest.approx(-veh.regen * abs(veh.wheel_power(15.0, -2.0)))


# ---------------------------------------------------------------- batarya
def test_battery_pack_parameters(cfg):
    b = Battery(cfg)
    assert b.q_ah == pytest.approx(73.7)
    assert b.ocv(1.0) == pytest.approx(58.8)
    assert b.ocv(0.0) == pytest.approx(42.0)
    assert b.r == pytest.approx(0.030 * 14 / 22)
    assert b.nominal_wh == pytest.approx(3700, rel=0.01)   # makale: 3.7 kWh
    assert 3700 < b.capacity_wh < 4000                     # OCV eğrisinden fiziksel enerji


def test_battery_energy_balance(cfg):
    """Her adımda: kimyasal enerji = terminal enerjisi + I²R kaybı."""
    b = Battery(cfg)
    rng = np.random.default_rng(0)
    e_chem = e_term = e_loss = 0.0
    for p in rng.uniform(-3000, 6000, 500):
        r = b.step(p, DT)
        e_chem += r["e_chem"]
        e_term += p * DT
        e_loss += r["p_loss"] * DT
    assert e_chem == pytest.approx(e_term + e_loss, rel=1e-12)
    assert e_loss > 0


def test_battery_charge_counting(cfg):
    b = Battery(cfg)
    b.reset(0.8)
    i_sum = sum(b.step(2000.0, DT)["i"] * DT for _ in range(600))
    assert 0.8 - b.soc == pytest.approx(i_sum / (3600 * b.q_ah), rel=1e-12)


def test_battery_thermal(cfg):
    b = Battery(cfg)
    for _ in range(100):
        b.step(0.0, DT)
    assert b.temp == pytest.approx(b.t_amb)        # akım yoksa ısınma yok
    b.step(5000.0, DT)
    assert b.temp > b.t_amb


# ---------------------------------------------------------------- süperkapasitör
def test_supercap_parameters(cfg):
    sc = Supercap(cfg)
    assert sc.soc == pytest.approx(1.0)
    assert sc.voltage == pytest.approx(48.0)
    assert sc.usable_wh == pytest.approx(0.75 * 0.5 * 406 * 48**2 / 3600)   # ≈ 97.4 Wh
    sc.reset(0.0)
    assert sc.voltage == pytest.approx(24.0)


def test_supercap_energy_balance(cfg):
    sc = Supercap(cfg)
    sc.reset(0.5)
    e0 = sc.energy
    rng = np.random.default_rng(1)
    e_term = e_loss = 0.0
    for p in rng.uniform(-1500, 1500, 300):
        r = sc.step(p, DT)
        e_term += p * DT
        e_loss += r["p_loss"] * DT
    assert e0 - sc.energy == pytest.approx(e_term + e_loss, rel=1e-9)


def test_supercap_limits(cfg):
    """Güç sınırlarıyla sürülen süperkapasitör SoC [0, 1] dışına çıkmamalı."""
    sc = Supercap(cfg)
    sc.reset(0.05)
    sc.step(sc.max_discharge_power(DT), DT)
    assert sc.soc == pytest.approx(0.0, abs=1e-6)
    sc.reset(0.97)
    sc.step(-sc.max_charge_power(DT), DT)
    assert sc.soc == pytest.approx(1.0, abs=1e-6)


def test_supercap_max_discharge_high_soc(cfg):
    """Yüksek SoC'de sınır, maksimum güç aktarımı V²/(4·ESR) olmalı (enerji değil)."""
    sc = Supercap(cfg)
    for soc in [0.3, 0.6, 1.0]:
        sc.reset(soc)
        assert sc.max_discharge_power(DT) == pytest.approx(sc.voltage**2 / (4 * sc.esr))
