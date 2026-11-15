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

Elektrikli iki tekerlekli araçlar (E2W) şehir içi ulaşımda hızla yaygınlaşıyor. Şehir içi sürüş sık hızlanma ve frenlemeden oluşur. Tek kaynak olarak lityum-iyon batarya kullanıldığında bu durum kısa süreli yüksek akım tepelerine yol açar. Akım tepeleri bataryayı ısıtır, yaşlanmasını hızlandırır ve kullanılabilir menzili azaltır. Bu soruna önerilen çözümlerden biri hibrit enerji depolama sistemidir (HESS). HESS'te batarya enerji deposu olarak çalışır, güç yoğunluğu yüksek süperkapasitör (SC) ise kısa süreli güç tepelerini ve rejeneratif frenle geri kazanılan enerjiyi üstlenir. HESS'in başarısı, her zaman adımında güç talebinin ne kadarının bataryadan, ne kadarının SC'den karşılanacağına karar veren **enerji yönetim stratejisine (EMS)** bağlıdır.

Bu kararın girdileri (güç talebi, batarya ve SC şarj durumları) belirsizdir ve aralarındaki ilişki doğrusal değildir. Uzman bilgisinin "SC doluysa ve talep yüksekse yükün çoğunu SC'ye ver" gibi dilsel kurallarla ifade edilebildiği bu yapı, bulanık mantık için doğal bir uygulama alanıdır. Bulanık mantık kontrolcüleri (FLC) yorumlanabilir ve modelden bağımsızdır, ancak kuralları sabittir. Pekiştirmeli öğrenme (RL) ise ortamla etkileşerek uyum sağlayabilir, fakat kara kutu gibi çalışır. Referans makale [1], bu iki yaklaşımı birleştiren bulanık takviyeli öğrenme (FRL) tabanlı bir EMS önermektedir: 36 kurallı bir Mamdani FLC'nin kararları, tablo Q-learning ile ayarlanır.

Bu projenin amacı [1]'deki yöntemi Python'da yeniden gerçekleştirmek, sonuçlarını makaleyle karşılaştırmak ve gözlenen bir zayıflığa yönelik özgün bir bulanık mantık geliştirmesi önerip deneysel olarak değerlendirmektir. Minimum yeniden gerçekleştirme kapsamı şunlardır: araç, batarya ve SC modelleri; Tablo 5'teki 36 kuralın birebir uygulandığı Mamdani FLC; FLC üzerine kurulan Q-learning katmanı; makalenin sadece-batarya, FLC ve FRL karşılaştırma deneyi. Çalışmanın katkıları:

1. **Açık kaynak yeniden üretim.** Bütün bileşenler, harici bir bulanık mantık kütüphanesi kullanılmadan yazılmıştır. Sadece-batarya baseline makaleyle uyumludur: tepe akım 137 A (makale 132 A), %100'den %20'ye deşarj süresi 6755 s (makale 6540 s).
2. **Eleştirel bulgular.** Makaledeki kural tabanının SC'yi uzun sürüşte ~1070 s içinde boşalttığı ve tepe akım kazancının bu noktadan sonra ortadan kalktığı gösterilmiştir. Makalenin ödül fonksiyonundaki tutarsızlıklar incelenmiş, FRL'nin FLC'ye üstünlüğü yeniden üretilememiştir.
3. **Özgün katkı: SoC-duyarlı SCS-FLC.** İki girdili, 12 kurallı bir Mamdani denetleyici önerilmiştir. SC'nin bataryadan şarjını bulanık bir yasayla yönetir. Eşit bütçeyle ayarlanmış crisp kural tabanlı bir rakiple, görülmemiş 30 sürüş çevrimi üzerinde, parametre bozulmaları ve ölçüm gürültüsü altında karşılaştırılmıştır.

