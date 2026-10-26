# Server on macOS

Install the Jarvis Automation server on a Mac that stays on: it is the server for your whole household. The installer is a disk image with one app in it; there is nothing to type.

Jarvis Automation is a **pre-release** (release candidate rc18.7). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Before you start

- A Mac with **Apple silicon** (M1 or later). Intel Macs are not supported.
- An administrator account: the installer asks for your password once.
- Memory decides which model runs well; see [Requirements and choosing a model](requirements.md).

## Install

1. From the newest release, download `Jarvis-Automation-Server-<version>.dmg`, where `<version>` is the release's version, such as `0.1.0-rc18.7`.
2. Open it and drag **Jarvis Automation Server** to **Applications**.
3. Open **Jarvis Automation Server** from Applications. macOS asks whether to open an app downloaded from the internet: click **Open**. The app is signed and notarized by Apple.
4. The app says it runs in the background on this Mac. Leave **Let devices on my network reach it** ticked, so phones, voice nodes and other computers can reach the server, and click **Install**.
5. Enter your password when macOS asks.

The app installs the server as a background service and opens the [setup wizard](setup-wizard.md) in your browser. macOS shows a **Background item added** notification for it; that is expected.

The service starts with the Mac, before anyone logs in, and runs as your account. Your data is in `~/.jarvisd`; see [Where the data lives](../operate/data-and-backups.md#where-the-data-lives).

## Open it again later

Opening **Jarvis Automation Server** again opens the setup wizard, or the admin once setup is done. It asks first in two cases:

- After you stopped the server from the admin, it offers **Start**.
- When the app carries a newer server than the one installed (you downloaded a newer disk image), it offers **Update**. See [Upgrade](upgrade.md).

To uninstall, hold **Option** while you open the app and choose **Uninstall…**. It keeps your data unless you say otherwise; see [Uninstall](uninstall.md).

## From a terminal instead

`install.sh` installs the same server from a terminal, which suits a Mac you reach over SSH. See [Advanced one-liners](one-liners.md).

## Next

Finish in the [setup wizard](setup-wizard.md) at `http://<host>:7710/setup`. If it didn't open, see [The setup wizard doesn't open](../troubleshooting/index.md#the-setup-wizard-doesnt-open).
