# Prompt Provider Reference

Complete interface reference for `IJarvisPromptProvider`, defined in `jarvis-command-center/app/core/interfaces/ijarvis_prompt_provider.py`.

## Interface Summary

```python
class IJarvisPromptProvider(ABC):
    # --- Abstract (must implement) ---
    name: str
    build_system_prompt(node_context, timezone, tools, available_commands) -> str

    # --- Optional properties (with defaults) ---
    use_tool_classifier: bool       # default: True
    supports_native_tools: bool     # default: False
    user_message_suffix: str        # default: ""

    # --- Optional methods (with defaults) ---
    get_response_format() -> Optional[Dict]
    parse_response(raw_content) -> Optional[str]
    build_tools(tools) -> List[Dict]

    # --- Training methods ---
    build_training_system_prompt() -> str
    build_training_completion(tool_call) -> str
    build_training_prompt(voice_command) -> str  # DEPRECATED

    # --- Metadata ---
    get_capabilities() -> Dict[str, Any]
```

---

## Abstract Members

These must be implemented by every provider.

### `name` (property)

```python
@property
@abstractmethod
def name(self) -> str: ...
```

Unique identifier used by `PromptProviderFactory` for matching. Compared case-insensitively.

**Convention:** `{Family}{Size}{Tier}` --- e.g., `Qwen25MediumUntrained`, `HermesMediumTrained`.

**Example:**

```python
@property
def name(self) -> str:
    return "Qwen25MediumUntrained"
```

---

### `build_system_prompt()`

```python
@abstractmethod
def build_system_prompt(
    self,
    node_context: Dict[str, Any],
    timezone: Optional[str],
    tools: List[Dict[str, Any]],
    available_commands: Optional[List[Dict[str, Any]]] = None,
) -> str: ...
```

Build the complete system prompt for an LLM call. This is the core method --- everything else is optional configuration around it.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_context` | `Dict[str, Any]` | Runtime context from the node. Contains `room`, `user`, `voice_mode`, `speaker_name`, `user_memories`, `agents` (agent context data), `room_hierarchy`, and other node metadata. |
| `timezone` | `Optional[str]` | User's IANA timezone string (e.g., `"America/New_York"`). May be `None`. |
| `tools` | `List[Dict[str, Any]]` | Tool definitions in OpenAI function-calling format. Each dict has `type`, `function` (with `name`, `description`, `parameters`). |
| `available_commands` | `Optional[List[Dict[str, Any]]]` | Command flag dicts with `command_name`, `allow_direct_answer`, `keywords`, and other metadata used for direct answer policy and example injection. |

**Returns:** Complete system prompt string ready for the LLM messages array.

**When to override:** Always --- this is abstract. Use the shared building blocks in `prompt_providers/shared/` to assemble your prompt.

**Example:**

```python
def build_system_prompt(
    self,
    node_context: Dict[str, Any],
    timezone: Optional[str],
    tools: List[Dict[str, Any]],
    available_commands: Optional[List[Dict[str, Any]]] = None,
) -> str:
    node_context = node_context or {}
    available_commands = available_commands or []

    room = node_context.get("room", "unknown")
    user = node_context.get("speaker_name") or node_context.get("user", "default")
    voice_mode = node_context.get("voice_mode", "brief")
    user_memories = node_context.get("user_memories", "")

    identity = build_identity_header(room, user, voice_mode, user_memories)
    rules = build_rules_block()
    tools_section = format_tools_for_prompt(tools, available_commands)
    agent_context = build_agent_context_summary(node_context)

    return f"{identity}\n\n{rules}\n{agent_context}\nTools:\n{tools_section}"
```

---

## Optional Properties

These have sensible defaults. Override only when your model needs different behavior.

### `use_tool_classifier` (property)

```python
@property
def use_tool_classifier(self) -> bool:
    return True
```

Whether the fastText tool classifier should provide routing hints to narrow the tool set.

- **`True` (default):** Untrained models benefit from seeing a smaller, pre-filtered tool list. The classifier predicts which tools are relevant and the prompt only includes those.
- **`False`:** Trained/adapter models that handle routing themselves. They see all tools.

**When to override:** Set to `False` for trained/adapter providers that have learned tool routing from fine-tuning data.

---

### `supports_native_tools` (property)

```python
@property
def supports_native_tools(self) -> bool:
    return False
```

Controls how tools are passed to the LLM and how responses are parsed.

**When `False` (default, text-based mode):**

1. Tools are embedded in the system prompt as formatted text
2. The model outputs tool calls as text (e.g., `<tool_call>` XML tags)
3. `parse_response()` transforms the text into Jarvis JSON
4. `ToolCallParser` processes the Jarvis JSON

**When `True` (native mode):**

1. `build_tools()` is called to format tools for the API's `tools` parameter
2. Tools are passed via the API request body, not in the system prompt
3. The backend handles structured tool call generation (grammar-constrained)
4. Tool calls are read from the structured response (`finish_reason="tool_calls"`)
5. `parse_response()` is not called

**When to override:** Set to `True` if your backend (vLLM, llama-cpp-python) reliably supports OpenAI-compatible function calling for your model. Text-based mode is more reliable for most local GGUF/MLX models.

---

### `user_message_suffix` (property)

```python
@property
def user_message_suffix(self) -> str:
    return ""
