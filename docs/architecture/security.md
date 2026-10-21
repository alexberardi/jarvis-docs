# Security model

What `jarvisd` exposes on your network, what it keeps on disk, and what leaves your network. For who may call what, see [Authentication](authentication.md).

## What listens

A fresh install listens on three ports:

| Port | What | Who calls it |
|---|---|---|
| 7700 | The API, every module under its own path | Nodes, the mobile app |
| 7710 | The web admin and setup wizard | Your browser |
| 1884 | The MQTT broker | Nodes |

The inference engines (`llama-server`, `whisper-server`) listen on the loopback interface only, for `jarvisd` itself. An upgraded install can also open the old per-service ports (`server.legacy_ports`); a fresh one does not.

- **Callers are authenticated.** Being on the LAN earns nothing: a node presents its key on every call, a person a token, and the MQTT broker checks each node's login and limits it to its own topics. The routes that answer without a credential are the ones a client needs before it has one, such as `/auth/public-key`.
- **Setup is guarded.** Until the first account exists, creating it needs the one-time setup token from the data directory, so someone else on the network cannot claim a fresh install first.
- **Sign-up is closed.** After the first account, joining needs an invite code.
- **Firewall.** `jarvisd doctor --fix` (as root) opens the host firewall for private LAN ranges only, with rules tagged `jarvisd`.
- **Transport.** The URLs `jarvisd` hands out are plain `http://`. To reach it from outside your home network, put it behind a tunnel or reverse proxy that terminates TLS, rather than opening the ports to the internet.

!!! warning "Development switch"
    `JARVIS_MQTT_ALLOW_ANONYMOUS=1` lets MQTT clients connect without a login (read anything, publish only under `jarvis/dev/`). It is for development: `jarvisd` warns at startup and `jarvisd doctor` flags it.

## What is stored

Everything lives in the data directory (`~/.jarvisd/` by default). `jarvisd` runs with `umask 077`: the directory is readable only by its own user (0700), and the database and key files only by that user (0600).

| What | Stored as |
|---|---|
| Passwords, node keys, app keys | bcrypt hashes |
| Refresh tokens, provisioning tokens | SHA-256 hashes |
| The token signing key | In the database (`auth_signing_keys`) |
| The setup token | A file until the first account is made; only its hash in memory |
| Command secrets (a command's API keys and account tokens) | Not on the server at all: encrypted end to end between the mobile app and the node |
| Voice | Voiceprints only, never recordings, and only for people who enroll |

Backups (database snapshots taken before an update) are 0600 too, and contain the signing key: keep them as private as the data directory. The settings API shows secret values masked.

Households share one database; each row carries its household and every request is checked against the caller's memberships. Deleting an account or a household removes its data in one transaction (see [Authentication](authentication.md#accounts-and-deletion)).

## What leaves your network

Nothing that needs the internet is on by default. The language model, speech to text, text to speech and speaker identification all run on your hardware.

| Connection | When | Default |
|---|---|---|
| Model weights (Hugging Face) and GPU engine downloads | When you pick a model in the web admin | Only on request |
| [Pantry](../pantry/index.md), the package store | Browsing and installing packages | Off (`pantry.enabled`, per household) |
| Push relay, for phone notifications | Each push | Off (`relay.url` empty); the setup wizard's privacy step turns it on |
| Remote language-model providers (OpenAI, Anthropic, ...) | Each request, if you configure one | Off |
| Updates from GitHub releases | When you update | Only on request |
| Commands that use the internet (weather, search, ...) | When they run | Only the commands you install and enable |

For running fully offline, see [Network egress and offline mode](../security/offline-mode.md).

## Updates are signed

Each release ships `SHA256SUMS` and its **minisign** signature. `jarvisd upgrade` and Update in the web admin check the signature against the project's public key, which is built into the running `jarvisd`, and refuse an update whose checksum does not match. Before swapping in the new binary, `jarvisd` snapshots the database and keeps the previous binary, and it rolls back if the new one fails its health check.

The install scripts verify the signature if `minisign` is installed, and warn if it is not. macOS builds are signed with an Apple Developer ID and notarized.

