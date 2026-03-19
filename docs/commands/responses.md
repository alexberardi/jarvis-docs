# Response Patterns

`CommandResponse` is the return type of every `run()` method. It carries the command's output data back through the pipeline to the command center, which uses it to generate a spoken response and update the mobile UI.

## CommandResponse Structure

```python
@dataclass
class CommandResponse:
    context_data: dict | None = None       # Raw data for the LLM to generate a spoken response
    success: bool = True                   # Whether the command succeeded
    error_details: str | None = None       # Error message (sets success=False automatically)
    wait_for_input: bool = True            # Whether to keep the conversation open
    clear_history: bool = False            # Clear conversation history before next turn
    metadata: dict | None = None           # Command-specific metadata
    actions: list[IJarvisButton] | None = None  # Interactive buttons
    is_chunked_response: bool = False      # Chunked response flag
    chunk_session_id: str | None = None    # Session ID for chunked responses
```

## Factory Methods

### `success_response()` -- Standard Success

The most common response. The conversation stays open for follow-up by default.

```python
return CommandResponse.success_response(
    context_data={
        "city": "Chicago",
        "temperature": 72,
        "description": "partly cloudy",
        "message": "It's 72 degrees and partly cloudy in Chicago",
    }
)
```

The LLM uses `context_data` to generate a natural spoken response. Include a `message` key as a hint for what to say, plus structured data for the mobile UI.

**Signature:**

```python
CommandResponse.success_response(
    context_data: dict | None = None,
    wait_for_input: bool = True,
    metadata: dict | None = None,
) -> CommandResponse
```

### `error_response()` -- Errors

Return when the command fails. The conversation closes by default.

```python
return CommandResponse.error_response(
    error_details="OpenWeather API key is not configured",
    context_data={"error": "missing_api_key"},
)
```

**Signature:**

```python
CommandResponse.error_response(
    error_details: str,
    context_data: dict | None = None,
    wait_for_input: bool = False,
) -> CommandResponse
```

**Tips:**

- `error_details` is a human-friendly message that the LLM uses to generate a spoken error
- Include `context_data` for debugging even in errors
- Set `wait_for_input=True` if the user can retry (e.g., "City not found, try a different one")

### `follow_up_response()` -- Expects More Input

Return when the command succeeds but expects the user to continue the conversation. Used by the calculator (for chained calculations), chat, and other interactive commands.

```python
return CommandResponse.follow_up_response(
    context_data={
        "result": 42,
        "calculation": "6 * 7 = 42",
        "message": "6 times 7 equals 42",
    }
)
```

The conversation stays open. The user can say "now multiply that by 2" and the command center will route the follow-up to the same command.

**Signature:**

```python
CommandResponse.follow_up_response(
    context_data: dict,
    metadata: dict | None = None,
) -> CommandResponse
```

### `final_response()` -- One-Shot, No Follow-Up

Return when the command is done and no follow-up is expected. The conversation ends.

```python
return CommandResponse.final_response(
    context_data={
        "message": "Timer set for 5 minutes",
        "timer_id": "abc123",
        "duration_seconds": 300,
    }
)
```

**Signature:**

```python
CommandResponse.final_response(
    context_data: dict | None = None,
    metadata: dict | None = None,
) -> CommandResponse
```

### `chunked_response()` -- Large Data

Return when the response is too large for a single message. The user can ask for more with follow-up commands like "continue" or "next page".

```python
return CommandResponse.chunked_response(
    session_id="news-session-abc123",
    context_data={
        "headlines": headlines[:5],
        "total": len(headlines),
        "message": f"Here are the top 5 of {len(headlines)} headlines. Say 'more' for the next batch.",
    }
)
```

**Signature:**

```python
CommandResponse.chunked_response(
    session_id: str,
    context_data: dict | None = None,
    metadata: dict | None = None,
) -> CommandResponse
```

The `session_id` is used to track the chunked session across turns. On the next turn, the command can use the session ID to resume from where it left off.

### `validation_error()` -- Parameter Validation Failures

Returned automatically by the `execute()` pipeline when `validate_call()` produces errors. You rarely call this directly -- it is generated for you.

```python
return CommandResponse.validation_error([
    ValidationResult(
        success=False,
        param_name="entity_id",
        command_name="control_device",
        message="Device 'light.nonexistent' not found",
        valid_values=["light.living_room", "light.kitchen", "light.bedroom"],
    ),
])
```

The command center receives this and can either:

- Retry with a corrected value from `valid_values`
- Ask the user to clarify

**Signature:**

```python
CommandResponse.validation_error(
    results: list[ValidationResult],
) -> CommandResponse
```

