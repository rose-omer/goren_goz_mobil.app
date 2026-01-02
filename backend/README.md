# Gören Göz Mobil - Backend API

FastAPI backend for real-time depth estimation and collision detection.

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip

### Installation

1. **Clone and navigate:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment:**
```bash
copy .env.example .env
# Edit .env with your settings
```

### Running the Server

**Development:**
```bash
python main.py
```

**Production (with Uvicorn):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Production (with Gunicorn + Uvicorn):**
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Server will start at: http://localhost:8000

API Documentation: http://localhost:8000/docs

## 📡 API Endpoints

### POST /api/analyze
Analyze image for depth estimation and collision detection.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body:
  - `image`: Image file (JPEG/PNG, max 10MB)
- Query Parameters:
  - `include_depth_image` (optional, default: false): Include depth visualization
  - `colormap` (optional, default: "JET"): Colormap name

**Response (200):**
```json
{
  "success": true,
  "timestamp": "2025-11-24T12:34:56.789Z",
  "processing_time_ms": 234.5,
  "data": {
    "alert_level": "DANGER",
    "distance_stats": {
      "min": 0.45,
      "max": 4.8,
      "avg": 2.1
    },
    "warnings": [
      {
        "message": "DANGER! Object detected at 0.45m",
        "level": "DANGER",
        "distance": 0.45,
        "area_percentage": 12.3
      }
    ],
    "depth_image_base64": "data:image/jpeg;base64,..."
  }
}
```

### GET /health
Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": 1732450896.789,
  "environment": "development",
  "model": {
    "loaded": true,
    "type": "MiDaS_small"
  },
  "version": "1.0.0"
}
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t goren-goz-backend .
```

### Run Container
```bash
docker run -d \
  --name goren-goz-api \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DEBUG=False \
  goren-goz-backend
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=False
    restart: unless-stopped
```

## 🌐 Cloud Deployment

### Render.com (Recommended - Free Tier Available)

1. Create new Web Service
2. Connect GitHub repository
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env`

### Railway

1. Create new project
2. Deploy from GitHub
3. Railway auto-detects Python
4. Add environment variables

### AWS EC2

1. Launch t2.medium instance (minimum for PyTorch)
2. SSH and clone repo
3. Install dependencies
4. Run with systemd service:

```ini
[Unit]
Description=Gören Göz Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/backend
ExecStart=/home/ubuntu/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## ⚙️ Configuration

### Environment Variables (.env)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `ENVIRONMENT`: development/production
- `DEBUG`: Enable debug mode (True/False)
- `CORS_ORIGINS`: Comma-separated allowed origins
- `RATE_LIMIT`: Requests per second limit
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)

### config.yaml
Model and alert settings are loaded from `../config/config.yaml`.

See main project README for configuration details.

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest

# With coverage
pytest --cov=.
```

## 📊 Performance

**Target Metrics:**
- Response time: < 500ms (MiDaS inference + encoding)
- Throughput: 5 requests/second/client
- Model loading: ~3-5 seconds (first request)

**Optimization Tips:**
1. Use `MiDaS_small` model for faster inference
2. Resize images to 640x480 before processing
3. Enable GPU with CUDA if available
4. Increase Uvicorn workers based on CPU cores

## 🔒 Security

- Rate limiting: 5 requests/second per IP
- File size limit: 10MB
- Input validation with Pydantic
- CORS configuration for production
- No authentication (add JWT/API keys for production)

## 📝 License

Part of Gören Göz Mobil project.
MIT License.

## 🤝 Support

For issues and questions, see main project repository.
