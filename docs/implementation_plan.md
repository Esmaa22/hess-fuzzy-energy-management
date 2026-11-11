# Uygulama Planı (Checkpoint 2)

Bu doküman referans makalenin [1] Python'da nasıl yeniden gerçekleştirileceğini tanımlar. Makalede eksik veya belirsiz bırakılan her nokta için yapılan **varsayım (A-xx)** ve **tasarım kararı (D-xx)** gerekçesiyle birlikte listelenmiştir. Rapordaki "Reproduction Methodology" bölümü bu dokümana dayanır.

---

## 1. Geliştirme Ortamı

| Öğe | Seçim |
|---|---|
| Dil | Python 3.13 |
| Kütüphaneler | numpy, scipy, pandas, matplotlib, pyyaml, pytest, streamlit (demo) |
| Bulanık mantık | **Kendi Mamdani motorumuz** (`src/hess/fuzzy.py`). Kodun her satırı açıklanabilir olsun diye hazır kütüphane kullanılmadı. Doğrulama testlerle yapılacak. |
| RL | Kendi tablo Q-learning uygulamamız (numpy). Problem küçük olduğu için derin öğrenme kütüphanesine gerek yok. |
| Tekrar üretilebilirlik | Tüm parametreler `config/default.yaml` dosyasında. Tüm rastgelelik `seed` ile kontrol ediliyor. |
| Zaman adımı | **D-01:** Δt = 1 s (makalede verilmemiş; araç simülasyonlarında yaygın değer) |

---

## 2. Sistem Modeli

### 2.1 Sürüş profili
- **A-01:** Makaledeki gerçek sürüş verisi paylaşılmamış ("istek üzerine"). Bu yüzden makalenin raporladığı istatistiklere uyan **sentetik bir şehir içi profil** üretilecek:

  | İstatistik | Hedef (makale) |
  |---|---|
  | Süre | 900 s |
  | Mesafe | 12.4 km |
  | Ortalama hız | 49.6 km/h |
  | En yüksek hız | 83 km/h |
  | En yüksek ivme / yavaşlama | +2.7 / −2.6 m/s² |

- **Profilin üretilmesi:** Profil, duraklar arasındaki kısa yolculuklardan (mikro-yolculuklar: hızlanma, seyir, yavaşlama, duruş) oluşturulacak. Parametreler sabit bir seed ile seçilecek ve istatistikler hedefe ±%3 içinde eşlenecek.
- **Dosya:** `data/synthetic_urban_900s.csv`
- **D-02:** Uzun deşarj testinde aynı profil, batarya SoC'si %20'ye inene kadar arka arkaya tekrarlanacak. Makaledeki 6540–6990 s'lik deşarj, yaklaşık 7–8 çevrime karşılık geliyor.

### 2.2 Araç dinamiği ve güç talebi
Tekerlekteki güç şöyle hesaplanır:

P_wheel = v · [ m·δ·a + ½·ρ·C_d·A·v² + m·g·C_r·cos θ + m·g·sin θ ]

| Parametre | Değer | Kaynak |
|---|---|---|
| Ön alan A | 0.88 m² | [1] Tablo 2 |
| Sürükleme katsayısı C_d | 0.22 | [1] Tablo 2 |
| Tekerlek yarıçapı | 0.23 m | [1] Tablo 2 |
| Aktarma verimi η_t | 0.95 | [1] Tablo 2 |
| Motor gücü sınırı | 6.2 kW | [1] Tablo 2 |
| **Toplam kütle m** | **195 kg** (120 kg araç + 75 kg sürücü) | **A-02** (makalede yok; 6 kW sınıfı ticari scooterlar için tipik değer) |
| **Yuvarlanma katsayısı C_r** | **0.015** | **A-03** (iki tekerlekliler için literatürde 0.01–0.02 aralığı) |
| Dönen kütle katsayısı δ | 1.05 | A-04 |
| Hava yoğunluğu ρ | 1.2 kg/m³ | Standart |
| Yol eğimi θ | 0 | A-05 (makalede eğim profili yok) |
| **Motor ve inverter verimi η_m** | **0.90 (sabit)** | **A-06** (makalede verim haritası yok) |

