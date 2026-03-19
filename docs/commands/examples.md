# Examples & Training

Every command provides two sets of examples: **prompt examples** for real-time LLM inference, and **adapter examples** for LoRA fine-tuning. Understanding the difference and writing effective examples is critical for accurate command parsing.

## Two Example Sets

| | Prompt Examples | Adapter Examples |
|---|---|---|
| **Method** | `generate_prompt_examples()` | `generate_adapter_examples()` |
| **Purpose** | Teach the LLM in-context (at inference time) | Train a LoRA adapter (offline) |
| **Count** | 3-7 examples | 15-40+ examples |
| **Included in** | Every system prompt | Training data only |
| **Performance impact** | More examples = slower inference | More examples = better accuracy |
| **Coverage** | Core patterns only | Edge cases, variations, casual phrasings |

## CommandExample Structure

```python
@dataclass
class CommandExample:
    voice_command: str              # What the user says
    expected_parameters: dict       # Parameters the LLM should extract
    is_primary: bool = False        # At most 1 per example list
```

### The `is_primary` Flag

One example (at most) can be marked `is_primary=True`. This example is used for:

- **One-shot inference** -- when the system needs a single representative example
- **Primary example display** -- shown first in command listings

```python
CommandExample(
    voice_command="What's the weather in Chicago?",
    expected_parameters={"city": "Chicago"},
    is_primary=True,  # This is THE canonical example for this command
)
```

If no example is marked primary, the first example in the list is used as a fallback.

**Validation:** If you mark more than one example as primary, a `ValueError` is raised at runtime.

## Writing Prompt Examples

Prompt examples go into every LLM system prompt, so they must be concise and high-signal. Focus on the most common patterns.

### Good Prompt Examples

```python
def generate_prompt_examples(self) -> List[CommandExample]:
    return [
        # Primary: the most common usage pattern
        CommandExample(
            voice_command="What's the weather in Chicago?",
            expected_parameters={"city": "Chicago", "resolved_datetimes": ["today"]},
            is_primary=True,
        ),
        # No city (use default location)
        CommandExample(
            voice_command="What's the weather like?",
            expected_parameters={"resolved_datetimes": ["today"]},
        ),
        # Tomorrow
        CommandExample(
            voice_command="What's the forecast for tomorrow?",
            expected_parameters={"resolved_datetimes": ["tomorrow"]},
        ),
        # Unit preference
        CommandExample(
            voice_command="What's the weather in metric?",
            expected_parameters={"unit_system": "metric", "resolved_datetimes": ["today"]},
        ),
    ]
```

### Prompt Example Anti-Patterns

```python
# BAD: Too many examples (slows down inference, wastes context)
def generate_prompt_examples(self):
    return [example1, example2, ..., example20]  # No! Keep it to 3-7

# BAD: Redundant examples that don't teach new patterns
CommandExample("What's the weather?", {"resolved_datetimes": ["today"]}),
CommandExample("How's the weather?", {"resolved_datetimes": ["today"]}),
CommandExample("Tell me the weather", {"resolved_datetimes": ["today"]}),
# These all teach the same thing -- keep only one

# BAD: Missing important patterns
# If the LLM confuses your command with another, you need an example
# that shows the distinguishing characteristic
```

## Writing Adapter Examples

Adapter examples are used to train a LoRA adapter for better accuracy on smaller models. Be thorough and varied.

### Coverage Checklist

- [x] **Every parameter value** -- at least one example per enum value or common input
- [x] **Optional parameters omitted** -- examples with and without optional params
- [x] **Casual phrasings** -- "Do I need an umbrella?" not just "Weather forecast"
- [x] **Implicit defaults** -- "What's the weather?" (no date = today)
- [x] **Shorthand** -- "Roll 2d8" alongside "Roll 2 eight-sided dice"
- [x] **Written-out numbers** -- "seven" alongside "7"
- [x] **Edge cases** -- unusual but valid inputs

### Example: Calculator Adapter Examples

