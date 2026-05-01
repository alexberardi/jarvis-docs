# `jdt init` --- Scaffold a Package

Creates a complete package directory with working stubs, a valid manifest, and supporting files. Everything passes `jdt test` immediately.

## Usage

```bash
jdt init <name> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `name` | Yes (or interactive) | Package name in `snake_case` |

### Options

| Option | Description |
|--------|-------------|
| `--type`, `-t` | Component types, comma-separated (default: `command`) |
| `--author` | GitHub username (default: interactive prompt) |
| `--category` | Package category (default: interactive prompt) |
| `--output`, `-o` | Output directory (default: current directory) |
| `--non-interactive` | Skip all prompts, use defaults |

## Examples

### Single command

```bash
jdt init my_weather --type command --author alexberardi --category weather
```

Creates:

```
my_weather/
├── commands/
│   └── my_weather/
│       ├── __init__.py
│       └── command.py
├── jarvis_package.yaml
├── CLAUDE.md
├── README.md
├── LICENSE
└── .gitignore
```

### Multi-component bundle

```bash
jdt init smart_lights --type command,protocol,manager
```

Creates stubs for all three component types in the convention directories:

```
smart_lights/
├── commands/
│   └── smart_lights/
│       ├── __init__.py
│       └── command.py
├── device_families/
│   └── smart_lights/
│       ├── __init__.py
│       └── protocol.py
├── device_managers/
│   └── smart_lights/
│       ├── __init__.py
│       └── manager.py
├── jarvis_package.yaml
├── CLAUDE.md
├── README.md
├── LICENSE
└── .gitignore
```

### Interactive mode

```bash
jdt init
```

Prompts for everything:

```
Package name (snake_case): my_weather

Component types:
  command          - Voice command (IJarvisCommand)
  agent            - Background agent (IJarvisAgent)
  protocol         - Device protocol (IJarvisDeviceProtocol)
  manager          - Device manager (IJarvisDeviceManager)
  routine          - Multi-step routine (JSON)
  prompt_provider  - LLM prompt provider (IJarvisPromptProvider)

Types (comma-separated) [command]: command
GitHub username []: alexberardi
Categories: automation, calendar, communication, ...
Category [utilities]: weather
```

### Non-interactive (CI/scripting)

```bash
jdt init my_pkg --non-interactive
```

Uses defaults: type `command`, author `community`, category `utilities`.

## Convention Layout

`jdt init` places files in the directories the discovery system expects:

| Component Type | Convention Directory |
|---------------|---------------------|
| command | `commands/{name}/command.py` |
| agent | `agents/{name}/agent.py` |
| device_protocol | `device_families/{name}/protocol.py` |
| device_manager | `device_managers/{name}/manager.py` |
| prompt_provider | `prompt_providers/{name}/provider.py` |
| routine | `routines/{name}/routine.json` |

This matches what `CommandDiscoveryService`, `AgentDiscoveryService`, and the other discovery services scan for at startup.

## Generated CLAUDE.md

Each scaffolded package includes a `CLAUDE.md` tailored to the package's component types. It contains:

- `jdt` commands for the development loop
- SDK quick reference (`CommandResponse`, `JarvisStorage`, `JarvisParameter`, `JarvisSecret`)
- Key rules (logging pattern, error handling, shared code naming, TTS output)
- Manifest management instructions

This file gives Claude Code (or any AI assistant) the context it needs to help you develop the package. See the [Claude Code Integration](claude-code.md) guide for more.

## Valid Categories

`automation`, `calendar`, `communication`, `entertainment`, `finance`, `fitness`, `food`, `games`, `health`, `home`, `information`, `media`, `music`, `news`, `productivity`, `shopping`, `smart-home`, `sports`, `travel`, `utilities`, `weather`
