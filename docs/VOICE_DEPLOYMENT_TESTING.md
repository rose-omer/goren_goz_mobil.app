# Voice Feature - Deployment & Testing Guide

## Pre-Deployment Checklist

### Code Review
- [ ] All code follows Dart style guide (Flutter)
- [ ] All code follows PEP 8 style (Python)
- [ ] No hardcoded credentials or sensitive data
- [ ] No debug print statements (use logger instead)
- [ ] No unused imports or variables
- [ ] Exception handling implemented for all I/O
- [ ] Comments added for complex logic
- [ ] Function/method documentation complete

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing on device completed
- [ ] All error scenarios tested
- [ ] Performance benchmarks acceptable
- [ ] Memory leak testing passed
- [ ] Crash testing completed

### Configuration
- [ ] API endpoints configured correctly
- [ ] Timeout values set appropriately
- [ ] Logging levels set for production
- [ ] Permission strings localized
- [ ] VLM model paths verified
- [ ] Backend environment variables set

### Dependencies
- [ ] All dependencies updated to stable versions
- [ ] No deprecated packages used
- [ ] Version constraints specified properly
- [ ] Lock files committed to version control
- [ ] License compliance verified

## Deployment Process

### Backend Deployment

#### Local Testing
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download/verify VLM model
# Model should be in backend/models/
ls -la backend/models/

# 4. Run tests
pytest tests/

# 5. Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 6. Test endpoint
curl -X POST http://localhost:8000/api/ask_context \
  -F "image=@test_image.jpg" \
  -F "question=What is in the image?"
```

#### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download models (optional, can be mounted)
# RUN python scripts/download_models.py

EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Cloud Deployment (AWS Example)
```bash
# 1. Build image
docker build -t goren-goz-backend:latest .

# 2. Tag for ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag goren-goz-backend:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/goren-goz-backend:latest

# 3. Push to ECR
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/goren-goz-backend:latest

# 4. Deploy to ECS/Fargate
# Use AWS console or CLI to create service

# 5. Set up load balancer
# Route API calls through ALB/NLB
```

#### Environment Variables
```bash
# .env (backend)
FLASK_ENV=production
VLM_MODEL_PATH=/models/llava-v1.6-mistral-7b
DEVICE=cuda
MAX_WORKERS=4
LOG_LEVEL=INFO
API_TIMEOUT=30
ENABLE_CACHING=true
CACHE_TTL=3600
```

### Mobile App Deployment

#### Android Release Build
```bash
# 1. Update version
cd mobile_app
# Edit pubspec.yaml: version: 1.0.0+1

# 2. Build APK
flutter build apk --release

# 3. Build AAB (for Play Store)
flutter build appbundle --release

# 4. Sign APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore ~/key.jks \
  build/app/outputs/apk/release/app-release.unsigned.apk \
  alias_name

# 5. Zipalign
zipalign -v 4 \
  app-release-unsigned.apk \
  app-release-signed.apk

# Output: build/app/outputs/apk/release/app-release.apk
```

#### iOS Release Build
```bash
# 1. Update version
# Edit ios/Runner/Info.plist and pubspec.yaml

# 2. Build iOS app
flutter build ios --release

# 3. Archive
cd ios
xcodebuild -workspace Runner.xcworkspace \
  -scheme Runner \
  -configuration Release \
  -archivePath build/Runner.xcarchive \
  archive

# 4. Export
xcodebuild -exportArchive \
  -archivePath build/Runner.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/ios/iphoneeos

# Output: iOS app ready for App Store
```

#### App Store Submission
```bash
# Android (Google Play)
1. Create app listing in Google Play Console
2. Upload APK/AAB
3. Add screenshots and descriptions
4. Set content rating
5. Submit for review (24-48 hours)

# iOS (Apple App Store)
1. Create app in App Store Connect
2. Upload via Xcode/Transporter
3. Add app information
4. Configure pricing
5. Submit for review (1-3 days)
```

## Testing Strategy

### Unit Testing

#### Backend (pytest)
```python
# tests/test_vlm_service.py
import pytest
from backend.services.vlm_service import VLMService

