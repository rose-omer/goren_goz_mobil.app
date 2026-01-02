# 📘 Gören Göz Mobil - Kapsamlı Teknik Proje Raporu

**Tarih:** 2 Ocak 2026  
**Versiyon:** 1.0.0  
**Durum:** Final Release Candidate  

---

## 1. 🎯 Yönetici Özeti

**Gören Göz Mobil**, görme engelli bireylerin bağımsız hareket kabiliyetini artırmak amacıyla geliştirilmiş, yapay zeka destekli bir mobil navigasyon asistanıdır. Proje, mobil cihaz kamerasından alınan görüntüleri gerçek zamanlı olarak işleyerek çevredeki engelleri, nesneleri ve tehlikeleri sesli olarak kullanıcıya bildirir.

### Temel Özellikler
- **Gerçek Zamanlı Derinlik Algılama:** MiDaS modeli ile monoküler derinlik tahmini.
- **Nesne Tanıma:** YOLOv11-Nano ile 80+ nesne sınıfının tespiti.
- **Sesli Asistan:** Doğal dil ile soru sorma ve sesli yanıt alma (VLM entegrasyonu).
- **Çarpışma Uyarısı:** Tehlikeli yakınlıktaki engeller için sesli ve titreşimli uyarı.
- **Tam Türkçe Desteği:** Arayüz ve sesli geri bildirimler tamamen Türkçe.

### Teknoloji Yığını
- **Mobil:** Flutter (Dart), Provider, Camera, TTS, Speech-to-Text.
- **Backend:** Python, FastAPI, PyTorch, OpenVINO, Ultralytics YOLO.
- **AI Modelleri:** MiDaS v2.1 Small, YOLOv11n, SmolVLM (opsiyonel).

---

## 2. 🏗️ Sistem Mimarisi

Sistem, istemci-sunucu (Client-Server) mimarisi üzerine kurulmuştur. Mobil uygulama "ince istemci" (thin client) olarak çalışır ve ağır işlem yükünü (AI inference) güçlü bir backend sunucusuna devreder.

### Veri Akış Şeması

```mermaid
graph TD
    A[Mobil Kamera] -->|Frame (JPEG)| B(API Service)
    B -->|HTTP POST /analyze| C[FastAPI Backend]
    
    subgraph Backend Processing
        C --> D{Router}
        D -->|Image| E[Depth Service (MiDaS)]
        D -->|Image| F[Object Detection (YOLOv11)]
        E -->|Depth Map| G[Alert Service]
        F -->|Objects| G
        G -->|Alerts & Stats| H[Response Builder]
    end
    
    H -->|JSON Response| B
    B --> I[UI Update]
    B --> J[TTS Service]
    B --> K[Sound Service]
```

---

## 3. ⚙️ Konfigürasyon ve Bağımlılıklar

### 3.1 Backend Konfigürasyonu (`config/config.yaml`)
Sistemin beyni `config.yaml` dosyasıdır. Tüm kritik parametreler buradan yönetilir:

- **Kamera:** 640x480 çözünürlük, 30 FPS hedefi.
- **Derinlik Modeli:** `MiDaS_small` (hız/performans dengesi için), OpenVINO aktif (`use_openvino: true`).
- **Uyarı Sistemi:** 
  - `min_distance: 0.5m` (Tehlike sınırı)
  - `warning_distance: 1.2m` (Uyarı sınırı)
  - `warning_area_threshold: 0.10` (%10 alan kaplama eşiği)
- **Performans:** `skip_frames: 2` (Her 3 frame'den 1'i işlenir, CPU yükünü azaltır).

### 3.2 Mobil Bağımlılıklar (`pubspec.yaml`)
Flutter tarafında kullanılan kritik paketler:
- `camera`: Kamera donanımına erişim.
- `dio`: Gelişmiş HTTP istemcisi (retry logic ile).
- `flutter_tts`: Metin okuma motoru.
- `speech_to_text`: Sesli komut algılama.
- `permission_handler`: Android/iOS izin yönetimi.
- `audioplayers`: Uyarı sesleri (beep) için.

