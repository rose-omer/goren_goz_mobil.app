# 🚀 Başlangıç Rehberi - Adım Adım Kurulum

Bu rehber, uygulamayı sıfırdan çalıştırmak için gereken tüm adımları içerir.

---

## ADIM 1: llama.cpp İndir (CPU Versiyonu)

### 1.1 İndirme

1. [llama.cpp Releases](https://github.com/ggerganov/llama.cpp/releases) sayfasına git
2. En son release'i bul (örn: `b4295` gibi bir numara)
3. **CPU versiyonunu** indir:
   - Dosya adı: `llama-b4295-bin-win-avx2-x64.zip` (numara değişebilir)
   - ⚠️ CUDA/GPU versiyonunu ALMA, senin ekran kartın yok

### 1.2 Çıkartma

1. ZIP dosyasını `C:\llama.cpp\` klasörüne çıkart
2. Klasör yapısı şöyle olmalı:
   ```
   C:\llama.cpp\
   ├── bin\
   │   ├── llama-server.exe
   │   ├── llama-cli.exe
   │   └── ...
   └── README.md
   ```

---

## ADIM 2: SmolVLM Modelini İndir

### 2.1 Otomatik İndirme (Önerilen)

Terminal aç ve şunu çalıştır:

```powershell
cd C:\llama.cpp\bin
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF
```

- Model otomatik indirilecek (~500MB)
- İndirme yeri: `C:\Users\admin\.cache\llama.cpp\`
- İlk seferde 5-10 dakika sürebilir

Server başladığında şunu göreceksin:
```
llama server listening at http://localhost:8080
```

**Server çalışıyor demektir!** Şimdilik KAPAT (Ctrl+C).

---

## ADIM 3: Backend Dependencies Yükle

### 3.1 Terminal Aç

PowerShell veya CMD aç.

### 3.2 Proje Klasörüne Git

```powershell
cd C:\Users\admin\Desktop\goren_goz_mobil.app\backend
```

### 3.3 Virtual Environment Aktif Et (Varsa)

Eğer venv varsa:
```powershell
.\.venv\Scripts\activate
```

Yoksa devam et.

### 3.4 Yeni Paketleri Yükle

```powershell
pip install requests aiohttp
```

Hepsi yüklendiğinde:
```
Successfully installed requests-2.31.0 aiohttp-3.9.0
```

---

## ADIM 4: Mobil Uygulamayı Telefona Yükle

### 4.1 Telefonu Bilgisayara Bağla

- USB kabloyla bağla
- Telefonda **Developer Options** açık olmalı
- **USB Debugging** aktif olmalı

### 4.2 Flutter Proje Klasörüne Git

```powershell
cd C:\Users\admin\Desktop\goren_goz_mobil.app\mobile_app
```

### 4.3 Telefon Bağlantısını Kontrol Et

```powershell
flutter devices
```

Çıktıda telefonunu görmelisin:
```
SM G996B (mobile) • abc123 • android-arm64
```

### 4.4 Backend IP Adresini Ayarla

Bilgisayarının IP adresini öğren:

```powershell
ipconfig
```

IPv4 adresini not et (örn: `192.168.1.100`)

**constants.dart dosyasını düzenle:**

Dosya yolu: `mobile_app\lib\utils\constants.dart`

```dart
static const String apiUrl = 'http://192.168.1.100:8000'; // IP'ni buraya yaz
```

### 4.5 Uygulamayı Yükle ve Çalıştır

```powershell
flutter run --release
```

- `--release` daha hızlı çalışır
- İlk seferde 5-10 dakika sürebilir
- Uygulama telefona yüklenip açılacak

---

## ADIM 5: Her Şeyi Başlat (Sırayla)

### 5.1 Terminal 1: llama-server (VLM)

```powershell
cd C:\llama.cpp\bin
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF
```

**Çıktı:**
```
llama server listening at http://localhost:8080
```

✅ Bu terminal açık kalmalı!

---

### 5.2 Terminal 2: Backend

Yeni bir terminal aç:

```powershell
cd C:\Users\admin\Desktop\goren_goz_mobil.app\backend
.\.venv\Scripts\activate  # Varsa
python main.py
```

**Çıktı:**
```
✓ VLM server is ready
INFO: Uvicorn running on http://0.0.0.0:8000
```

✅ Bu terminal de açık kalmalı!

---

### 5.3 Telefonda Uygulamayı Kullan

1. **Kamera ekranı açılır**
2. **"Soru Sor" butonuna tıkla** (ortadaki extended buton)
3. **Bir soru seç:** Örn: "Önümde ne var?"
4. **Bekle** (3-5 saniye - CPU'da yavaş)
5. **Cevap gelir ve sesli okunur!** 🔊

---

## Özet Sırası

```
SIRA 1: llama-server başlat (Terminal 1)
SIRA 2: Backend başlat (Terminal 2)
SIRA 3: Telefonda uygulamayı kullan
```

---

## Sorun Giderme

### "VLM sunucusu çalışmıyor olabilir"

✅ **Çözüm:** llama-server çalışıyor mu kontrol et (Terminal 1)

Browser'da aç: `http://localhost:8080`

Bir UI görmelisin.

---

### "Bağlantı hatası"

✅ **Çözüm:** 

1. Backend çalışıyor mu? (Terminal 2)
2. Telefon ve PC aynı WiFi'de mi?
3. `constants.dart` dosyasında IP doğru mu?

Test için browser'da aç: `http://192.168.1.100:8000/health`

---

### Çok Yavaş (5+ saniye)

✅ **Normal:** CPU'da SmolVLM yavaştır. Ekran kartı olsaydı 10x hızlı olurdu.

**Beklenen süre:**
- CPU: 3-5 saniye
- GPU: 0.5-1 saniye

---

## İlk Test

Backend başlattıktan sonra bu komutu çalıştır:

```powershell
curl http://localhost:8000/health
```

**Beklenen yanıt:**
```json
{
  "status": "healthy",
  "vlm": {
    "server_ready": true
  }
}
```

`"server_ready": true` ise her şey hazır! 🎉

---

## Notlar

- ⚠️ llama-server ve backend **her zaman** çalışmalı
- 💡 Bilgisayarı kapatırsan, tekrar ADIM 5'i yap
- 🔇 İlk çalıştırmada model yüklenir, biraz uzun sürer (normal)
- 📱 Telefon ve PC **aynı WiFi**'de olmalı

---

**Hazırsın!** Sorular olursa sor. 🚀
