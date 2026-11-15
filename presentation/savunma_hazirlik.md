# Savunma Hazırlığı: Olası Sorular ve Kısa Cevaplar

Bu doküman, yönergenin 14. maddesinde (Canlı Uygulama ve Sözlü Savunma) sayılan konulara göre hazırlanmıştır. Cevaplar kısa tutulmuştur; ayrıntılar rapordadır (`report/report.pdf`, bölüm numaraları köşeli parantezde). Sayıların hepsi `results/tables/` dosyalarından gelir.

**Akılda tutulacak 6 sayı:**

| Ne | Değer |
|---|---|
| SC'nin boşaldığı an (makale kuralları, uzun deşarj) | ~1070 s |
| S2'nin F0'a göre tepe akım azalması | −%55 (136.2 → 60.8 A) |
| Görülmemiş 30 çevrimde çökme sayısı | S2 0/30, C0 14/30 |
| S2 ile C0 arasındaki farkın anlamlılığı | p = 1.7·10⁻⁶ (26/30) |
| ±%20 parametre bozulmasında en büyük kötüleşme | S2 %12, C0 %138 |
| Bedel: F0'a göre deşarj süresi | −%3 |

---

## 1. Kuralların işlevi

**S: Referans FLC'nin kuralları ne yapıyor?** [§4.2]
SC doldukça yükün daha büyük kısmını SC'ye veriyor (%0–25'ten %60'a kadar). Talep seviyesi yalnızca SC Low/Medium iken yüksek talepte fark yaratıyor. Rejenerasyonda batarya şarj edilmiyor, SC Low/Medium ise fren enerjisini alıyor, High ise almıyor.

**S: Önerdiğin 12 kuralı iki cümleyle açıklar mısın?** [§6.2]
"Talep yüksekse ve SC doluysa yükü SC'ye ver" (alt satırlar) ve "talep düşükse ve SC boşalmışsa bataryadan SC'yi doldur" (Low sütunu). Talep Low iken SC'nin payı hep sıfır; SC yalnızca yüksek talepte çalışıyor. Şarj gücü SoC_SC arttıkça High → Medium → Zero olarak azalıyor.

**S: Demoda gösterdiğin kural (P_dem 4200 W) neden SC boşalınca tavanı yükseltiyor?**
S2'de P_cap yalnızca SoC_SC'ye bağlı: Low → Loose (yüksek tavan), High → Tight (düşük tavan). SC boşken tavanı yükseltmek, SC'den daha az güç istemek demek; bu SC'yi korur. Değerler: SoC_SC 0.9 → 2502 W, 0.1 → 2857 W.

**S: Hangi kural en kritik?**
P_dem Low ve SoC_SC Low → P_ch High kuralı. SC'yi geri dolduran ana kural bu. Ablasyonda şarj kaldırılınca (A1) iki varyant da makalenin FLC'si seviyesine dönüyor (S2'de 137.0 A).

**S: Neden SoC_B girdisini çıkardın? Batarya boşken de SC'yi şarj etmek mantıklı mı?** [§6.2, X2]
Makalenin Tablo 5'inde SoC_B neredeyse hiç fark yaratmıyor (Low ve High satırları tek hücre dışında aynı). Geri ekleyince (A3, 36 kural) tepe akım 1–2 A düşüyor, süre %0.7–1 uzuyor, ama SC rezervi azalıyor. Bu küçük kazanç için kural sayısını üçe katlamaya değmedi. Batarya %20'ye inince deşarj zaten bitiyor; bu aralıkta SoC_B'ye göre davranmayı gerektiren bir durum oluşmadı.

## 2. Üyelik fonksiyonu seçimleri

**S: Neden yamuk üyelik fonksiyonu?** [§3.1, §5.2]
Makale yamuk tip kullanıyor; yeniden üretimde tipi korudum. Yamuk, uçlarda (SoC %0–20 gibi) tam üyelik bölgesi bırakıyor, yani "kesinlikle Low" bölgesi oluşuyor.

**S: Köşe noktalarını nasıl seçtin?**
Makalede yalnızca aralıklar var. Komşu terimler %50 örtüşecek şekilde seçtim: SoC için Low (0, 0, 20, 40), Medium (20, 40, 60, 80), High (60, 80, 100, 100). Bu Ruspini bölümlemesi: her noktada üyelik toplamı 1. Örnek: SoC_SC = 0.30 → Low 0.5, Medium 0.5.

**S: Çıktı üyelik fonksiyonları nasıl?**
Her çıktı seviyesi o değer merkezli dar bir üçgen (C_SC için ±5, P_ch için ±100 W). Çıktı evreni seviyelerin biraz dışına taşırıldı ([−5, 105]); yoksa 0 ve 100'deki üçgenlerin yarısı dışarıda kaldığı için ağırlık merkezi 1.7 / 98.3 gibi kayık değerler veriyordu (D-17).

**S: Örtüşme oranını değiştirsen ne olur?**
X4'te SoC MF'lerinin ölçeği (k_soc) ±%20 bozuldu; S2'de tepe akım en fazla birkaç amper değişti, hiç çöküş olmadı. Örtüşme kalktıkça (crisp'e yaklaştıkça) davranış C0'a, yani kırılgan eşik kuralına yaklaşır.

