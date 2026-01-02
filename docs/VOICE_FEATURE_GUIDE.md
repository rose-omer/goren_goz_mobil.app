# Voice Feature Guide - Gören Göz Mobile App

## Overview

The Gören Göz Mobile App includes a comprehensive voice interaction feature that enables users to ask questions about their surroundings using voice input. The system converts speech to text, sends it to the VLM (Vision Language Model) backend, and speaks the answer back to the user.

## Features Implemented

### 1. **Voice-to-Text Conversion** 🎤
- Real-time speech recognition using `speech_to_text` package
- Automatic language detection (currently supports en_US, tr_TR)
- Partial and final result handling
- 30-second listening window with 3-second pause detection
- Visual feedback during recording

### 2. **VLM Question Processing**
- Send recognized question + current camera frame to VLM endpoint
- Backend analyzes image context to provide accurate answers
- Automatic TTS (Text-to-Speech) response playback
- Response displayed on screen for 5 seconds

### 3. **Integration with Camera System**
- Pause frame capture during VLM processing (prevents resource conflicts)
- Safe frame capture for question context
- Automatic resume of continuous monitoring after response
- Non-blocking UI during processing

### 4. **User Interface**
- **Voice Button (Mic Icon)**: Red when listening, Normal when ready
- **Question Button**: Blue "Soru Sor" button for preset questions
- **Status Indicators**: Loading bars and snackbar notifications
- **Multi-button Layout**: Pause, Ask (Text), Ask (Voice), Settings

## Architecture

### Components

#### Mobile App (Flutter)
```
lib/
├── screens/
│   └── camera_screen.dart          # Main screen with voice controls
├── services/
│   ├── speech_recognition_service.dart    # STT wrapper
│   ├── api_service.dart                   # Backend communication
│   └── tts_service.dart                   # Text-to-speech
└── utils/
    └── speech_helper.dart          # Speech utilities
```

#### Backend (Python)
```
backend/
├── routers/
│   ├── contextual_assistant.py     # /api/ask_context endpoint
│   └── analyze.py                  # /api/analyze endpoint
├── services/
│   ├── vlm_service.py              # Vision Language Model
│   └── depth_service_v2.py         # Depth estimation
└── core/
    └── config.py                   # Configuration
```

### Data Flow

```
User speaks question
    ↓
SpeechRecognitionService captures audio
    ↓
STT converts to text: "What is ahead?"
    ↓
Camera frame captured (frame paused)
    ↓
ApiService.askContext(frame, question)
    ↓
Backend: /api/ask_context endpoint
    ↓
VLM analyzes frame + question
    ↓
Response: "There is a door 2 meters ahead"
    ↓
TtsService speaks response
    ↓
SnackBar displays answer
    ↓
Frame capture resumes
```

## Setup & Configuration

### Prerequisites

#### Mobile App
- Flutter 3.0+
- iOS 11.0+ or Android 21+
- Microphone hardware
- Camera access

#### Backend
- Python 3.8+
- FastAPI
- CUDA 11.8+ (for GPU acceleration)
- Vision Language Model (e.g., LLaVA, MobileVLM)

### Dependencies

#### Flutter (pubspec.yaml)
```yaml
dependencies:
  speech_to_text: ^7.3.0        # Speech recognition
  flutter_tts: ^4.0.2           # Text-to-speech
  camera: ^0.10.5+5             # Camera access
  dio: ^5.4.0                   # HTTP client
```

#### Python (requirements.txt)
```
fastapi==0.109.0
uvicorn==0.27.0
pillow==10.1.0
torch==2.1.2+cu118
torchvision==0.16.2+cu118
transformers==4.36.2
```

### Permissions

#### Android (AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

#### iOS (Info.plist)
```xml
<key>NSMicrophoneUsageDescription</key>
<string>We need microphone access to understand voice questions</string>

<key>NSCameraUsageDescription</key>
<string>We need camera access to analyze your surroundings</string>
```

## Usage Guide

### Starting the Application

#### Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Mobile App
```bash
cd mobile_app
flutter run
```

### Voice Question Workflow

#### Method 1: Voice Input (Recommended for Accessibility)
1. **Tap Mic Button** (bottom right)
   - Button turns red: "🎤 Listening..."
   - Speak your question clearly
   - "What is in front of me?"

2. **System Processes**
   - Speech converted to text
   - Frame captured automatically
   - Question sent to VLM backend

3. **Receive Response**
   - Answer played via TTS
   - Text displayed on screen
   - Frame capture resumes

#### Method 2: Preset Questions
1. **Tap "Soru Sor"** (Ask Question button)
   - Blue button with text
   - Shows preset question options:
     - "What is ahead of me?"
     - "Is it safe to cross?"
     - "Where is the nearest obstacle?"
     - "Are there stairs ahead?"
     - "Are there people around?"

2. **Select Question**
   - Tap desired question
   - System automatically captures frame and sends

#### Method 3: Custom Text Questions
1. **Tap "Soru Sor"**
2. **Type custom question** (future enhancement)
3. **Submit to VLM**

### Voice Features Explained

#### Speech Recognition
- **Language Support**
  - English: `en_US`
  - Turkish: `tr_TR` (add to settings)
  - Others: Configurable

- **Recognition Settings**
  - Listening duration: 30 seconds
  - Pause detection: 3 seconds
  - Partial results: Enabled (real-time feedback)

- **Accuracy Factors**
  - Clear pronunciation
  - Minimal background noise
  - Proper microphone calibration
  - Language selection

