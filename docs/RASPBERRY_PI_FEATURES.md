# 🍓 GÖREN GÖZ MOBİL - RASPBERRY Pi 4 ÖZELLİK LİSTESİ VE YOLADIĞI

## 📊 MEVCUT PROJE ÖZELLİKLERİ (Şu an çalışıyor)

### ✅ **BACKEND (Python FastAPI)**
```
📍 Konum: C:\Users\admin\Desktop\goren_goz_mobil.app\backend\

✅ 1. MiDaS Derinlik Tahmini (depth_service.py)
   - PyTorch tabanlı monoküler derinlik tahmini
   - Model: DPT_Swin2_T_256 (~100MB)
   - CPU/GPU desteği
   - Çıktı: 0-3 metre derinlik haritası

✅ 2. YOLOv8 Nesne Tanıma (object_detection_service.py)
   - YOLOv8-Nano model (~6MB)
   - 80+ nesne sınıfı (COCO dataset)
   - Türkçe nesne isimleri
   - Confidence threshold: 50%
   - Bölgesel tespit (sol/orta/sağ)

✅ 3. Bölgesel Uyarı Sistemi (alert_service.py)
   - 3 bölge analizi (sol 33%, orta 33%, sağ 33%)
   - 5 seviye uyarı:
     * DANGER: < 0.5m (Kırmızı)
     * NEAR: 0.5-1.0m (Turuncu)
     * MEDIUM: 1.0-2.0m (Sarı)
     * FAR: 2.0-3.0m (Mavi)
     * SAFE: > 3.0m (Yeşil)

✅ 4. REST API (main.py + routers/analyze.py)
   - POST /api/analyze (görüntü analizi)
   - GET /health (sistem durumu)
   - GET /docs (API dokümantasyonu)
   - CORS desteği
   - Rate limiting (5 req/sec)

✅ 5. Görüntü İşleme (image_service.py)
   - Base64 decode
   - OpenCV formatına dönüştürme
   - Resizing (640x480 varsayılan)
```

### ✅ **MOBİL UYGULAMA (Flutter)**
```
📍 Konum: C:\Users\admin\Desktop\goren_goz_mobil.app\mobile_app\

✅ 1. Kamera Yakalama (camera_screen.dart)
   - Gerçek zamanlı frame yakalama
   - Ayarlanabilir FPS (1-10)
   - ResolutionPreset.high
   - Otomatik odaklama

✅ 2. TTS Sesli Yönlendirme (tts_service.dart)
   - Türkçe/İngilizce dil desteği
   - Konuşma hızı ayarlama (0.3-1.0x)
   - Bölgesel uyarılar:
     * "Sol tarafta tehlike! Sağa dönün!"
     * "Sağ tarafta yakın engel! Sola dönün."
     * "Önünüzde orta mesafede engel"
   - Nesne isimleri:
     * "Önünüzde sandalye var. 1.2 metre mesafede."

✅ 3. Titreşim Feedback (sound_service.dart)
   - 3x hızlı titreşim (100ms aralıklarla)
   - Tehlike seviyesine göre yoğunluk
   - Açma/kapama toggle

✅ 4. Sesli Alarm (sound_service.dart)
   - Tehlike anında alarm sesi
   - Ses seviyesi kontrolü (0-100%)
   - Bell-ringing ses dosyası

✅ 5. Bölgesel Görsel Göstergeler (regional_indicators.dart)
   - Sol/Orta/Sağ ok işaretleri (← ⚠️ →)
   - Renk kodlu uyarılar
   - Mesafe bilgisi

✅ 6. Nesne Listesi Widget (object_list.dart)
   - Tespit edilen nesnelerin listesi
   - Confidence yüzdesi
   - Türkçe/İngilizce isimler
   - Bölge bilgisi (sol/sağ/merkez)

✅ 7. Genişletilmiş Ayarlar (settings_screen.dart)
   - 🌐 Dil seçimi (TR/EN)
   - 📏 Mesafe eşikleri (0.3-5.0m)
   - 🔊 Ses/Titreşim/TTS açma/kapama
   - 🗣️ Konuşma hızı ayarı
   - 🎨 Tema (Koyu/Açık/Yüksek Kontrast)
   - 📷 FPS ayarı (1-10)
   - 🌐 API URL konfigürasyonu

✅ 8. İstatistik Paneli (info_panel.dart)
   - Anlık FPS
   - Min/Avg/Max mesafe
   - İşlem süresi (ms)

✅ 9. Tema Sistemi (main.dart)
   - Dark mode
   - Light mode
   - High contrast mode
   - Anlık tema değişimi
```

