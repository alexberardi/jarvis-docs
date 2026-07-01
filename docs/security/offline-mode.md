# Network Egress & Offline Mode

Jarvis is **local-first**. Out of the box, a self-hosted deployment makes **no unsolicited connections to the public internet** — voice commands, transcription, speech, memory, and device control all happen on your own hardware.

Everything that *could* reach the public internet is gated behind a setting that **defaults to off**. Nothing leaves your network unless you explicitly opt in, or unless you install a command package or device family that talks to a third party by design.

!!! success "Default posture"
    A fresh install with default settings is effectively **offline**. The only outbound traffic is between your own Jarvis services (all discovered via `jarvis-config-service`) and your own infrastructure (PostgreSQL, Redis, MinIO, the MQTT broker, Loki). To reach the public internet, you turn on a specific capability below.

## Local vs. external

| Treated as **local** (always allowed) | Treated as **external** (opt-in) |
|---|---|
| Service-to-service calls discovered via config-service (localhost, `*.local`, private IPs, container names, `host.docker.internal`) | Vendor clouds (weather, music, smart-home clouds) |
| Self-hosted infra: PostgreSQL, Redis, MinIO/S3, Mosquitto (MQTT), Loki/Grafana | Push providers (Expo → Apple APNs / Firebase FCM) |
| A node talking to *your* command center (LAN or your own cloud-hosted CC) | Model/asset downloads (HuggingFace, GitHub releases) |
| LAN device families (Hue, Kasa, LIFX, Z-Wave, HomeKit) | Update checks (`api.github.com`) |
| | Third-party reader proxy (`r.jina.ai`) |

## Outbound egress toggles

Every switch below **defaults to off** (or to a local option). Turn one on only when you want that capability.

| Capability | Reaches | Setting | Where to set | Default |
|---|---|---|---|---|
| **Web search** (quick answers) | DuckDuckGo + fetched pages | `web_search.enabled` *(household)* | Mobile app → Household Settings (admin) | **off** |
| **External reader proxy** (deep-research fallback) | `r.jina.ai` | `web_scraping.allow_external` *(household)* | Mobile app → Household Settings (admin) | **off** |
| **Node update checks** | `api.github.com` | `updates.allow_check` *(command-center, global)* | Settings DB / settings server | **off** |
| **Node self-update (OTA)** | GitHub releases | `allow_updates` / `JARVIS_ALLOW_UPDATES` *(node)* | Node `config.json` or env | **off** |
| **Wake-word model download** | GitHub (openWakeWord) | `wake_word_model_autodownload_enabled` / `JARVIS_WAKE_WORD_MODEL_AUTODOWNLOAD_ENABLED` *(node)* | Node `config.json` or env | **off** |
| **Speech-to-text model download** | `huggingface.co` | `whisper.allow_model_autodownload` / `WHISPER_ALLOW_MODEL_AUTODOWNLOAD` *(whisper)* | Settings DB or env | **off** |
| **Text-to-speech engine** | `huggingface.co` (Kokoro) vs. local (Piper) | `tts.provider` / `TTS_PROVIDER` *(tts)* | Settings DB or env | **`piper` (local)** |
| **Admin auto-update** | `api.github.com` | `JARVIS_ALLOW_UPDATES` *(admin)* | Admin env / `~/.jarvis/admin.json` | **off** |
| **Mobile push notifications** | Expo (`exp.host`) → APNs/FCM | in-app toggle (`@jarvis/push_notifications_enabled`) | Mobile app → Settings | **off (opt-in)** |
| **Push delivery relay** | your relay → Expo | `RELAY_URL` *(notifications)* | `.env` | **unset (off)** |

!!! note "Scope of each toggle"
    - **Household** settings (`web_search.enabled`, `web_scraping.allow_external`) are set once by a household **admin** in the mobile app and apply to everyone in the household.
    - **Global** service settings (`updates.allow_check`, `whisper.*`, `tts.provider`) live in the settings database and apply to that service.
    - **Node** settings live in each node's `config.json` (or its environment) and apply to that device.
    - **Push** is per-device — each phone decides for itself and contacts Expo only after you opt in.

## Fully-offline checklist

To keep a deployment fully local:

