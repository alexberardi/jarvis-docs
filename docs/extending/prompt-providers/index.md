# Prompt Providers

> **The Wordsmiths** --- Prompt providers craft the precise language that shapes how the LLM understands and responds to voice commands. They tailor every system prompt, tool schema, and instruction to the specific model being used --- the right framing for the right mind.

Prompt providers run on the **Command Center** (not the node). They control how the system prompt is constructed for a specific LLM model family. Different models need different prompt formats --- Qwen 2.5 uses `<tool_call>` XML tags, Hermes uses its own tool-calling syntax, and some models support native structured tool calling. Prompt providers encapsulate these differences behind a single interface.

## Why Prompt Providers Exist

The Command Center uses local LLMs (via `jarvis-llm-proxy-api`) to parse voice commands into tool calls. Each model family has its own:

- **System prompt format** --- how to present tools, rules, and context
- **Tool call format** --- XML tags, JSON blocks, native function calling
- **Response parsing** --- extracting structured tool calls from raw text output
- **Training data format** --- how to build fine-tuning examples

Without prompt providers, this logic would be scattered across the model service with conditionals. Instead, each model family gets a clean class that owns its prompt construction end-to-end.

## Where They Live

Prompt providers are organized in a directory hierarchy under the Command Center:

```
jarvis-command-center/app/core/prompt_providers/
├── __init__.py
├── shared/                          # Shared building blocks
│   ├── core_rules.py                # Identity header, rules, fallback
│   ├── context_builders.py          # Agent context, room hierarchy
│   ├── tool_formatters.py           # Format tools for prompt text
│   └── command_converters.py        # Command-to-tool conversion
├── small/
│   ├── trained/
│   │   └── custom/                  # User variants
│   └── untrained/
│       ├── llama_small_untrained.py
│       ├── llama32_3b_compressed.py
│       ├── qwen25_3b_compressed.py
│       └── custom/
├── medium/
│   ├── trained/
│   │   ├── hermes_medium_trained.py
│   │   └── custom/
│   └── untrained/
│       ├── qwen25_medium_untrained.py   # Active in production
│       ├── hermes_medium_untrained.py
│       ├── llama31_medium_untrained.py
│       ├── mistral7b_medium_untrained.py
│       ├── gemma2_medium_untrained.py
│       ├── hermes_medium_mlx.py
│       └── custom/
└── large/
    ├── trained/
    │   └── custom/
    └── untrained/
        ├── qwen25_large_untrained.py
        ├── qwen25_14b_untrained.py
        ├── qwen3_large_untrained.py
        ├── mixtral_large_untrained.py
        └── custom/
```

### Naming Convention

Provider names follow the pattern `{Family}{Size}{Tier}`:

| Component | Values | Example |
|-----------|--------|---------|
| Family | `Qwen25`, `Hermes`, `Llama31`, `Mistral7b`, `Gemma2`, `Qwen3` | `Qwen25` |
| Size | `Small`, `Medium`, `Large` | `Medium` |
| Tier | `Untrained`, `Trained` | `Untrained` |

Combined: `Qwen25MediumUntrained`, `HermesMediumTrained`, `Llama31MediumUntrained`

### Size Tiers

| Tier | Parameter Range | Example Models |
|------|----------------|----------------|
| Small | 1B--4B | Llama 3.2 3B, Qwen 2.5 3B |
| Medium | 5B--13B | Qwen 2.5 7B, Hermes 3 8B, Mistral 7B |
| Large | 14B+ | Qwen 2.5 14B, Qwen 3 32B, Mixtral 8x7B |

## Discovery and Configuration

### How Providers Are Found

The `PromptProviderFactory` discovers providers at runtime by recursively scanning `app/core/prompt_providers/` using `pkgutil.walk_packages`. For each Python module found, it inspects all classes, looking for subclasses of `IJarvisPromptProvider`. It then instantiates each one and compares its `name` property (case-insensitive) against the requested provider name.

There is no registration step. Drop a `.py` file in the appropriate subdirectory, implement `IJarvisPromptProvider`, and the factory will find it.

### How the Active Provider Is Selected

The active provider is resolved via a settings cascade:

1. **Database setting** `llm.interface` (via `jarvis-settings-client`) --- checked first
2. **Environment variable** `JARVIS_MODEL_INTERFACE` --- fallback
3. **Hardcoded default** `JarvisToolModel` --- last resort

To change the active provider:

```sql
-- Via database (preferred)
UPDATE settings SET value = 'Qwen25MediumUntrained' WHERE key = 'llm.interface';
```

```bash
# Via environment variable
export JARVIS_MODEL_INTERFACE=Qwen25MediumUntrained
```

### Listing Available Providers

