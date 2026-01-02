# Voice Feature - Technical Architecture

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    User Device (Mobile)                      │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Flutter Application                        │  │
│  │                                                         │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │              Camera Screen                       │  │  │
│  │  │  ┌─────────────────────────────────────────┐    │  │  │
│  │  │  │  Continuous Frame Monitoring            │    │  │  │
│  │  │  │  - Capture frames at 1-2 FPS           │    │  │  │
│  │  │  │  - Analyze with backend API            │    │  │  │
│  │  │  │  - Display alerts                       │    │  │  │
│  │  │  └─────────────────────────────────────────┘    │  │  │
│  │  │  ┌─────────────────────────────────────────┐    │  │  │
│  │  │  │  Voice Input Handler                    │    │  │  │
│  │  │  │  - Pause frame capture                  │    │  │  │
│  │  │  │  - Listen for voice input               │    │  │  │
│  │  │  │  - Send question to VLM                 │    │  │  │
│  │  │  │  - Play TTS response                    │    │  │  │
│  │  │  │  - Resume frame capture                 │    │  │  │
│  │  │  └─────────────────────────────────────────┘    │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    HTTP/HTTPS (REST API)
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                    Backend Server                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FastAPI Application                      │   │
│  │                                                       │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  /api/ask_context Endpoint                     │   │   │
│  │  │  - Receive image + question                    │   │   │
│  │  │  - Validate input                              │   │   │
│  │  │  - Load image to memory                        │   │   │
│  │  │  - Get VLM service instance                    │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  │                     │                                  │   │
│  │                     ▼                                  │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  VLM Service (Vision Language Model)          │   │   │
│  │  │  - Load model (if not cached)                 │   │   │
│  │  │  - Preprocess image                           │   │   │
│  │  │  - Run inference                              │   │   │
│  │  │  - Generate text response                     │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  │                     │                                  │   │
│  │                     ▼                                  │   │
│  │  ┌────────────────────────────────────────────────┐   │   │
│  │  │  Response Formatter                           │   │   │
│  │  │  - Format answer text                         │   │   │
│  │  │  - Add metadata (processing time, etc)        │   │   │
│  │  │  - Encode as JSON                             │   │   │
│  │  └────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

### Voice Question Flow

```
User Action: Tap Mic Button
    │
    ▼
SpeechRecognitionService.startListening()
    │
    ├─ System: Request microphone permission
    │
    ├─ Show: "🎤 Listening..." indicator
    │
    ├─ Listen: For 30 seconds
    │  │
    │  ├─ Partial results: Update in real-time
    │  │
    │  └─ Final result: "What is ahead?"
    │
    ▼
User stops speaking OR 30 seconds elapsed
    │
    ▼
CameraScreen._stopVoiceQuestion()
    │
    ├─ Get recognized text
    │
    ├─ Validate non-empty
    │
    └─ Call: _askVLMQuestion(question)
           │
           ▼
      CameraScreen._askVLMQuestion()
           │
           ├─ Pause frame capture
           │
           ├─ Capture current frame
           │
           ├─ Call: ApiService.askContext(frame, question)
           │  │
           │  ▼
           │  Dio HTTP Client
           │  │
           │  ├─ Build multipart form data
           │  │  ├─ image: JPEG bytes
           │  │  └─ question: text string
           │  │
           │  ├─ POST to /api/ask_context
           │  │
           │  ▼
           │  Backend receives request
           │  │
           │  ├─ Load image from file upload
           │  │
           │  ├─ Get VLM service
           │  │
           │  ├─ Run inference
           │  │  │
           │  │  ├─ Image preprocessing
           │  │  │  ├─ Resize to model input size
           │  │  │  ├─ Normalize pixel values
           │  │  │  └─ Convert to tensor
           │  │  │
           │  │  ├─ Tokenize question
           │  │  │
           │  │  ├─ Forward pass through VLM
           │  │  │  ├─ Image encoder
           │  │  │  └─ Language model
           │  │  │
           │  │  └─ Decode response tokens to text
           │  │
           │  ├─ Format response
           │  │  ├─ Clean answer text
           │  │  ├─ Calculate processing time
           │  │  └─ Prepare metadata
           │  │
           │  └─ Return JSON response
           │
           ├─ Parse response
           │
           ├─ Extract answer text
           │
           ├─ Call: TtsService.speak(answer)
           │  │
           │  ├─ Initialize TTS engine (Flutter TTS plugin)
           │  │
           │  ├─ Set language/voice
           │  │
           │  └─ Play audio to speakers
           │
           ├─ Show: SnackBar with answer (5 seconds)
           │
           └─ Resume frame capture
                │
                ▼
           Back to continuous monitoring
```

