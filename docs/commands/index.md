# Building Commands

> **The Specialists** --- Commands are the staff members who each know how to do one thing expertly. The chef cooks, the accountant balances the books, the gardener tends the grounds. When someone makes a request, the right specialist steps forward.

Commands are the core extension point of Jarvis. Every voice interaction -- "What's the weather?", "Play some jazz", "Turn off the lights" -- is handled by a **command**: a Python class that implements the `IJarvisCommand` interface.

## How It Works

A command runs on the **node**, the device you talk to. The server, `jarvisd`, runs speech-to-text, the model turn and text-to-speech; it never runs your command's code. When a user speaks:

1. The node records the request and `jarvisd` transcribes it.
2. The node tries each command's `pre_route()` on the text. If one claims it, the node runs that command straight away, with no model turn.
3. Otherwise the node sends the text to `jarvisd` with the tool schemas of all its commands. `jarvisd` runs the model, which picks a command and fills in its parameters.
4. `jarvisd` sends the tool call back to the node, which runs the command's `execute()` (validation, then your `run()`) and posts the result to `jarvisd`.
5. `jarvisd` turns the result into the spoken reply, and the node plays it.

[Execution Lifecycle](lifecycle.md) has the full flow.

A command runs on a Pi's Python node or on a computer's desktop agent, not on the server. [Where your code runs](../extending/where-code-runs.md) says which devices run what.

## Getting Started

Commands import everything from `jarvis_command_sdk`. The SDK is not on PyPI; install it from git:

```bash
pip install git+https://github.com/alexberardi/jarvis-command-sdk.git
```

The Python node already bundles it. See [jarvis-command-sdk](../libraries/command-sdk.md).

There are two ways to ship a command:

- **As a Pantry package** (the supported way): scaffold it with [`jdt init`](../extending/toolkit/init.md) and install it on a node with [`jdt deploy`](../extending/toolkit/deploy.md) or from the Pantry.
- **In a source checkout of jarvis-node-setup** (for development): drop a file into `commands/`, run `python scripts/install_command.py <name>` to seed its settings, then restart the node (`sudo systemctl restart jarvis-node`, or restart your dev process). The node discovers commands only when it starts or when a Pantry install or settings push refreshes it, so a new file is not picked up while it runs.

!!! note "`core.*` imports"
    Older samples import `JarvisParameter`, `CommandResponse` and friends from `core.*`, and read secrets with `services.secret_service`. Those modules exist only inside the Python node (`core.*` re-exports the SDK there for old commands), so such a command fails on a desktop agent. Use `jarvis_command_sdk` for everything.

## Minimal Skeleton

Every command follows this pattern:

