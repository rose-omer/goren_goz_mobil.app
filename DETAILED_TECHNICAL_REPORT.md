# 📚 Gören Göz Mobil - Detaylı Teknik Analiz ve Proje Raporu

## 1. Genel Mimari ve Katmanlar

- **Mobil Uygulama (Flutter/Dart):**
  - Kamera ile gerçek zamanlı görüntü alır.
  - Görüntüyü backend API'ye gönderir, derinlik ve nesne tespiti sonuçlarını işler.
  - Sesli uyarı, TTS, konuşma tanıma ve erişilebilirlik özellikleri sunar.
- **Backend (FastAPI/Python):**
  - REST API ile mobil istemciden gelen görüntüleri işler.
  - MiDaS/OpenVINO ile derinlik tahmini, YOLOv11 ile nesne tespiti yapar.
  - Uyarı ve analiz sonuçlarını JSON olarak döner.
- **AI Modelleri:**
  - MiDaS (derinlik), YOLOv11 (nesne), OpenVINO (hız optimizasyonu).
- **Dokümantasyon:**
  - Her modül ve özellik için kapsamlı Markdown dosyaları.

---

## 2. Mobil Uygulama (Flutter) - Ana Kod Dosyaları

### `main.dart`
- Uygulamanın giriş noktası.
- Tema, yönlendirme, sistem ayarları ve ana widget ağacı burada başlatılır.
- `SplashScreen`, `CameraScreen`, `SettingsScreen` gibi ekranlar tanımlı.

### `screens/splash_screen.dart`
- Uygulama açılışında kamera ve mikrofon izinlerini kontrol eder.
- İzinler alınmazsa kullanıcıya uyarı gösterir.
- Başarılıysa ana kameraya yönlendirir.

### `screens/camera_screen.dart`
- Kameradan alınan görüntüyü işler ve API'ye gönderir.
- Gerçek zamanlı uyarı, nesne listesi, derinlik haritası ve sesli asistan özelliklerini yönetir.
- Konuşma tanıma ve TTS entegrasyonu ile erişilebilirlik sağlar.

### `services/speech_recognition_service.dart`
- `speech_to_text` paketi ile konuşma tanıma işlemlerini yönetir.
- Tek seferlik başlatma, çoklu dil desteği, hata ve durum loglaması içerir.
- `startListening`, `stopListening`, `cancel` gibi fonksiyonlar ile konuşma akışını kontrol eder.

### `services/tts_service.dart` ve `utils/speech_helper.dart`
- `flutter_tts` ile Türkçe sesli yanıt ve uyarı üretir.
- Hız, ton, dil ayarları ve hata yönetimi içerir.

### `services/api_service.dart`
- Dio ile backend API'ye istek atar.
- Yeniden deneme, hata yönetimi ve loglama içerir.

### `services/sound_service.dart`
- Uyarı sesleri ve titreşim yönetimi.
- Sadece tehlike seviyesinde sesli uyarı verir.

### `widgets/alert_overlay.dart`, `object_list.dart`
- Ekranda uyarı ve tespit edilen nesneleri gösteren özel widget'lar.

### `utils/logger.dart`
- Tüm servislerde kullanılan merkezi loglama aracı.

---

## 3. Backend (FastAPI/Python) - Ana Kod Dosyaları

### `backend/main.py`
- FastAPI uygulamasının ana dosyası.
- CORS, rate limit, logging, yaşam döngüsü yönetimi.
- `/api/analyze` (görüntü analizi), `/health` (sağlık kontrolü) endpointleri.

### `backend/routers/analyze.py`
- `/api/analyze` endpointinin tüm iş mantığı burada.
- Görüntü alır, derinlik ve nesne tespiti servislerini çağırır, uyarı ve analiz sonuçlarını döner.
- Hatalı field mapping ve mesafe entegrasyonu gibi geçmişte tespit edilen sorunlar düzeltilmiş.

### `backend/services/object_detection_service.py`
- YOLOv11-Nano ile nesne tespiti.
- Türkçe/İngilizce etiketler, yönsel bilgi, hız ve doğruluk optimizasyonları.
- Ultralytics paketi ile entegre.

### `backend/services/depth_service.py`
- MiDaS/OpenVINO ile derinlik tahmini.
- Intel donanımda 3-5x hız artışı.
- Model ve cihaz seçimi, hata yönetimi.

### `backend/services/alert_service.py`
- Derinlik haritası analiz edilerek çarpışma riski ve uyarı seviyeleri belirlenir.
- Bölgesel (sol/orta/sağ) analiz ve detaylı istatistikler.

### `backend/models/response.py`
- Pydantic ile API response modelleri.
- Mesafe, uyarı, nesne, bölgesel analiz gibi tüm veri yapıları burada tanımlı.

---

## 4. Testler ve Kalite

- `tests/` klasöründe derinlik, nesne tespiti ve sistem testleri mevcut.
- Hata analizi ve düzeltme özetleri için `docs/hata_analizi.md`, `docs/duzeltme_ozeti.md` dosyaları detaylı.
- Kodun büyük kısmı loglama ve hata yönetimi ile donatılmış.

---

## 5. Dokümantasyon ve Teknik Raporlar

- `README.md`: Proje genel tanımı, kurulum, kullanım.
- `PROJECT_REPORT.md`: Bitirme projesi için kapsamlı özet ve teknik detaylar.
- `docs/INDEX.md`: Tüm dokümantasyonun ana dizini.
- `docs/NESNE_TANIMA_GELIŞTIRMELER.md`: Nesne tespiti ve takip algoritmalarının evrimi.
- `docs/performans_optimizasyonu.md`: Performans darboğazları ve optimizasyon önerileri.
- `docs/hata_analizi.md`: Tespit edilen tüm hata ve iyileştirme önerileri.
- `docs/duzeltme_ozeti.md`: Yapılan düzeltmelerin detaylı özeti.

---

## 6. Teknik Güçlü Yönler ve İyileştirmeler

- **Modüler ve ölçeklenebilir mimari** (hem mobil hem backend).
- **Gerçek zamanlı derinlik ve nesne tespiti** (mobil cihazda hızlı ve optimize).
- **Erişilebilirlik**: Sesli komut, TTS, sade arayüz.
- **Performans**: OpenVINO, frame skip, gereksiz servislerin kaldırılması.
- **Hata yönetimi ve loglama**: Tüm kritik işlemler loglanıyor, hata analizi ve düzeltme döngüsü mevcut.
- **Dokümantasyon**: Her modül ve algoritma için detaylı Markdown dosyaları.

---

## 7. Sonuç ve Öneriler

- Proje, görme engelliler için gerçek zamanlı, güvenli ve erişilebilir bir navigasyon çözümü sunuyor.
- Kod tabanı, modern yazılım geliştirme standartlarına uygun, test edilebilir ve sürdürülebilir.
- Gelecekte, model güncellemeleri, yeni sensör entegrasyonları ve daha fazla dil desteği eklenebilir.

---

> Ek: Her dosya ve modül için daha fazla teknik detay veya kod örneği isterseniz, belirli dosya/servis/algoritma adını belirtmeniz yeterli.

Bu analiz, projenizin teknik derinliğini ve mühendislik kalitesini akademik raporunuzda güçlü şekilde gösterecektir. İsterseniz bu raporu PDF/Word olarak da dışa aktarabilirim.
