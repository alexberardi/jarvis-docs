# Troubleshooting

Most problems with a Jarvis Automation server show up in two places: `jarvisd doctor`, which checks what nodes and phones need, and the server's log. Start with those, then look for your symptom below.

Running the old Docker install? See [Troubleshooting the old Docker install](../legacy/troubleshooting.md).

!!! tip "Having trouble?"

    Reach out here: [:fontawesome-brands-discord: **Ask in the Jarvis help channel**](https://discord.gg/9SuQFVexxJ). We're happy to help.

## Start with jarvisd doctor

On the server, run:

```bash
jarvisd doctor
```

It prints one line per check, `OK`, `WARN` or `FAIL`, and under a problem the command that fixes it. On a Linux server with ufw blocking the ports, for example (this sample is the next release's three-port layout; on rc18 the lines also count and list the legacy ports):

```text
OK    listening: jarvisd answers on all 3 TCP ports
FAIL  firewall 192.168.1.0/24: ufw drops 7700/tcp, 7710/tcp, 1884/tcp, 5353/udp from 192.168.1.0/24: nodes and phones can't reach jarvisd, though it works from this machine
      fix:
        sudo ufw allow from 192.168.1.0/24 to any port 7700,7710,1884 proto tcp comment jarvisd
        ...
OK    data directory: /var/lib/jarvisd and its database are owner-only
OK    legacy stack: no legacy Jarvis Docker stack running
OK    mqtt anonymous: the MQTT broker requires credentials
```

If a check can't read what it needs (a firewall's rules, a data directory that belongs to the service), it says so: run `sudo jarvisd doctor` for the full answer. `jarvisd doctor --json` prints the same as JSON.

| Check | When it fails or warns | What to do |
|---|---|---|
| **listening** | Nothing answers on one of the server's ports. | The server isn't running, or stopped while starting. Run `jarvisd service status`, then [read the log](#read-the-log). |
| **ports** | Another program holds a port the server needs, so it can't start. | The `fix:` line shows which program. If it is the old Docker install, stop it first. |
| **firewall** | The host firewall drops the server's ports from your local network. | `sudo jarvisd doctor --fix` (an Administrator PowerShell on Windows). See [Firewall](../operate/network.md#firewall). |
| **network profile** (Windows) | Windows treats your network as Public; the server's firewall rule covers Private networks only. | Settings → Network & internet → your network → **Private network**. |
| **sleep** (macOS) | The Mac sleeps when idle, and a sleeping server doesn't answer. | `sudo pmset -a sleep 0`, or prevent sleep in System Settings. |
| **data directory** (Linux, macOS) | Other accounts on the machine can read the data directory, or some of its files belong to another account. | Follow the `fix:` line. See [Data and backups](../operate/data-and-backups.md#where-the-data-lives). |
| **legacy stack** | The old Docker install is running and uses the server's ports or the GPU. | The `fix:` line stops it and keeps it from starting at boot; its data is kept. To bring its data over: [Migrating from the old install](../install/migrating-from-docker.md). |
| **mqtt anonymous** | `JARVIS_MQTT_ALLOW_ANONYMOUS=1` lets anyone on your network read every message. | Remove it from `jarvisd.env` and restart. |
| **env file** | `jarvisd.env` can't be read, so the checks used the default ports. | Run `sudo jarvisd doctor`. |

## Read the log

Where the server writes its log depends on the system:

=== "Linux"

    The service logs to the system journal:

    ```bash
    journalctl -u jarvisd -n 200          # the last 200 lines
    journalctl -u jarvisd -f              # follow it live
    ```

    For a user service (`--user`): `journalctl --user -u jarvisd`.

=== "macOS"

    ```bash
    tail -n 200 ~/.jarvisd/logs/jarvisd.log
    tail -f ~/.jarvisd/logs/jarvisd.log
    ```

    Run it as the account the server runs as.

=== "Windows"

    In an Administrator PowerShell:

    ```powershell
    Get-Content "$env:ProgramData\jarvisd\logs\jarvisd.log" -Tail 200
    Get-Content "$env:ProgramData\jarvisd\logs\jarvisd.log" -Wait
    ```

    The file is rotated at 10 MB; the last three are kept as `jarvisd.log.1` to `.3`.

Once the server is running, the admin web app's **Logs** page shows the same messages and lets you filter them. The log file matters most when the server doesn't start, because that page can't open then.

For more detail, add `JARVIS_LOG_LEVEL=debug` to `jarvisd.env` and restart (`jarvisd service restart`). Remove it when you're done.

## The server doesn't start

1. `jarvisd service status` shows whether the service manager started it and whether it answers its health check.
2. `jarvisd doctor` names a port another program holds, or the old Docker install.
3. [The log](#read-the-log) shows why it stopped. Look at the last lines.

If the log says the database was changed by a newer jarvisd, you are running an older version than the one that last ran on this data, for example after copying an older program over a newer one. Install the newer release again, or go back with `sudo jarvisd upgrade --rollback`, or restore a [backup](../operate/data-and-backups.md#restore) from that version. `jarvisd serve --allow-downgrade` exists for experts and can damage data.

## The setup wizard doesn't open

- Print the link again: `sudo jarvisd setup-link` (or `jarvisd setup-link --qr` for a phone). Once the first admin account exists, it prints the admin web app's address instead.
- From another device, use the server's address, not `localhost`: `http://<server-ip>:7710/setup`.
- If it works on the server but not from another device, see the next section.

## Phones and nodes can't connect, but it works on the server

This is almost always the firewall.

1. Run `jarvisd doctor` and look at the **firewall** lines.
2. Run `sudo jarvisd doctor --fix` (an Administrator PowerShell on Windows), which opens the ports to your local network only.
3. On Windows, make sure the network is **Private**. On macOS, turn off **Block all incoming connections**.
4. Check the device is on the same network: guest Wi-Fi and Wi-Fi with "client isolation" keep devices apart.

If the mobile app doesn't find the server by itself, type the address (`http://<server-ip>:7700`): mDNS doesn't cross networks or VLANs. See [mDNS discovery](../operate/network.md#mdns-discovery).

## An older node or app can't reach a service

Older nodes and apps may still use the per-service ports (7703 for the command center, and so on). On rc18 these legacy ports are always open, so this doesn't apply to an rc18 server: look at the [firewall](#phones-and-nodes-cant-connect-but-it-works-on-the-server) instead.

From the next release, a fresh install doesn't open them. To bring them back from the next release, turn on `server.legacy_ports` in the admin web app's **Settings** and restart, or set `JARVIS_LEGACY_PORTS=1` in `jarvisd.env`. See [Legacy ports](../operate/network.md#legacy-ports).

## The server stops answering after a while (macOS)

The Mac went to sleep. `jarvisd doctor` warns about this; `sudo pmset -a sleep 0` keeps it awake.

## An upgrade failed

`jarvisd upgrade` rolls itself back when the new version doesn't come up healthy, and says so. To go back by hand: `sudo jarvisd upgrade --rollback`. The database snapshot it took is in the data directory's `backups/` folder. See [Upgrade](../install/upgrade.md).

## Desktop Agent & Browser Issues

### Macro recording only shows "Opened" steps, or Jarvis can't see the page

**Cause:** the Jarvis Browser Control extension doesn't have access to websites. It can see tabs load, but can't read or act on pages, so a recording captures no clicks or typing.

**Fix:** turn on website access (Firefox: `about:addons` → **Jarvis Browser Control** → **Permissions** → **Access your data for all websites**; Chrome-family browsers: **Details** → **Site access** → **On all sites**), then **reload the tab**. Private windows need the extension allowed in them too. Full steps: [Desktop agent](../clients/desktop-agent.md#troubleshooting).

## Getting Help

If your problem isn't listed here, collect:

- `jarvisd version`
- `jarvisd service status`
- `jarvisd doctor` (or `jarvisd doctor --json`)
- the last 200 lines of [the log](#read-the-log)

Then [open an issue on GitHub](https://github.com/alexberardi/jarvis-server/issues) with them and your system (Linux distribution, macOS or Windows version), or [:fontawesome-brands-discord: ask in the Jarvis help channel](https://discord.gg/9SuQFVexxJ), often the fastest way to get unstuck. Check the log for passwords or tokens before you post it.
