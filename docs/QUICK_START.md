# 🚀 VLM Hızlı Başlangıç

## 5 Dakikalık Kurulum

### Terminal 1️⃣ - Ollama Sunucusu
```powershell
ollama serve
```
Port 11434'te dinlemeli

### Terminal 2️⃣ - Backend API
```powershell
cd backend
python main.py
```
Port 8000'de çalışmalı

### Terminal 3️⃣ - Test
```powershell
python test_vlm.py
```

## 📊 Beklenen Sonuç

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VLM İNTEGRASYON TESTİ SONUÇLARI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Test 1: VLM Bağlantısı
   Ollama server'a başarıyla bağlandı
   Server: http://localhost:11434
   Model: smolvlm

✅ Test 2: Resim Analizi
   Örnek resim analiz edildi
   Sonuç: [30 satır Türkçe analiz]

✅ Test 3: Nesne Tespiti ile
   YOLO detections: 5 nesne bulundu
   Analiz: [Türkçe bağlam metni]

✅ Test 4: Hazır Sorular
   6 soruda yanıt alındı
   Tümü başarılı

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Toplam: 4/4 TEST GEÇTİ ✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🔧 API Endpoints

```bash
# Bağlam sorgusu (resim + soru)
curl -X POST http://localhost:8000/api/ask_context \
  -F "image=@your_image.jpg" \
  -F "question=Hangi taraftan tehlike var?"

# Hazır sorular listesi
curl http://localhost:8000/api/preset_questions
```

## 🛠️ Ayarlar (config/config.yaml)

```yaml
vlm:
  enabled: true
  server_url: "http://localhost:11434"
  timeout: 30
  max_retries: 2
  model_name: "smolvlm"
  n_predict: 100
  temperature: 0.7
```

## ❌ Sorun mu var?

Şu dosyayı oku: [WINDOWS_VLM_SETUP.md](WINDOWS_VLM_SETUP.md)

---

**Hazırsa şimdi başla!** 🎯
