# Network Egress & Offline Mode

Jarvis is **local-first**. A Jarvis Automation server with its default settings makes **no connections to the internet on its own**: voice commands, transcription, speech, memory and device control all run on your own hardware, and the server talks only to your own nodes, phones and devices.

Everything that reaches the internet is either something you start (downloading a model, running `jarvisd upgrade`) or a setting that **defaults to off**. One client setting is on by default: the desktop agent updates itself from GitHub releases (see [On nodes and phones](#on-nodes-and-phones)).

!!! success "Default posture"
    A fresh install with default settings is effectively **offline** once its models are downloaded. To reach the internet, you turn on a specific capability below.

## Local vs. external

| Treated as **local** (always allowed) | Treated as **external** (you opt in) |
|---|---|
| Nodes, phones and desktop agents on your network talking to your server ([ports](../operate/network.md)) | Model and runtime downloads (`huggingface.co`, GitHub releases) |
| mDNS announcements on your local network | Update checks (`api.github.com`) |
| LAN device families (Hue, Kasa, LIFX, Z-Wave, HomeKit) | Web search and the reader proxy (`r.jina.ai`) |
| The model runtimes the server starts on the same machine | Push providers (Expo → Apple APNs / Firebase FCM) |
| | The Pantry package store, vendor clouds, cloud model providers |

## What can reach the internet

### Settings that are off by default

Change these in the admin web app (**Settings**), or household settings in the mobile app as a household admin.

| Capability | Reaches | Setting (scope) |
|---|---|---|
| **Server update checks** | `api.github.com`, GitHub releases | `updates.enabled` (server; or `JARVIS_ALLOW_UPDATES` in `jarvisd.env`) |
| **Node update checks** | `api.github.com` | `updates.allow_check` (server) |
| **Web search** (quick answers, deep research) | DuckDuckGo and the pages it finds | `web_search.enabled` (household) |
| **External reader proxy** (deep-research fallback) | `r.jina.ai` | `web_scraping.allow_external` (household) |
| **Pantry package store** | `pantry-api.jarvisautomation.io` (`pantry.base_url`) | `pantry.enabled` (household) |
| **Push delivery** | your relay (such as `relay.jarvisautomation.io`) → Expo | `relay.url` (server; or `RELAY_URL`); empty means off |

With `updates.enabled` off, the server makes no update request at all. With `relay.url` empty, push notifications are not sent; the inbox still works. With `pantry.enabled` off, package installs are refused.

### Things you start

| Action | Reaches |
|---|---|
| Installing a model in the setup wizard or on the **Models** page | `huggingface.co` for the model; GitHub releases for the runtime that runs it (llama.cpp, whisper.cpp) |
| Installing a Hugging Face directory model (MLX, vLLM or Transformers) | Also GitHub releases for uv and a Python build, and PyPI (`pypi.org`, `files.pythonhosted.org`) for the engine's packages |
| `jarvisd upgrade` | `api.github.com` and the release's files on GitHub |
| Adding a cloud model provider (an OpenAI-compatible endpoint or `api.anthropic.com`) | That provider, with the conversations sent to it |
| Setting up phone calls (Twilio) | `api.twilio.com` |
| Installing a command package or a vendor-cloud device family | Whatever that integration needs |

Runtimes are checked against checksums built into jarvisd before they run. The download addresses are settings too: point `llm.hf_endpoint` (env `HF_ENDPOINT`), `llm.engine_base_url` (llama.cpp) and `stt.engine_base_url` (whisper.cpp) at a mirror on your network to install models without the internet. uv and the Python engines have no mirror setting: they always download from their pinned defaults.

### On nodes and phones

| Capability | Reaches | Setting | Default |
|---|---|---|---|
| **Desktop agent self-update** (also the experimental Go Pi node, which is the same program) | `api.github.com`, GitHub releases | `auto_update` in the agent's `agent.json`, or `--no-auto-update` | **On** |
| **Python node self-update** | GitHub releases | `allow_updates` in the node's `config.json` (or `JARVIS_ALLOW_UPDATES`) | Off |
| **Wake-word model download** (Python node) | GitHub (openWakeWord) | `wake_word_model_autodownload_enabled` in the node's `config.json` | Off |
| **Mobile push notifications** | Expo (`exp.host`) → APNs/FCM | Mobile app → **Settings** | Off |

The desktop agent checks the server's version daily and, when it differs, downloads that release from GitHub and installs it. It also accepts an update sent to it from the server. See [Updates and settings](../agent/updates-settings.md).

## Fully offline checklist

1. Install the server and download your models while connected, or from a mirror on your network.
2. Leave every server and Python-node setting in the tables above **off** (the default).
3. Run desktop agents with `--no-auto-update`, or set `"auto_update": false` in `agent.json`: their self-update is **on** by default. Update them by hand instead.
4. Leave `relay.url` empty and mobile push off: no push payloads leave the phone or the server.
5. Don't add a cloud model provider.
6. Upgrade by hand: download a release on another machine and run `jarvisd upgrade` with `JARVISD_RELEASE_BASE` pointing at the folder ([CLI](../operate/cli.md#upgrade)).
7. Remember that a command package or a vendor-cloud device family (Nest, Ecobee, Govee cloud) adds outbound traffic for that feature by design. Installing it is the opt-in.

!!! tip "Verifying"
    On the server, list open connections with `sudo lsof -i -nP | grep ESTABLISHED` (Linux, macOS) or `Get-NetTCPConnection -State Established` (Windows), or check your router's logs. With everything above off, you should see only connections inside your network, not to `github.com`, `huggingface.co`, `exp.host` or `r.jina.ai`.

## Command packages & device families

- **Command packages** (`jarvis-cmd-weather`, `-news`, `-spotify`, ...) are external integrations by nature. Installing one from the Pantry is your consent for the traffic it needs; the package's code runs on your node, not in the cloud.
- **LAN device families** (Hue, Kasa, LIFX, Z-Wave, HomeKit) stay entirely on your network.
- **Vendor-cloud device families** (Nest/Google, Govee cloud, Resideo, SimpliSafe) need the vendor's cloud to work. Adding one is the opt-in.

## Enabling updates

Updates are off by default so a local-only server never phones home.

=== "Server"

    Turn on update checks on the admin web app's **Updates** page (the `updates.enabled` setting), or set `JARVIS_ALLOW_UPDATES=1` in `jarvisd.env` and restart. The server then checks GitHub for new releases and can install one from the admin web app.

    `jarvisd upgrade` on the command line works either way: running it is the opt-in. See [Upgrade](../install/upgrade.md).

=== "Nodes"

    A node update needs two switches:

    1. **On the server**: `updates.allow_check`, which lets the server look up the newest node release on `api.github.com`.
    2. **On the node**: allow it to download and apply a release:

        ```json title="config.json"
        { "allow_updates": true }
        ```

        or set `JARVIS_ALLOW_UPDATES=true` in the node's environment.

    You start the update from the mobile app. Installing an **explicit** version skips the GitHub lookup, but the node still needs `allow_updates` to fetch the release.

!!! warning "Updates require internet"
    Any update path connects to GitHub. Leave them off for an air-gapped install and upgrade by hand instead.

See also: [Security model: what leaves your network](../architecture/security.md#what-leaves-your-network) for every outbound connection and its default.
