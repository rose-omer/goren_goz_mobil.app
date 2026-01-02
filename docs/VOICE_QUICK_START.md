# Voice Feature - Quick Start Guide

## 🎤 Feature Overview

The Gören Göz app now supports **voice-based questions** about the user's surroundings. Users can:
- Tap the **Mic button** and speak a question
- Or select from **preset questions**
- Get intelligent answers powered by VLM (Vision Language Model)
- Hear responses via **Text-to-Speech**

## ⚡ Quick Implementation Summary

### What's Already Implemented

✅ **Mobile App Components**
- `SpeechRecognitionService`: STT wrapper using `speech_to_text` package
- `CameraScreenState._startVoiceQuestion()`: Voice listening logic
- `CameraScreenState._stopVoiceQuestion()`: Process recognized text
- `CameraScreenState._askVLMQuestion()`: Send to backend
- **UI Controls**: Mic button, preset questions, responses

✅ **Backend Components**
- `/api/ask_context` endpoint in `contextual_assistant.py`
- VLM model loading and inference
- Response formatting with metadata

✅ **Configuration**
- Android permissions: `RECORD_AUDIO`, `CAMERA`, `INTERNET`
- Dependencies: `speech_to_text: ^7.3.0`, `flutter_tts: ^4.0.2`
- Backend: FastAPI, transformers, torch

✅ **Permissions**
- Android manifest updated
- iOS Info.plist ready (microphone description)
- Runtime permission handling

## 🚀 Getting Started

### Start Backend Server
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Mobile App
```bash
cd mobile_app
flutter pub get
flutter run
```

### Test Voice Feature
1. **Tap Mic Button** (red icon, bottom right)
2. **Speak**: "What is ahead of me?"
3. **Wait**: System processes and responds
4. **Hear**: TTS speaks answer automatically

## 📱 User Interface

### Buttons at Bottom of Screen

| Button | Function | State |
|--------|----------|-------|
| ⏸️ Pause | Start/stop continuous monitoring | Normal/Paused |
| 🎤 Voice | Record voice question | Normal/Listening |
| 🔵 Ask | Preset questions menu | Normal/Processing |
| ⚙️ Settings | App configuration | Always active |

**Voice Button States:**
- 🔵 Teal: Ready to listen
- 🔴 Red: Currently listening

## 🔧 Code Structure

### Mobile App

**SpeechRecognitionService** (`lib/services/speech_recognition_service.dart`)
```dart
// Initialize
final service = SpeechRecognitionService();
await service.initialize();

// Listen
await service.startListening(
  languageCode: 'en_US',
  onResult: (text) => print('Heard: $text'),
);

// Stop
await service.stopListening();
final recognizedText = service.getRecognizedText();
```

**CameraScreen Voice Methods** (`lib/screens/camera_screen.dart`)
```dart
// Start listening
_startVoiceQuestion() {
  // Shows "🎤 Listening" indicator
  // Records audio for 30 seconds
}

// Process speech
_stopVoiceQuestion() {
  // Extracts recognized text
  // Calls VLM with question + current frame
}

// Ask VLM
_askVLMQuestion(String question) {
  // Pauses frame capture
  // Captures current frame
  // Sends to backend
  // Speaks response via TTS
  // Resumes frame capture
}
```

### Backend

**Endpoint** (`backend/routers/contextual_assistant.py`)
```python
@router.post("/ask_context")
async def ask_context(
    image: UploadFile,
    question: str,
    use_cached_detections: bool = True
) -> dict:
    # Load image
    # Get VLM service
    # Ask question about image
    # Return answer with metadata
```

**VLM Service** (`backend/services/vlm_service.py`)
```python
async def ask_context(image, question):
    # Image preprocessing
    # Load VLM model
    # Run inference
    # Return answer string
```

## 🧪 Testing

### Quick Test
```dart
// In camera_screen.dart, add test button
ElevatedButton(
  onPressed: () => _askVLMQuestion('Test question'),
  child: Text('Test VLM'),
)
```

### Check Logs
```bash
# Mobile
flutter logs -f

# Backend
tail -f backend/logs/app.log
```

### Test API Directly
```bash
# Using curl
curl -X POST http://localhost:8000/api/ask_context \
  -F "image=@test_frame.jpg" \
  -F "question=What is ahead?"
```