---

## 🍓 RASPBERRY Pi 4 İÇİN UYARLAMA PLANI

### **FAZ 1: TEMEL SİSTEM (1 Hafta)**

#### **Yapılacaklar:**

**1. Backend'i RPi 4'e Portlama**
```bash
✅ Görev: backend/ klasörünü RPi'ye kopyala
✅ Görev: Python 3.9+ kur (RPi OS 64-bit)
✅ Görev: Virtual environment oluştur
✅ Görev: requirements.txt'i yükle
✅ Görev: MiDaS ve YOLOv8 modellerini indir

Komutlar:
cd ~/goren_goz_mobil
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Model indirme (otomatik)
python backend/main.py  # İlk çalıştırmada modeller inecek
```

**2. Kamera Entegrasyonu (CSI/USB)**
```bash
✅ Görev: Raspberry Pi Camera Module 3 bağla (CSI port)
✅ Görev: Kamera testi yap
✅ Görev: Backend'de kamera kaynağını değiştir

Komutlar:
# Kamera aktif et
sudo raspi-config
# Interface Options → Camera → Enable

# Test
libcamera-hello --timeout 5000

# Python'da test
python3 -c "from picamera2 import Picamera2; p=Picamera2(); p.start(); print('OK')"
```

**3. Backend Kodu Düzenleme**
```python
✅ Görev: routers/analyze.py dosyasını düzenle
✅ Görev: Kamera frame'ini direkt picamera2'den al
✅ Görev: HTTP upload yerine local frame kullan

# YENİ DOSYA: backend/camera_capture.py
from picamera2 import Picamera2
import numpy as np

class CameraCapture:
    def __init__(self):
        self.picam = Picamera2()
        config = self.picam.create_preview_configuration(
            main={"size": (640, 480)}
        )
        self.picam.configure(config)
        self.picam.start()
    
    def get_frame(self):
        """Kameradan frame yakala"""
        return self.picam.capture_array()
    
    def stop(self):
        self.picam.stop()
```

**4. GPIO Titreşim Motoru Bağlantısı**
```bash
✅ Görev: Titreşim motoru + transistör sürücü bağla (GPIO18)
✅ Görev: Python GPIO kodu yaz

Bağlantı Şeması:
RPi GPIO18 → 1kΩ → BC547 Base
BC547 Collector → Vibration Motor (-)
BC547 Emitter → GND
Motor (+) → 3.3V (RPi Pin 1)

# YENİ DOSYA: backend/hardware/vibration.py
import RPi.GPIO as GPIO
import time

VIBRATION_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(VIBRATION_PIN, GPIO.OUT)

def vibrate_danger():
    """Tehlike titreşimi (3x hızlı)"""
    for _ in range(3):
        GPIO.output(VIBRATION_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(VIBRATION_PIN, GPIO.LOW)
        time.sleep(0.1)

def vibrate_warning():
    """Uyarı titreşimi (2x orta)"""
    for _ in range(2):
        GPIO.output(VIBRATION_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(VIBRATION_PIN, GPIO.LOW)
        time.sleep(0.2)
```

**5. TTS Ses Çıkışı (Hoparlör/Kulaklık)**
```bash
✅ Görev: 3.5mm kulaklık/hoparlör bağla veya Bluetooth hoparlör
✅ Görev: espeak-ng kur (Türkçe TTS)
✅ Görev: Python TTS kodu yaz

Komutlar:
sudo apt install espeak espeak-ng -y
pip install pyttsx3 py-espeak-ng

# Test
espeak-ng -v tr "Önünüzde tehlike var" --stdout | aplay

# YENİ DOSYA: backend/hardware/tts_speaker.py
import pyttsx3

class TTSSpeaker:
    def __init__(self, language='tr'):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Konuşma hızı
        voices = self.engine.getProperty('voices')
        # Türkçe ses seç
        for voice in voices:
            if 'turkish' in voice.name.lower() or 'tr' in voice.id:
                self.engine.setProperty('voice', voice.id)
                break
    
    def speak(self, text):
        """Sesli uyarı ver"""
        self.engine.say(text)
        self.engine.runAndWait()
    
    def speak_distance(self, distance, region='center'):
        """Mesafe uyarısı"""
        regions = {
            'left': 'Sol tarafta',
            'center': 'Önünüzde',
            'right': 'Sağ tarafta'
        }
        message = f"{regions[region]} {distance:.1f} metre mesafede engel var"
        self.speak(message)
```

