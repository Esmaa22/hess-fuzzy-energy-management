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

---

## 11. Adım 7.3: X1 ana karşılaştırma ve X2 ablasyonlar (eğitim çevrimi)

`experiments/proposed/run_main.py` (~30 s). Ayarlı parametreler `config/tuned.yaml` dosyasından okunuyor. Tablolar `results/tables/X1_*.csv` ve `X2_ablation.csv`, grafikler `results/figures/X1_summary.png`, `X1_soc_current.png` ve `X2_ablation.png`.

> **Uyarı:** Bu çevrim ayarda kullanılan eğitim çevrimi. Buradaki sonuçlar "en iyi durum"u gösteriyor. Genelleme X3'te (30 test çevrimi) sınanacak.

**Kod değişikliği:** Zamanlama sarmalayıcısı `TimedEMS` olarak `simulator.py`'ye taşındı ve artık `sc_recharge` bayrağını da iletiyor. `run_reproduction` bunu kullanıyor. Yeniden üretim tablolarında karar süresi dışında hiçbir değer değişmedi.

### X1: Uzun deşarj (%100 / %100 → SoC_B = %20)

| | Tepe I_B [A] | RMS I_B [A] | I²t [A²s] | ΔT [°C] | Süre, B1'e göre | En düşük SoC_SC | Karar [µs] |
|---|---|---|---|---|---|---|---|
| B0 sadece batarya | 137.1 | 48.0 | 1.56e7 | 2.10 | −%6.6 | – | 0.15 |
| B1 + rejenerasyon | 137.1 | 48.0 | 1.67e7 | 2.17 | 0 | – | 0.15 |
| F0 FLC (Tablo 5) | 136.2 | 43.6 | 1.42e7 | 1.88 | +%3.3 | 0.000 | 183 |
| R0 FRL (5 seed) | 132.9 ± 4.4 | 43.4 ± 0.3 | 1.41e7 | 1.84 ± 0.03 | +%3.2 | 0.030 | 396 |
| C0 crisp (ayarlı) | **57.1** | **35.9** | 9.43e6 | **1.15** | +%1.0 | 0.174 | 0.2 |
| S1 SCS-FLC pay | 73.2 | 37.2 | 1.01e7 | 1.27 | +%0.3 | **0.548** | 140 |
| S2 SCS-FLC tavan | 60.8 | 36.0 | **9.42e6** | 1.17 | +%0.3 | 0.408 | 101 |

**İlk çevrim (SC başlangıçta dolu), tepe I_B:**
- B0 117.0 A, F0 86.2 A, R0 103.9 A.
- C0 49.1 A, S1 61.5 A, S2 49.1 A.

**K1–K3** (`X1_criteria.csv`): Eğitim çevriminde S1, S2 ve C0'ın üçü de bütün ölçütleri sağlıyor.
- K1: Tepe I_B F0'a göre S1'de −%46.2, S2'de −%55.3, C0'da −%58.1. En düşük SoC_SC'nin üçünde de ≥ 0.17.
- K2: RMS, I²t ve ΔT üçünde de hem F0'dan hem R0'dan düşük.
- K3: Deşarj süresi B1'e göre +%0.3 (S1, S2) ve +%1.0 (C0).

**Gözlemler:**
1. **Tepe akım ile menzil arasında bir ödünleşim var.** Önerilen yöntemler, tepe akımı F0'a göre yarıdan fazla düşürüyor ama deşarj süresinde F0'ın ~%3 gerisinde kalıyor (S1/S2 −%2.9). Bu, yeniden şarj zincirindeki kayıpların bedeli: batarya → DC/DC → SC → DC/DC. F0'ın süre avantajı ise SC'yi ilk ~20 dakikada tamamen boşaltıp ondan sonra hiç kullanmamasından geliyor (`X1_soc_current.png`).
2. **SC'nin doluluğu farklı biçimde davranıyor.** S1 ve S2, SC'yi deşarj boyunca 0.4–0.7 bandında tutuyor. C0'da ise SoC_SC zamanla aşağı kayıyor ve deşarjın sonunda 0.17'ye iniyor. Bu, eğitim çevriminde bile C0'ın SC rezervinin ince olduğunu gösteriyor; 7.2'de görülen kırılganlık ile uyumlu.
3. **Hesaplama maliyeti.** S2'nin karar süresi 101 µs, S1'inki 140 µs, F0'ınki 183 µs. Kural sayısının 36'dan 12'ye inmesi süreyi kısaltıyor. Hepsi 1 s'lik zaman adımının çok altında. Crisp kural ise ~0.2 µs.

### X2: Ablasyonlar (uzun deşarj; ablasyonlar yeniden ayarlanmadı)