#### VLM Processing
- **Input**: Camera frame + Question
- **Processing**: Analyzes objects, depth, context
- **Output**: Natural language answer
- **Response Time**: 1-5 seconds (depends on model)

#### Text-to-Speech Response
- **Language**: Auto-matched to input
- **Rate**: 1.0x (normal speed)
- **Volume**: System volume
- **Interruption**: Can play multiple responses

### Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No speech detected" | Microphone silent | Speak louder/clearer |
| "Microphone not available" | Permission denied | Grant mic permission |
| "No response from server" | Backend down | Check server status |
| "Invalid response" | VLM error | Check backend logs |
| "Camera not initialized" | Camera access issue | Restart app |

## Configuration

### Mobile App Settings (SharedPreferences)

```dart
// Speech settings
prefs.setBool('voice_enabled', true);
prefs.setString('speech_language', 'en_US');
prefs.setInt('listening_timeout', 30); // seconds

// TTS settings
prefs.setDouble('tts_speed', 1.0);
prefs.setDouble('tts_volume', 1.0);
prefs.setBool('tts_enabled', true);

// Camera settings
prefs.setInt('frame_rate', 1); // FPS
```

### Backend Configuration (config.yaml)

```yaml
vlm:
  model: "llava-v1.6-mistral-7b"
  device: "cuda"
  max_tokens: 256
  temperature: 0.7
  
speech:
  default_language: "en_US"
  timeout_seconds: 30
  
api:
  base_url: "http://0.0.0.0:8000"
  ask_context_endpoint: "/api/ask_context"
```

## API Endpoints

### /api/ask_context

#### Request
```bash
POST /api/ask_context
Content-Type: multipart/form-data

Parameters:
- image: Binary JPEG image data
- question: String question about the image
- use_cached_detections: Boolean (optional, default: true)
```

#### Response
```json
{
  "success": true,
  "answer": "There is a red door approximately 2 meters ahead on your left.",
  "processing_time_ms": 2341,
  "metadata": {
    "model": "llava-v1.6-mistral-7b",
    "detected_objects": ["door", "wall", "ground"],
    "confidence": 0.92
  }
}
```

## Testing

### Mobile App Testing

#### Unit Tests
```bash
cd mobile_app
flutter test
```

#### Integration Tests
```bash
flutter drive --target=test_driver/app.dart
```

#### Manual Testing Checklist
- [ ] Voice recognition works (English)
- [ ] Voice recognition works (Turkish)
- [ ] Silent input handled gracefully
- [ ] Simultaneous requests prevented
- [ ] Frame capture paused during VLM
- [ ] Frame capture resumed after response
- [ ] TTS response plays correctly
- [ ] UI updates reflect state changes
- [ ] Error messages display correctly
- [ ] App doesn't crash on errors

### Backend Testing

```python
# Test voice question endpoint
import requests

with open('test_frame.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/ask_context',
        files={'image': f},
        data={'question': 'What is ahead?'}
    )
    print(response.json())
```

## Performance Optimization

### Mobile App
- **Frame Capture**: Pause during VLM processing
- **Memory**: Use Uint8List for efficient image handling
- **Threading**: Async/await for non-blocking operations
- **Caching**: Optional cached detections

### Backend
- **GPU**: CUDA acceleration for VLM inference
- **Quantization**: INT8 or FP16 for faster inference
- **Batch Processing**: Support multiple requests
- **Caching**: Cache image features for similar questions

## Troubleshooting

### Microphone Not Detected
```dart
// Check in SpeechRecognitionService
final available = await _speechToText.initialize();
if (!available) {
  // Handle unavailable microphone
}
```

### VLM Response Slow
- Reduce model size (use smaller VLM)
- Enable GPU acceleration
- Use INT8 quantization
- Check server logs for bottlenecks

### Speech Recognition Inaccurate
- Select correct language
- Improve microphone positioning
- Reduce background noise
- Speak slower and clearer

### No Response from Backend
```bash
# Test server
curl http://localhost:8000/api/health

# Check logs
tail -f backend/logs/app.log
```

## Future Enhancements

1. **Multi-Language Support**
   - Add more languages (e.g., German, French, Spanish)
   - Auto-detect user language

2. **Advanced Voice Features**
   - Voice commands (e.g., "Check right", "Analyze floor")
   - Continuous conversation mode
   - Voice macro recording

3. **Improved Accessibility**
   - Haptic feedback during listening
   - Vibrational patterns for different responses
   - Adjustable TTS rate and volume

4. **Offline Mode**
   - Local speech recognition (on-device STT)
   - Lightweight VLM models
   - Cached question-answer pairs

5. **Analytics**
   - Track frequently asked questions
   - Monitor response accuracy
   - Usage statistics

## Security Considerations

1. **Audio Privacy**
   - Audio only sent to backend (not stored)
   - HTTPS encryption for transmission
   - User consent for recording

2. **API Authentication**
   - JWT tokens for requests
   - Rate limiting (10 req/min per user)
   - Request validation

3. **Model Security**
   - Sandbox VLM execution
   - Input validation and sanitization
   - Output filtering for sensitive content

## References

- [speech_to_text Documentation](https://pub.dev/packages/speech_to_text)
- [flutter_tts Documentation](https://pub.dev/packages/flutter_tts)
- [LLaVA Model](https://github.com/haotian-liu/LLaVA)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For issues or questions:
1. Check the logs in `backend/logs/app.log`
2. Review error messages in Flutter debug console
3. Test API endpoints manually with curl
4. Check GitHub issues: [Gören Göz Issues](https://github.com/example/goren_goz/issues)

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: ✅ Complete & Tested
