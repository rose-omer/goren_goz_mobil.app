# Gören Göz

Görme engelli kişiler için sesli engel uyarısı ve Türkçe soru-cevap. Telefon kamerası önü izler; uygulama tehlikeyi sesle, titreşimle ve kısa Türkçe cümleyle bildirir.

> Gören Göz yardımcı bir araçtır. Baston ya da rehber köpeğin yerini tutmaz.

## Durum

| Parça | Durum |
|---|---|
| Mobil uygulama (Flutter 3.50.1) | Yeni arayüz: dört bantlı yürüyüş ekranı, TalkBack, haptik desen, Türkçe ses. `flutter analyze` 0 bulgu, 68 test. |
| Uyarı motoru | TTC + nesne boyu mesafesi + histerezis + konuşma kuyruğu. Mobil ve backend aynı kural. |
| Algılama | Şimdilik sunucuda (MiDaS + YOLO). Cihaz üstü LiteRT modeli eğitim bekliyor (`docs/MODELS.md`). |
| Backend (FastAPI 0.165) | API anahtarı, tek hız sınırı, oturum başına takip, debug uçları kapalı. 66 test, model indirmeden. |
| VLM | llama-server `/v1/chat/completions` + `image_url`, Türkçe istem. Model `VLM_MODEL` ile seçilir. |
| Ölçüm | Uçtan uca gecikme ve doğruluk tabloları henüz ölçülmedi. |

## Mimari

```
Telefon                                        Sunucu (isteğe bağlı)
┌──────────────────────────────┐   kare    ┌──────────────────────────┐
│ Kamera akışı (YUV, 640 px)   │──────────▶│ /api/analyze             │
│ Uyarı motoru + histerezis    │◀──────────│ MiDaS göreli derinlik    │
│ Konuşma kuyruğu, haptik, ses │  nesneler │ YOLO + oturum takibi/TTC │
│ Soru sor (tr_TR)             │──────────▶│ /api/ask_context → VLM   │
└──────────────────────────────┘           └──────────────────────────┘
```

Ayrıntı: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Hızlı başlangıç

### Backend

Bu makinede 8000, 1984, 8554, 8555 portları yasak. Varsayılan port 8110.

```powershell
cd backend
py -3.11 -m venv .venv; .venv\Scripts\activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-dev.txt
copy .env.example .env        # API_KEY değerini doldur
python scripts/download_models.py --target backend   # önce scripts/models.json'u doldur
Get-NetTCPConnection -LocalPort 8110 -State Listen    # boş olmalı
uvicorn main:app --host 0.0.0.0 --port 8110
```

- Telefondan bağlanmak için `--host 0.0.0.0` ve `API_KEY` zorunlu.
- `DEBUG=true` iken `/docs` ve `/monitor` yalnız bu makineden açılır.
- Docker: `docker build -t goren-goz-backend backend` → `docker run -p 8110:8110 --env-file backend/.env goren-goz-backend`.

### VLM (isteğe bağlı)

```powershell
llama-server -m <model>.gguf --mmproj <mmproj>.gguf --port 8120 --api-key $env:VLM_API_KEY
```

Backend `.env`: `VLM_SERVER_URL=http://127.0.0.1:8120`, `VLM_API_KEY`, `VLM_MODEL`. Varsayılan model `SmolVLM2-500M-Video-Instruct`; Türkçe ölçümden sonra değiştir.

### Mobil

```powershell
cd mobile_app
C:\src\flutter\bin\flutter.bat pub get
C:\src\flutter\bin\flutter.bat test
C:\src\flutter\bin\flutter.bat run      # Android cihaz
```

İlk açılış: kamera izni → Ayarlar bandı → sunucu adresi ve API anahtarı → "Kaydet ve dene". Debug sürümü yerel ağ HTTP'sini (`http://192.168.x.x:8110`) kabul eder; release sürümü yalnız `https://` kabul eder.

## Ekranlar

- **Açılış:** sesli karşılama, ekranın alt yarısında tek "Kamera iznini ver" düğmesi, bir kerelik güvenlik uyarısı ve kullanım turu.
- **Yürüyüş:** dört tam genişlik bant: Durumu söyle, Soru sor, Duraklat, Ayarlar. Üstte seviye şeridi (Dur, Dikkat).
- **Ayarlar:** konuşma hızı, ses, titreşim, yön anlatımı (sol/orta/sağ ya da saat yönü), ayrıntı düzeyi, sunucu, tema.
- **Yardımcı görünümü:** gören yardımcı ve jüri için kamera, kutular, FPS, gecikme.

Ayrıntı: [docs/ACCESSIBILITY.md](docs/ACCESSIBILITY.md).

## Ölçüm tabloları

Henüz ölçülmedi. Yöntem ve boş tablolar: [docs/TEST_PLAN.md](docs/TEST_PLAN.md).

| Ölçüm | Önce | Sonra |
|---|---|---|
| Uyarı gecikmesi p95 (kare → ses) | ölçülmedi | ölçülmedi |
| Nesne boyu mesafe hatası (insan, araç) | yok | ölçülmedi |
| VLM doğru cevap oranı (30 soru) | ölçülmedi | ölçülmedi |

## Sınırlar

- MiDaS göreli derinlik verir; uygulama derinlikten metre söylemez. Metre yalnız nesne boyundan ve kalibrasyonla gelir.
- COCO sınıfları merdiven, bordür, direk, çukur içermez. 12 sınıflı Türkiye modeli eğitilmedi.
- Algılama şimdilik sunucuya bağlı. Bağlantı koparsa uygulama bunu sesle ve uzun titreşimle bildirir.
- Android SDK olmadan APK derlenmedi; TalkBack el testi yapılmadı.

## Belgeler

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): bileşenler, veri akışı, güvenlik varsayılanları.
- [docs/MODELS.md](docs/MODELS.md): eğitim, dışa aktarma, model dağıtımı, lisanslar.
- [docs/ACCESSIBILITY.md](docs/ACCESSIBILITY.md): ekranlar, tasarım tokenleri, haptik ve ses desenleri, TalkBack.
- [docs/TEST_PLAN.md](docs/TEST_PLAN.md): otomatik testler, el testi listesi, saha testi.
- [docs/THESIS_REPORT.md](docs/THESIS_REPORT.md): bitirme raporu.

## Lisans

Karar bekliyor. Ultralytics AGPL-3.0 olduğu için öneri AGPL-3.0 (bkz. `docs/MODELS.md`).
