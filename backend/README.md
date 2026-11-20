# Gören Göz backend

FastAPI sunucusu: isteğe bağlı kare analizi ve Türkçe VLM sorusu. Genel bakış: kök `README.md`.

## Çalıştırma

```powershell
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-dev.txt
copy .env.example .env      # API_KEY doldur
Get-NetTCPConnection -LocalPort 8110 -State Listen   # boş olmalı
uvicorn main:app --host 127.0.0.1 --port 8110
```

- Ayar kaynakları: ortam değişkeni > `.env` > `config.yaml` > varsayılan (`core/config.py`).
- Modeller `model_files/` altında; indirme: `python scripts/download_models.py --target backend`.
- `DEBUG=true`: `/docs`, `/monitor` (yalnız yerel).

## Test

```powershell
pytest                       # model indirmez
pytest -m requires_model     # gerçek MiDaS IR ile
ruff check .; ruff format --check .
```

## Dizinler

| Dizin | İçerik |
|---|---|
| `core/` | Ayar, log, hata zarfı, API anahtarı, hız sınırı, ortak bağımlılıklar |
| `routers/` | `analyze`, `assistant`, `debug` |
| `services/` | Derinlik, tespit, takip, uyarı motoru, VLM, kare analizi |
| `models/` | Pydantic yanıt şemaları |
| `static/monitor.html` | Debug izleme sayfası |
