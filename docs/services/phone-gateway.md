# Phone Gateway

The phone gateway is the Twilio-facing worker for outbound phone calls (`jarvis/prds/phone-calls.md`, P1). It holds the Twilio credentials and the live media pipeline; jarvis-command-center never touches Twilio directly and only talks to this service over the internal contract in [session_client.py](#gateway-contract-with-command-center).

Added across jarvis-phone-gateway#1–#7 (foundation, live call loop, dev tooling, call-quality fixes) alongside the CC-side implementation in [Command Center: Phone Calls](command-center.md#phone-calls).

## Quick Reference

| | |
|---|---|
| **Port** | 7713 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-phone-gateway/` |
| **Framework** | FastAPI + Uvicorn (`python:3.11-slim`, digest-pinned) |
| **Image** | `ghcr.io/alexberardi/jarvis-phone-gateway` |
| **Tier** | 3 — Specialized (optional) |

`uvicorn[standard]` (not bare `uvicorn`) is required — `wsproto` is load-bearing for the Twilio media-stream WebSocket upgrade; without it the upgrade 404s.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | — | Health check. Reports `signature_validation` (Twilio request-signature enforcement posture). |
| `WS`  | Twilio media-stream WS (token in the URL) | Single-use session token, minted by the dial worker | Twilio's bidirectional audio stream for one call. Rejects unknown/reused tokens before `ws.accept()`. |
| `POST` | `/internal/call/{session_id}/escalation-answer` | app | CC forwards the household's answer into the live call's open escalation window (404 if no runtime, 409 if no window is open). |
| `POST` | `/internal/call/{session_id}/cancel` | app | CC-initiated termination (reaper, gate toggled off, user cancel). Requests hangup on the media session and, if dialed, ends the call via Twilio REST. |
| `POST` | `/internal/lookup/line-type` | app | Twilio Lookup v2 proxy for CC's number-resolve step — Twilio creds never leave the gateway. Degrades to `unknown` on lookup failure. |

`app` auth is validated by `services/app_auth.py` — a round-trip to jarvis-auth, fail-closed, with a 60 s cache.

## Call Lifecycle

1. **Dial worker** (`services/dial_worker.py`) pops a job from the Redis `phone:dial` list, `GET`s the session from CC, and performs a **claim CAS** against CC — a losing race (`409`) drops the job silently since another worker already claimed it.
2. Mints a single-use WSS session token, pre-synthesizes the compliance disclosure (see below), builds TwiML pointing at the media-stream WS, and calls Twilio `calls.create`.
3. Waits up to 60 s for the stream to start; no answer → REST hangup + an honest `failed` outcome reported to CC.
4. While live: heartbeats to CC at ≤30 s intervals plus a `max_call_seconds` watchdog (belt to CC's own reaper, which is suspenders).
5. **Turn pipeline** (`services/turn_pipeline.py`) drives each turn: whisper `/transcribe` (linear-PCM WAV) → llm-proxy live-streamed (think-strip → tool-token parse → sentence regroup) → per-sentence TTS through a content-type guard → 8 kHz PCM back to Twilio. Turn events are fire-and-forget to CC so a down CC never adds voice latency.
6. Tool tokens parsed from the LLM stream: `[HANGUP]` ends gracefully, `[ESCALATE:]` opens a bounded ~25 s window (`services/escalation.py`; timeout → "I'll check and call you back" + graceful end), `[OUTCOME:]` accumulates for wrapup, `[DTMF:]` is parsed and ignored until P2.
7. **Wrapup**: background-model call summary (honest fallback if summarization fails), recording upload, outcome + `done` reported to CC.

## Compliance Disclosure

The AI-and-recording disclosure (`services/prompt.py`) is always the call's first agent turn and is **never skippable**. It is pre-synthesized during dialing (prewarm); if TTS cannot produce it, the dial worker marks the session `failed` and never dials. The system prompt also encodes: honest "is this a robot" answers, hang-up-on-request, and a hard no on collecting payment data.

## Recording

`services/recording.py` mixes the two call directions (inbound-clocked) into an 8 kHz WAV and uploads it to MinIO/S3 (the same object-store env surface as jarvis-llm-proxy-api). Upload failure degrades to an audio-less outcome rather than failing the call. **Notice-off sessions never construct a recorder at all** — their turn events carry timings only, no audio.

## Gateway Contract with Command Center

`services/session_client.py` matches `jarvis-command-center`'s `/internal/phone/*` endpoints shape-for-shape: session snapshot fetch, `claim_dial` CAS (single winner; `409` = drop), state transitions through one choke point, and turn/heartbeat/escalation/outcome events. See [Command Center: Phone Calls](command-center.md#phone-calls) for the CC side of this contract.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SERVER_HOST` / `SERVER_PORT` | Bind address (default `0.0.0.0:7713`) |
| `PUBLIC_URL` | Public HTTPS base of this worker (named Cloudflare tunnel hostname — never a quick tunnel). Source for both the TwiML wss URL and the Twilio signature check. |
| `PUBLIC_WSS_URL` | Optional explicit wss base for TwiML; defaults to `PUBLIC_URL` with `https→wss`. |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_FROM_NUMBER` | Twilio credentials, held only by this service |
| `RUN_DIAL_WORKER` | Start the dial worker at boot (default `true`). Set `false` for media-only workers (chat-only deployments run without Redis). |
| `REDIS_URL` | Redis connection for the `phone:dial` queue — dial worker refuses to start without a reachable Redis |
| `VAD_RMS` | Voice-activity-detection RMS threshold (default `250`) |
| `JARVIS_AUTH_URL` | jarvis-auth base URL, for app-to-app auth on `/internal/*` (default `http://localhost:7701`) |
| `JARVIS_CONFIG_URL`, `JARVIS_APP_ID`, `JARVIS_APP_KEY` | Config-service discovery + app identity |
| `CC_BASE_URL` | jarvis-command-center base URL |
| `WHISPER_URL` | jarvis-whisper-api base URL |
| `LLM_URL` | jarvis-llm-proxy-api base URL |
| `TTS_URL` | jarvis-tts base URL |
| `S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_FORCE_PATH_STYLE`, `S3_REGION`, `PHONE_CALLS_BUCKET` | Recording storage (MinIO/S3), same surface as jarvis-llm-proxy-api |

Service URLs (`CC_BASE_URL`, `WHISPER_URL`, `LLM_URL`, `TTS_URL`) are overridden by config-service discovery when `jarvis-config-client` is installed; the env values are the fallback.

## Dependencies

- **jarvis-command-center** — session/claim/state/turn/escalation/outcome contract (see above)
- **jarvis-whisper-api** — `/transcribe` for the live turn pipeline
- **jarvis-llm-proxy-api** — streamed intent/response generation, and the recording object-store env surface
- **jarvis-tts** — per-sentence speech synthesis
- **jarvis-auth** — app-to-app auth for `/internal/*`
- **jarvis-config-service** — service discovery (optional; env URLs are the fallback)
- **jarvis-log-client** — structured logging (optional; falls back to stdlib logging)
- **Redis** — `phone:dial` job queue (dial worker only; the media/health surface works without it)
- **MinIO/S3** — recording storage
- **Twilio** — telephony provider (calls, media streams, Lookup v2)

## Dependents

- **jarvis-command-center** — the `make_phone_call` server tool dials through this service (see [Command Center: Phone Calls](command-center.md#phone-calls))

## Impact if Down

No outbound phone calls can be placed or continued. `make_phone_call` in command-center still drafts and confirms plans (the confirm-tap enqueues to Redis), but the dial worker never picks up the job, so calls never actually dial — sessions age out via CC's reaper. Nothing else in the voice/command pipeline depends on this service.
