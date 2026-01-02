# 🧑‍💻 Gören Göz Mobil - Kapsamlı Kod ve Sistem Analizi

Bu dosya, projenin tüm ana kod bloklarını, modüllerini ve işlevlerini ayrıntılı şekilde açıklayan, her satırına ve mimarisine hakim bir teknik rapordur. Kodun işleyişi, algoritmalar, veri akışı ve mühendislik kararları detaylı olarak anlatılmıştır.

---

## 1. Mobil Uygulama (Flutter/Dart)

### 1.1 main.dart
- **Amaç:** Uygulamanın giriş noktasıdır. Tema, yönlendirme, sistem ayarları ve ana widget ağacı burada başlatılır.
- **Kod Akışı:**
  - `main()` fonksiyonu ile Flutter binding başlatılır, ekran dikey moda sabitlenir, sistem UI ayarları yapılır.
  - `GorenGozApp` widget'ı başlatılır. Bu widget, tema ve erişilebilirlik ayarlarını yükler.
  - `MaterialApp` ile rotalar (`/splash`, `/camera`, `/settings`) tanımlanır.
- **Önemli Noktalar:**
  - Uygulama açılışında kullanıcı tercihleri (tema, kontrast) `SharedPreferences` ile yüklenir.
  - Tüm servisler (API, TTS, Sound) Provider ile yönetilir.

### 1.2 screens/splash_screen.dart
- **Amaç:** Uygulama açılışında kamera ve mikrofon izinlerini kontrol eder.
- **Kod Akışı:**
  - `initState()` içinde `_initialize()` çağrılır.
  - Kamera ve mikrofon izinleri istenir. İzinler tamamsa `/camera` ekranına yönlendirilir.
  - Eksik izin varsa kullanıcıya uyarı dialogu gösterilir.
- **Kritik Kod:**
  - `Permission.camera.request()`, `Permission.microphone.request()`
  - `Navigator.of(context).pushReplacementNamed('/camera')`

### 1.3 screens/camera_screen.dart
- **Amaç:** Kameradan alınan görüntüyü işler, API'ye gönderir, sonuçları ekranda ve sesli olarak sunar.
- **Kod Akışı:**
  - Kamera başlatılır, frame'ler belirli aralıklarla alınır.
  - Her frame, `ApiService` ile backend'e gönderilir.
  - Gelen yanıt ile uyarı overlay'i, nesne listesi ve derinlik haritası güncellenir.
  - Sesli asistan için konuşma tanıma başlatılır, sonuç TTS ile okunur.
- **Kritik Kod:**
  - `CameraController` ile kamera yönetimi.
  - `_speechRecognitionService.startListening()` ile konuşma başlatma.
  - `ObjectList`, `AlertOverlay` widget'ları ile görsel çıktı.

### 1.4 services/speech_recognition_service.dart
- **Amaç:** Konuşma tanıma işlemlerini yönetir.
- **Kod Akışı:**
  - `initialize()`: Tek seferlik başlatma, cihazda destek kontrolü, locale listesi.
  - `startListening()`: Belirtilen dilde konuşma başlatır, sonuçları callback ile döner.
  - `stopListening()`, `cancel()`: Dinlemeyi durdurur veya iptal eder.
- **Kritik Kod:**
  - `stt.SpeechToText().initialize()`
  - `listenFor: Duration(seconds: 60)`, `localeId: locale`
  - Hata ve durumlar `AppLogger` ile loglanır.

### 1.5 services/tts_service.dart & utils/speech_helper.dart
- **Amaç:** TTS ile sesli yanıt ve uyarı üretir.
- **Kod Akışı:**
  - `FlutterTts` ile Türkçe dil, hız, ton ayarlanır.
  - `speak(text)`, `stop()` fonksiyonları ile sesli çıktı yönetilir.
- **Kritik Kod:**
  - `await _tts.setLanguage('tr-TR')`, `await _tts.speak(text)`

### 1.6 services/api_service.dart
- **Amaç:** Backend API ile iletişim kurar.
- **Kod Akışı:**
  - Dio ile HTTP istekleri yapılır, yeniden deneme ve timeout yönetimi vardır.
  - Yanıtlar `ApiResponse` modeline parse edilir.
- **Kritik Kod:**
  - `Dio(BaseOptions(...))`, `RetryInterceptor`

### 1.7 services/sound_service.dart
- **Amaç:** Uyarı sesleri ve titreşim yönetimi.
- **Kod Akışı:**
  - `AudioPlayer` ile ses dosyası çalınır.
  - Sadece tehlike seviyesinde sesli uyarı verir, cooldown ile spam engellenir.
- **Kritik Kod:**
  - `await _player.play(AssetSource('sounds/beep.mp3'))`

### 1.8 widgets/alert_overlay.dart & object_list.dart
- **Amaç:** Ekranda uyarı ve tespit edilen nesneleri gösterir.
- **Kod Akışı:**
  - Uyarı seviyesi ve nesne listesi parametre olarak alınır, uygun renk ve ikonlarla ekrana basılır.