---

### **FAZ 2: STANDALONE SİSTEM (2 Hafta)**

#### **Yapılacaklar:**

**6. Otomatik Başlatma (Systemd Service)**
```bash
✅ Görev: RPi açıldığında otomatik çalış
✅ Görev: Systemd service dosyası oluştur

# YENİ DOSYA: /etc/systemd/system/goren-goz.service
[Unit]
Description=Gören Göz Mobil AI Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/goren_goz_mobil
ExecStart=/home/pi/goren_goz_mobil/venv/bin/python backend/main_standalone.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# Servisi aktif et
sudo systemctl enable goren-goz
sudo systemctl start goren-goz
sudo systemctl status goren-goz
```

**7. Ana Standalone Script**
```python
# YENİ DOSYA: backend/main_standalone.py
"""
Gören Göz Raspberry Pi Standalone Modu
=======================================
Mobil uygulama gerekmeden direkt RPi üzerinde çalışır.
"""

import time
import cv2
from camera_capture import CameraCapture
from services.depth_service import get_depth_service
from services.object_detection_service import ObjectDetectionService
from hardware.vibration import vibrate_danger, vibrate_warning
from hardware.tts_speaker import TTSSpeaker

# Servisler
camera = CameraCapture()
depth_service = get_depth_service()
object_service = ObjectDetectionService()
tts = TTSSpeaker(language='tr')

print("🚀 Gören Göz Standalone Modu Başlatıldı")
tts.speak("Gören Göz sistemi aktif")

try:
    while True:
        # Frame yakala
        frame = camera.get_frame()
        
        # Derinlik tahmini
        depth_result = depth_service.estimate_depth(frame)
        
        # Bölgesel analiz
        h, w = depth_result.depth_map.shape
        left = depth_result.depth_map[:, :w//3].min()
        center = depth_result.depth_map[:, w//3:2*w//3].min()
        right = depth_result.depth_map[:, 2*w//3:].min()
        
        min_distance = min(left, center, right) * 3.0  # Normalize (0-3m)
        
        # Nesne tanıma
        detected_objects = object_service.detect(frame)
        
        # UYARI SİSTEMİ
        if min_distance < 0.5:
            # TEHLİKE!
            vibrate_danger()
            tts.speak("TEHLİKE! Çok yakın engel! Durun!")
        elif min_distance < 1.0:
            # UYARI
            vibrate_warning()
            region = 'left' if left < center and left < right else \
                     'right' if right < center else 'center'
            tts.speak_distance(min_distance, region)
        
        # Nesne bildirimi
        if detected_objects:
            obj = detected_objects[0]  # En önemli nesne
            tts.speak(f"{obj.name_tr} tespit edildi. {min_distance:.1f} metre mesafede")
        
        # Debug
        print(f"Sol:{left:.2f}m Orta:{center:.2f}m Sağ:{right:.2f}m | "
              f"Nesneler: {len(detected_objects)}")
        
        time.sleep(0.2)  # 5 FPS

except KeyboardInterrupt:
    print("\n❌ Program sonlandırıldı")
    camera.stop()
    tts.speak("Sistem kapatılıyor")
```

**8. Powerbank/Batarya Yönetimi**
```bash
✅ Görev: 20,000mAh powerbank bağla (USB-C)
✅ Görev: Batarya seviyesi izleme scripti

# Batarya okuma (UPS HAT varsa)
pip install ina219  # Akım sensörü

# YENİ DOSYA: backend/hardware/battery_monitor.py
import subprocess

def get_battery_level():
    """Powerbank voltajını oku"""
    # Not: Powerbank genelde voltaj bilgisi vermez
    # Sadece UPS HAT ile mümkün
    return None

def low_battery_warning(tts):
    """Düşük batarya uyarısı"""
    tts.speak("Batarya seviyesi düşük. Şarj edin.")
```

---

### **FAZ 3: AKILLI BASTON ENTEGRASYONU (3 Hafta)**

#### **Yapılacaklar:**