Rapor şöyle düzenlenmiştir: Bölüm 2 ilgili çalışmaları, Bölüm 3 teorik altyapıyı, Bölüm 4 referans yöntemi özetler. Bölüm 5 yeniden gerçekleştirmeyi, Bölüm 6 önerilen geliştirmeyi, Bölüm 7 deney düzenini anlatır. Sonuçlar Bölüm 8'de verilir, Bölüm 9–11'de tartışılır.

# Related Work (İlgili Çalışmalar)

Batarya/SC HESS'leri için EMS'ler genel olarak kural tabanlı, optimizasyon tabanlı ve öğrenme tabanlı olarak sınıflandırılır [16]. Tablo \ref{tab:lit} bu bölümde ele alınan çalışmaları özetler.

**Bulanık mantık ile RL'nin birleşimi.** Son yıllarda bu iki yaklaşımı birleştiren çalışmalar artmıştır. Bu çalışmalarda bulanık mantık iki farklı rol üstlenir. Birinci yapıda, Glorennec ve Jouffe'nin önerdiği fuzzy Q-learning çizgisinde [21], [22], bulanık çıkarım sistemi Q-fonksiyonunu yaklaşıklamak için kullanılır. Böylece sürekli durum ve eylem uzayları ayrıklaştırmadan ele alınabilir. Guo ve ark. [5], yakıt hücreli bir araçta yakıt hücresinin sık başlatılmasını ödülde cezalandıran, modelden bağımsız bir fuzzy Q-learning EMS'si önermiştir. Yang ve ark. [6], yol koşullarını topluluk öğrenmesiyle tanıyıp her yol türü için farklı bir eylem uzayı kullanmıştır. Pan ve ark. [2], batarya/SC HESS'i için yol tanımayı derin bir fuzzy Q-ağıyla (D3FQN) birleştirmiştir. İkinci yapıda bulanık denetleyici taban kontrolcüdür ve RL onun kararını ayarlar. Ariche ve ark. [7], tek kaynaklı bir BEV'de motor güç katsayısını hız, eğim ve SoC'ye göre ayarlayan bir fuzzy Q-learning denetleyicisini FLC ile karşılaştırmıştır. Referans makale [1] de bu ikinci yapıdadır.

**Bulanık mantık olmadan RL.** Xu ve ark. [3], [4] tablo ve hiyerarşik Q-learning ile batarya/ultrakapasitör sistemlerinde batarya yaşlanmasını yavaşlatmıştır. Xiong ve ark. [8], Q-learning ile kural tabanlı EMS'ye göre enerji kaybını azaltmıştır. Daha yeni çalışmalar tablo yöntemler yerine derin RL kullanır: Wu ve ark. [9] PPO ile sürüş stiline duyarlı bir EMS, Liu ve ark. [10] ise taklit tabanlı RL önermiştir.

**Kural tabanlı ve optimize FLC'ler.** Şen ve ark. [11], rejeneratif frenlemeye odaklanan bir FLC ile batarya akımını ve ısı üretimini azaltmıştır. Rakhtala Rostami ve Al-Shibaany [12], FLC'nin kural ve üyelik fonksiyonlarını öğretme-öğrenme tabanlı optimizasyonla (TLBO) ayarlamıştır. Chen ve ark. [14], dinamik programlamadan çıkarılan kural örüntülerini meta-kurallara dönüştürmüştür. Al Takrouri ve ark. [15], klasik güç takipçisini üstel yumuşatmayla iyileştirmiştir. Referans makalenin yazarları aynı E2W sistemi için ANFIS tabanlı bir EMS de önermiştir [13].

Table: İlgili çalışmaların karşılaştırması. \label{tab:lit}

