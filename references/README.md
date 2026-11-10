# Literatür Taraması ve Kaynaklar

Bu klasör projenin literatür taramasını ve IEEE formatındaki kaynak listesini içerir. Teknik rapordaki **Related Work** bölümü bu dokümana dayanarak yazılacaktır.

> **Doğrulama notu:** Literatür taramasında üretken yapay zekâ araçlarından yardım alınmıştır (bkz. raporun "Generative AI Usage Disclosure" bölümü). Listelenen tüm kaynaklar DOI veya yayıncı sayfası üzerinden tarafımca doğrulanmıştır. Kaynakların başlık, yazar, dergi, cilt ve sayfa bilgileri yayıncı veya indeks kayıtları (ScienceDirect, IEEE, MDPI, arXiv, RePEc, DOAJ, kurumsal arşivler) üzerinden karşılaştırılmıştır.
> **Kontrol sütunu:**
> - `+` : Künye ve tablodaki sonuç, kaynağın kendi özetinde veya kayıt sayfasında doğrulandı.
> - `~` : Kaynağın var olduğu doğrulandı, ancak bazı künye bilgileri eksik ya da sonuç yalnızca [1]'in aktarımına dayanıyor (açıklama satırda).
> **Kaynak sütunu:**
> - **[R]**: Bilgi, referans makalenin [R0] kaynakçasından ve onun bu kaynağa ilişkin özetinden alınmıştır.
> - **[W]**: Bilgi, web aramasında kaynağın kendi özetinden ya da kayıt sayfasından görülmüştür.

---

## 1. Literatürün Sınıflandırılması

Batarya/süperkapasitör HESS için önerilen enerji yönetim stratejileri (EMS) dört ana grupta toplanabilir:

| Grup | Temel fikir | Avantaj | Dezavantaj |
|---|---|---|---|
| **Kural tabanlı ve FLC** | Uzman bilgisiyle yazılmış IF–THEN kuralları, bulanık üyelik fonksiyonları | Basit, yorumlanabilir, gerçek zamanlı | Sabit kurallar, uyarlanabilirlik yok |
| **Optimizasyon tabanlı** (DP, MPC, GA, PSO, TLBO) | Bir maliyet fonksiyonunun (enerji, yaşlanma) küresel ya da yerel olarak en aza indirilmesi | Optimale yakın sonuç | Hesaplama yükü yüksek, gelecek sürüş bilgisine ihtiyaç duyabilir |
| **Öğrenme tabanlı** (Q-learning, DQN, PPO, DDPG) | Ajan, ortamla etkileşerek ödülü en çoklayan politikayı öğrenir | Model gerektirmez, uyarlanabilir | Kara kutu, eğitim kararlılığı, genelleme sorunu |
| **Hibrit ve neuro-fuzzy** (ANFIS, AFNN, Fuzzy RL) | Bulanık mantığın yorumlanabilirliği ile öğrenmenin uyarlanabilirliğinin birleştirilmesi | İki dünyanın avantajları | Tasarım karmaşıklığı, çok sayıda hiperparametre |

Referans makale [R0] dördüncü grupta yer alır: Mamdani FLC ve tablo tabanlı Q-learning.

---

## 2. Karşılaştırmalı Literatür Tablosu