## Class Diagrams

### Mobile App Classes

```
┌─────────────────────────────────────┐
│   SpeechRecognitionService          │
├─────────────────────────────────────┤
│ - _speechToText: SpeechToText       │
│ - _isListening: bool                │
│ - _recognizedText: String           │
├─────────────────────────────────────┤
│ + initialize(): Future<bool>        │
│ + startListening(): Future<void>    │
│ + stopListening(): Future<void>     │
│ + cancel(): Future<void>            │
│ + getRecognizedText(): String       │
│ + clearRecognizedText(): void       │
└─────────────────────────────────────┘

┌──────────────────────────────────────────┐
│   _CameraScreenState                     │
├──────────────────────────────────────────┤
│ - _isListeningToSpeech: bool             │
│ - _recognizedQuestion: String            │
│ - _isAskingVLM: bool                     │
│ - _speechRecognitionService: Service     │
├──────────────────────────────────────────┤
│ + _startVoiceQuestion(): Future<void>    │
│ + _stopVoiceQuestion(): Future<void>     │
│ + _askVLMQuestion(String): Future<void>  │
│ + _showQuestionSheet(): void             │
└──────────────────────────────────────────┘

┌─────────────────────────────────────┐
│   ApiService                        │
├─────────────────────────────────────┤
│ - _dio: Dio client                  │
│ - baseUrl: String                   │
├─────────────────────────────────────┤
│ + askContext(bytes, question)       │
│   : Future<Map<String, dynamic>?>   │
│ + analyzeImage(bytes)               │
│   : Future<ApiResponse?>            │
│ + checkHealth(): Future<bool>       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   TtsService                        │
├─────────────────────────────────────┤
│ - _flutterTts: FlutterTts           │
│ - language: String                  │
├─────────────────────────────────────┤
│ + speak(String): Future<void>       │
│ + speakAlert(AlertLevel, dist)      │
│ + setLanguage(String): void         │
│ + stop(): void                      │
└─────────────────────────────────────┘
```

### Backend Classes

```
┌──────────────────────────────────────┐
│   contextual_assistant.py            │
├──────────────────────────────────────┤
│ Router: /api/ask_context             │
├──────────────────────────────────────┤
│ @router.post("/ask_context")         │
│ async def ask_context(               │
│   image: UploadFile,                 │
│   question: str                      │
│ ) -> dict                            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│   VLMService                         │
├──────────────────────────────────────┤
│ - model: transformers.Model          │
│ - processor: transformers.Processor  │
│ - device: torch.device               │
├──────────────────────────────────────┤
│ + ask_context(image, question)       │
│   : tuple[str, dict]                 │
│ + preprocess(image)                  │
│ + generate(tokens)                   │
│ + postprocess(tokens)                │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│   ImageService                       │
├──────────────────────────────────────┤
│ + load_image(bytes)                  │
│ + validate_image()                   │
│ + resize(target_size)                │
│ + normalize(image)                   │
└──────────────────────────────────────┘
```

## Data Flow Diagrams

### Request Data Flow

```
Request JSON (from mobile):
{
  "image": <binary JPEG data>,
  "question": "What is ahead?",
  "use_cached_detections": true
}
    │
    ▼
Backend Processing:
1. Validate inputs
2. Decode image bytes
3. Load PIL Image
4. Preprocess for VLM
5. Tokenize question
6. Run model inference
7. Decode output tokens
8. Format response
    │
    ▼
Response JSON (to mobile):
{
  "success": true,
  "answer": "There is a red door...",
  "processing_time_ms": 2341,
  "metadata": {
    "model": "llava-v1.6-mistral-7b",
    "tokens_generated": 45,
    "confidence": 0.92
  }
}
```

### Response Data Flow

```
Backend Response
    │
    ▼
ApiService.askContext() parses JSON
    │
    ├─ Extract: answer string
    │
    ├─ Extract: processing_time_ms
    │
    ├─ Extract: metadata
    │
    └─ Return: Map<String, dynamic>
        │
        ▼
    _askVLMQuestion() receives response
        │
        ├─ Validate success flag
        │
        ├─ Get answer text
        │
        ├─ Call: TtsService.speak(answer)
        │  │
        │  └─ Audio output to speaker
        │
        └─ Call: ScaffoldMessenger.showSnackBar()
           │
           └─ Visual display on screen
```

## State Management

### VLM Question State Machine

