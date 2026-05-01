# `jdt manifest` --- Generate a Manifest

Generates or updates `jarvis_package.yaml` by scanning your code and extracting metadata. Instead of writing YAML by hand, let `jdt manifest` introspect your classes and build the manifest for you.

## Usage

```bash
jdt manifest [path] [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Package directory (default: current directory) |

### Options

| Option | Description |
|--------|-------------|
| `--non-interactive` | Use defaults without prompting |
| `--output`, `-o` | Output directory (default: same as package) |

## Examples

```bash
jdt manifest               # Interactive, writes to current directory
jdt manifest . --non-interactive  # Use defaults
jdt manifest /path/to/pkg -o /tmp  # Write manifest to /tmp
```

## What It Does

### 1. Discovers components

Scans the directory tree for files matching convention patterns:

| Pattern | Type |
|---------|------|
| `command.py` at root | command |
| `commands/*/command.py` | command |
| `agents/*/agent.py` | agent |
| `device_families/*/protocol.py` | device_protocol |
| `device_managers/*/manager.py` | device_manager |
| `prompt_providers/*/provider.py` | prompt_provider |
| `routines/*/routine.json` | routine |

### 2. Introspects classes

Dynamically imports each Python component and reads:

- **Secrets** from the `required_secrets` property
- **Pip dependencies** from the `required_packages` property
- **Keywords** from the `keywords` property
- **Description** from the `description` property
- **Authentication config** for OAuth device protocols

For multi-component packages, secrets and pip packages are deduplicated.

### 3. Prompts for metadata (interactive mode)

```
Found 2 component(s):
  [command] my_weather -> commands/my_weather/command.py
  [agent] weather_alerts -> agents/weather_alerts/agent.py

Package name [my_weather]: my_weather
Display name [My Weather]: My Weather
Description [Get weather forecasts]: Weather forecasts with background alerts
Version [0.1.0]: 1.0.0
GitHub username []: alexberardi
Categories: automation, calendar, communication, ...
Categories (comma-separated) [weather]: weather, information
```

### 4. Writes the manifest

```yaml
schema: 1
name: my_weather
display_name: My Weather
description: Weather forecasts with background alerts
version: 1.0.0
author:
  github: alexberardi
categories:
  - weather
  - information
keywords:
  - weather
  - forecast
components:
  - type: command
    name: my_weather
    path: commands/my_weather/command.py
  - type: agent
    name: weather_alerts
    path: agents/weather_alerts/agent.py
secrets:
  - key: WEATHER_API_KEY
    description: OpenWeatherMap API key
    scope: integration
    value_type: string
    is_sensitive: true
    required: true
packages:
  - httpx
```

## Updating an Existing Manifest

If `jarvis_package.yaml` already exists, `jdt manifest` uses its values as defaults. This means you can:

1. Edit your code (add secrets, change descriptions, add components)
2. Run `jdt manifest .` to pick up the changes
3. Accept or modify the prompted values

The existing manifest is overwritten with the updated version.

## Non-Interactive Mode

```bash
jdt manifest . --non-interactive
```

Uses the package directory name as the package name, existing manifest values where available, and introspected values for everything else. Useful for CI or scripting.