| # | Çalışma | Araç / kaynaklar | Yöntem | Temel sonuç | Kaynak | Kontrol |
|---|---|---|---|---|---|---|
| R0 | Kumaresan & Rammohan, 2025 [1] | E2W, batarya + SC | Mamdani FLC (36 kural) + tablo Q-learning (FRL) | Tepe akımda sadece bataryaya göre ~%26, FLC'ye göre ~%4 azalma; menzilde +%7 | PDF | + |
| 1 | Pan vd., 2026 [2] | EV, batarya + SC | PCA ve KNN ile yol durumu tanıma + dueling double deep fuzzy Q-network (D3FQN), uyarlamalı ödül | Farklı yol koşullarında dinamik uyum ve verimli güç dağılımı (fiziksel deney) | [W] | + |
| 2 | Xu vd., 2021 [3] | EV, batarya + ultrakapasitör | Tablo Q-learning (UDDS'de eğitim, WLTP'de doğrulama), PSO ile optimize edilmiş iki kural tabanlı EMS ile karşılaştırma | Batarya yaşlanmasında %13–20 yavaşlama, menzilde %1.5–2 artış (SC'siz araca göre) | [W] | + |
| 3 | Xu vd., 2022 [4] | EV, batarya + ultrakapasitör | Hiyerarşik Q-learning (Q1: güç oranı, Q2: SC devreye alma) | Kapasite kaybında iki baseline yönteme göre %8, ultrakapasitörsüz araca göre %12 azalma | [W] | + |
| 4 | Guo, Li, Outbib, 2022 [5] | Yakıt hücreli HEV | Fuzzy Q-learning: bulanık mantıkla değer fonksiyonu yaklaşıklığı, yakıt hücresi başlatma cezası | Sürekli durum ve eylem uzayı, model gerektirmeden kendi kendine öğrenme; Python tabanlı eğitim ve test | [W] | + |
| 5 | Yang vd., 2024 [6] | Yakıt hücreli araç + batarya | Topluluk öğrenmesi ve karar ağacıyla yol tanıma + fuzzy Q-learning | Çevrimiçi güç dağılımı; yol örüntüsüne göre farklı eylem uzayları; benzetim ve donanım testi | [W] | ~ (ilk yazarın adı ve sayfa aralığı bulunamadı) |
| 6 | Ariche vd., 2025 [7] | BEV (tek kaynak) | Fuzzy Q-learning controller (FQLC), motor güç katsayısı | Hız, eğim ve SoC'ye göre uyarlamalı güç kontrolü; FLC ile karşılaştırma | [W] | ~ (cilt ve makale no bulunamadı) |
| 7 | Xiong, Cao, Yu, 2018 [8] | PHEV, batarya + SC | Q-learning tabanlı gerçek zamanlı güç yönetimi | Kural tabanlı EMS'ye göre toplam enerji kaybında %16.8 azalma | [W] | + |
| 8 | Wu vd., 2023 [9] | EV, batarya + SC | PPO (derin RL) + sürüş stili tanıma | Sürüş stili %95'in üzerinde doğrulukla tanınıyor, kapasite kaybı maliyetinde %3.30–4.19 azalma | [W] | + |
| 9 | Liu vd., 2025 [10] | EV, HESS | Taklit (adversarial imitation) RL | Batarya kapasite kaybı maliyetini en aza indirme; %5–12 azalma ([1]'in aktarımı) | [R] | ~ (künye doğrulandı, sayı yalnızca [1]'den) |
| 10 | Şen, Özcan, Eker, 2024 [11] | EV, HESS | FLC, rejeneratif fren odaklı (ADVISOR) | NEDC'de (ADVISOR) batarya akımında %29.1 azalma, bataryada %46.84 daha az ısı üretimi | [W] | + |
| 11 | Rostami & Al-Shibaany, 2024 [12] | EV, tam aktif HESS | TLBO ile optimize edilmiş FLC parametreleri | Kural tabanı ve üyelik fonksiyonları TLBO ile ayarlanıyor; PSO-fuzzy ve optimizasyonsuz fuzzy ile karşılaştırma | [W] | + |
| 12 | Kumaresan & Rammohan, 2025 [13] | E2W, batarya + SC | ANFIS tabanlı EMS | Batarya akımında ~%25 azalma, tüketimde düşüş ([1]'in aktarımı) | [R] | + |
| 13 | Chen, Li, Chen, 2023 [14] | EV, batarya + SC | Meta-kural EMS (DP ile kural örüntüsü, kümeleme, seagull optimizasyonu) | Seagull optimizasyonuyla meta-kural; enerji tüketiminde %3.4 azalma ([1]'in aktarımı) | [R] | + |
| 14 | Al Takrouri vd., 2025 [15] | EV, HESS | Rafine edilmiş güç takipçisi (rule-based) | Üstel yumuşatmalı güç takipçisi; klasik güç takipçisine göre RMS batarya akımında %18.73 azalma | [W] | + |
| 15 | Wangsupphaphol vd., 2023 [16] | – (derleme) | Batarya/SC EMS'leri üzerine sistematik derleme | HESS mimarileri, dönüştürücü topolojileri ve EMS sınıflandırması | [W] | + |

---

## 3. Sentez: Literatürden Çıkan Sonuçlar

1. **Bulanık mantık ile RL birleşimi güncel bir eğilim.** 2022–2026 arasında bu iki yaklaşımı birleştiren çalışmalar artmış [2], [5], [6], [7]. Bulanık mantık bu çalışmalarda iki farklı rol üstleniyor:
   - (a) **Değer fonksiyonu yaklaşıklayıcısı:** Glorennec ve Jouffe çizgisindeki "klasik" fuzzy Q-learning [5], [21].
   - (b) **Taban kontrolcü:** RL, FLC'nin kararını düzeltiyor veya ayarlıyor. Referans makale [1] bu ikinci yapıdadır.
2. **Derin RL'e geçiş.** En yeni çalışmalar tablo Q-learning yerine DQN türevlerini (D3FQN [2]) ve politika gradyanı yöntemlerini (PPO [9]) kullanıyor, buna yol durumu tanımayı da ekliyor. Tablo Q-learning [1], [3] daha basit ve açıklanabilir, ancak durum uzayının kaba ayrıklaştırılması ciddi bir sınırlama.
3. **Ölçülen metrikler.**
   - Çoğu çalışma tepe veya RMS batarya akımı, enerji tüketimi ve menzil üzerinden değerlendiriyor.
   - Yaşlanmayı doğrudan modelleyenler azınlıkta [3], [4], [10].
   - Referans makale yaşlanmayı yalnızca I_RMS, I²t ve severity index gibi vekil göstergelerle ele alıyor.
4. **İki tekerlekli araç (E2W) boşluğu.** E2W odaklı HESS çalışmaları sınırlı ve büyük kısmı aynı araştırma grubundan geliyor [1], [13]. Bu, referans makalenin iddia ettiği özgünlüğü destekliyor, ancak bağımsız doğrulama eksikliğine de işaret ediyor.
5. **Kazanç büyüklükleri.** FLC → öğrenme tabanlı geçişte raporlanan iyileşmeler genellikle tek haneli yüzdeler (%1–8). Bu da istatistiksel karşılaştırmanın (çoklu çevrim, çoklu seed, güven aralığı) önemini artırıyor. Referans makalede bu eksik.

### Projemizin konumu
Proje [1]'i Python'da açık kaynak olarak yeniden üretir. Literatürde sık görülen ama [1]'de eksik olan iki unsuru ekler:
- **Tutarlı bir ödül tasarımı**
- **Çoklu sürüş çevrimi ve çoklu seed ile dayanıklılık ve istatistik analizi**

(Kesin katkı Adım 6'da belirlenecektir.)

---

## 4. Teorik Altyapı Kaynakları

| Konu | Kaynak |
|---|---|
| Bulanık kümeler | Zadeh, 1965 [17] |
| Mamdani çıkarımı | Mamdani & Assilian, 1975 [18] |
| Q-learning | Watkins & Dayan, 1992 [19] |
| Pekiştirmeli öğrenme (genel) | Sutton & Barto, 2018 [20] |
| Fuzzy Q-learning | Glorennec & Jouffe, 1997 [21]; Jouffe, 1998 [22] |
| Type-2 bulanık mantık (olası katkı için) | Mendel & John, 2002 [23] |

---

## 5. Kaynakça (IEEE)

[1] N. Kumaresan and A. Rammohan, "Fuzzy reinforcement learning-based energy management strategy for the integration of hybrid energy storage system of electric vehicle," *Results Eng.*, vol. 28, Art. no. 107875, 2025, doi: 10.1016/j.rineng.2025.107875.

[2] R. Pan, J. Li, D. Yang, and Y. Yan, "A fuzzy RL-based energy management strategy for battery/supercapacitor hybrid energy storage system with road condition recognition," *IEEE Trans. Transp. Electrific.*, vol. 12, no. 2, pp. 2887–2898, Apr. 2026.

[3] B. Xu, J. Shi, S. Li, H. Li, and Z. Wang, "Energy consumption and battery aging minimization using a Q-learning strategy for a battery/ultracapacitor electric vehicle," *Energy*, vol. 229, Art. no. 120705, 2021, doi: 10.1016/j.energy.2021.120705.

[4] B. Xu, Q. Zhou, J. Shi, and S. Li, "Hierarchical Q-learning network for online simultaneous optimization of energy efficiency and battery life of the battery/ultracapacitor electric vehicle," *J. Energy Storage*, vol. 46, Art. no. 103925, 2022, doi: 10.1016/j.est.2021.103925.

[5] L. Guo, Z. Li, and R. Outbib, "A lifetime extended energy management strategy for fuel cell hybrid electric vehicles via self-learning fuzzy reinforcement learning," in *Proc. 10th Int. Conf. Syst. Control (ICSC)*, Marseille, France, 2022, pp. 161–167, doi: 10.1109/ICSC57768.2022.9993916.

[6] Yang *et al.*, "An online energy management strategy for fuel cell vehicles based on fuzzy Q-learning and road condition recognition," *IEEE Trans. Intell. Transp. Syst.*, vol. 25, p. 12120, 2024, doi: 10.1109/TITS.2024.3368149. *(Not: İlk yazarın adı ve sayfa aralığı teyit edilemedi. Rapora girmeden önce DOI açılıp tamamlanmalı; tamamlanamazsa kaynak çıkarılmalı.)*

[7] S. Ariche, Z. Boulghasoul, A. El Ouardi, A. Elbacha, A. Tajer, and S. Espié, "Enhancing energy management in battery electric vehicles: A novel approach based on fuzzy Q-learning controller," *Eng. Sci. Technol., Int. J.*, Jul. 2025. *(Not: Cilt, makale no ve DOI teyit edilemedi. ScienceDirect PII: S2215098625001259. Rapora girmeden önce tamamlanmalı.)*

[8] R. Xiong, J. Cao, and Q. Yu, "Reinforcement learning-based real-time power management for hybrid energy storage system in the plug-in hybrid electric vehicle," *Appl. Energy*, vol. 211, pp. 538–548, 2018, doi: 10.1016/j.apenergy.2017.11.072.

[9] Y. Wu *et al.*, "Driving style-aware energy management for battery/supercapacitor electric vehicles using deep reinforcement learning," *J. Energy Storage*, vol. 73, Art. no. 109199, 2023, doi: 10.1016/j.est.2023.109199.

[10] W. Liu, P. Yao, Y. Wu, L. Duan, H. Li, and J. Peng, "Imitation reinforcement learning energy management for electric vehicles with hybrid energy storage system," *Appl. Energy*, vol. 378, Art. no. 124832, 2025, doi: 10.1016/j.apenergy.2024.124832.

[11] M. Şen, M. Özcan, and Y. R. Eker, "Fuzzy logic-based energy management system for regenerative braking of electric vehicles with hybrid energy storage system," *Appl. Sci.*, vol. 14, no. 7, Art. no. 3077, 2024, doi: 10.3390/app14073077.

[12] S. M. Rakhtala Rostami and Z. Al-Shibaany, "Intelligent energy management for full-active hybrid energy storage systems in electric vehicles using teaching–learning-based optimization in fuzzy logic algorithms," *IEEE Access*, vol. 12, pp. 67665–67680, 2024, doi: 10.1109/ACCESS.2024.3399111.

[13] N. Kumaresan and A. Rammohan, "Adaptive neuro fuzzy inference system based optimized energy management strategy for the power integration of battery and supercapacitor in electric vehicle," *J. Energy Storage*, vol. 126, Art. no. 117073, 2025, doi: 10.1016/j.est.2025.117073.

[14] X. Chen, M. Li, and Z. Chen, "Meta rule-based energy management strategy for battery/supercapacitor hybrid electric vehicles," *Energy*, vol. 285, Art. no. 129365, 2023, doi: 10.1016/j.energy.2023.129365.

[15] M. Al Takrouri, N. R. N. Idris, M. J. A. Aziz, R. Ayop, and W. Y. Low, "Refined power follower strategy for enhancing the performance of hybrid energy storage systems in electric vehicles," *Results Eng.*, vol. 25, Art. no. 103960, 2025, doi: 10.1016/j.rineng.2025.103960.

[16] A. Wangsupphaphol, S. Phichaisawat, N. R. N. Idris, A. Jusoh, N. D. Muhamad, and R. Lengkayan, "A systematic review of energy management systems for battery/supercapacitor electric vehicle applications," *Sustainability*, vol. 15, no. 14, Art. no. 11200, 2023, doi: 10.3390/su151411200.

[17] L. A. Zadeh, "Fuzzy sets," *Inf. Control*, vol. 8, no. 3, pp. 338–353, 1965, doi: 10.1016/S0019-9958(65)90241-X.

[18] E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy logic controller," *Int. J. Man-Mach. Stud.*, vol. 7, no. 1, pp. 1–13, 1975, doi: 10.1016/S0020-7373(75)80002-2.

[19] C. J. C. H. Watkins and P. Dayan, "Q-learning," *Mach. Learn.*, vol. 8, pp. 279–292, 1992, doi: 10.1007/BF00992698.

[20] R. S. Sutton and A. G. Barto, *Reinforcement Learning: An Introduction*, 2nd ed. Cambridge, MA, USA: MIT Press, 2018.

[21] P. Y. Glorennec and L. Jouffe, "Fuzzy Q-learning," in *Proc. 6th IEEE Int. Conf. Fuzzy Syst.*, 1997, pp. 659–662, doi: 10.1109/FUZZY.1997.622790.

[22] L. Jouffe, "Fuzzy inference system learning by reinforcement methods," *IEEE Trans. Syst., Man, Cybern. C*, vol. 28, no. 3, pp. 338–355, 1998, doi: 10.1109/5326.704563.

[23] J. M. Mendel and R. I. B. John, "Type-2 fuzzy sets made simple," *IEEE Trans. Fuzzy Syst.*, vol. 10, no. 2, pp. 117–127, 2002, doi: 10.1109/91.995115.
