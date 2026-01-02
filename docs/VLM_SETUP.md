# VLM Server Setup Guide - LLaMA/Ollama Integration

## 🤖 Overview

The **Contextual Assistant** feature uses a Vision Language Model (VLM) to provide intelligent, context-aware responses about the user's surroundings. This requires a local VLM server (llama.cpp).

**Supported Models:**
- SmolVLM (recommended, 2.7B - fast and accurate)
- LLaVA 1.6 7B (higher accuracy, slower)
- Ollama with visual models

---

## 📦 Installation

### Option 1: Using Ollama (Easiest)

**1. Install Ollama**
```bash
# Windows
# Download from https://ollama.ai
# Or use winget:
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh
```

**2. Pull VLM Model**
```bash
# SmolVLM (fastest, recommended for real-time)
ollama pull smolvlm

# Or LLaVA 1.6 (higher quality)
ollama pull llava:7b-v1.6

# Or Llama 2 with vision
ollama pull llava:13b
```

**3. Start Ollama Server**
```bash
# Default runs on http://localhost:11434
ollama serve
```

**4. Configure Backend**

In `config/config.yaml` or via environment variable:
```yaml
vlm:
  server_url: "http://localhost:11434"
  model_name: "smolvlm"  # or "llava:7b-v1.6"
  timeout: 30
```

### Option 2: Using llama.cpp (Advanced)

**1. Build llama.cpp**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

**2. Download VLM Weights**
```bash
# SmolVLM GGUF format (recommended)
# Download from: https://huggingface.co/xtuner/SmolVLM-256M-GQA-int4

# Or LLaVA:
# Download from: https://huggingface.co/mys/ggml-model-f16
```

**3. Start Server**
```bash
./llama-server \
  -m models/smolvlm-256m-int4.gguf \
  --port 8080 \
  --n-gpu-layers 99 \
  --chat-template smolvlm
```

**4. Configure Backend**
```yaml
vlm:
  server_url: "http://localhost:8080"
  timeout: 30
```

---

## 🔧 API Endpoints

### 1. Ask Contextual Question

**Endpoint:** `POST /api/ask_context`

**Request:**
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
  "answer": "Sağ tarafta bir araç yaklaşıyor, mesafe yaklaşık 2 metre.",
  "processing_time_ms": 2500,
  "context_used": {
    "detections_count": 3,
    "detections": [
      {
        "name": "car",
        "name_tr": "araba",
        "confidence": 0.95,
        "distance": 2.0,
        "region": "right"
      }
    ],
    "cached": false
  },
  "metadata": {
    "processing_time_ms": 2500,
    "server_url": "http://localhost:11434",
    "detections_count": 3,
    "tokens_generated": 42,
    "attempt": 1
  },
  "timestamp": "2025-11-24T12:34:56Z"
}
```

### 2. Get Preset Questions

**Endpoint:** `GET /api/preset_questions`

**Response:**
```json
{
  "success": true,
  "preset_questions": {
    "which_direction": "Hangi taraftan en yakın tehlike?",
    "safe_path": "Güvenli bir yol var mı?",
    "obstacles": "Çevrede ne tür engeller var?",
    "distance_info": "Nesneler ne kadar uzakta?"
  }
}
```

---

## 📋 Prompt Templates

The backend automatically creates context-aware prompts using information from YOLO detections:

**Example Prompt:**
```
You are a helpful assistant for visually impaired users.

Detected objects in the scene:
- person at 1.5m (center region)
- car at 2.0m (right region)
- tree at 3.5m (left region)

User question: Hangi taraftan tehlike var?

Respond in Turkish, be concise and focus on navigation safety.
```

---

## 🧪 Testing

### Test 1: Check VLM Server Status

```bash
curl http://localhost:11434/api/tags
# Expected: List of available models
```

### Test 2: Simple Inference

```bash
# Test without backend
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "smolvlm",
    "messages": [
      {
        "role": "user",
        "content": "What do you see in this image?"
      }
    ],
    "stream": false
  }'
```

### Test 3: Full Backend Integration

```bash
# Create test image
python -c "
import cv2
import numpy as np

