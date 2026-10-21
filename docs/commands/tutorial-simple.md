# Tutorial: Build a Dice Roll Command

This tutorial walks you through building a complete command from scratch. By the end, you will have a working `roll_dice` command that responds to voice input like "Roll two dice" or "Roll a d20".

**Prerequisites:**

- A running `jarvisd` with a live model (see [Install](../install/index.md)).
- A source checkout of [jarvis-node-setup](https://github.com/alexberardi/jarvis-node-setup) set up as a node and paired with that server (see [Node](../clients/node-setup.md)). The checkout bundles the SDK. To write a command outside it, install the SDK from git: `pip install git+https://github.com/alexberardi/jarvis-command-sdk.git` (it is not on PyPI).

This tutorial adds the command to the checkout, which is the quickest loop while you develop. To ship a command to other nodes, package it instead: [`jdt init`](../extending/toolkit/init.md) scaffolds a Pantry package with the same class in `command.py`.

## Step 1: Create the File

In your jarvis-node-setup checkout, create `commands/dice_command.py`:

```python
import random
from typing import List

from jarvis_command_sdk import (
    CommandExample,
    CommandResponse,
    IJarvisCommand,
    IJarvisSecret,
    JarvisParameter,
    RequestInformation,
)
```

Every command imports from `jarvis_command_sdk`, so it runs on any node that has the SDK.

## Step 2: Define the Class and Required Properties

```python
class DiceCommand(IJarvisCommand):

    @property
    def command_name(self) -> str:
        return "roll_dice"

    @property
    def description(self) -> str:
        return "Roll one or more dice with a configurable number of sides. Default is one six-sided die."

    @property
    def keywords(self) -> List[str]:
        return ["roll", "dice", "die", "d20", "random", "d6"]
```

The `command_name` is the unique identifier. The `description` tells the LLM when to use this command. The `keywords` help with fuzzy matching during command discovery.

## Step 3: Define Parameters

Our dice command takes two optional parameters:

```python
    @property
    def parameters(self) -> List[JarvisParameter]:
        return [
            JarvisParameter(
                "sides",
                "int",
                required=False,
                description="Number of sides on each die (default 6)",
                default="6",
            ),
            JarvisParameter(
                "count",
                "int",
                required=False,
                description="Number of dice to roll (default 1)",
                default="1",
            ),
        ]
```

Both parameters are optional with sensible defaults. The LLM sees these as the tool's parameter schema and extracts values from the voice command.

## Step 4: Declare Secrets

This command does not need any API keys or configuration:

```python
    @property
    def required_secrets(self) -> List[IJarvisSecret]:
        return []
```

If your command needed an API key, you would return `JarvisSecret` objects here. See the [API Integration Tutorial](tutorial-api.md) for that pattern.

## Step 5: Write Prompt Examples

Prompt examples teach the LLM how to parse voice commands into parameters. Keep this list concise -- these go into every system prompt.

```python
    def generate_prompt_examples(self) -> List[CommandExample]:
        return [
            CommandExample(
                voice_command="Roll a die",
                expected_parameters={},
                is_primary=True,
            ),
            CommandExample(
                voice_command="Roll two dice",
                expected_parameters={"count": 2},
            ),
            CommandExample(
                voice_command="Roll a d20",
                expected_parameters={"sides": 20},
            ),
            CommandExample(
                voice_command="Roll 3 twelve-sided dice",
                expected_parameters={"sides": 12, "count": 3},
            ),
        ]
```

The `is_primary=True` example is used for one-shot inference. Only one example can be primary.

Notice that the first example has empty `expected_parameters` -- when the user says just "Roll a die", no parameters need to be extracted because the defaults handle it.

## Step 6: Write Adapter Examples

Adapter examples are used for LoRA fine-tuning. They should be more varied and cover edge cases:

```python
    def generate_adapter_examples(self) -> List[CommandExample]:
        return [
            CommandExample("Roll a die", {}, is_primary=True),
            CommandExample("Roll a dice", {}),
            CommandExample("Roll the dice", {}),
            CommandExample("Throw a die", {}),
            CommandExample("Roll two dice", {"count": 2}),
            CommandExample("Roll 5 dice", {"count": 5}),
            CommandExample("Roll a d20", {"sides": 20}),
            CommandExample("Roll a twenty-sided die", {"sides": 20}),
            CommandExample("Roll a d12", {"sides": 12}),
            CommandExample("Roll 4 d6", {"sides": 6, "count": 4}),
            CommandExample("Roll 3 twelve-sided dice", {"sides": 12, "count": 3}),
            CommandExample("Roll 2 twenty-sided dice", {"sides": 20, "count": 2}),
            CommandExample("Roll 2d8", {"sides": 8, "count": 2}),
            CommandExample("Give me a random number", {"sides": 6}),
        ]
```

More examples = better adapter training. Cover casual phrasings, shorthand notations, and spoken-out numbers.

## Step 7: Implement `run()`

This is where the actual logic lives:

```python
    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        sides = int(kwargs.get("sides", 6))
        count = int(kwargs.get("count", 1))

        # Validate inputs
        if sides < 2:
            return CommandResponse.error_response(
                error_details="A die must have at least 2 sides",
            )
        if count < 1 or count > 100:
            return CommandResponse.error_response(
                error_details="You can roll between 1 and 100 dice",
            )

        # Roll the dice
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)

        return CommandResponse.final_response(
            context_data={
                "rolls": rolls,
                "total": total,
                "sides": sides,
                "count": count,
                "message": f"Rolled {count}d{sides}: {rolls} (total: {total})",
            }
        )
```

Key points:

- Extract parameters from `**kwargs` with defaults
- Validate inputs and return `error_response` for bad values
- Return `final_response` because dice rolls don't need follow-up conversation
- The `context_data["message"]` is what the LLM uses to generate the spoken response (on the fast path, with no LLM, it is spoken as written)

## Complete File

Here is the full `dice_command.py`:

```python
import random
from typing import List

from jarvis_command_sdk import (
    CommandExample,
    CommandResponse,
    IJarvisCommand,
    IJarvisSecret,
    JarvisParameter,
    RequestInformation,
)


class DiceCommand(IJarvisCommand):

    @property
    def command_name(self) -> str:
        return "roll_dice"

    @property
    def description(self) -> str:
        return "Roll one or more dice with a configurable number of sides. Default is one six-sided die."

    @property
    def keywords(self) -> List[str]:
        return ["roll", "dice", "die", "d20", "random", "d6"]

    @property
    def parameters(self) -> List[JarvisParameter]:
        return [
            JarvisParameter(
                "sides", "int", required=False,
                description="Number of sides on each die (default 6)",
                default="6",
            ),
            JarvisParameter(
                "count", "int", required=False,
                description="Number of dice to roll (default 1)",
                default="1",
            ),
        ]

    @property
    def required_secrets(self) -> List[IJarvisSecret]:
        return []

    def generate_prompt_examples(self) -> List[CommandExample]:
        return [
            CommandExample("Roll a die", {}, is_primary=True),
            CommandExample("Roll two dice", {"count": 2}),
            CommandExample("Roll a d20", {"sides": 20}),
            CommandExample("Roll 3 twelve-sided dice", {"sides": 12, "count": 3}),
        ]

    def generate_adapter_examples(self) -> List[CommandExample]:
        return [
            CommandExample("Roll a die", {}, is_primary=True),
            CommandExample("Roll a dice", {}),
            CommandExample("Roll the dice", {}),
            CommandExample("Throw a die", {}),
            CommandExample("Roll two dice", {"count": 2}),
            CommandExample("Roll 5 dice", {"count": 5}),
            CommandExample("Roll a d20", {"sides": 20}),
            CommandExample("Roll a twenty-sided die", {"sides": 20}),
            CommandExample("Roll a d12", {"sides": 12}),
            CommandExample("Roll 4 d6", {"sides": 6, "count": 4}),
            CommandExample("Roll 3 twelve-sided dice", {"sides": 12, "count": 3}),
            CommandExample("Roll 2 twenty-sided dice", {"sides": 20, "count": 2}),
            CommandExample("Roll 2d8", {"sides": 8, "count": 2}),
            CommandExample("Give me a random number", {"sides": 6}),
        ]

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        sides = int(kwargs.get("sides", 6))
        count = int(kwargs.get("count", 1))

        if sides < 2:
            return CommandResponse.error_response(
                error_details="A die must have at least 2 sides",
            )
        if count < 1 or count > 100:
            return CommandResponse.error_response(
                error_details="You can roll between 1 and 100 dice",
            )

        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)

        return CommandResponse.final_response(
            context_data={
                "rolls": rolls,
                "total": total,
                "sides": sides,
                "count": count,
                "message": f"Rolled {count}d{sides}: {rolls} (total: {total})",
            }
        )
```

## Step 8: Install the Command

Run the install script, then restart the node:

```bash
cd jarvis-node-setup
python scripts/install_command.py roll_dice
sudo systemctl restart jarvis-node   # or stop and start your dev process
```

The script runs the node's database migrations, resolves the command's `required_packages`, creates empty rows for its secrets and records it in the command registry. It does not reach the running node: the node discovers commands only when it starts (or when a Pantry install or a settings push refreshes it), hence the restart. After it, the node sends the new tool to `jarvisd` with its next voice turn, so "roll a d20" works from then on.

## Step 9: Test It

### E2E Testing

Add test cases to `test_command_parsing.py` and run it against your `jarvisd` (the harness reads the server address from the node's config; see [Testing Commands](testing.md#prerequisites)):

```bash
# List all tests to find your command
python test_command_parsing.py -l

# Run tests for your command
python test_command_parsing.py -c roll_dice
```

### Unit Testing

You can also test `run()` directly:

```python
from commands.dice_command import DiceCommand
from jarvis_command_sdk import RequestInformation

cmd = DiceCommand()
request = RequestInformation(voice_command="Roll 2d6", conversation_id="test")

response = cmd.run(request, sides=6, count=2)
assert response.success
assert len(response.context_data["rolls"]) == 2
assert all(1 <= r <= 6 for r in response.context_data["rolls"])
```

See [Testing Commands](testing.md) for comprehensive testing guidance.

## What's Next

- Add [parameters with enums](parameters.md) for constrained values
- Add [API integration](tutorial-api.md) for commands that call external services
- Add [OAuth authentication](tutorial-oauth.md) for commands that need user authorization
- Learn about [response patterns](responses.md) for interactive follow-up flows