1. Leave every toggle in the table above **off** (that is the default — you don't have to do anything).
2. Keep `tts.provider` = **`piper`** (the default). Piper is baked into the image and needs no download. Kokoro would fetch its weights from HuggingFace on first use.
3. Provide a **local Whisper model** and point `whisper.model_path` (or `WHISPER_MODEL`) at it, since `whisper.allow_model_autodownload` is off. With no local model and the gate off, transcription fails loudly with instructions rather than silently downloading one.
4. **Pre-stage the wake-word model** (or accept keyboard/fallback wake), since `wake_word_model_autodownload_enabled` is off. Installers that already ship the model need nothing further.
5. Do **not** set `RELAY_URL`, and leave mobile push disabled — no push payloads leave the device or the box.
6. Be aware that **installing a command package** (`jarvis-cmd-*`) or a **vendor-cloud device family** (e.g. Nest, Ecobee, Govee cloud) intentionally adds outbound traffic for that feature. Installing it is the opt-in.

!!! tip "Verifying"
    From the box, you can confirm the posture with a passive check like `sudo lsof -i -nP | grep ESTABLISHED` or your firewall/router logs — with everything above off, you should see only intra-network connections (your own services + infra), not connections to `github.com`, `huggingface.co`, `exp.host`, or `r.jina.ai`.

## Command packages & device families

- **Command packages** (`jarvis-cmd-weather`, `-news`, `-spotify`, …) are external integrations by nature. Installing one from the Pantry is your consent for the traffic it needs; the package's code runs on your node, not in the cloud.
- **LAN device families** (Hue, Kasa, LIFX, Z-Wave, HomeKit) stay entirely on your network.
- **Vendor-cloud device families** (e.g. Nest/Google, Govee cloud, Resideo, SimpliSafe) require the vendor's cloud to function. Choosing to add one is the opt-in.

## Enabling updates

Updates are off by default so a local-only box never phones home. Turn them on per surface:

=== "Node updates (OTA)"

    The node-update flow spans two services, so allow it in both places:

    1. **On the node** — allow the device to download and apply a release:

        ```json title="config.json"
        { "allow_updates": true }
        ```

        or set the environment variable:

        ```bash
        JARVIS_ALLOW_UPDATES=true
        ```

    2. **In command-center** — allow the version lookup that finds the latest release:

        ```
        updates.allow_check = true   # settings DB (global)
        ```

    **How it flows:** you trigger an update from the mobile app → command-center looks up the latest release on `api.github.com` (needs `updates.allow_check`) → the node downloads and applies it (needs `allow_updates`). Applying an **explicit** version to a node skips the GitHub lookup (no egress for the check), but the node still needs `allow_updates` to fetch the release.

=== "Admin dashboard self-update"

    The admin app has no household/JWT context at its update-check call site, so its gate is a box-level flag:

    ```bash
    JARVIS_ALLOW_UPDATES=true          # admin container environment
    ```

    or in `~/.jarvis/admin.json`:

    ```json
    { "allowUpdates": true }
    ```

    With it off, `/api/update/check` makes no request to `api.github.com` and `/api/update/apply` returns `403`.

!!! warning "Updates require internet"
    Enabling any update path allows outbound connections to GitHub (and, for the applied release, GitHub release assets). Leave these off if you want a fully air-gapped deployment and update manually instead.

## Where these settings live

- **Household & service settings** (`web_search.enabled`, `web_scraping.allow_external`, `updates.allow_check`, `whisper.*`, `tts.provider`) are runtime settings — change them via the **mobile app**, the **settings server API**, or the **settings database**. See [Configuration → Runtime Settings](../getting-started/configuration.md#runtime-settings).
- **Node settings** live in each node's `config.json` (or its environment).
- **Environment variables** (`JARVIS_ALLOW_UPDATES`, `JARVIS_WAKE_WORD_MODEL_AUTODOWNLOAD_ENABLED`, `WHISPER_ALLOW_MODEL_AUTODOWNLOAD`, `TTS_PROVIDER`) are documented in the [Environment Variables reference](../reference/env-vars.md#network-egress-offline-mode).

See also: [Cloud Services](../architecture/cloud.md) for the optional cloud components (Pantry, Relay, Web) and how they stay opt-in.