DC barasındaki güç talebi şöyle tanımlanır:
- **Çekişte (P_wheel > 0):** P_dem = P_wheel / (η_t·η_m), en fazla 6.2 kW ile sınırlı.
- **Frenlemede (P_wheel < 0):** P_dem = −α_rgb·|P_wheel|. Burada α_rgb = **0.20**. **A-07:** Makaledeki sabit %20 geri kazanım oranı. Aktarma ve motor kayıpları bu orana dahil kabul edilir.

### 2.3 Batarya paketi
- **Yapı:** 14s × 22p, NMC 18650 hücre, 3.35 Ah [1]. Paket kapasitesi Q = 73.7 Ah, enerjisi 3.7 kWh.
- **Model:** Eşdeğer devre, R_int modeli.
  - Açık devre gerilimi V_oc(SoC) için tipik bir NMC eğrisi kullanılacak (**A-08**): hücre başına 3.0 V → 4.2 V, yani paket için 42.0 V → 58.8 V. Bu, makaledeki dönüştürücü giriş aralığı (38.3–59.5 V) ile uyumlu.
  - Hücre iç direnci R_cell = 30 mΩ (**A-09**, 18650 NMC için tipik). Paket direnci R = 30 mΩ · 14 / 22 ≈ 19 mΩ.
  - Akım: I = (V_oc − √(V_oc² − 4·R·P_b)) / (2R)
  - SoC güncellemesi: SoC ← SoC − I·Δt / (3600·Q)
- **Kesme:** SoC_B ≥ %20.

### 2.4 Batarya termal modeli
- **A-10:** Makale sıcaklığın hangi modelle hesaplandığını vermiyor. Bu yüzden toplu parametreli, birinci dereceden bir hücre modeli kullanılacak:

  m_c·c_p·dT/dt = I_cell²·R_cell − hA·(T − T_amb)

  | Parametre | Değer |
  |---|---|
  | Hücre kütlesi m_c | 47.5 g |
  | Özgül ısı c_p | 900 J/(kg·K) |
  | Ortam sıcaklığı T_amb | 20 °C [1] |

- **hA değeri:** Sadece batarya senaryosunda sıcaklık artışı yaklaşık 2 °C olacak şekilde **bir kez kalibre edilip sabitlenecek**.
- Sıcaklık sonuçları mutlak değer olarak değil, **göreli karşılaştırma** olarak yorumlanacak.

### 2.5 Süperkapasitör paketi
- **Yapı:** 18s × 15p, 500 F hücre. Makaleye göre paket 406 F, 48 V ve 0.012 Ω (**D-03:** makalenin paket değerleri doğrudan kullanılacak).
- **Model:** İdeal kapasitör ve seri direnç (ESR).
  - Kapasitör gerilimi: V_c = √(2E/C)
  - Akım: I = (V_c − √(V_c² − 4·ESR·P_sc)) / (2·ESR)
- **D-04, SoC tanımı:** Enerji tabanlı. V_min = V_max/2 alınarak:

  SoC_SC = (V² − V_min²) / (V_max² − V_min²)

  Böylece kullanılabilir enerji ≈ 98 Wh olur. Toplam enerji ½·C·V² ≈ 130 Wh, bunun %75'i kullanılabilir.

### 2.6 DC/DC dönüştürücüler
- **D-05:** İki dönüştürücü için de sabit verim η_c = 0.96 [1]. Dönüştürücüler ideal güç takibi yapıyor kabul edilecek; PWM ve akım kontrol döngüsü modellenmeyecek.
- Gerekçe: Çalışmanın amacı EMS karşılaştırması. Dönüştürücü dinamiği 50 kHz'de, 1 s'lik adımın çok altında kalıyor.
- Verim duyarlılığı (makaledeki Şekil 14: %91–100) ayrı bir deneyle tekrarlanacak.

