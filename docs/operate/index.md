# Operate

Running a Jarvis Automation server day to day: the `jarvisd` command, where the data lives and how to back it up, the ports nodes and phones use, what reaches the internet, and what to do when something doesn't connect.

Jarvis Automation is a **pre-release** (release candidate rc18.6). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*. These pages describe rc18.6 and say where older releases differ.

| Page | Read it to |
|---|---|
| [The jarvisd command](cli.md) | Look up a command: the service, `doctor`, `setup-link`, `upgrade`, the imports. |
| [Data and backups](data-and-backups.md) | Find the data directory on your system, back it up and restore it. |
| [Ports, firewall and mDNS](network.md) | See which ports to open, let your network through the firewall, and how desktop agents find the server (phones are given its address). |
| [Network egress and offline mode](../security/offline-mode.md) | See everything that can reach the internet, and keep the server offline. |
| [Troubleshooting](../troubleshooting/index.md) | Fix a server that doesn't start or that phones and nodes can't reach. |
| [Security](../security/index.md) | Read how Jarvis handles accounts, keys and your data. |

## The commands you'll use most

```bash
jarvisd service status     # is it running, and does it answer?
jarvisd doctor             # can nodes and phones reach it?
sudo jarvisd doctor --fix  # open the firewall to your local network
sudo jarvisd setup-link    # the setup wizard's link again
sudo jarvisd service restart  # after editing jarvisd.env
```

On Windows, run them in an Administrator PowerShell instead of with `sudo`.

Running the old Docker install? Its pages are frozen under [Legacy](../legacy/index.md), including its [environment variables](../legacy/reference/env-vars.md), [configuration](../legacy/getting-started/configuration.md) and [troubleshooting](../legacy/troubleshooting.md).
