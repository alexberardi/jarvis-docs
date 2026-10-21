# `jdt deploy` --- Install to a Node

Deploys a package to a Jarvis node. Supports three targets: local filesystem, Docker container (legacy install only), or remote Pi Zero over SSH.

!!! warning "Restart the node after deploying"
    `jdt deploy` installs the files but does not load them into the running node. Restart the node service afterwards (`sudo systemctl restart jarvis-node` on a Pi) so it discovers the new components and sends their tool schemas to jarvisd. jdt's own "Discovery caches will auto-refresh" message is out of date; see [below](#after-the-install-restart-the-node).

## Usage

```bash
jdt deploy <target> [options]
```

### Targets

#### `jdt deploy local`

Installs to a local `jarvis-node-setup` installation.

```bash
jdt deploy local [path] [--node-dir <dir>]
```

| Argument/Option | Description |
|----------------|-------------|
| `path` | Package directory (default: current directory) |
| `--node-dir` | Path to jarvis-node-setup (auto-detected) |

**Node directory resolution order:**

1. `--node-dir` flag
2. `JARVIS_NODE_DIR` environment variable
3. Sibling repo: `../jarvis-node-setup`
4. Production install: `/opt/jarvis-node`

```bash
jdt deploy local .                         # Auto-detect node location
jdt deploy local . --node-dir ~/jarvis/jarvis-node-setup  # Explicit path
```

#### `jdt deploy docker`

Installs into a Docker node container.

!!! note "Legacy Docker install only"
    This target is for nodes of the [legacy Docker install](../../legacy/index.md). Jarvis Automation (jarvisd) runs no node containers: use `local` or `ssh` for a Pi's Python node, and the mobile app for a computer's desktop agent ([Where your code runs](../where-code-runs.md)).

```bash
jdt deploy docker <container> [path]
```

| Argument | Description |
|----------|-------------|
| `container` | Container name (partial match OK) |
| `path` | Package directory (default: current directory) |

```bash
jdt deploy docker jarvis-node-kitchen .
jdt deploy docker jarvis-node .          # Partial name match
```

**What it does:**

1. `docker cp` the package to `/tmp/jarvis-pkg-install` in the container
2. `docker exec` the container's `command_store.py install` command
3. Cleans up the temp directory

#### `jdt deploy ssh`

Installs on a remote Pi Zero (or any Linux host) over SSH.

```bash
jdt deploy ssh <host> [path] [--node-dir <dir>]
```

| Argument/Option | Description |
|----------------|-------------|
| `host` | SSH target (e.g., `pi@<dev-node>.local`) |
| `path` | Package directory (default: current directory) |
| `--node-dir` | Remote node directory (default: `/opt/jarvis-node`) |

```bash
jdt deploy ssh pi@<dev-node>.local .
jdt deploy ssh pi@<kitchen-node>.local . --node-dir /opt/jarvis-node
```

**What it does:**

1. `scp` the package to the remote host
2. `ssh` in, `cd` to the node directory and run `command_store.py install` as the SSH user (no `sudo`: the install writes to that user's `~/.jarvis/`; apt and post-install steps escalate through the node's own sudoers grants)
3. Cleans up the temp files

## Examples

### Development loop

```bash
# Edit, test, deploy, restart, repeat
jdt test . && jdt deploy local . && sudo systemctl restart jarvis-node
```

### Deploy to all nodes

```bash
jdt deploy local .
jdt deploy docker jarvis-node-kitchen .  # legacy Docker install only
jdt deploy ssh pi@<dev-node>.local .
```

### CI/CD deploy

```bash
jdt test . && jdt deploy ssh pi@<kitchen-node>.local . --node-dir /opt/jarvis-node \
  && ssh pi@<kitchen-node>.local sudo systemctl restart jarvis-node
```

## What Happens During Install

All three targets ultimately run the node's `command_store.py install` command, which:

1. Reads `jarvis_package.yaml` from the package
2. Copies each component to its `custom_*` directory: `commands/custom_commands/<name>`, `agents/custom_agents/<name>`, `device_families/custom_families/<name>`, `device_managers/custom_managers/<name>` or `routines/custom_routines/<name>` (see [Where installed packages land](../discovery.md#where-installed-packages-land))
3. Installs pip dependencies declared in the manifest
4. Seeds secret placeholders (user fills values via the mobile app)
5. On a Pi, runs the manifest's system steps (`apt_packages`, `apt_sources`, `post_install`)

### After the install: restart the node

The install runs as a separate process, and it does not refresh the running node: the node has no background refresh and nothing watches its directories. The new components load when the node restarts:

```bash
sudo systemctl restart jarvis-node
```

For a node you run from a checkout, stop and start it. jdt prints "Installed successfully. Discovery caches will auto-refresh." after a deploy; that message predates the current node and is wrong, so restart anyway. (An install from the mobile app restarts the node by itself.)
