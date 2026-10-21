# Server in Docker

Jarvis runs as one container on any Linux machine with Docker: the whole server, the same `jarvisd` as the other installs, in container mode. On Unraid, use the [Unraid template](unraid.md) instead; it sets up the same container for you.

## Requirements

- Linux with Docker Engine, and Docker Compose if you use the compose file. The image is for x86-64 (amd64).
- Optional: an NVIDIA GPU, with the driver and the **NVIDIA Container Toolkit** on the host. Without one, everything runs on the CPU.

## The image

The image is `ghcr.io/alexberardi/jarvisd:<tag>`, where `<tag>` is a release's tag. Each release's notes on the [releases page](https://github.com/alexberardi/jarvis-server/releases) name its image; use the newest.

!!! note "No `:latest` yet"
    `:latest` follows stable releases only. While Jarvis Automation is a pre-release, name the tag. Releases up to rc18 have no image; the first one comes with the next release.

## Run it

Pick a folder on the host for Jarvis's data, here `/srv/jarvis`. Then either run it with `docker run`:

```sh
docker run -d --name jarvis --restart=unless-stopped \
  -p 7700:7700 -p 7710:7710 -p 1884:1884 \
  -v /srv/jarvis:/data \
  -e JARVIS_CONTAINER=docker \
  ghcr.io/alexberardi/jarvisd:<tag>
```

or put this in a `compose.yaml` and run `docker compose up -d` next to it:

```yaml
services:
  jarvis:
    image: ghcr.io/alexberardi/jarvisd:<tag>
    container_name: jarvis
    restart: unless-stopped
    ports:
      - "7700:7700"
      - "7710:7710"
      - "1884:1884"
    volumes:
      - /srv/jarvis:/data
    environment:
      - JARVIS_CONTAINER=docker
```

`JARVIS_CONTAINER=docker` is the image's default; it is written out so you can see the container is in container mode, which changes how it is [updated](#updating).

Moving from the old Docker install and keeping its data? Don't open the setup wizard yet: [import your data](#coming-from-the-old-install) first.

## First run

1. Read the setup token from the container's log:

    ```sh
    docker logs jarvis
    ```

    It is on the line `Setup token: …`. It is also in the file `/srv/jarvis/setup-token`.

2. Open `http://<host>:7710/` and paste the token. That is the [setup wizard](setup-wizard.md).
3. Follow the wizard. It downloads a language model (LLM) and a speech-to-text model; text-to-speech is built in.

Give phones and voice nodes the server's address: `http://<host>:7700`. They never find a server by themselves, in a container or not.

## Ports

| Port | What uses it |
|------|--------------|
| 7700 | The API: voice nodes, the mobile app and the recipes app |
| 7710 | The admin and the setup wizard |
| 1884 | MQTT, for voice nodes |

Every service lives on 7700 under its own path, so these three ports are all a new install needs; see [Ports](../architecture/index.md#ports). To use another port on the host, change the left side of a mapping (`8700:7700`) and use that port in the addresses you give phones and nodes.

## The data folder and its owner

Everything Jarvis keeps (the database, the setup token, models and engines) is in `/data`, the folder you mounted. Removing the container and running it again keeps your data, and so do updates.

Jarvis runs as user 99, group 100 inside the container. On start, the container makes the data folder belong to that user if it doesn't already. To use another user, set `PUID` and `PGID`:

```sh
  -e PUID=1000 -e PGID=1000 \
```

With `docker run --user`, the container runs Jarvis as that user and changes no owners; the folder must then be writable by it.

Back the folder up with the container stopped (`docker stop jarvis`). More: [Data and backups](../operate/data-and-backups.md).

## NVIDIA GPU

With the NVIDIA Container Toolkit on the host, add two options:

```sh
docker run -d --name jarvis --restart=unless-stopped \
  --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=all \
  -p 7700:7700 -p 7710:7710 -p 1884:1884 \
  -v /srv/jarvis:/data \
  -e JARVIS_CONTAINER=docker \
  ghcr.io/alexberardi/jarvisd:<tag>
```

In `compose.yaml`, the same is `runtime: nvidia` and `NVIDIA_VISIBLE_DEVICES=all` under `environment`. Set `NVIDIA_VISIBLE_DEVICES` to one GPU's UUID (`nvidia-smi -L` lists them) to give Jarvis only that one. The wizard's **Hardware** step then shows the GPU.

AMD and Intel GPUs are not supported in the container yet.

## Updating

Jarvis doesn't update itself in a container. Pull the newer image and recreate the container; your data in `/data` is kept. See [Upgrade: In a container](upgrade.md#in-a-container).

## Coming from the old install

To move the old Docker install's data into the container, see [Migrating: On Unraid or in Docker](migrating-from-docker.md#on-unraid-or-in-docker). Do it before the setup wizard.