**S: Neden Mamdani, neden Sugeno değil?** [§3.2]
Mamdani'de sonuçlar da dilsel terim; kurallar doğrudan okunabiliyor ve makalenin tablosu da dilsel. Sugeno hesaplama açısından daha ucuz ve ANFIS gibi veriyle ayarlanan yöntemlere uygun. Bizde karar süresi zaten 1 s adımın çok altında (S2: 84 µs), hız bir sorun değil.

## 3. Parametrelerin etkileri

**S: Hangi parametre sonucu en çok etkiliyor?** [X4]
C0'da eşik p_th: %10 düşünce SC boşalıyor ve tepe akım 136 A'ya fırlıyor. S2'de en hassas olan tavanın merkezi c_cap (+%20'de 68.3 A); kötüleşme en fazla %12.

**S: Ayarı nasıl yaptın, aşırı uydurma (overfitting) olmadı mı?** [§7]
Her yöntem dört parametreyle, aynı bütçeyle (24 değerlendirme, Latin hiperküp) ve yalnızca eğitim çevriminde ayarlandı. Test için ayarda hiç kullanılmayan 30 çevrim var (X3). Crisp kural tam olarak bu yüzden test çevrimlerinde çöküyor; bulanık sürüm çökmüyor.

**S: Ayarlı S2 parametreleri neler?**
c_cap 2666 W, d_cap 192 W (tavan 2474–2858 W), k_ch 1.53 (şarj seviyeleri ~459 / 1071 / 1836 W), k_soc 1.16.

