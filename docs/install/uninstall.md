# Uninstall

How to remove the server and the desktop agent from macOS, Windows and Linux, and how to remove your data too if you want.

Jarvis Automation is a **pre-release** (release candidate rc18.8). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

Every way below **keeps your data** unless you ask for it to go: reinstall later and the server picks up where it left off. Deleting the data removes everything the server knows (accounts, households, devices, settings, models) and can't be undone. [Where the data lives](../operate/data-and-backups.md#where-the-data-lives) lists the folders; take a [backup](../operate/data-and-backups.md#back-up) first if you might want it back.

## macOS

1. Hold **Option** while you open **Jarvis Automation Server** from Applications.
2. Choose **Uninstall…**.
3. When it asks whether to also delete the data, **Keep data** is the default. Choose delete only if you want everything gone.

It removes the background service, the firewall entry and `/usr/local/bin/jarvisd`. Then drag the app from Applications to the Trash. When the server is stopped, opening the app normally also offers **Uninstall…**.

## Windows

1. Open **Settings → Apps**, find **Jarvis Automation Server** and choose **Uninstall**.
2. When it asks **Also delete Jarvis Automation's data?**, **No** is the default and keeps `%ProgramData%\jarvisd`.

It removes the service, its updater, the firewall rule and the program folder. A silent uninstall keeps the data unless it is given `/PURGE`.

## Debian and Ubuntu

Remove the package and keep the data in `/var/lib/jarvisd`:

```sh
sudo apt remove jarvis-automation-server
```

Remove it and delete the data, the settings in `/etc/jarvisd` and the `jarvisd` account:

```sh
sudo apt purge jarvis-automation-server
```

Either removes the service, the program and the firewall rules the install added.

## Installed with a script

Run the same script with `--uninstall` (`-Uninstall` on Windows). It removes the service, the firewall rules and the program, and keeps the data. Add `--purge` (`-Purge`) to delete the data too; it asks you to type a confirmation first.

```sh
sh install.sh --uninstall
sh install.sh --uninstall --purge
```

For a `--user` install, add `--user`.

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall -Purge
```

With `--purge`, `--yes` skips the confirmation, for scripts. If you no longer have the script, download it again from the release, as in [Advanced one-liners](one-liners.md).

`jarvisd service uninstall` does the same from the server's own command line but leaves the program in place; add `--purge` to delete the data. See [the jarvisd CLI](../operate/cli.md).

## The desktop agent

Each person removes their own copy from the agent's setup page; see [Desktop agent: Remove it](../agent/index.md#remove-it).
