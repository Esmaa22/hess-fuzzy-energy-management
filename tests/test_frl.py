"""Q-learning ve FRL testleri."""

import numpy as np
import pytest

from hess import ROOT, load_config
from hess.drive_cycle import load_profile
from hess.flc_ems import FLCEMS
from hess.frl_ems import FRLEMS, reward_paper
from hess.qlearning import QLearningAgent
from hess.simulator import Simulator


def test_q_update_math():
    ag = QLearningAgent(2, 2, alpha=0.1, gamma=0.9, eps_start=0, eps_decay=1, eps_min=0)
    ag.Q[1] = [2.0, 5.0]
    ag.update(0, 1, r=1.0, s_next=1)
    assert ag.Q[0, 1] == pytest.approx(0.1 * (1.0 + 0.9 * 5.0))
    ag.update(0, 0, r=-1.0, s_next=None)          # terminal
    assert ag.Q[0, 0] == pytest.approx(-0.1)


def test_mask_and_tie_break():
    allowed = np.array([[False, True, False]])
    ag = QLearningAgent(1, 3, 0.1, 0.9, 1.0, 1, 1.0, allowed=allowed, preferred_action=1, seed=0)
    assert all(ag.act(0, train=True) == 1 for _ in range(50))   # yalnızca izinli eylem
    ag2 = QLearningAgent(1, 5, 0.1, 0.9, 0.0, 1, 0.0, preferred_action=2)
    assert ag2.act(0, train=False) == 2                          # eşitlikte Δ = 0


@pytest.mark.parametrize("p,cb,csc,soc,r", [
    (1000, 40, 60, 0.5, 0.5), (1000, 50, 50, 0.5, 0.5), (1000, 75, 25, 0.5, -0.5),
    (1000, 100, 0, 0.5, -0.5), (1000, 55, 45, 0.5, -1.0), (-500, 0, 20, 0.5, 1.0),
    (-500, 0, 0, 0.5, 0.0), (1000, 40, 60, 0.19, -1.5)])
def test_reward_paper(p, cb, csc, soc, r):
    assert reward_paper(p, cb, csc, soc, 0.2) == r


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_state_indexing(cfg):
    e = FRLEMS(cfg, seed=0)
    assert e.state_terms(e.state(500, 0.1, 0.1)) == ("Low", "Low", "Low")
    assert e.state_terms(e.state(5000, 0.9, 0.5)) == ("High", "Medium", "High")
    assert e.state_terms(e.state(-2000, 0.5, 0.9)) == ("Medium", "High", "Regeneration")
    assert len({e.state(p, b, c) for p in (-2000, 500, 2500, 5000)
                for b in (0.1, 0.5, 0.9) for c in (0.1, 0.5, 0.9)}) == 36


def test_untrained_frl_equals_flc(cfg):
    """Q tablosu sıfırken açgözlü FRL her durumda Δ = 0 seçer -> FLC ile birebir aynı."""
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    a = sim.run(FLCEMS(cfg), max_cycles=1).log
    b = sim.run(FRLEMS(cfg, seed=0), max_cycles=1).log
    np.testing.assert_allclose(a.p_sc_bus, b.p_sc_bus, atol=1e-9)


def test_training_updates_q(cfg):
    sim = Simulator(cfg, load_profile(ROOT / cfg["drive_cycle"]["file"]))
    e = FRLEMS(cfg, seed=0)
    e.train = True
    sim.run(e, soc_b=0.8, soc_sc=0.8, max_cycles=1, log=False)
    assert np.count_nonzero(e.agent.Q) > 0
    reg = [s for s in range(36) if e.state_terms(s)[2] == "Regeneration"]
    assert (e.agent.Q[reg][:, [0, 1, 3, 4]] == 0).all()   # rejenerasyonda yalnızca Δ = 0