**S: FRL'nin hiperparametreleri?**
Makaledeki gibi α = 0.1, γ = 0.9, ε 1.0'dan ×0.995 ile 0.01'e. Makalede verilmeyen bölüm sayısı 1000 (ε'un alt sınıra inmesi için ~920 bölüm gerekiyor), 5 tohum.

**S: Termal model parametresi hA nereden geldi?**
Sadece-batarya senaryosunda makaledeki 2.1 °C artışı verecek şekilde bir kez kalibre edildi (0.0846 W/K) ve sonra sabitlendi. Sıcaklık sonuçlarını yalnızca göreli yorumluyorum.

## 4. Kullanılan algoritmalar

**S: Mamdani çıkarımının adımlarını anlat.** [§3.2]
(1) Ateşleme: öncül üyeliklerinin minimumu. (2) Çıkarım: sonuç kümesi bu seviyeden kırpılır (min). (3) Birleştirme: kırpılmış kümelerin maksimumu. (4) Durulaştırma: ayrık evrende ağırlık merkezi, y* = Σ yᵢ μ(yᵢ) / Σ μ(yᵢ).

**S: FRL tam olarak nasıl çalışıyor?** [§4.3, §5.3]
Durum, her girdinin en yüksek üyelikli dilsel terimi (36 durum). Eylem, FLC'nin C_SC çıktısına eklenen Δ ∈ {−20, −10, 0, +10, +20}. Ödül makalenin Denk. 5'i; koşullar örtüştüğü için ilk eşleşen geçerli. Tablo Q-learning ile güncelleniyor. Q tablosu sıfırken FRL birebir FLC gibi davranıyor (testle doğrulandı).

**S: Neden Wilcoxon testi?** [§7]
Yöntemler aynı 30 çevrimde koşturuldu, yani veriler eşleştirilmiş. Çöküşler yüzünden dağılım normal değil (iki tepeli: ~57 A ve ~137 A), bu yüzden parametrik olmayan işaretli sıra testi seçildi.

**S: Latin hiperküp nedir, neden?**
Arama uzayını her boyutta eşit aralıklara bölüp her aralıktan bir örnek alan bir örnekleme. Küçük bütçeyle (24 nokta) uzayı düzgün taramak için. Bütün yöntemlerde aynı tohum kullanıldı, böylece aynı birim tasarım noktaları karşılaştırılabildi.

## 5. Yapılan değişikliklerin gerekçeleri

**S: Neden bu katkıyı seçtin?** [§6.1]
Yeniden üretim, sorunun öğrenme katmanında değil kural tabanında olduğunu gösterdi: SC ~1070 s'de boşalıyor ve bataryadan SC şarjı kuralı yok. Q-learning bunu çözemiyor, çünkü SC'yi koruyabilmek için onu kullanmayı bırakıyor.

**S: Bulanık mantık burada gerçekten gerekli mi? Crisp kural en iyi durumda daha iyi değil mi?** [§9]
Evet, eğitim çevriminde crisp kural biraz daha iyi (57.1 / 60.8 A). Bulanık mantığın değeri en iyi durumda değil, dayanıklılıkta: crisp kural görülmemiş çevrimlerin 14/30'unda, %10'luk bir parametre hatasında bile çöküyor; S2 hiç çökmüyor. Ablasyon (A5) bunun nedenini gösteriyor: S2'ye crisp şarj kuralı takılınca 11/30 çevrimde çöküyor.

**S: Neden S2'yi sonradan ekledin?** [§6, D-23]
Eşit bütçeli ayarda S1'in (pay çıktısı) en iyi durumda crisp'in gerisinde kaldığı görüldü, çünkü yüzde payında yüksek talepte bataryanın payı da büyüyor. S2, crisp'in düz kırpma yapısını korurken şarjı bulanık geri beslemeye bağlıyor. Ekleme, deney sonuçlarından önce, ayar aşamasında yapıldı ve raporda açıkça yazıldı.

**S: Uyarlamalı tavan işe yaramadıysa neden S2'de tutuyorsun?**
Olumsuz bulgu olarak dürüstçe raporladım (A4, p = 0.17). Sabit tavanlı S2 de aynı sonucu veriyor; yöntemin kazancı tavandan değil, kırpma yapısının bulanık şarjla birleşmesinden geliyor. Bu, deney tasarımının (ablasyonların) amacına uygun bir sonuç.

## 6. Sonuçların nedenleri

**S: FLC neden uzun deşarjda tepe akımı azaltamıyor?** [§8.1]
SC'nin kullanılabilir enerjisi ~98 Wh, bataryanın %2.6'sı. Kurallar SC boşken bile pay veriyor ve şarj yok; tek kaynak %20 rejenerasyon. SC ilk ~1070 s'de boşalıyor; tepe akım ise deşarjın sonunda, batarya gerilimi düşükken oluşuyor.

**S: Makale neden farklı sonuç bulmuş olabilir?**
Bir hipotez: SoC denklemlerinde zaman adımı ve birimler verilmemiş; SC enerjisinin yanlış ölçeklenmesi boşalmayı gizlemiş olabilir. Ayrıca makale tepe akımın hangi pencerede ölçüldüğünü vermiyor; ilk çevrimde ölçülmüşse sonuçlarımız uyumlu (bizde −%26.3, makalede −%22.7). Bunlar doğrulanamıyor, raporda hipotez olarak yazıldı.

**S: FRL neden FLC'den iyi çıkmadı?** [§9]
Ödül monoton değil ve SoC_SC içermiyor. Ajan SoC_SC Low iken SC payını kısmayı öğreniyor; SC korunuyor ama tepe akımda kullanılmıyor. Farklar 5 tohumun standart sapmasının altında; makale tek çalıştırma raporluyor.

**S: Önerilen yöntem neden daha kısa deşarj süresi veriyor?**
Bataryadan SC'ye aktarılan enerji iki kez dönüştürücüden (şarj ve deşarj) ve SC'nin iç direncinden geçiyor. F0'ın süre avantajı, SC'yi ilk ~20 dakikada boşaltıp sonra hiç kullanmamasından geliyor. Adil baseline B1'e göre S2 ortalamada +%0.13, en kötü çevrimde −%0.45.

**S: Menzil kazancının 2/3'ü rejenerasyondan ne demek?** [§8.1, E6]
Makalenin sadece-batarya baseline'ında rejeneratif fren kapalı. Rejenerasyonu açık bir sadece-batarya senaryosu (B1) eklediğimde süre %7.1 uzadı; FLC'nin bu adil baseline'a göre kazancı yalnızca %3.3.

## 7. Kodun belirli bölümlerinin görevleri

| Soru | Dosya / fonksiyon |
|---|---|
| Üyelik fonksiyonları | `src/hess/fuzzy.py`: `trapmf`, `trimf`, `FuzzyVariable.fuzzify` |
| Ateşleme, birleştirme, durulaştırma | `MamdaniFIS.firing_strengths`, `aggregate`, `defuzzify`; hangi kuralın ne kadar ateşlendiği: `explain` (demoda Sekme 1) |
| Makalenin 36 kuralı | `src/hess/flc_ems.py`: `build_fis`, `FLCEMS.decide` |
| Önerilen 12 kural | `src/hess/scs_flc.py`: `RULES`, `CAP_BY_SOC`; S2 = `SCSFLCCapEMS.decide` / `sc_request` |
| Crisp rakip | `src/hess/crisp_ems.py`: `CrispEMS.sc_request` (4 satırlık kural) |
| Q-learning | `src/hess/qlearning.py`: `QLearningAgent.update`, `act`, `decay_epsilon`; ödül: `frl_ems.reward_paper` |
| Güç paylaşımı ve güvenlik katmanı | `src/hess/simulator.py`: `Simulator._arbitrate` (SC sınırları, eksik güç bataryadan, fazla fren mekanik frene), `run` |
| Batarya / SC modelleri | `src/hess/battery.py` (`Battery.current`, `step`), `src/hess/supercap.py` |
| Ayar ve test çevrimleri | `src/hess/tuning.py` (`make_ems`, `load_tuned`), `src/hess/test_cycles.py` |

**S: Bir EMS simülatörle nasıl konuşuyor?**
Her EMS tek bir metot uyguluyor: `sc_request(p_dem, soc_b, soc_sc)` → SC'den istenen bara gücü. Negatif değer, bataryadan SC'ye şarj demek (yalnızca `sc_recharge = True` olan EMS'lerde). Simülatör bu isteği fiziksel sınırlara göre kırpıp kalan gücü bataryaya veriyor; böylece bütün yöntemler aynı güvenlik katmanından geçiyor.

## 8. Çalışmanın sınırlılıkları [§10]

- Yalnızca benzetim; dönüştürücü ve motor verimi sabit.
- Makalede verilmeyen parametreler (kütle, MF köşeleri, eylem kümesi, termal model) tarafımızdan seçildi.
- Sürüş çevrimleri sentetik ve aynı üreteç ailesinden; gerçek kayıt ya da standart çevrim (WMTC) denenmedi.
- Yaşlanma doğrudan modellenmedi; tepe akım, RMS, I²t ve ΔT vekil göstergeler.
- K-FRL (SCS-FLC + düzeltilmiş ödüllü Q-learning) zaman nedeniyle yapılmadı; FRL X3'te koşturulmadı.

**S: Bir sonraki adımda ne yapardın?**
SCS-FLC'nin üzerine monoton ve SoC_SC terimi içeren bir ödülle Q-learning; ölçüm belirsizliği için tip-2 bulanık kümeler; gerçek sürüş kayıtlarıyla test; donanım-döngüde doğrulama.

## 9. Üretken yapay zekâ kullanımı

**S: Yapay zekâyı nasıl kullandın?**
Claude'u kod, testler, deney betikleri, literatür taraması ve rapor taslağı için kullandım; raporun GenAI bölümünde açıkça yazıyor. Proje adım adım yürütüldü; her alt adımın sonucunu inceleyip onayladım, tasarım kararlarını (varsayımlar, katkının seçimi, S2'nin eklenmesi) ben verdim.

**S: Doğruluğundan nasıl emin oldun?**
96 birim testi; bütün tablo ve grafiklerin betiklerle yeniden üretilmesi; rapordaki sayıların CSV'lerle betikle karşılaştırılması; kaynakların DOI üzerinden tek tek kontrolü (doğrulanamayan bir sayfa numarası kaynakçadan çıkarıldı).

> **Not:** Bu bölümdeki cevapları kendi çalışma şeklinle karşılaştır ve gerekirse kendi cümlelerinle değiştir. Bu bölümde en önemlisi, söylediklerinin raporun GenAI bölümüyle tutarlı olması.

---

## Demo sırasında sorulabilecekler

- **"Başka bir değer gir."** Sekme 1'de istenen P_dem ve SoC_SC'yi gir; ateşlenen kuralları ve ağırlık merkezini göster. Beklenen eğilim: SoC_SC düştükçe P_cap ↑, P_ch ↑ (düşük talepte).
- **"Yeni bir koşul dene."** Sekme 3'te farklı rejim/tohum ya da gürültü seç. Agresif rejimde C0 10/10 çöker; S2'nin tepe akımı 66–72 A bandında kalır (sakin rejimde 55–57 A).
- **Demo açılmazsa:** yedek slayt (demo değerleri) ve `results/figures/` grafikleri.
- **Sunumdan önce:** demoyu `(base)` ortamında değil, kullanacağın ortamda bir kez çalıştır (`streamlit run demo/app.py`).
