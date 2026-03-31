# Production Readiness Checklist

Bu dosya, projeyi PoC seviyesinden kontrollu bir production yayinina tasimak icin yasayan kontrol listesidir.

## P0 - Yayin Oncesi Zorunlu

- [x] `core` paketini acik paket haline getir
- [x] `pytest` repo kokunden tek komutla calissin
- [x] Tekli donusumde makinece ayristirilabilir hata kodlarini koru
- [x] Batch donusumde satir bazli dogrulama uygula
- [x] Gecersiz batch satirlarinda `inf` veya sessiz bozuk cikti uretimini engelle
- [x] Baslangic bagimlilik manifesti ekle (`requirements.txt`)
- [x] CI ekle: her push/PR'da `pytest -q`
- [x] Batch icin dosya boyutu ve kolon semasi guardrail'leri ekle
- [x] Log yapilandirmasini merkezilestir ve hata seviyelerini standardize et

## P1 - Operasyonel Dayaniklilik

- [x] Streamlit baslangic/calisma talimatlarini belgeleyen bir `README.md` ekle
- [x] Tekli ve toplu akis icin kullanici dostu hata metinlerini standardize et
- [x] Harici servisler icin timeout + retry + gorunur hata kaydi ekle
- [x] Batch sonuclarinda ozet metrikler ekle: basarili satir, hatali satir, hata tipleri
- [x] Girdi/cikti sozlesmeleri icin daha genis test kapsami ekle

## P2 - Production Konforu

- [x] Dagitim hedefi sec: Streamlit Community Cloud
- [x] Ortam bazli yapilandirma ekle (`dev`, `staging`, `prod`)
- [x] Basit saglik kontrolu ve surum bilgisi ekrani ekle
- [ ] Ornek veri dosyalari ve kabul test senaryolari ekle

## Cikis Kriteri

Bu proje production'a "yakin" sayilabilir durumdadir eger:

- `pytest -q` temiz geciyorsa
- Batch akisinda bozuk satirlar acikca isaretleniyorsa
- Tek komutla kurulum yapilabiliyorsa
- Deploy hedefi ve calisma talimati belgelenmisse
- En az bir CI hatti degisikliklerde otomatik dogrulama calistiriyorsa
