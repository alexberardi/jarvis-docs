# Desktop agent

**Jarvis Automation Agent** runs on your own computer (macOS, Windows or Linux) and connects it to your Jarvis Automation server. With it, Jarvis can listen for "Hey Jarvis" on the computer, open apps and links, set the volume, find and switch windows, type what you dictate, read your screen when you ask, and, with the **Jarvis Browser Control** extension, work with your browser tabs and pages.

Jarvis Automation is a **pre-release** (release candidate rc18). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

You need a running server first: [install it](../install/index.md) and finish its [setup wizard](../install/setup-wizard.md) (`http://<host>:7710/setup`). What the agent and the extension read goes only to that server; see the [Privacy Policy](../security/privacy-policy.md#information-the-desktop-agent-and-browser-extension-handle).

## Install

Install it as yourself, on the computer you want Jarvis to use. In the file names below, `<version>` is the release's version, such as `0.1.0-rc18`.

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
2. **Add this computer**, with a [pairing code](#pair-this-computer) or by signing in with your Jarvis Automation email and password.
3. **Let Jarvis use your browser:** a button for the [browser extension](#browser-control).
4. **Permissions:** on a Mac, the [macOS permissions](#macos-permissions); on GNOME or KDE with Wayland, [Allow typing](#dictation-on-linux).
5. **Voice:** **Listen for "Hey Jarvis"** on or off, and **Test my microphone**. Listening is on by default.

Click **Done** to finish. To come back later, choose **Set up / Settings…** in the shield icon's menu, or open the app again.

## Pair this computer

Pairing adds the computer without typing a password into it. Anyone in your household can approve it.

1. On the setup page, choose **Show a pairing code**. The computer shows a code such as `ABCD-EFGH` and its own name.
2. In Jarvis Automation (the web app, `http://<host>:7710`), open **Add-ons** (admins also find it on **Nodes**). Under **Pending pairings**, type the code, choose the household and the room, and click **Approve**. **Deny** refuses it.
3. Back on the computer, the page names the household and who approved it. Click **Yes, add it**. **No, cancel** adds nothing.

A code works once and only for 10 minutes; if it runs out, show a new one. From a terminal, `jarvis-agent enroll --server <host>` shows a code the same way.

## macOS permissions

macOS asks you to allow each of these once. On the setup page, **Allow** shows macOS's own prompt and opens the right pane of **System Settings → Privacy & Security**; the tick turns green when it's granted.

| Permission | What it lets Jarvis do |
|---|---|
| **Microphone** | Hear "Hey Jarvis" and what you say next |
| **Accessibility** | Type what you dictate, press keys, and focus, minimise or close windows |
| **Automation (System Events)** | See which windows are open and switch between them, also by app name ("type hello in Notes") |
| **Screen Recording** | Read what's on your screen, only when you ask ("what does this error say?") |
| **Input Monitoring** | Watch what you do in an app when you ask it to learn a task, never what you type into a password field. Not needed yet: see [In progress](#in-progress) |

Some grants only apply to a fresh start of the agent. When the page says **Granted — restart Jarvis to apply**, choose **Quit Jarvis Automation Agent** in the shield icon's menu, then open the app again.

Updates keep your grants: they are tied to the app's signature, which stays the same.

## Dictation on Linux

Dictation (typing what you say, "press enter", "click OK") works out of the box on Hyprland, sway and other wlroots compositors, and on X11.

**GNOME and KDE on Wayland** need a one-time permission. Click **Allow typing** on the setup page, or run:

```bash
jarvis-agent dictation allow
```

Your desktop asks once: choose **Allow** (it may say **Share**) and keep its "remember" option on. `jarvis-agent dictation status` shows the grant and `jarvis-agent dictation revoke` forgets it. On GNOME and KDE, Jarvis types into the window in front; it can't switch to an app you name first.

Reading the screen works on Hyprland and sway and needs `grim` installed. It isn't available on GNOME, KDE or X11 yet.

## Browser control

The **Jarvis Browser Control** extension lets Jarvis list, open, switch and close tabs, read a page, fill in fields, click buttons and control audio and video. It talks only to the agent on the same computer, through the browser's native-messaging channel, and makes no network requests of its own.

!!! warning "Website access must be on"
    Installing the extension is not enough. The extension also needs **access to all websites**,
    and the browser lets you switch that off (Firefox may leave it off). Without it, Jarvis can
    still list and open tabs, but it can't read or act on pages.
    [Turn on website access](#turn-on-website-access) right after installing.

### Install the extension

When you pair the computer, the agent registers itself with the browsers it finds. Then add the extension to your browser. To register again, or with a browser installed later, run this as the user who uses the browser:

```bash
jarvis-agent browser install
```

It registers the agent with every supported browser it finds (Firefox, Chrome, Edge, Brave, Arc, Vivaldi; `--all` registers with all of them, found or not) and prints the next step for each.

=== "Firefox"

    Firefox gets the **Firefox add-on**, signed by Mozilla. `jarvis-agent browser install` asks Firefox to install it:

    1. Firefox shows **Add "Jarvis Browser Control"?**. Click **Add**.
    2. Then [turn on website access](#turn-on-website-access).

    If Firefox doesn't open (or you passed `--no-open`), the command prints where it saved the `.xpi`. Open that file in Firefox, or drag it onto a Firefox window, and click **Add**.

=== "Chrome, Edge, Brave, Arc, Vivaldi"

    The extension's **Chrome Web Store** listing isn't public yet. Until it is, load the copy the agent ships with. `jarvis-agent browser install` writes it to a folder and prints its path:

    1. Open the extensions page: `chrome://extensions` (`edge://extensions`, `brave://extensions`).
    2. Turn on **Developer mode**.
    3. Click **Load unpacked** and choose the folder the command printed.
    4. **Jarvis Browser Control** appears. Keep that folder: the browser loads the extension from there.
    5. Then [turn on website access](#turn-on-website-access).

    After the agent updates, click the reload button on **Jarvis Browser Control** on the extensions page, so the browser runs the new copy.

## Turn on website access

=== "Firefox"

    1. Open `about:addons` (menu → **Add-ons and themes**).
    2. Click **Jarvis Browser Control**.
    3. Open the **Permissions** tab.
    4. Turn on **Access your data for all websites**.
    5. **Reload the tabs** you want Jarvis to use. Pages opened before the change still lack access.

=== "Chrome, Edge, Brave, Arc, Vivaldi"

    1. Open `chrome://extensions` (`edge://extensions`, `brave://extensions`).
    2. On **Jarvis Browser Control**, click **Details**.
    3. Under **Site access**, choose **On all sites**.
    4. **Reload the tabs** you want Jarvis to use.

### Private windows

Extensions don't run in private windows unless you allow it:

- **Firefox:** `about:addons` → **Jarvis Browser Control** → **Details** → **Run in Private Windows** → **Allow**.
- **Chrome-family browsers:** **Details** → turn on **Allow in Incognito**.

### Check that it works

In Jarvis Automation, open **Add-ons**: under **Your devices**, the computer reads **Browser extension connected**, or **Website access is off** with the steps to fix it.

On the computer, with the agent running:

```bash
jarvis-agent browser status
```

Each browser should show `registered`, and the last line should read `Agent: running; connected: ...` with your browser in it. `no browser connected` means the extension isn't installed or is turned off.

## Sign out

Signing out removes the computer from your server. Anyone who talks to a signed-in computer acts as the member who added it, so sign out a computer you hand on.

- **On the computer:** choose **Sign out of Jarvis Automation** in the shield icon's menu. The setup page opens, ready to add it again. If the server can't be reached, the computer signs out anyway and stays listed until someone removes it in Add-ons.
- **From Jarvis Automation:** **Add-ons** → **Your devices** → **Sign out** on the computer. The member who added it and the household's admins can do this.

## Updates

The agent updates itself to your server's version: when your server is upgraded, its computers follow (they check at start, when the server's version changes, and once a day). It installs only a release signed with the project's key, and if the new version doesn't come up within 2 minutes it goes back to the old one. The shield icon's menu shows the progress, such as "Updated to v0.2.0".

`jarvis-agent update` does the same by hand. Two cases need you:

- **Linux, from the `.deb`:** if the update asks for it, run `jarvis-agent install` once, so the agent keeps a copy it can update.
- **macOS, as a standard user** who can't write to `/Applications`: install the new `.dmg` yourself.

## In progress

!!! note ""
    These are being built. Don't rely on them yet.

    - **Computer control and macros** (Teach Jarvis): the **Computer control** switch in the shield icon's menu (off by default) and recording what you do so Jarvis can repeat it. Input Monitoring is for this.
    - **Store listings:** the Firefox add-on on addons.mozilla.org and the extension in the Chrome Web Store. Until they are public, the setup page's buttons open these docs, Firefox gets the add-on from the agent and Chrome-family browsers use **Load unpacked**.
    - **Voice on Windows**, and reading the screen on Windows, GNOME, KDE and X11.

## Troubleshooting

### "That address doesn't look like a Jarvis Automation server"

Something answered at the address you typed, but not a Jarvis Automation server. Check the host and port. **No Jarvis Automation server answered at …** means nothing answered: check that the server is running and that this computer can reach it.

### I allowed a permission but it still doesn't work

Some macOS grants apply only to a fresh start. Quit the agent from the shield icon's menu and open the app again ([macOS permissions](#macos-permissions)).

### Jarvis says it can't see or control the page

Jarvis may say that the browser doesn't let extensions read or control this page. Check, in order:

1. **Website access** is on ([steps](#turn-on-website-access)), and you **reloaded the tab** since turning it on.
2. The tab isn't a **private window** the extension isn't allowed in ([steps](#private-windows)).
3. The page isn't one browsers keep from every extension: `about:` and `chrome://` pages, the extension stores (addons.mozilla.org, the Chrome Web Store) and some built-in viewers. Jarvis can't act on those.

### A macro recording only shows "Opened" steps

Recording is [in progress](#in-progress). If you try it, a recording that lists only **Opened** steps (no **Clicked** or **Typed** steps) means website access is off: [turn it on](#turn-on-website-access), **reload the tab**, and record again. In a private window, also allow [private windows](#private-windows).

### `jarvis-agent browser status` says "no browser connected"

The extension isn't installed or is disabled in that browser, or the browser isn't running. Install it ([above](#install-the-extension)) and check that it's enabled on the extensions page. `found, not registered` means you need to run `jarvis-agent browser install` again (for example after moving the `jarvis-agent` binary).

## Remove it

[Sign out](#sign-out) first, so the computer leaves your household's list. Then open the setup page (**Set up / Settings…** in the shield icon's menu) and click **Remove Jarvis Automation Agent from this computer**. It stops the agent and deletes its login item, menu entries, browser registration, sign-in and settings. On a Mac, then drag the app from **Applications** to the Trash.

To remove only browser control:

```bash
jarvis-agent browser uninstall
```

This unregisters the agent from every browser. Remove the extension itself in each browser: Firefox `about:addons` → **Jarvis Browser Control** → **Remove**; Chrome-family browsers: the extensions page → **Jarvis Browser Control** → **Remove**.
