# Browser control

The **Jarvis Browser Control** extension lets Jarvis list, open, switch and close tabs, read a page, fill in fields, click buttons and control audio and video. It talks only to the agent on the same computer, through the browser's native-messaging channel, and makes no network requests of its own.

!!! warning "Website access must be on"
    Installing the extension is not enough. The extension also needs **access to all websites**,
    and the browser lets you switch that off (Firefox may leave it off). Without it, Jarvis can
    still list and open tabs, but it can't read or act on pages.
    [Turn on website access](#turn-on-website-access) right after installing.

## Install the extension

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

If Jarvis still can't act on a page, see [Troubleshooting](troubleshooting.md#jarvis-says-it-cant-see-or-control-the-page).
