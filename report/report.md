---
lang: tr
mainfont: Liberation Serif
monofont: DejaVu Sans Mono
fontsize: 11pt
geometry: "a4paper,margin=2.3cm"
linestretch: 1.15
colorlinks: true
linkcolor: black
urlcolor: blue
---

```{=latex}
\begin{titlepage}
\centering
\vspace*{1.5cm}
{\large İstanbul Üniversitesi-Cerrahpaşa\\Mühendislik Fakültesi -- Bilgisayar Mühendisliği Bölümü\par}
\vspace{0.8cm}
{\large Bulanık Mantık Dersi -- Dönem Projesi Teknik Raporu\par}
\vspace{2cm}
{\LARGE\bfseries Elektrikli İki Tekerlekli Araçlarda Batarya/Süperkapasitör\\Hibrit Enerji Depolama Sistemi için Bulanık Takviyeli\\Öğrenme Tabanlı Enerji Yönetimi:\\[0.3em] Yeniden Gerçekleştirme ve SoC-Duyarlı Bulanık Şarj Yasası ile Geliştirme\par}
\vspace{1.5cm}
{\normalsize\itshape Referans makale: N. Kumaresan ve A. Rammohan, ``Fuzzy reinforcement learning-based energy management strategy for the integration of hybrid energy storage system of electric vehicle,'' \textit{Results in Engineering}, c. 28, 107875, 2025.\par}
\vfill
\begin{tabular}{ll}
\textbf{Öğrenci} & Esma Mutlu \\
\textbf{Öğrenci No} & 1306220051 \\
\textbf{Dersin Yürütücüsü} & Prof. Dr. Rüya Şamlı \\
\textbf{GitHub} & \url{https://github.com/Esmaa22/hess-fuzzy-energy-management} \\
\end{tabular}
\vspace{1.5cm}

{\large Kasım 2026\par}
\end{titlepage}
```

# Özet {.unnumbered}

> **[9.5'te yazılacak]** 150–200 kelime: problem, yeniden üretim, temel bulgular (literal FLC'de SC'nin tükenmesi, FRL > FLC'nin yeniden üretilememesi), katkı (S2 SCS-FLC), sayısal sonuçlar (30 görülmemiş çevrimde tepe akım, çöküş sayıları, p-değeri) ve dürüst olumsuz bulgu (uyarlamalı tavanın katkısı yok).

**Anahtar kelimeler:** bulanık mantık, Mamdani çıkarımı, fuzzy Q-learning, hibrit enerji depolama, süperkapasitör, enerji yönetim stratejisi, elektrikli iki tekerlekli araç

```{=latex}
\tableofcontents
\newpage
```

# Introduction (Giriş)

> **[9.3]** Problem (şehir içi E2W sürüşünde batarya akım tepeleri, ısınma, yaşlanma), HESS çözümü, EMS karar problemi. Bulanık mantığın kullanılma nedeni. Çalışmanın amacı ve kapsamı (MRR: Mamdani FLC + tablo Q-learning FRL + araç/batarya/SC modelleri + en az bir deney). Katkıların madde madde listesi. Raporun düzeni. *(~0.6 sayfa)*

# Related Work (İlgili Çalışmalar)

> **[9.3]** `references/README.md` sentezine dayanır: kural tabanlı ve optimize FLC [11], [12], [15]; tablo/hiyerarşik Q-learning [3], [4], [8]; derin RL [9], [10]; fuzzy RL [2], [5]–[7]; aynı grubun ANFIS çalışması [13]; meta-kural [14]; derleme [16]. Karşılaştırmalı tablo (Tablo 1, kısaltılmış). Projenin konumu. *(~1 sayfa)*

# Theoretical Background (Teorik Altyapı)

> **[9.3]** Bulanık küme ve üyelik fonksiyonu [17]; dilsel değişken; bulanıklaştırma; kural tabanı; Mamdani çıkarımı (min–max) [18]; ağırlık merkezi ile durulaştırma (denklem). Sugeno ile kısa karşılaştırma (neden Mamdani). Q-learning güncelleme denklemi [19], [20]; fuzzy Q-learning'in iki yorumu [21], [22]. *(~1 sayfa)*

# Original Method (Referans Yöntem)

> **[9.3]** Sistem mimarisi (Şekil 1: araç → güç talebi → EMS → batarya/SC, DC/DC). Araç, batarya (14s×22p) ve SC (18s×15p) parametreleri. FLC: girdiler (P_dem, SoC_B, SoC_SC), çıktı (SC payı), 36 kural (Tablo 5), üyelik fonksiyonları (Şekil 2: `flc_membership.png`). FRL: durum, eylem, ödül fonksiyonu ve Q-tablosu. Makalenin raporladığı sonuçlar. *(~1 sayfa)*

