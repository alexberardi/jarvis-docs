# TTS

The TTS (text-to-speech) service converts text responses into audio and streams them to nodes over HTTP. It supports multiple synthesis backends through a provider abstraction: **Piper** (default, baked-in, robotic but fast) and **Kokoro** (82M-param Apache 2.0 model, natural prosody, weights downloaded on first use). The active provider is selected at runtime via a setting.

The service can also generate contextual wake word responses by calling the LLM proxy.

## Quick Reference

| | |
|---|---|
| **Port** | 7707 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-tts/` |
| **Framework** | FastAPI + Uvicorn |
| **Providers** | Piper (default), Kokoro |
| **Tier** | 3 — Specialized |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/ping` | — | Simple liveness probe |
| `GET`  | `/health` | — | Health check |
| `GET`  | `/audio/format` | app | Current provider's audio format (sample rate, width, channels) |
| `POST` | `/speak` | app | Synthesize text, return full WAV audio |
| `POST` | `/speak/stream` | app | Stream raw 16-bit PCM as it is synthesized (low latency). Format metadata in `X-Audio-*` response headers |
| `POST` | `/generate-wake-response` | app | **Deprecated.** Generate a wake-word greeting via the LLM proxy. New nodes should call `POST /api/v0/wake-response` on jarvis-command-center instead. |
| `*`    | `/settings/*` | — | Settings CRUD (see Settings Server) |

`/speak/stream` is the preferred endpoint for nodes — the node's `play_pcm_stream()` reads the `X-Audio-Sample-Rate`, `X-Audio-Channels`, and `X-Audio-Sample-Width` headers and pipes the raw PCM to `aplay`, so the node works with any provider regardless of sample rate.

## Provider Selection

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tts.provider` | string | `piper` | Active backend: `piper` or `kokoro` |
| `tts.default_voice` | string | `en_GB-alan-low` | Piper ONNX voice file name (looked up in `app/models/`) |
| `tts.kokoro_voice` | string | `bm_george` | Kokoro voice ID. Notable British male options: `bm_george`, `bm_fable`, `bm_daniel`, `bm_lewis` |
| `tts.kokoro_speed` | float | `1.25` | Kokoro speech speed multiplier (validated natural-sounding default) |
| `tts.kokoro_device` | string | `cpu` | Kokoro inference device (`cpu` or `cuda`) |
| `tts.kokoro_gain` | float | `2.0` | Kokoro output gain — the primary loudness control |

Changes take effect within ~60 seconds (the settings service has a 60s cache). No container restart is required — the provider is rebuilt lazily on the next synthesis request. If the newly selected provider fails to load, the service logs a warning and falls back to Piper so voice responses never break.

### Comparing providers

| | Piper | Kokoro |
|---|---|---|
| Install | Baked into image | Optional (`pip install .[kokoro]`) |
| Model weights | ~15 MB, in image | ~300 MB, downloaded to `HF_HOME` on first use |
| Hardware | CPU only | CPU (~2–3× realtime) or GPU (fast) |
| Latency | Very low | ~550 ms time-to-first-audio |
| Quality | Robotic but intelligible | Natural prosody, especially on long text |
| Voice selection | Per-model files | Built-in multilingual catalog (see `VOICES.md` in hexgrad/kokoro) |

## Model Caching

Kokoro weights download lazily via `huggingface_hub` on first use. The Docker image mounts a named volume at `HF_HOME=/app/models/hf_cache` so weights persist across container restarts — otherwise each cold start re-downloads ~300 MB. The installer (jarvis-admin) and the `docker-compose.*.yaml` files in the service declare this volume (`jarvis-tts-hf-cache`).

## Native macOS Discovery

When run natively on macOS (outside Docker), the service reaches Dockerized peers like jarvis-auth via their host-published `localhost` ports rather than `host.docker.internal` (which a native process can't resolve). The native launchd plist sets `JARVIS_CONFIG_URL_STYLE=external` so config-service hands back `localhost` URLs — see [Service Discovery: URL Resolution](../architecture/service-discovery.md#url-resolution). This requires `jarvis-config-client` >= 0.2.1, the first version to honor the `external` style.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TTS_PORT` | API port (default 7707) |
| `TTS_PROVIDER` | Initial provider selection (also settable via `tts.provider`) |
| `HF_HOME` | Cache dir for Kokoro voice weights (default `/app/models/hf_cache`) |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |
| `JARVIS_APP_ID` | App identity for app-to-app auth (default `jarvis-tts`) |
| `JARVIS_APP_KEY` | App key for app-to-app auth |
| `JARVIS_LLM_PROXY_API_URL` | LLM proxy URL (for wake responses) |
| `JARVIS_CONFIG_URL` | Config service URL (for discovery) |
| `NODE_AUTH_CACHE_TTL` | Auth validation cache TTL (seconds) |

## Dependencies

- **Piper TTS** — default backend, baked into the image
- **Kokoro TTS** — optional backend, installed via the `kokoro` extra
- **jarvis-auth** — validates node and app credentials
- **jarvis-logs** — structured logging
- **jarvis-llm-proxy-api** — wake-response generation (optional)
- **jarvis-config-service** — service discovery (optional)

## Dependents

- **jarvis-node-setup** — Pi Zero nodes call `/speak/stream` for voice responses
- **jarvis-command-center** — requests TTS for voice responses

## Impact if Down

No voice responses from Jarvis. Nodes receive text-only responses (if the client supports it). Wake-word acknowledgment audio is unavailable. The service is not on the critical path — command processing continues to work; only audible output is lost.
