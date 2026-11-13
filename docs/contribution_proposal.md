# Katkı Önerisi (Checkpoint 4)

**Önerilen katkı:** Süperkapasitör enerjisini koruyan bulanık EMS (**SCS-FLC**, *SC-sustaining FLC*).
Yeniden tasarlanmış kural tabanı ve bataryadan SC'ye yeniden şarj için yeni bir çıktı değişkeni içerir.

**Yönergedeki katkı türleri:**
- Rule base değişikliği
- Yeni output değişkeni
- Yeni deney senaryosu
- Gürültü/robustness analizi
- Ablation study

---

## 1. Ne değiştirilecek? (özet)

| Bileşen | Referans FLC (makale, Tablo 5) | Önerilen SCS-FLC |
|---|---|---|
| Girdiler | SoC_B, SoC_SC, P_dem | SoC_SC, P_dem (SoC_B ablasyonda geri eklenir) |
| Kural sayısı | 36 | 12 (4 × 3) |
| Çıktı 1 | C_SC: SC'nin talep payı | C_SC: aynı anlam, yeni kurallar |
| Çıktı 2 | – | **P_ch**: düşük talepte bataryadan SC'ye şarj gücü [W] (yeni) |
| SC'nin rolü | Her talep seviyesinde %25–60 pay → SC ~1070 s'de boşalıyor | Yalnızca yüksek talepte kullanılır; düşük talepte yeniden doldurulur |
| Çıkarım | Mamdani, min-max, centroid | Aynı (kendi motorumuz `src/hess/fuzzy.py`) |

Çıktı 1'in anlamı makaledekiyle aynı tutuluyor. Böylece:
- (a) Karşılaştırmada yalnızca kurallar değişmiş oluyor.
- (b) Makalenin Q-learning katmanı (Δ C_SC eylemleri) hiç değişmeden SCS-FLC'nin üstüne konabiliyor (§4, isteğe bağlı K-FRL).

**Simülatördeki tek değişiklik:**
- Çekiş sırasında negatif SC isteğine, yani bataryadan SC'ye şarja izin veriliyor.
- Güvenlik katmanının diğer bütün sınırları aynı kalıyor. Batarya akımı bu durumda da deşarj yönünde.
- Dolayısıyla makaledeki "batarya dönüştürücüsü tek yönlü" kabulü bozulmuyor (D-15).

---

## 2. Neden? (bilimsel ve teknik gerekçe)

### 2.1 Yeniden üretimden gelen bulgular
1. **Literal FLC SC'yi tüketiyor (§11, bulgu 3).**
   - Tablo 5, düşük ve orta talepte de SC'ye %25–45 pay veriyor. SC ~1070 s'de boşalıyor.
   - Uzun deşarjda tepe akım azalması bu yüzden −%26'dan −%0.7'ye düşüyor.
   - Makalenin −%22.7'lik tepe akım iddiası yalnızca ilk çevrim için geçerli.
2. **FRL SC'yi koruyor ama kullanmıyor (§11.4).**
   - Monoton olmayan ödül, SoC_SC Low iken SC payını kısmayı öğretiyor.
   - SC %15–30'da atıl kalıyor; tepe akım azalması −%3.1.
3. **FRL ile FLC ayırt edilemiyor (§11.2, E4).** Fark tüm deneylerde 0.7 std'nin altında. Q-learning katmanı, temeldeki kural tabanının yapısal sorununu çözmüyor.
4. **SoC_B girdisinin etkisi çok küçük.** Tablo 5'te SoC_B = Low ve High satırları, tek hücre dışında aynı (70/30 – 65/35). Bu durum girdinin kaldırılıp kural tabanının 36'dan 12'ye indirilmesini destekliyor. Etkisi ablasyonla ayrıca ölçülecek.

### 2.2 Fiziksel gerekçe
- SC'nin kullanılabilir enerjisi ~97 Wh (V_max/2'ye kadar), batarya paketinin ~%2.6'sı.
- Bu kadar küçük bir tampon enerji kaynağı olarak kullanılırsa birkaç dakikada tükenir.
- Literatürde HESS'te SC'nin doğru rolü güç tamponu olarak tanımlanıyor: tepe güçleri karşılamak ve SoC'yi bir hedef bantta tutmak (charge-sustaining). Bu konu Adım 2'deki literatür taramasında da öne çıkıyordu.

