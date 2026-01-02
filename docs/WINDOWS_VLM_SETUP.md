# VLM Kurulumu - Windows (llama.cpp + SmolVLM-500M)

## 🎯 Genel Bakış

**llama-server** (llama.cpp) + **SmolVLM-500M** kombinasyonu CPU'da çalışmak için optimize edilmiş setup.

- **RAM Kullanımı**: ~800MB
- **Disk Alanı**: ~1.5GB
- **CPU Usage**: Orta (25-40%)
- **Cevap Hızı**: 2-5 saniye (CPU'da)
- **GPU**: Gerekli değil ✅

---

## Adım 1: llama-server Binary İndir ✅ TAMAMLANDI

Windows x64 CPU versiyonunu indir:
- ✅ **`llama-b7598-bin-win-cpu-x64.zip`** (21.4 MB)
- Çıkart → `C:\llama-server\` klasörüne koy

Test:
```powershell
cd C:\llama-server
.\llama-server.exe --version
```

Çıktı:
```
version: 7598
built with Clang 19.1.5 for Windows x86_64 ✅
```

---

## Adım 2: llama-server'ı Başlat (Terminal 1) ✅ ÇALIŞIYOR

```powershell
cd C:\llama-server

.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF `
  --host 127.0.0.1 `
  --port 8080 `
  -ngl 0
```

Çıktı:
```
main: model loaded
main: server is listening on http://127.0.0.1:8080 ✅
```

**Bu terminal AÇIK KALSIN!**

---

## Adım 3: config/config.yaml Güncelle

Dosyayı aç: `c:\Users\admin\Desktop\goren_goz_mobil.app\config\config.yaml`

```yaml
vlm:
  server_url: "http://localhost:8080"
  timeout: 60
  model_name: "smolvlm-500m"
  enabled: true
```

---

## Adım 4: Backend'i Başlat (Terminal 2)

```powershell
cd c:\Users\admin\Desktop\goren_goz_mobil.app\backend
python main.py
```

Beklenen:
```
INFO: Uvicorn running on http://0.0.0.0:8000 ✅
```

---

## Adım 5: VLM Test Et (Terminal 3)

```powershell
cd c:\Users\admin\Desktop\goren_goz_mobil.app
python test_vlm.py
```

Beklenen:
```
✅ PASS - VLM Connection
✅ PASS - Image Analysis  
✅ PASS - With Detections
✅ PASS - Preset Questions

Total: 4/4 tests passed ✅
```

---

## ✅ Final Kontrol Listesi

- [x] llama-server.exe indir ve çalıştır (Port 8080)
- [x] Terminal 1: llama-server çalışıyor ✅
- [ ] config/config.yaml güncelle
- [ ] Terminal 2: python main.py (Port 8000)
- [ ] Terminal 3: python test_vlm.py (4/4 başarılı)

---

## 📊 3 Terminal Kullanımı

```powershell
# Terminal 1
cd C:\llama-server
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF `
  --host 127.0.0.1 --port 8080 -ngl 0

# Terminal 2
cd c:\Users\admin\Desktop\goren_goz_mobil.app\backend
python main.py

# Terminal 3
cd c:\Users\admin\Desktop\goren_goz_mobil.app
python test_vlm.py
```

---

## 🐛 Sorun Giderme

### Port 8080 zaten kullanımda
```powershell
netstat -an | findstr 8080
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF --port 8081
# config.yaml'da da: server_url: "http://localhost:8081"
```

### API timeout
```yaml
vlm:
  timeout: 120
```

### Çok yavaş
```powershell
.\llama-server.exe -hf ggml-org/SmolVLM-256M-Instruct-GGUF --host 127.0.0.1 --port 8080 -ngl 0
```

---

## 📚 Kaynaklar

- **llama.cpp**: https://github.com/ggerganov/llama.cpp/releases
- **SmolVLM-500M**: https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF

---

**Durum**: llama-server ✅ ÇALIŞIYOR  
**Sonraki**: Terminal 2 + 3 başlat
