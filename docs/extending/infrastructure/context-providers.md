# Context Providers

Context providers let a command expose typed, **read-only** queries that server-side planners (e.g. jarvis-command-center) can call **at plan time only** — never during a live phone call, since the callee on the other end of an active call is untrusted input. Provider logic and any credentials it needs stay node-side; only the query params and result cross the wire.

**SDK requirement:** `jarvis-command-sdk >= 0.6.0` (adds `context_operations`, `execute_context_operation`, `ContextOperation`, `ContextResult`). See [Command SDK: Context Providers](../../libraries/command-sdk.md#context-providers) for the type reference.

## Declaring an Operation

Override `context_operations` to advertise what a command supports, and `execute_context_operation` to answer queries:

```python
from jarvis_command_sdk import ContextOperation, ContextResult

AVAILABILITY = ContextOperation(
    name="availability",
    description="Free/busy windows in a date range",
    params_schema={
        "start": {"type": "string", "required": True, "description": "ISO date"},
        "end": {"type": "string", "required": True, "description": "ISO date"},
    },
)

class MyCommand(IJarvisCommand):
    @property
    def context_operations(self):
        return [AVAILABILITY]

    def execute_context_operation(self, operation, params):
        if operation != "availability":
            return ContextResult.failed(f"unknown op {operation}")
        ...
        return ContextResult(data={"free": [...], "busy": [...]})
```

`ContextResult.data` must be JSON-serialisable — it crosses MQTT to reach the requesting planner.

## Reference Implementation: `availability` (jarvis-cmd-calendar)

The built-in calendar command (`ReadCalendarCommand`) is the first real context provider, added to support auto-populating phone-call plans with the household's real free/busy time (see [Command Center: Phone Calls](../../services/command-center.md)).

**Operation:** `availability`

| Param | Type | Required | Notes |
|---|---|---|---|
| `start` | string | yes | ISO date `YYYY-MM-DD`, range start |
| `end` | string | yes | ISO date `YYYY-MM-DD`, range end (exclusive) |

**Response (`ContextResult.data`):**

```json
{
  "free": ["Mon 9am-12pm", "Thu 2-5pm"],
  "busy": ["Mon 12-1pm (Lunch with Sam)", "Mon 10am-Wed 12am (Vacation)"]
}
```

Rules to be aware of when consuming or extending this operation:

- Free/busy windows are computed only within **waking hours, fixed 09:00–20:00 local** (not configurable).
- Windows shorter than 30 minutes are not offered as "free".
- Overlapping events are merged before free/busy is computed.
- Multi-day or midnight-crossing spans name both days, e.g. `"Mon 10am-Wed 12am"`.
- Malformed events are silently skipped; an event missing `end_time` defaults to a 1-hour duration.

**Failure modes** — `execute_context_operation` returns `ContextResult.failed(...)` when:

- `operation` isn't `"availability"` (`"unsupported context operation '<op>'"`).
- `start`/`end` don't parse as `YYYY-MM-DD` (`"invalid date range: <exc>"`).
- There's no resolved speaker for the request, since calendar credentials are per-user (`"unknown speaker — no personal calendar"`).
- Calendar configuration (`CALENDAR_TYPE`, `CALENDAR_DEFAULT_NAME`, and provider-specific secrets such as `GOOGLE_ACCESS_TOKEN`/`GOOGLE_REFRESH_TOKEN` or `CALENDAR_USERNAME`/`CALENDAR_PASSWORD`) is missing or unsupported.

## How Planners Call This

Server-side planners don't call `execute_context_operation` directly — they go through the node's MQTT context-query handler (jarvis-node-setup) and a typed client (e.g. jarvis-command-center's `context_provider_client`). See [Command Center: Phone Calls](../../services/command-center.md) for the wire protocol and how the planner degrades gracefully when no provider is available.