### 2.3 Ön deneme: crisp eşik kuralı
Betik: `experiments/proposed/probe_crisp_threshold.py`. Tablo: `results/tables/probe_crisp_threshold.csv`. Koşul: uzun deşarj.

Kural:
- P > P_th ise SC, P − P_th kadarını karşılıyor.
- Düşük talepte batarya SC'yi P_ch ile hedef SoC'ye kadar dolduruyor.

| EMS | Tepe I_B | %99 I_B | RMS I_B | ΔT | Deşarj süresi | En düşük SoC_SC |
|---|---|---|---|---|---|---|
| Sadece batarya | 137.1 A | 132.3 A | – | 2.10 °C | – | – |
| FLC (literal) | −%0.7 | 127.7 A | −%9.3 | 1.88 °C | +%10.7 | 0.00 |
| Crisp, P_th = 3000, P_ch = 1000 | **−%53.0** | **63.9 A** | −%22.1 | **1.26 °C** | +%8.1 | 0.42 |
| Crisp, P_th = 3000, P_ch = 500 | −%1.3 | 109.9 A | −%19.6 | 1.56 °C | +%9.7 | 0.00 |
| Crisp, P_th = 2500, P_ch = 1000 | −%1.1 | 90.9 A | −%23.7 | 1.40 °C | +%8.3 | 0.00 |
| Crisp, P_th = 3500, P_ch = 500 | −%44.9 | 74.7 A | −%19.0 | 1.38 °C | +%8.5 | 0.45 |

Çıkarımlar:
1. **Fikir çalışıyor.** SC korunduğunda tepe akım uzun deşarj boyunca yaklaşık yarıya iniyor. Sıcaklık artışı da literal FLC'den ~%33 düşük.
2. **Crisp kural kırılgan.** Sonuç, SC'den çekilen ve SC'ye geri konan enerjinin dengesine bağlı.
   - Denge bozulunca (P_th biraz düşük ya da P_ch biraz küçük) SC yine boşalıyor ve kazanç tümüyle kayboluyor: −%53'ten −%1.3'e.
   - Yani komşu parametreler arasında bir uçurum var. Doğru parametreler sürüş çevrimine göre değişeceği için ayarlanmış bir crisp kural başka bir çevrimde çökebilir.
3. **Bulanık mantığın gerekçesi:**
   - SCS-FLC'de SC'nin talep payı ve şarj gücü SoC_SC'nin sürekli bir fonksiyonu. SC boşaldıkça pay kendiliğinden azalıyor, şarj kendiliğinden artıyor.
   - Bu doğal bir geri besleme oluşturuyor ve SoC_SC'yi bir banda çekmesi bekleniyor. Böylece enerji dengesi parametre ayarına bağımlı olmaktan çıkıyor.
   - Bu hipotez K4 ile test edilecek.
4. **Bedel:** Bataryadan SC'ye şarj iki kez dönüştürücüden geçtiği için deşarj süresi kazancı literal FLC'den 2–3 puan düşük. Yine de E6'nın (+%7.1) üstünde. Bu ödünleşim raporlanacak.

---

## 3. SCS-FLC tasarım taslağı

**Girdi üyelik fonksiyonları:**
- Makaledekiyle aynı tutuluyor: P_dem 4 terim, SoC_SC 3 terim, yamuk, Ruspini bölümlemesi.
- Böylece fark yalnızca kurallardan ve yeni çıktıdan geliyor.
- MF değişikliği ayrı bir ablasyon olarak ele alınacak.

**Kural tabanı taslağı (C_SC % / P_ch):**

| P_dem \ SoC_SC | Low | Medium | High |
|---|---|---|---|
| Low (< ~1.5 kW) | 0 / **Yüksek** | 0 / Orta | 0 / 0 |
| Medium | 0 / Düşük | 10 / 0 | 25 / 0 |
| High (> ~3.5 kW) | 20 / 0 | 45 / 0 | 60 / 0 |
| Regeneration | kabul 100 / 0 | kabul 100 / 0 | kabul 100 / 0 |

Dilsel okuma:
- **Yüksek talep:** "Talep yüksekse ve SC doluysa yükü SC'ye ver."
- **Düşük talep:** "Talep düşükse ve SC boşalmışsa bataryadan SC'yi doldur."

