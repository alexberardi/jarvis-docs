# Status and troubleshooting

## Status

```bash
jarvis-agent status
```

It shows whether the computer is paired, whether it reaches your server, and what this computer can do right now. In Jarvis Automation, **Add-ons** → **Your devices** shows each computer and its browser extension. `jarvis-agent browser status` checks browser control alone ([Browser control](browser.md#check-that-it-works)).

## Troubleshooting

### "That address doesn't look like a Jarvis Automation server"

Something answered at the address you typed, but not a Jarvis Automation server. Check the host and port. **No Jarvis Automation server answered at …** means nothing answered: check that the server is running and that this computer can reach it.

### I allowed a permission but it still doesn't work

Some macOS grants apply only to a fresh start. Quit the agent from the shield icon's menu and open the app again ([macOS permissions](macos-permissions.md)).

### Jarvis says it can't see or control the page

Jarvis may say that the browser doesn't let extensions read or control this page. Check, in order:

1. **Website access** is on ([steps](browser.md#turn-on-website-access)), and you **reloaded the tab** since turning it on.
2. The tab isn't a **private window** the extension isn't allowed in ([steps](browser.md#private-windows)).
3. The page isn't one browsers keep from every extension: `about:` and `chrome://` pages, the extension stores (addons.mozilla.org, the Chrome Web Store) and some built-in viewers. Jarvis can't act on those.

### A macro recording only shows "Opened" steps

Recording is [in progress](index.md#in-progress). If you try it, a recording that lists only **Opened** steps (no **Clicked** or **Typed** steps) means website access is off: [turn it on](browser.md#turn-on-website-access), **reload the tab**, and record again. In a private window, also allow [private windows](browser.md#private-windows).

### `jarvis-agent browser status` says "no browser connected"

The extension isn't installed or is disabled in that browser, or the browser isn't running. Install it ([Browser control](browser.md#install-the-extension)) and check that it's enabled on the extensions page. `found, not registered` means you need to run `jarvis-agent browser install` again (for example after moving the `jarvis-agent` binary).
