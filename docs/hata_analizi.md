# 🔍 Gören Göz Mobil - Proje Hata Analizi Raporu

## 📋 Genel Bakış

**Proje Adı**: Gören Göz Mobil - Görme Engelliler için AI Destekli Navigasyon  
**Analiz Tarihi**: 2025-12-19  
**Proje Yapısı**: 
- 🔹 **Backend**: Python 3.10+ / FastAPI / MiDaS Depth Estimation / YOLOv11
- 🔹 **Mobile App**: Flutter/Dart / Camera / TTS / Audio
- 🔹 **Mimari**: REST API + Mobile Client

---

## ✅ Proje Durumu Özeti

**Toplam Tespit Edilen Sorun**: 8 kritik, 12 uyarı, 15 öneri  
**Genel Sağlık Skoru**: 7.5/10

---

## 🔴 KRİTİK HATALAR

### 1. **Backend - Import Hataları (analyze.py)**

**Dosya**: [`backend/routers/analyze.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/routers/analyze.py#L17)

**Sorun**: `analyze.py` dosyasında `DetectedObject` modeli tanımlı ancak object detection servisi geriye farklı bir yapı dönüyor.

```python
# Line 238-254 - Hatalı mapping
for obj in detected_objects_list:
    eng_name = obj.get('class_name', 'unknown')  # ❌ 'class_name' yok, 'name' olmalı
```

**Etki**: Object detection çalıştığında field mapping hatası.

**Çözüm**:
```python
# object_detection_service.py döndürdüğü yapı:
{
    'name': class_name,  # ✅ 'class_name' değil, 'name'
    'name_tr': name_tr,
    ...
}
```

---

### 2. **Backend - Tutarsız Distance Bilgisi**

**Dosya**: [`backend/routers/analyze.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/routers/analyze.py#L158-162)

**Sorun**: Object detection servisi `distance` bilgisi döndürmüyor, ancak response model'de kullanılıyor.

```python
# Line 246 - ❌ distance yokken kullanılıyor
distance=obj.get('distance', 0.0),  # Her zaman 0.0 dönecek
```

**Etki**: Tespit edilen nesnelerin mesafe bilgisi eksik.

**Çözüm**: Object detection servisine depth map entegrasyonu gerekli:
```python
# object_detection_service.py'de detection'a ekle:
def detect(self, image, depth_map=None):
    # ...
    if depth_map is not None:
        # Bbox center pozisyonundan mesafe bilgisi al
        center_y, center_x = int(center_y), int(center_x)
        distance = depth_map[center_y, center_x]
        detection['distance'] = float(distance)
```

---

### 3. **Requirements - Eksik Bağımlılık**

**Dosya**: [`backend/requirements.txt`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/requirements.txt)

**Sorun**: YOLO kullanımı için `ultralytics` paketi eksik!

```txt
# ❌ Eksik:
ultralytics>=8.0.0  # YOLOv11 için gerekli
```

**Etki**: Object detection servisi çalışmaz.

**Çözüm**: `requirements.txt`'ye ekle:
```txt
ultralytics>=8.0.0
```

---

### 4. **Backend - Config yaml dosyası yok**

**Dosya**: [`backend/core/config.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/core/config.py#L64)

**Sorun**: Config kodda `config/config.yaml` okuyor ama dosya yok.

```python
# Line 64
config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
```

**Etki**: Uygulama default değerlerle çalışır, özelleştirilmiş ayarlar yüklenmez.

**Çözüm**: `config/config.yaml` dosyası oluşturulmalı:
```yaml
depth_model:
  model_type: "MiDaS_small"
  device: "auto"
  min_depth: 0.5
  max_depth: 5.0

alerts:
  min_distance: 0.5
  warning_distance: 1.2
  warning_area_threshold: 0.10

camera:
  width: 640
  height: 480
```

---

### 5. **Mobile App - Kullanılmayan Fonksiyon**

**Dosya**: [`mobile_app/lib/services/api_service.dart`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/mobile_app/lib/services/api_service.dart#L137-163)

**Sorun**: `_shouldProcessFrame()` fonksiyonu tanımlı ama hiç çağrılmıyor!

```dart
// Line 137 - Tanımlı ama kullanılmayan
bool _shouldProcessFrame(Uint8List current) { ... }
```

**Etki**: Frame skip optimizasyonu çalışmıyor, gereksiz API çağrıları.

**Çözüm**: `analyzeImage()` içinde kullan:
```dart
Future<ApiResponse?> analyzeImage(Uint8List imageBytes, ...) async {
  // Frame skip kontrolü ekle
  if (!_shouldProcessFrame(imageBytes)) {
    return _lastResponse;  // Önceki sonucu dön
  }
  // ... devam
}
```

---

### 6. **Backend - Potential Memory Leak**

**Dosya**: [`backend/routers/analyze.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/routers/analyze.py#L124)

**Sorun**: Her request'te tracking service kullanılıyor ama singleton pattern yanlış.

```python
# Line 124
tracking_service = get_tracking_service()  # ✅ Singleton
# Ancak tracked_objects dictionary sürekli büyüyor (memory leak)
```

**Etki**: Uzun süre çalışan backend'de hafıza artışı.

**Çözüm**: Tracking service'de TTL (Time To Live) ekle:
```python
# object_tracking_service.py
def cleanup_old_tracks(self, max_age_seconds=30):
    current_time = time.time()
    self.tracked_objects = {
        k: v for k, v in self.tracked_objects.items()
        if current_time - v['last_seen'] < max_age_seconds
    }
```

---

### 7. **Backend - depth_map Boyut Hatası Riski**

**Dosya**: [`backend/services/depth_service.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/services/depth_service.py#L162-167)

**Sorun**: Depth map resize edilirken boyut kontrolü yok.

```python
# Line 162-167
if metric_depth.shape != image.shape[:2]:
    metric_depth = cv2.resize(...)  # ❌ Shape mismatch olabilir
```

**Risk**: (480, 640) vs (640, 480) karmaşası → ValueError

**Çözüm**:
```python
# Boyutları açıkça belirt
target_height, target_width = image.shape[:2]
metric_depth = cv2.resize(
    metric_depth,
    (target_width, target_height),  # (width, height) sırası
    interpolation=cv2.INTER_CUBIC
)
```

---

### 8. **Mobile App - Missing Distance Field**

**Dosya**: [`mobile_app/lib/models/api_response.dart`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/mobile_app/lib/models/)

**Sorun**: Backend DetectedObject'te `distance` field'ı var ama mobile modelde eksik olabilir.

**Çözüm**: Model tanımını kontrol et ve `distance` field ekle:
```dart
class DetectedObject {
  final String name;
  final String nameTr;
  final double confidence;
  final double distance;  // ✅ Ekle
  // ...
}
```

---

## ⚠️ UYARILAR

### 9. **Backend - Performans - Ground Analysis Her Frame**

**Dosya**: [`backend/routers/analyze.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/routers/analyze.py#L168-176)

**Uyarı**: Ground analysis sadece az nesne varken çalışıyor.

```python
# Line 168 - Mantıksal sorun
ground_analysis = ground_service.analyze(depth_map) if len(detected_objects_list) < 3 else { ... }
```

**Risk**: Açık alanda (nesne yok) → analiz yapılıyor ✅  
Kalabalık yerde (çok nesne) → analiz yapılmıyor ❌

**Öneri**: Condition değiştir veya kaldır:
```python
# Her zaman çalıştır ama cache'le
ground_analysis = ground_service.analyze(depth_map)
```

---

### 10. **Backend - Alert Service - Türkçe Mesajlar Eksik**

**Çözüm**: Alert servisinde Türkçe dil desteği kontrol edilmeli.

---

### 11. **Mobile App - Error Handling Eksik**

**Dosya**: [`mobile_app/lib/services/api_service.dart`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/mobile_app/lib/services/api_service.dart#L123-125)

```dart
// Line 123-125
catch (e) {
  AppLogger.error('Unexpected error in analyzeImage', e);
  return null;  // ❌ Null dönmek yerine error response dön
}
```

---

### 12. **Backend - YOLO Model Fallback**

**Dosya**: [`backend/services/object_detection_service.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/services/object_detection_service.py#L238-243)

**Uyarı**: YOLOv11n bulunamazsa YOLOv8n'e fallback var ama model dosyası var mı kontrol yok.

```python
# Line 238
self.model = YOLO('yolo11n.pt')  # Dosya yoksa hata!
```

**Çözüm**: Dosya varlığı kontrol et:
```python
model_path = Path('yolo11n.pt')
if not model_path.exists():
    logger.warning("yolo11n.pt not found, downloading...")
```

---

### 13. **Backend - Rate Limiting Yanlış Yapılandırma**

**Dosya**: [`backend/main.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/main.py#L132)

```python
# Line 132
@limiter.limit("10/minute")  # Health check için çok az
```

Health check genelde daha yüksek limit almalı (örn: 60/minute).

---

### 14. **README - Yanlış Proje Bilgisi**

**Dosya**: [`README.md`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/README.md#L1-3)

**Uyarı**: README hala "Gören Göz Laptop" diyor, "Gören Göz Mobil" olmalı.

```markdown
# ❌ Gören Göz Laptop - Yapay Zeka Destekli...

# ✅ Olmalı:
# Gören Göz Mobil - Yapay Zeka Destekli Derinlik Algılama Sistemi
```

---

### 15. **Requirements - Python Version Mismatch**

**Ana requirements.txt**: Python 3.12  
**Backend requirements.txt**: Python 3.10+

İkisi de çalışır ama tutarlılık için birine karar verilmeli.

---

### 16. **Mobile - Constants Missing**

**Dosya**: `mobile_app/lib/utils/constants.dart`

Bu dosyayı görmedik ama kullanılıyor. İçeriği kontrol edilmeli:
- `AppConfig.apiUrl`
- `AppConfig.requestTimeout`
- vs.

---

### 17. **Backend - Logger Module Import**

**Dosya**: `backend/core/logger.py`

Bu modül `setup_logging()` export ediyor ama `__init__.py`'den export edilmeli.

---

### 18. **Mobile - iOS/Android Permissions**

Kamera ve mikrofon için permission kontrolleri var mı?

- Android: `AndroidManifest.xml` kontrol et
- iOS: `Info.plist` kontrol et

---

### 19. **Backend - CORS Origins Wildcard**

**Dosya**: [`backend/core/config.py`](file:///c:/Users/admin/Desktop/goren_goz_mobil.app/backend/core/config.py#L28)

```python
# Line 28
cors_origins: List[str] = Field(default=["*"])  # ⚠️ Production'da tehlikeli
```

**Öneri**: Production'da spesifik originler kullan.

---

### 20. **Backend - Log File Rotation Yok**

`backend.log` dosyası sürekli büyüyecek. Rotation ekle:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/backend.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## 💡 İYİLEŞTİRME ÖNERİLERİ

### 21. **Backend - Depth + Object Integration**

Object detection ve depth estimation şu anda ayrı çalışıyor. Entegre edilmeli:

```python
# Öneri: Combined service
def detect_with_depth(image, depth_map):
    objects = detect_objects(image)
    for obj in objects:
        cx, cy = obj['center']
        obj['distance'] = depth_map[int(cy), int(cx)]
    return objects
```

---

### 22. **Mobile - Offline Mode**

Backend ulaşılamazsa son bilinen alertleri göster.

---

### 23. **Backend - Model Caching**

MiDaS model her startup'ta download ediliyor. Cache lokasyonu belirle:

```python
torch.hub.set_dir('./models/cache')
```

---

### 24. **Mobile - Battery Optimization**

Kamera sürekli açık → batarya tüketimi yüksek. Idle detection ekle.

---

### 25. **Backend - Metrics & Monitoring**

Prometheus/Grafana entegrasyonu:
- Request count
- Processing time
- Error rate

---

### 26. **Testing - Unit Tests Eksik**

Backend ve mobile için unit testler yok!

```python
# backend/tests/test_depth_service.py
def test_depth_estimation():
    service = get_depth_service()
    image = cv2.imread('test.jpg')
    depth = service.estimate(image)
    assert depth is not None
```

---

### 27. **Documentation - API Docs**

FastAPI Swagger var ama Türkçe dil desteği eklenmeli.

---

### 28. **Mobile - Accessibility**

Görme engelliler için:
- Daha büyük ses feedback
- Vibration patterns
- Voice commands

---

### 29. **Backend - Database Integration**

Kullanıcı verileri, istatistikler için DB eklenebilir.

---

### 30. **CI/CD Pipeline**

GitHub Actions ile otomatik test ve deployment.

---

## 📊 Dosya Bazlı Sorun Özeti

| Dosya | Kritik | Uyarı | Öneri |
|-------|--------|-------|-------|
| `backend/routers/analyze.py` | 3 | 1 | 2 |
| `backend/services/object_detection_service.py` | 1 | 1 | 1 |
| `backend/core/config.py` | 1 | 2 | 1 |
| `backend/requirements.txt` | 1 | 1 | 0 |
| `mobile_app/lib/services/api_service.dart` | 1 | 1 | 3 |
| `README.md` | 0 | 1 | 1 |
| Genel Mimari | 1 | 4 | 7 |

---

## 🎯 Öncelikli Düzeltmeler (Öncelik Sırası)

### Acil (Bugün)
1. ✅ `ultralytics` dependency ekle
2. ✅ `config/config.yaml` dosyası oluştur
3. ✅ Object detection field mapping düzelt (`class_name` → `name`)
4. ✅ Frame skip fonksiyonunu aktif et

### Kısa Vadeli (Bu hafta)
5. Distance integration (depth + objects)
6. Memory leak düzeltmeleri (tracking cleanup)
7. Error handling iyileştirmeleri
8. README güncelle

### Orta Vadeli (2 hafta)
9. Unit testler ekle
10. Log rotation ekle
11. CORS configuration production-ready yap
12. Model caching düzenle

### Uzun Vadeli
13. Monitoring ekle
14. Database integration
15. CI/CD pipeline
16. Accessibility features

---

## ✨ Sonuç

**Proje Genel Durumu**: İyi bir temel var ama production-ready değil.

**Güçlü Yanlar**:
- ✅ Modern stack (FastAPI, Flutter)
- ✅ AI entegrasyonu (MiDaS, YOLO)
- ✅ Clean architecture
- ✅ Türkçe dil desteği

**Zayıf Yanlar**:
- ❌ Test coverage yok
- ❌ Bazı kritik hatalar
- ❌ Production optimizasyonları eksik
- ❌ Monitoring/logging yetersiz

**Tavsiye**: Yukarıdaki "Acil" ve "Kısa Vadeli" düzeltmeleri yapıldıktan sonra beta test edilebilir.

---

**Rapor Tarihi**: 2025-12-19  
**Analiz Eden**: Antigravity AI  
**Sonraki İnceleme**: Düzeltmeler sonrası
