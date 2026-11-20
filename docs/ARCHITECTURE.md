# Mimari

## Bileşenler

| Katman | Dosya | Görev |
|---|---|---|
| Kare kaynağı | `mobile_app/lib/perception/frame_source.dart` | `startImageStream`, `ResolutionPreset.medium`, YUV420. Önceki kare işlenmeden yenisini almaz. JPEG kodlaması isolate'ta; oran korunur, uzun kenar 640 px. |
| Uyarı motoru | `mobile_app/lib/core/hazard_engine.dart` | Seviye kuralı, histerezis, Türkçe mesaj. |
| Konuşma kuyruğu | `mobile_app/lib/core/speech_queue.dart` | DANGER keser; aynı nesne-yön 6 s içinde tekrar edilmez; en fazla 2 bekleyen mesaj. |
| Yürüyüş döngüsü | `mobile_app/lib/walk/walk_controller.dart` | Kare → sunucu → motor → ses, titreşim, TTS. Bağlantı kopmasını bildirir. |
| Sunucu istemcisi | `mobile_app/lib/services/api_client.dart` | Analiz ve soru ayrı `Dio` örneği (zaman aşımı birbirini ezmez). Analiz: bağlantı 2 s, okuma 2 s, yeniden deneme yok; 2 ardışık zaman aşımı "bağlantı koptu" sayılır. Soru: bağlantı 5 s, okuma 30 s, yeni FormData ile bir yeniden deneme. |
| API | `backend/main.py`, `backend/routers/*` | Uygulama fabrikası, lifespan'da servis yükleme, tek hata zarfı. |
| Kare analizi | `backend/services/pipeline.py` | Derinlik + tespit thread havuzunda; oturum durumu kilitli. |
| Derinlik | `backend/services/depth/` | `DepthEstimator` protokolü; `openvino_midas` arka ucu; tek ön işleme fonksiyonu. |
| Yakınlık | `backend/services/proximity.py` | Göreli derinliği son 30 karenin yüzdelikleriyle 0–1 yakınlığa çevirir. Metre üretmez. |
| Takip ve TTC | `backend/services/tracking.py` | IoU eşleştirme, kutu yüksekliği büyümesinden TTC, `X-Session-Id` başına durum, 60 s TTL. |
| VLM | `backend/services/vlm_service.py` | `/v1/chat/completions` + `image_url`; paylaşılan `httpx.AsyncClient`; Türkçe istem. |

## Uyarı kuralı (mobil ve backend aynı)

- `DANGER`: orta bölgede TTC < 2 s ya da nesne boyu mesafesi < 1 m.
- `NEAR`: TTC < 4 s ya da mesafe < 2 m; yanda tehlike de NEAR olur. Orta bandın "çok yakın" alanı ≥ %10 ise NEAR.
- `INFO`: algılanan nesne var, risk yok.
- `CLEAR`: nesne yok. "Yol açık" yalnız tespit modeli çalışıyorsa (`detector_ok: true`) ve derinlik ısınmış ve temizse söylenir. Tespit yoksa mobil bunu bir kez söyler ve "Yol açık" demez.
- Histerezis: seviye 2 ardışık karede görülmeden yükselmez, 5 karede görülmeden düşmez.
- Mesaj: önce eylem, sonra nesne, sonra yön. "Dur. İnsan, önde." · "Dikkat. Direk, sağda." · "İnsan, önde, 2 metre."

## Mesafe

1. Nesne boyu: `d = f_px · H / h_px`. `f_px` A4 kalibrasyonundan (1 m'de dik tutulan kâğıt). Kutu kare kenarına değiyorsa mesafe verilmez.
2. Göreli derinlik: yalnız "çok yakın / yakın / uzak" ve yön sıralaması.
3. TTC: kutu yüksekliğinin üstel düzleştirilmiş büyüme hızından; metre gerektirmez.

## API

| Uç | Kimlik | Not |
|---|---|---|
| `POST /api/analyze` | `X-API-Key` | `image` (JPEG/PNG), isteğe bağlı `focal_px`, `include_depth_image`. Başlık `X-Session-Id`. |
| `POST /api/ask_context` | `X-API-Key` | `image`, `question` (≤ 300 karakter). VLM yoksa 503 `VLM_UNAVAILABLE`. |
| `GET /api/preset_questions` | `X-API-Key` | Türkçe hazır sorular. |
| `GET /health` | yok | Yalnız durum okur; model yüklemez, VLM'e bağlanmaz. |
| `GET /monitor`, `GET /api/ask_context_history` | yalnız `DEBUG=true` ve yerel istemci | Geçmiş metin içerir, görüntü içermez. |

Hata zarfı: `{"success": false, "error": {"code": "...", "message": "..."}}`. İç ayrıntı istemciye gitmez.

## Güvenlik varsayılanları

- `DEBUG=false`, `HOST=127.0.0.1`, `PORT=8110`. `/docs` yalnız debug'da.
- `API_KEY` yoksa ve debug kapalıysa istekler 503 `API_KEY_NOT_CONFIGURED` alır.
- CORS kapalı; `CORS_ORIGINS` yalnız tarayıcı debug sayfası için, `allow_credentials=False`.
- Gövde boyutu `Content-Length` ile okunmadan, piksel sayısı çözülmeden denetlenir (5 MB, 4 MP).
- Sunucu görüntü saklamaz; log'da soru metni ve görüntü yok. Uygulama kareyi diske yazmaz.
- Model dosyası yoksa sunucu indirmez; açık hata verir. `torch.hub` çağrısı yok.
- Android release yalnız HTTPS; debug yerel ağ HTTP'sine izin verir. Release sürümünde ayar ekranı `http://` adresini reddeder. Release imzası `android/key.properties` ile.
- `X-Session-Id` istemci denetimli: oturum sözlüğü `MAX_SESSIONS` (256) ile sınırlı, dolunca en eski atılır. Hız sınırı anahtarı API anahtarı ya da IP; oturum kimliği değil.