```python
from app.core.prompt_provider_factory import PromptProviderFactory

names = PromptProviderFactory.get_available_providers()
# ['Gemma2Compressed', 'Gemma2MediumUntrained', 'HermesCompressed', ...]

info = PromptProviderFactory.get_provider_info("Qwen25MediumUntrained")
# {
#     "name": "Qwen25MediumUntrained",
#     "class": "Qwen25MediumUntrained",
#     "module": "app.core.prompt_providers.medium.untrained.qwen25_medium_untrained",
#     "capabilities": {
#         "provider_name": "Qwen25MediumUntrained",
#         "model_family": "qwen",
#         "size_tier": "medium",
#         "training_tier": "untrained",
#         "use_tool_classifier": True,
#         "supports_native_tools": False,
#     },
# }
```

## Shared Building Blocks

All providers share a set of utilities in `prompt_providers/shared/` that produce the common sections of a system prompt. This avoids duplication --- when a rule needs updating, it changes in one place.

### `core_rules.py`

Provides the identity header, rules block, and fallback line:

- **`build_identity_header(room, user, voice_mode, user_memories)`** --- "You are Jarvis, a function calling voice assistant. Context: room=kitchen, user=alex, style=brief" plus user memories if present
- **`build_rules_block(param_names_rule, extra_rules, terminology)`** --- Assembled from shared rule constants (one tool at a time, extract params, STT awareness, date params, etc.). The `terminology` parameter substitutes "function" or "tool" throughout.
- **`build_fallback_line(hermes_style)`** --- What to do when no tool matches

### `context_builders.py`

Builds agent context (Home Assistant devices, room hierarchy) from `node_context`:

- **`build_agent_context_summary(node_context)`** --- Compact summary (~50 tokens) with device counts per domain and floor layout. Tells the LLM to call `get_ha_entities` for specifics.
- **`build_agent_context_by_room(node_context)`** --- Full device listing grouped by room/area. Used when context window allows it.
- **`build_direct_answer_section(available_commands)`** --- Policy section listing which commands must use tools vs which allow direct answers.
- **`build_room_hierarchy_section(node_context)`** --- Room parent/child relationships so the LLM knows "upstairs" includes "bedroom 1, bedroom 2, hallway."

### `tool_formatters.py`

Thin wrapper around `tool_call_parser.format_tools_for_prompt()`:

- **`format_tools_for_prompt(tools, available_commands, primary_examples_only)`** --- Formats tool definitions as text for inclusion in the system prompt. The `primary_examples_only` flag limits examples to save context window space.

## Two Modes of Tool Calling

Prompt providers support two modes, controlled by the `supports_native_tools` property.

### Text-Based Tool Calling (default)

When `supports_native_tools = False`:

1. Tools are embedded in the system prompt as text (formatted by the provider)
2. The LLM outputs tool calls as text (e.g., `<tool_call>{"name": "...", "arguments": {...}}</tool_call>`)
3. The provider's `parse_response()` method transforms this text into Jarvis JSON
4. `ToolCallParser` processes the Jarvis JSON

This is the default and most reliable mode for local GGUF/MLX models.

### Native Tool Calling

When `supports_native_tools = True`:

1. Tools are passed via the API's `tools` parameter (formatted by `build_tools()`)
2. The LLM backend handles tool call formatting internally
3. Tool calls are read from the structured response (`finish_reason="tool_calls"`)
4. `parse_response()` is not used

This mode works with backends that support OpenAI-compatible function calling (e.g., vLLM, llama-cpp-python with grammar constraints).

## Tutorial: Writing a Custom Prompt Provider

This tutorial creates a prompt provider for a hypothetical "Phi-3 Medium" model. We will extend the shared building blocks to minimize boilerplate.

### Step 1: Create the File

Create `jarvis-command-center/app/core/prompt_providers/medium/untrained/phi3_medium_untrained.py`:

```python
import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.interfaces.ijarvis_prompt_provider import IJarvisPromptProvider
from app.core.prompt_providers.shared.context_builders import (
    build_agent_context_summary,
    build_direct_answer_section,
)
from app.core.prompt_providers.shared.core_rules import (
    ANTI_HALLUCINATION_MANDATE,
    build_fallback_line,
    build_identity_header,
    build_rules_block,
)
from app.core.prompt_providers.shared.tool_formatters import format_tools_for_prompt

logger = logging.getLogger("uvicorn")

# Regex for the model's tool call output format
_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL
)


class Phi3MediumUntrained(IJarvisPromptProvider):
    """Prompt provider for Phi-3 Medium (untrained)."""

    @property
    def name(self) -> str:
        return "Phi3MediumUntrained"

    @property
    def use_tool_classifier(self) -> bool:
        return True  # Untrained models need fastText routing hints

    @property
    def supports_native_tools(self) -> bool:
        return False  # Text-based tool calling

    def build_system_prompt(
        self,
        node_context: Dict[str, Any],
        timezone: Optional[str],
        tools: List[Dict[str, Any]],
        available_commands: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        available_commands = available_commands or []
        node_context = node_context or {}

        room: str = node_context.get("room", "unknown")
        user: str = (
            node_context.get("speaker_name")
            or node_context.get("user", "default")
        )
        voice_mode: str = node_context.get("voice_mode", "brief")
        user_memories: str = node_context.get("user_memories", "")

        # Use shared building blocks
        identity: str = build_identity_header(room, user, voice_mode, user_memories)
        rules: str = build_rules_block()
        fallback: str = build_fallback_line()
        direct_answer_section: str = build_direct_answer_section(available_commands)
        agent_context: str = build_agent_context_summary(node_context)

        tools_section: str = format_tools_for_prompt(
            tools, available_commands, primary_examples_only=True
        )

        return f"""{identity}

You are a function calling AI model. {ANTI_HALLUCINATION_MANDATE}

For each function call, return JSON within <tool_call></tool_call> tags:
<tool_call>
{{"name": "<function-name>", "arguments": {{"<arg>": "<value>"}}, "failure_message": "<fallback>"}}
</tool_call>

{rules}
{agent_context}
{fallback}
{direct_answer_section}
Tools:
{tools_section}
"""

    def get_response_format(self) -> Optional[Dict[str, Any]]:
        return {"type": "text"}

    def parse_response(self, raw_content: str) -> Optional[str]:
        """Transform <tool_call> tags into Jarvis JSON."""
        cleaned: str = raw_content.strip()

        matches = _TOOL_CALL_RE.findall(cleaned)
        if matches:
            calls: list[Dict[str, Any]] = []
            for match in matches:
                try:
                    calls.append(json.loads(match.strip()))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse tool_call: %s", match[:100])
            if calls:
                return json.dumps({
                    "message": "",
                    "tool_calls": calls,
                    "error": None,
                })

        # Plain text response
        if cleaned and not cleaned.startswith("{"):
            return json.dumps({
                "message": cleaned,
                "tool_calls": [],
                "error": None,
            })

        return None

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider_name": self.name,
            "model_family": "phi",
            "size_tier": "medium",
            "training_tier": "untrained",
            "use_tool_classifier": self.use_tool_classifier,
            "supports_native_tools": self.supports_native_tools,
        }
```

### Step 2: Activate It

Set the active provider to your new provider:

```sql
UPDATE settings SET value = 'Phi3MediumUntrained' WHERE key = 'llm.interface';
```

Or via environment variable:

```bash
export JARVIS_MODEL_INTERFACE=Phi3MediumUntrained
```

### Step 3: Test It

Restart the Command Center and send a voice command. Check the logs for:

```
PromptProviderFactory: found provider Phi3MediumUntrained (Phi3MediumUntrained)
Built Phi3MediumUntrained system prompt: 2341 chars, 15 tools
```

### Design Notes

- **Reuse shared building blocks.** The `core_rules.py`, `context_builders.py`, and `tool_formatters.py` modules handle 80% of prompt construction. Your provider mostly just assembles these pieces in the right order for your model.
- **Prompt prefix caching.** llama.cpp caches the KV state by prefix. Structure your prompt so that stable content (identity, rules) comes first and tool-dependent content (tool list) comes last. This maximizes KV cache reuse across requests.
- **Override `parse_response()`.** If your model outputs tool calls in a format that the default `ToolCallParser` does not understand, override `parse_response()` to transform the output into Jarvis JSON before it reaches the parser.
- **The `custom/` directories** exist for user-created variants that should not be overwritten by updates. Place experimental providers there.

## Source Files

| File | Description |
|------|-------------|
| `jarvis-command-center/app/core/interfaces/ijarvis_prompt_provider.py` | `IJarvisPromptProvider` ABC |
| `jarvis-command-center/app/core/prompt_provider_factory.py` | `PromptProviderFactory` (discovery + creation) |
| `jarvis-command-center/app/core/prompt_providers/shared/core_rules.py` | Shared rules, identity header, fallback |
| `jarvis-command-center/app/core/prompt_providers/shared/context_builders.py` | Agent context, room hierarchy, direct answers |
| `jarvis-command-center/app/core/prompt_providers/shared/tool_formatters.py` | Tool formatting for prompt text |
| `jarvis-command-center/app/core/prompt_providers/medium/untrained/qwen25_medium_untrained.py` | Reference implementation (active in production) |
