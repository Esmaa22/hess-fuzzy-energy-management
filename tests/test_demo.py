"""Canlı demonun (demo/app.py) hatasız açıldığını ve temel etkileşimlerin çalıştığını kontrol eder."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "demo" / "app.py")


def test_demo_tabs_and_single_decision():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    for m in ("S1", "S2", "F0"):
        at.radio(key="t1m").set_value(m).run()
        assert not at.exception
        assert len(at.metric) == 2
    at.radio(key="t2m").set_value("S2").run()
    assert not at.exception


def test_demo_simulation_first_cycle():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    kosul = [r for r in at.radio if r.label == "Koşul"][0]
    kosul.set_value("cycle").run()                 # tek çevrim (hızlı)
    at.button[0].click().run()
    assert not at.exception
    df = at.dataframe[-1].value
    assert len(df) == 3 and (df["Tepe I_B [A]"] > 0).all()
