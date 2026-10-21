# Server on Linux

Install the Jarvis Automation server on a Linux machine that stays on: it is the server for your whole household. On Debian and Ubuntu there is a package; on other distributions, use the install script.

Jarvis Automation is a **pre-release** (release candidate rc18). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Before you start

- A 64-bit machine: Intel or AMD (`amd64`) or ARM (`arm64`).
- systemd, which runs the server as a service.
- A GPU helps a lot (NVIDIA through CUDA, AMD through ROCm or Vulkan); without one the server runs a small model on the CPU. See [Requirements and choosing a model](requirements.md).

## Debian and Ubuntu

1. From the newest release, download the package for your processor, where `<version>` is the release's version, such as `0.1.0-rc18`:
    - `jarvis-automation-server_<version>_amd64.deb` for Intel and AMD,
    - `jarvis-automation-server_<version>_arm64.deb` for ARM.
2. Open it: App Center (or Software) installs it after your password.

On a machine without a screen, install it from a terminal instead:

```sh
sudo apt install ./jarvis-automation-server_<version>_amd64.deb
```

The package installs the server as a system service, run by its own `jarvisd` account, and opens the firewall for your local network when ufw or firewalld is active. Then it opens the [setup wizard](setup-wizard.md) in your browser. Without a screen (or over SSH) it prints the link and a QR code instead: scan the code with your phone to open the wizard there.

If the browser didn't open, **Jarvis Automation Server** in the app menu opens the setup page later (it asks for your password, because the link holds the setup token).

Your data is in `/var/lib/jarvisd` and settings in `/etc/jarvisd`; see [Where the data lives](../operate/data-and-backups.md#where-the-data-lives).

## Other distributions

On Fedora, Arch, Bazzite and other distributions, `install.sh` installs the same server. It takes `--user` to run it as a service of your own account, without root, with the data in `~/.jarvisd`. See [Advanced one-liners](one-liners.md).

## Next

Finish in the [setup wizard](setup-wizard.md) at `http://<host>:7710/setup`. If it didn't open, see [The setup wizard doesn't open](../troubleshooting/index.md#the-setup-wizard-doesnt-open).

To remove it later, see [Uninstall](uninstall.md).