### 2.7 Güvenlik katmanı (her EMS için ortak)
- **D-06:** EMS'nin ürettiği paylaşım fiziksel olarak uygulanamazsa (süperkapasitör boş veya dolu ya da güç sınırı aşılmışsa) eksik güç bataryadan karşılanır. Frenlemede fazla enerji mekanik frene gider.
- Bu katman üç durum (sadece batarya, FLC, FRL) için de aynı olduğundan karşılaştırma adil kalır.

---

## 3. EMS 1: Sadece Batarya

- **D-07:** Makalede sadece batarya durumunda **rejeneratif fren yok** ([1] Bölüm 4.4). Yeniden üretimde bu aynen uygulanacak.
- **Eleştiri notu:** Bu seçim HESS'in kazancını şişirir. Kazancın bir kısmı süperkapasitörden değil, rejenerasyondan gelir. Bu nedenle **ek bir baseline** olarak "sadece batarya + rejenerasyon" durumu da raporlanacak. Bu, katkı bölümü için de kullanılabilecek bir analiz.

---

## 4. EMS 2: Bulanık Mantık Kontrolcüsü (FLC, Mamdani)

### 4.1 Girdi üyelik fonksiyonları (A-11: makalede köşe noktaları yok, yamuk tipi korunarak seçildi)

| Girdi | Dilsel değer | Yamuk (a, b, c, d) |
|---|---|---|
| SoC_B [%] | Low | (0, 0, 20, 40) |
| | Medium | (20, 40, 60, 80) |
| | High | (60, 80, 100, 100) |
| SoC_SC [%] | Low / Medium / High | SoC_B ile aynı |
| P_dem [W] | Regeneration | (−5100, −5100, −100, 0) |
| | Low | (0, 0, 1000, 2000) |
| | Medium | (1000, 2000, 3000, 4000) |
| | High | (3000, 4000, 5600, 5600) |

- Komşu kümeler %50 örtüşüyor ve bir girdinin üyelik dereceleri toplamı her noktada 1. Bu, Ruspini bölümlemesi denen yapı.
- P_dem, [−5100, 5600] aralığına kırpılır. Böylece makaledeki 5930 W > 5600 W tutarsızlığı da ele alınmış olur.

### 4.2 Çıktı üyelik fonksiyonları
- **A-12:** Makaledeki çıktı seviyelerinin her biri, o değer merkezli ve ±5 genişlikli bir **üçgen** üyelik fonksiyonuyla temsil edilecek.
  - C_B ∈ {0, 40, 55, 65, 70, 75, 100}
  - C_SC ∈ {0, 20, 25, 30, 35, 45, 60}

### 4.3 Çıkarım
| Adım | Yöntem |
|---|---|
| AND operatörü | min |
| Çıkarım (implication) | min (kırpma) |
| Birleştirme (aggregation) | max |
| Durulaştırma | Ağırlık merkezi (centroid), 1001 noktalı ayrık evren |
| Kural tabanı | [1] Tablo 5'teki 36 kural, birebir |

### 4.4 Çıktının güce çevrilmesi
- **D-08, çekişte:** C_B ve C_SC normalize edilir: c_sc = C_SC / (C_B + C_SC). Ardından P_SC = c_sc·P_dem ve P_B = (1 − c_sc)·P_dem.
  - Gerekçe: Çekiş kurallarının hepsinde C_B + C_SC = 100. Ancak bulanık karışım ara bölgelerde toplamı 100'den saptırabilir, talebin tamamı karşılanmak zorunda.
- **D-09, frenlemede:** Kural çıktısı C_SC ∈ {0, 20}. Bu değer süperkapasitörün geri kazanılan enerjiyi **kabul etme oranı** olarak yorumlanır: P_SC,şarj = (C_SC / 20)·|P_dem|. Batarya frenlemede şarj edilmez (C_B = 0).
  - Gerekçe: Makale hem "süperkapasitör tüm rejenerasyon enerjisini emer" diyor hem de %20'lik sabit geri kazanım oranı kullanıyor. Bu yorum ikisini tutarlı hale getiriyor.

