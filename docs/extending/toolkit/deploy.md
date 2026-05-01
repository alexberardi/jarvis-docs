# `jdt deploy` --- Install to a Node

Deploys a package to a Jarvis node. Supports three targets: local filesystem, Docker container, or remote Pi Zero over SSH.

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
| `host` | SSH target (e.g., `pi@jarvis-dev.local`) |
| `path` | Package directory (default: current directory) |
| `--node-dir` | Remote node directory (default: `/opt/jarvis-node`) |

```bash
jdt deploy ssh pi@jarvis-dev.local .
jdt deploy ssh pi@jarvis-kitchen.local . --node-dir /opt/jarvis-node
```

**What it does:**

1. `scp` the package to the remote host
2. `ssh` in and runs `command_store.py install` with `sudo`
3. Cleans up the temp files

## Examples

### Development loop

```bash
# Edit, test, deploy, repeat
jdt test . && jdt deploy local .
```

### Deploy to all nodes

```bash
jdt deploy local .
jdt deploy docker jarvis-node-kitchen .
jdt deploy ssh pi@jarvis-dev.local .
```

### CI/CD deploy

```bash
jdt test . && jdt deploy ssh pi@jarvis-kitchen.local . --node-dir /opt/jarvis-node
```

## What Happens During Install

All three targets ultimately run the node's `command_store.py install` command, which:

1. Reads `jarvis_package.yaml` from the package
2. Copies components to their convention directories (`commands/`, `agents/`, etc.)
3. Installs pip dependencies declared in the manifest
4. Seeds secret placeholders (user fills values via the mobile app)
5. The node's discovery services pick up the new components automatically

No restart is required --- the discovery system's background refresh detects new files.
