# Coordinate Converter

Coordinate Converter, `pyproj` ve `PROJ` uzerine kurulu bir koordinat donusum
uygulamasidir. Streamlit arayuzu ile tekli koordinat donusumu, toplu dosya
isleme, donusum dogrulamasi ve temel harita onizlemesi sunar.

Surum: `1.0.0`

## 1. Projenin Amaci

Bu proje, farkli koordinat referans sistemleri (CRS) arasinda donusum yaparken
asagidaki sorunlari ayni yerde toplamak icin gelistirildi:

- tek nokta veya batch veri donusumu
- kaynak sistem seciminin anlamli bir onerisi
- gecersiz veri ve kapsam disi noktalar icin acik hata mesajlari
- donusum sonrasinda geri donus (round-trip) kontrolu
- harita uzerinde hizli gorsel kontrol

Uygulama, "sayilari bir formattan digerine cevirmek" degil, geodezik olarak
anlamli bir referans sistemi donusumu yapmak uzere tasarlanmistir.

## 2. Bilimsel Arka Plan

### 2.1 Koordinat neden tek basina yeterli degildir?

Bir noktanin koordinati, yalnizca sayisal bir cift degildir. O sayilarin hangi
referans elipsoidine, hangi datum'a, hangi referans cercevesine ve hangi
projeksiyona gore yazildigi bilinmeden anlam tam olmaz [1][2].

Ornek:

- `39.93, 32.85` gibi bir ifade cogunlukla cografi koordinattir.
- `500000, 4400000` gibi bir ifade ise buyuk olasilikla duzleme izdusen,
  yani projeksiyonlu bir koordinattir.

Ayni fiziksel nokta, farkli datum veya farkli projeksiyon altinda farkli
sayilarla ifade edilebilir. Bu bir hata degil, geodezinin dogal sonucudur [1].

### 2.2 Cografi koordinat ile projeksiyon koordinati farki

Cografi koordinatlar, elipsoid uzerindeki enlem-boylam tanimidir.
Projeksiyon koordinatlari ise bu elipsoidal yuzeyin duzleme aktarilmis halidir.
Bu aktarim sirasinda aci, alan, uzaklik veya yon gibi niceliklerin hepsi ayni
anda kusursuz korunamaz; bu nedenle her projeksiyon belirli amaclara gore
secilir [2].

Bu uygulamada:

- cografi sistemler derece cinsinden yorumlanir
- projeksiyon sistemleri metre cinsinden yorumlanir
- eksen sunumu `always_xy=True` davranisina uygun olarak yapilir

### 2.3 Datum, referans cercevesi ve zaman etkisi

WGS84, ITRF ailesi ve ulusal/bolgesel sistemler yalnizca farkli isimler degil,
farkli referans tanimlaridir. Ozellikle modern yerbilim ve hassas konumlama
uygulamalarinda referans cercevesinin zamana bagli hareketi de onemlidir [3][4].

Bu nedenle:

- "ayni nokta neden farkli sistemlerde farkli cikiyor?" sorusunun cevabi
  cogu zaman datum ve referans cercevesidir
- milimetre veya santimetre duzeyindeki islerde epoch ve hiz bilgisi onemli
  hale gelir

Bu uygulama operasyonel donusum araci olarak calisir; tam zamana bagli
tektonik modelleme araci degildir.

### 2.4 Donusum, ters donusum ve round-trip farki

Uygulamadaki "Bilimsel Ispat ve Geri Donus Kontrolu" bolumu su mantikla calisir:

1. Kaynak koordinat hedef sisteme donusturulur.
2. Elde edilen sonuc tekrar kaynak sisteme geri donusturulur.
3. Ilk giris ile geri donen koordinat arasindaki fark olculur.

Buradaki amac, donusumun sayisal tutarliligini gormektir. Kucuk round-trip
farki iyi bir isarettir; fakat tek basina "mutlak dogruluk garantisi" degildir.
Cunku gercek dunya hatasi su etkenlerden de etkilenir:

- secilen kaynak CRS'in dogru olup olmamasi
- kullanilan datum donusum modeli
- grid tabanli duzeltmelerin mevcutlugu
- floating-point hesaplama sinirlari
- referans cercevesi ve epoch farklari

Dolayisiyla:

- ileri donusum ve geri donusum ayni islem degildir
- ama birbirini sinayan iki bagli islemdir
- round-trip farki kucukse, algoritmik tutarlilik genellikle iyidir [5][6][7]

### 2.5 Dinamik UTM secimi ne yapar?

`WGS84 / UTM (Dinamik)` hedefi secildiginde uygulama, koordinati once WGS84
uzerine getirir ve boylama gore uygun UTM zonunu otomatik belirler. Bu pratik
bir kolayliktir; ancak zone secimi hala cografi konuma bagli bir karar oldugu
icin kullanicinin bolgesel baglami bilmesi gerekir [1][2].

## 3. Uygulamanin Bilimsel Olarak Ne Yaptigi

Uygulama su asamalari izler:

1. Girdiyi ayrisir ve muhtemel sistem tipini tahmin eder.
2. Kaynak CRS kapsam ve mantik kontrolu yapar.
3. `pyproj` araciligiyla PROJ donusum pipeline'ini calistirir.
4. Sonucu hedef sistem eksen ve birimleriyle sunar.
5. Istenirse geri donus farkini hesaplayarak numerik kontrol verir.
6. Batch modda her satir icin durum ve hata kodu uretir.

Bu sayede uygulama yalnizca "donusturme" yapmaz; ayni zamanda "bu sonuc neden
guvenilir / neden supheli olabilir?" sorusuna da cevap vermeye calisir.

## 4. Ne Zaman Guvenmeli, Ne Zaman Suphelenmeli?

Su durumlarda sonuca daha fazla guvenilir:

- kaynak koordinat sistemi dogru secilmisse
- nokta, secilen sistemin kapsama alanindaysa
- round-trip farki cok kucukse
- batch sonuclarinda satir bazli hata yoksa

Su durumlarda dikkat gerekir:

- kullanici kaynak sistemi tahmin ederek secmisse
- veri farkli datumlardan karisik geldiyse
- tarihi / ulusal / lokal grid donusumleri gerekiyorsa
- yasal kadastro, muhendislik aplikasyonu veya santimetre alti tolerans isteniyorsa

Bu uygulama guclu bir teknik yardimcidir; ancak resmi jeodezik denetim,
kurumsal grid dosyalari veya yasal onay mekanizmasinin yerine gecmez.

## 5. Teknik Ozellikler

- Tekli koordinat donusumu
- Toplu CSV/XLSX donusumu
- Satir bazli batch hata raporu
- `Durum`, `Hata_Kodu`, `Hata_Mesaji` kolonlari
- Dinamik UTM zone secimi
- Round-trip dogrulama tablosu
- Tarayici konumu ile baslangic doldurma
- Harita onizlemesi
- Merkezi logging
- Timeout + retry ile geocode dayanikliligi

## 6. Proje Yapisi

```text
config/      Ayarlar ve logging
core/        Donusum, CRS, UTM ve cozumleyici mantigi
data/        Sistem veritabani
services/    Batch, export, geocode, cihaz GPS servisleri
ui/          Streamlit arayuzu
tests/       Pytest senaryolari
```

## 7. Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 8. Calistirma

```bash
python main.py --ui
```

Alternatif:

```bash
streamlit run ui/streamlit_app.py
```

## 9. Ortam Ayarlari

Desteklenen temel ortam degiskenleri:

- `APP_ENV=dev|staging|prod`
- `APP_VERSION=1.0.0`
- `APP_TITLE=Coordinate Converter`
- `MAX_UPLOAD_SIZE_MB=10`
- `APP_LOG_LEVEL=INFO`
- `GEOCODE_TIMEOUT_SECONDS=10`
- `GEOCODE_MAX_RETRIES=3`
- `GEOCODE_RETRY_BACKOFF_SECONDS=0.5`
- `GPS_TIMEOUT_MS=10000`

Streamlit Community Cloud uzerinde bunlar `Settings > Secrets` icinden
tanimlanabilir.

## 10. Batch Girdi / Cikti Sozlesmesi

Beklenen mantik:

- kullanici X ve Y kolonlarini acikca secer
- kaynak ve hedef sistem secilir
- her satir icin donusum ayri degerlendirilir

Batch sonucu orijinal kolanlara ek olarak sunlari uretir:

- `Hedef_<X>`
- `Hedef_<Y>`
- `Durum`
- `Hata_Kodu`
- `Hata_Mesaji`