Notlar:
- P_ch çıktı terimleri {0, Düşük ≈ 300 W, Orta ≈ 700 W, Yüksek ≈ 1200 W}. Kesin değerler Adım 7'de belirlenecek. Ayar, crisp kuralla **aynı değerlendirme bütçesiyle** ve yalnızca eğitim çevriminde yapılacak.
- Rejenerasyonda batarya şarj kabul etmiyor (makale, C_B = 0). Bu yüzden frenleme enerjisi SC'ye veriliyor; SC doluysa güvenlik katmanı fazlasını mekanik frene aktarıyor.

---

## 4. Karşılaştırılan yöntemler

| Kod | Yöntem | Rolü |
|---|---|---|
| B0 | Sadece batarya | Makale baseline'ı |
| B1 | Sadece batarya + rejenerasyon (E6) | Adil baseline |
| F0 | Literal FLC (Tablo 5) | Referans yöntem |
| R0 | FRL (makale ödülü, 5 seed) | Referans yöntem |
| C0 | Crisp eşik + şarj (ayarlı) | Bulanık olmayan kontrol grubu |
| **S1** | **SCS-FLC** | **Önerilen** |
| A1 | Ablasyon: S1'in kuralları, P_ch = 0 | Yeniden şarjın katkısı |
| A2 | Ablasyon: Tablo 5 + P_ch çıktısı | Kural tabanı değişikliğinin katkısı |
| A3 | Ablasyon: S1 + SoC_B girdisi (36 kural) | SoC_B'nin gerekliliği |
| K-FRL | *(isteğe bağlı)* S1 + Q-learning, düzeltilmiş ödül | Zaman kalırsa |

**K-FRL'deki düzeltilmiş ödül:** Monoton olacak, bir SoC_SC hedef bandı terimi ve bir tepe akım cezası içerecek.

---

## 5. Deney tasarımı

| # | Deney | Amaç |
|---|---|---|
| X1 | Uzun deşarj, tüm yöntemler (E1 ile aynı koşul) | Ana karşılaştırma |
| X2 | Ablasyon A1–A3 | Her değişikliğin ayrı katkısı |
| X3 | **Test çevrimleri:** 3 rejim (sakin / nominal / agresif; mikro dalgalanma 0.5 / 1.0 / 1.5 m/s) × 10 seed = 30 çevrim | Genelleme. Ayar yalnızca eğitim çevriminde (seed 7) yapılıyor |
| X4 | Parametre duyarlılığı: C0'ın eşiği ve P_ch'si, S1'in P_dem MF sınırları ve P_ch seviyeleri ±%10 ve ±%20 | Kırılganlık (§2.3, çıkarım 2) |
| X5 | Ölçüm gürültüsü: SoC_SC ve P_dem'e Gauss gürültüsü (σ = %2, %5) | Gürültü dayanıklılığı |
| X6 | Hesaplama maliyeti (µs/adım) | Gerçek zamanlı uygulanabilirlik |

**Adil karşılaştırma kuralları:**
- Bütün yöntemlerde aynı simülatör, güvenlik katmanı, η_c = 0.96, sürüş çevrimi ve başlangıç koşulları (%100 / %100) kullanılıyor.
- HESS yöntemlerinin hiçbirinde batarya frenlemede şarj olmuyor.
- C0 ve S1 aynı sayıda değerlendirmeyle (~24) ve yalnızca eğitim çevriminde ayarlanıyor. Test çevrimleri ayar sırasında hiç kullanılmıyor.
- FRL sonuçları 5 seed ortalaması ± std olarak veriliyor.
- X3'te yöntemler aynı 30 çevrim üzerinde eşleştirilmiş Wilcoxon işaretli sıra testiyle karşılaştırılıyor.

**Ölçütler:**
- Uzun deşarjda tepe I_B, %99 I_B (tek bir anlık tepeye daha az duyarlı), RMS, I²t, ΔT.
- Deşarj süresi: hem B0'a hem B1'e göre.
- En düşük ve ortalama SoC_SC.
- Karar süresi.

---

## 6. Başarı ölçütleri (önceden tanımlanmış)

