# Setup wizard

Once the server is running, open `http://<host>:7710/setup` in a browser (`<host>` is the machine running the server, or `localhost` on that machine) to finish setting up. The installers open it for you.

Jarvis Automation is a **pre-release** (release candidate rc18.7). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## The setup link and its token

The link the installer opens looks like this:

```text
http://<host>:7710/setup#token=…
```

The part after `#token=` is the **setup token**: a one-time secret that proves you can reach the server itself, so nobody else on your network can create the first admin account before you. The server writes it to `setup-token` in its [data directory](../operate/data-and-backups.md#where-the-data-lives) on first start, readable only by the server's account, and deletes it once the first admin account exists.

To print the link again, run this on the server:

```sh
sudo jarvisd setup-link          # add --qr to show a QR code
```

`--qr` draws the link as a QR code in the terminal: scan it with your phone to open the wizard there, which suits a server without a screen. Once setup is done, `jarvisd setup-link` prints the admin's address instead. On Windows, run it in an administrator PowerShell without `sudo`; on Linux with a `--user` install, without `sudo`.

From another device, use the server's address, not `localhost`: for example `http://192.168.1.20:7710/setup#token=…`.

## The steps

The wizard saves each step as you go: close the tab and the link opens where you left off.

1. **Check**: checks that phones, voice nodes and other computers can reach the server. If something is blocked (usually the firewall), it shows the check that failed and its fix.
2. **Account**: creates the first account, the household's admin.
3. **Hardware**: shows what the server found on this machine, which decides the models it can run.
4. **Language model**: understands requests and writes the answers; the biggest download. The wizard suggests one that fits and marks the others **Fits** or not; see [Requirements and choosing a model](requirements.md).
5. **Speech-to-text**: turns what you say to a voice node into text. Needed for voice.
6. **Voice**: how Jarvis sounds when it answers. Needed for voice.
7. **Voice recognition** (optional): tells household members apart by voice.
8. **Memory & search** (optional): lets Jarvis find related memories and notes. Small, and runs on the CPU.
9. **Privacy**: asks what may leave the server, such as add-on commands from the Pantry and push notifications to phones.
10. **This computer** (optional): **Also use Jarvis Automation on this computer** downloads the [desktop agent](../agent/index.md) for the computer you are on, pairs it with the server and, if you tick it, sets up the browser extension. **Skip for now** leaves it for later; the admin's **Add-ons** page has the same download.
11. **Done**: the wizard hands over to the admin.

Steps 4 to 8 each pick the model for one job and suggest one that fits this machine. Nothing large is downloaded until you confirm a step; the download then carries on while you move to the next one. **Install everything recommended**, on the first of them, confirms all five suggestions at once. Each can be skipped (**Skip for now** on the three Jarvis needs, **Skip** on the two optional ones) and set later on the admin's **Models** page.

After setup, the admin stays on port 7710 (`http://<host>:7710`). Phones and voice nodes need the server's address, `http://<host>:7700`: you type it into the [mobile app](mobile-app.md), and the app passes it to a voice node when it sets the node up. Only the [desktop agent](../clients/desktop-agent.md) finds the server on the network by itself.

## Next

- Add a computer: the [desktop agent](../clients/desktop-agent.md).
- Add a [voice node](voice-node.md) and the [mobile app](mobile-app.md).

If the wizard doesn't open, or opens on the server but not from another device, see [Troubleshooting](../troubleshooting/index.md#the-setup-wizard-doesnt-open).
