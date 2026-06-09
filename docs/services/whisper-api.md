# Whisper API

The Whisper API provides speech-to-text transcription via whisper.cpp. It supports speaker identification through voice profile enrollment, returning both the transcribed text and a speaker confidence score.

## Quick Reference

| | |
|---|---|
| **Port** | 7706 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-whisper-api/` |
| **Framework** | FastAPI + Uvicorn |
| **Backend** | whisper.cpp |
| **Tier** | 3 - Specialized |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ping` | Simple liveness probe |
| `GET` | `/health` | Health check |
| `POST` | `/transcribe` | Transcribe audio to text |
| `POST` | `/api/v0/voice-profiles/enroll` | Enroll a voice profile for speaker ID |
| `GET` | `/api/v0/voice-profiles` | List enrolled voice profiles |
| `DELETE` | `/api/v0/voice-profiles/{id}` | Delete a voice profile |
| `*` | `/settings/*` | Settings CRUD (see Settings Server) |

## Transcription

The `/transcribe` endpoint accepts a WAV file upload. Optional query parameters tune accuracy and preprocessing:

| Query Parameter | Default | Description |
|----------------|---------|-------------|
| `prompt` | — | Initial text to guide transcription style |
| `preprocess` | `false` | Apply audio normalization and silence trimming before transcription |
| `temperature` | `0.0` | Initial sampling temperature (0.0–1.0). `0` = greedy decoding |
| `temperature_inc` | `0.2` | Temperature increment on decode failure |
| `beam_size` | `5` | Beam size for beam search (1–16) |

The response always includes a `speaker` field. Speaker identification is only populated when `USE_VOICE_RECOGNITION=true`:

```json
{
  "text": "what's the weather like",
  "speaker": {
    "user_id": 1,
    "confidence": 0.87
  }
}
```

When speaker recognition is disabled, `user_id` is `null` and `confidence` is `0.0`.

The command center uses the speaker result to resolve display names and load user-specific memories.

## Speaker Identification

Voice profiles are enrolled as WAV samples. The service uses [resemblyzer](https://github.com/resemble-ai/Resemblyzer) for speaker embedding comparison.

!!! warning "Latency"
    Resemblyzer on CPU adds 5–9 s per transcription request. On CUDA it is under 1 s. Use the GPU Docker image (`docker-compose.gpu.yaml`) if speaker ID latency matters.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | API port (default `7706`) |
| `WHISPER_MODEL` | Path to the whisper.cpp GGML model file (e.g. `~/whisper.cpp/models/ggml-base.en.bin`) |
| `WHISPER_CLI` | Path to the `whisper-cli` binary — auto-detected from `PATH` if unset |
| `WHISPER_ENABLE_CUDA` | Enable CUDA acceleration for the whisper.cpp build (`false`) |
| `USE_VOICE_RECOGNITION` | Enable speaker identification via resemblyzer (`false`) |
| `JARVIS_VOICE_DEVICE` | Device for the speaker-recognition encoder: `auto`, `cpu`, or `cuda` (default `auto`) |
| `JARVIS_APP_ID` | App identity for service-to-service auth (default `jarvis-whisper`) |
| `JARVIS_APP_KEY` | App key for service-to-service auth |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for validating incoming requests |
| `JARVIS_AUTH_CACHE_SUCCESS_TTL` | Auth validation success cache TTL in seconds (default `300`) |
| `JARVIS_AUTH_CACHE_FAILURE_TTL` | Auth validation failure cache TTL in seconds (default `60`) |
| `JARVIS_LOG_CONSOLE_LEVEL` | Console log level (default `INFO`) |
| `JARVIS_LOG_REMOTE_LEVEL` | Remote log level sent to jarvis-logs (default `DEBUG`) |

## Dependencies

- **whisper.cpp** -- speech-to-text engine
- **resemblyzer** -- speaker identification (optional, install via `pip install .[speaker]`)
- **jarvis-auth** -- validates node and app credentials
- **jarvis-logs** -- structured logging

## Dependents

- **jarvis-command-center** -- sends audio for transcription

## Impact if Down

Speech-to-text transcription is unavailable. If the command center uses server-side transcription (rather than on-device), voice input cannot be processed. Text-based commands still work.