---

## 5. EMS 3: Bulanık Pekiştirmeli Öğrenme (FRL)

### 5.1 MDP tanımı
- **Durum (D-10):** FLC'nin dilsel kategorileri kullanılır: (SoC_B: 3) × (SoC_SC: 3) × (P_dem: 4) = **36 durum**. Her girdi için üyelik derecesi en yüksek olan küme seçilir (argmax). Bu yapı makaledeki "durumlar Low, Medium, High ve Regeneration olarak kategorize edilir" ifadesiyle birebir uyuşuyor.
- **Eylem (D-11):** Makalede tanımlı değil. RL'nin **FLC kararını düzeltmesi** fikri ([1] Bölüm 3.3) şu şekilde uygulanır:
  - Eylem kümesi: Δ ∈ {−20, −10, 0, +10, +20} yüzde puan (5 eylem).
  - C_SC = clip(C_SC,FLC + Δ, 0, 100) ve C_B = 100 − C_SC.
  - Δ = 0, "FLC'nin kararını aynen uygula" anlamına gelir. Böylece makaledeki "düşük belirsizlikte FLC, yüksek belirsizlikte RL" mantığı, ajanın hangi durumda Δ = 0'ı öğrendiğine bakılarak **sonuçtan okunabilir** hale gelir.
- **Rejenerasyon durumlarında** RL devreye girmez, FLC kararı uygulanır (D-12).
  - Gerekçe: Makaleye göre frenleme enerjisinin tamamı süperkapasitöre gidiyor. Ödül fonksiyonunun +1'lik terimi de zaten bunu ödüllendiriyor.

### 5.2 Ödül fonksiyonu
- **D-13:** Makaledeki Denklem (5) **olduğu gibi** uygulanır. Koşullar birbirini dışlamadığı için **ilk eşleşen koşul geçerli** sayılır:
  1. SoC_B < SoC_min (= %20) → −1.5
  2. P < 0 ve C_B = 0 ve C_SC > 0 → +1
  3. P > 0 ve C_SC ≥ 50 → +0.5
  4. P > 0 ve C_SC = C_B → 0
  5. P > 0 ve C_B ≥ 75 → −0.5
  6. P > 0 ve C_B > 0 → −1
- **Not:** Bu sıralamada ödül monoton değil. C_B = 55–70 için −1, C_B ≥ 75 için −0.5 veriliyor. Ayrıca ödülde süperkapasitörün SoC'si yer almıyor. Bu iki sorun Adım 6'daki katkı önerisinin ana adayı.

