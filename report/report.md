---
lang: tr
mainfont: Liberation Serif
monofont: DejaVu Sans Mono
fontsize: 10pt
geometry: "a4paper,margin=2.0cm"
linestretch: 1.08
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

Bu çalışmada, elektrikli iki tekerlekli araçların batarya/süperkapasitör hibrit enerji depolama sistemi için önerilen bulanık takviyeli öğrenme tabanlı enerji yönetim stratejisi [1] Python'da yeniden gerçekleştirilmiş ve geliştirilmiştir. Referans yöntem, 36 kurallı bir Mamdani bulanık denetleyiciden ve onu ayarlayan tablo Q-learning'den oluşur. Yeniden üretimde sadece-batarya baseline'ı makaleyle uyumlu çıkmıştır (tepe akım 137 A ve 132 A). Bulanık denetleyicinin tepe akım azalması süperkapasitör dolu iken yeniden üretilmiştir (−%26.3 ve −%22.7). Ancak kural tabanının süperkapasitörü uzun sürüşte ~1070 s içinde boşalttığı ve öğrenme katmanının üstünlüğünün istatistiksel olarak yeniden üretilemediği gösterilmiştir. Bu bulgulara dayanarak, süperkapasitörü bulanık bir yasayla bataryadan yeniden şarj eden iki girdili ve 12 kurallı bir Mamdani denetleyici (SCS-FLC) önerilmiştir. Önerilen yöntem, görülmemiş 30 sürüş çevriminde hiç çökmeden ortalama tepe batarya akımını referans denetleyiciye göre %55, eşit bütçeyle ayarlanmış kesin (crisp) kural tabanına göre %35 düşürmüştür (Wilcoxon $p = 1.7 \times 10^{-6}$). Crisp kural 30 çevrimin 14'ünde çökmüştür. Ablasyonlar, dayanıklılığın kaynağının süperkapasitör doluluğuyla sürekli değişen bulanık şarj yasası olduğunu, uyarlamalı güç tavanının ise anlamlı bir katkısı olmadığını göstermiştir.

**Anahtar kelimeler:** bulanık mantık, Mamdani çıkarımı, fuzzy Q-learning, hibrit enerji depolama, süperkapasitör, enerji yönetim stratejisi, elektrikli iki tekerlekli araç