| Çalışma | Sistem | Yöntem | Bulanık mantığın rolü |
|---|---|---|---|
| [1] (referans) | E2W, batarya + SC | Mamdani FLC + tablo Q-learning | Taban kontrolcü |
| [2] | EV, batarya + SC | Yol tanıma + D3FQN | Q-ağı yaklaşıklayıcı |
| [3], [4] | EV, batarya + UC | Tablo / hiyerarşik Q-learning | Yok |
| [5] | Yakıt hücreli HEV | Fuzzy Q-learning | Q-fonksiyonu yaklaşıklayıcı |
| [6] | Yakıt hücreli araç | Yol tanıma + fuzzy Q-learning | Q-fonksiyonu yaklaşıklayıcı |
| [7] | BEV (tek kaynak) | Fuzzy Q-learning denetleyici | Taban kontrolcü |
| [8] | PHEV, batarya + SC | Q-learning | Yok |
| [9], [10] | EV, batarya + SC | PPO / taklit RL | Yok |
| [11], [12] | EV, HESS | FLC / TLBO ile ayarlı FLC | Denetleyicinin kendisi |
| [13] | E2W, batarya + SC | ANFIS | Nöro-bulanık model |
| [14], [15] | EV, batarya + SC | Meta-kural / güç takipçisi | Yok |

**Projenin konumu.** Literatürden üç gözlem çıkmaktadır. (i) E2W odaklı HESS çalışmaları azdır ve büyük kısmı aynı gruptandır [1], [13]. (ii) FLC'den öğrenme tabanlı yönteme geçişte raporlanan kazançlar genellikle tek haneli yüzdelerdir. Bu kadar küçük farkların iddia edilebilmesi için çoklu çevrim ve istatistiksel test gerekir, [1]'de bunlar yoktur. (iii) Kural tabanlarının SC enerji dengesini koruyup korumadığı, yani uzun sürüşte SC'nin sürdürülebilir kullanımı, nadiren ayrıca incelenir. Bu proje, [1]'i açık kaynak olarak yeniden üretir ve (ii) ile (iii)'e odaklanan bir geliştirme önerir.

# Theoretical Background (Teorik Altyapı)

## Bulanık kümeler ve dilsel değişkenler

Klasik kümelerde bir eleman kümeye ya aittir ya da değildir. Zadeh'in bulanık kümelerinde [17] ise $X$ evrenindeki bir $A$ kümesi, her elemana $[0,1]$ aralığında bir üyelik derecesi atayan bir üyelik fonksiyonuyla (MF) tanımlanır: $\mu_A : X \rightarrow [0,1]$. Bu projede, referans makaleyle uyumlu olarak yamuk (trapezoidal) MF kullanılmıştır. Üçgen MF, yamuğun $b = c$ olduğu özel durumudur:

$$\mu_{\mathrm{trap}}(x; a,b,c,d) = \max\left(\min\left(\frac{x-a}{b-a},\, 1,\, \frac{d-x}{d-c}\right),\, 0\right).$$

**Dilsel değişken**, değerleri sözcüklerle ifade edilen bir değişkendir. Örneğin "süperkapasitör SoC'si" değişkeni *Low*, *Medium* ve *High* terimlerini alır ve her terim bir bulanık kümeyle temsil edilir. **Bulanıklaştırma**, ölçülen keskin bir girdi değerinin her terimdeki üyelik derecesinin hesaplanmasıdır. Örneğin $SoC_{SC} = 0.45$ değeri aynı anda kısmen *Low*, kısmen *Medium* olabilir. Komşu terimler arasındaki bu örtüşme, denetleyicinin çıktısının girdiyle birlikte sıçramadan, sürekli değişmesini sağlar.

## Kural tabanı ve Mamdani çıkarımı

Bulanık kural tabanı *EĞER–İSE* kurallarından oluşur. Örneğin: *EĞER $SoC_B$ Medium VE $SoC_{SC}$ High VE $P_{dem}$ High İSE $C_{SC}$ = %60*. Mamdani çıkarımında [18] her $k$ kuralı için şu adımlar uygulanır:

1. **Ateşleme gücü (VE işlemi, min):** $w_k = \min\big(\mu_{A_k}(x_1),\, \mu_{B_k}(x_2),\, \mu_{C_k}(x_3)\big)$.
2. **Çıkarım (min):** Sonuç kümesi ateşleme gücü seviyesinden kırpılır: $\mu'_k(y) = \min\big(w_k,\, \mu_{D_k}(y)\big)$.
3. **Birleştirme (max):** Kırpılmış kümeler birleştirilir: $\mu_{\mathrm{agg}}(y) = \max_k \mu'_k(y)$.
4. **Durulaştırma (ağırlık merkezi):** Birleşik kümeden tek bir keskin çıktı elde edilir:

$$y^{*} = \frac{\int y\, \mu_{\mathrm{agg}}(y)\, dy}{\int \mu_{\mathrm{agg}}(y)\, dy} \approx \frac{\sum_i y_i\, \mu_{\mathrm{agg}}(y_i)}{\sum_i \mu_{\mathrm{agg}}(y_i)}.$$

Uygulamada integral, ayrık bir çıktı evreni üzerinde toplamla hesaplanır. Bu projedeki bütün bulanık denetleyiciler, `src/hess/fuzzy.py` içinde yazılan bu min–min–max–centroid motorunu kullanır.

**Mamdani ile Sugeno.** Takagi–Sugeno tipi sistemlerde kural sonuçları bulanık küme değil, girdilerin (çoğunlukla doğrusal) fonksiyonlarıdır. Çıktı, bu fonksiyonların ateşleme güçleriyle ağırlıklı ortalamasıdır. Sugeno hesaplama açısından daha ucuzdur ve ANFIS gibi veriyle ayarlanan yöntemlere uygundur. Mamdani ise sonuçları da dilsel terim olarak tuttuğu için uzman bilgisini doğrudan ifade etmeye ve kuralları yorumlamaya daha uygundur. Referans makalenin kural tablosu (Tablo 5) dilsel sonuçlar içerdiği ve projenin önerisi de yorumlanabilirliğe dayandığı için Mamdani tercih edilmiştir.

## Q-learning ve bulanık takviyeli öğrenme

Pekiştirmeli öğrenmede bir ajan, $s_t$ durumunda $a_t$ eylemini seçer, ortamdan $r_t$ ödülünü alır ve $s_{t+1}$ durumuna geçer. Amaç, indirgenmiş toplam ödülü en büyükleyen politikayı bulmaktır [20]. Q-learning [19], durum–eylem değerlerini modelden bağımsız olarak şu kuralla günceller:

$$Q(s_t,a_t) \leftarrow Q(s_t,a_t) + \alpha \left[ r_t + \gamma \max_{a'} Q(s_{t+1},a') - Q(s_t,a_t) \right].$$

Burada $\alpha$ öğrenme oranı, $\gamma$ indirim katsayısıdır. Keşif ile sömürü arasındaki denge $\varepsilon$-açgözlü seçimle kurulur: ajan $\varepsilon$ olasılıkla rastgele, $1-\varepsilon$ olasılıkla en yüksek Q değerli eylemi seçer. $\varepsilon$ zamanla azaltılır.

Bulanık takviyeli öğrenme (FRL) iki şekilde kurulabilir. *Fuzzy Q-learning*'de [21], [22] her bulanık kuralın sonucu, aday eylemler arasından Q-learning ile seçilir. Sistemin çıktısı da kuralların ateşleme güçleriyle ağırlıklandırılmış eylemlerdir. Böylece bulanık sistem, sürekli durum uzayında bir değer fonksiyonu yaklaşıklayıcısı gibi çalışır. İkinci yapıda bulanık denetleyicinin kararı korunur ve RL ajanı yalnızca bu karara bir düzeltme ekler. Referans makale [1] bu ikinci yapıyı kullanır (Bölüm 4.3).

# Original Method (Referans Yöntem)

## Sistem