## ⚠️ Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| "Mic not available" | Permission denied | Grant `RECORD_AUDIO` permission |
| "No speech detected" | Silent input | Speak louder/clearer |
| "Backend unreachable" | Server offline | Start backend server |
| "Slow response" | Small model/no GPU | Use GPU, smaller model |
| "Garbled text" | Poor recognition | Better microphone, clearer speech |

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────┐
│         Mobile App (Flutter)            │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      Camera Screen              │   │
│  │  ┌───────────────┐              │   │
│  │  │  🎤 Mic Btn   │              │   │
│  │  └───────────────┘              │   │
│  └─────────────────────────────────┘   │
│            │                            │
│            ▼                            │
│  ┌─────────────────────────────────┐   │
│  │ SpeechRecognitionService        │   │
│  │ (speech_to_text)                │   │
│  └─────────────────────────────────┘   │
│            │                            │
│      Recognized Text: "What..."         │
│            │                            │
│            ▼                            │
│  ┌─────────────────────────────────┐   │
│  │ ApiService.askContext()         │   │
│  │ (frame + question)              │   │
│  └─────────────────────────────────┘   │
└────────────┬────────────────────────────┘
             │
             │ POST /api/ask_context
             ▼
┌─────────────────────────────────────────┐
│      Backend (Python/FastAPI)           │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  contextual_assistant.py        │   │
│  │  /api/ask_context endpoint      │   │
│  └─────────────────────────────────┘   │
│            │                            │
│            ▼                            │
│  ┌─────────────────────────────────┐   │
│  │ VLM Service                     │   │
│  │ (LLaVA / MobileVLM / etc)       │   │
│  └─────────────────────────────────┘   │
│            │                            │
│      Response: "There is..."            │
│            │                            │
└────────────┬────────────────────────────┘
             │
             │ JSON: {"answer": "..."}
             ▼
┌─────────────────────────────────────────┐
│      Mobile App - Response Display       │
│                                         │
│  TtsService.speak(answer)               │
│  SnackBar.show(answer)                  │
│  Resume frame capture                   │
└─────────────────────────────────────────┘
```

## 📝 Configuration Files

### Android Permissions
**File**: `mobile_app/android/app/src/main/AndroidManifest.xml`
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
```

### iOS Permissions
**File**: `mobile_app/ios/Runner/Info.plist`
```xml
<key>NSMicrophoneUsageDescription</key>
<string>Microphone access enables voice questions about surroundings</string>
```

### Flutter Packages
**File**: `mobile_app/pubspec.yaml`
```yaml
dependencies:
  speech_to_text: ^7.3.0
  flutter_tts: ^4.0.2
  camera: ^0.10.5+5
  dio: ^5.4.0
```

### Backend Dependencies
**File**: `backend/requirements.txt`
```
fastapi==0.109.0
transformers==4.36.2
torch==2.1.2+cu118
```

## 🎯 Next Steps

1. **Test the feature**
   - Start backend and mobile app
   - Tap mic button and speak
   - Verify response

2. **Optimize performance**
   - Enable GPU inference
   - Use model quantization
   - Add request caching

3. **Enhance UX**
   - Add more languages
   - Implement voice commands
   - Add visual feedback during processing

4. **Add features**
   - Conversation history
   - Favorite questions
   - Custom voice commands

## 📚 Documentation

- **Full Guide**: [VOICE_FEATURE_GUIDE.md](VOICE_FEATURE_GUIDE.md)
- **VLM Setup**: [VLM_SETUP.md](VLM_SETUP.md)
- **Mobile App**: [BASLANGIC_REHBERI.md](BASLANGIC_REHBERI.md)
- **Backend**: [backend/README.md](../backend/README.md)

## 🤝 Support

### Debug Checklist
- [ ] Backend server running on port 8000
- [ ] Microphone permission granted
- [ ] Camera working
- [ ] Internet connected
- [ ] VLM model loaded
- [ ] Speech recognition available

### View Logs
```bash
# Mobile app logs
flutter logs

# Backend logs
tail -f backend/logs/app.log

# Test health
curl http://localhost:8000/api/health
```

---

**Status**: ✅ Complete & Ready to Use
**Version**: 1.0.0
