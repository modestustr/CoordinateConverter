İstediğiniz üzerine README.md içeriğindeki tüm Türkçe kelimeleri, imla kurallarına uygun şekilde Türkçe karakterlerle (ç, ğ, ı, ö, ş, ü) güncelledim:

Coordinate Converter

Bu proje, pyproj ve PROJ üzerine kurulu bir koordinat dönüşüm
uygulamasıdır. Streamlit arayüzü ile tekli koordinat dönüşümü, toplu dosya
işleme, dönüşüm doğrulaması ve temel harita önizlemesi sunar.

Sürüm: 1.0.0

## 1. Projenin Amacı

Bu proje, farklı koordinat referans sistemleri (CRS) arasında dönüşüm yaparken
aşağıdaki sorunları aynı yerde toplamak için geliştirildi:

- Tek nokta veya batch veri dönüşümü
- Kaynak sistem seçiminin anlamlı bir önerisi
- Geçersiz veri ve kapsam dışı noktalar için açık hata mesajları
- Dönüşüm sonrasında geri dönüş (round-trip) kontrolü
- Harita üzerinde hızlı görsel kontrol

Uygulama, "sayıları bir formattan diğerine çevirmek" değil, geodezik olarak
anlamlı bir referans sistemi dönüşümü yapmak üzere tasarlanmıştır.

## 2. Bilimsel Arka Plan

### 2.1 Koordinat neden tek başına yeterli değildir?

Bir noktanın koordinatı, yalnızca sayısal bir çift değildir. O sayıların hangi
referans elipsoidine, hangi datum'a, hangi referans çerçevesine ve hangi
projeksiyona göre yazıldığı bilinmeden anlam tam olmaz [1][2].

Örnek:

- 39.93, 32.85 gibi bir ifade çoğunlukla coğrafi koordinattır.
- 500000, 4400000 gibi bir ifade ise büyük olasılıkla düzleme izdüşen,
yani projeksiyonlu bir koordinattir.

Aynı fiziksel nokta, farklı datum veya farklı projeksiyon altında farklı
sayılarla ifade edilebilir. Bu bir hata değil, geodezinin doğal sonucudur [1].

### 2.2 Coğrafi koordinat ile projeksiyon koordinatı farkı

Coğrafi koordinatlar, elipsoid üzerindeki enlem-boylam tanımıdır.
Projeksiyon koordinatları ise bu elipsoidal yüzeyin düzleme aktarılmış halidir.
Bu aktarım sırasında açı, alan, uzaklık veya yön gibi niceliklerin hepsi aynı
anda kusursuz korunamaz; bu nedenle her projeksiyon belirli amaçlara göre
seçilir [2].

Bu uygulamada:

- Coğrafi sistemler derece cinsinden yorumlanır
- Projeksiyon sistemleri metre cinsinden yorumlanır
- Eksen sunumu always_xy=True davranışına uygun olarak yapılır

### 2.3 Datum, referans çerçevesi ve zaman etkisi
WGS84, ITRF ailesi ve ulusal/bölgesel sistemler yalnızca farklı isimler değil,
farklı datum tanımlarıdır. Özellikle modern yerbilim ve hassas konumlama
uygulamalarında referans çerçevesinin zamana bağlı hareketi de önemlidir [3][4].

Bu nedenle:

- "Aynı nokta neden farklı sistemlerde farklı çıkıyor?" sorusunun cevabı
çoğu zaman datum ve referans çerçevesidir.
- Milimetre veya santimetre düzeyindeki işlerde epoch ve hız bilgisi önemli
hale gelir.

Bu uygulama operasyonel dönüşüm aracı olarak çalışır; tam zamana bağlı
tektonik modelleme aracı değildir.

### 2.4 Dönüşüm, ters dönüşüm ve round-trip farkı

Uygulamadaki "Bilimsel İspat ve Geri Dönüş Kontrolü" bölümü şu mantıkla çalışır:

1. Kaynak koordinat hedef sisteme dönüştürülür.
2. Elde edilen sonuç tekrar kaynak sisteme geri dönüştürülür.
3. İlk giriş ile geri dönen koordinat arasındaki fark ölçülür.

Buradaki amaç, dönüşümün sayısal tutarlılığını görmektir. Küçük round-trip
farkı iyi bir işarettir; fakat tek başına "mutlak doğruluk garantisi" değildir.
Çünkü gerçek dünya hatası şu etkenlerden de etkilenir:

- Seçilen kaynak CRS'in doğru olup olmaması
- Kullanılan datum dönüşüm modeli
- Grid tabanlı düzeltmelerin mevcudiyeti
- Floating-point hesaplama sınırları
- Referans çerçevesi ve epoch farkları

Dolayısıyla:

İleri dönüşüm ve geri dönüşüm aynı işlem değildir.
Ama birbirini sınayan iki bağlı işlemdir.
Round-trip farkı küçükse, algoritmik tutarlılık genellikle iyidir [5][6][7].

### 2.5 Dinamik UTM seçimi ne yapar?

'WGS84 / UTM (Dinamik)' hedefi seçildiğinde uygulama, koordinatı önce WGS84
üzerine getirir ve boylama göre uygun UTM zonunu otomatik belirler. Bu pratik
bir kolaylıktır; ancak zone seçimi hala coğrafi konuma bağlı bir karar olduğu
için kullanıcının bölgesel bağlamı bilmesi gerekir [1][2].

## 3. Uygulamanın Bilimsel Olarak Ne Yaptığı

Uygulama şu aşamaları izler:

1. Girdiyi ayrıştırır ve muhtemel sistem tipini tahmin eder.
2. Kaynak CRS kapsam ve mantık kontrolü yapar.
3. 'pyproj' aracılığıyla PROJ dönüşüm pipeline'ını çalıştırır.
4. Sonucu hedef sistem eksen ve birimleriyle sunar.
5. İstenirse geri dönüş farkını hesaplayarak nümerik kontrol verir.
6. Batch modda her satır için durum ve hata kodu üretir.

Bu sayede uygulama yalnızca "dönüştürme" yapmaz; aynı zamanda "bu sonuç neden
güvenilir / neden şüpheli olabilir?" sorusuna da cevap vermeye çalışır.

## 4. Ne Zaman Güvenmeli, Ne Zaman Şüphelenmeli?

Şu durumlarda sonuca daha fazla güvenilir:

- Kaynak koordinat sistemi doğru seçilmişse
- Nokta, seçilen sistemin kapsama alanındaysa
- Round-trip farkı çok küçükse
- Batch sonuçlarında satır bazlı hata yoksa

Şu durumlarda dikkat gerekir:

- Kullanıcı kaynak sistemi tahmin ederek seçmişse
- Veri farklı datumlardan karışık geldiyse
- Tarihi / ulusal / lokal grid dönüşümleri gerekiyorsa
- Yasal kadastro, mühendislik aplikasyonu veya santimetre altı tolerans isteniyorsa

Bu uygulama güçlü bir teknik yardımcıdır; ancak resmi jeodezik denetim,
kurumsal grid dosyaları veya yasal onay mekanizmasının yerine geçmez.

## 5. Teknik Özellikler

- Tekli koordinat dönüşümü
- Toplu CSV/XLSX dönüşümü
- Satır bazlı batch hata raporu
- 'Durum', 'Hata_Kodu', 'Hata_Mesajı' kolonları
- Dinamik UTM zone seçimi
- Round-trip doğrulama tablosu
- Tarayıcı konumu ile başlangıç doldurma
- Harita önizlemesi
- Merkezi logging
- Timeout + retry ile geocode dayanıklılığı

## 6. Proje Yapısı

```text
config/      Ayarlar ve logging
core/        Dönüşüm, CRS, UTM ve çözümleyici mantığı
data/        Sistem veritabanı
services/    Batch, export, geocode, cihaz GPS servisleri
ui/          Streamlit arayüzü
tests/       Pytest senaryoları
```

## 7. Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 8. Çalıştırma

```bash
python main.py --ui
```

Alternatif:

```bash
streamlit run streamlit_app.py
```

## 9. Ortam Ayarları

Desteklenen temel ortam değişkenleri:

- APP_ENV=dev|staging|prod
- APP_VERSION=1.0.0
- APP_TITLE=Coordinate Converter
- MAX_UPLOAD_SIZE_MB=10
- APP_LOG_LEVEL=INFO
- GEOCODE_TIMEOUT_SECONDS=10
- GEOCODE_MAX_RETRIES=3
- GEOCODE_RETRY_BACKOFF_SECONDS=0.5
- GPS_TIMEOUT_MS=10000

Streamlit Community Cloud üzerinde bunlar Settings > Secrets içinden
tanımlanabilir.

## 10. Batch Girdi / Çıktı Sözleşmesi

Beklenen mantık:

- Kullanıcı X ve Y kolonlarını açıkça seçer
- Kaynak ve hedef sistem seçilir
- Her satır için dönüşüm ayrı değerlendirilir

