# 🚀 Gören Göz Mobil - Öncelikli Geliştirme Önerileri

**Tarih**: 2025-12-20  
**Mevcut Durum**: Backend stabil, performans kabul edilebilir (230ms)  
**Hedef**: Production-ready + Accuracy artışı

---

## 🎯 ÖNCELİK 1: ACCURACY ARTIŞI (En Önemli!)

### 1.1 Custom Dataset + Fine-tuning ⭐⭐⭐⭐⭐

**Neden En Önemli**:
- Türkiye'ye özgü nesneler (kaldırım, elektrik direkleri, Türk trafik işaretleri)
- Görme engelli kullanım senaryolarına özel
- %20-30 accuracy artışı bekleniyor
- Bigger model'den daha etkili

**Adımlar**:

#### A. Dataset Toplama (1 hafta)
```
Hedef: 300-500 image
- Türk sokakları, kaldırımlar
- Farklı şehirler (İstanbul, Ankara, İzmir)
- Farklı hava koşulları (güneşli, yağmurlu, sisli)
- Zemin engelleri (çukur, kırık kaldırım, taş)
```

**Özel Sınıflar**:
- `sidewalk` (kaldırım)
- `pole_electric` (elektrik direği)
- `pothole` (çukur)
- `curb` (bordür)
- `turkish_traffic_sign` (Türk trafik levhaları)

#### B. Annotation (3-5 gün)
```bash
# Roboflow kullan (tavsiye!)
1. Roboflow hesabı oluştur
2. "Goren-Goz-Custom" projesi
3. Web interface ile annotate et
4. Augmentation: 3x (brightness, blur, noise)
5. YOLO format export
```

#### C. Fine-tuning (1-2 gün)
```python
from ultralytics import YOLO

# YOLOv11-Nano base
model = YOLO('yolo11n.pt')

# Fine-tune on custom data
results = model.train(
    data='custom_dataset.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device='cpu',  # veya Google Colab'da GPU
    patience=20,
    project='goren_goz',
    name='yolo11n_custom'
)

# Export custom model
model.export(format='onnx')
```

**Süre**: 2-3 hafta  
**Beklenen Kazanç**: +20-30% accuracy (domain-specific)  
**ROI**: ⭐⭐⭐⭐⭐ (En yüksek)

---

## 🎯 ÖNCELİK 2: OPENVINO DÜZELTMESİ

### 2.1 OpenVINO Conversion Hatası Çözümü ⭐⭐⭐⭐

**Sorun**: Model conversion başarısız (ONNX export hatası)

**Çözüm Adımları**:

#### A. NumPy Upgrade
```bash
pip install numpy==2.2.6 --upgrade
```

#### B. ONNX Opset Version Artır
```python
# depth_service.py - _convert_to_openvino()
torch.onnx.export(
    self.model,
    dummy_input,
    str(onnx_path),
    opset_version=17,  # 11 → 17 ✅
    do_constant_folding=True,
    verbose=True  # Debug için
)
```

#### C. Manuel Test
```python
# Ayrı script ile test
python scripts/convert_midas_openvino.py
```

**Beklenen Kazanç**: 3-5x hızlanma (230ms → 50-80ms)  
**Süre**: 2-3 gün  
**ROI**: ⭐⭐⭐⭐

---

## 🎯 ÖNCELİK 3: MOBİL APP İYİLEŞTİRMELERİ

### 3.1 Sesli Geri Bildirim İyileştirme ⭐⭐⭐⭐

**Şu An**: Text-to-speech var ama basit

**Öneriler**:
- **3D Audio**: Nesnenin yönü (sol/sağ) stereo ses ile
- **Mesafe Feedback**: Uzaklığa göre ses şiddeti
- **Öncelik Sıralaması**: En tehlikeli nesneyi önce söyle

```dart
// Örnek implementation
class AudioFeedbackService {
  void playDirectionalSound(String direction, double distance) {
    // Sol/sağ kanal ayarı
    if (direction == 'left') {
      setPan(-0.7);  // Sol kanal
    } else if (direction == 'right') {
      setPan(0.7);   // Sağ kanal
    }
    
    // Mesafeye göre volume
    setVolume(1.0 / distance);
  }
}
```