```python
from typing import List

from jarvis_command_sdk import (
    CommandExample,
    CommandResponse,
    IJarvisCommand,
    IJarvisSecret,
    JarvisParameter,
    RequestInformation,
)


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

All eight members are required: leave one out and the class can't be instantiated, and the node skips it without loading it.

## Built-in Commands

These commands ship with the Python node (`jarvis-node-setup/commands/`):

| Command | Name | Description |
|---------|------|-------------|
| `ActOnItemsCommand` | `act_on_items` | Acts on items from a list the user was just shown ("mark those as read") |
| `AnswerQuestionCommand` | `answer_question` | General-knowledge questions |
| `CalculatorCommand` | `calculate` | Arithmetic on two numbers |
| `CancelTimerCommand` | `cancel_timer` | Cancel a running timer |
| `ChatCommand` | `chat` | Small talk and greetings |
| `CheckTimersCommand` | `check_timers` | Time left on running timers |
| `ControlDeviceCommand` | `control_device` | Smart-home device control (lights, TV, locks, thermostat) |
| `ControlNodeCommand` | `control_node` | The speaker's own volume and mute |
| `ExportShoppingListCommand` | `export_shopping_list` | Send the shopping list to a store as a cart link |
| `ExportTodoListCommand` | `export_todo_list` | Send the to-do list to the user's phone |
| `MeasurementConversionCommand` | `convert_measurement` | Unit conversions |
| `ReminderCommand` | `reminder` | Reminders and alarms at a clock time or date; list, delete, snooze |
| `RoutineCommand` | `routine` | Run a named routine (good morning, good night) |
| `SendLinkCommand` | `send_link` | Send a link from an earlier result to the user's phone |
| `ShoppingListCommand` | `shopping_list` | Add to, read, check off or clear the shopping list |
| `TellAJokeCommand` | `tell_joke` | Tell a joke |
| `TimerCommand` | `set_timer` | Countdown timers |
| `TimezoneCommand` | `get_current_time` | Time and date somewhere else |
| `TodoListCommand` | `todo_list` | Add to, read, complete or clear the to-do list |
| `WhatsUpCommand` | `check_alerts` | Read out or dismiss pending alerts (news, calendar) |

The experimental Go Pi node runs the same commands except `control_device`, `routine` and `send_link`; the desktop agent has its own tools. See [Where your code runs](../extending/where-code-runs.md).

## Pantry-Installable Commands

The following commands are available as standalone [Pantry](../pantry/index.md) packages. Install them from the mobile app: open the Pantry, pick a package and the node to install it on. Pantry is off by default; a household admin turns it on in the household settings first (installs are refused until then). On a node source checkout, `python scripts/command_store.py install <name>` does the same from a shell.

| Command | Name | Description |
|---------|------|-------------|
| `OpenWeatherCommand` | `get_weather` | Current weather and forecasts via OpenWeather API (requires API key) |
| `OpenMeteoWeatherCommand` | `get_weather_meteo` | Current weather and forecasts via Open-Meteo — **free, no API key required** |
| `NewsCommand` | `get_news` | News headlines via RSS feeds |
| `SportsCommand` | `get_sports` | Live sports scores via ESPN (NFL, NBA, MLB, NHL, College) |
| `WebSearchCommand` | `search_web` | Live web search for current information |
| `MusicCommand` | `music` | Play content and control playback via Music Assistant |
| `PandoraCommand` | `pandora` | Stream Pandora Radio with voice control — skip, thumbs up/down, station listing |
| `SpotifyCommand` | `spotify` | Stream Spotify with voice control via spotifyd — tracks, artists, albums, playlists |
| `AudacyCommand` | `audacy` | Live radio from the Audacy network |
| `EmailCommand` | `email` | List, read, search, send, reply, archive email (Gmail/IMAP) |
| `ReadCalendarCommand`, `AddEventCommand` | `get_calendar_events`, `add_event` | Read and add calendar events (iCloud CalDAV, Google Calendar) |
| `CheckTextsCommand`, `ReadThreadCommand`, `DraftReplyCommand` | `check_texts`, `read_thread`, `draft_reply` | Check, read and reply to text messages (through a Mac running jarvis-osx-api) |
| `MedicationCommand` | `medication` | Personal + household medication tracking with dose reminders. Mark doses by voice; add and manage records in the app. Personal med alerts are push-only (not spoken aloud on shared nodes) |
| `RottenTomatoesCommand` | `rotten_tomatoes` | Movie and TV ratings, what's in theaters — Tomatometer scores, no API key |
| `EntertainmentKnowledgeCommand` | `entertainment_knowledge` | Look up a movie or TV show and send a rich card to the inbox |
| `GetBarstoolCommand` | `get_barstool` | Barstool Sports headlines |
| `GetDriveTimeCommand` | `get_drive_time` | Driving time and distance with live traffic |
| `DadJokeCommand` | `tell_dad_joke` | Random dad jokes via icanhazdadjoke.com — no configuration required |
| `GreetingCommand` | `greeting` | Say hello in 10 languages |

The live catalog may list more; browse it in the app.

Device families (LIFX, Kasa, Govee, Apple, Nest, Hue, and more) are also available as Pantry packages, installed the same way. See [Device Packages](../extending/devices/index.md#available-device-packages).

!!! note
    `BluetoothCommand` (jarvis-cmd-bluetooth) has been archived and is no longer maintained. Use a music command (`PandoraCommand`, `SpotifyCommand`, or `MusicCommand`) for audio playback.

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

-   **[Testing Commands](testing.md)**

    E2E tests, multi-turn tests, and unit testing patterns.

</div>
