# Development Workflow

This guide walks through the complete lifecycle of building a Jarvis package, from initial idea to running on a node. We will build a simple weather command as a concrete example.

## Prerequisites

- Python 3.10+
- `jdt` installed (`pip install git+https://github.com/alexberardi/jarvis-developer-toolkit.git`)
- A running Jarvis node (local, Docker, or SSH-accessible)

## Step 1: Scaffold

```bash
jdt init my_weather --type command --author alexberardi --category weather
cd my_weather
```

You now have a working package:

```
my_weather/
├── commands/my_weather/
│   ├── __init__.py
│   └── command.py          # <- Your code goes here
├── jarvis_package.yaml
├── CLAUDE.md
├── README.md
├── LICENSE
└── .gitignore
```

Verify it passes immediately:

```bash
jdt test .
# PASS - 5/5 checks passed
```

## Step 2: Implement

Open `commands/my_weather/command.py`. The scaffold gives you a working stub --- now replace the logic with real functionality.

```python
"""Voice command: My Weather."""

from jarvis_command_sdk import (
    IJarvisCommand, CommandResponse, CommandExample,
    JarvisParameter, JarvisSecret, RequestInformation,
    JarvisStorage,
)

try:
    from jarvis_log_client import JarvisLogger
except ImportError:
    import logging

    class JarvisLogger:
        def __init__(self, **kw):
            self._log = logging.getLogger(kw.get("service", __name__))

        def info(self, msg, **kw):
            self._log.info(msg)

        def error(self, msg, **kw):
            self._log.error(msg)


logger = JarvisLogger(service="cmd.my_weather")


class MyWeatherCommand(IJarvisCommand):
    @property
    def command_name(self) -> str:
        return "my_weather"

    @property
    def description(self) -> str:
        return "Get the current weather for a city"

    @property
    def parameters(self) -> list[JarvisParameter]:
        return [
            JarvisParameter(
                name="city",
                param_type="string",
                required=True,
                description="City name",
            ),
            JarvisParameter(
                name="units",
                param_type="string",
                required=False,
                description="Temperature units",
                enum_values=["imperial", "metric"],
                default="imperial",
            ),
        ]

    @property
    def required_secrets(self) -> list[JarvisSecret]:
        return [
            JarvisSecret(
                key="WEATHER_API_KEY",
                description="OpenWeatherMap API key",
                scope="integration",
                value_type="string",
                is_sensitive=True,
                required=True,
                friendly_name="Weather API Key",
            ),
        ]

    @property
    def keywords(self) -> list[str]:
        return ["weather", "forecast", "temperature", "outside"]

    def generate_prompt_examples(self) -> list[CommandExample]:
        return [
            CommandExample(
                voice_command="What's the weather in Chicago?",
                expected_parameters={"city": "Chicago"},
                is_primary=True,
            ),
            CommandExample(
                voice_command="Weather in Tokyo in metric",
                expected_parameters={"city": "Tokyo", "units": "metric"},
            ),
        ]

    def generate_adapter_examples(self) -> list[CommandExample]:
        cities = ["New York", "London", "Paris", "Tokyo", "Sydney",
                  "Berlin", "Cairo", "Mumbai", "Toronto", "Seoul"]
        return [
            CommandExample(
                voice_command=f"What's the weather in {city}?",
                expected_parameters={"city": city},
            )
            for city in cities
        ]

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        city = kwargs.get("city", "")
        units = kwargs.get("units", "imperial")

        if not city:
            return CommandResponse.error_response(
                error_details="I need a city name to check the weather."
            )

        # Access secrets via JarvisStorage
        storage = JarvisStorage("my_weather")
        api_key = storage.get_secret("WEATHER_API_KEY", scope="integration")

        if not api_key:
            return CommandResponse.error_response(
                error_details="Weather API key is not configured."
            )

        # TODO: Call the weather API using httpx
        # For now, return a placeholder
        return CommandResponse.success_response(
            context_data={"message": f"The weather in {city} is sunny and 72 degrees."},
            wait_for_input=False,
        )
```