### 1.9 utils/logger.dart
- **Amaç:** Tüm servislerde kullanılan merkezi loglama aracı.
- **Kod Akışı:**
  - `AppLogger.info()`, `AppLogger.error()` ile debug çıktısı alınır.

---

## 2. Backend (FastAPI/Python)

### 2.1 main.py
- **Amaç:** FastAPI uygulamasının ana dosyası.
- **Kod Akışı:**
  - Ayarlar ve loglama başlatılır.
  - CORS, rate limit, lifespan eventleri tanımlanır.
  - `/api/analyze` ve `/health` endpointleri eklenir.
- **Kritik Kod:**
  - `@asynccontextmanager lifespan(app)`
  - `app.include_router(analyze.router, ...)`

### 2.2 routers/analyze.py
- **Amaç:** `/api/analyze` endpointinin iş mantığı.
- **Kod Akışı:**
  - Görüntü dosyası alınır, derinlik ve nesne tespiti servislerine gönderilir.
  - Sonuçlar `AnalyzeResponse` modeli ile döner.
- **Kritik Kod:**
  - `@router.post('/analyze', ...)`
  - `get_depth_service().predict(image)`
  - `get_object_detection_service().detect(image)`

### 2.3 services/object_detection_service.py
- **Amaç:** YOLOv11-Nano ile nesne tespiti.
- **Kod Akışı:**
  - Ultralytics YOLO modeli yüklenir.
  - Görüntüdeki nesneler tespit edilir, Türkçe/İngilizce etiketlenir, yön ve öncelik atanır.
- **Kritik Kod:**
  - `YOLO(model_path).predict(image)`
  - `TURKISH_LABELS` ile etiket çevirisi

### 2.4 services/depth_service.py
- **Amaç:** MiDaS/OpenVINO ile derinlik tahmini.
- **Kod Akışı:**
  - Model ve cihaz seçimi yapılır (OpenVINO varsa hızlandırma).
  - Görüntüden derinlik haritası çıkarılır.
- **Kritik Kod:**
  - `self.use_openvino`, `self.model_type`, `predict(image)`

### 2.5 services/alert_service.py
- **Amaç:** Derinlik haritası analiz edilerek çarpışma riski ve uyarı seviyesi belirlenir.
- **Kod Akışı:**
  - Derinlik haritası bölgesel olarak analiz edilir (sol/orta/sağ).
  - Minimum mesafe, uyarı yüzdesi ve seviye hesaplanır.
- **Kritik Kod:**
  - `analyze_depth(depth_map)`

### 2.6 models/response.py
- **Amaç:** API yanıt modelleri (Pydantic).
- **Kod Akışı:**
  - Mesafe, uyarı, nesne, bölgesel analiz gibi tüm veri yapıları burada tanımlı.

---

## 3. Testler ve Kalite
- `tests/` klasöründe derinlik, nesne tespiti ve sistem testleri mevcut.
- Kodun büyük kısmı loglama ve hata yönetimi ile donatılmış.

---

## 4. Dokümantasyon ve Teknik Raporlar
- `README.md`: Proje genel tanımı, kurulum, kullanım.
- `PROJECT_REPORT.md`: Bitirme projesi için kapsamlı özet ve teknik detaylar.
- `docs/INDEX.md`: Tüm dokümantasyonun ana dizini.
- `docs/NESNE_TANIMA_GELIŞTIRMELER.md`: Nesne tespiti ve takip algoritmalarının evrimi.
- `docs/performans_optimizasyonu.md`: Performans darboğazları ve optimizasyon önerileri.
- `docs/hata_analizi.md`: Tespit edilen tüm hata ve iyileştirme önerileri.
- `docs/duzeltme_ozeti.md`: Yapılan düzeltmelerin detaylı özeti.

---

## 5. Güçlü Yönler ve Mühendislik Kararları
- **Modüler ve ölçeklenebilir mimari** (hem mobil hem backend).
- **Gerçek zamanlı derinlik ve nesne tespiti** (mobil cihazda hızlı ve optimize).
- **Erişilebilirlik**: Sesli komut, TTS, sade arayüz.
- **Performans**: OpenVINO, frame skip, gereksiz servislerin kaldırılması.
- **Hata yönetimi ve loglama**: Tüm kritik işlemler loglanıyor, hata analizi ve düzeltme döngüsü mevcut.
- **Dokümantasyon**: Her modül ve algoritma için detaylı Markdown dosyaları.

---

## 6. Sonuç ve Öneriler
- Proje, görme engelliler için gerçek zamanlı, güvenli ve erişilebilir bir navigasyon çözümü sunuyor.
- Kod tabanı, modern yazılım geliştirme standartlarına uygun, test edilebilir ve sürdürülebilir.
- Gelecekte, model güncellemeleri, yeni sensör entegrasyonları ve daha fazla dil desteği eklenebilir.

---

> Her dosya ve modül için daha fazla teknik detay veya kod örneği isterseniz, belirli dosya/servis/algoritma adını belirtmeniz yeterli.

Bu analiz, projenizin teknik derinliğini ve mühendislik kalitesini akademik raporunuzda güçlü şekilde gösterecektir.
