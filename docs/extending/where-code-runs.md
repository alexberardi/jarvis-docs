# Where your code runs

A package you build with the [Command SDK](../libraries/command-sdk.md) runs on a device that talks to your Jarvis Automation server, not on the server itself. The device decides which parts of the package run.

Jarvis Automation is a **pre-release** (release candidate rc18.9), so this changes from release to release. Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases).

## At a glance

| Device | SDK packages | What runs |
|--------|--------------|-----------|
| Pi with the Python node | Yes | Commands, agents, device managers and device protocols |
| Computer with the desktop agent | Yes | Commands only |
| Pi with the Go voice node | Not supported yet | Commands and device managers, in a Python sidecar (built, not yet checked on a Pi) |
| The server (jarvisd) | No | Nothing: [prompt providers](../legacy/extending/prompt-providers/index.md) are not supported |

## On a Pi

The Python node (`jarvis-node-setup`, see [Node Setup](../clients/node-setup.md)) is the supported Pi node. It loads every part of a package and runs the system setup a package asks for (`apt_packages`, `post_install`).

The Go voice node that `install-pi.sh` installs is still being built. It runs packages in a Python sidecar, and package support is built but not yet checked on a Pi, so it isn't the supported Pi node yet: keep the Python node on a Pi that needs your packages. The two can be installed side by side; only one runs at a time.

## On a computer

A [desktop agent](../agent/index.md) (`jarvis-agent`, installed with the Agent app or `install-agent.sh`) installs a package from the mobile app the way a Pi does, with no restart. It runs the package in its own Python (3.12, managed by `uv`), with the SDK version the agent pins and the `packages` your manifest lists.

- **Commands only.** Agents, device managers, device protocols and the other components are skipped, and the install result lists them in `skipped_components`.
- **The SDK only.** A computer has the SDK but not the Python node's own modules, so import everything from `jarvis_command_sdk`.
- **No system setup.** A computer installs no system packages and runs no setup steps.

## Pi-only packages

A computer is never offered a package it can't run. A package is **Pi-only** when its manifest:

- has `targets` that leave out `desktop`, or
- needs `apt_packages` (the desktop agent also refuses `apt_sources` and `post_install`).

For a Pi-only package the mobile app leaves computers out of the node picker. If an install is asked for anyway, the server refuses it ("… is made for Pi nodes, not computers", or "… needs system packages that only a Pi node installs" for `apt_packages`), and the desktop agent checks the manifest it downloads against the same rules.

A package with **no `targets`** is offered to computers, as long as its `platforms` (if any) include the computer's system. To make the intent explicit, say where it runs in `jarvis_package.yaml`:

```yaml
targets: [node, desktop]
platforms: [linux, darwin, windows]
```

Leave out `desktop` for a Pi-only package. See [`jdt manifest`](toolkit/manifest.md) for the rest of the manifest.

!!! warning "`jdt manifest` drops `targets`"
    `jdt manifest` does not know `targets`, `apt_packages`, `apt_sources` or `post_install`, and removes them when it rewrites `jarvis_package.yaml`. A Pi-only package then has no `targets` and is offered to computers. Write these keys by hand, and put them back after any run of `jdt manifest` ([details](toolkit/manifest.md#updating-an-existing-manifest)).

## Next

- [Building Commands](../commands/index.md): write your first command.
- [Developer Toolkit](toolkit/index.md): scaffold, test and deploy a package.
