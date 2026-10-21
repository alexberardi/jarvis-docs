# Upgrade

How to move the server, the desktop agent and voice nodes to a newer release, what is kept when you do, and how to go back.

Jarvis Automation is a **pre-release** (release candidate rc18). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Upgrade the server

Pick one; they all end the same way.

- **From the admin.** The admin's **Updates** page offers new releases: click **Update**. The server downloads the release, checks it, restarts on it and the page shows how it went. Nothing to type, on any system.
- **From a terminal** on the server:

    ```sh
    sudo jarvisd upgrade                          # the newest release
    sudo jarvisd upgrade --version v0.1.0-rc18    # a given release
    ```

    On Windows, run it in an administrator PowerShell without `sudo`. `jarvisd upgrade --check` only says whether a newer release exists. All options: [jarvisd upgrade](../operate/cli.md#upgrade).

- **With a newer installer.** Open the newer release's installer over the old one: the macOS app offers **Update** when it carries a newer server, and the Windows setup, the `.deb` package and [`install.sh` or `install.ps1`](one-liners.md) upgrade in place. An installer never replaces a newer server with an older one.

While Jarvis Automation is a pre-release, a pre-release upgrades to the next pre-release. The admin only moves forward; to go to an older release on purpose, use `jarvisd upgrade --version <tag> --allow-older`.

## What happens during an upgrade

1. The server downloads the release's `SHA256SUMS` and its signature first and checks the signature against the project key built into the running server. An unsigned or wrongly signed release is refused before anything large is downloaded.
2. It checks there is enough free disk, downloads the new server and checks it against `SHA256SUMS`.
3. It snapshots the database into `backups/` in the data directory, named after the version it upgrades from, and keeps the last 3 per database.
4. It keeps the current program next to the new one as `jarvisd.prev` (`jarvisd.prev.exe` on Windows) and swaps in the new one.
5. It restarts on the new version and waits for it to answer its health check, for up to 2 minutes.

If the new version doesn't come up healthy, or fails to start twice, the server **rolls back by itself**: it puts `jarvisd.prev` back and, only if the new version had already changed the database, restores the snapshot.

## What is kept

Everything in the [data directory](../operate/data-and-backups.md#where-the-data-lives): accounts, households, devices, settings, downloaded models and files. An upgrade replaces the program only. The installer's firewall choice stays as it was.

The snapshots in `backups/` cover the database only and sit on the same disk: they are no replacement for a [backup](../operate/data-and-backups.md#back-up).

## Roll back by hand

To go back to the version you upgraded from:

```sh
sudo jarvisd upgrade --rollback
```

It puts `jarvisd.prev` back and restarts the server. During an upgrade that hasn't passed its health check yet, it also restores the database snapshot if the new version had changed the database; it then tells you that data written since the snapshot was rolled back. After an upgrade that succeeded, it leaves the database alone; if the older version can't read it, the server refuses to start, says why and points to the snapshots in `backups/`. See [An upgrade failed](../troubleshooting/index.md#an-upgrade-failed).

## The desktop agent and voice nodes

- **Desktop agent:** it updates itself to follow its server's version. Nothing to do.
- **Voice nodes:** update them from the mobile app's [Nodes](../mobile/nodes.md) page. See [Voice node](voice-node.md).
