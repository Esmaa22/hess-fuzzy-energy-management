# Referans Makale Analizi (Checkpoint 1)

## 1. Künye

N. Kumaresan and A. Rammohan, "Fuzzy reinforcement learning-based energy management strategy for the integration of hybrid energy storage system of electric vehicle," *Results in Engineering*, vol. 28, p. 107875, 2025, doi: 10.1016/j.rineng.2025.107875. (Açık erişim, CC BY-NC 4.0)

## 2. Problem ve Motivasyon

- **Uygulama alanı:** Elektrikli iki tekerlekli araçlar (E2W: scooter/motosiklet), şehir içi sürüş.
- **Sorun:** Şehir içinde sık yapılan hızlanma ve frenler bataryada ani akım tepelerine yol açar. Bunun sonucunda batarya ısınır, yaşlanması hızlanır ve menzil düşer.
- **Önerilen çözüm:** Batarya ile süperkapasitörün birlikte kullanıldığı bir hibrit enerji depolama sistemi (HESS). Batarya enerjiyi depolar, süperkapasitör kısa süreli yüksek güç patlamalarını ve rejeneratif frenle geri kazanılan enerjiyi karşılar.
- **Asıl karar problemi:** Her zaman adımında motorun talep ettiği gücün ne kadarı bataryadan, ne kadarı süperkapasitörden karşılanacak? Bu kararı enerji yönetim stratejisi (EMS) verir.
- **Bulanık mantığın kullanılma nedeni:** Kural tabanlı bir EMS yorumlanabilir ve belirsizliğe dayanıklıdır, ancak kuralları sabit olduğu için uyarlanabilir değildir. RL kendi kendine öğrenebilir, ancak kara kutu gibi çalışır ve kararlılığı zayıftır. Makale iki yaklaşımı birleştiren bir **Fuzzy RL (FRL)** öneriyor.
- **Yazarların belirttiği literatür boşlukları:**
  1. Çalışmaların çoğu dört tekerlekli araçlar için.
  2. Çoğu çalışma yalnızca standart sürüş çevrimleriyle test ediliyor.
  3. Sıcaklık ve SoC kararlılığı genellikle göz ardı ediliyor.
  4. Rejeneratif fren enerjisi süperkapasitöre iyi yönlendirilmiyor.

## 3. Sistem Tanımı

### 3.1 Araç (Tablo 2)
| Parametre | Değer |
|---|---|
| Motor gücü | 6.2 kW |
| Motor torku | 26 N·m |
| Tekerlek yarıçapı | 0.23 m |
| Ön alan | 0.88 m² |
| Sürükleme katsayısı Cd | 0.22 |
| Aktarma verimi η | 0.95 |
| Tırmanma kabiliyeti | 20° |
| **Araç kütlesi, yuvarlanma direnci** | **Verilmemiş** |

### 3.2 Batarya paketi (Tablo 3)
- 18650 NMC hücre: 3.35 Ah, 3.6 V. Şarj akımı en fazla 1C, deşarj akımı en fazla 3C.
- Paket 14s × 22p: 50.4 V, 73.7 Ah, 3.7 kWh.

### 3.3 Süperkapasitör paketi
- Hücre: 500 F, 2.7 V, 0.01 Ω.
- Paket 18s × 15p: makaleye göre 48 V, 406 F, 0.012 Ω ve en fazla 48 kW deşarj gücü.
- Kendi hesabımız: C = 500·15/18 ≈ 417 F ve E = ½CV² ≈ 0.49 MJ ≈ **136 Wh**. Bu, bataryanın enerjisinin yaklaşık %3.7'si.

### 3.4 DC/DC dönüştürücüler
- Bataryada tek yönlü, süperkapasitörde çift yönlü dönüştürücü var. İkisi de 50 kHz'de çalışıyor ve hedef verimleri %96.
- Mimari aktif HESS: iki kaynak da dönüştürücü üzerinden kontrol ediliyor.

### 3.5 Güç talebi (Denklem 1)
P_dem = P_accel + P_cruise + P_resistive − P_regen

Aerodinamik direnç, yuvarlanma direnci ve eğim kuvvetleri dahil. Rejeneratif fren geri kazanım oranı **sabit %20** alınmış.

## 4. Yöntem

