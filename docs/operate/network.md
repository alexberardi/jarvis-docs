# Ports, firewall and mDNS

Your voice nodes, phones and desktop agents reach the Jarvis Automation server over your local network. This page lists what they connect to, how to let them through the server's firewall, and how they find the server on their own.

## Ports

A new install listens on three TCP ports and announces itself on mDNS:

| Port | What uses it |
|---|---|
| **7700** TCP | The API (HTTP): nodes, the mobile app and the desktop agent. Every part of the server answers here under its own path (`/cc`, `/auth`, `/stt`, `/tts`, ...), and `/health` reports whether the server is up. |
| **7710** TCP | The admin web app and the setup wizard (`http://<host>:7710/setup`). |
| **1884** TCP | The MQTT message broker that nodes stay connected to. It asks every client for credentials. |
| **5353** UDP | The server's mDNS announcement, so the mobile app finds it without typing an address. |

### Legacy ports

Before jarvisd, each part of Jarvis was a separate service with its own port, and older nodes and apps still use those ports. jarvisd can open them too:

| Port | Service |
|---|---|
| 7701 | Auth |
| 7702 | Logs |
| 7703 | Command center |
| 7704 | LLM |
| 7706 | Speech-to-text |
| 7707 | Text-to-speech |
| 7712 | Notifications |
| 7030 | Recipes |
| 7031 | OCR |
| 9883 | MQTT over WebSocket |

The `server.legacy_ports` setting (admin web app → **Settings**) turns them on or off; a restart applies it. `JARVIS_LEGACY_PORTS=1` (or `0`) in `jarvisd.env` overrides the setting.

!!! note "Which servers open them"
    Up to and including rc18, jarvisd always opens the legacy ports. From the next release, a new install opens only the ports in the first table, and a server upgraded from an earlier jarvisd keeps the legacy ports on, so nodes set up against them keep working. `jarvisd doctor` checks exactly the ports your server opens.

### Change a port

Set the port in `jarvisd.env` and restart (`jarvisd service restart`):

| Variable | Meaning |
|---|---|
| `JARVIS_PORT_ADMIN`, `JARVIS_PORT_CONFIG`, `JARVIS_PORT_COMMAND_CENTER`, ... | One listener's port (`JARVIS_PORT_` plus the listener name in capitals, `-` as `_`). The API is `CONFIG` (7700). |
| `JARVIS_MQTT_ADDR` | The MQTT broker's listen address, such as `:1884`. |
| `JARVIS_HOST` | The address every listener binds to. Default `0.0.0.0` (all interfaces). |

### Run a second server beside the first

`jarvisd serve --port-offset N` (or `JARVIS_PORT_OFFSET=N`) adds `N` to every default port, the broker's included: with `10000` the API is on 17700, the admin web app on 17710 and MQTT on 11884. Give the second server its own data directory with `--home`.

## Firewall

If the server's firewall blocks these ports, everything works from the server itself but nodes and phones can't connect. `jarvisd doctor` reads the firewall and tells you, per local network, whether it lets the ports in. To open them:

```bash
sudo jarvisd doctor --fix
```

On Windows, run `jarvisd doctor --fix` in an Administrator PowerShell. The desktop installers run this step for you unless you declined it.

What `--fix` changes, on each system:

| Firewall | What `--fix` adds |
|---|---|
| **ufw** (Linux) | `allow` rules for the server's ports from each private local network, with the comment `jarvisd`. |
| **firewalld** (Linux) | A `jarvisd` service listing the ports, allowed from each private local network. |
| **Application firewall** (macOS) | Allows the `jarvisd` program. If **Block all incoming connections** is on, turn it off in System Settings → Network → Firewall. |
| **Windows Defender Firewall** | An inbound rule named `jarvisd` for the program, on the **Private** profile, from the local subnet. |

On Linux the rules admit only private address ranges (such as `192.168.x.x` and `10.x.x.x`), and on Windows only the local subnet; the macOS firewall allows or blocks whole programs, not ports. `jarvisd service uninstall` removes these rules again unless you pass `--keep-firewall`.

!!! warning "Windows: Public networks"
    The Windows rule covers Private networks only. If Windows treats your network as **Public**, `jarvisd doctor` warns; switch the network to Private in Settings → Network & internet.

Don't forward these ports on your router. Jarvis is built for your local network; the admin web app's **Connections** page sets the public addresses to use if you reach the server through a tunnel.

## mDNS discovery

The server announces itself on the local network as a `_jarvis-config._tcp` service named `Jarvis (<hostname>)`, pointing at the API port (7700). The mobile app looks for that announcement, so on the same Wi-Fi it finds the server without an address. The announcement uses UDP port 5353, which `doctor --fix` opens with the others.

| Variable | Meaning |
|---|---|
| `JARVIS_MDNS=0` | Don't announce the server. Phones then need the address typed in. |
| `JARVIS_MDNS_INTERFACES` | The network interfaces to announce on, comma-separated (for example `eth0` or `en0`), when the server has several and picks the wrong one. The setup link uses the same interface's address. |

mDNS doesn't cross between networks: a phone on a guest Wi-Fi or another VLAN won't see the server. Type the address in the app instead (`http://<server-ip>:7700`).

## What the server connects to

Outbound, the server talks to your own devices and nothing else until you turn an internet feature on. The list: [Network egress and offline mode](../security/offline-mode.md).