Batch sonucu orijinal kolonlara ek olarak şunları üretir:

- `Hedef_<X>`
- `Hedef_<Y>`
- `Durum`
- `Hata_Kodu`
- `Hata_Mesajı`

Bu tasarım sayesinde bozuk satırlar sessizce yutulmaz; ayrı olarak işaretlenir.

## 11. Test

```bash
pytest -q
```

Test kapsamı şu alanları içerir:

- Tekli dönüşüm davranışı
- Batch hata sözleşmesi
- Dinamik UTM davranışı
- Hata geri bildirimi
- Geocode retry mantığı
- Sidebar sistem durumu
- Ayar normalizasyonu

## 12. Deploy

Seçilen yayın hedefi Streamlit Community Cloud.

1. Repo'yu GitHub'a push et.
2. `share.streamlit.io` üzerinden GitHub hesabını bağla.
3. Create app seç.
4. Repository olarak bu repo'yu seç.
5. Entrypoint file olarak streamlit_app.py gir.
6. Gerekirse Python sürümünü Advanced settings içinden seç.
7. Deploy et.

Notlar:

- Community Cloud repo kökünden çalışır.
- requirements.txt repo kökündedir.
- Entrypoint yolu olarak streamlit_app.py tercih edilmelidir.
- Tema ve temel server ayarları .streamlit/config.toml içinde sabitlenmiştir.

## 13. Sınırlılıklar

- Sonuç kalitesi, seçilen kaynak CRS'in doğruluğuna doğrudan bağlıdır.
- Grid tabanlı yerel dönüşümlerin tümü her ortamda mevcut olmayabilir.
- Küçük round-trip hatası, veri setinin kurumsal/yasal olarak kesin uyumlu
- olduğu anlamına gelmez.
- Tarayıcı GPS ve Nominatim geocode özellikleri yardımcı bileşendir;
  geodezik çekirdekten farklı olarak dış servis bağımlılığı taşır.

## 14. Bilimsel Referanslar

Aşağıdaki kaynaklar, bu uygulamanın anlattığı temel kavramların bilimsel
dayanağını oluşturur:

1. Lu, Z., Qu, Y., Qiao, S. Geodesy: Introduction to Geodetic Datum and
Geodetic Systems. Springer, 2014.
DOI: https://doi.org/10.1007/978-3-642-41245-5

2. Grafarend, E. W., You, R.-J., Syffus, R. Map Projections: Cartographic
Information Systems. Springer, 2014.
DOI: https://doi.org/10.1007/978-3-642-36494-5

3. Altamimi, Z., Rebischung, P., Metivier, L., Collilieux, X.
ITRF2014: A new release of the International Terrestrial Reference Frame
modeling nonlinear station motions. Journal of Geophysical Research:
Solid Earth, 2016.
DOI: https://doi.org/10.1002/2016JB013098

4. Altamimi, Z., Rebischung, P., Collilieux, X., Metivier, L., Chanard, K.
ITRF2020: an augmented reference frame refining the modeling of nonlinear
station motions. Journal of Geodesy, 2023.
DOI: https://doi.org/10.1007/s00190-023-01738-w

5. Watson, G. A. Computing Helmert transformations.
Journal of Computational and Applied Mathematics, 2006.
DOI: https://doi.org/10.1016/j.cam.2005.06.047

6. Featherstone, W. E., Claessens, S. J.
Closed-form transformation between geodetic and ellipsoidal coordinates.
Studia Geophysica et Geodaetica, 2008.
DOI: https://doi.org/10.1007/s11200-008-0002-6

7. Karney, C. F. F. Algorithms for geodesics.
Journal of Geodesy, 2013.
DOI: https://doi.org/10.1007/s00190-012-0578-z

8. Smith, W. H. F. Direct conversion of latitude and height from one
ellipsoid to another. Journal of Geodesy, 2022.
DOI: https://doi.org/10.1007/s00190-022-01608-x

## 15. Yazılım Referansları

Bu uygulamanın hesap çekirdeği şu yazılımlara dayanır:

- PROJ:
DOI: https://doi.org/10.5281/zenodo.14253019

- pyproj 3.7.1:
DOI: https://doi.org/10.5281/zenodo.14876934


## 16. Son Not

Bu README, projeyi hem kullanıcıya hem de teknik denetim yapan bir kişinin
gözüne hitap edecek şekilde hazırlandı. Amaç yalnızca "nasıl çalışır?" sorusuna
değil, "neden böyle çalışır?" sorusuna da açık cevap verebilmektir.