**9. Donanım Kasası Tasarımı**
```bash
✅ Görev: 3D model tasarla (Fusion 360 / Tinkercad)
✅ Görev: 3D print yaptır veya plastik kasa satın al
✅ Görev: Kamera lens deliği aç
✅ Görev: Powerbank, RPi, kamera montajı

Boyutlar:
- Kasa: 12cm x 8cm x 4cm
- Ağırlık: ~500g (RPi+Powerbank+Kamera)
- Malzeme: ABS plastik (su geçirmez)

Kasa İçi Yerleşim:
┌─────────────────────────┐
│   [Kamera]              │ ← Ön taraf
│                         │
│   [Raspberry Pi 4]      │
│                         │
│   [Powerbank 20Ah]      │
│                         │
│   [Titreşim Motoru]     │
└─────────────────────────┘
```

**10. Baston Montaj Aparatı**
```bash
✅ Görev: Kasa'yı bastona sabitleme aparatı tasarla
✅ Görev: Kamera açısı 30° aşağı (yere bakacak)
✅ Görev: Titreşim motoru baston sapına yerleştir

Montaj Noktaları:
- Kamera: Baston başından 20cm yukarı
- Kasa: Velcro bantla veya vida ile
- Hoparlör: Kullanıcının omzuna yakın (boyun askısı)
```

**11. Ergonomi İyileştirmeleri**
```bash
✅ Görev: Ağırlık dağılımını optimize et
✅ Görev: Kablo yönetimi (dahili kablolama)
✅ Görev: Suya dayanıklılık testi (IP54 seviyesi)
```

---

### **FAZ 4: GELİŞMİŞ ÖZELLIKLER (1 Ay)**

#### **Yapılacaklar:**

**12. Stereo Kamera Desteği (2x Camera Module)**
```bash
✅ Görev: 2. kamera modülü ekle
✅ Görev: Stereo kalibrasyonu yap
✅ Görev: Gerçek derinlik hesaplama (triangulation)

Avantajlar:
- Hassasiyet: ±2cm (monoküler ±20cm yerine)
- Daha hızlı (AI gerekmez)

# Stereo hesaplama
import cv2
stereo = cv2.StereoBM_create(numDisparities=16, blockSize=15)
disparity = stereo.compute(left_img, right_img)
depth = (baseline * focal_length) / disparity
```

**13. GPS/Konum Entegrasyonu**
```bash
✅ Görev: GPS modülü ekle (USB GPS veya Serial)
✅ Görev: Tehlikeli yerleri kaydet
✅ Görev: "Bu bölgede dikkatli olun" uyarısı

pip install gpsd-py3

# GPS okuma
from gps import gps, WATCH_ENABLE
session = gps(mode=WATCH_ENABLE)
lat, lon = session.next()['lat'], session.next()['lon']
```

**14. Google Coral USB Accelerator**
```bash
✅ Görev: Coral USB takıp YOLOv8'i hızlandır
✅ Görev: Edge TPU modeli derle

Performans artışı:
- YOLOv8: 15 FPS → 30 FPS
- Latency: 150ms → 50ms
- Maliyet: +$60
```

**15. Web Dashboard (Opsiyonel)**
```bash
✅ Görev: Flask/Streamlit web arayüzü
✅ Görev: Canlı kamera görüntüsü
✅ Görev: İstatistikler (günlük tespit sayısı)
✅ Görev: Ayar değiştirme (uzaktan)

Erişim: http://raspberrypi.local:5000
```

---

## 📋 ÖNCELIK SIRALADIĞI

### **🔥 HEMEN YAPIN (1 Hafta)**
1. ✅ Backend'i RPi'ye kopyala
2. ✅ Kamera bağla ve test et
3. ✅ Titreşim motoru bağla
4. ✅ TTS hoparlör bağla
5. ✅ Standalone script çalıştır

### **⚡ SONRAKI ADIMLAR (2 Hafta)**
6. ✅ Otomatik başlatma (systemd)
7. ✅ Powerbank entegrasyonu
8. ✅ İlk prototip testi

### **🚀 GELİŞMİŞ (1 Ay)**
9. ✅ Kasa tasarımı
10. ✅ Baston montajı
11. ✅ Stereo kamera (opsiyonel)
12. ✅ GPS modülü (opsiyonel)

---

## 🛒 ALIŞ VERİŞ LİSTESİ