# Reproduction Methodology (Yeniden Gerçekleştirme Yöntemi)

> **[9.4]** Python yazılım mimarisi (`src/hess/` modülleri). Kendi Mamdani motorumuz. Makalede eksik olan parametreler için verilen kararlar (D-xx; araç kütlesi, yuvarlanma direnci, sıcaklık kalibrasyonu hA = 0.0846 W/K). Sürüş çevrimi üretimi. Güvenlik katmanı. FRL eğitimi (5 seed). Doğrulama: birim testleri (96 test). *(~1.2 sayfa)*

# Proposed Extension (Önerilen Geliştirme)

> **[9.4]** Gerekçe: literal FLC'de SC'nin ~1070 s'de tükenmesi ve FRL ödülünün tutarsızlığı. S1 ve S2 SCS-FLC: 2 girdi (P_dem, SoC_SC), 12 kural, çıktılar (C_SC / P_cap ve P_ch). Bataryadan SC şarjı (D-20). Kural tablosu (Tablo 2) ve üyelik fonksiyonları. Karşılaştırma için ayarlı crisp kural tabanlı C0. Başarı kriterleri K1–K5. *(~1.2 sayfa)*

# Experimental Setup (Deney Düzeni)

> **[9.4]** Yazılım ortamı (Python 3.13, NumPy, SciPy, pandas, Matplotlib, PyYAML, Streamlit; donanım). Deney listesi (Tablo 3): E1–E4 (yeniden üretim), X1–X5 (katkı). Eşit bütçeli ayar (24 değerlendirme, LHS). 30 görülmemiş test çevrimi (seed 101–110 × sakin/nominal/agresif). Performans ölçütleri: tepe/RMS batarya akımı, min SoC_SC, deşarj süresi, çöküş sayısı. İstatistik test (Wilcoxon). *(~0.6 sayfa)*

# Results (Sonuçlar)

## Yeniden Üretim Sonuçları

> **[9.5]** Sadece-batarya baseline: tepe 137 A (makale 132), deşarj süresi 6755 s (makale 6540). FLC ilk çevrim tepe azalması −%26.3 (makale −%22.7), uzun deşarjda −%0.7. FRL. E4 DC/DC verim taraması. ECR tanımı. Tablo 4 (makale ve yeniden üretim yan yana), Şekil 3 (`reproduction_summary.png` veya `E1_current.png`).

## Önerilen Yöntemin Sonuçları

> **[9.5]** X1 eğitim çevrimi (Tablo 5, Şekil 4: `X1_summary.png`). X2 ablasyonlar A1–A5 (`X2_ablation.png`). X3 30 test çevrimi (Tablo 6, Şekil 5: `X3_generalization.png`, Wilcoxon p = 1.7e-6). X4 parametre duyarlılığı (`X4_sensitivity.png`). X5 ölçüm gürültüsü (`X5_noise.png`). K4/K5 kriter tablosu. Yönergedeki "Baseline / Geliştirilen / Değişim" biçiminde özet tablo.

# Discussion (Tartışma)

> **[9.5]** Mekanizma: dayanıklılığı sağlayan bulanık şarj yasası (A5 ile crisp şarjda 11/30 çöküş). Uyarlamalı tavanın katkısının olmaması (A4, p = 0.17). C0 en iyi durumda daha iyi ama kırılgan. Süredeki küçük kayıp. FRL > FLC'nin neden yeniden üretilemediği.

# Limitations (Sınırlılıklar)

> **[9.5]** Benzetim tabanlı (donanım yok); makalede eksik parametreler; sentetik sürüş çevrimleri; yaşlanma yalnızca vekil göstergelerle; K-FRL yapılmadı; tek araç modeli.

# Conclusion (Sonuç)

> **[9.5]** Genel sonuçlar ve gelecek çalışmalar (K-FRL, Type-2 [23], gerçek sürüş verisi, donanım-döngüde test).

# Generative AI Usage Disclosure (Üretken Yapay Zekâ Kullanım Beyanı) {.unnumbered}

> **[9.5]** Kullanılan araç, amaçlar (kod geliştirme, hata ayıklama, literatür taramasına yardım, dil düzenleme) ve doğrulama yöntemi (testler, kaynakların DOI üzerinden kontrolü, sonuçların yeniden koşturulması).

# References (Kaynaklar) {.unnumbered}

> **[9.5]** `references/README.md` §5'teki IEEE listesi, yalnızca metinde atıf yapılan kaynaklar.
