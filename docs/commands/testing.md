# Testing Commands

Jarvis provides three levels of testing for commands: E2E command parsing tests, multi-turn conversation tests, and direct unit tests. Use all three for comprehensive coverage.

The two harnesses (`test_command_parsing.py` and `test_multi_turn_conversation.py`) live in a source checkout of [jarvis-node-setup](https://github.com/alexberardi/jarvis-node-setup) and talk to your `jarvisd` the way a node does. Unit tests need only the SDK.

## E2E Command Parsing Tests

`test_command_parsing.py` tests the "front half" of the pipeline: given a voice command, does the model select the right command and extract the right parameters?

### Prerequisites

1. **A running `jarvisd` with a live model.** Both harnesses send real model turns; check the model is loaded in the admin first (see [Install](../install/index.md)).
2. **A dev node paired with it.** Set up the jarvis-node-setup checkout as a node and pair it with your server (see [Node](../clients/node-setup.md)). Pairing writes the node's config: `node_id`, `api_key` and `jarvis_command_center_api_url`, which is your server's address, `http://<server>:7700`. The harnesses read that config, so run them with the same `CONFIG_PATH` the dev node uses.
3. **Your command in the checkout**, installed with `python scripts/install_command.py <name>`.

Nothing else needs to run: speech, the model and the conversation state are all inside `jarvisd`.

### Running Tests

```bash
cd jarvis-node-setup

# Run all tests
python test_command_parsing.py

# List all available tests with indices
python test_command_parsing.py -l

# Run specific tests by index
python test_command_parsing.py -t 5 7 11

# Run all tests for specific commands
python test_command_parsing.py -c calculate get_weather

# Custom output file
python test_command_parsing.py -o my_results.json
```

### Test Structure

Each test is a `CommandTest` with a voice command, expected command name, and expected parameters:

```python
class CommandTest:
    def __init__(
        self,
        voice_command: str,          # "What's 5 plus 3?"
        expected_command: str,       # "calculate"
        expected_params: dict,       # {"num1": 5, "num2": 3, "operation": "add"}
        description: str,            # Human-readable test description
        ha_context: dict | None = None,  # Optional Home Assistant context
    ):
```

### Adding Tests for Your Command

Add test cases to the test list in `test_command_parsing.py`:

```python
CommandTest(
    voice_command="Roll a d20",
    expected_command="roll_dice",
    expected_params={"sides": 20},
    description="Roll a 20-sided die",
),
CommandTest(
    voice_command="Roll 3 twelve-sided dice",
    expected_command="roll_dice",
    expected_params={"sides": 12, "count": 3},
    description="Roll multiple dice with custom sides",
),
```

### Understanding Results

Results are written to `test_results.json` (or your custom path). The file has this shape (values shortened):

```json
{
    "summary": {
        "total_tests": 50,
        "passed": 47,
        "failed": 3,
        "success_rate": 94.0,
        "avg_response_time": 0.85,
        "min_response_time": 0.41,
        "max_response_time": 2.3,
        "test_run_timestamp": "2026-10-21 14:02:11"
    },
    "test_results": [
        {
            "test_number": 0,
            "passed": true,
            "description": "Roll a 20-sided die",
            "voice_command": "Roll a d20",
            "expected": {"command": "roll_dice", "parameters": {"sides": 20}},
            "actual": {"command": "roll_dice", "parameters": {"sides": 20}},
            "pre_routed": false,
            "response_time_seconds": 0.72,
            "conversation_id": "...",
            "failure_reason": null,
            "full_response": {}
        }
    ],
    "failed_test_details": [],
    "analysis": {
        "command_success_rates": {
            "get_weather": {"success_rate": 87.5, "passed": 7, "failed": 1, "total": 8},
            "calculate": {"success_rate": 100.0, "passed": 5, "failed": 0, "total": 5}
        },
        "command_confusion_matrix": {
            "get_weather → search_web": 1
        },
        "parameter_extraction_issues": {},
        "recommendations": []
    },
    "slow_tests": []
}
```

Key sections:

- **summary** -- overall pass/fail counts, success rate and response times (in seconds)
- **test_results** -- per-test details with expected vs. actual (`pre_routed` is true when the fast path answered)
- **analysis** -- per-command success rates (lowest first), a confusion matrix of `expected → actual` commands, parameter extraction issues, and suggested fixes

### Interpreting Failures

| Failure Type | Meaning | Fix |
|-------------|---------|-----|
| Wrong command selected | The model confused this with another command | Add `antipatterns`, improve `description`, add more examples |
| Wrong parameters | Right command, wrong param values | Add more `prompt_examples` for this pattern, add `critical_rules` |
| Missing parameters | Required param not extracted | Check `description` on the parameter, add examples showing this param |
| Extra parameters | The model hallucinated a parameter | Add `rules` telling the model what NOT to include |

---

## Multi-Turn Conversation Tests

`test_multi_turn_conversation.py` tests the "back half": tool execution, validation flows, context preservation, and result incorporation.

### Prerequisites

The same as for the parsing tests: a dev node's config pointing at your `jarvisd`.

### Running Tests

```bash
cd jarvis-node-setup

# Fast mode (text-based, no audio)
python test_multi_turn_conversation.py

# List all tests
python test_multi_turn_conversation.py -l

# Run specific category
python test_multi_turn_conversation.py -c validation

# Run specific tests by index
python test_multi_turn_conversation.py -t 0 1 2
```

!!! warning "Full mode is not known to work on jarvisd"
    `--full` (and `--save-audio <dir>`) put each turn through text-to-speech and then speech-to-text before the model sees it. The harness still calls a separate TTS and Whisper service: `jarvis_tts_api_url` and `jarvis_whisper_api_url` from the node's config, defaulting to `http://localhost:7707` and `http://localhost:7706`, the ports of the old stack. On `jarvisd` both run inside the server, and its own `/speak` and `/transcribe` routes expect an app login, not the node key the harness sends. Full mode has not been tried against `jarvisd`; use fast mode.

### Test Categories

| Category | Tests |
|----------|-------|
| `tool_execution` | Single-turn tool execution (happy path) |
| `validation` | Validation and clarification flows |
| `result_incorporation` | Tool results appear in final spoken response |
| `context` | Context preservation across turns |
| `error_handling` | Graceful error handling |
| `complex` | Complex queries (knowledge, unit conversions) |

### Test Structure

Multi-turn tests define a sequence of conversation turns:

```python
@dataclass
class Turn:
    voice_command: str | None           # What the user says (None for continuation)
    expected_stop_reason: StopReason    # tool_calls, validation_required, or complete
    expected_tool: str | None = None    # Expected tool to be called
    expected_params: dict | None = None # Expected parameters (subset match)
    validation_response: str | None = None  # Response if validation is needed

@dataclass
class MultiTurnTest:
    description: str
    turns: list[Turn]
    category: str = "general"
    verify_response_contains: str | None = None  # Check final response text
```

### Example Multi-Turn Test

```python
MultiTurnTest(
    description="Calculator with follow-up",
    category="context",
    turns=[
        Turn(
            voice_command="What's 5 plus 3?",
            expected_stop_reason=StopReason.TOOL_CALLS,
            expected_tool="calculate",
            expected_params={"num1": 5, "num2": 3, "operation": "add"},
        ),
        Turn(
            voice_command="Now multiply that by 2",
            expected_stop_reason=StopReason.TOOL_CALLS,
            expected_tool="calculate",
            expected_params={"num1": 8, "num2": 2, "operation": "multiply"},
        ),
    ],
    verify_response_contains="16",
)
```

---

## Unit Testing `run()` Directly

For fast iteration on command logic, test `run()` directly without `jarvisd` or a model. These tests need only the SDK (`pip install git+https://github.com/alexberardi/jarvis-command-sdk.git`) and your command's module.

### Basic Pattern

```python
import pytest

from commands.dice_command import DiceCommand
from jarvis_command_sdk import RequestInformation


@pytest.fixture
def cmd():
    return DiceCommand()


@pytest.fixture
def request_info():
    return RequestInformation(
        voice_command="test",
        conversation_id="test-conv-001",
    )


def test_basic_roll(cmd, request_info):
    response = cmd.run(request_info, sides=6, count=1)
    assert response.success
    assert len(response.context_data["rolls"]) == 1
    assert 1 <= response.context_data["rolls"][0] <= 6


def test_multiple_dice(cmd, request_info):
    response = cmd.run(request_info, sides=20, count=3)
    assert response.success
    assert len(response.context_data["rolls"]) == 3
    assert response.context_data["total"] == sum(response.context_data["rolls"])


def test_invalid_sides(cmd, request_info):
    response = cmd.run(request_info, sides=1, count=1)
    assert not response.success
    assert "at least 2 sides" in response.error_details


def test_too_many_dice(cmd, request_info):
    response = cmd.run(request_info, sides=6, count=101)
    assert not response.success
    assert "between 1 and 100" in response.error_details
```

### Testing the Full Execute Pipeline

To test validation, use `execute()` instead of `run()`:

```python
from commands.calculator_command import CalculatorCommand


def test_execute_with_missing_required_param(request_info):
    """execute() raises ValueError for missing required params"""
    with pytest.raises(ValueError, match="Missing required params"):
        CalculatorCommand().execute(request_info)  # No kwargs provided


def test_execute_with_invalid_enum(request_info):
    """execute() returns validation_error for invalid enum values"""
    response = CalculatorCommand().execute(
        request_info, num1=5, num2=3, operation="invalid_op",
    )
    assert not response.success
    assert response.context_data.get("_validation_error")
```

### Testing Pre-Route

```python
def test_pre_route_matches(cmd):
    result = cmd.pre_route("pause")
    assert result is not None
    assert result.arguments == {"action": "pause"}


def test_pre_route_falls_through(cmd):
    result = cmd.pre_route("play some jazz music in the living room")
    assert result is None  # Too complex, falls through to the model


def test_pre_route_honours_disabled_pattern(cmd):
    assert cmd.pre_route("pause", disabled_pattern_ids={"music.pause"}) is None
```

### Testing Post-Process

```python
def test_post_process_fixes_missing_query(cmd):
    args = {"action": "play"}
    result = cmd.post_process_tool_call(args, "Play some jazz")
    assert result["query"] == "jazz"


def test_post_process_preserves_existing_query(cmd):
    args = {"action": "play", "query": "Beatles"}
    result = cmd.post_process_tool_call(args, "Play Beatles")
    assert result["query"] == "Beatles"  # Unchanged
```

### Testing Handle Action

```python
def test_handle_send_action(cmd, request_info):
    context = {
        "draft": {"to": "alice@example.com", "subject": "Hi", "body": "Hello!"}
    }
    response = cmd.handle_action("send_click", context)
    assert response.success


def test_handle_cancel_action(cmd, request_info):
    response = cmd.handle_action("cancel_click", {})
    assert response.success
    assert response.context_data["cancelled"]


def test_handle_unknown_action(cmd, request_info):
    response = cmd.handle_action("unknown_action", {})
    assert not response.success
```

### Passing Secrets

A command that reads its secrets from the `secrets` keyword (as the [API tutorial](tutorial-api.md)'s does) needs no mocking: pass them to `execute()`, as the node does.

```python
from jarvis_command_sdk import MissingSecretsError

from commands.stock_price_command import StockPriceCommand


class FakeQuote:
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return {"name": "Apple", "price": 190.5, "change": 1.2, "change_percent": 0.6}


def test_run_with_api_key(request_info, monkeypatch):
    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: FakeQuote())
    response = StockPriceCommand().execute(
        request_info,
        secrets={"FINANCE_API_KEY": "test-key-123", "FINANCE_DEFAULT_CURRENCY": "USD"},
        ticker="AAPL",
    )
    assert response.success


def test_missing_api_key(request_info):
    with pytest.raises(MissingSecretsError):
        StockPriceCommand().execute(request_info, secrets={}, ticker="AAPL")
```

For code that reads secrets through `JarvisStorage`, register a fake backend for the test:

```python
from unittest.mock import MagicMock

from jarvis_command_sdk import StorageBackend, set_backend


@pytest.fixture
def fake_secrets():
    backend = MagicMock(spec=StorageBackend)
    values = {("OPENWEATHER_LOCATION", "integration"): "Miami,FL,US"}
    backend.get_secret.side_effect = lambda key, scope, user_id=None: values.get((key, scope))
    set_backend(backend)
    yield backend
    set_backend(None)
```

### Mocking HTTP Requests

The tutorial's command calls `httpx.get`, so patch that:

```python
from unittest.mock import patch

import httpx


@patch("httpx.get")
def test_api_timeout(mock_get, request_info):
    mock_get.side_effect = httpx.TimeoutException("timeout")
    response = StockPriceCommand().execute(
        request_info, secrets={"FINANCE_API_KEY": "test-key"}, ticker="AAPL",
    )
    assert not response.success
    assert "not responding" in response.error_details
```

!!! note "Commands that import `services.secret_service`"
    An older command that does `from services.secret_service import get_secret_value` holds its own reference to the function, so patch it where it is looked up, `commands.<module>.get_secret_value`, not `services.secret_service.get_secret_value`. Better: move it to the `secrets` keyword or `JarvisStorage`.

## Running Tests

```bash
cd jarvis-node-setup

# Run all unit tests
pytest

# Run tests for a specific command
pytest tests/test_dice_command.py

# Run with coverage
pytest --cov=commands --cov-report=html

# Run with verbose output
pytest -v tests/test_dice_command.py
```

## Test Strategy Summary

| Level | What It Tests | Speed | Needs |
|-------|---------------|-------|-------|
| Unit tests (`pytest`) | `run()` logic, validation, pre_route | Fast (ms) | The SDK only |
| E2E parsing (`test_command_parsing.py`) | Model command selection + parameter extraction | Medium (1-2s/test) | A paired dev node config and `jarvisd` with a live model |
| Multi-turn (`test_multi_turn_conversation.py`) | Execution flow, validation, context | Medium (1-2s/turn) | The same |

**Recommended workflow:**

1. Write unit tests first (TDD)
2. Add E2E parsing tests for your command
3. Add multi-turn tests for complex flows
4. Try it by voice on a node before you ship it