```

String appended to every user message before sending to the LLM. Used for model-specific control tokens.

**When to override:** When the model needs a control token in the user turn. For example, Qwen 3 supports a `/nothink` suffix to disable chain-of-thought reasoning for faster responses.

**Example:**

```python
@property
def user_message_suffix(self) -> str:
    return " /nothink"
```

---

## Optional Methods

### `get_response_format()`

```python
def get_response_format(self) -> Optional[Dict[str, Any]]:
    return None
```

Override the default JSON response format schema passed to the LLM backend.

- **`None` (default):** Uses the shared default from `system_prompt_builder`
- **`{"type": "text"}`:** Free-form text output (used when the provider handles parsing via `parse_response()`)
- **Custom schema:** A JSON schema dict for grammar-constrained output

**When to override:** When your model outputs tool calls in a non-JSON format (e.g., XML tags) and you handle parsing in `parse_response()`. Return `{"type": "text"}` to disable JSON grammar constraints.

**Example:**

```python
def get_response_format(self) -> Optional[Dict[str, Any]]:
    return {"type": "text"}  # Model outputs <tool_call> XML tags
```

---

### `parse_response()`

```python
def parse_response(self, raw_content: str) -> Optional[str]:
    return None
```

Transform raw LLM output into Jarvis JSON format. Only used when `supports_native_tools = False`.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `raw_content` | `str` | Raw text output from the LLM |

**Returns:**

- A Jarvis JSON string if the content was transformed
- `None` to pass `raw_content` to `ToolCallParser` unchanged

**Jarvis JSON format:**

```json
{
    "message": "Optional spoken text",
    "tool_calls": [
        {
            "name": "function_name",
            "arguments": {"param": "value"},
            "failure_message": "Fallback if this fails"
        }
    ],
    "error": null
}
```

**When to override:** When your model outputs tool calls in a model-specific format that needs transformation. Common transformations:

- Extract `<tool_call>` XML tags and wrap in Jarvis JSON
- Handle bare JSON tool calls (just `{"name": ..., "arguments": ...}`)
- Wrap plain text responses as Jarvis message JSON
- Normalize array parameters (e.g., wrap string values in lists)

**Example (Qwen 2.5 style):**

```python
def parse_response(self, raw_content: str) -> Optional[str]:
    cleaned = raw_content.strip()

    # Extract <tool_call> blocks
    matches = _TOOL_CALL_TAG_RE.findall(cleaned)
    if matches:
        calls = []
        for match in matches:
            try:
                calls.append(json.loads(match.strip()))
            except json.JSONDecodeError:
                continue
        if calls:
            return json.dumps({
                "message": "",
                "tool_calls": calls,
                "error": None,
            })

    # Already Jarvis JSON? Pass through
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "tool_calls" in parsed:
            return None
    except json.JSONDecodeError:
        pass

    # Plain text -> wrap as message
    if cleaned and not cleaned.startswith("{"):
        return json.dumps({
            "message": cleaned,
            "tool_calls": [],
            "error": None,
        })

    return None
```

---

### `build_tools()`

```python
def build_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return tools
```

Build OpenAI-format tool definitions for native tool calling. Only called when `supports_native_tools = True`.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | `List[Dict[str, Any]]` | Raw tool definitions from the tool registry |

**Returns:** OpenAI-format tool definitions ready for the API `tools` parameter.

**When to override:** When you need to customize tool schemas for your model (e.g., strip descriptions to save tokens, adjust parameter schemas, use `ToolBuilder` for clean formatting).

**Example:**

```python
from app.core.tool_builder import ToolBuilder

def build_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return ToolBuilder.build(tools)
```

---

## Training Methods

These methods control how fine-tuning data is formatted for LoRA adapter training.

### `build_training_system_prompt()`

```python
def build_training_system_prompt(self) -> str:
    return (
        "You are a function calling AI model. "
        "For each function call return a json object with function name and arguments "
        "within <tool_call></tool_call> XML tags as follows:\n"
        "<tool_call>\n"
        '{"name": "<function-name>", "arguments": {"<arg-name>": "<arg-value>"}, '
        '"failure_message": "<brief spoken response if this call fails>"}\n'
        "</tool_call>"
    )