## Choosing the Right Response

| Scenario | Factory Method | `wait_for_input` |
|----------|---------------|------------------|
| Weather report | `success_response()` | `True` |
| Calculator result | `follow_up_response()` | `True` |
| Timer set | `final_response()` | `False` |
| Music playing | `success_response(wait_for_input=False)` | `False` |
| API error | `error_response()` | `False` |
| News with pagination | `chunked_response()` | `True` |
| Bad device name | `validation_error()` | `False` |
| Email sent | `final_response()` | `False` |
| Email draft preview | Response with `actions` | `True` |

## Interactive Actions with IJarvisButton

Attach buttons to a response for interactive flows. The mobile app renders these as tappable buttons.

```python
from core.ijarvis_button import IJarvisButton

return CommandResponse(
    context_data={
        "draft": {
            "to": "alice@example.com",
            "subject": "Meeting tomorrow",
            "body": "Hi Alice, are we still on for tomorrow?",
        },
        "message": "Here's your email draft to Alice. Send it or cancel?",
    },
    success=True,
    wait_for_input=True,
    actions=[
        IJarvisButton(
            button_text="Send",
            button_action="send_click",
            button_type="primary",
            button_icon="send",
        ),
        IJarvisButton(
            button_text="Cancel",
            button_action="cancel_click",
            button_type="destructive",
            button_icon="close",
        ),
    ],
)
```

### Button Types

| Type | Appearance | Use Case |
|------|------------|----------|
| `"primary"` | Highlighted / accent color | Main action (Send, Confirm) |
| `"secondary"` | Neutral | Alternative action (Edit, Save Draft) |
| `"destructive"` | Red / warning | Dangerous action (Delete, Cancel) |

### Button Icons

Use [MaterialCommunityIcons](https://pictogrammers.com/library/mdi/) names:

```python
IJarvisButton("Send", "send_click", "primary", button_icon="send")
IJarvisButton("Edit", "edit_click", "secondary", button_icon="pencil")
IJarvisButton("Delete", "delete_click", "destructive", button_icon="delete")
```

## Handling Button Actions

When the user taps a button, the command center calls your command's `handle_action()` method:

```python
def handle_action(self, action_name: str, context: dict) -> CommandResponse:
    if action_name == "send_click":
        draft = context.get("draft", {})
        self._send_email(
            to=draft["to"],
            subject=draft["subject"],
            body=draft["body"],
        )
        return CommandResponse.final_response(
            context_data={"message": "Email sent successfully."}
        )

    # The base class handles "cancel_click" automatically
    return super().handle_action(action_name, context)
```

The `context` dict contains the `context_data` from the original response. This is how you pass data from the preview to the action handler (e.g., the email draft).

### Default `cancel_click` Handler

The base class provides a default handler for `cancel_click`:

```python
# Built-in on JarvisCommandBase -- no need to implement
if action_name == "cancel_click":
    return CommandResponse.final_response(
        context_data={"cancelled": True, "message": "Cancelled."}
    )
```

## `context_data` Best Practices

`context_data` is the bridge between your command and the LLM's spoken response. The command center's LLM reads this data and generates natural language.

### Always include a `message` key

```python
context_data={
    "temperature": 72,
    "city": "Chicago",
    "message": "It's 72 degrees in Chicago",  # LLM uses this as a starting point
}
```

### Include structured data for the mobile UI

```python
context_data={
    "emails": [
        {"from": "alice@example.com", "subject": "Meeting", "snippet": "..."},
        {"from": "bob@example.com", "subject": "Lunch?", "snippet": "..."},
    ],
    "total": 5,
    "message": "You have 5 unread emails. The first is from Alice about Meeting.",
}
```

### Keep error context helpful

```python
# Good -- gives the LLM context to explain the problem
context_data={
    "ticker": "INVALID",
    "error": "not_found",
    "message": "I couldn't find a stock with ticker 'INVALID'",
}

# Bad -- no context
context_data=None
```

## The `metadata` Field

`metadata` is for command-internal data that should not influence the spoken response. It flows through the pipeline but is not shown to the LLM.

```python
return CommandResponse.success_response(
    context_data={"message": "Timer set for 5 minutes"},
    metadata={
        "timer_id": "internal-uuid",
        "created_at": "2025-01-01T12:00:00Z",
        "node_id": "abc123",
    },
)
```

## The `clear_history` Flag

Set `clear_history=True` to reset the conversation context before the next turn. Useful when a command fundamentally changes the conversation state:

```python
return CommandResponse(
    context_data={"message": "Starting a new conversation"},
    success=True,
    clear_history=True,
)
```
