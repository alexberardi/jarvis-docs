# TTS

The TTS (text-to-speech) service converts text responses into audio using Piper TTS. It delivers audio to nodes via MQTT or direct HTTP. It can also generate contextual wake word responses using the LLM proxy.

## Quick Reference

| | |
|---|---|
| **Port** | 7707 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-tts/` |
| **Framework** | FastAPI + Uvicorn |
| **Backend** | Piper TTS |
| **Tier** | 3 - Specialized |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v0/tts/synthesize` | Synthesize text to audio |
| `POST` | `/api/v0/tts/speak` | Synthesize and deliver to a node via MQTT |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PIPER_MODEL_PATH` | Path to the Piper TTS voice model |
| `MQTT_BROKER_HOST` | Mosquitto MQTT broker address |
| `MQTT_BROKER_PORT` | MQTT broker port |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |

## Dependencies

- **Piper TTS** -- speech synthesis engine
- **Mosquitto** -- MQTT broker for audio delivery to nodes
- **jarvis-auth** -- validates node and app credentials
- **jarvis-logs** -- structured logging
- **jarvis-llm-proxy-api** -- generates contextual wake word responses (optional)

## Dependents

- **jarvis-node-setup** -- Pi Zero nodes receive audio via MQTT or direct HTTP
- **jarvis-command-center** -- may request TTS for voice responses

## Impact if Down

No voice responses from Jarvis. Nodes receive text-only responses (if the client supports it). Wake word acknowledgment audio is unavailable.
