import cv2
import asyncio
import numpy as np
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path

from core.state import app_state

router = APIRouter()

# Setup templates structure
templates_dir = Path(__file__).parent.parent / "templates"
if not templates_dir.exists():
    templates_dir.mkdir(parents=True)

# Basic HTML template if file doesn't exist
DEFAULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Gören Göz - Debug Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #1a1a1a; color: white; margin: 0; padding: 20px; }
        .container { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
        .panel { background: #2d2d2d; padding: 10px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h2 { margin-top: 0; border-bottom: 1px solid #444; padding-bottom: 10px; }
        img { width: 100%; max-width: 640px; border-radius: 4px; background: #000; }
        .stats { margin-top: 10px; font-family: monospace; font-size: 14px; color: #aaa; }
    </style>
</head>
<body>
    <h1>👁️ Gören Göz - Canlı İzleme Paneli</h1>
    <div class="container">
        <div class="panel">
            <h2>📷 Kamera / YOLO</h2>
            <img src="/api/stream/video_feed" alt="Video Feed">
        </div>
        <div class="panel">
            <h2>📏 Derinlik Haritası</h2>
            <img src="/api/stream/depth_feed" alt="Depth Feed">
        </div>
    </div>
</body>
</html>
"""

async def video_generator():
    """Generator for video feed (MJPEG)"""
    while True:
        try:
            snapshot = app_state.get_snapshot()
            frame = snapshot.get('frame')
            
            if frame is None:
                # Return black frame if no data
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Waiting for stream...", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Draw YOLO detections if available
            analysis = snapshot.get('analysis', {})
            objects = analysis.get('objects', [])
            
            if objects:
                for obj in objects:
                    # Get bbox (x1, y1, x2, y2)
                    bbox = obj.get('bbox')
                    if not bbox:
                        continue
                        
                    x1, y1, x2, y2 = map(int, bbox)
                    label = f"{obj.get('name', 'obj')} {obj.get('confidence', 0.0):.2f}"
                    
                    # Draw rectangle
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw label background
                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), (0, 255, 0), -1)
                    
                    # Draw text
                    cv2.putText(frame, label, (x1, y1 - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control framerate (~30/15 fps to save CPU)
            await asyncio.sleep(0.06)  # ~15 FPS
            
        except Exception as e:
            print(f"Stream error: {e}")
            await asyncio.sleep(1)

async def depth_generator():
    """Generator for depth feed (MJPEG)"""
    while True:
        try:
            snapshot = app_state.get_snapshot()
            depth = snapshot.get('depth')
            
            if depth is None:
                # Return black frame if no data
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Waiting for depth...", (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                # Normalize and colormap for visualization
                # Assuming depth is 0-1 float or close
                if depth.dtype != np.uint8:
                     depth_norm = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
                     depth_uint8 = depth_norm.astype(np.uint8)
                else:
                    depth_uint8 = depth
                
                # Apply colormap (Inferno/Magma looks good for depth)
                frame = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_INFERNO)

            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control framerate
            await asyncio.sleep(0.06)
            
        except Exception as e:
            print(f"Depth stream error: {e}")
            await asyncio.sleep(1)

@router.get("/video_feed")
async def video_feed():
    """Video streaming route."""
    return StreamingResponse(
        video_generator(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/depth_feed")
async def depth_feed():
    """Depth streaming route."""
    return StreamingResponse(
        depth_generator(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page"""
    # Simply return the HTML string for now (easiest integration)
    return HTMLResponse(content=DEFAULT_HTML)