### 3.3 Backend Bağımlılıkları (`requirements.txt`)
Python tarafındaki güç üniteleri:
- `fastapi`, `uvicorn`: Yüksek performanslı web sunucusu.
- `torch`, `torchvision`: Derin öğrenme altyapısı.
- `ultralytics`: YOLOv11 implementasyonu.
- `openvino`: Intel işlemcilerde AI hızlandırma.
- `opencv-python`: Görüntü işleme.

---

## 4. 🧠 Backend Kod Analizi (Derinlemesine)

### 4.1 `backend/main.py`
Uygulamanın giriş kapısıdır.
- **Lifespan Manager:** Uygulama başlarken (`startup`) modelleri belleğe yükler, kapanırken (`shutdown`) kaynakları temizler.
- **Middleware:** CORS ayarları (tüm originlere izin verilir) ve Rate Limiting (saniyede 5 istek) burada yapılandırılır.

### 4.2 `backend/routers/analyze.py`
İş mantığının orkestra şefidir.
- **Akış:**
  1. İstemciden gelen resmi okur.
  2. `DepthService` ile derinlik haritasını çıkarır.
  3. `ObjectDetectionService` ile nesneleri bulur.
  4. `AlertService` ile bu iki veriyi birleştirip tehlike analizi yapar.
  5. Sonuçları `AnalyzeResponse` modeline paketleyip döner.
- **Önemli Detay:** Hata yönetimi (try-except blokları) ile bir servis çökse bile diğerlerinin çalışmaya devam etmesi sağlanır (Graceful Degradation).

### 4.3 `backend/services/depth_service.py`
Derinlik algılama motoru.
- **Model Yükleme:** PyTorch veya OpenVINO backend'ini dinamik olarak seçer. OpenVINO varsa `.xml` modelini yükler, yoksa `.pt` modelini kullanır.
- **Optimizasyon:** Görüntüyü modele girmeden önce yeniden boyutlandırır (384x384) ve normalize eder.
- **Çıktı:** Her pikselin kameraya olan tahmini mesafesini içeren bir matris (Depth Map) üretir.

### 4.4 `backend/services/object_detection_service.py`
Nesne tanıma motoru.
- **YOLOv11:** En güncel YOLO mimarisini kullanır. "Nano" versiyonu seçilerek hız önceliklendirilmiştir.
- **Yerelleştirme:** `TURKISH_LABELS` sözlüğü ile 80 COCO sınıfını (person -> insan, car -> araba) Türkçe'ye çevirir.
- **Önceliklendirme:** Her nesneye bir "çarpışma önceliği" atanır. Örneğin, "araba" ve "insan" yüksek öncelikli iken, "saksı" düşük önceliklidir.

### 4.5 `backend/services/alert_service.py`
Karar mekanizması.
- **Bölgesel Analiz:** Görüntüyü dikey olarak 3 şeride böler (Sol, Orta, Sağ).
- **Tehlike Hesabı:** Her şerit için ortalama derinliği hesaplar. Eğer bir şeritteki nesne `min_distance`'dan yakınsa `DANGER` alarmı verir.
- **Histerezis:** Uyarıların sürekli yanıp sönmesini engellemek için eşik değerlerinde tolerans payı bırakır.

---

## 5. 📱 Mobil Uygulama Kod Analizi (Derinlemesine)

### 5.1 `lib/main.dart`
Uygulamanın iskeleti.
- **Başlatma:** `WidgetsFlutterBinding.ensureInitialized()` ile native köprüleri kurar.
- **Oryantasyon:** Ekranı dikey moda (`portraitUp`) kilitler.
- **Tema:** Kullanıcı tercihine göre Karanlık/Aydınlık mod seçimi yapar.

