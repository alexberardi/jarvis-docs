# OCR Service

The OCR service extracts text from images using pluggable backends: Tesseract, EasyOCR, PaddleOCR, and Apple Vision (macOS only). It supports async processing via a Redis queue with callback notifications.

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
| `POST` | `/api/v0/ocr` | Submit an image for OCR (sync) |
| `POST` | `/api/v0/ocr/async` | Submit an image for async OCR processing |
| `GET` | `/api/v0/ocr/status/{job_id}` | Check async job status |

## Platform Behavior

| Platform | Available Backends |
|----------|-------------------|
| macOS (Apple Silicon) | Apple Vision, Tesseract, EasyOCR |
| Linux | Tesseract, EasyOCR, PaddleOCR |

On macOS, this service runs **locally** (not in Docker) to access Apple Vision frameworks.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OCR_BACKEND` | Default OCR backend (`tesseract`, `easyocr`, `paddleocr`, `apple_vision`) |
| `REDIS_URL` | Redis connection for async job queue |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |

## Dependencies

- **OCR engine** -- one of Tesseract, EasyOCR, PaddleOCR, or Apple Vision
- **Redis** -- async job queue
- **jarvis-auth** -- app-to-app auth validation
- **jarvis-logs** -- structured logging
- **jarvis-settings-client** -- runtime backend opt-in settings

## Dependents

- **jarvis-recipes-server** -- sends recipe images for text extraction
- **jarvis-command-center** -- optional OCR for image-based commands

## Impact if Down

No image-to-text extraction. Recipe image scanning and any image-based command processing will fail. Text-based workflows are unaffected.