Referans makale [1], şehir içinde kullanılan bir elektrikli scooter için aktif bir HESS ele alır (Şekil \ref{fig:arch}). Batarya bir tek yönlü, SC ise bir çift yönlü DC/DC dönüştürücüyle ortak DC baraya bağlıdır. Motorun güç talebi $P_{dem}$, boylamsal araç dinamiğinden hesaplanır. Talep; ivmelenme, aerodinamik direnç, yuvarlanma direnci ve eğim bileşenlerini içerir, frenleme enerjisinin sabit %20'si geri kazanılır. EMS her adımda $P_{dem}$'in batarya ve SC arasındaki paylaşımına karar verir. Temel parametreler Tablo \ref{tab:params}'de verilmiştir.

![HESS ve EMS'nin sistem mimarisi. Kesikli çizgiler kontrol (mavi) ve ölçüm (gri) sinyallerini, siyah oklar güç akışını gösterir. Turuncu ok, bu projede önerilen bataryadan SC şarjı yoludur (Bölüm 6).](results/figures/system_architecture.png){#fig:arch width=95%}

Table: Referans sistemin temel parametreleri [1]. \label{tab:params}

| Bileşen | Değer |
|---|---|
| Motor | 6.2 kW, 26 N·m; tekerlek yarıçapı 0.23 m |
| Aerodinamik | Ön alan 0.88 m², $C_d$ = 0.22; aktarma verimi 0.95 |
| Batarya | 18650 NMC hücre (3.35 Ah, 3.6 V), 14s×22p: 50.4 V, 73.7 Ah, 3.7 kWh |
| Süperkapasitör | 500 F / 2.7 V hücre, 18s×15p: 48 V, ≈417 F, ≈136 Wh |
| DC/DC | 50 kHz, hedef verim %96 |
| Sürüş verisi | Gerçek sürüş, 900 s, 12.4 km, en yüksek hız 83 km/h |

## Bulanık mantık kontrolcüsü (FLC)

FLC'nin üç girdisi vardır: batarya SoC'si $SoC_B$ ve SC SoC'si $SoC_{SC}$ (her biri *Low*, *Medium*, *High*) ile güç talebi $P_{dem}$ (*Low*, *Medium*, *High*, *Regeneration*; $[-5100, 5600]$ W). Çıktılar batarya ve SC güç katsayılarıdır: $C_B$ ve $C_{SC}$, talebin yüzde kaçının her kaynaktan karşılanacağını belirler. Kural tabanı $3 \times 3 \times 4 = 36$ kuraldan oluşur. Çekiş (pozitif talep) kurallarında $C_B + C_{SC} = 100$'dür. Rejenerasyonda batarya şarj edilmez ($C_B = 0$) ve SC, $SoC_{SC}$ *Low* veya *Medium* ise geri kazanılan enerjiyi alır, *High* ise almaz. Tablo \ref{tab:rules}, 36 kuralın $C_{SC}$ değerlerini tek tabloda özetler. Makalede üyelik fonksiyonlarının tipi (yamuk) ve girdi aralıkları verilmiştir, köşe noktaları verilmemiştir.

Table: Referans FLC'nin kural tabanı [1, Tablo 5]: SC payı $C_{SC}$ (%). Her hücrede $SoC_B$ = Low / Medium / High için üç değer vardır. Çekişte $C_B = 100 - C_{SC}$, rejenerasyonda $C_B = 0$'dır. \label{tab:rules}

| $SoC_{SC}$ \\ $P_{dem}$ | Low | Medium | High | Regeneration |
|---|:---:|:---:|:---:|:---:|
| Low | 0 / 25 / 0 | 0 / 25 / 0 | 25 / 25 / 25 | 20 / 20 / 20 |
| Medium | 30 / 45 / 35 | 30 / 45 / 35 | 35 / 45 / 35 | 20 / 20 / 20 |
| High | 60 / 60 / 60 | 60 / 60 / 60 | 60 / 60 / 60 | 0 / 0 / 0 |

Tablo \ref{tab:rules}'den kural tabanının iki özelliği okunabilir. Birincisi, kararı belirleyen asıl değişken $SoC_{SC}$'dir: SC doldukça yükün daha büyük kısmı SC'ye kayar. Talep seviyesi yalnızca SC *Low* ve *Medium* iken yüksek talepte fark yaratır. İkincisi, bataryanın SC'yi şarj ettiği hiçbir kural yoktur ve $SoC_B$ *Medium* iken $SoC_{SC}$ *Low* olsa bile SC'ye %25 pay verilir. SC'nin tek şarj kaynağı %20'lik rejenerasyondur. Bölüm 8'de gösterildiği gibi bu durum, uzun sürüşte SC'nin boşalmasına yol açar.

## Q-learning katmanı (FRL)

FRL'de ajanın durumu, FLC girdilerinin dilsel kategorileridir ($3 \times 3 \times 4 = 36$ durum). Eylem, FLC'nin önerdiği paylaşım oranında yapılan düzeltmedir. Durum geçişi SoC denklemleriyle tanımlanır: $SoC_B(t+1) = SoC_B(t) - C_B P_{dem} / E_B$, SC için de benzer şekilde. Hiperparametreler $\alpha = 0.1$, $\gamma = 0.9$'dur. $\varepsilon$ 1.0'dan başlayıp her bölümde 0.995 ile çarpılır, alt sınırı 0.01'dir. Ödül fonksiyonu Tablo \ref{tab:reward}'de verilmiştir. Makaleye göre belirsizliğin düşük olduğu durumlarda FLC kararı doğrudan uygulanır. Ani ivmelenme veya rejenerasyon dalgalanması gibi belirsiz durumlarda ise RL kararı ayarlar.

Table: Referans makalenin ödül fonksiyonu [1, Denk. 5]. \label{tab:reward}

| Koşul | Ödül |
|---|---:|
| $P_{dem} < 0$, $C_B = 0$ ve $C_{SC} > 0$ (fren enerjisi SC'ye) | +1 |
| $P_{dem} > 0$ ve $C_{SC} \geq 50\%$ | +0.5 |
| $P_{dem} > 0$ ve $C_{SC} = C_B$ | 0 |
| $P_{dem} > 0$ ve $C_B \geq 75\%$ | −0.5 |
| $P_{dem} > 0$ ve $C_B > 0$ | −1 |
| $SoC_B < SoC_{min}$ | −1.5 |

## Raporlanan sonuçlar ve belirsizlikler

Makale, deneyleri MATLAB/Simulink'te ve bir donanım test düzeneğinde yapmıştır. Raporlanan tepe batarya akımı sadece-batarya için 132 A, FLC için 102 A, FRL için 97.9 A'dır. Batarya SoC'sinin %100'den %20'ye inme süresi sırasıyla 6540, 6950 ve 6990 s'dir. Ayrıntılı karşılaştırma Bölüm 8.1'de verilmiştir. Makaleyi yeniden üretmeyi zorlaştıran eksikler şunlardır: MF köşe noktaları, araç kütlesi, yuvarlanma katsayısı, Q-learning eylem kümesi, bölüm sayısı ve $SoC_{min}$ verilmemiştir; RL'nin hangi belirsizlik eşiğinde devreye girdiği tanımlanmamıştır; sürüş verisi açık değildir. Ödül fonksiyonunun koşulları birbirini dışlamaz (ör. $C_B = 40$, $C_{SC} = 60$ hem +0.5 hem −1 koşulunu sağlar). Ayrıca ödül, $C_B$ arttıkça monoton değişmez. Tablolarda da bazı iç tutarsızlıklar vardır, ör. sadece-batarya için ortalama akım (84.8 A) RMS akımdan (40.4 A) büyük verilmiştir, bu matematiksel olarak mümkün değildir. Bu eksikler için alınan kararlar Bölüm 5'te açıklanmıştır.

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
