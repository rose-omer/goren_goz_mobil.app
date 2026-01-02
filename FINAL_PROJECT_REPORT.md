# 🎓 GÖREN GÖZ MOBİL - BİTİRME PROJESİ NİHAİ RAPORU

**Proje Adı:** Gören Göz Mobil  
**Konu:** Görme Engelliler İçin Yapay Zeka Destekli Gerçek Zamanlı Derinlik Algılama ve Nesne Tanıma Sistemi  
**Geliştirici:** [Adınız Soyadınız]  
**Tarih:** 2 Ocak 2026  
**Versiyon:** 1.0.0 (Release Candidate)  

---

## 📋 1. YÖNETİCİ ÖZETİ

**Gören Göz Mobil**, görme engelli bireylerin günlük yaşamlarında bağımsız hareket edebilmelerini sağlamak amacıyla geliştirilmiş, gelişmiş bir mobil navigasyon asistanıdır. Proje, mobil cihaz kamerasından alınan görüntüleri gerçek zamanlı olarak işleyerek çevredeki engelleri, nesneleri ve potansiyel tehlikeleri sesli ve titreşimli geri bildirimlerle kullanıcıya iletir.

Sistem, **Flutter** tabanlı bir mobil uygulama ve **FastAPI** tabanlı güçlü bir backend sunucusundan oluşur. Görüntü işleme için **MiDaS** (derinlik tahmini) ve **YOLOv11** (nesne tanıma) gibi son teknoloji yapay zeka modelleri kullanılmıştır. Ayrıca, **SmolVLM** entegrasyonu sayesinde kullanıcılar çevreleri hakkında doğal dilde sorular sorabilir ("Önümde ne var?", "Karşıya geçmek güvenli mi?" gibi).

---

## 🏗️ 2. SİSTEM MİMARİSİ VE TASARIM

Proje, **İstemci-Sunucu (Client-Server)** mimarisi üzerine inşa edilmiştir. Bu yaklaşım, mobil cihazın pil ve işlemci gücünü korurken, ağır yapay zeka işlemlerinin (inference) güçlü bir sunucuda gerçekleştirilmesine olanak tanır.

### 2.1 Veri Akış Diyagramı

```mermaid
graph TD
    User[Kullanıcı] -->|Kamera Görüntüsü| MobileApp[Mobil Uygulama (Flutter)]
    User -->|Sesli Komut| MobileApp
    
    MobileApp -->|HTTP POST /analyze| Backend[Backend Sunucusu (FastAPI)]
    
    subgraph "Backend İşleme Hattı"
        Backend -->|Görüntü| DepthService[Derinlik Servisi (MiDaS)]
        Backend -->|Görüntü| ObjectService[Nesne Tanıma (YOLOv11)]
        
        DepthService -->|Derinlik Haritası| AlertService[Uyarı Servisi]
        ObjectService -->|Nesne Listesi| AlertService
        
        AlertService -->|Analiz Sonucu| ResponseBuilder
    end
    
    ResponseBuilder -->|JSON Yanıt| MobileApp
    
    MobileApp -->|Sesli Uyarı (TTS)| User
    MobileApp -->|Titreşim| User
    MobileApp -->|Görsel Arayüz| User
```

### 2.2 Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **Mobil** | Flutter (Dart) | Cross-platform UI, Kamera, Sensörler |
| **Backend** | Python, FastAPI | REST API, İş Mantığı |
| **AI (Derinlik)** | MiDaS v2.1 Small | Monoküler Derinlik Tahmini |
| **AI (Nesne)** | YOLOv11-Nano | Gerçek Zamanlı Nesne Tespiti |
| **AI (VLM)** | SmolVLM-500M | Görsel Dil Modeli (Soru-Cevap) |
| **Hızlandırma** | OpenVINO | Intel CPU/GPU Optimizasyonu |

---

## 💻 3. DETAYLI KOD VE MODÜL ANALİZİ

