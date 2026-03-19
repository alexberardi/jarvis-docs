# Building Commands

> **The Specialists** --- Commands are the staff members who each know how to do one thing expertly. The chef cooks, the accountant balances the books, the gardener tends the grounds. When someone makes a request, the right specialist steps forward.

Commands are the core extension point of Jarvis. Every voice interaction -- "What's the weather?", "Play some jazz", "Turn off the lights" -- is handled by a **command**: a Python class that implements the `IJarvisCommand` interface.

## How It Works

When a user speaks a voice command, the pipeline looks like this:

1. **Speech-to-text** converts audio to text
2. The **command center** sends the text to the LLM with all registered command schemas
3. The LLM selects a command and extracts parameters
4. The **node** executes the command's `run()` method
5. The response flows back through the command center to the user

Commands live as Python files in `jarvis-node-setup/commands/`. Drop in a new file, implement the interface, and run `install_command.py` -- that's it.

## Minimal Skeleton

Every command follows this pattern:

```python
from typing import List

from core.ijarvis_command import IJarvisCommand, CommandExample
from core.ijarvis_parameter import JarvisParameter
from core.ijarvis_secret import IJarvisSecret
from core.command_response import CommandResponse
from core.request_information import RequestInformation


class MyCommand(IJarvisCommand):

    @property
    def command_name(self) -> str:
        return "my_command"

    @property
    def description(self) -> str:
        return "Short description of what this command does"

    @property
    def keywords(self) -> List[str]:
        return ["keyword1", "keyword2"]

    @property
    def parameters(self) -> List[JarvisParameter]:
        return []

    @property
    def required_secrets(self) -> List[IJarvisSecret]:
        return []

    def generate_prompt_examples(self) -> List[CommandExample]:
        return [
            CommandExample(
                voice_command="Example voice input",
                expected_parameters={},
                is_primary=True,
            ),
        ]

    def generate_adapter_examples(self) -> List[CommandExample]:
        return self.generate_prompt_examples()

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        return CommandResponse.final_response(
            context_data={"message": "Hello from my command!"}
        )
```

## Built-in Commands

Jarvis ships with these commands out of the box:

| Command | Name | Description |
|---------|------|-------------|
| `CalculatorCommand` | `calculate` | Two-number arithmetic (add, subtract, multiply, divide) |
| `OpenWeatherCommand` | `get_weather` | Current weather and forecasts via OpenWeather API |
| `MusicCommand` | `music` | Play content and control playback via Music Assistant |
| `EmailCommand` | `email` | List, read, search, send, reply, archive email (Gmail/IMAP) |
| `ControlDeviceCommand` | `control_device` | Smart home device control (Home Assistant + direct WiFi) |
| `GetDeviceStatusCommand` | `get_device_status` | Query smart home device state |
| `ChatCommand` | `chat` | Open-ended conversation with the LLM |
| `AnswerQuestionCommand` | `answer_question` | Factual Q&A |
| `TimerCommand` | `set_timer` | Set countdown timers |
| `CheckTimersCommand` | `check_timers` | List active timers |
| `CancelTimerCommand` | `cancel_timer` | Cancel a running timer |
| `SportsCommand` | `get_sports_scores` | Live sports scores via ESPN |
| `NewsCommand` | `get_news` | News headlines |
| `WebSearchCommand` | `search_web` | Web search with deep research |
| `TellAJokeCommand` | `tell_a_joke` | Random jokes |
| `StoryCommand` | `tell_a_story` | Generate stories |
| `MeasurementConversionCommand` | `convert_measurement` | Unit conversions |
| `TimezoneCommand` | `get_current_time` | Current time in any timezone |
| `ReadCalendarCommand` | `read_calendar` | Calendar events (iCloud) |
| `RoutineCommand` | `routine` | Multi-step automations |
| `WhatsUpCommand` | `whats_up` | Morning briefing (weather + calendar + news) |

## Guides

<div class="grid cards" markdown>

-   **[Simple Command Tutorial](tutorial-simple.md)**

    Build a dice-rolling command from scratch. Best starting point.

-   **[API Integration Tutorial](tutorial-api.md)**

    Build a command that calls an external API with secrets management.

-   **[OAuth Command Tutorial](tutorial-oauth.md)**

    Build a command requiring OAuth authentication (external and local discovery).

</div>

## Reference

<div class="grid cards" markdown>

-   **[Interface Reference](interface-reference.md)**

    Complete reference for `IJarvisCommand` and all related classes.

-   **[Parameters Deep Dive](parameters.md)**

    All parameter types, enums, validation, and the `refinable` flag.

-   **[Secrets Deep Dive](secrets.md)**

    Secret scopes, sensitivity, installation flow, and runtime access.

-   **[Response Patterns](responses.md)**

    Success, error, follow-up, chunked responses, and interactive buttons.

-   **[Execution Lifecycle](lifecycle.md)**

    Full flow from voice input to command execution, with Mermaid diagrams.

-   **[Examples & Training](examples.md)**

    Prompt examples, adapter examples, and the training workflow.

-   **[Testing Commands](testing.md)**

    E2E tests, multi-turn tests, and unit testing patterns.

</div>
