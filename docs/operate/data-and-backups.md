# Data and backups

Everything your Jarvis Automation server knows lives in one folder, its **data directory**: the database (accounts, households, nodes, devices, settings, memories, routines, the inbox), uploaded files, downloaded models and its logs. Back up that folder and you can rebuild the server from it.

## Where the data lives

- **Linux** (`.deb`): data in `/var/lib/jarvisd`, env file `/etc/jarvisd/jarvisd.env`, program `/usr/local/bin/jarvisd`.
- **Linux, user service** (`--user`): data in `~/.jarvisd`, env file `~/.jarvisd/jarvisd.env`.
- **macOS** (`.dmg`): data in `~/.jarvisd` of the account the server runs as, env file `~/.jarvisd/jarvisd.env`, program `/usr/local/bin/jarvisd`.
- **Windows** (`Setup.exe`): data in `%ProgramData%\jarvisd` (usually `C:\ProgramData\jarvisd`), env file `%ProgramData%\jarvisd\jarvisd.env`, program `%ProgramFiles%\jarvisd\jarvisd.exe`.

`jarvisd service status` prints the data directory on its `home:` line. To run jarvisd on another folder, see [the data directory and the env file](cli.md#the-data-directory-and-the-env-file).

The data directory is readable only by the account the server runs as (`jarvisd` on Linux, `NT SERVICE\jarvisd` on Windows). It holds the key the server signs logins with and everyone's password hashes, so keep it that way: `jarvisd doctor` warns if other accounts can read it.

## What is in it

| Path | What it holds |
|---|---|
| `jarvis.db` (with `jarvis.db-wal`, `jarvis.db-shm`) | The database: everything you set up. The two companion files belong to it while the server runs. |
| `blobs/` | Uploaded files: photos, attachments, recordings. |
| `models/` | Language models downloaded from the setup wizard or the Models page. Often the largest folder by far. |
| `engines/`, `lib/` | The model runtimes and speech libraries jarvisd downloads or unpacks. |
| `backups/` | Database snapshots taken before each upgrade (the last 3). |
| `updates/` | Downloaded releases and the state of an upgrade in progress. |
| `logs/` | The server's start-up log on macOS and Windows (`logs/jarvisd.log`). See [Logs](../troubleshooting/index.md#read-the-log). |
| `jarvisd.env` | Settings jarvisd reads at start (usually comments only). |
| `setup-token` | The setup wizard's one-time token, until the first admin account exists. |

Models, runtimes and libraries can be downloaded again, so a backup can leave out `models/`, `engines/` and `lib/` if space matters. Everything else is yours alone.

## Back up

There is no `jarvisd backup` command yet. Copy the data directory while the server is stopped, so the database is not changing under the copy:

=== "Linux"

    ```bash
    sudo jarvisd service stop
    sudo tar -czf jarvisd-backup-$(date +%F).tar.gz -C /var/lib jarvisd
    sudo jarvisd service start
    ```

    For a user service (`--user`), drop `sudo`, add `--user` to the service commands and archive `~/.jarvisd`.

=== "macOS"

    ```bash
    sudo jarvisd service stop
    tar -czf jarvisd-backup-$(date +%F).tar.gz -C ~ .jarvisd
    sudo jarvisd service start
    ```

    Run `tar` as the account the server runs as (the one that installed it).

=== "Windows"

    In an Administrator PowerShell:

    ```powershell
    jarvisd service stop
    Compress-Archive -Path "$env:ProgramData\jarvisd" -DestinationPath "jarvisd-backup-$(Get-Date -Format yyyy-MM-dd).zip"
    jarvisd service start
    ```

Store the archive somewhere other than the server, and protect it like the data directory itself: it holds the signing key and password hashes.

## Restore

1. Install the same release you backed up from, or a newer one ([releases](https://github.com/alexberardi/jarvis-server/releases)). An older release refuses a database a newer one has changed.
2. Stop the server: `jarvisd service stop` (with `sudo`, or as Administrator).
3. Replace the data directory with the one from the archive. On Linux, give it back to the service account: `sudo chown -R jarvisd:jarvisd /var/lib/jarvisd`.
4. Start it again: `jarvisd service start`, then check with `jarvisd doctor`.

## Snapshots before upgrades

`jarvisd upgrade` copies the database into `backups/` before it swaps the program, named after the version it upgraded from and the time (`jarvis-<version>-<time>.db`), and keeps the last 3. The program it replaced stays next to the new one as `jarvisd.prev` (`jarvisd.prev.exe` on Windows). If the new version doesn't come up healthy, the upgrade puts both back by itself; `jarvisd upgrade --rollback` does the same by hand. These snapshots only cover the database and stay on the same disk, so they are no replacement for a backup. See [Upgrade](../install/upgrade.md).

## Remove the data

`jarvisd service uninstall` keeps the data directory. `jarvisd service uninstall --purge` deletes it, with the env file and the service account. See [Uninstall](../install/uninstall.md).