### Key patterns to follow

- **Logging**: Always use the `try: from jarvis_log_client` pattern. The fallback ensures your command works even if the log client isn't installed.
- **Errors**: Never raise exceptions from `run()`. Return `CommandResponse.error_response()` instead.
- **Secrets**: Use `JarvisStorage` to access secrets, not environment variables.
- **TTS output**: The value at `context_data["message"]` is what gets spoken aloud.
- **Shared code**: If you need helper modules, name the directory `my_weather_shared/` (not `shared/`, `lib/`, or `helpers/` --- those collide on `sys.path` after install).

## Step 3: Update the Manifest

After changing secrets, dependencies, or descriptions, regenerate the manifest:

```bash
jdt manifest . --non-interactive
```

Or interactively:

```bash
jdt manifest .
```

This reads your class properties and updates `jarvis_package.yaml` with the current secrets, pip packages, keywords, and description.

If your command uses `httpx` for HTTP calls, add it to the manifest's `packages` list (or it will be picked up automatically if you declare it in `required_packages`):

```yaml
packages:
  - httpx
```

## Step 4: Validate

Run the full test suite:

```bash
jdt test .
```

If your command has pip dependencies that aren't installed locally:

```bash
jdt test . --install-deps
```

Fix any failures before deploying. Common issues:

| Error | Fix |
|-------|-----|
| `Dangerous import: subprocess` | Use `httpx` for HTTP calls, not subprocess |
| `Class does not inherit from IJarvisCommand` | Check your import and class definition |
| `version 'X.Y' is not valid semver` | Use three-part version: `1.0.0` |
| `component path does not exist` | Check paths in `jarvis_package.yaml` match actual files |

## Step 5: Deploy

Install to your local node:

```bash
jdt deploy local .
```

Or to a Docker node:

```bash
jdt deploy docker jarvis-node-kitchen .
```

Or to a Pi Zero:

```bash
jdt deploy ssh pi@jarvis-dev.local .
```

The node's discovery system picks up the new command automatically. No restart needed.

## Step 6: Test It

Issue a voice command (or use the web/mobile chat):

> "What's the weather in Chicago?"

The command center should route the request to your `my_weather` command, which runs `run()` and returns the response.

## Step 7: Iterate

The development loop:

```bash
# Edit code
vim commands/my_weather/command.py

# Validate
jdt test .

# Deploy
jdt deploy local .

# Test via voice or chat
# ... repeat ...
```

For rapid iteration, chain test and deploy:

```bash
jdt test . && jdt deploy local .
```

## Step 8: Publish (Optional)

To share your package via the Jarvis Pantry:

1. Create a GitHub repository for your package
2. Push your code
3. Submit to Pantry via the web UI or Forge

The Pantry runs the same `jdt test` pipeline on submission. If it passes locally, it will pass review.

## Multi-Component Packages

The workflow is the same for bundles. For example, a smart lights package with a command, protocol, and agent:

```bash
jdt init smart_lights --type command,protocol,agent
cd smart_lights

# Implement each component
# commands/smart_lights/command.py   -- voice control
# device_families/smart_lights/protocol.py -- hardware communication
# agents/smart_lights/agent.py       -- background state polling

# Manifest picks up all components
jdt manifest . --non-interactive

# Test and deploy as usual
jdt test . && jdt deploy local .
```

## Project Structure Best Practices

| Do | Don't |
|----|-------|
| Keep components focused and small | Cram unrelated features into one package |
| Use `JarvisStorage` for data persistence | Use raw SQLite or file I/O |
| Return `CommandResponse.error_response()` | Raise exceptions from `run()` |
| Name shared dirs `{pkg}_shared/` | Use generic names like `shared/` or `lib/` |
| Declare all secrets in `required_secrets` | Hardcode API keys |
| Provide 10+ adapter training examples | Provide fewer than 5 examples |