class TestVLMService:
    @pytest.fixture
    def vlm_service(self):
        return VLMService()
    
    def test_initialization(self, vlm_service):
        assert vlm_service.model is not None
        assert vlm_service.device is not None
    
    def test_ask_context(self, vlm_service):
        # Load test image
        image = Image.open('tests/test_image.jpg')
        question = "What is in this image?"
        
        # Get response
        answer, metadata = vlm_service.ask_context(image, question)
        
        # Assertions
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert 'processing_time_ms' in metadata
```

#### Frontend (flutter_test)
```dart
// test/services/speech_recognition_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/services/speech_recognition_service.dart';

void main() {
  group('SpeechRecognitionService', () {
    late SpeechRecognitionService service;

    setUp(() {
      service = SpeechRecognitionService();
    });

    test('initialization', () async {
      final result = await service.initialize();
      expect(result, isNotNull);
    });

    test('get recognized text', () {
      service.startListening();
      // Simulate speech...
      final text = service.getRecognizedText();
      expect(text, isNotEmpty);
    });
  });
}
```

### Integration Testing

#### Backend Integration
```python
# tests/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_ask_context_endpoint(client):
    with open('tests/test_image.jpg', 'rb') as image_file:
        response = client.post(
            '/api/ask_context',
            files={'image': image_file},
            data={'question': 'What is this?'}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert 'answer' in data
    assert 'processing_time_ms' in data
```

#### Frontend Integration
```bash
# Run integration tests
flutter drive \
  --target=test_driver/app.dart \
  --driver=test_driver/integration_test.dart
```

### Manual Testing

#### Test Cases

**Test 1: Basic Voice Recognition**
```
Steps:
1. Open app
2. Tap mic button
3. Speak: "What is ahead?"
4. Wait for response

Expected:
✓ Mic button turns red
✓ "Listening" indicator shown
✓ Text recognized correctly
✓ Response received
✓ TTS plays answer
✓ Mic button turns blue
```

**Test 2: No Speech Detected**
```
Steps:
1. Tap mic button
2. Stay silent for 3+ seconds
3. Wait for timeout

Expected:
✓ Listening stops
✓ "No speech detected" message
✓ Option to retry
✓ Mic button returns to normal
```

**Test 3: Simultaneous Requests**
```
Steps:
1. Tap mic button
2. While listening, tap question button

Expected:
✓ Question button disabled
✓ Only one request processed
✓ No crashes or errors
✓ Proper error message shown
```

**Test 4: Network Failure**
```
Steps:
1. Turn off internet
2. Tap mic button
3. Speak question
4. Wait for response

Expected:
✓ Error message: "Server unreachable"
✓ Option to retry
✓ App doesn't crash
✓ Can turn internet back on and retry
```

**Test 5: Frame Capture Consistency**
```
Steps:
1. Ask voice question
2. Monitor frame rate (should drop to 0)
3. Wait for response
4. Observe frame rate resume

Expected:
✓ Frame capture pauses
✓ VLM processes without conflict
✓ Frame capture resumes smoothly
✓ No frame drops or artifacts
```

**Test 6: Memory Management**
```
Steps:
1. Ask 20 voice questions rapidly
2. Monitor memory usage
3. Check for memory leaks

Expected:
✓ Memory stable (no growth > 50MB)
✓ No crashes
✓ Consistent response time
✓ GC handles cleanup
```

**Test 7: TTS Response**
```
Steps:
1. Ask question
2. Wait for response
3. Verify audio playback

Expected:
✓ Audio device initialized
✓ Response spoken clearly
✓ Correct language/voice
✓ Appropriate speed/volume
```

### Performance Testing

#### Response Time Benchmarks
```bash
# Backend response time (target: < 5 seconds)
python -m pytest tests/test_performance.py -v

Small model: 1-2 seconds
Medium model: 2-4 seconds
Large model: 4-6 seconds

# Mobile STT latency (target: < 2 seconds)
Flutter: measure in logs
```

#### Load Testing
```bash
# Using Apache JMeter or locust
locust -f tests/load_test.py --host=http://localhost:8000

# Test 10 concurrent users
# 10 requests/user
# Expected response time < 5s
```

#### Memory Profiling
```python
# tests/test_memory.py
from memory_profiler import profile

@profile
def test_vlm_inference():
    service = VLMService()
    image = Image.open('test_image.jpg')
    for i in range(10):
        answer, _ = service.ask_context(image, "What?")
    # Check memory growth
```

### Automated Testing Pipeline

#### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/
      - run: python -m pytest --cov=backend tests/

  test-mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: 3.0.0
      - run: cd mobile_app && flutter pub get
      - run: flutter test
```

## Monitoring & Logging

### Backend Logging
```python
# Configure logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.info('VLM service initialized')
logger.warning('Slow response: 4.5s')
logger.error('Model loading failed', exc_info=True)
```

### Mobile Logging
```dart
// Use AppLogger throughout app
AppLogger.info('Voice question: What is ahead?');
AppLogger.warning('STT not available');
AppLogger.error('VLM response timeout', exception);
```

### Metrics Collection
```python
# Prometheus metrics (optional)
from prometheus_client import Counter, Histogram

request_count = Counter('ask_context_requests_total', 'Total requests')
request_duration = Histogram('ask_context_duration_seconds', 'Request duration')

# In endpoint
@request_duration.time()
async def ask_context():
    request_count.inc()
    # Process request
```

### Alerting
```yaml
# Example alert rules (Prometheus)
groups:
  - name: goren-goz-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(ask_context_errors[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate in VLM service"
      
      - alert: SlowResponse
        expr: ask_context_duration_seconds > 10
        annotations:
          summary: "VLM response time exceeding threshold"
```

## Rollback Procedure

### If Issues Detected

```bash
# 1. Stop current deployment
docker stop goren-goz-backend

# 2. Revert to previous version
docker run -d --name goren-goz-backend \
  goren-goz-backend:previous-tag

# 3. Update DNS/load balancer
# Point traffic back to stable version

# 4. Investigate issue
# Check logs
tail -f container-logs

# 5. Fix and redeploy
# Make necessary fixes
# Build new image
# Test thoroughly
# Deploy again
```

## Maintenance Tasks

### Weekly
- [ ] Check server logs for errors
- [ ] Monitor error rates
- [ ] Verify backups working
- [ ] Check disk space

### Monthly
- [ ] Update dependencies
- [ ] Review performance metrics
- [ ] Update documentation
- [ ] Test disaster recovery

### Quarterly
- [ ] Security audit
- [ ] Load testing
- [ ] Model retraining (if needed)
- [ ] Capacity planning

## Troubleshooting Guide

| Issue | Symptom | Solution |
|-------|---------|----------|
| No response | Timeout | Restart backend, check GPU |
| Slow response | >10s latency | Reduce model size, enable quantization |
| Memory leak | Growing usage | Restart backend, check image handling |
| Crash on startup | Can't initialize | Verify model path, check CUDA |
| STT not working | "Not available" | Grant permissions, check mic |
| Network error | Can't reach backend | Verify API URL, check firewall |

## Release Notes Template

```markdown
# Release v1.1.0

## New Features
- Voice-based question asking
- Real-time speech recognition
- Automatic response playback
- Multi-language support (EN, TR)

## Bug Fixes
- Fixed frame capture timing
- Improved error handling
- Better memory management

## Performance
- 30% faster VLM inference (with GPU)
- 50% less memory usage
- 20% fewer network timeouts

## Security
- Added input validation
- Encrypted audio transmission
- User consent for recording

## Breaking Changes
None

## Migration Guide
No migration needed. Simply update app.

## Known Issues
- Large models slow on low-end devices
- Offline mode not yet supported

## Contributors
- Development Team
```

---

**Document Version**: 1.0.0
**Last Updated**: 2024
**Next Review**: 3 months
