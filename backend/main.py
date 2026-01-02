"""
Gören Göz Mobil - FastAPI Backend
==================================

REST API server for real-time depth estimation and collision alerts.
Designed for mobile (Android/iOS) clients.

Endpoints:
    POST /api/analyze  - Analyze image and return depth map + alerts
    GET  /health       - Health check endpoint
    GET  /             - API documentation redirect

Author: Gören Göz Team
Version: 1.0.0
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import analyze, stream, contextual_assistant
from core.config import get_settings
from core.logger import setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 70)
    logger.info("🚀 Gören Göz Mobil Backend Starting...")
    logger.info("=" * 70)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"Rate Limit: {settings.rate_limit_per_second} requests/second")
    logger.info("=" * 70)
    
    # Preload AI model (optional - can be lazy loaded)
    try:
        from services.depth_service import get_depth_service
        depth_service = get_depth_service()
        logger.info("✓ MiDaS model preloaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Model preload failed: {e}")
        logger.info("Model will be loaded on first request")
    
    # Check VLM server (optional - will be lazy loaded if not available)
    try:
        from services.vlm_service import get_vlm_service
        vlm_config = settings.vlm if hasattr(settings, 'vlm') else {}
        vlm_server_url = vlm_config.get('server_url', 'http://localhost:8080')
        vlm_timeout = vlm_config.get('timeout', 60)
        vlm_service = get_vlm_service(
            server_url=vlm_server_url,
            timeout=vlm_timeout
        )
        is_ready = await vlm_service.is_server_ready()
        if is_ready:
            logger.info("✓ VLM server is ready")
        else:
            logger.warning("⚠️ VLM server not available - contextual features will be disabled")
    except Exception as e:
        logger.warning(f"⚠️ VLM service check failed: {e}")
        logger.info("VLM features will be available when server is started")
    
    yield
    
    # Shutdown
    logger.info("=" * 70)
    logger.info("🛑 Gören Göz Mobil Backend Shutting Down...")
    logger.info("=" * 70)


# Create FastAPI app
app = FastAPI(
    title="Gören Göz Mobil API",
    description="Real-time depth estimation and collision detection API for visually impaired users",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # Convert to ms
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    
    # Log slow requests
    if process_time > 1000:  # > 1 second
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}ms"
        )
    
    return response


# Include routers
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
app.include_router(stream.router, prefix="/api/stream", tags=["Stream"])
app.include_router(contextual_assistant.router, prefix="/api", tags=["Contextual Assistant"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


# VLM Test page
@app.get("/vlm-test", include_in_schema=False)
async def vlm_test():
    """Serve VLM test page."""
    import os
    static_path = os.path.join(os.path.dirname(__file__), "static", "vlm_test.html")
    return FileResponse(static_path)


# VLM Monitor page
@app.get("/monitor", include_in_schema=False)
async def monitor():
    """Serve VLM monitor page."""
    import os
    static_path = os.path.join(os.path.dirname(__file__), "static", "monitor.html")
    return FileResponse(static_path)

# Health check endpoint
@app.get("/health", tags=["Health"])
@limiter.limit("10/minute")
async def health_check(request: Request) -> Dict:
    """
    Health check endpoint.
    
    Returns system status, uptime, and model availability.
    """
    try:
        from services.depth_service import get_depth_service
        depth_service = get_depth_service()
        model_loaded = depth_service.is_loaded
    except Exception:
        model_loaded = False
    
    # Check VLM server status
    vlm_ready = False
    try:
        from services.vlm_service import get_vlm_service
        vlm_service = get_vlm_service()
        vlm_ready = await vlm_service.is_server_ready()
    except Exception:
        pass
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.environment,
        "model": {
            "loaded": model_loaded,
            "type": settings.model_type
        },
        "vlm": {
            "server_ready": vlm_ready,
            "server_url": "http://localhost:8080"
        },
        "version": "1.0.0"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        }
    )


if __name__ == "__main__":
    # Run with Uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        reload_dirs=["backend"],
        log_level=settings.log_level.lower()
    )
