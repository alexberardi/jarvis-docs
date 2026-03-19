# Command Center Client

The `JarvisCommandCenterClient` is the primary HTTP client for communicating with the command center from node-side code. It is built on `RestClient`, which auto-injects `X-API-Key` authentication headers on every request using the node's registered credentials.

**Module:** `clients/jarvis_command_center_client.py`

## Quick Start

```python
from clients.jarvis_command_center_client import JarvisCommandCenterClient

client = JarvisCommandCenterClient()

# Simple text response from the LLM
answer = client.chat_text("What is the capital of France?")
# answer == "The capital of France is Paris."
```

## Structured LLM Parsing

The most common use case for commands is asking the LLM to parse unstructured text into a typed Pydantic model:

```python
from clients.jarvis_command_center_client import JarvisCommandCenterClient
from pydantic import BaseModel

class CityInfo(BaseModel):
    name: str
    country: str
    population: int | None = None

client = JarvisCommandCenterClient()
result = client.chat("What city is the Eiffel Tower in?", CityInfo)
# result.name == "Paris"
# result.country == "France"
```

This sends the message to the LLM along with the Pydantic model's JSON schema. The LLM response is parsed and validated automatically. If parsing fails, the method returns `None`.

## API Reference

### Voice Commands

These methods are used by the node's voice pipeline to send transcribed speech through the command center's tool-routing system.

#### `send_command(voice_command, conversation_id) -> Optional[ToolCallingResponse]`

Send a text command for tool routing. The command center parses the intent, selects the appropriate tool, and returns a `ToolCallingResponse` with the result.

```python
response = client.send_command(
    voice_command="What's the weather in Miami?",
    conversation_id="conv-abc-123"
)
if response:
    print(response.text_response)
```

#### `send_command_stream(voice_command, conversation_id, chunk_size) -> tuple`

Streaming variant that returns audio chunks for real-time playback. Used when the command center generates a TTS response directly.

```python
content_type, audio_stream = client.send_command_stream(
    voice_command="Tell me a joke",
    conversation_id="conv-abc-123",
    chunk_size=4096
)
```

#### `send_command_unified(voice_command, conversation_id) -> tuple[str, Any]`

Unified entry point that returns a tagged result. The first element indicates the response type:

- `("audio", (content_type, stream))` --- streaming audio response
- `("control", ToolCallingResponse)` --- structured control response (tool call, validation prompt, etc.)
- `("error", str)` --- error message

```python
tag, payload = client.send_command_unified(
    voice_command="Turn off the lights",
    conversation_id="conv-abc-123"
)

if tag == "audio":
    content_type, stream = payload
    # Play audio stream
elif tag == "control":
    response: ToolCallingResponse = payload
    # Handle tool response
elif tag == "error":
    error_msg: str = payload
    # Handle error
```

#### `send_tool_results(conversation_id, tool_results) -> Optional[ToolCallingResponse]`

Continue a multi-turn tool conversation by sending the results of executed tools back to the command center.

```python
response = client.send_tool_results(
    conversation_id="conv-abc-123",
    tool_results=[
        {"tool_name": "get_weather", "result": {"temp": 75, "condition": "sunny"}}
    ]
)
```

#### `send_validation_response(conversation_id, request, response) -> Optional[ToolCallingResponse]`

Answer a validation prompt from the command center. When a command needs user confirmation (e.g., "Did you mean Miami, FL or Miami, OH?"), this sends the user's choice back.

```python
response = client.send_validation_response(
    conversation_id="conv-abc-123",
    request=validation_request,
    response="Miami, FL"
)
```

#### `start_conversation(conversation_id, commands, date_context?, speaker_user_id?, agents?) -> bool`

Register a new conversation with the command center. This sends the list of available commands (tool definitions), optional date context, speaker identity, and agent definitions. Returns `True` on success.

```python
success = client.start_conversation(
    conversation_id="conv-abc-123",
    commands=command_definitions,
    date_context=date_ctx,
    speaker_user_id=42,
    agents=agent_definitions
)
```

### LLM Chat

These methods provide direct access to the LLM for use within command implementations.

#### `chat_text(message) -> Optional[str]`

Send a message and get a raw text response. Uses the primary (live) model.

```python
summary = client.chat_text("Summarize this in one sentence: " + long_text)
```

#### `chat(message, model: Type[T]) -> Optional[T]`

Send a message with a Pydantic model for structured parsing. The LLM response is validated against the model's schema. Returns `None` if parsing fails.

```python
from pydantic import BaseModel

class SentimentResult(BaseModel):
    sentiment: str  # "positive", "negative", "neutral"
    confidence: float

result = client.chat(
    "Analyze the sentiment: 'I love this product!'",
    SentimentResult
)
# result.sentiment == "positive"
# result.confidence == 0.95
```

#### `lightweight_chat(message, model: Type[T]) -> Optional[T]`

Same as `chat()` but uses the background model instead of the live model. Use this for non-latency-sensitive tasks where you want to avoid competing with the voice pipeline for the primary model.

```python
# Background parsing that doesn't block voice commands
parsed = client.lightweight_chat(
    "Extract the date from: 'Let's meet next Tuesday at 3pm'",
    DateExtraction
)
```

### Utilities

#### `get_date_context() -> Optional[DateContext]`

Fetch the current date and timezone context from the command center. Useful for commands that need to resolve relative dates ("tomorrow", "next week").

```python
ctx = client.get_date_context()
if ctx:
    print(ctx.current_date)    # "2026-03-17"
    print(ctx.timezone)        # "America/New_York"
    print(ctx.day_of_week)     # "Tuesday"
```

#### `train_tool_router(payload) -> Optional[dict]`

Submit a training payload to train the fastText tool-routing model. Used by admin scripts, not typically called from commands.

```python
result = client.train_tool_router({
    "training_data": [...],
    "model_params": {"epochs": 25}
})
```

#### `train_node_adapter(payload) -> Optional[dict]`

Queue a LoRA adapter training job for the LLM. Returns job metadata including the job ID for status polling.

```python
result = client.train_node_adapter({
    "base_model_id": ".models/Qwen2.5-7B-Instruct",
    "training_data": [...]
})
job_id = result["job_id"]
```

#### `get_adapter_job_status(job_id) -> Optional[dict]`

Poll the status of a LoRA adapter training job.

```python
status = client.get_adapter_job_status("job-abc-123")
# status == {"status": "completed", "metrics": {...}}
```

## Authentication

`JarvisCommandCenterClient` extends `RestClient`, which reads the node's credentials from the config file (`config.json` or `config-mac.json`) and injects the `X-API-Key` header on every request:

```
X-API-Key: <node_id>:<node_key>
```

You do not need to handle authentication manually. The client is ready to use immediately after construction.

## Error Handling

All methods return `None` (or `False` for `start_conversation`) on failure. Errors are logged via `JarvisLogger` but do not raise exceptions. This follows Jarvis's convention of graceful degradation --- a failed HTTP call should not crash the node.

```python
result = client.chat("Parse this", MyModel)
if result is None:
    # LLM call failed or response didn't match the model
    # Fall back to a default or return an error response
    return CommandResponse.error_response(
        error_details="Could not reach the command center"
    )
```