### 5.3 Eğitim
| Parametre | Değer | Kaynak |
|---|---|---|
| Öğrenme oranı α | 0.1 | [1] |
| İndirim katsayısı γ | 0.9 | [1] |
| ε başlangıç / azalma / alt sınır | 1.0 / ×0.995 her bölüm / 0.01 | [1] |
| Bölüm sayısı N | **1000** | **A-13** (ε'un alt sınıra inmesi için ~920 bölüm gerekir) |
| Bir bölüm | Profilin 1 tam geçişi (900 adım) | A-14 |
| Başlangıç durumu | SoC_B ~ U(30, 100), SoC_SC ~ U(30, 100) | A-15 (durum uzayının taranması için) |
| Q tablosu başlangıcı | 0 | – |
| **Seed sayısı** | **5** | **D-14** (makalede yok; sonuçlar ortalama ± std olarak raporlanacak) |

### 5.4 Değerlendirme
- Eğitilmiş Q tablosuyla **açgözlü (greedy) politika** kullanılır (ε = 0).
- Başlangıç: SoC_B = %100, SoC_SC = %100. Profil SoC_B = %20 olana kadar tekrarlanır.

---

## 6. Performans Ölçütleri

| Ölçüt | Tanım | Makaledeki karşılığı |
|---|---|---|
| Tepe batarya akımı | max(I_B) [A] | Tablo 8 |
| Ortalama akım | mean(\|I_B\|) [A] | Şekil 6 |
| RMS akım | √(mean(I_B²)) [A] | Tablo 7 |
| I²t | Σ I_B²·Δt [A²s] | Tablo 7 |
| Severeness index | mean(\|I_B\| / I_rated), I_rated = 73.7 A (1C) | Tablo 7 (A-16: I_rated tanımlı değil) |
| Sıcaklık artışı | max(T) − T_amb [°C] | Tablo 8 |
| Deşarj süresi | %100'den %20 SoC_B'ye geçen süre [s] | Şekil 8 |
| Enerji tüketimi (ECR) | Bataryadan çekilen enerji / mesafe [Wh/km] | Tablo 8 |
| Menzil (DR) | **İki şekilde**: E_paket / ECR (makalenin yöntemi) ve 0.8·E_paket / ECR (%20 kesmeye uygun) | Tablo 8 |
| Süperkapasitör kullanımı | Tepe süperkapasitör gücü, SoC_SC seyri | Şekil 10–12 |
| Çalışma süresi | Adım başına EMS karar süresi [µs] | – (katkı için) |

### Makaleyle karşılaştırma yöntemi
- Sürüş profili, araç kütlesi ve hücre modeli farklı olduğu için **mutlak değerlerin** tutması beklenmez.
- Karşılaştırma **göreli değişimler** üzerinden yapılacak. Örneğin "FLC'nin sadece bataryaya göre tepe akımda sağladığı azalma: makalede %23, bizde %x".
- Bunun yanında **sıralamanın korunup korunmadığı** kontrol edilecek: Sadece batarya > FLC > FRL.

---

## 7. Yazılım Mimarisi

```
config/default.yaml          # tüm parametreler
src/hess/
  __init__.py
  drive_cycle.py             # sentetik profil üretimi ve yükleme
  vehicle.py                 # P_wheel, P_dem
  battery.py                 # R_int modeli, SoC, termal model
  supercap.py                # C + ESR modeli, SoC
  fuzzy.py                   # genel Mamdani motoru (trapezoid, triangle, centroid)
  flc_ems.py                 # 36 kurallı FLC (Tablo 5)
  qlearning.py               # tablo Q-learning ajanı
  frl_ems.py                 # FLC + Q düzeltmesi
  simulator.py               # zaman adımı döngüsü, güvenlik katmanı
  metrics.py                 # Tablo 7–8 ölçütleri
experiments/baseline/
  run_reproduction.py        # 3 durumu çalıştırır, tablo ve grafikleri üretir
  train_frl.py               # FRL eğitimi (5 seed)
tests/
  test_fuzzy.py              # üyelik fonksiyonları, centroid, bilinen girdiler
  test_models.py             # enerji korunumu, SoC sınırları
results/figures/, results/tables/
```

### 2. günün kodlama sırası (Adım 4)
1. `config` + `drive_cycle` → profil istatistiklerinin doğrulanması
2. `vehicle` + `battery` + `supercap` → enerji korunumu testi
3. `simulator` + sadece batarya EMS → ilk akım ve SoC grafikleri
4. `fuzzy` + `flc_ems` → kural yüzeyi grafikleri ve testler
5. `qlearning` + `frl_ems` → öğrenme eğrisi
6. `metrics` + `run_reproduction` → Tablo 7–8'in karşılığı

---

## 8. Deney Planı (Yeniden Üretim)

| # | Deney | Amaç | Makaledeki karşılığı |
|---|---|---|---|
| E1 | Üç durum, uzun deşarj | Akım, sıcaklık, SoC, ECR, menzil karşılaştırması | Tablo 7–8, Şekil 6–8, 13 |
| E2 | Tek çevrimde güç paylaşımı | Batarya ve süperkapasitör güç profilleri | Şekil 9–11 |
| E3 | Süperkapasitör SoC seyri | FLC ve FRL karşılaştırması | Şekil 12 |
| E4 | DC/DC verim taraması (%91–100) | Menzil ve tüketim duyarlılığı | Şekil 14 |
| E5 | FRL öğrenme eğrisi (5 seed) | Yakınsamanın gösterilmesi | – (makalede yok) |
| E6 | Sadece batarya + rejenerasyon | Adil baseline kontrolü | – (eleştiri) |

---

## 9. Riskler ve Önlemler

| Risk | Önlem |
|---|---|
| Sentetik profil makaledeki gerçek profilden farklı | İstatistikler eşleniyor. Karşılaştırma göreli değişimlerle yapılıyor. Katkıda farklı çevrimlerle test edilecek. |
| Makaledeki ödül fonksiyonu ajanı süperkapasitörü tüketmeye itebilir | Literal uygulama korunuyor, gözlenen davranış raporlanacak ve katkının gerekçesi olacak. |
| FRL'nin FLC'ye göre kazancı çok küçük çıkabilir (makalede de ~%0.6–4) | 5 seed ile ortalama ± std raporlanacak, farkın gürültüden büyük olup olmadığı tartışılacak. |
| Sıcaklık modeli kalibrasyona bağlı | Yalnızca göreli değişim yorumlanacak, sınırlılıklar bölümünde belirtilecek. |

---

## 10. Uygulama Sırasında Eklenen Varsayımlar ve Kararlar (Adım 4)

### A-17: Seyirde mikro hız dalgalanması
- **Gözlem:** Pürüzsüz sentetik profilde (yalnızca rampalar ve sabit seyir) sadece-batarya tüketimi **24.7 Wh/km** çıktı. Makaledeki değer **41.59 Wh/km**, yani fark %40.
- **Neden:** Makaledeki profil, gerçek bir sürüşün telefonla yapılmış 1 Hz kaydı. Böyle kayıtlarda sürekli küçük hızlanma ve yavaşlamalar bulunur. Frenlemede enerjinin yalnızca %20'si geri kazanıldığı (A-07) için bu salınımlar tüketimi artırır. HESS'in bastırmaya çalıştığı akım tepeleri de bu salınımlardan gelir.
- **Uygulama:** Seyir bölümlerine AR(1) gürültüsü eklendi: x_k = φ·x_{k−1} + ε_k. Gürültü bir zarfla çarpılarak seyrin iki ucunda sıfıra indiriliyor. Ardışık hız farkı ±1.8 m/s² ile sınırlı. Profilin 6 istatistiği yine birebir tutuyor.
- **Parametre seçimi (φ = 0.5, genlik = 1.0 m/s):** Seyirde RMS ivme 0.83 m/s², hız sapması yaklaşık ±3.5 km/h. Tüketim **32.9 Wh/km**, kalan fark %21.
  - Makaleye tam eşleşme (φ = 0.3, genlik 2.05 m/s → 41.2 Wh/km) mümkün. Ancak bu, seyrin %30'unda |a| > 1.5 m/s² olan, gerçekçi olmayan sert bir sürüş gerektiriyor ve süperkapasitörün faydasını olduğundan büyük gösterebilir. Bu yüzden seçilmedi.
  - Tam eşleşme `make_drive_cycle.py --calibrate` ile yeniden üretilebilir. Duyarlılık analizi için kullanılabilir.
- **Sonuç:** Kalan %21'lik fark Limitations bölümünde raporlanacak. Karşılaştırma, planlandığı gibi göreli değişimler üzerinden yapılacak.

### A-08 ek: Nominal ve fiziksel paket enerjisi
- OCV eğrisinden hesaplanan fiziksel enerji **3.87 kWh** (ortalama V_oc ≈ 3.75 V/hücre). Makaledeki **3.7 kWh** ise nominal gerilimle hesaplanmış: 73.7 Ah × 14 × 3.6 V = 3.71 kWh.
- Simülasyon fiziksel modeli kullanıyor. Menzil formülünde (E_paket / ECR) makaleyle aynı tanımda kalmak için **nominal enerji (3.71 kWh)** kullanılıyor.

### Ayrıklaştırma notu
- Güç, adımın ortalama hızıyla hesaplanıyor: v̄_k = (v_k + v_{k+1})/2, a_k = v_{k+1} − v_k.
- Adım başı hızı v_k kullanılsaydı kapalı çevrimde −½·m·δ·Σ(Δv)² kadar sahte bir enerji kaybı oluşurdu. Orta nokta kullanımıyla kinetik enerji tam korunuyor (`tests/test_models.py`).

### D-15: Sadece-batarya durumunda da dönüştürücü
- Sadece-batarya durumunda da batarya aynı DC/DC dönüştürücüden (η_c = 0.96) geçer.
- Gerekçe: Üç durum arasındaki fark yalnızca EMS'ten gelmeli. Dönüştürücü kaybı bir durumda olup diğerinde olmasaydı karşılaştırma adil olmazdı.
- Makalede batarya dönüştürücüsü tek yönlü. Bu, HESS'te bataryanın frenlemede şarj edilmemesiyle (C_B = 0) tutarlı. E6'daki rejenerasyonlu varyant, karşılaştırma amacıyla çift yönlü kabul edilir.

### D-16: Güvenlik katmanının uygulanışı ve işaret kuralı
- Bara dengesi: P_dem = P_B,bus + P_SC,bus + P_mek. P_mek ≤ 0 ve yalnızca frenlemede oluşur.
- EMS yalnızca süperkapasitörden istenen bara gücünü verir (`sc_request`). Güvenlik katmanı bu isteği iki sınıra göre kırpar:
  - **Deşarj:** Akım, enerji sınırı ile maksimum güç aktarım noktasının (I = V/(2·ESR)) küçüğüyle sınırlanır.
  - **Şarj:** SoC_SC ≤ 1 olacak şekilde sınırlanır.
- Kalan çekiş gücü bataryadan gelir. Kalan fren gücü, izin varsa bataryaya, yoksa mekanik frene gider.

### A-10 sonucu: Termal kalibrasyon
- `calibrate_thermal.py`, sadece-batarya senaryosunda (rejenerasyonsuz, %100 → %20) ΔT = 2.1 °C veren değeri buldu: **hA = 0.0846 W/K/hücre**.
  - Termal zaman sabiti τ ≈ 505 s.
  - 18650 hücrenin yüzeyi ≈ 42 cm² olduğundan h ≈ 20 W/(m²·K), yani hafif hava soğutmasına karşılık gelen makul bir değer.
- Bu değer bundan sonra **sabit**. FLC ve FRL sıcaklık sonuçları bu kalibrasyona göre öngörüdür, ayarlanmaz.

### Bulgu: Makaledeki ECR tanımı
- Makalenin değerleri: 41.59 Wh/km × (6540 s / 900 s × 12.4 km = 90.1 km) ≈ **3748 Wh ≈ paket enerjisinin tamamı**. Oysa %100'den %20'ye kadar paketin yalnızca %80'i harcanıyor.
- Dolayısıyla makaledeki ECR fiilen **E_nominal / (%20'ye kadar gidilen mesafe)**. Menzil formülü (E_paket / ECR) de bu yüzden döngüsel: gidilen mesafeyi geri veriyor.
- Ölçütler bu yüzden iki tanımla raporlanacak:
  - **ECR (makale tanımı)** = E_nominal / mesafe
  - **ECR (fiziksel)** = bataryadan çekilen terminal enerjisi / mesafe

| Ölçüt (sadece batarya, rejenerasyonsuz) | Makale | Bizim model | Fark |
|---|---|---|---|
| Tepe akım | 132 A | 137.1 A | +%3.9 |
| Deşarj süresi | 6540 s | 6755 s | +%3.3 |
| ΔT (kalibrasyon hedefi) | 2.1 °C | 2.10 °C | – |
| ECR (makale tanımı) | 41.59 Wh/km | 39.60 Wh/km | −%4.8 |
| Menzil (makale tanımı) | 88.95 km | 93.81 km | +%5.5 |

- **Sonuç:** A-17'de görülen %21'lik tüketim farkının büyük kısmı modelden değil, tanım farkından kaynaklanıyor. Aynı tanımla fark %5.
