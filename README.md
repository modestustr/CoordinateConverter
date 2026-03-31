# Coordinate Converter

Coordinate Converter, `pyproj` tabanli bir koordinat donusum aracidir. Streamlit arayuzu, tekli donusum ve toplu dosya isleme akislari sunar.

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Calistirma

```bash
python main.py --ui
```

Alternatif olarak:

```bash
streamlit run ui/streamlit_app.py
```

## Test

```bash
pytest -q
```

## Ortam Ayarlari

Desteklenen ortam degiskenleri:

- `APP_ENV=dev|staging|prod`
- `APP_VERSION=1.0.0`
- `MAX_UPLOAD_SIZE_MB=10`
- `APP_LOG_LEVEL=INFO`

Streamlit Community Cloud uzerinde bunlari `Settings > Secrets` icinden
tanimlayabilirsin. Yerelde ise PowerShell oturumu icinde ortam degiskeni olarak
verebilirsin.

## Deploy: Streamlit Community Cloud

Secilen yayin hedefi `Streamlit Community Cloud`.

1. Repo'yu GitHub'a push et.
2. `share.streamlit.io` uzerinden GitHub hesabini bagla.
3. `Create app` sec.
4. Repository olarak bu repo'yu sec.
5. Entrypoint file olarak `ui/streamlit_app.py` gir.
6. Gerekirse Python surumunu `Advanced settings` icinden sec.
7. Deploy et.

Notlar:

- Community Cloud repo kokunden calisir; bu projede `requirements.txt` kokte oldugu icin uygun.
- Entrypoint alt klasorde olabilir; burada dogru yol `ui/streamlit_app.py`'dir.
- Windows tipi `\` yerine `/` kullan.
- Tema ve temel server ayarlari `.streamlit/config.toml` dosyasinda sabitlenmistir.

## Notlar

- Batch yuklemelerinde varsayilan dosya limiti `10 MB`'dir.
- Gecersiz satirlar toplu donusum sonucunda `Durum`, `Hata_Kodu` ve `Hata_Mesaji` kolonlari ile isaretlenir.
- Log seviyesi `APP_LOG_LEVEL` ortam degiskeni ile degistirilebilir.
