# Server on Unraid

Jarvis runs on Unraid as one container, installed from a Community Applications template. The container holds the whole server: speech-to-text, the language model, text-to-speech, and the services that voice nodes, the mobile app and the recipes app talk to.

## Requirements

- Unraid 6.12 or later.
- The **Community Applications** plugin (the Apps tab).
- Optional: an NVIDIA GPU, with the **Nvidia Driver** plugin. Without one, everything runs on the CPU.

## Install

1. Open the **Apps** tab and search for **Jarvis**.
2. If it isn't listed yet, add the template by URL instead (until it is in Community Applications):

    ```text
    https://raw.githubusercontent.com/alexberardi/jarvis-server/main/scripts/packaging/unraid/jarvis.xml
    ```

3. Set **Repository** to a release tag, `ghcr.io/alexberardi/jarvisd:<tag>` (see [The image tag](#the-image-tag)). Leave the rest at the defaults.
4. Click **Apply**.

Moving from the old Docker install and keeping its data? Don't open the WebUI yet: [import your data](#coming-from-the-old-install) first.

### The image tag

The template installs `ghcr.io/alexberardi/jarvisd:latest`, but `:latest` follows stable releases only. While Jarvis Automation is a pre-release there is no `:latest`, and the container can't be pulled with the default. Name a release instead: `ghcr.io/alexberardi/jarvisd:<tag>`, where `<tag>` is the newest tag on the [releases page](https://github.com/alexberardi/jarvis-server/releases); its release notes name the image. Releases up to rc18 have no image; the first one comes with the next release.

Not on Unraid? The same container runs in plain [Docker](docker.md).

## First run

1. On the **Docker** tab, click the Jarvis icon and choose **WebUI**. It opens the [setup wizard](setup-wizard.md) on port 7710.
2. The wizard asks for a **setup token**. It is in two places:
    - the container's log: **Docker** tab → the Jarvis icon → **Logs**, on the line `Setup token: …`;
    - the file `/mnt/user/appdata/jarvis/setup-token`.
3. Follow the wizard. It downloads a language model (LLM) and a speech-to-text model; text-to-speech is built in.

## Ports

| Port | What uses it |
|------|--------------|
| 7700 | The API: voice nodes, the mobile app and the recipes app |
| 7710 | The admin and the setup wizard (the WebUI) |
| 1884 | MQTT, for voice nodes |

Every service lives on 7700 under its own path (`/cc`, `/auth`, `/stt` and so on), so these three ports are all a new install needs. Clients find the paths through `/services`; see [Ports](../architecture/index.md#ports).

Older clients that expect the old per-service ports (7701–7712, 7030, 7031) need `server.legacy_ports` turned on in the admin's Settings, or `JARVIS_LEGACY_PORTS=1` in the template. jarvisd then also listens on those ports, and you must map each one you need in the template yourself.

## Bridge or host networking

The template uses **bridge** networking:

- The three ports above are mapped from the container to the server.
- Give phones and voice nodes the server's address: `http://<unraid-ip>:7700`. (Phones and nodes never find the server by themselves.)

**Host** networking (set Network Type to Host in the template) also works:

- The server's mDNS announcement reaches your network, so [desktop agents](../clients/desktop-agent.md) find the server by themselves. Phones and voice nodes still take the address.
- There is no port mapping. Ports 7700, 7710 and 1884 must be free on the Unraid server itself; another container or plugin on any of them stops Jarvis from starting.

## NVIDIA GPU

1. Install the **Nvidia Driver** plugin from the Apps tab and reboot if it asks you to.
2. Edit the Jarvis container (switch on **Advanced View**):
    - add `--runtime=nvidia` to **Extra Parameters**, after what is already there;
    - set `NVIDIA_VISIBLE_DEVICES` to `all`, or to one GPU's UUID (the Nvidia Driver plugin's page lists them).
3. Apply. The wizard's **Hardware** step now shows the GPU.

Without these settings Jarvis runs everything on the CPU, which works but is slower. The template can't add `--runtime=nvidia` for you: without the Nvidia Driver plugin the container would not start.

AMD and Intel GPUs are not supported in the container yet.

## Data

Everything Jarvis keeps (the database, models and engines) is under `/mnt/user/appdata/jarvis`.

- Removing the container and adding it again keeps your data, and so do updates.
- Back it up with the appdata backup plugin, with the container stopped.

## Updating

Update from the **Docker** tab: **Check for Updates**, then **apply update** on Jarvis. Your data in appdata is kept.

The admin's **Updates** page tells you when a new release exists, but in the container it doesn't install it; it points you to the Docker tab. While you run a pre-release, it tells you about the next pre-release too.

With a release tag in **Repository**, Check for Updates only finds a rebuild of that tag; to move to a newer release, put its tag in **Repository**. More: [Upgrade: In a container](upgrade.md#in-a-container).

## Coming from the old install

To move the old Docker install's data into Jarvis, see [Migrating: On Unraid or in Docker](migrating-from-docker.md#on-unraid-or-in-docker). Do it before you open the WebUI.

## Troubleshooting

**The container doesn't start: a port is already in use.**
Another container already uses 7700, 7710 or 1884 (an MQTT broker on 1884 is the usual one). In bridge mode, change the host side of Jarvis's mapping and use that port in the addresses you give phones and nodes; in host mode, stop the other container or move it.

**The WebUI asks for a token.**
That is the setup token. Copy it from the container's log (Docker tab → the Jarvis icon → **Logs**) or from `/mnt/user/appdata/jarvis/setup-token`.

**The GPU is not listed.**
Check that **Extra Parameters** has `--runtime=nvidia` and that `NVIDIA_VISIBLE_DEVICES` is set. Then open the container's **Console** and run `nvidia-smi`: if it fails, the container can't see the GPU, so check the Nvidia Driver plugin.

**The recipes app can't connect.**
If you once typed an address with `:7030` into the recipes app, clear it. That old port is closed on a new install; the app then finds the server on 7700.
