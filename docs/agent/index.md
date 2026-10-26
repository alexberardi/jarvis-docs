# Desktop agent

**Jarvis Automation Agent** runs on your own computer (macOS, Windows or Linux) and connects it to your Jarvis Automation server. With it, Jarvis can listen for "Hey Jarvis" on the computer, open apps and links, set the volume, find and switch windows, type what you dictate, read your screen when you ask, and, with the **Jarvis Browser Control** extension, work with your browser tabs and pages.

Jarvis Automation is a **pre-release** (release candidate rc18.7). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

You need a running server first: [install it](../install/index.md) and finish its [setup wizard](../install/setup-wizard.md) (`http://<host>:7710/setup`). What the agent and the extension read goes only to that server; see the [Privacy Policy](../security/privacy-policy.md#information-the-desktop-agent-and-browser-extension-handle).

| Page | What it covers |
|---|---|
| [Pairing](pairing.md) | Adding the computer to your household, approved from the web app or the mobile app |
| [macOS permissions](macos-permissions.md) | The grants a Mac asks for, and what each one is for |
| [Browser control](browser.md) | The Jarvis Browser Control extension and its website access |
| [Voice and the island](voice.md) | "Hey Jarvis", follow-ups and the on-screen indicator |
| [Dictation](dictation.md) | Typing what you say, and the permission GNOME and KDE need |
| [What it can do](tools.md) | The tools the agent gives Jarvis |
| [Updates and settings](updates-settings.md) | Self-update and the settings file |
| [Status and troubleshooting](troubleshooting.md) | `jarvis-agent status` and common problems |
| [Raspberry Pi node (preview)](pi-node.md) | The same agent as a voice node on a Pi |

## Install

Install it as yourself, on the computer you want Jarvis to use. In the file names below, `<version>` is the release's version, such as `0.1.0-rc18.7`.

=== "macOS"

    1. Download `Jarvis-Automation-Agent-<version>.dmg` and open it.
    2. Drag **Jarvis Automation Agent** to **Applications**, then open it from there.

    The app is signed and notarized. It starts at login from then on and shows a shield icon in the menu bar.

=== "Windows"

    1. Download `Jarvis-Automation-Agent-Setup-<version>.exe` and run it. It installs for your account only and needs no admin rights.
    2. The installer isn't signed yet, so Windows may say **Windows protected your PC**. Click **More info**, then **Run anyway**.
    3. Leave **Put a shortcut on the desktop** ticked if you want one.

    The agent starts at login from then on and shows a shield icon in the notification area.

=== "Linux"

    **Debian and Ubuntu:** download `jarvis-automation-agent_<version>_amd64.deb` (`_arm64.deb` on ARM) and install it:

    ```bash
    sudo apt install ./jarvis-automation-agent_<version>_amd64.deb
    ```

    Then open **Jarvis Automation Agent** from the app menu. The first time, it sets itself up for your account.

    **Fedora, Arch and others:** download `install-agent.sh` from the same release and run it as yourself, not with `sudo`:

    ```bash
    sh install-agent.sh
    ```

    It checks the agent against the release's `SHA256SUMS` before installing it.

    The agent starts at login from then on. Its shield icon shows in panels with a tray (KDE Plasma, waybar, XFCE; GNOME needs the AppIndicator extension).

Each release carries `SHA256SUMS` and its signature, `SHA256SUMS.minisig`, so you can check a download before you open it: `sha256sum --ignore-missing -c SHA256SUMS` on Linux, `shasum -a 256 <file>` on macOS or `Get-FileHash <file>` in PowerShell, compared with the file's line in `SHA256SUMS`. [Advanced one-liners](../install/one-liners.md) covers the signature.

## Set it up

When the agent isn't set up yet, opening it opens **Set up Jarvis Automation** in your browser. The page is served by the agent on this computer only, and it walks through five steps:

1. **Find your Jarvis Automation server.** It looks on this computer and on your network. If your server isn't listed, type its address: the server's IP or name (`192.168.1.10`), or the address you open Jarvis Automation at (`http://<host>:7710`).
2. **Add this computer**, with a [pairing code](pairing.md) or by signing in with your Jarvis Automation email and password.
3. **Let Jarvis use your browser:** a button for the [browser extension](browser.md).
4. **Permissions:** on a Mac, the [macOS permissions](macos-permissions.md); on GNOME or KDE with Wayland, [Allow typing](dictation.md#dictation-on-linux).
5. **Voice:** **Listen for "Hey Jarvis"** on or off, and **Test my microphone**. Listening is on by default.

Click **Done** to finish. To come back later, choose **Set up / Settings…** in the shield icon's menu, or open the app again.

## Sign out

Signing out removes the computer from your server. Anyone who talks to a signed-in computer acts as the member who added it, so sign out a computer you hand on.

- **On the computer:** choose **Sign out of Jarvis Automation** in the shield icon's menu. The setup page opens, ready to add it again. If the server can't be reached, the computer signs out anyway and stays listed until someone removes it in Add-ons.
- **From Jarvis Automation:** **Add-ons** → **Your devices** → **Sign out** on the computer. The member who added it and the household's admins can do this.

## In progress

!!! note ""
    These are being built. Don't rely on them yet.

    - **Computer control and macros** (Teach Jarvis): the **Computer control** switch in the shield icon's menu (off by default) and recording what you do so Jarvis can repeat it. Input Monitoring is for this.
    - **Store listings:** the Firefox add-on on addons.mozilla.org and the extension in the Chrome Web Store. Until they are public, the setup page's buttons open these docs, Firefox gets the add-on from the agent and Chrome-family browsers use **Load unpacked**.
    - **Voice on Windows**, and reading the screen on Windows, GNOME, KDE and X11.

## Remove it

[Sign out](#sign-out) first, so the computer leaves your household's list. Then open the setup page (**Set up / Settings…** in the shield icon's menu) and click **Remove Jarvis Automation Agent from this computer**. It stops the agent and deletes its login item, menu entries, browser registration, sign-in and settings. On a Mac, then drag the app from **Applications** to the Trash.

To remove only browser control:

```bash
jarvis-agent browser uninstall
```

This unregisters the agent from every browser. Remove the extension itself in each browser: Firefox `about:addons` → **Jarvis Browser Control** → **Remove**; Chrome-family browsers: the extensions page → **Jarvis Browser Control** → **Remove**.
