# Gören Göz backend imajı. Bağlam: backend/
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8110 \
    ENVIRONMENT=production \
    DEBUG=false

WORKDIR /app

# opencv-python-headless libGL istemez; OpenVINO ve torch için libgomp yeter.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY . .
RUN useradd --create-home app && mkdir -p logs model_files && chown -R app /app
USER app

EXPOSE 8110

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://127.0.0.1:8110/health').is_success else 1)"

# Tek worker: modeller bir kez belleğe girer; paralelliği thread havuzu sağlar (plan E8).
CMD ["sh", "-c", "uvicorn main:app --host ${HOST} --port ${PORT} --workers 1"]