### 3.1 Mobil Uygulama (Flutter)

Mobil uygulama, kullanıcı arayüzünü ve donanım etkileşimini yönetir.

#### `lib/main.dart` (Giriş Noktası)
- Uygulamanın yaşam döngüsünü başlatır.
- `SystemChrome` ile ekranı dikey moda kilitler (görme engelliler için tutuş kolaylığı).
- Tema (Karanlık/Aydınlık) ve global state yönetimini (`Provider`) başlatır.

#### `lib/screens/camera_screen.dart` (Ana Ekran)
- **Kamera Yönetimi:** `CameraController` ile cihaz kamerasından sürekli görüntü akışı (`ImageStream`) alır.
- **Frame Throttling:** Cihazı yormamak ve ağ trafiğini şişirmemek için her frame işlenmez. `_processFrame` fonksiyonu, sadece önceki işlem bittiyse ve belirli bir süre geçtiyse yeni frame gönderir.
- **Sesli Asistan:** Ekranın altındaki büyük mikrofon butonu, `GestureDetector` ile yönetilir. Tek dokunuşla dinlemeyi başlatır.
- **Uyarı Mantığı:** Backend'den gelen `AlertLevel` (DANGER, NEAR, SAFE) verisine göre ekran rengini değiştirir ve `SoundService`'i tetikler.

#### `lib/services/speech_recognition_service.dart` (Konuşma Tanıma)
- **Başlatma:** Uygulama açılışında `initialize()` metodu çalışır. Cihazın konuşma tanıma yeteneğini ve mikrofon iznini kontrol eder.
- **Dil Desteği:** Cihazın dil ayarlarını algılar, ancak varsayılan olarak Türkçe (`tr-TR`) veya İngilizce (`en-US`) kullanır.
- **Hata Toleransı:** Gürültülü ortamlarda veya anlaşılamayan komutlarda kullanıcıya sesli geri bildirim verir.

#### `lib/services/tts_service.dart` (Metin Okuma)
- **Öncelik Yönetimi:** Acil uyarılar (Çarpışma riski), normal bilgilendirmelerin (Nesne adı) önüne geçer.
- **Konfigürasyon:** Konuşma hızı (0.5) ve ses tonu (1.0) görme engellilerin rahat anlayabileceği şekilde optimize edilmiştir.

### 3.2 Backend Sistemi (Python/FastAPI)

Backend, sistemin "beyni" olarak çalışır.

#### `backend/main.py` (Sunucu Yapılandırması)
- **Lifespan Events:** Sunucu başlarken (`startup`) ağır AI modellerini belleğe yükler, böylece ilk istekte gecikme yaşanmaz.
- **Rate Limiting:** `slowapi` kütüphanesi ile IP başına saniyede 5 istek sınırı koyarak sunucuyu aşırı yükten korur.
- **CORS:** Mobil uygulamanın farklı ağlardan erişebilmesi için Cross-Origin Resource Sharing ayarlarını yönetir.

#### `backend/routers/analyze.py` (Analiz Endpoint'i)
- **İş Akışı:**
  1. Gelen resmi `decode_image` ile numpy dizisine çevirir.
  2. Paralel veya sıralı olarak `DepthService` ve `ObjectDetectionService`'i çağırır.
  3. Elde edilen verileri `AlertService`'e gönderir.
  4. Sonuçları `AnalyzeResponse` Pydantic modeline dönüştürüp JSON olarak döner.
- **Hata Yönetimi:** Görüntü bozuksa veya işlenemezse 400 Bad Request döner, ancak sunucuyu çökertmez.

#### `backend/services/depth_service.py` (Derinlik Tahmini)
- **Model Seçimi:** `config.yaml` dosyasındaki ayara göre PyTorch veya OpenVINO backend'ini seçer.
- **OpenVINO Optimizasyonu:** Intel işlemcilerde `.xml` formatındaki optimize edilmiş modeli kullanarak 3-5 kat performans artışı sağlar.
- **Çıktı:** Görüntüdeki her piksel için tahmini mesafeyi içeren bir "Depth Map" üretir.

