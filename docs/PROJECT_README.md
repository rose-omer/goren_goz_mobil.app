# 👁️ Gören Göz Mobil - Yapay Zeka Destekli Derinlik Algılama Sistemi

**Gören Göz Mobil**, görme engelli ve düşük görüşlü bireyler için geliştirilmiş, **yapay zeka tabanlı gerçek zamanlı engel algılama** sistemidir. Android telefonun kamerasını kullanarak derinlik tahmini yapar ve çarpışma risklerinde kullanıcıyı uyarır.

## 🎯 Sistem Mimarisi

```
┌─────────────────────────┐
│  Android App (Flutter)  │
│  - Kamera yakalama      │
│  - Görsel/sesli uyarı   │
│  - UI/UX                │
└────────┬────────────────┘
         │ HTTP/REST
         │ (Image Upload)
         ↓
┌─────────────────────────┐
│  FastAPI Backend        │
│  - MiDaS AI Model       │
│  - Derinlik tahmini     │
│  - Alert analizi        │
└─────────────────────────┘
```

## ✨ Özellikler

### 🤖 Backend (FastAPI)
- ✅ **MiDaS Derinlik Modeli**: PyTorch tabanlı tek kamera derinlik tahmini
- ✅ **REST API**: `/api/analyze` endpoint'i ile görüntü analizi
- ✅ **Rate Limiting**: Saniyede 5 istek sınırı (DDoS koruması)
- ✅ **CORS Desteği**: Mobil uygulama için güvenli iletişim
- ✅ **Health Check**: `/health` endpoint'i ile sistem durumu
- ✅ **Docker Desteği**: Production-ready Dockerfile
- ✅ **Auto-scaling**: Uvicorn workers ile paralel işlem

### 📱 Mobil Uygulama (Flutter)
- ✅ **Gerçek Zamanlı Kamera**: 5 FPS (ayarlanabilir) frame yakalama
- ✅ **Akıllı Uyarı Sistemi**: 
  - 🔴 **DANGER** (< 1m): Kırmızı ekran + sesli alarm
  - 🟡 **NEAR** (1-2m): Sarı uyarı barı
  - 🟢 **SAFE** (> 2m): Yeşil durum
- ✅ **İstatistikler**: FPS, min/avg mesafe, işlem süresi
- ✅ **Ayarlar**: API URL, ses aç/kapa, frame rate
- ✅ **Retry Logic**: Bağlantı hatalarında otomatik tekrar deneme
- ✅ **Offline Mode**: API olmadan çalışma (demo için)

## 📁 Proje Yapısı

```
goren_goz_mobil.app/
│
├── backend/                    # FastAPI Backend
│   ├── main.py                # Ana uygulama
│   ├── routers/
│   │   └── analyze.py         # /api/analyze endpoint
│   ├── services/
│   │   ├── depth_service.py   # MiDaS wrapper
│   │   ├── alert_service.py   # Uyarı mantığı
│   │   └── image_service.py   # Görüntü işleme
│   ├── models/
│   │   └── response.py        # Pydantic modeller
│   ├── core/
│   │   ├── config.py          # Ayarlar
│   │   └── logger.py          # Loglama
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── mobile_app/                 # Flutter Mobil Uygulama
│   ├── lib/
│   │   ├── main.dart          # Uygulama giriş noktası
│   │   ├── screens/
│   │   │   ├── splash_screen.dart
│   │   │   ├── camera_screen.dart   # Ana ekran
│   │   │   └── settings_screen.dart
│   │   ├── services/
│   │   │   ├── api_service.dart     # Backend iletişimi
│   │   │   └── sound_service.dart   # Sesli uyarı
│   │   ├── models/
│   │   │   ├── alert_level.dart
│   │   │   └── api_response.dart
│   │   ├── widgets/
│   │   │   ├── alert_overlay.dart   # Uyarı barı
│   │   │   └── info_panel.dart      # İstatistik paneli
│   │   └── utils/
│   │       ├── constants.dart       # Sabitler
│   │       └── logger.dart          # Log yönetimi
│   ├── android/
│   │   └── app/src/main/
│   │       └── AndroidManifest.xml  # İzinler
│   ├── pubspec.yaml
│   └── README.md
│
├── src/                        # Orijinal Python Desktop App (Legacy)
├── config/                     # Paylaşılan konfigürasyon
│   └── config.yaml
├── data/                       # Model ve test verileri
└── README.md                   # Bu dosya
```

## 🚀 Kurulum ve Çalıştırma

### 1️⃣ Backend Kurulumu

```bash
# Backend dizinine git
cd backend

# Virtual environment oluştur
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
copy .env.example .env

# Sunucuyu başlat
python main.py
```

Backend şu adreste çalışacak: **http://localhost:8000**

API Dokümantasyonu: **http://localhost:8000/docs**

### 2️⃣ Mobil Uygulama Kurulumu