### 4.1 Katman 1: Bulanık Mantık Kontrolcüsü (FLC)
- **Çıkarım tipi:** Mamdani olduğu anlaşılıyor (açıkça yazılmamış). Üyelik fonksiyonları yamuk (trapezoidal).
- **Girdiler (Tablo 4):**
  | Girdi | Dilsel değerler | Aralık |
  |---|---|---|
  | Batarya SoC | Low, Medium, High | [0, 100] % |
  | Süperkapasitör SoC | Low, Medium, High | [0, 100] % |
  | Motor güç talebi | Low, Medium, High, Regeneration | [−5100, 5600] W |
- **Çıktılar:**
  | Çıktı | Dilsel değerler | Aralık |
  |---|---|---|
  | Batarya güç katsayısı C_B | 0, 40, 55, 65, 70, 75, 100 % | [0, 100] |
  | Süperkapasitör güç katsayısı C_SC | 0, 20, 25, 30, 35, 45, 60 % | [0, 100] |
- **Kural tabanı:** 3 × 3 × 4 = **36 kural** (Tablo 5). Hücrelerde C_B / C_SC (%) değerleri var:

  **Batarya SoC = Low**
  | SC SoC \ P_dem | Low | Medium | High | Regen |
  |---|---|---|---|---|
  | Low | 100/0 | 100/0 | 75/25 | 0/20 |
  | Medium | 70/30 | 70/30 | 65/35 | 0/20 |
  | High | 40/60 | 40/60 | 40/60 | 0/0 |

  **Batarya SoC = Medium**
  | SC SoC \ P_dem | Low | Medium | High | Regen |
  |---|---|---|---|---|
  | Low | 75/25 | 75/25 | 75/25 | 0/20 |
  | Medium | 55/45 | 55/45 | 55/45 | 0/20 |
  | High | 40/60 | 40/60 | 40/60 | 0/0 |

  **Batarya SoC = High**
  | SC SoC \ P_dem | Low | Medium | High | Regen |
  |---|---|---|---|---|
  | Low | 100/0 | 100/0 | 75/25 | 0/20 |
  | Medium | 65/35 | 65/35 | 65/35 | 0/20 |
  | High | 40/60 | 40/60 | 40/60 | 0/0 |

- **Kuralların mantığı:**
  - Süperkapasitör SoC'si yükseldikçe yükün daha büyük kısmı süperkapasitöre kayıyor (%60'a kadar).
  - Rejenerasyonda batarya hiç şarj edilmiyor. Süperkapasitör SoC'si Low veya Medium ise enerjinin %20'si süperkapasitöre gidiyor, High ise hiç geri kazanım yapılmıyor.
  - Kuralların büyük kısmında güç talebi seviyesinin sonuca etkisi yok. Sadece SC SoC = Low veya Medium iken High talepte fark yaratıyor.

### 4.2 Katman 2: Q-learning
- **Ajan:** FRL kontrolcüsü. **Ortam:** aracın güç sistemi.
- **Durum:** İki SoC değeri ve güç talebinin ayrık kategorileri (3 × 3 × 4 = 36 durum).
- **Eylem:** Güç paylaşım oranı. Eylem kümesinin içeriği **açıkça tanımlanmamış**.
- **Geçiş (Denklem 2–4):**
  - SoC_B(t+1) = SoC_B(t) − C_B·P_d / E_B
  - SoC_SC(t+1) = SoC_SC(t) − C_SC·P_d / E_SC
  - Rejenerasyonda süperkapasitör için aynı denklem α = 0.2 çarpanıyla kullanılıyor.
- **Ödül (Denklem 5):**
  | Koşul | Ödül |
  |---|---|
  | P_d < 0 ve C_B = 0, C_SC > 0 (frenleme enerjisi süperkapasitöre gidiyor) | +1 |
  | P_d > 0 ve C_SC ≥ 50 % | +0.5 |
  | P_d > 0 ve C_SC = C_B | 0 |
  | P_d > 0 ve C_B ≥ 75 % | −0.5 |
  | P_d > 0 ve C_B > 0 | −1 |
  | SoC_B < SoC_min | −1.5 |
- **Hiperparametreler:**
  - Öğrenme oranı α = 0.1, indirim katsayısı γ = 0.9.
  - ε-greedy keşif: ε 1.0'dan başlıyor, her bölümden sonra 0.995 ile çarpılıyor, alt sınırı 0.01.