**Süre**: 1 hafta  
**Kullanıcı Etkisi**: ⭐⭐⭐⭐⭐

---

### 3.2 Haptic Feedback (Titreşim) ⭐⭐⭐

**Özellik**: Tehlike yakınlığına göre titreşim

```dart
import 'package:vibration/vibration.dart';

void vibrateForDanger(String level) {
  switch (level) {
    case 'DANGER':
      Vibration.vibrate(pattern: [0, 500, 100, 500]); // Uzun-kısa-uzun
      break;
    case 'NEAR':
      Vibration.vibrate(duration: 300);
      break;
  }
}
```

**Süre**: 2-3 gün  
**Accessibility**: ⭐⭐⭐⭐⭐

---

## 🎯 ÖNCELİK 4: BACKEND İYİLEŞTİRMELERİ

### 4.1 Caching Stratejisi ⭐⭐⭐

**Model Caching**: İlk yükleme yavaş (6s), cache'le

```python
# Model preload on startup
@app.on_event("startup")
async def preload_models():
    depth_service = get_depth_service()
    depth_service.load_model()  # Lazy load yerine eager
    
    object_detection = get_object_detection_service()
    # YOLO otomatik yükleniyor
```

**Süre**: 1 gün  
**Kazanç**: İlk request hızlanır

---

### 4.2 Redis Cache (Frame Results) ⭐⭐

**Özellik**: Benzer frame'leri cache'le

```python
import redis
import hashlib

redis_client = redis.Redis()

def get_cached_result(image_hash):
    return redis_client.get(f"result:{image_hash}")

def cache_result(image_hash, result, ttl=60):
    redis_client.setex(f"result:{image_hash}", ttl, result)
```