Bu tasarim sayesinde bozuk satirlar sessizce yutulmaz; ayri olarak isaretlenir.

## 11. Test

```bash
pytest -q
```

Test kapsami su alanlari icerir:

- tekli donusum davranisi
- batch hata sozlesmesi
- dinamik UTM davranisi
- hata geri bildirimi
- geocode retry mantigi
- sidebar sistem durumu
- ayar normalizasyonu

## 12. Deploy

Secilen yayin hedefi `Streamlit Community Cloud`.

1. Repo'yu GitHub'a push et.
2. `share.streamlit.io` uzerinden GitHub hesabini bagla.
3. `Create app` sec.
4. Repository olarak bu repo'yu sec.
5. Entrypoint file olarak `ui/streamlit_app.py` gir.
6. Gerekirse Python surumunu `Advanced settings` icinden sec.
7. Deploy et.

Notlar:

- Community Cloud repo kokunden calisir.
- `requirements.txt` repo kokundedir.
- Entrypoint yolu `ui/streamlit_app.py` olmalidir.
- Tema ve temel server ayarlari `.streamlit/config.toml` icinde sabitlenmistir.

## 13. Sinirliliklar

- Sonuc kalitesi, secilen kaynak CRS'in dogruluguna dogrudan baglidir.
- Grid tabanli yerel donusumlerin tumu her ortamda mevcut olmayabilir.
- Kucuk round-trip hatasi, veri setinin kurumsal/yasal olarak kesin uyumlu
  oldugu anlamina gelmez.
- Tarayici GPS ve Nominatim geocode ozellikleri yardimci bile sendir;
  geodezik cekirdekten farkli olarak dis servis bagimliligi tasir.

## 14. Bilimsel Referanslar

Asagidaki kaynaklar, bu uygulamanin anlattigi temel kavramlarin bilimsel
dayanagini olusturur:

1. Lu, Z., Qu, Y., Qiao, S. *Geodesy: Introduction to Geodetic Datum and
   Geodetic Systems*. Springer, 2014.
   DOI: https://doi.org/10.1007/978-3-642-41245-5

2. Grafarend, E. W., You, R.-J., Syffus, R. *Map Projections: Cartographic
   Information Systems*. Springer, 2014.
   DOI: https://doi.org/10.1007/978-3-642-36494-5

3. Altamimi, Z., Rebischung, P., Metivier, L., Collilieux, X.
   *ITRF2014: A new release of the International Terrestrial Reference Frame
   modeling nonlinear station motions*. Journal of Geophysical Research:
   Solid Earth, 2016.
   DOI: https://doi.org/10.1002/2016JB013098

4. Altamimi, Z., Rebischung, P., Collilieux, X., Metivier, L., Chanard, K.
   *ITRF2020: an augmented reference frame refining the modeling of nonlinear
   station motions*. Journal of Geodesy, 2023.
   DOI: https://doi.org/10.1007/s00190-023-01738-w

5. Watson, G. A. *Computing Helmert transformations*.
   Journal of Computational and Applied Mathematics, 2006.
   DOI: https://doi.org/10.1016/j.cam.2005.06.047

6. Featherstone, W. E., Claessens, S. J.
   *Closed-form transformation between geodetic and ellipsoidal coordinates*.
   Studia Geophysica et Geodaetica, 2008.
   DOI: https://doi.org/10.1007/s11200-008-0002-6

7. Karney, C. F. F. *Algorithms for geodesics*.
   Journal of Geodesy, 2013.
   DOI: https://doi.org/10.1007/s00190-012-0578-z

8. Smith, W. H. F. *Direct conversion of latitude and height from one
   ellipsoid to another*. Journal of Geodesy, 2022.
   DOI: https://doi.org/10.1007/s00190-022-01608-x

## 15. Yazilim Referanslari

Bu uygulamanin hesap cekirdegi su yazilimlara dayanir:

- PROJ:
  DOI: https://doi.org/10.5281/zenodo.14253019
- pyproj 3.7.1:
  DOI: https://doi.org/10.5281/zenodo.14876934

## 16. Son Not

Bu README, projeyi hem kullaniciya hem de teknik denetim yapan bir kisinin
gozune hitap edecek sekilde hazirlandi. Amac yalnizca "nasil calisir?" sorusuna
degil, "neden boyle calisir?" sorusuna da acik cevap verebilmektir.