```{=latex}
\setcounter{tocdepth}{1}
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
| Süperkapasitör | 500 F / 2.7 V hücre, 18s×15p: 48 V, 406 F, 12 mΩ |
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

## Yazılım yapısı

Yöntem, harici bir bulanık mantık ya da RL kütüphanesi kullanılmadan Python'da yazılmıştır. Böylece kodun her satırı açıklanabilir. Bütün parametreler `config/default.yaml` dosyasında tutulur ve rastgelelik her yerde tohum (seed) ile kontrol edilir. `src/hess/` paketi şu modüllerden oluşur:

- Fiziksel modeller: `drive_cycle`, `vehicle`, `battery`, `supercap`.
- Benzetim döngüsü ve güvenlik katmanı: `simulator`.
- Mamdani motoru: `fuzzy`.
- Denetleyiciler: `flc_ems` (36 kural), `qlearning` ile `frl_ems` (FRL), `scs_flc` ve `crisp_ems` (Bölüm 6).
- Ölçütler: `metrics`.

Doğruluk 96 birim testiyle kontrol edilir. Örneğin 36 kuralın her biri, tek başına tam ateşlendiği noktada Tablo 5'teki değeri birebir üretir. Kinetik enerji kapalı bir çevrimde korunur.

## Modeller ve eksik parametreler için kararlar

Makalede verilmeyen her nokta için bir varsayım (A-xx) ya da tasarım kararı (D-xx) alınmış ve gerekçesiyle `docs/implementation_plan.md` dosyasına yazılmıştır. Başlıcaları:

- **Zaman adımı ve sürüş profili.** $\Delta t = 1$ s seçilmiştir. Gerçek sürüş verisi paylaşılmadığı için, makalenin raporladığı altı istatistiğe uyan sentetik bir şehir içi profil üretilmiştir: 900 s, 12.4 km, en yüksek hız 83 km/h, +2.7 / −2.6 m/s². Profil duraklar arasındaki kısa yolculuklardan oluşur. Seyir bölümlerine telefon kaydındaki küçük hız dalgalanmalarını taklit eden AR(1) gürültüsü eklenmiştir. Uzun deşarj testinde profil, $SoC_B$ %20'ye inene kadar tekrarlanır.
- **Araç.** Toplam kütle 195 kg (araç 120 kg, sürücü 75 kg), yuvarlanma katsayısı 0.015, motor ve inverter verimi 0.90 alınmıştır. Talep 6.2 kW'ta sınırlanır.
- **Batarya.** $R_{int}$ eşdeğer devresi kullanılmıştır: NMC açık devre gerilimi eğrisi ve 30 mΩ hücre direnci. Termal model birinci derecedendir: $m c_p\, dT/dt = I^2 R - hA\,(T - T_{amb})$. $hA = 0.0846$ W/K değeri, sadece-batarya senaryosunda makaledeki 2.1 °C artışı verecek şekilde bir kez kalibre edilip sabitlenmiştir.
- **Süperkapasitör ve dönüştürücüler.** SC, ideal kapasitör ve seri dirençle modellenmiştir (406 F, 12 mΩ). $SoC_{SC}$ enerji tabanlı tanımlanmıştır ($V_{min} = V_{max}/2$), bu tanımla kullanılabilir enerji ≈ 98 Wh'tir. İki dönüştürücünün verimi de sabit 0.96'dır.
- **Güvenlik katmanı.** Bütün EMS'ler için ortaktır. SC'nin karşılayamadığı çekiş gücü bataryadan alınır, fazla fren enerjisi mekanik frene gider.
- **FLC'nin üyelik fonksiyonları.** Yamuk tip korunmuş, köşe noktaları komşu terimler %50 örtüşecek şekilde seçilmiştir (Şekil \ref{fig:mf}). Bu yapıda her girdi değerinin üyelik derecelerinin toplamı 1'dir (Ruspini bölümlemesi). Çıktı seviyeleri ±5 genişlikli üçgenlerle temsil edilmiştir. Çıktı evreni $[-5, 105]$ alınmıştır, böylece ağırlık merkezi uç değerlerde içe doğru kaymaz.

![Referans FLC'nin üyelik fonksiyonları ($SoC_B$, $SoC_{SC}$, $P_{dem}$ ve çıktılar).](results/figures/flc_membership.png){#fig:mf width=88%}

## FRL'nin uygulanması

FRL'nin durumu, her girdinin en yüksek üyelikli dilsel terimidir (36 durum). Makalede eylem kümesi tanımlanmadığı için, RL'nin FLC kararını düzelttiği fikri şöyle uygulanmıştır: eylem, FLC'nin $C_{SC}$ çıktısına eklenen $\Delta \in \{-20, -10, 0, +10, +20\}$ yüzde puandır. $\Delta = 0$, FLC kararını aynen uygulamak anlamına gelir. Ödül (Tablo \ref{tab:reward}) aynen uygulanmıştır, koşullar örtüştüğü için ilk eşleşen koşul geçerli sayılır. Rejenerasyon durumlarında FLC kararı değiştirilmez. Ajan 1000 bölümle eğitilir. Her bölüm, rastgele başlangıç SoC'leriyle profilin bir geçişidir. Eğitim 5 farklı tohumla tekrarlanır ve sonuçlar ortalama ± standart sapma olarak verilir. Değerlendirmede açgözlü politika kullanılır. Hiç öğrenilmemiş durumlarda $\Delta = 0$ seçildiği için, Q tablosu sıfırken FRL birebir FLC gibi davranır.

# Proposed Extension (Önerilen Geliştirme)

## Gerekçe

Yeniden üretim iki yapısal sorun göstermiştir (Bölüm 8.1). (i) Tablo \ref{tab:rules}, düşük ve orta talepte de SC'ye pay verir ve bataryadan SC şarjı içermez. Bu yüzden SC uzun sürüşün ilk ~1070 s'sinde boşalır ve tepe akım kazancı kaybolur. (ii) Q-learning katmanı bu sorunu çözmez: ödül monoton olmadığından ajan, SC'yi korumayı ancak onu kullanmaktan vazgeçerek öğrenir. Bu bulgular sorunun öğrenme katmanında değil kural tabanında olduğunu gösterir. SC'nin enerjisi (≈98 Wh) bataryanınkinin yalnızca ~%2.6'sı kadardır. Bu yüzden SC bir enerji kaynağı olarak değil, bir **güç tamponu** olarak kullanılmalıdır: yüksek talepte devreye girmeli, düşük talepte yeniden doldurulmalıdır.

Bu fikir, ön denemede basit bir crisp kuralla sınanmıştır: eşiğin üstündeki talebi SC'ye vermek ve düşük talepte SC'yi şarj etmek. Kural uzun deşarjda tepe akımı yarıya indirmiştir, ancak kırılgan çıkmıştır. Eşik ya da şarj gücü biraz değişince SC yine boşalmış ve kazanç tamamen kaybolmuştur (−%53'ten −%1.3'e). Bulanık mantığın buradaki gerekçesi, kararın $SoC_{SC}$'nin **sürekli** bir fonksiyonu olmasıdır. SC boşaldıkça SC'nin kullanımı azalır ve şarj artar. Bu doğal geri besleme, SC'nin doluluğunu parametre ayarına bağımlı olmadan bir bantta tutmalıdır.

## SoC-duyarlı SCS-FLC

Önerilen denetleyicinin adı **SCS-FLC**'dir (*supercapacitor-sustaining FLC*). İki girdisi vardır: $P_{dem}$ ve $SoC_{SC}$. Üyelik fonksiyonları referans FLC ile aynı tutulmuştur, böylece fark yalnızca kurallardan gelir. $SoC_B$ girdisi Tablo \ref{tab:rules}'de neredeyse hiç etki göstermediği için çıkarılmıştır; gerekliliği ayrı bir ablasyonla sınanmıştır. Kural sayısı $4 \times 3 = 12$'ye iner. Çıkarım Bölüm 3.2'deki Mamdani motoruyla yapılır. İki varyant vardır, ikincisi ana katkıdır:

- **S1 (pay):** Birinci çıktı $C_{SC}$'dir, talebin SC'ye giden yüzdesi: $P_{SC} = C_{SC} P_{dem}/100 - P_{ch}$.
- **S2 (tavan):** Birinci çıktı $P_{cap}$'tir, bataryanın güç tavanı. SC yalnızca tavanın üstünde kalan talebi karşılar: $P_{SC} = \max(P_{dem} - P_{cap}, 0) - P_{ch}$. $P_{cap}$ yalnızca $SoC_{SC}$'ye bağlıdır: *Low* → *Loose* (yüksek tavan, SC korunur), *Medium* → *Mid*, *High* → *Tight* (düşük tavan, dolu SC daha çok çalışır).
- **İki varyantta ortak yeni çıktı $P_{ch}$:** Bataryadan SC'ye şarj gücüdür. Simülatörde tek değişiklik, çekiş sırasında bu şarja izin verilmesidir (Şekil \ref{fig:arch}'deki turuncu yol). Batarya bu durumda da yalnızca deşarj eder. Frenlemede enerjinin tamamı SC'ye yönlendirilir.

Table: SCS-FLC kural tabanı: $C_{SC}$ (S1) ve $P_{ch}$. S2'de $P_{ch}$ kuralları aynıdır, $P_{cap}$ yalnızca $SoC_{SC}$ sütununa bağlıdır (Loose / Mid / Tight). Ayar öncesi seviyeler: $C_{SC}$: Z = 0, VS = 10, S = 20, M = 25, L = 45, VL = 60, Full = 100 %; $P_{ch}$: 0 / 300 / 700 / 1200 W. \label{tab:scs}

| $P_{dem}$ \\ $SoC_{SC}$ | Low | Medium | High |
|---|:---:|:---:|:---:|
| Low | Z / **High** | Z / Medium | Z / Zero |
| Medium | Z / Low | VS / Zero | M / Zero |
| High | S / Zero | L / Zero | VL / Zero |
| Regeneration | Full / Zero | Full / Zero | Full / Zero |

Kurallar dilsel olarak şöyle okunur: "Talep yüksekse ve SC doluysa yükü SC'ye ver" (son satırlar) ve "Talep düşükse ve SC boşalmışsa bataryadan SC'yi doldur" (ilk sütun). $P_{ch}$, $SoC_{SC}$ arttıkça High → Medium → Zero olarak **sürekli** azalır. S2'nin dayanıklılığını bu bulanık şarj yasasının sağladığı Bölüm 8.2'de ablasyonla gösterilmiştir.

## Karşılaştırma grubu ve başarı ölçütleri

Bulanıklığın etkisini tek başına ölçmek için aynı fikri keskin eşiklerle uygulayan **C0** (crisp) kural tabanlı bir EMS kurulmuştur. C0'da talep $P_{th}$'yi aşınca fazlasını SC karşılar. Talep $P_{lo}$'nun altındaysa ve $SoC_{SC}$ hedefin altındaysa batarya SC'yi sabit $P_{ch}$ ile şarj eder. Başarı ölçütleri deneylerden **önce** tanımlanmıştır:

- **K1:** Uzun deşarjda tepe $I_B$ F0'dan en az %30 düşük olmalı ve en düşük $SoC_{SC} \geq 0.10$ kalmalı.
- **K2:** RMS, $I^2t$ ve $\Delta T$, F0 ve R0'dan düşük olmalı.
- **K3:** Deşarj süresi B1'den en fazla %1 kısa olmalı.
- **K4:** Bulanık sürüm crisp'ten daha dayanıklı olmalı. Görülmemiş çevrimlerde ortalama ve en kötü tepe akım C0'dan iyi ($p < 0.05$), parametre bozulmasında kötüleşme C0'dan küçük olmalı.
- **K5:** Her bileşen (yeniden şarj, kural tabanı, uyarlamalı tavan) anlamlı bir katkı vermeli.

# Experimental Setup (Deney Düzeni)

**Ortam.** Python 3.13 kullanılmıştır. Kütüphaneler NumPy, SciPy (Wilcoxon testi), pandas, Matplotlib, PyYAML, pytest ve canlı demo için Streamlit'tir; sürüm alt sınırları `requirements.txt` dosyasındadır. Deneyler yalnızca CPU ile koşturulmuştur (macOS dizüstü bilgisayar; FRL eğitimi Linux bulut ortamında). FRL eğitimi tohum başına ~5 dk, bütün katkı deneyleri toplam ~5 dk sürer. Her deney, `experiments/` altındaki tek bir betikle yeniden üretilebilir.

**Karşılaştırılan yöntemler.**

- B0: sadece batarya, makaledeki gibi rejenerasyonsuz.
- B1: sadece batarya, rejenerasyonlu. Rejenerasyonun katkısını ayırmak için eklenmiş adil baseline.
- F0: referans FLC.
- R0: referans FRL.
- C0: crisp kural tabanı.
- S1, S2: önerilen yöntem.
- A1–A5: ablasyonlar.

Bütün yöntemler aynı simülatörü, güvenlik katmanını, dönüştürücü verimini ve başlangıç koşulunu ($SoC_B = SoC_{SC} = 1$) kullanır. Hiçbir HESS yönteminde batarya frenlemede şarj olmaz.

**Adil ayar.** C0, S1 ve S2'nin her biri dört parametreyle tanımlanmış ve **eşit bütçeyle** ayarlanmıştır: başlangıç noktası ve 23 Latin hiperküp noktası, yöntem başına 24 değerlendirme. Ayar yalnızca eğitim çevriminde (tohum 7) yapılmıştır. Amaç, $SoC_{SC} \geq 0.10$ ve K3 kısıtları altında tepe $I_B$'yi en aza indirmektir. S2 için ayarlanan parametreler tavanın merkezi ve yayılımı ($c_{cap} = 2666$ W, $d_{cap} = 192$ W) ile $P_{ch}$ ve $SoC_{SC}$ üyelik fonksiyonlarının ölçek çarpanlarıdır ($k_{ch} = 1.53$, $k_{soc} = 1.16$). Ayarlı değerler `config/tuned.yaml` dosyasındadır.

Table: Deneyler. \label{tab:exp}

| Kod | Deney | Koşul |
|---|---|---|
| E1–E3 | Üç senaryo: akım, sıcaklık, SoC, güç paylaşımı | Uzun deşarj ve ilk çevrim |
| E4 | DC/DC verim taraması, $\eta_c$ = 0.91–1.00 | Uzun deşarj |
| E6 | Rejenerasyonlu sadece-batarya (B1) | Uzun deşarj |
| X1 | Bütün yöntemlerin ana karşılaştırması | Eğitim çevrimi, uzun deşarj |
| X2 | Ablasyonlar A1–A5 | Eğitim çevrimi |
| X3 | Genelleme: 30 görülmemiş çevrim (tohum 101–110 × sakin / nominal / agresif) | Uzun deşarj |
| X4 | Parametre duyarlılığı: her parametre tek tek ±%10, ±%20 | Eğitim çevrimi |
| X5 | Ölçüm gürültüsü: $SoC_{SC}$ ve $P_{dem}$'e Gauss gürültüsü, σ = 0.02, 0.05 | Eğitim çevrimi, 5 tohum |

X3'teki üç rejim, seyirdeki hız dalgalanmasının genliğiyle ayrılır (0.5 / 1.0 / 1.5 m/s). Altı temel istatistik bütün çevrimlerde aynıdır. Rejimler arasında değişen talebin dağılımıdır: ortalama çekiş gücü 1.8 / 2.4 / 2.8 kW.

**Ölçütler.** Ana ölçüt, uzun deşarj (%100 → %20) boyunca tepe batarya akımıdır. Bunun yanında %99'luk batarya akımı, RMS akım, $I^2t$, sıcaklık artışı $\Delta T$, deşarj süresi, en düşük $SoC_{SC}$ ve adım başına karar süresi raporlanır. SC'nin boşalıp tepe akımın sadece-batarya seviyesine döndüğü çalıştırmalar **çökme** olarak sayılır. X3'te yöntemler aynı 30 çevrim üzerinde eşleştirilmiş Wilcoxon işaretli sıra testiyle karşılaştırılır. Makaleyle karşılaştırmada sürüş profili ve hücre modeli farklı olduğu için mutlak değerler yerine **göreli değişimler** ve sıralama kullanılır.

# Results (Sonuçlar)

## Yeniden Üretim Sonuçları

Tablo \ref{tab:repro}, yeniden üretimin sonuçlarını makaleyle yan yana gösterir. Şekil \ref{fig:repro} ise sadece-bataryaya göre göreli değişimleri karşılaştırır.

Table: Makale [1] ve yeniden üretim (E1, E2). B0: sadece batarya. FRL için 5 tohumun ortalaması ± std. "Uzun": %100 → %20 SoC deşarjı; "ilk çevrim": SC dolu iken ilk 900 s. Menzil makalenin tanımıyla hesaplanmıştır. \label{tab:repro}

| Ölçüt | Makale B0 | Makale FLC | Makale FRL | Bizim B0 | Bizim F0 (FLC) | Bizim R0 (FRL) |
|---|---:|---:|---:|---:|---:|---:|
| Tepe $I_B$, uzun (A) | 132 | 102 | 97.9 | 137.1 | 136.2 | 132.9 ± 4.4 |
| Tepe $I_B$, ilk çevrim (A) | – | – | – | 117.0 | 86.2 | 103.9 ± 3.9 |
| RMS $I_B$ (A) | 40.40 | 39.69 | 36.10 | 48.0 | 43.6 | 43.4 ± 0.3 |
| Sıcaklık artışı (°C) | 2.1 | 1.95 | 1.9 | 2.10 | 1.88 | 1.84 ± 0.03 |
| Deşarj süresi (s) | 6540 | 6950 | 6990 | 6755 | 7477 | 7466 ± 19 |
| Menzil (km) | 88.95 | 94.34 | 95.06 | 93.8 | 103.1 | 103.0 ± 0.3 |

![Sadece-bataryaya göre göreli değişimler: makale ile yeniden üretimin ilk çevrim ve uzun deşarj sonuçları.](results/figures/reproduction_summary.png){#fig:repro width=72%}

**Baseline.** Sadece-batarya modeli makaleyle uyumludur. Tepe akım +%3.9, deşarj süresi +%3.3 farklıdır, sıcaklık bu senaryoya kalibre edilmiştir. Makalenin tanımıyla enerji tüketimindeki fark %5'tir. Makalenin tüketim (ECR) tanımı aslında döngüseldir: paketin nominal enerjisinin gidilen mesafeye bölünmesidir, menzil formülü de bu yüzden gidilen mesafeyi geri verir.

**FLC.** SC dolu olduğu sürece makalenin tepe akım azalması yeniden üretilir: ilk çevrimde −%26.3 (makale −%22.7). Uzun deşarjda ise azalma −%0.7'ye düşer. Nedeni, SC'nin ilk ~1070 s'de boşalması ve deşarjın geri kalanında ortalama $SoC_{SC}$'nin 0.05'te kalmasıdır (Şekil \ref{fig:x1}, mavi). RMS akım (−%9.3), sıcaklık (−%10.3) ve deşarj süresi (+%10.7) değişimleri makaleyle aynı yönde ve aynı mertebededir.

**FRL.** Uzun deşarjda FRL, tepe akım, RMS ve $\Delta T$'de FLC'den biraz iyidir, yani sıralama makaleyle aynı yöndedir. Ancak farklar tohumlar arası standart sapmanın 0.5–1.3 katıdır ve anlamlı değildir. İlk çevrimde FRL, FLC'den 4 std'den fazla **kötüdür** (103.9 A ve 86.2 A). Öğrenilen politika, $SoC_{SC}$ *Low* olduğunda SC payını kısar. Bu SC'yi %15–30 bandında korur, ama korunan enerji tepe akımı karşılamak için kullanılmaz. E4'te dönüştürücü verimi 0.91–1.00 aralığında taranmıştır. HESS > sadece batarya sıralaması bütün noktalarda korunur, ama menzilde 10 noktanın 10'unda FLC ≥ FRL'dir. Makalenin FRL > FLC iddiası bu kurulumda yeniden üretilememiştir. Son olarak, rejenerasyonlu adil baseline'a (B1) göre FLC'nin deşarj süresi kazancı yalnızca +%3.3'tür. Makalenin raporladığı kazancın yaklaşık üçte ikisi SC'den değil, rejeneratif frenlemeden gelmektedir.

## Önerilen Yöntemin Sonuçları

Tablo \ref{tab:main}, önerilen yöntemi referans FLC (baseline) ve crisp rakip C0 ile bütün deneylerde karşılaştırır.

Table: Baseline (F0) ile önerilen yöntemlerin karşılaştırması. X1: eğitim çevrimi; X3: 30 görülmemiş çevrim; X4: tek parametrenin ±%20 bozulması; X5: ölçüm gürültüsü σ = 0.05. Son sütun S2'nin F0'a göre değişimidir. \label{tab:main}

| Ölçüt | F0 (FLC) | C0 (crisp) | S1 | **S2** | S2 / F0 |
|---|---:|---:|---:|---:|---:|
| X1 tepe $I_B$ (A) | 136.2 | 57.1 | 73.2 | **60.8** | −%55.3 |
| X1 RMS $I_B$ (A) | 43.6 | 35.9 | 37.2 | 36.0 | −%17.3 |
| X1 $\Delta T$ (°C) | 1.88 | 1.15 | 1.27 | 1.18 | −%37.6 |
| X1 deşarj süresi (s) | 7477 | 7308 | 7258 | 7255 | −%3.0 |
| X1 en düşük $SoC_{SC}$ | 0.00 | 0.17 | 0.55 | 0.41 | – |
| X3 tepe $I_B$ ort. / en kötü (A) | 136.9 / 137.2 | 93.6 / 137.1 | 75.9 / 88.6 | **61.1 / 71.5** | −%55.4 / −%47.9 |
| X3 çöken çevrim | 30 / 30 | 14 / 30 | 0 / 30 | **0 / 30** | – |
| X4 en büyük kötüleşme | – | +%137.6 | +%18.1 | **+%12.3** | – |
| X5 tepe $I_B$ (σ = 0.05) | 136.2 | 71.7 | 81.1 | 71.6 | – |
| Karar süresi (µs/adım) | 163 | 0.2 | 117 | 84 | −%48.7 |

**X1: eğitim çevrimi.** Ayarlanan üç yöntem de K1–K3'ü sağlar. Tepe akım F0'a göre %46–58 düşer, RMS akım, $I^2t$ ve $\Delta T$ hem F0'dan hem R0'dan düşüktür. Deşarj süresi B1'den kısa değildir (+%0.3 ile +%1.0). Şekil \ref{fig:x1}, farkın kaynağını gösterir. S1 ve S2, SC'yi deşarj boyunca 0.4–0.7 bandında tutar ve tepe akımı yarıdan fazla düşürür. C0'da $SoC_{SC}$ zamanla aşağı kayar ve sonda 0.17'ye iner. Bu, eğitim çevriminde bile C0'ın SC rezervinin ince olduğunu gösterir. Bedel deşarj süresidir: S2, F0'dan %3 kısa sürer, çünkü bataryadan SC'ye aktarılan enerji iki kez dönüştürücüden geçer. Bu çevrimdeki en iyi değerde crisp kural S2'den biraz iyidir (57.1 ve 60.8 A).

![X1, eğitim çevrimi. Sol: $SoC_{SC}$ seyri (60 s ortalama). Sağ: en yüksek 400 adımdaki batarya akımı, sıralı.](results/figures/X1_soc_current.png){#fig:x1 width=100%}

**X2: ablasyonlar.** Yeniden şarj kaldırılınca (A1, $P_{ch} = 0$) SC iki yöntemde de boşalır ve tepe akım F0 seviyesine döner (S1'de 134.7 A, S2'de 137.0 A). Tablo 5'in kurallarına yalnızca $P_{ch}$ eklemek (A2) tepe akımı 89.4 A'ya indirir. S1'in yeni kuralları ise 73.2 A verir. Yani kazancın çoğu yeniden şarjdan, ~16 A'lık kısmı kural tabanından gelir. $SoC_B$ girdisinin eklenmesi (A3, 36 kural) tepe akımı 1–2 A düşürür ve süreyi %0.7–1 uzatır, ama SC rezervini azaltır. Bu küçük kazanç için kural sayısının üç katına çıkması gerekir. S2'de tavanı sabitlemek (A4) sonucu değiştirmez (59.7 A). S2'nin bulanık şarj yasasını C0'ın crisp şarj kuralıyla değiştirmek (A5) ise tepe akımı değiştirmez, ama en düşük $SoC_{SC}$'yi 0.41'den 0.23'e indirir.

**X3: görülmemiş 30 çevrim.** Şekil \ref{fig:x3} ve Tablo \ref{tab:main} genelleme sonuçlarını verir. S2 hiçbir çevrimde çökmez, en kötü tepe akımı 71.5 A'dır. C0, 30 çevrimin 14'ünde çöker. Çöküşlerin dağılımı: sakin 0/10, nominal 4/10, agresif 10/10. Eğitim çevriminde ayarlanan eşik, daha zorlu sürüşte SC'yi koruyamaz. Eşleştirilmiş Wilcoxon testinde S2, 30 çevrimin 26'sında C0'dan daha düşük tepe akım verir (medyan fark −1.9 A, ortalama fark −32.5 A, $p = 1.7 \times 10^{-6}$). Fark tipik çevrimde küçük, C0'ın çöktüğü çevrimlerde büyüktür. S1 en kötü durumda C0'dan iyidir (88.6 A), ama tipik çevrimde daha kötüdür (medyan fark +9.4 A). Ablasyonlar X3'te de sınanmıştır. A1 ve A2, tam yöntemden anlamlı derecede kötüdür ($p = 1.9 \times 10^{-9}$). A5, 30 çevrimin 11'inde çöker ($p = 0.002$). A4 ile S2 arasında anlamlı fark yoktur (medyan −0.1 A, $p = 0.17$).

![X3, 30 görülmemiş test çevrimi (her nokta bir çevrim, renkler rejimleri gösterir, siyah çizgi medyandır). Soldan sağa: tepe $I_B$, en düşük $SoC_{SC}$, B1'e göre deşarj süresi.](results/figures/X3_generalization.png){#fig:x3 width=100%}

**X4 ve X5: duyarlılık ve gürültü.** Şekil \ref{fig:x4}'te her parametre tek tek bozulmuştur. C0'da eşik ya da şarj gücü yalnızca %10 düşünce SC boşalır. C0, 16 bozulmanın 7'sinde çöker ve en büyük kötüleşme +%138'dir. Bulanık sürümlerde kötüleşme düzgün ve sınırlıdır: S1'de en fazla %18, S2'de %12, hiçbir bozulmada çöküş yoktur. σ = 0.05 ölçüm gürültüsünde C0 ve S2'nin tepe akımı eşitlenir (~72 A). Fark SC rezervindedir: C0'da en düşük $SoC_{SC}$ 0.06'ya, yani çöküşün eşiğine iner, S2'de 0.40'ta kalır.

![X4, eğitim çevrimi, tek parametre bozulması (içi boş halka: SC boşaldı). Soldan sağa: C0, S1, S2.](results/figures/X4_sensitivity.png){#fig:x4 width=100%}

**Hipotezler.** S2 için K1–K4'ün hepsi sağlanır. S1 için K4'ün "tipik çevrimde crisp'ten iyi" koşulu sağlanmaz. K5'te yeniden şarjın (A1), kural tabanının (A2) ve bulanık şarj yasasının (A5) katkısı anlamlıdır. SoC'ye uyarlanan tavanın (A4) katkısı ise anlamlı değildir.

# Discussion (Tartışma)

**Dayanıklılığın mekanizması bulanık şarj yasasıdır.** S2'yi C0'dan ayıran bileşen tepe kırpma yapısı değil, şarj kuralıdır. A4'te tavan sabitlenince sonuç değişmez. A5'te yalnızca şarj kuralı crisp yapılınca yöntem 11/30 çevrimde çöker. Crisp kural SC'yi yalnızca talep $P_{lo}$'nun altındayken ve sabit güçle şarj eder. Agresif sürüşte düşük talep anları azaldığı için şarj, SC'den çekilen enerjiyi karşılamaz. Bulanık kurallar ise talep *Medium* iken de SC boşsa şarja devam eder. Şarj gücü $SoC_{SC}$ düştükçe sürekli artar ve üyelik fonksiyonlarının örtüşmesi şarjı daha geniş bir durum bölgesine yayar. Böylece SC'nin doluluğunu bir banda çeken kendiliğinden bir geri besleme oluşur. Bu da ayardaki %10–20'lik hatalara ve görülmemiş sürüş rejimlerine karşı dayanıklılık sağlar. Bulanık mantığın bu problemdeki asıl değeri, en iyi durumda daha düşük akım vermesi değildir (eğitim çevriminde crisp kural biraz daha iyidir). Asıl değeri, enerji dengesini parametre ayarına bağımlı olmaktan çıkarmasıdır.

**Olumsuz bulgu: uyarlamalı tavanın katkısı yoktur.** S2, crisp kuralın düz kırpma yapısını korumak ve tavanı $SoC_{SC}$'ye göre bulanık olarak ayarlamak için tasarlanmıştı. Ayar küçük bir yayılım seçmiştir ($d_{cap} = 192$ W) ve sabit tavanla (A4) fark yoktur. Doğru ifade şudur: S2'nin kazancı bulanık tavandan değil, kırpma yapısının bulanık şarj geri beslemesiyle birleşmesinden gelir.

**Çıktı değişkeninin seçimi kurallardan daha önemlidir.** S1 ile S2'nin kuralları ve şarj yasası aynıdır, yalnızca birinci çıktı farklıdır. S1, talebin bir *yüzdesini* SC'ye verir. Bu yüzden yüksek talepte bataryanın payı da büyür ve tipik çevrimde S2'den 30/30, C0'dan medyanda 9.4 A kötüdür. S2'de batarya gücü bir tavanda kırpılır. Bulanık bir denetleyicide çıktı değişkeninin fiziksel anlamı, kural tabanı kadar belirleyicidir.

**Ödünleşim.** Önerilen yöntem, tepe akımı F0'ın yarısının altına indirirken deşarj süresinde ~%3 kaybeder. F0'ın süre avantajı, SC'yi ilk 20 dakikada boşaltıp ondan sonra hiç kullanmamasından gelir. Bu, kısa bir ölçümde görünmeyen bir davranıştır. Adil baseline B1'e göre S2'nin süresi ortalamada +%0.13'tür, en kötü çevrimde −%0.45'tir. K3 bütün çevrimlerde sağlanır. Tepe akım ve $\Delta T$'deki büyük azalma, bataryanın yaşlanması için bu küçük kaybı karşılamaya değerdir. Ancak bu çalışmada yaşlanma doğrudan modellenmemiştir.

**FRL > FLC neden yeniden üretilemedi?** Q-learning katmanı, kural tabanının yapısal sorununu (bataryadan SC şarjı olmaması) çözemez. Ödül fonksiyonu monoton değildir ve SC'nin durumunu içermez. Ajanın SC'yi koruması bu yüzden dolaylı bir yan etkidir ve kullanımdan vazgeçme pahasına gerçekleşir. Makale tek bir çalıştırma raporlar. FLC ile FRL arasındaki %1–4'lük farklar, bizim 5 tohumlu deneylerimizde tohumdan kaynaklanan değişkenlikten küçüktür. Makalenin donanımında, tam açıklanmamış bir "belirsizlik" geçiş mekanizmasıyla farklı bir sonuç elde edilmiş olabilir. Ancak bu raporlanan bilgilerle doğrulanamaz.

**Hesaplama maliyeti.** Kural sayısının 36'dan 12'ye inmesiyle S2'nin karar süresi F0'ın yaklaşık yarısıdır (84 ve 163 µs, Python). Bütün denetleyiciler 1 s'lik kontrol adımının çok altında çalışır.

# Limitations (Sınırlılıklar)

- **Yalnızca benzetim.** Donanım testi yapılmamıştır. Dönüştürücüler sabit verimli, motor sabit verimli ve batarya basit bir $R_{int}$ modeliyle temsil edilmiştir.
- **Makalede verilmeyen parametreler.** Araç kütlesi, yuvarlanma katsayısı, MF köşe noktaları, FRL eylem kümesi ve termal model tarafımızdan seçilmiştir. Sıcaklık tek bir senaryoya kalibre edildiği için yalnızca göreli olarak yorumlanmalıdır.
- **Sentetik sürüş çevrimleri.** Gerçek sürüş verisi yoktur. Test çevrimleri eğitim çevrimiyle aynı üreteçten gelir ve aynı temel istatistiklere sahiptir. X3 bu nedenle aynı ailedeki çevrimlere genellemeyi ölçer. Eğim, farklı hız profilleri ve standart çevrimler (WMTC vb.) denenmemiştir.
- **Yaşlanma.** Batarya yaşlanması doğrudan modellenmemiştir. Tepe akım, RMS, $I^2t$ ve $\Delta T$ yalnızca vekil göstergelerdir.
- **Kapsam dışı kalanlar.** FRL, X3'te koşturulmamıştır, çünkü X1'de FLC'den ayırt edilemiyordu. Önerilen SCS-FLC'nin üzerine düzeltilmiş ödülle bir Q-learning katmanı (K-FRL) zaman nedeniyle eklenmemiştir. S1'in ayarında bazı en iyi noktalar arama aralığının sınırına yakındır, ancak bütçe eşitliğini bozmamak için aralıklar sonradan genişletilmemiştir.

# Conclusion (Sonuç)

Bu projede, E2W batarya/SC HESS'i için önerilen FRL tabanlı EMS [1] Python'da yeniden gerçekleştirilmiştir. Sadece-batarya baseline'ı makaleyle uyumludur. FLC'nin tepe akım azalması SC dolu olduğu sürece yeniden üretilmiştir. Bununla birlikte makalenin kural tabanının SC'yi uzun sürüşte boşalttığı, menzil kazancının yaklaşık üçte ikisinin rejenerasyondan geldiği ve FRL'nin FLC'ye üstünlüğünün istatistiksel olarak yeniden üretilemediği gösterilmiştir.

Bu bulgulara dayanarak, iki girdili ve 12 kurallı bir Mamdani denetleyicisi (SCS-FLC) önerilmiştir. Bu denetleyici SC'yi bir güç tamponu olarak kullanır ve bataryadan bulanık bir yasayla yeniden şarj eder. Önerilen S2 varyantı, görülmemiş 30 çevrimde hiç çökmeden ortalama tepe batarya akımını F0'a göre %55, eşit bütçeyle ayarlanmış crisp kurala göre %35 düşürmüştür ($p = 1.7 \times 10^{-6}$). Parametre bozulmalarında en fazla %12 kötüleşmiştir (crisp kuralda %138). Ablasyonlar, dayanıklılığın kaynağının SoC'ye uyarlanan tavan değil, sürekli değişen bulanık şarj yasası olduğunu göstermiştir. Bedel, F0'a göre ~%3 daha kısa deşarj süresidir.

**Gelecek çalışmalar:** SCS-FLC'nin üzerine monoton ve $SoC_{SC}$ terimi içeren bir ödülle Q-learning katmanı (K-FRL). Ölçüm belirsizliğini doğrudan modellemek için tip-2 bulanık kümeler [23]. Gerçek sürüş kayıtları ve standart çevrimlerle test. Elektrokimyasal bir yaşlanma modeli. Donanım-döngüde (HIL) doğrulama.

# Generative AI Usage Disclosure (Üretken Yapay Zekâ Kullanım Beyanı) {.unnumbered}

Bu projede üretken yapay zekâ aracı olarak Anthropic'in Claude modeli kullanılmıştır. Kullanım alanları şunlardır:

- Python kodunun ve birim testlerinin yazılması, hata ayıklama.
- Deney betiklerinin ve grafiklerin hazırlanması.
- Literatür taramasında aday kaynakların bulunması.
- Proje dokümanlarının ve bu raporun taslak metninin yazılması ve dil düzenlemesi.

Proje adımları, araca her aşamada açık talimat verilerek ve her alt adımın sonucu incelenip onaylanarak yürütülmüştür. Tasarım kararları (varsayımlar, katkının seçimi, S2 varyantının eklenmesi) bu süreçte değerlendirilip onaylanmıştır. Doğrulama şöyle yapılmıştır:

- Kodun doğruluğu 96 birim testiyle kontrol edilmiştir.
- Bütün tablo ve grafikler repodaki betiklerle yeniden üretilmiştir.
- Rapordaki sayılar `results/tables/` dosyalarıyla karşılaştırılmıştır.
- Kaynakların her biri DOI veya yayıncı sayfası üzerinden doğrulanmıştır; doğrulanamayan künye bilgileri kaynakçaya alınmamıştır.

# References (Kaynaklar) {.unnumbered}

```{=latex}
\small
```

\[1\] N. Kumaresan and A. Rammohan, "Fuzzy reinforcement learning-based energy management strategy for the integration of hybrid energy storage system of electric vehicle," *Results Eng.*, vol. 28, Art. no. 107875, 2025, doi: 10.1016/j.rineng.2025.107875.

\[2\] R. Pan, J. Li, D. Yang, and Y. Yan, "A fuzzy RL-based energy management strategy for battery/supercapacitor hybrid energy storage system with road condition recognition," *IEEE Trans. Transp. Electrific.*, vol. 12, no. 2, pp. 2887–2898, Apr. 2026.

\[3\] B. Xu, J. Shi, S. Li, H. Li, and Z. Wang, "Energy consumption and battery aging minimization using a Q-learning strategy for a battery/ultracapacitor electric vehicle," *Energy*, vol. 229, Art. no. 120705, 2021, doi: 10.1016/j.energy.2021.120705.

\[4\] B. Xu, Q. Zhou, J. Shi, and S. Li, "Hierarchical Q-learning network for online simultaneous optimization of energy efficiency and battery life of the battery/ultracapacitor electric vehicle," *J. Energy Storage*, vol. 46, Art. no. 103925, 2022, doi: 10.1016/j.est.2021.103925.

\[5\] L. Guo, Z. Li, and R. Outbib, "A lifetime extended energy management strategy for fuel cell hybrid electric vehicles via self-learning fuzzy reinforcement learning," in *Proc. 10th Int. Conf. Syst. Control (ICSC)*, Marseille, France, 2022, pp. 161–167, doi: 10.1109/ICSC57768.2022.9993916.

\[6\] D. Yang, S. Wang, Y. Liao, and R. Pan, "An online energy management strategy for fuel cell vehicles based on fuzzy Q-learning and road condition recognition," *IEEE Trans. Intell. Transp. Syst.*, vol. 25, no. 9, Sep. 2024, doi: 10.1109/TITS.2024.3368149.

\[7\] S. Ariche, Z. Boulghasoul, A. El Ouardi, A. Elbacha, A. Tajer, and S. Espié, "Enhancing energy management in battery electric vehicles: A novel approach based on fuzzy Q-learning controller," *Eng. Sci. Technol., Int. J.*, vol. 67, Jul. 2025, Art. no. 102070, doi: 10.1016/j.jestch.2025.102070.

\[8\] R. Xiong, J. Cao, and Q. Yu, "Reinforcement learning-based real-time power management for hybrid energy storage system in the plug-in hybrid electric vehicle," *Appl. Energy*, vol. 211, pp. 538–548, 2018, doi: 10.1016/j.apenergy.2017.11.072.

\[9\] Y. Wu *et al.*, "Driving style-aware energy management for battery/supercapacitor electric vehicles using deep reinforcement learning," *J. Energy Storage*, vol. 73, Art. no. 109199, 2023, doi: 10.1016/j.est.2023.109199.

\[10\] W. Liu, P. Yao, Y. Wu, L. Duan, H. Li, and J. Peng, "Imitation reinforcement learning energy management for electric vehicles with hybrid energy storage system," *Appl. Energy*, vol. 378, Art. no. 124832, 2025, doi: 10.1016/j.apenergy.2024.124832.

\[11\] M. Şen, M. Özcan, and Y. R. Eker, "Fuzzy logic-based energy management system for regenerative braking of electric vehicles with hybrid energy storage system," *Appl. Sci.*, vol. 14, no. 7, Art. no. 3077, 2024, doi: 10.3390/app14073077.

\[12\] S. M. Rakhtala Rostami and Z. Al-Shibaany, "Intelligent energy management for full-active hybrid energy storage systems in electric vehicles using teaching–learning-based optimization in fuzzy logic algorithms," *IEEE Access*, vol. 12, pp. 67665–67680, 2024, doi: 10.1109/ACCESS.2024.3399111.

\[13\] N. Kumaresan and A. Rammohan, "Adaptive neuro fuzzy inference system based optimized energy management strategy for the power integration of battery and supercapacitor in electric vehicle," *J. Energy Storage*, vol. 126, Art. no. 117073, 2025, doi: 10.1016/j.est.2025.117073.

\[14\] X. Chen, M. Li, and Z. Chen, "Meta rule-based energy management strategy for battery/supercapacitor hybrid electric vehicles," *Energy*, vol. 285, Art. no. 129365, 2023, doi: 10.1016/j.energy.2023.129365.

\[15\] M. Al Takrouri, N. R. N. Idris, M. J. A. Aziz, R. Ayop, and W. Y. Low, "Refined power follower strategy for enhancing the performance of hybrid energy storage systems in electric vehicles," *Results Eng.*, vol. 25, Art. no. 103960, 2025, doi: 10.1016/j.rineng.2025.103960.

\[16\] A. Wangsupphaphol, S. Phichaisawat, N. R. N. Idris, A. Jusoh, N. D. Muhamad, and R. Lengkayan, "A systematic review of energy management systems for battery/supercapacitor electric vehicle applications," *Sustainability*, vol. 15, no. 14, Art. no. 11200, 2023, doi: 10.3390/su151411200.

\[17\] L. A. Zadeh, "Fuzzy sets," *Inf. Control*, vol. 8, no. 3, pp. 338–353, 1965, doi: 10.1016/S0019-9958(65)90241-X.

\[18\] E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy logic controller," *Int. J. Man-Mach. Stud.*, vol. 7, no. 1, pp. 1–13, 1975, doi: 10.1016/S0020-7373(75)80002-2.

\[19\] C. J. C. H. Watkins and P. Dayan, "Q-learning," *Mach. Learn.*, vol. 8, pp. 279–292, 1992, doi: 10.1007/BF00992698.

\[20\] R. S. Sutton and A. G. Barto, *Reinforcement Learning: An Introduction*, 2nd ed. Cambridge, MA, USA: MIT Press, 2018.

\[21\] P. Y. Glorennec and L. Jouffe, "Fuzzy Q-learning," in *Proc. 6th IEEE Int. Conf. Fuzzy Syst.*, 1997, pp. 659–662, doi: 10.1109/FUZZY.1997.622790.

\[22\] L. Jouffe, "Fuzzy inference system learning by reinforcement methods," *IEEE Trans. Syst., Man, Cybern. C*, vol. 28, no. 3, pp. 338–355, 1998, doi: 10.1109/5326.704563.

\[23\] J. M. Mendel and R. I. B. John, "Type-2 fuzzy sets made simple," *IEEE Trans. Fuzzy Syst.*, vol. 10, no. 2, pp. 117–127, 2002, doi: 10.1109/91.995115.