### **Minimum Kurulum (~$150)**
| Ürün | Adet | Fiyat | Toplam |
|------|------|-------|--------|
| Raspberry Pi 4 (4GB) | 1 | $55 | $55 |
| Pi Camera Module 3 (Wide) | 1 | $25 | $25 |
| MicroSD 32GB (Class 10) | 1 | $10 | $10 |
| Powerbank 20,000mAh | 1 | $20 | $20 |
| Titreşim Motoru + BC547 | 1 | $3 | $3 |
| Mini Bluetooth Hoparlör | 1 | $15 | $15 |
| Jumper Kablolar | 1 set | $5 | $5 |
| Breadboard | 1 | $3 | $3 |
| Plastik Kasa | 1 | $10 | $10 |
| **TOPLAM** | | | **$146** |

### **Gelişmiş Kurulum (~$280)**
+ Google Coral USB Accelerator: $60
+ 2. Kamera (Stereo): $25
+ GPS Modülü: $20
+ UPS HAT (Batarya Yönetimi): $25
+ Suya Dayanıklı Kasa: $25
+ **TOPLAM: $301**

---

## 🎯 TEST SENARYOSU

### **Temel Test (Masa Üstü)**
```bash
1. RPi'yi başlat
2. Kamerayı bir sandalyeye tut
3. Bekle: "Önünüzde sandalye var. 1.2 metre mesafede"
4. Titreşimi hisset
5. Sandalyeyi yaklaştır (<0.5m)
6. Bekle: "TEHLİKE! Çok yakın engel! Durun!"
```

### **Gerçek Dünya Testi (Dışarıda)**
```bash
1. Bastona monte et
2. Sokakta yürü
3. Bir duvara yaklaş
4. Uyarı al: "Önünüzde duvar var"
5. Sola dön
6. Başka bir engele yaklaş
7. Uyarı al: "Sağ tarafta tehlike! Sola dönün!"
```

---

## 📞 DESTEK VE İLETİŞİM

**Sorular için:**
- GitHub Issues: [github.com/yourrepo/issues](https://github.com)
- E-posta: support@gorengoz.com
- Discord: discord.gg/gorengoz

**Raspberry Pi Topluluk:**
- RaspberryPi Forums: [raspberrypi.org/forums](https://raspberrypi.org/forums)
- RPi Discord: discord.gg/raspberrypi

---

## ✅ SON KONTROL LİSTESİ

**Donanım:**
- [ ] Raspberry Pi 4 (4GB) sipariş edildi
- [ ] Pi Camera Module 3 sipariş edildi
- [ ] Powerbank 20,000mAh sipariş edildi
- [ ] Titreşim motoru + transistör alındı
- [ ] Bluetooth hoparlör/kulaklık hazır
- [ ] Jumper kablolar + breadboard hazır

**Yazılım:**
- [ ] Raspberry Pi OS (64-bit) kuruldu
- [ ] Python 3.9+ yüklendi
- [ ] Backend kodu RPi'ye kopyalandı
- [ ] requirements.txt kuruldu
- [ ] Kamera testi başarılı
- [ ] GPIO testi başarılı
- [ ] TTS testi başarılı

**Entegrasyon:**
- [ ] main_standalone.py çalışıyor
- [ ] Derinlik tahmini çalışıyor
- [ ] Nesne tanıma çalışıyor
- [ ] Titreşim motoru çalışıyor
- [ ] TTS sesli uyarı çalışıyor
- [ ] Systemd service aktif

**Fiziksel:**
- [ ] Kasa tasarlandı/alındı
- [ ] Kamera monte edildi
- [ ] RPi monte edildi
- [ ] Powerbank monte edildi
- [ ] Baston montajı yapıldı
- [ ] Ergonomi testi yapıldı

---

## 🚀 HEMEN BAŞLAYALIM!

**İlk Adım:**
```bash
# Raspberry Pi siparişi ver
# https://thepihut.com/products/raspberry-pi-4-model-b
# veya https://www.raspberrypi.com/products/raspberry-pi-4-model-b/

# Gelene kadar backend kodunu hazırla:
cd C:\Users\admin\Desktop\goren_goz_mobil.app\backend
# Kodları gözden geçir, test et
```

**Kodu ben yazayım mı? Hangisinden başlayalım?** 🎯
1. `main_standalone.py` (Ana standalone script)
2. `camera_capture.py` (Picamera2 entegrasyonu)
3. `hardware/vibration.py` (Titreşim kontrolü)
4. `hardware/tts_speaker.py` (Sesli uyarı)
5. Hepsini! 🚀
