# Install Jarvis Automation

Jarvis Automation is a **pre-release** (release candidate rc18.9). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

Jarvis Automation is one server (`jarvisd`) that runs on a Mac, a Windows PC or a Linux machine on your network, plus the clients you talk to Jarvis through.

1. Check the [requirements and choose a model](requirements.md).
2. Install the server on [macOS](macos.md), [Windows](windows.md) or [Linux](linux.md), or with an [install script](one-liners.md). Or run it as a container on [Unraid](unraid.md) or in [Docker](docker.md).
3. Finish in the [setup wizard](setup-wizard.md) at `http://<host>:7710/setup`.
4. Add clients: the [desktop agent](../clients/desktop-agent.md), a [voice node](voice-node.md) and the [mobile app](mobile-app.md).

Later: [upgrade](upgrade.md) or [uninstall](uninstall.md).

## Coming from the old Docker install

The old Docker/microservice install is retired for new users: it no longer installs out of the box (MinIO is gone). Its pages are kept, frozen, under [Legacy](../legacy/index.md). To move an existing install over, see [Migrating from the old install](migrating-from-docker.md).