```
┌─────────────────┐
│  Initial State  │
│  Ready to listen│
└────────┬────────┘
         │ User taps mic
         ▼
┌─────────────────────┐
│  Listening State    │
│  - Show indicator   │
│  - Record audio     │
│  - Accept speech    │
└────────┬────────────┘
         │ Speech ends or timeout
         ▼
┌─────────────────────┐
│  Processing State   │
│  - Parse speech     │
│  - Pause frames     │
│  - Capture frame    │
│  - Send to VLM      │
└────────┬────────────┘
         │ Response received
         ▼
┌─────────────────────┐
│  Response State     │
│  - Play TTS         │
│  - Show answer      │
│  - Resume frames    │
└────────┬────────────┘
         │ Complete
         ▼
┌─────────────────┐
│  Ready State    │
│  Listen again   │
└─────────────────┘

Error Handling:
Any state → Error State → Show message → Ready State
```

## Data Structures

### Request Format (MultipartForm)

```dart
FormData {
  'image': MultipartFile {
    data: Uint8List (JPEG bytes),
    filename: 'frame.jpg',
    contentType: 'image/jpeg'
  },
  'question': String ("What is ahead?"),
  'use_cached_detections': String ("true")
}
```

### Response Format (JSON)

```json
{
  "success": boolean,
  "answer": "string",
  "processing_time_ms": integer,
  "metadata": {
    "model": "string",
    "tokens_generated": integer,
    "confidence": float,
    "detected_objects": ["object1", "object2"]
  },
  "error": "optional error message"
}
```

## Concurrency Control

### Preventing Simultaneous Requests

```dart
// In _askVLMQuestion()
if (_controller == null || _isAskingVLM) {
  // Already processing or controller null
  return;
}

setState(() => _isAskingVLM = true);
try {
  // Process request
} finally {
  setState(() => _isAskingVLM = false);
}

// In _startVoiceQuestion()
if (_isListeningToSpeech || _isAskingVLM) {
  // Already listening or processing
  return;
}
```

## Frame Capture Management

### Pause/Resume Mechanism

```
Normal Operation:
Frame Capture Timer (every 1000ms at 1 FPS)
├─ Capture image
├─ Send to /api/analyze
└─ Continue loop

When VLM Question Received:
1. Cancel frame timer: _frameTimer?.cancel()
2. Wait 150ms: await Future.delayed()
3. Capture question frame safely
4. Send to /api/ask_context
5. Restart frame timer: _startFrameCapture()

Benefits:
- Prevents simultaneous camera access
- Avoids resource conflicts
- Ensures clean frame for VLM
- Resumes monitoring automatically
```

## Error Recovery Strategies

```
┌─────────────────┐
│  STT Error      │ → Show "Mic not available"
└─────────────────┘

┌─────────────────┐
│  Network Error  │ → Retry with exponential backoff
└─────────────────┘    (1s, 2s, 4s)

┌─────────────────┐
│  VLM Error      │ → Show "Server error"
└─────────────────┘    → Try again button

┌─────────────────┐
│  TTS Error      │ → Log error
└─────────────────┘    → Show text instead

┌─────────────────┐
│  Timeout        │ → Resend request
└─────────────────┘    → Show spinner
```

## Performance Optimization Points

### Mobile
- **Async Operations**: All I/O non-blocking
- **Image Compression**: JPEG at 85% quality
- **Memory Management**: Dispose resources properly
- **UI Updates**: Minimal rebuilds with Provider
- **Frame Rate**: Configurable (0.5-5 FPS)

### Backend
- **GPU Acceleration**: CUDA for inference
- **Model Caching**: Load once, reuse
- **Batch Processing**: Support multiple concurrent
- **Response Caching**: Cache similar questions
- **Efficient Loading**: Use transformers pipeline

## Security Measures

```
Mobile App:
├─ Permission verification before STT
├─ Input validation (non-empty question)
├─ HTTPS for API calls (configurable)
├─ No audio caching
├─ Clean sensitive data

Backend:
├─ Input validation (image format, size)
├─ Output sanitization (remove HTML/scripts)
├─ Rate limiting (optional)
├─ Authentication tokens (optional)
├─ Secure model loading
├─ No image persistent storage
```

## Scalability Considerations

```
Single Instance:
├─ Supports ~5-10 concurrent requests
├─ ~2-3 second response time per request
└─ Memory: ~2GB for VLM model

Multiple Instances:
├─ Load balancer
├─ Request queue
├─ Model server (separate process)
└─ Shared cache (Redis)

Optimization Path:
Small VLM → Medium VLM → Large VLM
└─ Fast (but less accurate)
    └─ Balanced (recommended)
        └─ Accurate (but slower)
```

---

**Version**: 1.0.0
**Last Updated**: 2024
**Status**: Complete & Documented