# Create simple test image
img = np.ones((480, 640, 3), dtype=np.uint8) * 200
cv2.imwrite('test_scene.jpg', img)
"

# Test endpoint
curl -X POST http://localhost:8000/api/ask_context \
  -F "image=@test_scene.jpg" \
  -F "question=Bu nedir?"
```

---

## ⚙️ Performance Tuning

### For Faster Inference

**Use smaller models:**
```bash
# SmolVLM (recommended for real-time)
ollama pull smolvlm  # ~500ms per query

# Or use quantized models
ollama pull llava:7b-v1.6-q4  # 4-bit quantization
```

**Increase GPU allocation:**
```yaml
vlm:
  gpu_layers: 99  # Use all available GPU layers
  num_threads: 8
```

**Reduce image resolution:**
```python
# In vlm_service.py
max_size = 384  # Reduce from 512 to 384 pixels
```

### For Higher Accuracy

```bash
# Use 7B or 13B models
ollama pull llava:13b
```

---

## 🐛 Troubleshooting

### Issue: VLM Server Not Responding

**Solution:**
```bash
# Check if server is running
ps aux | grep ollama

# Or check port
netstat -an | grep 11434

# Restart server
ollama serve
```

### Issue: Memory Error

**Solution:**
```bash
# Use CPU instead of GPU
export CUDA_VISIBLE_DEVICES=-1
ollama serve

# Or reduce model size
ollama pull smolvlm  # Smaller model
```

### Issue: Slow Responses

**Solution:**
```bash
# Check GPU utilization
nvidia-smi

# Use quantized model
ollama pull llava:7b-v1.6-q4

# Reduce max tokens
# In vlm_service.py: n_predict=50 (was 100)
```

---

## 🔗 Integration Points

### 1. Main Backend (`backend/main.py`)
- VLM service is optional (lazy loaded)
- If unavailable, app starts without VLM features

### 2. API Router (`routers/contextual_assistant.py`)
- `/api/ask_context` - Main endpoint
- `/api/preset_questions` - Get preset questions

### 3. Services
- `services/vlm_service.py` - VLM communication
- `services/prompt_templates.py` - Prompt building

---

## 📊 Architecture Diagram

```
┌──────────────────┐
│  Mobile App      │
│  (Flutter)       │
└────────┬─────────┘
         │
         │ POST /api/ask_context
         │ (image + question)
         ↓
┌──────────────────────────┐
│  FastAPI Backend         │
│  ┌─────────────────────┐ │
│  │ Contextual Router   │ │
│  └──────┬──────────────┘ │
│         │                │
│    ┌────┴──────┐         │
│    ↓           ↓         │
│  ┌──────────┐ ┌──────────┐
│  │YOLO Det. │ │VLM Svc.  │
│  └────┬─────┘ └────┬─────┘
│       │            │
└───────┼────────────┼───────┘
        │            │
        ↓            ↓
   [Detections]  [llama.cpp/Ollama]
                 (SmolVLM/LLaVA)
```

---

## 📝 Configuration Examples

### `config/config.yaml`

```yaml
vlm:
  # Server configuration
  server_url: "http://localhost:11434"
  timeout: 30
  max_retries: 2
  
  # Model settings
  model_name: "smolvlm"
  
  # Performance
  n_predict: 100  # Max tokens
  temperature: 0.7
  top_p: 0.9

# Or set via environment:
# VLM_SERVER_URL=http://localhost:11434
# VLM_MODEL=llava:7b-v1.6
```

---

## 🚀 Next Steps

1. ✅ Install Ollama or llama.cpp
2. ✅ Pull VLM model (SmolVLM recommended)
3. ✅ Start server
4. ✅ Configure backend URL
5. ✅ Test with `/api/preset_questions`
6. ✅ Test with `/api/ask_context`
7. ✅ Monitor performance with `/api/health`

---

## 📚 Resources

- **Ollama**: https://ollama.ai
- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **SmolVLM**: https://huggingface.co/xtuner/SmolVLM-256M
- **LLaVA**: https://llava-vl.github.io
