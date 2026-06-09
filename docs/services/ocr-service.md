# OCR Service

The OCR service extracts text from images using pluggable backends. It uses a Redis queue for async processing with callback notifications, and validates results via configurable minimum-character thresholds.

## Quick Reference

| | |
|---|---|
| **Port** | 7031 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-ocr-service/` |
| **Framework** | FastAPI + Uvicorn |
| **Tier** | 3 - Specialized |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/providers` | List available OCR backends |
| `POST` | `/v1/ocr` | Submit an image for OCR (queued async) |
| `GET` | `/v1/ocr/jobs/{job_id}` | Check job status and retrieve result |
| `POST` | `/v1/ocr/batch` | Submit multiple images in one request |
| `GET` | `/v1/queue/status` | Queue depth and worker status |

## Backends

| Backend | Platform | Notes |
|---------|----------|-------|
| Tesseract | All | Classic OCR, no GPU required |
| EasyOCR | All | Deep learning, GPU optional |
| PaddleOCR | Linux | Best accuracy on dense text, GPU recommended |
| RapidOCR | All | Fast CPU-based inference |
| LLM Proxy Vision | All | Routes to jarvis-llm-proxy-api vision endpoint |
| LLM Proxy Cloud | All | Routes to a cloud vision API via the LLM proxy REST backend |

The active backend is selected at runtime via settings. Multiple backends can be enabled simultaneously; the `tier` configuration controls fallback order.

## Environment Variables

### Core

| Variable | Description |
|----------|-------------|
| `OCR_PORT` | API port (default `7031`) |
| `OCR_BACKEND` | Default OCR backend (`tesseract`, `easyocr`, `paddleocr`, `rapidocr`, `llm_proxy_vision`, `llm_proxy_cloud`) |
| `OCR_ENABLED_TIERS` | Comma-separated list of enabled backend tiers |
| `OCR_ENABLE_RAPIDOCR` | Enable RapidOCR backend (`false`) |
| `OCR_ENABLE_LLM_PROXY_VISION` | Enable LLM Proxy Vision backend (`false`) |
| `OCR_ENABLE_LLM_PROXY_CLOUD` | Enable LLM Proxy Cloud backend (`false`) |
| `OCR_PUBLIC_URL` | Publicly reachable URL for this service (used in callback URLs) |

### Result Validation

| Variable | Description |
|----------|-------------|
| `OCR_MAX_TEXT_BYTES` | Maximum text size returned per job |
| `OCR_MIN_VALID_CHARS` | Minimum characters for a result to be considered valid |
| `OCR_LANGUAGE_DEFAULT` | Default language hint (e.g. `en`) |
| `OCR_MAX_ATTEMPTS` | Retry attempts per job before failing |
| `OCR_VALIDATION_MODEL` | LLM model used for result validation (when enabled) |

### Redis (async queue)

| Variable | Description |
|----------|-------------|
| `REDIS_URL` | Full Redis connection URL (takes precedence over host/port/password) |
| `REDIS_HOST` | Redis host (default `localhost`) |
| `REDIS_PORT` | Redis port (default `6379`) |
| `REDIS_PASSWORD` | Redis password |

### S3/MinIO (optional artifact storage)

| Variable | Description |
|----------|-------------|
| `S3_ENDPOINT_URL` | S3-compatible endpoint (e.g. MinIO URL) |
| `S3_REGION` | S3 region |
| `S3_FORCE_PATH_STYLE` | Use path-style S3 URLs (required for MinIO) |

### Auth

| Variable | Description |
|----------|-------------|
| `JARVIS_AUTH_BASE_URL` | Auth service URL |
| `JARVIS_APP_ID` | App identity for service-to-service auth |
| `JARVIS_APP_KEY` | App key for service-to-service auth |

## Dependencies

- **OCR engine** -- one or more of: Tesseract, EasyOCR, PaddleOCR, RapidOCR
- **Redis** -- async job queue
- **jarvis-auth** -- app-to-app auth validation
- **jarvis-logs** -- structured logging
- **jarvis-settings-client** -- runtime backend selection
- **jarvis-llm-proxy-api** -- optional vision inference backend

## Dependents

- **jarvis-recipes-server** -- sends recipe images for text extraction
- **jarvis-command-center** -- optional OCR for image-based commands

## Impact if Down

No image-to-text extraction. Recipe image scanning and any image-based command processing will fail. Text-based workflows are unaffected.