```

Return the system message used for training examples. The training script wraps this as the system message in the chat template, the voice command as the user message, and `build_training_completion()` output as the assistant message.

**When to override:** When your model needs the training system prompt to match the structural cues it sees at inference (identity header, rules block, etc.). The Qwen 2.5 provider overrides this to include the full rules block and anti-hallucination mandate.

---

### `build_training_completion()`

```python
def build_training_completion(self, tool_call: Dict[str, Any]) -> str:
    return " " + json.dumps({
        "message": "",
        "tool_calls": [tool_call],
        "error": None,
    })
```

Format a tool call as the model is expected to output it during inference. This becomes the assistant message in training examples.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool_call` | `Dict[str, Any]` | A single tool call dict with `name`, `arguments`, and optionally `failure_message` |

**Returns:** Formatted string matching the model's expected output format.

**When to override:** When your model outputs tool calls in a format other than raw Jarvis JSON. For example, the Qwen 2.5 provider wraps the call in `<tool_call>` XML tags:

```python
def build_training_completion(self, tool_call: Dict[str, Any]) -> str:
    return f" <tool_call>\n{json.dumps(tool_call)}\n</tool_call>"
```

---

### `build_training_prompt()` (DEPRECATED)

```python
def build_training_prompt(self, voice_command: str) -> str: ...
```

**Deprecated.** Use `build_training_system_prompt()` + voice command with the tokenizer's chat template instead. Kept for backward compatibility with older training scripts that do not support chat templates.

---

## Metadata

### `get_capabilities()`

```python
def get_capabilities(self) -> Dict[str, Any]:
    return {
        "provider_name": self.name,
        "model_family": "unknown",
        "size_tier": "unknown",
        "training_tier": "unknown",
        "use_tool_classifier": self.use_tool_classifier,
    }
```

Return metadata about this provider for health checks, admin UI, and debugging.

**Expected keys:**

| Key | Type | Description |
|-----|------|-------------|
| `provider_name` | `str` | Same as `name` property |
| `model_family` | `str` | Model family identifier (e.g., `"qwen"`, `"hermes"`, `"llama"`, `"phi"`) |
| `size_tier` | `str` | `"small"`, `"medium"`, or `"large"` |
| `training_tier` | `str` | `"untrained"` or `"trained"` |
| `use_tool_classifier` | `bool` | Whether fastText routing is enabled |
| `supports_native_tools` | `bool` | (optional) Whether native tool calling is used |

**When to override:** Always override to provide accurate metadata. The default returns `"unknown"` for most fields.

---

## Method Call Flow

### Text-Based Mode (`supports_native_tools = False`)

```
Voice request arrives
  │
  ▼
PromptProviderFactory.create_provider(name)
  │
  ▼
provider.build_system_prompt(node_context, tz, tools, commands)
  │  → Assembles identity + rules + tools section + agent context
  │
  ▼
provider.get_response_format()
  │  → Usually {"type": "text"} for XML-tag models
  │
  ▼
LLM inference (system prompt in messages, no tools param)
  │
  ▼
provider.parse_response(raw_content)
  │  → Extracts <tool_call> tags → Jarvis JSON
  │  → Or wraps plain text as Jarvis message
  │
  ▼
ToolCallParser processes Jarvis JSON
  │
  ▼
Tool execution
```

### Native Mode (`supports_native_tools = True`)

```
Voice request arrives
  │
  ▼
PromptProviderFactory.create_provider(name)
  │
  ▼
provider.build_system_prompt(node_context, tz, tools, commands)
  │  → Assembles identity + rules + agent context (no tools section)
  │
  ▼
provider.build_tools(tools)
  │  → OpenAI-format tool definitions
  │
  ▼
LLM inference (tools passed via API tools param)
  │
  ▼
Structured tool_calls read from response
  │  → parse_response() is NOT called
  │
  ▼
Tool execution
```

### Training Data Generation

```
Training script
  │
  ▼
provider.build_training_system_prompt()
  │  → System message for chat template
  │
  ▼
voice_command (raw text)
  │  → User message for chat template
  │
  ▼
provider.build_training_completion(tool_call)
  │  → Assistant message for chat template
  │
  ▼
tokenizer.apply_chat_template([system, user, assistant])
  │  → Properly formatted training example with special tokens
```

## Source Files

| File | Description |
|------|-------------|
| `jarvis-command-center/app/core/interfaces/ijarvis_prompt_provider.py` | `IJarvisPromptProvider` ABC (this reference) |
| `jarvis-command-center/app/core/prompt_provider_factory.py` | Discovery and creation |
| `jarvis-command-center/app/core/prompt_providers/shared/core_rules.py` | Shared rule constants and builders |
| `jarvis-command-center/app/core/prompt_providers/shared/context_builders.py` | Agent context and room hierarchy builders |
| `jarvis-command-center/app/core/prompt_providers/shared/tool_formatters.py` | Tool formatting for prompt text |
| `jarvis-command-center/app/core/prompt_providers/medium/untrained/qwen25_medium_untrained.py` | Reference implementation |
