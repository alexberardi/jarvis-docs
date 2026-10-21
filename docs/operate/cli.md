# The jarvisd command

`jarvisd` is the Jarvis Automation server: one program that runs every part of Jarvis, plus the commands to install it as a service, check it and upgrade it. The installers put it on your `PATH`, so you can run these commands in a terminal on the server.

This page covers release candidate rc18 and was checked against the help that `jarvisd help` prints. Run that on your own server to see what your version supports.

!!! note "When you need sudo"
    The server normally runs as a system service, and its data directory belongs to that service. Commands that change the service, its firewall rules or its data need `sudo` on Linux and macOS, or an Administrator PowerShell on Windows. Read-only commands such as `jarvisd version` and `jarvisd service status` don't.

## At a glance

| Command | What it does |
|---|---|
| [`jarvisd serve`](#serve) | Run the server in this terminal (the service runs this for you) |
| [`jarvisd service ...`](#service) | Install, start, stop, check or remove the background service |
| [`jarvisd doctor`](#doctor) | Check that nodes and phones can reach the server; `--fix` opens the firewall |
| [`jarvisd setup-link`](#setup-link) | Print the setup wizard link, or the admin address once set up |
| [`jarvisd upgrade`](#upgrade) | Install a newer signed release, or roll back the last one |
| [`jarvisd version`](#version) | Print the version |
| [`jarvisd migrate status`](#migrate-status) | Show each module's database migration state |
| [`jarvisd import-legacy`](#import-legacy) | Copy an old Docker install's data in (once, before setup) |
| [`jarvisd import-recipes`](#import-recipes) | Copy recipes and meal plans in from an old install's export |
| [`jarvisd install-from-app`](#install-from-app) | The desktop installers' own step; you don't run it by hand |

## The data directory and the env file

Every command works on one **data directory** (the server's home). jarvisd picks it in this order:

1. `--home DIR`, given before or after the command (`jarvisd --home /srv/jarvis doctor`);
2. the `JARVIS_HOME` environment variable;
3. the data directory of the installed service, if there is one;
4. `~/.jarvisd` in your own home directory.

So on a machine with the service installed, plain `jarvisd doctor` checks the service's data. Where that is on each system: [Data and backups](data-and-backups.md#where-the-data-lives).

At start, jarvisd reads `jarvisd.env` in the data directory: one `KEY=value` per line, for settings it needs before it can open its database. A variable already set in the environment wins over the file. The Linux system service also reads `/etc/jarvisd/jarvisd.env`. A fresh install writes the file with comments only, because it needs none of them: everyday settings live in the admin web app. After you edit the file, restart: `sudo jarvisd service restart` (on Windows, in an Administrator PowerShell without `sudo`).

## serve

```text
jarvisd serve [--no-browser] [--allow-downgrade] [--port-offset N]
```

Runs the server in the foreground until you stop it (Ctrl+C). The service runs exactly this, so you need it only to try jarvisd without installing a service, or to watch it start. On its first start it prints the setup link and, at a desktop, opens it in your browser.

| Option | Meaning |
|---|---|
| `--no-browser` | Don't open the setup link (same as `JARVIS_NO_BROWSER=1`). |
| `--allow-downgrade` | Start on a database that a newer jarvisd has already migrated. For experts recovering from a failed upgrade; normally jarvisd refuses. |
| `--port-offset N` | Add `N` to every default port, to run a second server beside the installed one: `10000` puts the API on 17700. Same as `JARVIS_PORT_OFFSET`. See [Ports](network.md#run-a-second-server-beside-the-first). |

## service

```text
jarvisd service install [--user] [--bin PATH] [--run-as USER] [--no-start]
jarvisd service uninstall [--user] [--purge [--yes]] [--keep-firewall]
jarvisd service start|stop|restart [--user]
jarvisd service status [--user] [--json] [--wait DURATION]
```

Registers jarvisd with the system's service manager (systemd on Linux, launchd on macOS, the Service Control Manager on Windows) so it starts at boot and restarts if it stops. The installers do this for you.

| Command | What it does |
|---|---|
| `jarvisd service install` | Register the service and start it. Creates the data directory and an env file of comments. |
| `jarvisd service start`, `jarvisd service stop`, `jarvisd service restart` | Control the running service. |
| `jarvisd service status` | Show the service manager, its state and process, the data directory, and whether the server answers its health check. |
| `jarvisd service uninstall` | Remove the service and the firewall rules `doctor --fix` added. Keeps your data unless you add `--purge`. See [Uninstall](../install/uninstall.md). |

| Option | Meaning |
|---|---|
| `--user` | Linux only, any service command: a systemd user service for your own account, which needs no root (data in `~/.jarvisd`). |
| `--bin PATH` | `install` only. The jarvisd program the service runs. Default: the one you are running. |
| `--run-as USER` | `install` only, macOS only: the account the service runs as. Default: the account that ran `sudo`. |
| `--no-start` | `install` only. Register the service without starting it. |
| `--json` | `status` only. Print the status as JSON. |
| `--wait DURATION` | `status` only. Wait up to this long (for example `60s`) for the server to be running and healthy. |
| `--purge` | `uninstall` only. Also delete the data directory, the env file and the service account. This deletes everything Jarvis knows. It asks first. |
| `--yes` | With `uninstall --purge`: don't ask. |
| `--keep-firewall` | `uninstall` only. Leave the firewall rules in place. |

A healthy server looks like this (the details differ by system):

```text
$ jarvisd service status
supervisor: systemd
state:      running, pid 1234
home:       /var/lib/jarvisd
health:     ok (http://127.0.0.1:7700/health)
```

## doctor

```text
jarvisd doctor [--json] [--fix]
```

Checks that nodes and phones can reach the server, and prints one line per check, `OK`, `WARN` or `FAIL`, with the command that fixes it where there is one. It exits with an error when any check fails. Start here when something doesn't connect; [Troubleshooting](../troubleshooting/index.md#start-with-jarvisd-doctor) explains each check.

It checks:

- **listening**: the server answers on each of its ports;
- **ports**: no other program holds a port the server needs;
- **firewall**: the host firewall (ufw or firewalld on Linux, the macOS firewall, Windows Defender Firewall) lets your local network in;
- **network profile** (Windows): the active network is not marked Public;
- **sleep** (macOS): the Mac doesn't go to sleep;
- **data directory** (Linux, macOS): only the server's account can read the data directory and database;
- **legacy stack**: the old Docker install isn't running and holding ports or GPU memory;
- **gpu memory** (Linux with an NVIDIA GPU): which other programs, the old stack included, hold GPU memory that jarvisd's models then can't use;
- **MQTT**: the message broker asks clients for credentials.

| Option | Meaning |
|---|---|
| `--json` | Print the checks as JSON (`name`, `status`, `detail`, and the fix when there is one). |
| `--fix` | Apply the firewall fix: allow the server's ports from your private local network only, in rules tagged `jarvisd`, then check again. Needs `sudo` (or an Administrator prompt). |

## setup-link

```text
jarvisd setup-link [--url] [--qr]
```

Until the first admin account exists, prints the setup wizard's link with its one-time token (`http://<host>:7710/setup...`). Afterwards it prints the admin web app's address. Run it with `sudo` when the server runs as a system service: the token file belongs to the service.

| Option | Meaning |
|---|---|
| `--url` | Print the address alone (for scripts). |
| `--qr` | Also draw it as a QR code, to open it on a phone. |

## upgrade

```text
jarvisd upgrade [--version vX.Y.Z [--allow-older]] [--check] [--rollback] [--bin PATH] [--user]
```

Installs a signed release from the [releases page](https://github.com/alexberardi/jarvis-server/releases). It checks the release's signature, snapshots the database into `backups/`, swaps the program (keeping the old one as `jarvisd.prev`), restarts the service and rolls back by itself if the new version doesn't come up healthy. It contacts GitHub when you run it. Full guide: [Upgrade](../install/upgrade.md).

| Option | Meaning |
|---|---|
| `--version vX.Y.Z` | Install this release instead of the newest. |
| `--allow-older` | With `--version`: allow an older (or the same) release. |
| `--check` | Only say whether a newer release exists. |
| `--rollback` | Undo the last upgrade: put `jarvisd.prev` back, and the database snapshot too if the new version had changed the database and never passed its health check. |
| `--bin PATH` | The jarvisd program to replace. Default: the one you are running. |
| `--user` | Linux: the service is a systemd user service. |

`JARVISD_RELEASE_BASE` (a URL or a directory) makes `upgrade` read a release from there instead of GitHub: a flat folder with `SHA256SUMS`, `SHA256SUMS.minisig` and the archives. Use it to upgrade a server that can't reach the internet.

## version

```text
jarvisd version
```

Prints the release this jarvisd program is, such as `v0.1.0-rc18`.

## migrate status

```text
jarvisd migrate status
```

Shows each module's database migration state. Useful when an upgrade or a downgrade stops at start.

## import-legacy

```text
jarvisd import-legacy (--compose DIR | --from postgres://USER:PASS@HOST:PORT) [--apply] [--accept-head DB=HEAD]...
```

Copies an old Docker install's users, households, nodes, rooms, devices, settings, memories, routines, contacts and inbox into jarvisd, keeping their ids so nodes and phones carry on. It reads the old PostgreSQL database read-only. Run it once, with jarvisd stopped, before the setup wizard. Without `--apply` it is a dry run that checks every row and writes nothing. The steps: [Migrating from the old install](../install/migrating-from-docker.md).

| Option | Meaning |
|---|---|
| `--compose DIR` | The old install's compose directory (`~/.jarvis/compose`); the database credentials come from its env files. |
| `--from postgres://...` | The old database's address and credentials, instead of `--compose`. |
| `--apply` | Write the import. |
| `--accept-head DB=HEAD` | Accept an old database at another schema version (repeatable). |

## import-recipes

```text
jarvisd import-recipes [--apply] [--household OLD=NEW]... [--park-unmatched] [--legacy-host HOST]... BUNDLE
```

Imports recipes, meal plans, staples and product mappings from an old install's recipes export (`BUNDLE`), owned by the accounts whose email addresses match. A dry run unless `--apply`. You can run it again after more people sign up.

| Option | Meaning |
|---|---|
| `--apply` | Write the import. |
| `--household OLD=NEW` | Map an old household to a new one by hand (repeatable). |
| `--park-unmatched` | Import the rows of people who have no account yet, unowned until they sign up. |
| `--legacy-host HOST` | The old recipes server's host: image links to it become local (repeatable). |

## install-from-app

```text
jarvisd install-from-app [--run-as USER] [--bin PATH] [--no-firewall] [--url-file FILE] [--qr] [--open] [--allow-no-service]
```

The desktop installers' privileged step: puts this program where the service runs it, then runs `service install` and `doctor --fix` (unless `--no-firewall`) and prints the address to open. The `.dmg`, `.exe` and `.deb` installers call it; you don't need to. `--open` (Linux) opens the setup link in the browser of whoever is at the screen; `--url-file`, `--qr` and `--allow-no-service` are for the installers too.