### 5.2 `lib/screens/camera_screen.dart`
Kullanıcının gördüğü ana ekran.
- **Kamera Döngüsü:** `startImageStream` ile kameradan sürekli görüntü akışı alır.
- **Frame Kontrolü:** Her frame'i işlemek yerine, cihazı yormamak için belirli aralıklarla (throttle) backend'e gönderir.
- **Sesli Asistan Butonu:** Ekranın altına yerleştirilen büyük mikrofon butonu, `GestureDetector` ile dokunma olaylarını yakalar ve `SpeechRecognitionService`'i tetikler.

### 5.3 `lib/services/speech_recognition_service.dart`
Sesli komut sistemi.
- **Başlatma (`initialize`):** Uygulama açıldığında bir kez çalışır, mikrofon iznini ve cihaz desteğini kontrol eder.
- **Dinleme (`startListening`):** Kullanıcı butona bastığında aktifleşir. Ortam gürültüsünü filtreleyerek konuşmayı metne çevirir.
- **Hata Yönetimi:** "Anlaşılamadı" veya "Mikrofon hatası" gibi durumları yakalar ve loglar.

### 5.4 `lib/services/tts_service.dart`
Uygulamanın sesi.
- **Konfigürasyon:** Türkçe dil paketi (`tr-TR`), konuşma hızı (0.5) ve ses tonu (1.0) ayarlanır.
- **Kuyruk Yönetimi:** Üst üste gelen konuşma isteklerini sıraya koyar veya öncelikli olan (örn. tehlike uyarısı) için diğerini keser.

### 5.5 `lib/services/api_service.dart`
İletişim katmanı.
- **Retry Logic:** Ağ kopmalarına karşı dayanıklılık için `RetryInterceptor` kullanır. İstek başarısız olursa artan aralıklarla (500ms, 1s, 2s) tekrar dener.
- **Timeout:** 5 saniye içinde yanıt gelmezse isteği iptal eder ve kullanıcıyı bekletmez.

---

## 6. 📚 Dokümantasyon İncelemesi (`docs/`)

Proje, kodun yanı sıra kapsamlı bir dokümantasyon setine sahiptir:
- **`BASLANGIC_REHBERI.md`:** Yeni geliştiriciler için adım adım kurulum (Python venv, Flutter doctor vb.).
- **`hata_analizi.md`:** Geliştirme sürecinde karşılaşılan 8 kritik hata ve çözümleri.
- **`duzeltme_ozeti.md`:** Yapılan son 11 kritik düzeltmenin (bug fix) kaydı.
- **`performans_optimizasyonu.md`:** Sistem darboğazları ve çözüm stratejileri (örn. Ground Analysis servisinin kaldırılması).
- **`NESNE_TANIMA_GELIŞTIRMELER.md`:** Nesne takibi (tracking) ve kararlılık (stability) algoritmalarının detayları.

---

## 7. 🧪 Test ve Kalite Güvencesi

### Test Kapsamı
- **Birim Testleri (`tests/`):**
  - `test_depth_v2.py`: Derinlik servisinin farklı çözünürlüklerdeki başarısını ölçer.
  - `test_zoedepth.py`: Alternatif derinlik modellerini kıyaslar.
  - `test_system.py`: Uçtan uca (E2E) sistem testi yapar.

### Kalite Metrikleri
- **Loglama:** `utils/logger.dart` ve Python `logging` modülü ile tüm kritik işlemler kayıt altına alınır.
- **Hata Yakalama:** Hem mobil hem backend tarafında global exception handler'lar mevcuttur.

---

## 8. 🚀 Gelecek Yol Haritası

1. **Offline Mod:** Derinlik tahmininin tamamen mobil cihaz üzerinde (TensorFlow Lite ile) yapılması.
2. **GPS Entegrasyonu:** Konum bazlı uyarılar ("Otobüs durağına yaklaştınız").
3. **Çoklu Dil:** İngilizce ve Arapça dil desteğinin eklenmesi.
4. **Akıllı Gözlük:** Projenin giyilebilir teknolojilere (örn. Ray-Ban Meta) uyarlanması.

---

**Rapor Sonu**  
*Bu rapor, projenin kaynak kodları, konfigürasyon dosyaları ve dokümantasyonu incelenerek otomatik olarak oluşturulmuştur.*
