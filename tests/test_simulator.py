"""Simülatör ve güvenlik katmanı testleri."""

import numpy as np
import pytest

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.simulator import EMS, BatteryOnlyEMS, Simulator


@pytest.fixture(scope="module")
def sim():
    cfg = load_config()
    return Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))


class GreedySC(EMS):
    """Güvenlik katmanını zorlamak için: her zaman talebin tamamını SC'den ister."""
    name = "greedy_sc"

    def sc_request(self, p_dem, soc_b, soc_sc):
        return p_dem


def _bus_balance(log):
    return log.p_b_bus + log.p_sc_bus + log.p_mech - log.p_dem


def test_bus_power_balance(sim):
    for ems in [BatteryOnlyEMS(False), BatteryOnlyEMS(True), GreedySC()]:
        log = sim.run(ems, soc_b=0.9, soc_sc=0.5, max_cycles=2).log
        np.testing.assert_allclose(_bus_balance(log), 0.0, atol=1e-9)
        assert (log.p_mech <= 1e-12).all()


def test_battery_only_no_regen(sim):
    log = sim.run(BatteryOnlyEMS(False), max_cycles=1).log
    brake = log.p_dem < 0
    assert (log.p_b_bus[brake] == 0).all()                    # D-07
    assert np.allclose(log.p_mech[brake], log.p_dem[brake])   # tamamı mekanik frene
    assert (log.p_sc == 0).all()


def test_safety_layer_limits_supercap(sim):
    """SC'den aşırı güç istense bile SoC_SC [0, 1] içinde kalmalı, eksik bataryadan gelmeli."""
    log = sim.run(GreedySC(), soc_b=0.9, soc_sc=0.3, max_cycles=3).log
    assert log.soc_sc.min() >= -1e-9 and log.soc_sc.max() <= 1 + 1e-9
    assert log.soc_sc.min() < 0.01                            # SC gerçekten boşaldı
    trac = log.p_dem > 0
    assert (log.p_b_bus[trac] > 0).any()                      # eksik güç bataryadan


def test_converter_losses(sim):
    """Deşarjda kaynak gücü bara gücünden η_c oranında büyük olmalı."""
    log = sim.run(BatteryOnlyEMS(False), max_cycles=1).log
    m = log.p_b_bus > 0
    np.testing.assert_allclose(log.p_b[m], log.p_b_bus[m] / sim.eta)


def test_long_discharge_stops_at_soc_min(sim):
    r = sim.run(BatteryOnlyEMS(False), max_cycles=20)
    assert r.discharge_time_s is not None
    assert r.log.soc_b.iloc[-1] <= sim.bat.soc_min < r.log.soc_b.iloc[-2]
