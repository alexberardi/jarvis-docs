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
| `GET` | `/health` | Health check |
| `POST` | `/v1/audio/transcriptions` | Transcribe audio to text |
| `POST` | `/api/v0/voice-profiles/enroll` | Enroll a voice profile for speaker ID |
| `GET` | `/api/v0/voice-profiles` | List enrolled voice profiles |
| `DELETE` | `/api/v0/voice-profiles/{id}` | Delete a voice profile |

## Speaker Identification

Whisper returns transcription results with speaker metadata:

```json
{
  "text": "what's the weather like",
  "speaker": {
    "user_id": 1,
    "confidence": 0.87
  }
}
```

The command center uses this to resolve display names and load user-specific memories.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WHISPER_MODEL_PATH` | Path to the whisper.cpp model file |
| `JARVIS_AUTH_BASE_URL` | Auth service URL for node validation |

## Dependencies

- **whisper.cpp** -- speech-to-text engine
- **jarvis-auth** -- validates node credentials
- **jarvis-logs** -- structured logging

## Dependents

- **jarvis-command-center** -- sends audio for transcription

## Impact if Down

Speech-to-text transcription is unavailable. If the command center uses server-side transcription (rather than on-device), voice input cannot be processed. Text-based commands still work.