- **Güncelleme kuralı:** Q[s,a] ← Q[s,a] + α (r + γ·max Q[s′,:] − Q[s,a])
- **Eğitim akışı (Tablo 6):** Kural tabanı ve Q tablosu başlatılır → ε-greedy ile eylem seçilir → bulanık çıkarım yapılır → ödül gözlenir → Q güncellenir → ε azaltılır → N bölümden sonra eğitim durur.

### 4.3 FLC ile RL nasıl birleşiyor
- **Belirsizliğin düşük olduğu durumlar:** FLC'nin kararı doğrudan uygulanıyor.
- **Belirsizliğin yüksek olduğu durumlar** (ani ivmelenme, rejenerasyondaki dalgalanma, yaşlanma, sürüş çevriminin değişmesi): RL devreye girip kararı ayarlıyor.
- **Belirsizliğin nasıl ölçüldüğü ve geçişin hangi eşikte olduğu tanımlanmamış.**

## 5. Deney Düzeni
- **Ortam:** MATLAB/Simulink ve donanım test platformu (batarya, süperkapasitör, DC/DC dönüştürücüler, inverter, motor, veri toplama sistemi).
- **Veri:** Gerçek bir sürüşün hız profili, MATLAB Mobile ile kaydedilmiş. 900 s, 12.4 km, en yüksek hız 83 km/h, ortalama hız 49.6 km/h, ivme +2.7 / −2.6 m/s². Veri "istek üzerine" paylaşılıyor.
- **Karşılaştırılan durumlar:** (1) sadece batarya, (2) FLC tabanlı EMS, (3) FRL tabanlı EMS.
- **Ortam sıcaklığı:** 20 °C.

## 6. Raporlanan Sonuçlar
| Ölçüt | Sadece batarya | FLC | FRL |
|---|---|---|---|
| Tepe batarya akımı (A) | 132 | 102 | 97.9 |
| Ortalama batarya akımı (A) | 84.8 | 54 | 52.4 |
| RMS akım (A) | 40.40 | 39.69 | 36.10 |
| I²t (A²s) | 1.14e7 | 1.03e7 | 9.12e6 |
| Severeness index | 0.455 | 0.427 | 0.401 |
| Hücre sıcaklık artışı (°C) | 2.1 | 1.95 | 1.9 |
| %100'den %20 SoC'ye süre (s) | 6540 | 6950 | 6990 |
| Batarya tepe gücü / SC tepe gücü (W) | 5930 / – | 4385 / 1850 | 4535 / 2050 |
| Menzil (km) | 88.95 | 94.34 | 95.06 |
| Enerji tüketimi (Wh/km) | 41.59 | 39.21 | 38.93 |

Ek bir analiz olarak DC/DC verimi %100'den %91'e düşürüldüğünde FRL > FLC > sadece batarya sıralamasının korunduğu gösterilmiş (Şekil 14).

## 7. Yazarların Kabul Ettiği Sınırlılıklar
- Rejeneratif fren verimi sabit %20 alınmış.
- Batarya yaşlanması (kapasite kaybı, iç direnç artışı) modelde yok.
- Tek bir sürüş profili ve tek bir ortam sıcaklığı kullanılmış.

## 8. Eleştirel Notlar: Tutarsızlıklar ve Belirsizlikler

### 8.1 Yeniden üretimi engelleyen eksik bilgiler
1. Üyelik fonksiyonlarının köşe noktaları verilmemiş, sadece aralıklar var.
2. Araç kütlesi ve yuvarlanma direnci katsayısı verilmemiş.
3. Q-learning'in eylem kümesi, eğitimdeki bölüm sayısı N ve SoC_min değeri tanımlanmamış.
4. Q tablosunun FLC kurallarını nasıl güncellediği ve "belirsizlik" geçişinin nasıl yapıldığı belirsiz.
5. Denklem 2–3'te zaman adımı Δt ve birimler yok.
6. Batarya ve süperkapasitör katsayılarının toplamının 100 olup olmadığı belirtilmemiş. Örneğin 40/60 toplamı 100, ama rejenerasyonda 0/20 veya 0/0 var. Kalan gücün nereye gittiği (mekanik fren olabilir) açıklanmamış.
7. Sıcaklığın hangi termal modelle hesaplandığı ya da nasıl ölçüldüğü belli değil.
8. Hız profili verisi açık değil.

