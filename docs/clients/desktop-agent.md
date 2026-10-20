# Desktop Agent & Browser Control

The **Jarvis desktop agent** (`jarvis-agent`) runs on your own computer and connects to your Jarvis server. With the **Jarvis Browser Control** extension it lets Jarvis work with your browser: list, open, switch and close tabs, read a page, fill in fields, click buttons and control audio and video. It also records the browser macros you teach Jarvis ([Teach Jarvis](#macros-teach-jarvis)).

The extension talks only to the desktop agent on the same computer, through the browser's native-messaging channel. It makes no network requests of its own. What it reads goes to the agent and then to your own Jarvis server; see the [Privacy Policy](../security/privacy-policy.md#information-the-desktop-agent-and-browser-extension-handle).

`jarvis-agent` ships in the [jarvis-server](https://github.com/alexberardi/jarvis-server) release archives (and as a `.deb` for Debian and Ubuntu). Enroll it with your server first; enrolling then offers to set up browser control.

!!! warning "Macros need website access"
    Installing the extension is not enough. The extension also needs **access to all websites**,
    and the browser lets you switch that off (Firefox may leave it off). Without it, Jarvis can
    still list and open tabs, but a macro recording captures **only page loads** (no clicks or
    typing), and Jarvis can't read or act on pages. [Turn on website access](#turn-on-website-access)
    right after installing.

## Install the extension

Run this on the computer, as the user who uses the browser:

```bash
jarvis-agent browser install
```

It registers the agent with every supported browser it finds (Firefox, Chrome, Edge, Brave, Arc, Vivaldi; `--all` registers with all of them, found or not) and prints the next step for each.

=== "Firefox"

    Firefox gets a Mozilla-signed `.xpi`. `jarvis-agent browser install` asks Firefox to install it:

    1. Firefox shows **Add "Jarvis Browser Control"?**. Click **Add**.
    2. Then [turn on website access](#turn-on-website-access).

    If Firefox doesn't open (or you passed `--no-open`), the command prints where it saved the `.xpi`. Open that file in Firefox, or drag it onto a Firefox window, and click **Add**.

=== "Chrome, Edge, Brave, Arc, Vivaldi"

    The command writes the extension to a folder and prints its path. Load it once:

    1. Open the extensions page: `chrome://extensions` (`edge://extensions`, `brave://extensions`).
    2. Turn on **Developer mode**.
    3. Click **Load unpacked** and choose the folder the command printed.
    4. **Jarvis Browser Control** appears. Keep that folder: the browser loads the extension from there.
    5. Then [turn on website access](#turn-on-website-access).

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

## Check that it works

1. Make sure the agent is running (`jarvis-agent run`, or it starts at login), then run:

    ```bash
    jarvis-agent browser status
    ```

    Each browser should show `registered`, and the last line should read `Agent: running; connected: ...` with your browser in it. `no browser connected` means the extension isn't installed or is turned off.

2. `status` shows the connection; depending on your version it may not say whether website access is on. To check that, [record a short macro](#macros-teach-jarvis): open a page, click a link or a button, type something, stop recording. The recording should list **Clicked ...** and **Typed ...** steps, not only **Opened ...** steps.

## Macros (Teach Jarvis)

Teach Jarvis records what you do in the browser once, so Jarvis can repeat it later.

- **Start:** "Jarvis, record this macro" (or "watch me do this"), **Record a macro…** in the Jarvis Automation menu, or `jarvis-agent computer record start`.
- **Stop:** "I'm done" (or "stop recording"), **Stop recording** in the menu, or `jarvis-agent computer record stop`.

Each step you take becomes a line in the recording, such as **Opened** example.com, **Clicked** Download CSV or **Typed** "May" in Month. Review recordings on the **Recordings** page of the jarvisd web app; the workflows Jarvis learns from them are on its **Workflows** page.

Recording works only in the browser for now, and needs the extension's [website access](#turn-on-website-access).

## Troubleshooting

### My recording only shows "Opened" steps

The extension can see tabs load but not the pages themselves: website access is off. [Turn it on](#turn-on-website-access), **reload the tab**, and record again. In a private window, also allow [private windows](#private-windows).

### Jarvis says it can't see or control the page

Jarvis may say that the browser doesn't let extensions read or control this page. Check, in order:

1. **Website access** is on ([steps](#turn-on-website-access)), and you **reloaded the tab** since turning it on.
2. The tab isn't a **private window** the extension isn't allowed in ([steps](#private-windows)).
3. The page isn't one browsers keep from every extension: `about:` and `chrome://` pages, the extension stores (addons.mozilla.org, the Chrome Web Store) and some built-in viewers. Jarvis can't act on those.

### `jarvis-agent browser status` says "no browser connected"

The extension isn't installed or is disabled in that browser, or the browser isn't running. Install it ([above](#install-the-extension)) and check that it's enabled on the extensions page. `found, not registered` means you need to run `jarvis-agent browser install` again (for example after moving the `jarvis-agent` binary).

## Remove it

```bash
jarvis-agent browser uninstall
```

This unregisters the agent from every browser. Remove the extension itself in each browser: Firefox `about:addons` → **Jarvis Browser Control** → **Remove**; Chrome-family browsers: the extensions page → **Jarvis Browser Control** → **Remove**.
