# OlaiSearch — Backend Dockerfile (multi-stage build)
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
        tesseract-ocr tesseract-ocr-tam tesseract-ocr-san tesseract-ocr-mal \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY . .

# Pre-build FAISS index if sentence-transformers is available
RUN python -c "from backend.retrieval.hybrid import HybridRetriever; print('Ready')" || true

# ─── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///olaisearch.db \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

COPY --from=builder /app /app
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu 2>/dev/null || true
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
