# Testing Commands

Jarvis provides three levels of testing for commands: E2E command parsing tests, multi-turn conversation tests, and direct unit tests. Use all three for comprehensive coverage.

## E2E Command Parsing Tests

`test_command_parsing.py` tests the "front half" of the pipeline: given a voice command, does the LLM select the right command and extract the right parameters?

### Prerequisites

1. **Register a dev node** (see [jarvis-node-setup CLAUDE.md](https://github.com/alexberardi/jarvis/blob/main/jarvis-node-setup/CLAUDE.md#node-authentication-dev-setup))
2. **Start required services:**

```bash
# Command center (port 7703)
cd jarvis-command-center && ./run-docker-dev.sh

# LLM proxy (port 7704)
cd jarvis-llm-proxy-api && ./run.sh
```

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
        ha_context: dict | None,     # Optional Home Assistant context
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

Results are written to `test_results.json` (or your custom path). The output includes:

```json
{
    "summary": {
        "total": 50,
        "passed": 47,
        "failed": 3,
        "success_rate": 94.0,
        "avg_response_time_ms": 850
    },
    "results": [
        {
            "voice_command": "Roll a d20",
            "expected_command": "roll_dice",
            "actual_command": "roll_dice",
            "expected_params": {"sides": 20},
            "actual_params": {"sides": 20},
            "passed": true,
            "response_time_ms": 720
        }
    ],
    "analysis": {
        "command_success_rates": {
            "calculate": {"total": 5, "passed": 5, "rate": 100.0},
            "get_weather": {"total": 8, "passed": 7, "rate": 87.5}
        },
        "confusion_matrix": {
            "get_weather -> search_web": 1
        }
    }
}
```

Key sections:

- **summary** -- overall pass/fail counts and success rate
- **results** -- per-test details with expected vs. actual
- **analysis** -- command-level success rates and confusion matrix showing which commands get confused with which

### Interpreting Failures

| Failure Type | Meaning | Fix |
|-------------|---------|-----|
| Wrong command selected | LLM confused this with another command | Add `antipatterns`, improve `description`, add more examples |
| Wrong parameters | Right command, wrong param values | Add more `prompt_examples` for this pattern, add `critical_rules` |
| Missing parameters | Required param not extracted | Check `description` on the parameter, add examples showing this param |
| Extra parameters | LLM hallucinated a parameter | Add `rules` telling the LLM what NOT to include |

---

## Multi-Turn Conversation Tests

`test_multi_turn_conversation.py` tests the "back half": tool execution, validation flows, context preservation, and result incorporation.

### Prerequisites

Same as E2E parsing tests, plus optionally:

```bash
# For full audio pipeline mode:
cd jarvis-tts && ./run-docker-dev.sh       # TTS (port 7707)
cd jarvis-whisper-api && ./run-dev.sh       # Whisper (port 7706)
```

### Running Tests

```bash
cd jarvis-node-setup

# Fast mode (text-based, no audio)
python test_multi_turn_conversation.py

# Full mode (TTS -> Whisper -> Command Center)
python test_multi_turn_conversation.py --full

# List all tests
python test_multi_turn_conversation.py -l

# Run specific category
python test_multi_turn_conversation.py -c validation

# Run specific tests by index
python test_multi_turn_conversation.py -t 0 1 2

# Save audio artifacts (full mode only)
python test_multi_turn_conversation.py --full -t 0 1 2 --save-audio ./audio_artifacts/
```

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
    expected_tool: str | None           # Expected tool to be called
    expected_params: dict | None        # Expected parameters (subset match)
    validation_response: str | None     # Response if validation is needed

@dataclass
class MultiTurnTest:
    description: str
    turns: list[Turn]
    category: str
    verify_response_contains: str | None  # Check final response text
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

### Fast vs. Full Mode

| Aspect | Fast Mode | Full Mode |
|--------|-----------|-----------|
| Input | Text sent directly | TTS generates audio, Whisper transcribes |
| Speed | ~1s per turn | ~5-10s per turn |
| Coverage | Command parsing + execution | Full audio pipeline |
| Services needed | CC + LLM proxy | CC + LLM proxy + TTS + Whisper |
| Use when | Developing/iterating | Final verification before deploy |

---

## Unit Testing `run()` Directly

For fast iteration on command logic, test `run()` directly without involving the command center or LLM.

### Basic Pattern

```python
import pytest
from commands.dice_command import DiceCommand
from core.request_information import RequestInformation


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
def test_execute_with_missing_required_param(cmd, request_info):
    """execute() should raise ValueError for missing required params"""
    # If your command has required params, omitting them should fail
    with pytest.raises(ValueError, match="Missing required params"):
        cmd.execute(request_info)  # No kwargs provided


def test_execute_with_invalid_enum(cmd, request_info):
    """execute() should return validation_error for invalid enum values"""
    # For a command with enum parameters like calculator
    calc = CalculatorCommand()
    response = calc.execute(request_info, num1=5, num2=3, operation="invalid_op")
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
    assert result is None  # Too complex, falls through to LLM
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

### Mocking Secrets

For commands that depend on secrets, mock `get_secret_value`:

```python
from unittest.mock import patch


@patch("services.secret_service.get_secret_value")
def test_run_with_api_key(mock_secret, cmd, request_info):
    mock_secret.side_effect = lambda key, scope: {
        ("FINANCE_API_KEY", "integration"): "test-key-123",
        ("FINANCE_DEFAULT_CURRENCY", "integration"): "USD",
    }.get((key, scope))

    response = cmd.run(request_info, ticker="AAPL")
    assert response.success
```

### Mocking HTTP Requests

```python
from unittest.mock import patch, MagicMock


@patch("httpx.get")
@patch("services.secret_service.get_secret_value", return_value="test-key")
def test_api_timeout(mock_secret, mock_get, cmd, request_info):
    mock_get.side_effect = httpx.TimeoutException("timeout")
    response = cmd.run(request_info, ticker="AAPL")
    assert not response.success
    assert "not responding" in response.error_details
```

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

| Level | What It Tests | Speed | Services Needed |
|-------|---------------|-------|-----------------|
| Unit tests (`pytest`) | `run()` logic, validation, pre_route | Fast (ms) | None |
| E2E parsing (`test_command_parsing.py`) | LLM command selection + parameter extraction | Medium (1-2s/test) | CC + LLM proxy |
| Multi-turn fast (`test_multi_turn_conversation.py`) | Execution flow, validation, context | Medium (1-2s/turn) | CC + LLM proxy |
| Multi-turn full (`--full`) | Complete audio pipeline | Slow (5-10s/turn) | CC + LLM + TTS + Whisper |

**Recommended workflow:**

1. Write unit tests first (TDD)
2. Add E2E parsing tests for your command
3. Add multi-turn tests for complex flows
4. Run full mode before deploying to production nodes
