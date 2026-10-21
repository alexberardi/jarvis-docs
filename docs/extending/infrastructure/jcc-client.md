# Command Center Client

A package that needs the household's LLM, or needs to call the server, uses two helpers from the [Command SDK](../../libraries/command-sdk.md):

| Helper | What it does |
|--------|--------------|
| `llm_chat_text(prompt)` | Sends `prompt` to the server's LLM and returns its text reply (a `str`) |
| `cc_post(path, json)` | POSTs `json` to a server route as the node and returns the decoded JSON reply (a `dict`) |

Both are plain functions, never raise, and return `None` when there is no answer. The device the package runs on registers the backend behind them at startup, so a package never needs a URL, a key or an HTTP client.

## Where they work

| Device | `llm_chat_text` | `cc_post` |
|--------|-----------------|-----------|
| Pi with the Python node | Yes | Yes, any server route, authenticated as the node |
| Computer with the desktop agent | No: returns `None` | No: returns `None` |
| Pi with the Go voice node | Yes | Only `/api/v0/node/...` routes |

On a computer the desktop agent registers neither backend, so a command there gets the SDK's safe default (`None`). Write every caller with a fallback. See [Where your code runs](../where-code-runs.md).

## Ask the LLM

```python
from jarvis_command_sdk import llm_chat_text

text = llm_chat_text("Write one cheerful sentence about Monday mornings.")
if text is None:
    text = "Happy Monday."  # no LLM, or the call failed
```

The prompt goes to the server's live model as a single system message, at temperature 0 (`POST /api/v0/node/llm/chat`). The reply is plain text.

### Structured answers

There is no schema-aware variant. Ask for JSON in the prompt and parse it yourself, keeping a fallback for a reply that doesn't parse:

```python
import json

from jarvis_command_sdk import llm_chat_text


def parse_city(question: str) -> dict | None:
    reply = llm_chat_text(
        "Answer with JSON only, as {\"name\": str, \"country\": str}. "
        f"Question: {question}"
    )
    if reply is None:
        return None
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        return None
```

## Call the server

`cc_post` takes a path on the server and a JSON body. The routes made for packages are the node plugin API under `/api/v0/node/`, for example:

| Route | Body |
|-------|------|
| `/api/v0/node/push-notification` | `title`, `body`, optional `priority`, `category`, `user_id`, `dedupe_key` |
| `/api/v0/node/llm/chat` | What `llm_chat_text` uses |

```python
from jarvis_command_sdk import cc_post

resp = cc_post(
    "/api/v0/node/push-notification",
    {"title": "Laundry", "body": "The dryer is done.", "category": "reminder"},
)
if resp is None:
    pass  # no backend, or the request failed
```

For the inbox, timers and alerts, prefer the SDK's own helpers (`JarvisInbox`, `timer_set`, `alerts_pending` and the rest; see the [Command SDK](../../libraries/command-sdk.md)) over raw routes.

## Testing

In tests, and while Pantry validates a package, no backend is registered and both helpers return `None`. To test the success path, register a fake:

```python
from jarvis_command_sdk import LLMBackend, set_llm_backend


class FakeLLM(LLMBackend):
    def chat_text(self, prompt: str) -> str | None:
        return '{"name": "Paris", "country": "France"}'


set_llm_backend(FakeLLM())
# ... run the code under test ...
set_llm_backend(None)
```

`CCHttpBackend` and `set_cc_backend` do the same for `cc_post`.

## The node's own client

The Python node talks to the server through `JarvisCommandCenterClient` (`clients/jarvis_command_center_client.py` in `jarvis-node-setup`). It is node-internal: the voice pipeline (`send_command*`, `start_conversation`, tool results) and the backends above are built on it. It is not in the SDK, a computer doesn't have it, and its constructor needs the server URL from the node's service discovery. Packages use `llm_chat_text` and `cc_post` instead.

Some of its methods call routes jarvisd doesn't have, and return `None` there: `lightweight_chat` (`/api/v0/lightweight/chat`), `train_tool_router`, `train_node_adapter` and `get_adapter_job_status`. Tool-router and adapter training were cut from jarvisd.