| # | Hipotez | Ölçüt |
|---|---|---|
| K1 | SCS-FLC, SC'yi uzun deşarj boyunca kullanılabilir tutuyor | X1'de tepe I_B, F0'a göre ≥ %30 düşük. En düşük SoC_SC ≥ 0.10 |
| K2 | Akım ve sıcaklık yükü azalıyor | X1'de RMS, I²t ve ΔT, F0 ve R0'dan düşük |
| K3 | Menzil kaybı kabul edilebilir | X1'de deşarj süresi B1'den kötü değil (≥ −%1). F0'a göre kayıp ayrıca raporlanıyor |
| K4 | Bulanık sürüm crisp kuraldan daha dayanıklı | X3: 30 çevrimin ortalamasında tepe I_B ≤ C0 ve en kötü durumu C0'dan iyi (p < 0.05). X4: ±%20 bozulmada performans kaybı C0'dan küçük |
| K5 | Her bileşen katkı veriyor | X2: A1 ve A2, S1'den anlamlı derecede kötü. A3 ile S1 arasında fark yok (SoC_B gereksiz) |

Bir hipotez tutmazsa sonuç olduğu gibi raporlanacak ve nedenleri Discussion bölümünde tartışılacak. Yönergenin 6.2 maddesi buna açıkça izin veriyor.
Özellikle K4 tutmazsa, yani ayarlı crisp kural da 30 çevrimde dayanıklı çıkarsa, ana bulgu "SC enerji yönetimi kuralın kendisinden daha önemli" olacak. Bu da raporlanabilir bir sonuç.

---

## 7. Riskler

| Risk | Önlem |
|---|---|
| SCS-FLC'nin geri beslemesi SoC_SC'yi bantta tutmayabilir (örneğin agresif çevrimde) | P_ch seviyeleri ve SoC_SC MF sınırları X4 kapsamında; gerekirse P_ch'ye P_dem Medium kuralı eklenir |
| Yeniden şarj kayıpları menzili B1'in altına düşürebilir | K3 ile izleniyor. Ödünleşim (tepe akım ↔ menzil) bir Pareto grafiğiyle gösterilecek |
| Test çevrimleri sentetik | Limitations bölümünde belirtilecek. Üç farklı rejim çeşitlilik sağlıyor |
| K-FRL eğitimi zaman alıyor (5 seed × ~5 dk) | İsteğe bağlı tutuluyor. Ana katkı FRL'ye bağlı değil |

---

## 8. Adım 7 iş listesi (4. gün)
1. **7.1** `src/hess/scs_flc.py` ve simülatörde bataryadan SC'ye şarj desteği (+ testler).
2. **7.2** C0 ve S1 için eşit bütçeli ayar, yalnızca eğitim çevriminde.
3. **7.3** X1 ve X2 → `experiments/proposed/run_main.py`.
4. **7.4** X3 test çevrimlerinin üretilmesi, X3–X5 → `experiments/proposed/run_robustness.py`.
5. **7.5** *(zaman kalırsa)* K-FRL.
6. **8** Canlı demo (Streamlit). FLC ile SCS-FLC aynı çevrimde yan yana, girdiler kaydırıcıyla değiştirilebilir.

---

## 9. Uygulama sırasında alınan kararlar (Adım 7)

### D-20: Bataryadan SC'ye şarj (simülatör)
- EMS arayüzüne `sc_recharge` bayrağı eklendi (varsayılan `False`).
- Bayrak açık bir EMS, P_dem ≥ 0 iken negatif istek verirse bu bir şarj isteği sayılıyor: P_B,bus = P_dem + P_ch, P_SC,bus = −P_ch.
- Güvenlik katmanı P_ch'yi iki sınıra kırpıyor: SC'nin şarj sınırı (`max_charge_power`) ve batarya gücünün V_oc²/(4R) değerinin %90'ı.
- Bayrak kapalı EMS'lerde (B0, B1, F0, R0) negatif istek eskisi gibi 0'a kırpılıyor.
- **Regresyon kontrolü:** `run_reproduction` değişiklik öncesi ve sonrası çalıştırıldı. E1/E2 tablolarında yalnızca karar süresi (µs) satırı değişti (ölçüm gürültüsü); bütün fiziksel sonuçlar bit düzeyinde aynı.