#### `backend/services/object_detection_service.py` (Nesne Tanıma)
- **YOLOv11-Nano:** Hız ve doğruluk dengesi için en hafif YOLO modeli seçilmiştir.
- **Yerelleştirme:** `TURKISH_LABELS` sözlüğü ile "person" -> "insan", "car" -> "araba" gibi çeviriler yapılır.
- **Filtreleme:** Sadece %50 güven (confidence) üzerindeki tespitler dikkate alınır.

#### `backend/services/alert_service.py` (Uyarı Mantığı)
- **Bölgesel Analiz:** Görüntüyü dikey olarak 3 şeride böler: **Sol, Orta, Sağ**.
- **Tehlike Algoritması:**
  - Her bölge için ortalama ve minimum mesafe hesaplanır.
  - Eğer bir bölgedeki piksellerin %10'undan fazlası `min_distance` (0.5m) altındaysa **DANGER** alarmı verilir.
  - 0.5m - 1.2m arası **NEAR** (Yakın) uyarısıdır.
- **Öncelik:** Orta şeritteki engeller, yan şeritlere göre daha yüksek önceliklidir.

---

## ⚙️ 4. KONFİGÜRASYON VE BAĞIMLILIKLAR

### 4.1 `config/config.yaml`
Sistemin tüm ayarları bu dosyadan yönetilir:
```yaml
camera:
  width: 640
  height: 480
  fps: 30

depth_model:
  model_type: "MiDaS_small"
  use_openvino: true  # Performans için kritik

alerts:
  min_distance: 0.5       # 50cm altı tehlike
  warning_distance: 1.2   # 1.2m altı uyarı
  warning_area_threshold: 0.10 # %10 doluluk oranı
```

### 4.2 Bağımlılıklar
- **Backend (`requirements.txt`):** `fastapi`, `uvicorn`, `torch`, `ultralytics`, `openvino`, `opencv-python`.
- **Mobil (`pubspec.yaml`):** `camera`, `dio`, `flutter_tts`, `speech_to_text`, `permission_handler`, `provider`.

---

## 🧪 5. TEST VE KALİTE GÜVENCESİ

### 5.1 Test Stratejisi
- **Birim Testleri (`tests/`):** Her servis (Depth, Object, Alert) izole edilerek test edilmiştir.
- **Entegrasyon Testleri:** API endpoint'lerine gerçek görüntüler gönderilerek sistemin bütünü test edilmiştir.
- **Saha Testleri:** Farklı ışık koşullarında ve engelli parkurlarında denemeler yapılmıştır.

### 5.2 Hata Yönetimi
- **Graceful Degradation:** Eğer nesne tanıma servisi çökerse, sistem sadece derinlik bilgisiyle çalışmaya devam eder.
- **Loglama:** Tüm hatalar ve kritik olaylar `logs/` klasörüne ve konsola detaylı olarak yazılır.

---

## 🚀 6. SONUÇ VE GELECEK ÇALIŞMALAR

**Gören Göz Mobil**, akademik bir bitirme projesi olmanın ötesinde, gerçek hayatta kullanılabilecek potansiyele sahip bir prototiptir. Modern yapay zeka tekniklerini mobil teknolojilerle birleştirerek, görme engelli bireyler için erişilebilir bir çözüm sunmaktadır.

### Gelecek Planları
1.  **Offline Mod:** TensorFlow Lite kullanarak tüm işlemlerin internet olmadan cihazda yapılması.
2.  **GPS Navigasyon:** "Otobüs durağına 50 metre kaldı" gibi konum bazlı uyarılar.
3.  **Giyilebilir Teknoloji:** Sistemin akıllı gözlüklere entegre edilmesi.

---

*Bu rapor, projenin kaynak kodları ve teknik dokümantasyonu temel alınarak hazırlanmıştır.*