```python
def generate_adapter_examples(self) -> List[CommandExample]:
    items = [
        # One per operation
        ("What's 7 plus 9?", 7, 9, "add"),
        ("Add 18 and 4", 18, 4, "add"),
        ("What's 50 minus 13?", 50, 13, "subtract"),
        ("Subtract 7 from 22", 22, 7, "subtract"),
        ("What's 9 times 8?", 9, 8, "multiply"),
        ("What is 81 divided by 9?", 81, 9, "divide"),
        ("Divide 72 by 8", 72, 8, "divide"),

        # Floating point
        ("Add 3.5 and 2.1", 3.5, 2.1, "add"),

        # Written-out numbers
        ("What's seven times nine?", 7, 9, "multiply"),

        # Percentage (maps to multiply)
        ("What's 20 percent of 150?", 0.20, 150, "multiply"),

        # Casual
        ("Double forty-two", 42, 2, "multiply"),
        ("Half of sixty", 60, 2, "divide"),

        # Large numbers
        ("What's 1000 plus 2500?", 1000, 2500, "add"),
    ]
    examples = []
    for i, (utterance, num1, num2, op) in enumerate(items):
        examples.append(CommandExample(
            voice_command=utterance,
            expected_parameters={"num1": num1, "num2": num2, "operation": op},
            is_primary=(i == 0),
        ))
    return examples
```

### Example: Weather Adapter Examples

The weather command demonstrates patterns for implicit defaults and date handling:

```python
def generate_adapter_examples(self) -> List[CommandExample]:
    return [
        # Implicit today -- no date word = today
        CommandExample("What's the weather?", {"resolved_datetimes": ["today"]}, is_primary=True),
        CommandExample("How's the weather?", {"resolved_datetimes": ["today"]}),
        CommandExample("Do I need an umbrella?", {"resolved_datetimes": ["today"]}),

        # Implicit today + city
        CommandExample("Weather in Miami", {"city": "Miami", "resolved_datetimes": ["today"]}),
        CommandExample("Is it raining in Portland?", {"city": "Portland", "resolved_datetimes": ["today"]}),

        # Tomorrow
        CommandExample("Weather in Denver tomorrow", {"city": "Denver", "resolved_datetimes": ["tomorrow"]}),

        # Day after tomorrow
        CommandExample("Forecast for the day after tomorrow", {"resolved_datetimes": ["day_after_tomorrow"]}),

        # Weekend
        CommandExample("What's the weather this weekend?", {"resolved_datetimes": ["this_weekend"]}),
    ]
```

## How Examples Are Used

### At Inference Time

The command center builds a system prompt that includes all registered commands and their prompt examples. The LLM sees something like:

```
Available tools:

get_weather: Weather conditions or forecast (up to 5 days)
  Parameters: city (string, optional), resolved_datetimes (array<datetime>, required)
  Examples:
    "What's the weather in Chicago?" -> {city: "Chicago", resolved_datetimes: ["today"]}
    "What's the forecast for tomorrow?" -> {resolved_datetimes: ["tomorrow"]}

calculate: Perform two-number arithmetic
  Parameters: num1 (float), num2 (float), operation (string, enum: add/subtract/multiply/divide)
  Examples:
    "What's 5 plus 3?" -> {num1: 5, num2: 3, operation: "add"}
```

### During Adapter Training

The adapter training script (`train_node_adapter.py`) collects all adapter examples from all commands and builds training data:

```bash
cd jarvis-node-setup
python scripts/train_node_adapter.py \
  --base-model-id .models/Qwen2.5-7B \
  --hf-base-model-id Qwen/Qwen2.5-7B-Instruct
```

Each adapter example becomes a training pair:

- **Input:** System prompt + user utterance
- **Output:** Tool call with expected parameters

More diverse examples = better adapter accuracy, especially for smaller models (3B-14B).

## Training Workflow

### 1. Write Examples

Add or update adapter examples in your command file:

```python
def generate_adapter_examples(self) -> List[CommandExample]:
    return [...]
```

### 2. Install the Command

```bash
python scripts/install_command.py your_command
```

### 3. Train the Adapter

```bash
python scripts/train_node_adapter.py \
  --base-model-id .models/YourModel \
  --hf-base-model-id org/model-name
```

Optional flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--rank` | varies | LoRA rank |
| `--epochs` | varies | Training epochs |
| `--batch-size` | varies | Batch size |
| `--max-seq-len` | varies | Max sequence length |
| `--dry-run` | | Print payload without executing |

### 4. Monitor Training

```bash
curl http://localhost:7704/v1/training/status/<job_id>
```

### 5. Test

```bash
python test_command_parsing.py -c your_command
```

## Tips for Better Accuracy

1. **Diverse phrasings** -- include questions, imperatives, fragments, and casual speech
2. **Realistic inputs** -- use city names, real stock tickers, actual measurement units
3. **Negative examples via antipatterns** -- tell the LLM what NOT to confuse with your command
4. **Test-driven iteration** -- run E2E tests, find failures, add examples to fix them
5. **Keep prompt examples minimal** -- 3-5 high-signal examples beat 10 redundant ones
6. **Cover every enum value** -- if you have 4 operations, show at least one example per operation
7. **Show implicit defaults** -- if "no date" means "today", include examples without dates