### D-21: SCS-FLC'de C_SC'nin anlamı
- Referans FLC'de C_SC, C_B ile normalize ediliyor: c_sc = C_SC / (C_B + C_SC). SCS-FLC'de C_B çıktısı yok.
- Bu yüzden C_SC, P_dem'in doğrudan SC'ye giden yüzdesi: P_SC = C_SC/100 · P_dem.
- Frenlemede kabul oranı C_SC/100 (Full = 100 → frenleme gücünün tamamı SC'ye).

### D-22: P_ch çıktısı ve çıktı evrenleri
- P_ch terimleri: Zero / Low / Medium / High = 0 / 300 / 700 / 1200 W (CP4 §3 taslağı). Simetrik üçgen, yarı genişlik 100 W.
- Çekişteki net istek: C_SC/100 · P_dem − P_ch.
- Çıktı evrenleri seviyelerden otomatik kuruluyor: [min − hw, max + hw]. Böylece 7.2'deki ayar seviyeleri değiştirdiğinde D-17'deki sınır yanlılığı geri gelmiyor.
- Bütün sayısal değerler `config/default.yaml` → `scs_flc` altında. Girdi MF'leri yazılmazsa `flc` bölümündekiler kullanılıyor. `SCSFLCEMS(cfg, overrides=...)` ile ayar ve X4 için geçersiz kılınabiliyor.
- Ablasyon A1: `SCSFLCEMS(cfg, recharge=False)`.

### 7.1 duman testi (taslak parametreler, ayarsız; resmî X1 değil)
Uzun deşarj, eğitim çevrimi, %100 / %100 başlangıç:

| | Tepe I_B [A] | %99 I_B [A] | RMS [A] | ΔT [°C] | Deşarj süresi [s] | En düşük SoC_SC |
|---|---|---|---|---|---|---|
| B1 | 137.1 | 132.0 | 48.05 | 2.17 | 7235 | 1.000 |
| F0 | 136.2 | 127.7 | 43.57 | 1.88 | 7477 | 0.000 |
| **S1** | **90.4** | **81.1** | **37.11** | **1.32** | **7332** | **0.279** |
| A1 | 135.8 | 120.7 | 42.47 | 1.81 | 7488 | 0.000 |

- Taslak değerlerle K1 (tepe −%33.6 ≥ %30, SoC_SC ≥ 0.10), K2 (RMS, ΔT < F0) ve K3 (B1'e göre +%1.3) ön sinyal olarak sağlanıyor.
- F0'a göre deşarj süresi −%1.9. Bu, yeniden şarjın dönüştürücü ve ESR kayıplarının bedeli.
- A1 neredeyse F0 ile aynı. Kazancı yeniden şarj üretiyor, kural değişikliği tek başına yetmiyor.
- Kesin sonuçlar 7.2'deki ayardan sonra 7.3'te (X1, X2) üretilecek.

---

## 10. Adım 7.2: Eşit bütçeli ayar

**Yöntem** (`src/hess/tuning.py`, `experiments/proposed/tune.py`, ~50 s):
- Her yöntem 4 parametreyle tanımlanıyor ve 24 değerlendirmeyle ayarlanıyor: başlangıç noktası + 23 Latin hiperküp noktası.
- Tasarım tohumu bütün yöntemlerde aynı (seed 0). Bu yüzden aynı `i` aynı birim tasarım noktasına karşılık geliyor.
- Yalnızca eğitim çevrimi kullanılıyor (seed 7); test çevrimleri hiç kullanılmıyor.
- Deney uzun deşarj (X1 ile aynı koşul).
- Amaç: uygun çözümler arasında en düşük tepe I_B (K1).
- Uygunluk: t_dis ≥ 0.99 · t(B1) (K3) ve en düşük SoC_SC ≥ 0.10. Uygunsuz çözüme +1000 A ceza ekleniyor.
- Ayarlı değerler `config/tuned.yaml` dosyasına yazılıyor. Sonraki deneyler bu değerleri `load_tuned()` ile okuyor.

| Yöntem | Parametreler ve aralıklar | Başlangıç |
|---|---|---|
| C0 | P_th 2000–4500 W, P_lo 500–2500 W, P_ch 300–1800 W, hedef 0.50–0.95 | CP4 ön denemesinin en iyisi (3000 / 1500 / 1000 / 0.8) |
| S1 | k_ch 0.4–1.6, k_csc 0.5–1.5, k_p 0.8–1.3, k_soc 0.75–1.2 (CP4 §3 taslağının çarpanları) | Hepsi 1 |
| S2 | c_cap 2000–4500 W (C0'ın P_th aralığı), d_cap 0–1500 W, k_ch, k_soc | 3000 / 1000 / 1 / 1 |

### Sonuç (eğitim çevrimi, 24 nokta / yöntem)

| | En iyi tepe I_B | Medyan | En kötü | Std | Uygun | Çöken (SC boşalan) |
|---|---|---|---|---|---|---|
| C0 (crisp) | **57.1 A** | 83.4 A | 136.6 A | 27.3 | 17/24 | 6 |
| S1 (SCS-FLC, pay) | 73.2 A | 90.5 A | **105.6 A** | **9.6** | **24/24** | **0** |
| S2 (SCS-FLC, tavan) | 60.8 A | **77.8 A** | 135.2 A | 16.3 | 21/24 | 2 |

(Karşılaştırma: F0'ın tepe I_B değeri 136.2 A, B1'inki 137.1 A.)

Ayarlı değerler:
- C0: P_th 2666 W, P_lo 756 W, P_ch 1713 W, hedef 0.91. Tepe I_B 57.1 A, en düşük SoC_SC 0.17.
- S1: k_ch 1.35, k_csc 1.04, k_p 1.29, k_soc 1.05. Tepe I_B 73.2 A, en düşük SoC_SC 0.55.
- S2: c_cap 2666 W, d_cap 192 W, k_ch 1.53, k_soc 1.16. Tepe I_B 60.8 A, en düşük SoC_SC 0.41.

### Bulgular
1. **En iyi durumda crisp kazanıyor (S1'e karşı yapısal neden).** C0 bataryayı tam P_th'de düz kırpıyor. S1 ise talebin bir *yüzdesini* SC'ye veriyor, yani yüksek talepte batarya payı da büyüyor. Bu yüzden S1'in en iyi tepe akımı C0'ın gerisinde kalıyor.
2. **S1 en dayanıklı yöntem.** 24 noktanın hiçbirinde çökmüyor; en kötü durumu 105.6 A, standart sapması C0'ın üçte biri. Orantılı pay, SC boşalırken kendiliğinden küçülüyor (C_SC'nin SoC_SC Low sütunu). Bu bir doğal geri besleme.
3. **D-23: S2 bu bulgudan sonra eklendi.** Amaç C0'ın düz kırpma yapısını korumak, eşiği ve şarjı ise bulanık geri beslemeye bağlamaktı.
   - S2, en iyi durumda C0'a yaklaşıyor (60.8 A).
   - Medyanda üç yöntemin en iyisi (77.8 A).
   - Çöken nokta sayısı 6'dan 2'ye düşüyor.
4. **Eşleştirilmiş karşılaştırma (aynı birim tasarım noktaları, S2 − C0).**
   - S2, 24 noktanın 19'unda daha düşük tepe I_B veriyor. Medyan fark −2.6 A, Wilcoxon p = 0.015.
   - İkisinin de uygun olduğu 17 noktada medyan fark yalnızca −0.7 A. Yani farkın çoğu C0'ın çöktüğü noktalardan geliyor: S2'nin üstünlüğü ortalama performansta değil, dayanıklılıkta.
   - Not: Eşleştirme birim koordinatlar üzerinden. 1. ve 3. boyutlar (eşik / tavan ve şarj gücü) fiziksel olarak karşılık geliyor, 2. ve 4. boyutlar farklı parametreler.
5. **Ayarlanan S2'de tavan yayılımı küçük çıktı (d_cap = 192 W).** Eğitim çevriminde SoC'ye uyarlanan tavanın katkısı sınırlı; S2'nin kazancı büyük ölçüde bulanık şarj yasasından geliyor (P_ch, SoC_SC arttıkça sürekli azalıyor; crisp'te ise aç-kapa). Bu iddia X2'de S2 için ek ablasyonla sınanacak: d_cap = 0 olan S2 ile C0'ın şarj kuralını kullanan S2 karşılaştırılacak.
6. **Aralık sınırları.** S1'de en iyi noktalar k_p ve k_ch aralıklarının üst ucuna yakın (1.29 / 1.3 ve 1.35–1.57 / 1.6). Daha geniş bir aralık S1'i biraz iyileştirebilirdi. Bütçe eşitliğini bozmamak için aralıklar sonradan genişletilmedi; Limitations bölümünde belirtilecek.

### Sonraki adımlar için sonuç
- K1 eğitim çevriminde üç yöntem için de sağlanıyor (F0'a göre tepe I_B −%46…−%58).
- K4'ün "ortalama tepe ≤ C0" kısmı en iyi noktalar arasında tutmuyor: C0 < S2 < S1.
- Ana sınama X3 (30 test çevrimi) ve X4'te olacak: ayarlı noktalar, görmedikleri çevrimlerde ve bozulan parametrelerde ne kadar dayanıklı?