### 8.2 Sayısal ve yazımsal tutarsızlıklar
1. **Ortalama ve RMS akım çelişkisi:** RMS akım her zaman ortalama akımın mutlak değerinden büyük ya da ona eşittir. Oysa sadece batarya durumunda ortalama 84.8 A, RMS 40.4 A verilmiş. Bu matematiksel olarak imkânsız. Ayrıca 84.8 A × 50.4 V ≈ 4.3 kW ortalama güç, 12.4 km'lik 900 s'lik sürüşte yaklaşık 86 Wh/km eder. Bu da raporlanan 41.59 Wh/km ile uyuşmuyor.
2. **Menzil hesabı:** Menzil, paketin tüm enerjisi tüketime bölünerek hesaplanmış görünüyor: 3700 / 41.59 ≈ 88.96 km, 3700 / 38.93 ≈ 95.04 km. Ancak metinde deşarj %20 SoC'de kesiliyor. %80'lik kullanılabilir enerjiyle hesaplanırsa menzil yaklaşık 71 km olurdu.
3. **Özet ile tablo arasındaki fark:** Özette tepe akım azalmaları "sadece bataryaya göre %3, FLC'ye göre %23" diye yazılmış. Doğrusu tam tersi. Tablo 8'de ise FRL için %26 deniyor. (132 − 97.9) / 132 = **%25.8**.
4. **Birim hatası:** Tablo 8'de enerji tüketiminin birimi "kWh/km" yazılmış, doğrusu Wh/km.
5. **Aralık dışı talep:** Güç talebinin bulanık aralığı [−5100, 5600] W, ama raporlanan tepe talep 5930 W bu aralığın dışında.
6. **Denklem numarası:** Ödül fonksiyonu metinde Denklem (4) olarak anılıyor, doğrusu (5). Ayrıca Tablo 2'de aktarma verimi "0.95 %" yazılmış.
7. **Ödül fonksiyonu tutarsız:**
   - Koşullar birbirini dışlamıyor. Örneğin C_B = 40 ve C_SC = 60 iken hem +0.5 hem −1 koşulu sağlanıyor.
   - P_d > 0 iken C_B > 0 durumunun her zaman −1 alması, bataryanın her kullanımını cezalandırıyor. Bu, kural tabanının kendisiyle çelişiyor.
8. **İstatistik eksikliği:** FLC'ye göre kazançlar küçük (yaklaşık %0.6–3). Tekrar sayısı, güven aralığı ya da std raporlanmamış (kısaltmalarda "CI" ve "SI" geçse de).

## 9. Projeye Etkileri

### 9.1 Minimum yeniden üretim (MRR) önerisi
Python'da şu bileşenler kurulacak:
1. Boylamsal araç dinamiği ve güç talebi modeli
2. Batarya modeli (eşdeğer devre: R_int ve SoC)
3. Süperkapasitör modeli (C ve ESR)
4. 36 kurallı, yamuk üyelik fonksiyonlu Mamdani FLC
5. FLC'nin üzerine kurulan Q-learning katmanı (FRL)
6. Üç durumun tek bir şehir içi sürüş profilinde karşılaştırılması: tepe/ortalama/RMS akım, I²t, SoC süresi, Wh/km ve menzil
7. Sonuçların makaledeki Tablo 7–8 ile **göreli değişim** üzerinden kıyaslanması. Donanım farkı nedeniyle mutlak değerlerin birebir tutması beklenmiyor.

### 9.2 Bizim belirlememiz gereken varsayımlar (Adım 3'te)
- Üyelik fonksiyonlarının köşe noktaları
- Araç kütlesi (yaklaşık 120 kg araç ve 70 kg sürücü) ve yuvarlanma direnci katsayısı (yaklaşık 0.015)
- Sürüş profili (WMTC veya benzeri bir şehir içi profil)
- Q-learning'in eylem kümesi, bölüm sayısı ve SoC_min
- Δt = 1 s
- Termal model (birinci dereceden, I²R ısınma)

### 9.3 Katkı için açık kapılar
- Ödül fonksiyonunun tutarlı hale getirilmesi ve akım değişim hızı cezası eklenmesi
- Type-2 bulanık sistem
- Farklı sürüş çevrimleriyle dayanıklılık testi
- Değişken rejeneratif fren modeli
- İstatistiksel karşılaştırma (çoklu seed)