| Varyant | Tepe I_B [A] | %99 I_B [A] | Süre, B1'e göre | En düşük SoC_SC |
|---|---|---|---|---|
| **S1** | 73.2 | 68.8 | +%0.32 | 0.548 |
| A1: S1, P_ch = 0 | 134.7 | 103.1 | +%3.54 | 0.000 |
| A2: Tablo 5 + P_ch | 89.4 | 82.3 | +%0.97 | 0.225 |
| A3: S1 + SoC_B (36 kural) | 71.5 | 67.4 | +%1.34 | 0.349 |
| **S2** | 60.8 | 56.9 | +%0.28 | 0.408 |
| A1: S2, P_ch = 0 | 137.0 | 127.0 | +%3.37 | 0.000 |
| A3: S2 + SoC_B (36 kural) | 59.9 | 57.2 | +%1.02 | 0.278 |
| A4: S2, sabit tavan (d_cap = 0) | 59.7 | 56.8 | +%0.29 | 0.407 |
| A5: S2 tavanı + C0'ın crisp şarjı | 60.7 | 58.8 | +%0.83 | 0.229 |

**K5 değerlendirmesi** (tek deterministik çevrim olduğu için istatistiksel anlamlılık yok; yönler aşağıda, anlamlılık X3'te sınanacak):
1. **Yeniden şarj (A1) vazgeçilmez.** P_ch olmadan SC iki yöntemde de boşalıyor ve tepe akım F0 seviyesine geri dönüyor. Bu, 7.1 duman testindeki bulguyu ayarlı parametrelerle doğruluyor.
2. **Kural tabanının değişikliği (A2) de katkı veriyor.** Tablo 5'e yalnızca P_ch eklemek tepe akımı 136 A'dan 89 A'ya indiriyor. S1'in yeni kuralları bunu 73 A'ya düşürüyor. Yani kazancın büyük kısmı şarjdan, ~16 A'lık bir kısmı da kural tabanından geliyor.
3. **SoC_B girdisi (A3) gereksiz değil.** K5 "A3 ile S1 arasında fark yok" diyordu. Gerçekte A3 tepe akımı ~1–2 A azaltıyor ve deşarj süresini ~%0.7–1 uzatıyor; buna karşılık SC rezervini düşürüyor (S1'de 0.55 → 0.35, S2'de 0.41 → 0.28). Bunlar küçük etkiler ve kural sayısı 3 katına çıkıyor. 12 kuralda kalma kararı korunuyor, ama raporda "SoC_B gereksiz" yerine "küçük bir menzil–rezerv ödünleşimi sağlıyor" denecek.
4. **SoC'ye uyarlanan tavanın (A4) eğitim çevriminde katkısı yok.** Sabit tavan S2 ile aynı sonucu veriyor (59.7 A ve 60.8 A; SC rezervi de aynı). 7.2'deki ayarın küçük bir d_cap (192 W) seçmesiyle tutarlı.
5. **Bulanık şarj yasası (A5) tepe akımı değil, SC rezervini etkiliyor.** S2'nin tavanına C0'ın crisp şarj kuralı takılınca tepe akım değişmiyor (60.7 A), ama en düşük SoC_SC 0.41'den 0.23'e iniyor. Yani S2'nin farkı ortalama performansta değil, güvenlik payında. Bu, 7.2'deki dayanıklılık bulgusunun mekanizması için bir aday. Kesin hüküm X3 ve X4'te verilecek.

### Ara sonuç
Eğitim çevriminde en iyi tek nokta karşılaştırmasında C0 ile S2 hemen hemen eşit (tepe I_B 57 / 61 A, I²t ve ΔT aynı). Bulanık sürümün iddiası artık açıkça şu: **aynı performansı daha büyük bir SC güvenlik payıyla ve parametre değişimlerine karşı daha dayanıklı biçimde vermek.** Bu iddia X3 (görülmemiş çevrimler) ve X4 (±%10 / ±%20 bozulma) ile sınanacak.

---

## 12. Adım 7.4: X3 genelleme, X4 parametre duyarlılığı, X5 ölçüm gürültüsü

`experiments/proposed/run_robustness.py` (~3.5 dk, 2 süreç, 395 çalıştırma). Tablolar `results/tables/X3_*.csv`, `X4_*.csv`, `X5_*.csv` ve `K4_K5.csv`; grafikler `results/figures/X3_generalization.png`, `X4_sensitivity.png` ve `X5_noise.png`.

### X3 test çevrimleri (`src/hess/test_cycles.py`)
- Eğitim çevrimiyle aynı üreteç ve aynı kalibre istatistikler kullanılıyor: 900 s, 12.4 km, v_max 83 km/h, a_max 2.7 m/s², d_max 2.6 m/s².
- Seed'ler 101–110; eğitim seed'i 7 hiç kullanılmıyor.
- Rejimler, seyirdeki mikro dalgalanmanın genliğiyle ayrılıyor: sakin 0.5 m/s, nominal 1.0 m/s, agresif 1.5 m/s.
- Kalibre edilen istatistikler rejimler arasında aynı. Farklı olan talep gücünün dağılımı:

| Rejim | Pozitif P_dem ort. | P_dem > 3 kW süre payı | Frenleme enerjisi / çevrim |
|---|---|---|---|
| sakin | 1834 W | %11.3 | 15.4 Wh |
| nominal | 2399 W | %19.0 | 26.2 Wh |
| agresif | 2837 W | %23.3 | 36.2 Wh |

- R0 X3'e dahil edilmedi. X1'de F0 ile arasındaki fark 1 std'nin altındaydı; 5 seed × 30 çevrim maliyetine karşılık yeni bilgi vermiyor. Limitations bölümünde belirtilecek.

### X3 sonuçları (30 çevrim, uzun deşarj)

| | Tepe I_B ort. | Medyan | En kötü | Std | Sakin / nominal / agresif | Süre, B1'e göre ort. | En düşük SoC_SC (en kötü çevrim) | Çöken |
|---|---|---|---|---|---|---|---|---|
| F0 | 137.0 | 137.0 | 137.1 | 0.2 | 137 / 137 / 137 | +%3.20 | 0.000 | 30/30 |
| C0 | 93.6 | **57.1** | 137.1 | 39.8 | 57.1 / 87.0 / 137 | +%0.59 | 0.000 | **14/30** |
| S1 | 75.9 | 73.7 | 88.6 | 7.2 | 68.7 / 73.9 / 85.3 | +%0.54 | 0.309 | 0/30 |
| **S2** | **61.1** | 57.2 | **71.5** | 6.2 | 55.5 / 58.4 / 69.4 | +%0.13 | 0.133 | **0/30** |

**Eşleştirilmiş Wilcoxon testleri (tepe I_B, 30 çevrim):**
- **S2 − C0:** S2, 30 çevrimin 26'sında daha iyi. Medyan fark −1.9 A, ortalama fark −32.5 A, p = 1.7·10⁻⁶. %99 I_B'de 28/30 çevrimde daha iyi.
- **S1 − C0:** Medyan fark +9.4 A, yani tipik çevrimde S1 daha kötü. Ortalama fark ise −17.7 A, çünkü C0 bazı çevrimlerde çöküyor (p = 0.047).
- **S2 − S1:** S2, 30 çevrimin 30'unda daha iyi (−14.5 A).
- **C0'ın çöktüğü 14 çevrimin dağılımı:** sakin 0/10, nominal 4/10, agresif 10/10. Ayarlı eşik, eğitim çevriminden (nominal) daha zorlu bir sürüşte SC'yi koruyamıyor.

### X4: Parametre duyarlılığı (eğitim çevrimi, tek parametre bozulması)

| | Nominal tepe I_B | ±%20'de en kötü | ±%20'de en büyük kötüleşme | ±%10'da en büyük kötüleşme | Çöken (16 bozulmadan) | En hassas parametre |
|---|---|---|---|---|---|---|
| C0 | 57.1 A | 136 A | +%138 | +%137 | **7** | p_th −%20 |
| S1 | 73.2 A | 86.5 A | +%18.1 | +%12.0 | 0 | k_p +%20 |
| **S2** | 60.8 A | 68.3 A | **+%12.3** | **+%3.6** | **0** | c_cap +%20 |

- C0'da yalnızca −%10'luk bir değişiklik bile çöküşe yol açıyor: eşik veya şarj gücü %10 düşünce SC boşalıyor.
- Bulanık sürümlerde kötüleşme düzgün ve sınırlı; hiçbir bozulmada çöküş yok.

### X5: Ölçüm gürültüsü (eğitim çevrimi, 5 tohum)

| | σ = 0 | σ = 0.02 | σ = 0.05 | σ = 0.05'te en düşük SoC_SC |
|---|---|---|---|---|
| F0 | 136.2 | 136.2 (+%0) | 136.2 (+%0) | 0.00 |
| C0 | 57.1 | 62.6 (+%9.6) | 71.7 (+%25.5) | **0.06** |
| S1 | 73.2 | 75.0 (+%2.4) | 81.1 (+%10.7) | 0.52 |
| S2 | 60.8 | 62.9 (+%3.5) | 71.6 (+%17.7) | 0.40 |

- σ = 0.05'te C0 ile S2 aynı tepe akıma iniyor (~72 A).
- Göreli kötüleşme C0'da daha büyük. Asıl fark SC rezervinde: C0 0.06'ya iniyor ve çöküşün eşiğine geliyor, S2 ise 0.40'ta kalıyor.
- F0 gürültüden etkilenmiyor, çünkü SC zaten boş.

### Hipotezlerin değerlendirilmesi (`K4_K5.csv`)

| | S1 | S2 |
|---|---|---|
| K4a: X3 ort. tepe I_B ≤ C0 | ✓ (75.9 / 93.6) | ✓ (61.1 / 93.6) |
| K4b: X3 en kötü durum C0'dan iyi ve p < 0.05 | ✗ (en kötüsü iyi, ama tipik çevrimde daha kötü: medyan +9.4 A) | ✓ (71.5 / 137.1 A, p = 1.7·10⁻⁶) |
| K4c: X4 ±%20 kötüleşme C0'dan küçük | ✓ (%18 / %138) | ✓ (%12 / %138) |

| K5 (X3, tepe I_B, Wilcoxon) | Medyan fark | p | Sonuç |
|---|---|---|---|
| S1-A1 (P_ch = 0) | +50.3 A | 1.9·10⁻⁹ | anlamlı kötü ✓ |
| S1-A2 (Tablo 5 + P_ch) | +15.8 A | 1.9·10⁻⁹ | anlamlı kötü ✓ |
| S2-A1 (P_ch = 0) | +79.6 A | 1.9·10⁻⁹ | anlamlı kötü ✓ |
| S2-A4 (sabit tavan) | −0.1 A | 0.17 | fark yok ✗ |
| S2-A5 (crisp şarj kuralı) | +0.6 A (ort. +24.4 A) | 0.002 | anlamlı kötü ✓; **11/30 çevrimde çöküyor** |

### Sonuç
1. **S2, ana katkı olarak bütün ölçütleri sağlıyor (K1–K4).** Görülmemiş 30 çevrimde hiç çökmüyor. Ortalama tepe akımı C0'dan %35, F0'dan %55 düşük; en kötü durumu 71.5 A (C0'da 137 A). Parametre bozulmasında en fazla %12 kötüleşiyor (C0'da %138).
2. **Dayanıklılığın mekanizması bulanık şarj yasası.** A5'te S2'nin tavanı korunup yalnızca şarj kuralı crisp yapılınca yöntem 11/30 çevrimde çöküyor. A4'te tavan sabitlenince hiçbir şey değişmiyor. Yani S2'yi C0'dan ayıran bileşen, SoC_SC arttıkça sürekli azalan bulanık P_ch. Crisp kuraldaki aç-kapa şarj, talep arttığında SC'yi koruyamıyor.
3. **SoC'ye uyarlanan tavan (D-23'teki motivasyon) bu deneylerde katkı vermedi** (A4, p = 0.17). Rapordaki dürüst ifade şu: "S2'nin kazancı bulanık tavandan değil, crisp kırpma yapısının bulanık şarj geri beslemesiyle birleşmesinden geliyor."
4. **S1 en dayanıklı ama en az etkili.** En kötü durumu iyi, ama orantılı pay yapısı nedeniyle tipik çevrimde crisp'in gerisinde (K4b ✗). Bu, Discussion bölümünde çıktı yapısının seçimiyle ilgili bir ders olarak tartışılacak.
5. **Bedel menzil.** S2'nin deşarj süresi B1'e göre +%0.13, F0'a göre ~−%3. K3 (≥ −%1) bütün çevrimlerde sağlanıyor; S2'nin en kötü çevrimi −%0.45.

---

## 13. Adım 8: Canlı demo

- `demo/app.py` (Streamlit), çalıştırma: `streamlit run demo/app.py`. Sekmeler ve önerilen gösterim senaryosu `demo/README.md` dosyasında.
- Demo, deneylerle aynı kodu kullanıyor: `make_ems`, `config/tuned.yaml`, `Simulator`, `test_cycles`. Örneğin agresif rejim, seed 101, uzun deşarj koşulunda demo X3 tablosundaki değerleri birebir üretiyor: C0 136.9 A ve çöküyor, S2 69.5 A.
- `NoisyEMS` (X5 gürültü sarmalayıcısı) `simulator.py`'ye taşındı ve demoda da kullanılıyor. X5 sonuçları değişmedi.
- Testler: `tests/test_demo.py` (Streamlit `AppTest`). Toplam 96 test.
- 7.5 (K-FRL, isteğe bağlı) zaman nedeniyle yapılmadı. Ana bulgular FRL'ye bağlı değil. Limitations ve Future Work bölümlerinde belirtilecek.