**Süre**: 2-3 gün  
**Kazanç**: %30-40 hız artışı (tekrar eden frame'ler için)

---

### 4.3 Database Integration ⭐⭐⭐

**Özellik**: Kullanıcı verileri, rota geçmişi

```python
# PostgreSQL + SQLAlchemy
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    routes = relationship("Route", back_populates="user")

class Route(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_location = Column(String)
    end_location = Column(String)
    obstacles_encountered = Column(JSON)
```

**Süre**: 1 hafta  
**Özellikler**: User analytics, route planning

---

## 🎯 ÖNCELİK 5: PRODUCTION HAZIRLIĞI

### 5.1 Unit Tests ⭐⭐⭐⭐

**Backend Tests**:
```python
# tests/test_object_detection.py
def test_yolo_detection():
    service = ObjectDetectionService()
    image = cv2.imread('test.jpg')
    results = service.detect(image)
    assert len(results) > 0
    assert results[0]['name'] in COCO_CLASSES

# tests/test_depth_estimation.py
def test_depth_map_shape():
    service = DepthService()
    image = cv2.imread('test.jpg')
    depth = service.estimate(image)
    assert depth.shape == image.shape[:2]
```

**Mobile Tests**:
```dart
// test/api_service_test.dart
test('API should return valid response', () async {
  final response = await apiService.analyzeImage(testImage);
  expect(response.success, true);
  expect(response.detectedObjects, isNotEmpty);
});
```

**Coverage Hedefi**: >70%  
**Süre**: 1 hafta

---

### 5.2 CI/CD Pipeline ⭐⭐⭐

```yaml
# .github/workflows/backend-test.yml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov
```

**Süre**: 2-3 gün  
**Benefit**: Otomatik test + deployment

---

### 5.3 Monitoring & Logging ⭐⭐⭐

**Prometheus + Grafana**:
```python
from prometheus_client import Counter, Histogram

request_counter = Counter('api_requests_total', 'Total API requests')
inference_time = Histogram('inference_duration_seconds', 'Inference time')

@app.post("/api/analyze")
async def analyze(image: UploadFile):
    request_counter.inc()
    with inference_time.time():
        result = process_image(image)
    return result
```

**Süre**: 3-5 gün  
**Benefit**: Production monitoring

---

## 🎯 ÖNCELİK 6: KULLANICI DENEYİMİ

### 6.1 Offline Mode ⭐⭐⭐⭐

**Özellik**: İnternet olmadan çalışma

```dart
// TFLite model (edge deployment)
import 'package:tflite_flutter/tflite_flutter.dart';

class OfflineDetectionService {
  Interpreter? _interpreter;
  
  Future<void> loadModel() async {
    _interpreter = await Interpreter.fromAsset('yolo11n.tflite');
  }
  
  List<Detection> detect(Uint8List image) {
    // Local inference
  }
}
```

**Süre**: 1 hafta  
**Kullanıcı Etkisi**: ⭐⭐⭐⭐⭐

---

### 6.2 Route Planning ⭐⭐⭐

**Özellik**: Engelsiz rota planlama

```python
# Google Maps API + engel veritabanı
def find_accessible_route(start, end):
    # Statik engeller (merdiven, kaldırım yok vs)
    # Dinamik engeller (son 24 saatte tespit edilenler)
    return optimized_route
```

**Süre**: 2 hafta  
**Premium Feature**: Subscription model

---

## 📊 ÖNCELİKLENDİRME MATRİSİ

| Öneri | Etki | Süre | Zorluk | ROI | Öncelik |
|-------|------|------|--------|-----|---------|
| **Custom Dataset** | ⭐⭐⭐⭐⭐ | 2-3 hafta | Orta | ⭐⭐⭐⭐⭐ | **1** |
| **Sesli Feedback** | ⭐⭐⭐⭐⭐ | 1 hafta | Düşük | ⭐⭐⭐⭐⭐ | **2** |
| **OpenVINO Fix** | ⭐⭐⭐⭐ | 2-3 gün | Orta | ⭐⭐⭐⭐ | **3** |
| **Offline Mode** | ⭐⭐⭐⭐⭐ | 1 hafta | Orta | ⭐⭐⭐⭐ | **4** |
| **Haptic Feedback** | ⭐⭐⭐⭐ | 2-3 gün | Düşük | ⭐⭐⭐⭐ | **5** |
| **Unit Tests** | ⭐⭐⭐⭐ | 1 hafta | Orta | ⭐⭐⭐⭐ | **6** |
| **Database** | ⭐⭐⭐ | 1 hafta | Orta | ⭐⭐⭐ | **7** |
| **Route Planning** | ⭐⭐⭐ | 2 hafta | Yüksek | ⭐⭐⭐ | **8** |

---

## 🗓️ ROADMAP

### Ay 1: Temel İyileştirmeler
- ✅ Hafta 1-2: **Custom dataset toplama + annotation**
- ✅ Hafta 3: **Fine-tuning + test**
- ✅ Hafta 4: **Sesli feedback + haptic**

### Ay 2: Performans & Stability
- ✅ Hafta 1: **OpenVINO fix**
- ✅ Hafta 2: **Unit tests + CI/CD**
- ✅ Hafta 3-4: **Offline mode implementation**

### Ay 3: Production
- ✅ Hafta 1-2: **Database + user analytics**
- ✅ Hafta 3: **Monitoring + logging**
- ✅ Hafta 4: **Beta testing + bug fixes**

---

## ✅ HEMEN BAŞLANAB İLECEKLER (Bu Hafta)

1. **Dataset Toplama Başlat** 📸
   - Telefon ile sokak fotoğrafları çek
   - 50-100 image ile başla
   - Roboflow hesabı oluştur

2. **Sesli Feedback Prototip** 🔊
   - Directional audio test et
   - Volume tabanlı mesafe feedback

3. **OpenVINO NumPy Fix** 🔧
   - `pip install numpy==2.2.6`
   - ONNX opset 17'ye çevir

---

## 💰 MONETIZATION ÖNERİLERİ

### Free Tier
- Temel object detection
- Depth estimation
- Sesli uyarılar

### Premium ($4.99/ay)
- **Offline mode** (internet gerektirmez)
- **Route planning** (engelsiz rotalar)
- **Gelişmiş analytics** (rota geçmişi)
- **Priority support**

---

## ✨ SONUÇ

**En Öncelikli 3**:
1. 🎯 **Custom Dataset + Fine-tuning** (accuracy %30 artacak)
2. 🔊 **Sesli Feedback İyileştirme** (UX çok artacak)
3. ⚡ **OpenVINO Fix** (hız 3-5x artacak)

**Hangi öneriyle başlamak istersin?** 🚀
