# VLM Quick Start Guide

## 🚀 5 Dakikada VLM Kurulumu

### Windows

```powershell
# 1. PowerShell'i yönetici olarak aç
# 2. Script'i çalıştır:
.\setup_vlm.ps1

# 3. Ollama server'ı başlat
ollama serve

# 4. Yeni terminal açıp backend'i başlat
cd backend
python main.py

# 5. VLM'yi test et
python ../test_vlm.py
```

### macOS / Linux

```bash
# 1. Script'i çalıştırılabilir yap
chmod +x setup_vlm.sh

# 2. Script'i çalıştır
./setup_vlm.sh

# 3. Ollama server'ı başlat
ollama serve

# 4. Yeni terminal açıp backend'i başlat
cd backend
python main.py

# 5. VLM'yi test et
python ../test_vlm.py
```

---

## ✨ Kullanılabilecek Modeller

### SmolVLM (Önerilen) ✅
```bash
ollama pull smolvlm
# - Boyut: 500MB
# - Hız: ~500ms/query
# - Kalite: Yeterli
```

### LLaVA 1.6 (7B - Daha Doğru)
```bash
ollama pull llava:7b-v1.6
# - Boyut: 4GB
# - Hız: ~1-2s/query
# - Kalite: Yüksek
```

### LLaVA 1.6 (13B - En Doğru)
```bash
ollama pull llava:13b
# - Boyut: 7GB
# - Hız: ~2-3s/query
# - Kalite: Çok yüksek
```

---

## 🧪 Test Komutları

### Test 1: Server Durumu
```bash
# Çalışan modelleri listele
ollama list
```

### Test 2: Simple Chat
```bash
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "smolvlm",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

### Test 3: Backend API
```bash
# Python test script'i çalıştır
python test_vlm.py
```

### Test 4: Gerçek Resim
```bash
# Resim yükleyerek test et
curl -X POST http://localhost:8000/api/ask_context \
  -F "image=@your_photo.jpg" \
  -F "question=Bu resimde ne var?" \
  -F "use_cached_detections=false"
```

---

## 🔧 Troubleshooting

### Ollama server çalışmıyor
```bash
# Çalışan işlemi kontrol et
ps aux | grep ollama

# Manüel olarak başlat
ollama serve

# Port 11434'ü kontrol et
netstat -an | grep 11434
```

### Model indirimi yavaş
```bash
# Proxy kullan (gerekirse)
export HTTP_PROXY=...
export HTTPS_PROXY=...

# Daha küçük model kullan
ollama pull smolvlm  # Yerine llava:7b-v1.6-q4
```

### Bellek sorunu
```bash
# CPU'da çalıştır
export CUDA_VISIBLE_DEVICES=-1
ollama serve

# Daha küçük model kullan
ollama pull smolvlm
```

### API timeouts
```bash
# config.yaml'da timeout'ı artır
vlm:
  timeout: 60  # 30'dan 60'a çıkart
```

---

## 📊 Performance İpuçları

### Daha Hızlı
```bash
# 1. SmolVLM kullan
ollama pull smolvlm

# 2. Resim boyutunu küçült (config.yaml)
vlm:
  max_image_size: 384  # 512'den 384'e

# 3. Token limitini azalt
vlm:
  n_predict: 50  # 100'den 50'ye
```

### Daha Doğru
```bash
# 1. Daha büyük model kullan
ollama pull llava:13b

# 2. Daha yüksek temperature
vlm:
  temperature: 0.8  # 0.7'den 0.8'e
```

---

## 🔌 API Endpoints

### POST /api/ask_context
```bash
curl -X POST http://localhost:8000/api/ask_context \
  -F "image=@scene.jpg" \
  -F "question=Hangi taraftan tehlike var?" \
  -F "use_cached_detections=true"
```

**Response:**
```json
{
  "success": true,
  "answer": "Sağ tarafta 2 metre uzakta bir araç var.",
  "processing_time_ms": 2500,
  "context_used": {
    "detections_count": 3,
    "cached": false
  },
  "metadata": {...}
}
```

### GET /api/preset_questions
```bash
curl http://localhost:8000/api/preset_questions
```

**Response:**
```json
{
  "success": true,
  "preset_questions": {
    "whats_ahead": "Önümde ne var?",
    "safe_to_cross": "Karşıya geçmek güvenli mi?",
    "nearest_obstacle": "En yakın engel nerede?",
    ...
  }
}
```

---

## 📝 Konfigürasyon (config.yaml)

```yaml
vlm:
  enabled: true
  server_url: "http://localhost:11434"
  timeout: 30
  max_retries: 2
  model_name: "smolvlm"
  n_predict: 100
  temperature: 0.7
  max_image_size: 512
```

---

## ✅ Kontrol Listesi

- [ ] Ollama yüklü
- [ ] SmolVLM model indirildi (`ollama list`)
- [ ] `ollama serve` çalışıyor
- [ ] Backend başlatıldı (`python main.py`)
- [ ] Test script geçti (`python test_vlm.py`)
- [ ] API endpoint'i cevap veriyor (`test_vlm.py`)
- [ ] Mobile app'de `/api/ask_context` kullanılabiliyor

---

## 🆘 Hızlı Çözümler

| Problem | Çözüm |
|---------|-------|
| `ConnectionError: Cannot connect to server` | `ollama serve` çalıştır |
| `"smolvlm not found"` | `ollama pull smolvlm` çalıştır |
| `Timeout` | `timeout: 60` olarak artır |
| `Out of memory` | Daha küçük model kullan veya CPU'da çalıştır |
| `Slow response` | SmolVLM kullan, `n_predict` değerini azalt |

---

## 📚 Kaynaklar

- **Ollama Docs**: https://github.com/ollama/ollama
- **SmolVLM**: https://huggingface.co/xtuner/SmolVLM-256M
- **LLaVA**: https://llava-vl.github.io
- **Detaylı Setup Guide**: docs/VLM_SETUP.md

---

**Herhangi bir sorun yaşarsan `test_vlm.py` çalıştırarak detaylı log görebilirsin!** 🎯
