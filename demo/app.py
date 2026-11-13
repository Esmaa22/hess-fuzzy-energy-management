"""Canlı demo (Adım 8): FLC (makale) ile SCS-FLC (önerilen) yan yana.

Çalıştırma (repo kökünden):  streamlit run demo/app.py

Sekmeler:
  1. Tek karar        : girdiler kaydırıcıyla; bulanıklaştırma → kural ateşleme → birleştirme → centroid
  2. Karar yüzeyi     : seçilen çıktının P_dem × SoC_SC yüzeyi
  3. Sürüş simülasyonu: eğitim ya da test çevrimi, yöntemler yan yana, parametre ve gürültü kaydırıcıları
  4. Kayıtlı sonuçlar : X1–X5 grafikleri (results/figures)
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from hess import load_config
from hess.drive_cycle import generate_urban_profile, load_profile
from hess.flc_ems import FLCEMS
from hess.metrics import compute
from hess.simulator import BatteryOnlyEMS, NoisyEMS, Simulator
from hess.test_cycles import REGIMES
from hess.tuning import SPACES, load_tuned, make_ems, metric_args

# Grafik renkleri: sonuç grafikleriyle aynı (dataviz referans paleti, sabit sıra)
COLOR = {"F0": "#2a78d6", "C0": "#eb6834", "S1": "#1baf7a", "S2": "#eda100", "B1": "#a3a29b"}
NAME = {"F0": "F0 · FLC (makale, Tablo 5)", "C0": "C0 · Crisp eşik (ayarlı)",
        "S1": "S1 · SCS-FLC pay (önerilen)", "S2": "S2 · SCS-FLC tavan (önerilen, ana katkı)",
        "B1": "B1 · Sadece batarya + rejenerasyon"}
INK, MUTED, GRID = "#2b2b29", "#6b6a64", "#e4e3dd"
OUT_LABEL = {"c_b": "C_B [%]", "c_sc": "C_SC [%]", "p_ch": "P_ch [W]", "p_cap": "P_cap [W]"}
IN_LABEL = {"p_dem": "P_dem [W]", "soc_sc": "SoC_SC [%]", "soc_b": "SoC_B [%]"}

st.set_page_config(page_title="HESS bulanık EMS demo", layout="wide")


def full_width(fn, *args, **kw):
    """Tam genişlik: yeni Streamlit `width="stretch"`, eski sürümler `use_container_width`."""
    try:
        return fn(*args, width="stretch", **kw)
    except (TypeError, ValueError):
        return fn(*args, use_container_width=True, **kw)


# --------------------------------------------------------------------------- önbellek
@st.cache_resource
def base():
    cfg = load_config()
    return cfg, load_tuned()


@st.cache_data
def profile(kind: str, regime: str, seed: int) -> pd.DataFrame:
    cfg, _ = base()
    if kind == "train":
        return load_profile(ROOT / cfg["drive_cycle"]["file"])
    c = copy.deepcopy(cfg)
    c["drive_cycle"]["seed"] = seed
    return generate_urban_profile(c, micro_amp=REGIMES[regime])


def build(code: str, prm: dict | None = None):
    cfg, tuned = base()
    if code == "F0":
        return FLCEMS(cfg)
    if code == "B1":
        return BatteryOnlyEMS(True)
    return make_ems(code, cfg, prm or tuned[code])


def style(ax, grid="both"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    if grid:
        ax.grid(True, axis=grid if grid != "both" else "both", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def rule_text(r) -> str:
    a = " VE ".join(f"{v} = {t}" for v, t in r.antecedent.items())
    c = ", ".join(f"{v} = {t}" for v, t in r.consequent.items())
    return f"EĞER {a} İSE {c}"


# --------------------------------------------------------------------------- yan menü
cfg, tuned = base()
st.sidebar.title("HESS bulanık EMS")
st.sidebar.markdown(
    "**Makale:** Kumaresan & Rammohan, *Results in Engineering* 28 (2025) 107875.\n\n"
    "**Öneri:** SCS-FLC, SC enerjisini koruyan 12 kurallı bulanık EMS (P_dem, SoC_SC → "
    "C_SC veya P_cap, ve P_ch: bataryadan SC'ye şarj).")
st.sidebar.markdown("**Ayarlı parametreler** (`config/tuned.yaml`)")
st.sidebar.json(tuned, expanded=False)

tab1, tab2, tab3, tab4 = st.tabs(["1 · Tek karar", "2 · Karar yüzeyi", "3 · Sürüş simülasyonu",
                                  "4 · Kayıtlı sonuçlar"])

# --------------------------------------------------------------------------- 1. tek karar
with tab1:
    st.subheader("Bir zaman adımında bulanık çıkarım (Mamdani: min-AND, min-çıkarım, max-birleştirme, centroid)")
    c1, c2 = st.columns([1, 2.4])
    with c1:
        m = st.radio("Yöntem", ["F0", "S1", "S2"], format_func=NAME.get, key="t1m")
        p = st.slider("P_dem: talep edilen güç [W] (negatif = frenleme)", -5000, 5600, 4200, 100)
        ssc = st.slider("SoC_SC: süperkapasitör doluluğu [%]", 0, 100, 50)
        sb = st.slider("SoC_B: batarya doluluğu [%] (yalnızca F0 kullanır)", 20, 100, 80, disabled=m != "F0")
    ems = build(m)
    fis = ems.fis
    x = {"p_dem": float(p), "soc_sc": float(ssc)}
    if m == "F0":
        x["soc_b"] = float(sb)
    x = {v.name: x[v.name] for v in fis.inputs}
    w = fis.firing_strengths(**x)
    out = fis.evaluate(**x)
    req = ems.sc_request(float(p), sb / 100, ssc / 100)
    with c1:
        st.markdown("**Çıktılar (durulaştırılmış)**")
        for k, v in out.items():
            st.metric(OUT_LABEL[k], f"{v:,.1f}")
        if p >= 0:
            st.markdown(f"SC'den istenen bara gücü: **{req:,.0f} W** "
                        f"({'bataryadan SC şarjı' if req < 0 else 'tepe tıraşlama'})  \n"
                        f"Bataryadan istenen: **{p - req:,.0f} W** (güvenlik katmanından önce)")
        else:
            st.markdown(f"Frenleme: SC'ye istenen **{-req:,.0f} W**, kalanı mekanik frene.")
    with c2:
        n_in, n_out = len(fis.inputs), len(fis.outputs)
        fig, axs = plt.subplots(2, max(n_in, n_out), figsize=(11, 5.2))
        axs = np.atleast_2d(axs)
        for j, var in enumerate(fis.inputs):
            ax = axs[0, j]
            lo, hi = (-5100, 5600) if var.name == "p_dem" else (0, 100)
            xs = np.linspace(lo, hi, 600)
            mu = var.fuzzify(x[var.name])
            for k, (t, mf) in enumerate(var.terms.items()):
                col = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"][k % 4]
                ax.plot(xs, mf(xs), color=col, lw=1.8, label=f"{t}: {mu[t]:.2f}")
            ax.axvline(x[var.name], color=INK, lw=1.2, ls="--")
            ax.set_title(f"Girdi: {IN_LABEL[var.name]}", fontsize=9, color=INK, loc="left")
            ax.legend(fontsize=7, frameon=False, loc="center right" if var.name != "p_dem" else "upper left")
            ax.set_ylim(-0.03, 1.12)
            style(ax)
        for j in range(n_in, axs.shape[1]):
            axs[0, j].axis("off")
        agg = fis.aggregate(w)
        for j, var in enumerate(fis.outputs):
            ax = axs[1, j]
            for t, mfv in fis._out_mf[var.name].items():
                ax.plot(var.universe, mfv, color=GRID, lw=1)
            ax.fill_between(var.universe, agg[var.name], color=COLOR[m], alpha=0.45, lw=0)
            ax.plot(var.universe, agg[var.name], color=COLOR[m], lw=1.6)
            ax.axvline(out[var.name], color=INK, lw=1.5)
            ax.text(out[var.name], 1.05, f" centroid = {out[var.name]:,.1f}", fontsize=8, color=INK)
            ax.set_title(f"Çıktı: {OUT_LABEL[var.name]} (birleştirilmiş küme)", fontsize=9, color=INK, loc="left")
            ax.set_ylim(-0.03, 1.15)
            style(ax)
        for j in range(n_out, axs.shape[1]):
            axs[1, j].axis("off")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    fired = sorted([(wi, r) for wi, r in zip(w, fis.rules) if wi > 0], key=lambda t: -t[0])
    st.markdown(f"**Ateşlenen kurallar:** {len(fired)} / {len(fis.rules)}")
    full_width(st.dataframe, pd.DataFrame([{"Ateşleme gücü": round(wi, 3), "Kural": rule_text(r)}
                                           for wi, r in fired]), hide_index=True)

# --------------------------------------------------------------------------- 2. karar yüzeyi
with tab2:
    st.subheader("Karar yüzeyi: çıktının P_dem ve SoC_SC'ye göre değişimi")
    c1, c2 = st.columns([1, 2.4])
    with c1:
        m2 = st.radio("Yöntem", ["F0", "S1", "S2"], format_func=NAME.get, key="t2m")
        e2 = build(m2)
        outs = [o.name for o in e2.fis.outputs]
        o2 = st.radio("Çıktı", outs, format_func=OUT_LABEL.get)
        sb2 = st.slider("SoC_B [%] (F0 için)", 20, 100, 80, key="t2b", disabled=m2 != "F0")
        st.caption("Ruspini bölümlemesi nedeniyle yüzey sürekli; kural sınırlarında sıçrama yok. "
                   "Crisp kuralda (C0) aynı yüzey basamaklı olurdu.")
    P = np.linspace(0, 5600, 57)
    S = np.linspace(0, 100, 41)
    Z = np.zeros((len(S), len(P)))
    for i, s in enumerate(S):
        for j, pv in enumerate(P):
            xx = {"p_dem": pv, "soc_sc": s, "soc_b": float(sb2)}
            Z[i, j] = e2.fis.evaluate(**{v.name: xx[v.name] for v in e2.fis.inputs})[o2]
    with c2:
        fig, ax = plt.subplots(figsize=(9, 4.6))
        im = ax.imshow(Z, origin="lower", aspect="auto", extent=(P[0], P[-1], S[0], S[-1]), cmap="Blues")
        cs = ax.contour(P, S, Z, levels=6, colors=INK, linewidths=0.6)
        ax.clabel(cs, fontsize=7, fmt="%.0f")
        ax.set_xlabel("P_dem [W]", fontsize=8, color=MUTED)
        ax.set_ylabel("SoC_SC [%]", fontsize=8, color=MUTED)
        cb = fig.colorbar(im, ax=ax)
        cb.set_label(OUT_LABEL[o2], fontsize=8, color=MUTED)
        cb.ax.tick_params(labelsize=7, colors=MUTED)
        style(ax, grid=None)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

# --------------------------------------------------------------------------- 3. simülasyon
with tab3:
    st.subheader("Sürüş simülasyonu: aynı çevrimde yöntemler yan yana")
    c1, c2, c3 = st.columns(3)
    with c1:
        kind = st.radio("Çevrim", ["train", "test"],
                        format_func=lambda k: "Eğitim çevrimi (seed 7, ayarda kullanıldı)" if k == "train"
                        else "Test çevrimi (ayarda hiç kullanılmadı)")
        regime = st.selectbox("Rejim", list(REGIMES), index=2, disabled=kind == "train")
        seed = st.slider("Test çevrimi seed", 101, 110, 101, disabled=kind == "train")
    with c2:
        cond = st.radio("Koşul", ["long", "cycle"],
                        format_func=lambda k: "Uzun deşarj (SoC_B %100 → %20, ~2 saat)" if k == "long"
                        else "Tek çevrim (900 s)")
        soc_sc0 = st.slider("Başlangıç SoC_SC [%]", 0, 100, 100) / 100
        methods = st.multiselect("Yöntemler", ["B1", "F0", "C0", "S1", "S2"], default=["F0", "C0", "S2"],
                                 format_func=NAME.get)
    with c3:
        sigma = st.slider("Ölçüm gürültüsü σ (SoC_SC ve P_dem)", 0.0, 0.10, 0.0, 0.01)
        with st.expander("S2 parametreleri (ayarlı değerden başlar)"):
            s2 = {k: st.slider(k, float(lo), float(hi), float(tuned["S2"][k]), key=f"s2{k}")
                  for k, (lo, hi) in SPACES["S2"].items()}
        with st.expander("C0 parametreleri (ayarlı değerden başlar)"):
            c0 = {k: st.slider(k, float(lo), float(hi), float(tuned["C0"][k]), key=f"c0{k}")
                  for k, (lo, hi) in SPACES["C0"].items()}
    run = st.button("Çalıştır", type="primary")
    if run and methods:
        prof = profile(kind, regime, seed)
        sim = Simulator(cfg, prof)
        margs = metric_args(cfg, sim)
        kw = dict(max_cycles=30) if cond == "long" else dict(max_cycles=1, stop_at_soc_min=False)
        rows, logs = [], {}
        bar = st.progress(0.0)
        for i, mcode in enumerate(methods):
            e = build(mcode, s2 if mcode == "S2" else c0 if mcode == "C0" else None)
            if sigma > 0 and mcode != "B1":
                e = NoisyEMS(e, sigma, seed=0)
            r = sim.run(e, soc_sc=soc_sc0, **kw)
            mt = compute(r, **margs)
            logs[mcode] = r.log
            rows.append({"Yöntem": NAME[mcode], "Tepe I_B [A]": mt["peak_I"],
                         "%99 I_B [A]": np.percentile(r.log.i_b, 99), "RMS I_B [A]": mt["rms_I"],
                         "ΔT [°C]": mt["dT"], "Deşarj süresi [s]": mt["t_dis"],
                         "En düşük SoC_SC": mt["socsc_min"],
                         "SC boşaldı mı": "evet" if mt["socsc_min"] < 0.01 else "hayır"})
            bar.progress((i + 1) / len(methods))
        st.session_state["sim"] = (pd.DataFrame(rows), logs, cond)
    if "sim" in st.session_state:
        df, logs, cond_r = st.session_state["sim"]
        full_width(st.dataframe, df.style.format(precision=2), hide_index=True)
        fig, axs = plt.subplots(1, 3, figsize=(15, 3.8), gridspec_kw=dict(width_ratios=[1.5, 1.5, 1]))
        tscale = 3600 if cond_r == "long" else 1
        tl = "Zaman [saat]" if cond_r == "long" else "Zaman [s]"
        for mcode, L in logs.items():
            col = COLOR[mcode]
            ib = L.i_b.rolling(30, min_periods=1).max() if cond_r == "long" else L.i_b
            axs[0].plot(L.t / tscale, ib, color=col, lw=1.0 if cond_r == "long" else 0.9, label=mcode)
            axs[1].plot(L.t / tscale, L.soc_sc, color=col, lw=1.4, label=mcode)
            top = np.sort(L.i_b.to_numpy())[::-1][:300]
            axs[2].plot(np.arange(len(top)), top, color=col, lw=1.8, label=mcode)
        axs[0].set_title("Batarya akımı I_B [A]" + (" (30 s tepe)" if cond_r == "long" else ""),
                         fontsize=9, color=INK, loc="left")
        axs[1].set_title("SoC_SC", fontsize=9, color=INK, loc="left")
        axs[1].axhline(0.10, color=MUTED, lw=0.8, ls=":")
        axs[2].set_title("I_B süre eğrisi (en yüksek 300 adım)", fontsize=9, color=INK, loc="left")
        for a, xl in zip(axs, [tl, tl, "Sıra"]):
            a.set_xlabel(xl, fontsize=8, color=MUTED)
            style(a)
            a.legend(fontsize=7.5, frameon=False)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Ayarları seçip **Çalıştır**'a basın. Uzun deşarj yöntem başına ~1–3 s sürer.")

# --------------------------------------------------------------------------- 4. sonuçlar
with tab4:
    figs = [("X1_summary.png", "X1 · Ana karşılaştırma, eğitim çevrimi"),
            ("X1_soc_current.png", "X1 · SoC_SC ve akım süre eğrisi"),
            ("X2_ablation.png", "X2 · Ablasyonlar"),
            ("X3_generalization.png", "X3 · 30 test çevrimi"),
            ("X4_sensitivity.png", "X4 · Parametre duyarlılığı"),
            ("X5_noise.png", "X5 · Ölçüm gürültüsü"),
            ("reproduction_summary.png", "Yeniden üretim · makaleye göre")]
    for f, cap in figs:
        path = ROOT / "results" / "figures" / f
        if path.exists():
            st.markdown(f"**{cap}**")
            full_width(st.image, str(path))
