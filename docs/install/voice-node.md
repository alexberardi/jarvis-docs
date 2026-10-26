# Voice node

A voice node is a small device with a microphone and speaker, usually a Raspberry Pi, that listens for "Hey Jarvis", sends what you say to your server and plays the reply. Install the server first and finish its [setup wizard](setup-wizard.md); the node then needs only the server's address, `http://<server>:7700`.

Jarvis Automation is a **pre-release** (release candidate rc18.8). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Choose a node

| Node | Status | Install |
|------|--------|---------|
| Python node (`jarvis-node-setup`) on a Raspberry Pi | **Supported** | `install.sh` from `jarvis-node-setup` v0.3.6 |
| Go node (`install-pi.sh`) on a Raspberry Pi with the ReSpeaker 2-Mics HAT | **Experimental** preview | `install-pi.sh` from the server release |
| Node in Docker | Text mode for demos and development; voice on a Linux host | A container image |

Use the Python node unless you want to try the preview on a spare Pi.

## Install the Python node

On the Pi:

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-node-setup/v0.3.6/install.sh | sudo bash
```

Then pair it from the [mobile app](mobile-app.md): tap **Add Node** and follow the steps. The fresh node opens a Wi-Fi hotspot (`jarvis-XXXX`); the app joins it, gives the node your Wi-Fi and the server's address, and the node joins your household. [Provisioning](../clients/provisioning.md) walks through each step, and [Node Setup](../clients/node-setup.md) covers the installer's flags and the node itself.

## Try the Go node (experimental)

The Go node uses much less memory, but it is a preview: some voice commands (devices, routines, "send me a link") do not work by voice yet, and it is not yet checked on every Pi. It installs **next to** the Python node, disabled, and `--activate` switches between them. Read its limits and steps first: [Go Pi node](../clients/node-setup.md#go-pi-node-experimental-preview).

## Node in Docker

Running the node as a container belongs to the old Docker install; its page is under [Legacy: Node in Docker](../legacy/clients/node-docker.md).

## If the node can't reach the server

Run `jarvisd doctor` on the server. It checks that nodes and phones can reach it; `sudo jarvisd doctor --fix` opens the firewall if that is what is in the way.
