# Advanced one-liners

Each release also carries install scripts, for a server you reach over SSH, a distribution without a package, or installing many machines the same way. They install the same server as the [macOS](macos.md), [Windows](windows.md) and [Linux](linux.md) installers.

Jarvis Automation is a **pre-release** (release candidate rc18). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

| Script | Installs | Runs on |
|---|---|---|
| `install.sh` | the server | Linux with systemd (amd64, arm64), macOS on Apple silicon |
| `install.ps1` | the server | Windows (Windows PowerShell 5.1 or later) |
| `install-agent.sh` | the [desktop agent](../agent/index.md) | any Linux |
| `install-pi.sh` | a [Raspberry Pi voice node](../clients/node-setup.md) (preview) | Raspberry Pi OS, 64-bit |

## Use the release's own link

While only pre-releases exist, take each script from its release's own address. GitHub's "latest release" links skip pre-releases, so they lead nowhere. The commands below use `v0.1.0-rc18` as the example tag: replace it with the newest tag on the [releases page](https://github.com/alexberardi/jarvis-server/releases). A script installs the release it came from.

## Linux and macOS: install.sh

```sh
curl -fsSLO https://github.com/alexberardi/jarvis-server/releases/download/v0.1.0-rc18/install.sh
less install.sh          # read it first
sh install.sh            # asks for sudo
```

Download it, then run it: piped straight into `sh`, a failed download would leave nothing to run, with no error.

The script:

1. downloads the server for your system and checks it against the release's `SHA256SUMS`, and the signature of that file too when `minisign` is installed ([below](#check-a-download));
2. places it in `/usr/local/bin/jarvisd` and registers the service (`jarvisd service install`);
3. runs `jarvisd doctor` and offers to open the firewall for your local network (answer **Y**, the default, unless you manage the firewall yourself);
4. prints the setup link, which looks like `http://<server-ip>:7710/setup#token=…`, and a QR code of it.

Open the link in a browser, or scan the QR code with your phone, to start the [setup wizard](setup-wizard.md). The part after `#token=` is the setup token; keep it to yourself.

Run the same script again to upgrade to the release it came from; see [Upgrade](upgrade.md).

### Options

Put them after `sh install.sh`. `sh install.sh --help` lists them too.

| Option | What it does |
|---|---|
| `--version <tag>` | Install that release, such as `v0.1.0-rc18`, instead of the one the script came from. |
| `--user` | Linux only: run the server as a service of your own account, without root. The program goes to `~/.local/bin`, the data to `~/.jarvisd`. Run it without `sudo`. |
| `--yes` | Answer yes for you: apply the firewall fix without asking. Use it where there is no terminal to ask in. |
| `--stop-legacy` | Stop the old Docker install on the same machine (its containers, and on macOS its background services and admin), so the new server can take its ports. Nothing is deleted. See [Migrating from the old install](migrating-from-docker.md). |
| `--force` | Reinstall even when this version is already installed. |
| `--uninstall` | Remove the service, the firewall rules and the program. Your data is kept. See [Uninstall](uninstall.md). |
| `--purge` | With `--uninstall`: also delete the data, after you type a confirmation. |
| `--base-url <url>` | Fetch the release files from your own mirror instead of GitHub (also `JARVISD_RELEASE_BASE`). The signature is still checked. |

Intel Macs are not supported. A Linux machine without systemd needs the release's archive and your own supervisor running `jarvisd serve`.

## Windows: install.ps1

In PowerShell (it asks for administrator rights if it doesn't have them):

```powershell
irm https://github.com/alexberardi/jarvis-server/releases/download/v0.1.0-rc18/install.ps1 | iex
```

It does what `install.sh` does: checks the download, places the server in `%ProgramFiles%\jarvisd`, registers the Windows service, offers the firewall rule for your local network and prints the setup link.

### Options

Options need the downloaded file:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -StopLegacy
```

| Option | What it does |
|---|---|
| `-Version <tag>` | Install that release instead of the one the script came from. |
| `-Yes` | Apply the firewall fix without asking. |
| `-StopLegacy` | Stop the old Docker install's containers. Nothing is deleted. |
| `-Force` | Reinstall even when this version is already installed. |
| `-Uninstall` | Remove the service, the firewall rule, the program and its `PATH` entry. Your data is kept. |
| `-Purge` | With `-Uninstall`: also delete `%ProgramData%\jarvisd`, after a confirmation. |
| `-BaseUrl <url>` | Fetch the release files from your own mirror instead of GitHub. |

Under `irm | iex` there is no file to pass options to; set them as environment variables first: `JARVISD_VERSION` for `-Version`, `JARVISD_RELEASE_BASE` for `-BaseUrl`, and `JARVISD_YES=1` for `-Yes`.

## Check a download

Each release carries `SHA256SUMS`, the checksums of its installers and archives, and `SHA256SUMS.minisig`, the project's signature of that file. `install.sh`, `install.ps1` and `install-agent.sh` are not in `SHA256SUMS`: they come over HTTPS from the release, so read them before you run them. `install-pi.sh`, the voice node installer, is listed, so you can check it first.

To check a file by hand, download it with `SHA256SUMS` and `SHA256SUMS.minisig` into one folder, then check the signature with [minisign](https://jedisct1.github.io/minisign/) and the file against the list:

```sh
minisign -Vm SHA256SUMS -P RWRyW6ICtU+iyX4p4RnS24ju0gRsWpxvv6B8pI9G+ZS01q8t8oupAQ8L
sha256sum --ignore-missing -c SHA256SUMS
```

`RWRyW6ICtU+iyX4p4RnS24ju0gRsWpxvv6B8pI9G+ZS01q8t8oupAQ8L` is the project's public key, the same one the server trusts when it upgrades itself. On macOS, compare `shasum -a 256 <file>`, and on Windows `Get-FileHash <file>` in PowerShell, with the file's line in `SHA256SUMS`.

`install.sh` does the same check when `minisign` is installed; without it, it checks the checksums only and says so. Upgrades are always signature-checked by the server itself.
