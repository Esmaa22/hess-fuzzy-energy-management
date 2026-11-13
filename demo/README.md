# Canlı demo

Repo kökünden:

```bash
streamlit run demo/app.py
```

Tarayıcıda `http://localhost:8501` açılır.

| Sekme | Ne gösterir | Savunmada hangi soruya cevap |
|---|---|---|
| 1 · Tek karar | Girdi üyelik dereceleri, ateşlenen kurallar ve güçleri, birleştirilmiş çıktı kümesi ve centroid | "Bu kural ne işe yarıyor?", "Bu üyelik fonksiyonu neden böyle?" |
| 2 · Karar yüzeyi | Çıktının P_dem × SoC_SC yüzeyi (F0, S1, S2) | "Bulanık kural crisp kuraldan neden farklı davranıyor?" |
| 3 · Sürüş simülasyonu | Eğitim ya da test çevrimi (rejim + seed), yöntemler yan yana; S2/C0 parametreleri ve ölçüm gürültüsü kaydırıcıyla | "Farklı bir giriş / yeni bir koşulla dener misin?" |
| 4 · Kayıtlı sonuçlar | X1–X5 ve yeniden üretim grafikleri | Sunum sırasında sonuçlara hızlı dönüş |

**Önerilen gösterim senaryosu (~3 dk):**
1. Sekme 1: S2, P_dem = 4200 W. SoC_SC'yi 90'dan 10'a kaydır: tavan (P_cap) yükselir, SC korunur. P_dem = 500 W yap: SoC_SC düştükçe P_ch artar (bulanık şarj yasası).
2. Sekme 3: test çevrimi, rejim agresif, seed 101, uzun deşarj, F0 + C0 + S2 → Çalıştır. C0'da SC boşalır ve tepe akım ~137 A'ya döner; S2'de ~69 A'da kalır.
3. C0 parametrelerinde p_th'yi biraz düşür ya da gürültüyü σ = 0.05 yap: crisp kuralın kırılganlığı.

Testler: `tests/test_demo.py` (Streamlit `AppTest` ile sekmelerin hatasız açıldığını kontrol eder).
