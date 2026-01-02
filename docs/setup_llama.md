# llama.cpp ve SmolVLM Kurulum Rehberi (Windows)

Bu doküman, Windows sistemlerde llama.cpp ve SmolVLM modelinin kurulumu için adım adım rehberdir.

## Gereksinimler

- Windows 10/11
- En az 4GB RAM (8GB+ önerilir)
- İnternet bağlantısı (model indirme için)
- (Opsiyonel) NVIDIA GPU (CUDA desteği için)

## Adım 1: llama.cpp İndirme

### Pre-built Binary Kullanma (Önerilen)

1. [llama.cpp GitHub Releases](https://github.com/ggerganov/llama.cpp/releases) sayfasına gidin
2. En son release'i bulun
3. Windows için uygun binary'yi indirin:
   - **CPU Only**: `llama-*-bin-win-avx2-x64.zip`
   - **NVIDIA GPU**: `llama-*-bin-win-cuda-cu12.2.0-x64.zip`
   - **AMD GPU**: `llama-*-bin-win-rocm-avx2-x64.zip`

4. ZIP dosyasını çıkartın (örn: `C:\llama.cpp\`)

5. PATH'e ekleyin (opsiyonel):
   - Sistem Özellikleri > Gelişmiş > Ortam Değişkenleri
   - `Path` değişkenine `C:\llama.cpp\bin` ekleyin

### Kaynak Koddan Derleme (İleri Seviye)

```powershell
# Git, CMake ve Visual Studio gerekli
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# CPU build
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# NVIDIA GPU build
cmake -B build -DLLAMA_CUBLAS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

## Adım 2: SmolVLM Model İndirme

SmolVLM modelini iki yöntemle indirebilirsiniz:

### Yöntem 1: llama-server Otomatik İndirme (Önerilen)

llama-server ilk çalıştırmada modeli otomatik indirir:

```powershell
cd C:\llama.cpp\bin
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF
```

Model `%USERPROFILE%\.cache\llama.cpp\` klasörüne indirilir.

### Yöntem 2: Manuel İndirme

1. [Hugging Face SmolVLM](https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF) sayfasına gidin
2. `SmolVLM-500M-Instruct-Q8_0.gguf` dosyasını indirin (~500MB)
3. Modeli uygun bir klasöre kaydedin (örn: `C:\llama.cpp\models\`)

## Adım 3: llama-server Başlatma

### Temel Başlatma (CPU)

```powershell
cd C:\llama.cpp\bin
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF
```

### GPU ile Başlatma (NVIDIA)

```powershell
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF -ngl 99
```

`-ngl 99` parametresi GPU'ya tüm katmanları yükler (daha hızlı).

### Manuel Model ile Başlatma

```powershell
.\llama-server.exe -m C:\llama.cpp\models\SmolVLM-500M-Instruct-Q8_0.gguf -ngl 99
```

### Başlatma Parametreleri

```powershell
.\llama-server.exe `
  -hf ggml-org/SmolVLM-500M-Instruct-GGUF `
  -ngl 99 `
  --host 0.0.0.0 `
  --port 8080 `
  -c 2048 `
  --log-disable
```

**Parametreler:**
- `-ngl 99`: GPU kullanımı (NVIDIA/AMD için)
- `--host 0.0.0.0`: Tüm network interface'lerden erişim
- `--port 8080`: Port numarası (default: 8080)
- `-c 2048`: Context boyutu (token)
- `--log-disable`: Verbose logları kapat

## Adım 4: Test

### Web UI ile Test

1. Browser'da `http://localhost:8080` adresini açın
2. Bir görüntü yükleyin
3. "What do you see?" gibi bir soru sorun
4. Yanıt geldiğini doğrulayın

### API ile Test

PowerShell:
```powershell
$body = @{
    prompt = "What objects do you see in this image?"
    image_data = @(@{
        data = [Convert]::ToBase64String([IO.File]::ReadAllBytes("test.jpg"))
        id = 1
    })
    n_predict = 100
} | ConvertTo-Json -Depth 3

Invoke-WebRequest -Uri "http://localhost:8080/completion" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

cURL:
```bash
curl -X POST http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What do you see?",
    "image_data": [{"data": "...base64...", "id": 1}],
    "n_predict": 100
  }'
```

## Adım 5: Backend Entegrasyonu

Backend'i başlatırken llama-server'ın çalıştığından emin olun:

```powershell
# Terminal 1: llama-server
cd C:\llama.cpp\bin
.\llama-server.exe -hf ggml-org/SmolVLM-500M-Instruct-GGUF -ngl 99

# Terminal 2: Backend
cd C:\Users\admin\Desktop\goren_goz_mobil.app\backend
python main.py
```

Backend health check'te VLM durumunu görebilirsiniz:
```powershell
curl http://localhost:8000/health
```

Yanıt:
```json
{
  "status": "healthy",
  "vlm": {
    "server_ready": true,
    "server_url": "http://localhost:8080"
  }
}
```

## Troubleshooting

### Problem 1: "llama-server.exe not found"

**Çözüm:**
- ZIP dosyasını doğru çıkardığınızdan emin olun
- `bin` klasöründe olduğunuzu kontrol edin
- PATH'e eklediyseniz, PowerShell'i yeniden başlatın

### Problem 2: "Model download failed"

**Çözüm:**
- İnternet bağlantınızı kontrol edin
- Firewall/antivirus'ün Hugging Face'i engellemediğinden emin olun
- Manuel indirme yöntemini deneyin

### Problem 3: "Out of memory"

**Çözüm:**
- Context boyutunu azaltın: `-c 1024`
- Daha küçük model kullanın (Q4 quantization)
- GPU kullanıyorsanız VRAM'inizi kontrol edin

### Problem 4: "Server not responding"

**Çözüm:**
- Port 8080'in kullanımda olmadığını kontrol edin: `netstat -ano | findstr :8080`
- Firewall'da 8080 portunu açın
- `--host 0.0.0.0` parametresini ekleyin

### Problem 5: "VLM server not available"

**Çözüm:**
- llama-server'ın çalıştığından emin olun
- `http://localhost:8080` adresini browser'da test edin
- Backend'deki `VLM_SERVER_URL` konfigürasyonunu kontrol edin

## Performans İpuçları

1. **GPU Kullanımı**: `-ngl 99` parametresi ile performansı 5-10x artırın
2. **Quantization**: Q8 yerine Q4 model daha hızlı ama daha düşük kaliteli
3. **Context Size**: Küçük context (`-c 1024`) daha hızlı işleme
4. **Batch Size**: Tek seferde birden fazla istek için `-b` parametresi

## Sistem Gereksinimleri

### Minimum (CPU)
- CPU: Intel i5 veya AMD Ryzen 5
- RAM: 4GB
- Disk: 1GB boş alan
- Response time: ~3-5 saniye

### Önerilen (GPU)
- GPU: NVIDIA GTX 1660 veya üstü (6GB+ VRAM)
- RAM: 8GB
- Disk: 1GB boş alan
- Response time: ~0.5-1 saniye

## Ek Kaynaklar

- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [SmolVLM Hugging Face](https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF)
- [llama.cpp Multimodal Docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)

---

**Not**: Bu rehber Windows için hazırlanmıştır. Linux/Mac için komutlar farklılık gösterebilir.
