# Server on Windows

Install the Jarvis Automation server on a Windows PC that stays on: it is the server for your whole household. The installer is a normal setup program; there is nothing to type.

Jarvis Automation is a **pre-release** (release candidate rc18.9). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Before you start

- 64-bit Windows on an Intel or AMD processor (`amd64`).
- An administrator account: setup asks for administrator rights.
- Memory and the graphics card decide which model runs well; see [Requirements and choosing a model](requirements.md).

The Windows server is built and tested automatically for every release, but has not yet been tried on many real PCs. If something goes wrong, the [Discord](https://discord.gg/9SuQFVexxJ) is the place to say so.

## Install

1. From the newest release, download `Jarvis-Automation-Server-Setup-<version>.exe`, where `<version>` is the release's version, such as `0.1.0-rc18.9`.
2. Open it. Windows may say **Windows protected your PC**: Windows shows this for any installer that isn't signed with a paid code-signing certificate, and Jarvis Automation's isn't. Click **More info**, then **Run anyway**. To check the file first, compare its SHA-256 with its line in the release's `SHA256SUMS` (`Get-FileHash <file>` in PowerShell).
3. Allow setup to make changes when Windows asks.
4. On the **Tasks** page, leave **Let phones, voice nodes and other computers on my local network reach Jarvis Automation** ticked. It opens the Windows firewall for your local network only. Tick the desktop shortcut if you want one.
5. Click through to **Finish**.

Setup installs the server as a Windows service that starts with the PC, and opens the [setup wizard](setup-wizard.md) in your browser. The Start menu gets **Jarvis Automation Server**, which opens the admin on this PC later.

Your data is in `%ProgramData%\jarvisd` (usually `C:\ProgramData\jarvisd`), so upgrades keep it; see [Where the data lives](../operate/data-and-backups.md#where-the-data-lives).

## From a terminal instead

`install.ps1` installs the same server from PowerShell. See [Advanced one-liners](one-liners.md).

## Next

Finish in the [setup wizard](setup-wizard.md) at `http://<host>:7710/setup`. If it didn't open, see [The setup wizard doesn't open](../troubleshooting/index.md#the-setup-wizard-doesnt-open).

To remove it later, use **Settings → Apps**; see [Uninstall](uninstall.md).