```bash
# Mobil uygulama dizinine git
cd mobile_app

# Flutter bağımlılıklarını yükle
flutter pub get

# API URL'ini ayarla (lib/utils/constants.dart)
# defaultApiUrl = 'http://YOUR_IP:8000'

# Uygulamayı çalıştır
flutter run
```

**NOT:** Android emülatör için `http://10.0.2.2:8000` kullanın.

### 3️⃣ Docker ile Çalıştırma (Opsiyonel)

```bash
cd backend

# Image oluştur
docker build -t goren-goz-backend .

# Container çalıştır
docker run -d -p 8000:8000 goren-goz-backend
```

## 🧪 Test

### Backend Testi
```bash
cd backend

# Health check
curl http://localhost:8000/health

# Image analizi (test.jpg ile)
curl -X POST http://localhost:8000/api/analyze \
  -F "image=@test.jpg" \
  -F "include_depth_image=true"
```

### Mobil Test
1. Backend'in çalıştığından emin olun
2. Mobil uygulamayı açın
3. Kamera izni verin
4. Kamerayı bir nesneye doğrultun
5. Uyarıları gözlemleyin

## 📊 Performans Metrikleri

| Metrik | Hedef | Gerçek |
|--------|-------|--------|
| Backend Response Time | < 500ms | ~234ms (avg) |
| Mobil FPS | 5 | 4.8-5.2 |
| Gecikme (End-to-End) | < 1s | ~700ms |
| Model Loading | 3-5s | ~3.2s |

**Test Ortamı:** Intel i7, 16GB RAM, MiDaS_small model

## 🔧 Konfigürasyon

### Backend (config.yaml)
```yaml
depth_model:
  model_type: "MiDaS_small"  # Hızlı çalışır
  device: "auto"              # CPU/GPU otomatik

alerts:
  min_distance: 1.0           # DANGER eşiği (metre)
  warning_distance: 2.0       # NEAR eşiği
```

### Mobil (constants.dart)
```dart
static const Duration frameInterval = Duration(milliseconds: 200); // 5 FPS
static const int maxRetries = 2;
static const Duration requestTimeout = Duration(seconds: 5);
```

## 🌐 Deployment

### Backend - Render.com (Ücretsiz)
1. GitHub'a push yapın
2. Render.com'da yeni Web Service oluşturun
3. Repository'yi bağlayın
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Mobil - APK Build
```bash
cd mobile_app
flutter build apk --release
```

APK: `build/app/outputs/flutter-apk/app-release.apk`

## 🐛 Sorun Giderme

### Backend
- **Model yüklenmiyor**: İlk çalıştırmada model indirilir (~400MB), internet bağlantısı gerekli
- **CORS hatası**: `.env` dosyasında `CORS_ORIGINS=*` olduğundan emin olun
- **Yavaş response**: `MiDaS_small` modeline geçin

### Mobil
- **Kamera açılmıyor**: Cihaz ayarlarından kamera izni verin
- **Bağlantı hatası**: API URL'ini kontrol edin, backend çalışıyor olmalı
- **Donma/lag**: Frame rate'i düşürün (3 FPS)

## 📝 API Referansı

### POST /api/analyze

**Request:**
```bash
Content-Type: multipart/form-data

image: [JPEG/PNG file]
include_depth_image: boolean (optional)
colormap: string (optional, default: JET)
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-11-24T12:34:56.789Z",
  "processing_time_ms": 234.5,
  "data": {
    "alert_level": "DANGER",
    "distance_stats": {
      "min": 0.45,
      "max": 4.8,
      "avg": 2.1
    },
    "warnings": [
      {
        "message": "DANGER! Object detected at 0.45m",
        "level": "DANGER",
        "distance": 0.45,
        "area_percentage": 12.3
      }
    ],
    "depth_image_base64": "data:image/jpeg;base64,..."
  }
}
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun: `git checkout -b feature/amazing-feature`
3. Commit yapın: `git commit -m 'feat: Add amazing feature'`
4. Push edin: `git push origin feature/amazing-feature`
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altındadır.

## 🙏 Teşekkürler

- **MiDaS** - Intel ISL (Derinlik tahmini modeli)
- **FastAPI** - Modern Python web framework
- **Flutter** - Cross-platform mobil framework
- **PyTorch** - Derin öğrenme library
- **OpenCV** - Görüntü işleme

## 👨‍💻 Geliştirici

**Proje:** Gören Göz Mobil  
**Versiyon:** 1.0.0  
**Tarih:** Kasım 2025  

**Not:** Bu sistem, görme engelli bireylerin bağımsız mobilitesini artırmak için geliştirilmiştir. Ancak tamamen güvenlik cihazı değildir ve baston/rehber köpek gibi asıl yardımcı araçların yerine geçmez.

---

**Destek İçin:** Issues sekmesinden bildirebilirsiniz.  
**Dokümantasyon:** Backend ve Mobil klasörlerindeki README.md dosyalarına bakın.

🚀 **Başarılar!**
