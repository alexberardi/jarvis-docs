# Alert System

Alerts are time-sensitive notifications produced by [agents](index.md). An agent returns them from `get_alerts()`, and the node keeps them in an in-memory queue until they are announced, read out on request or expire.

## The Alert dataclass

From the SDK (`jarvis_command_sdk/agent.py`); import it with `from jarvis_command_sdk import Alert`. The node's `core/alert.py` re-exports the same class.

```python
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class Alert:
    source_agent: str                  # name of the agent that created it
    title: str                         # short title (also the queue's dedup key)
    summary: str                       # what is read aloud or shown
    priority: int = 2                  # 1=low, 2=medium, 3=high
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dedupe_key: str | None = None      # stable identity across runs
    category: str = "general"          # groups alerts for routing preferences
    target_user_id: str | None = None  # one household member, or None for everyone

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
```

`to_dict()` returns every field, with the datetimes as ISO strings.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `source_agent` | `str` | The `name` of the agent that produced the alert. |
| `title` | `str` | Short identifier. The node's queue also uses it to **deduplicate** (case-insensitive). |
| `summary` | `str` | The text that is read aloud or displayed. |
| `priority` | `int` | **1** = low, **2** = medium (default), **3** = high. Priority 3 is announced aloud; see below. |
| `created_at` | `datetime` | Defaults to now (UTC). |
| `expires_at` | `datetime` | Defaults to an hour from now. After it, the alert is dropped from the queue. |
| `id` | `str` | A fresh UUID per instance, so it can't identify a re-emitted alert. |
| `dedupe_key` | `str` or `None` | A stable identity, such as an article ID or `"storm:2026-07-18"`, so queues and the server can suppress repeats across runs. |
| `category` | `str` | Groups alerts for per-source routing preferences. Default `"general"`. |
| `target_user_id` | `str` or `None` | Address one household member; `None` for the whole household. |

Only the first three fields are required:

```python
from jarvis_command_sdk import Alert

alert = Alert(source_agent="calendar", title="Meeting soon", summary="Standup starts in 5 minutes", priority=3)
```

### Priority levels

| Priority | Value | Use for | Example |
|----------|-------|---------|---------|
| Low | 1 | Informational, no urgency | "Package delivered" |
| Medium | 2 | Worth mentioning when asked | "Market update" |
| High | 3 | Needs attention now; spoken without being asked | "Meeting starts in 5 minutes", "Disk almost full" |

### Expiration (TTL)

Choose `expires_at` by how long the information stays actionable:

| Agent type | Suggested TTL | Reasoning |
|------------|---------------|-----------|
| Calendar alerts | 5--15 minutes | The event is imminent; stale once it starts |
| News alerts | 1--2 hours | Short relevance window |
| Email alerts | 30--60 minutes | The user likely checks email within this window |
| System alerts | 5--10 minutes | Transient conditions resolve or escalate |

## How alerts reach the user

On the Python node:

- **Priority 3 and up** (`ALERT_ANNOUNCE_PRIORITY = 3`) is **announced**: during a quiet moment in the wake loop the node speaks the alert, listens briefly for a snooze or dismiss reply, and removes the alerts it spoke. While any such alert is queued, the node's **LED** shows the alert pattern.
- **Priority 1 and 2** stay **quiet** in the queue: no announcement, no LED. The user hears them by saying "what's up" or by a short press of the node's button, which reads out everything pending and clears the queue.

Expired alerts disappear on their own.

## AlertQueueService

The node's `AlertQueueService` (`jarvis-node-setup/services/alert_queue_service.py`) is a thread-safe in-memory queue between the agents (on the scheduler thread) and the voice loop. It is node-internal: an agent only returns alerts from `get_alerts()`, and a command reads the queue with the SDK's `alerts_pending()`, `alerts_flush()`, `alerts_remove()` and `alerts_count()`.

```
Scheduler thread                        Wake loop / button / "what's up"
────────────────                        ────────────────────────────────
Agent.run()                             announce priority >= 3 (quiet moments)
  │                                     read out and flush (button, "what's up")
  ▼                                       ▲
Agent.get_alerts()                        │
  │                                       │
  ▼                                       │
alert_queue.add_alert(alert) ──► [ thread-safe queue: dedup by title, max 50, TTL ]
```

### Behaviour

**Thread safety:** every operation holds a `threading.Lock`.

**Deduplication by title:** `add_alert()` compares titles case-insensitively. A duplicate with the **same or lower** priority is dropped; one with a **higher** priority replaces the queued alert, so it can be announced.

**Expired alerts are refused:** `add_alert()` rejects an alert that has already expired, and every read or write sweeps expired ones out.

**Capacity (50 alerts):** when an add takes the queue over 50, it sorts by `(priority, -created_at)` and keeps the last 50. That evicts the lowest priority first, and within that priority the **newest** alerts (not the oldest, as the code's own comment says).

**Change callback:** `on_change` is called after every operation with the count of *announceable* alerts (priority 3 and up). The node uses it to drive the LED.

### API

```python
class AlertQueueService:
    on_change: Optional[Callable[[int], None]]  # called with the announceable count

    def add_alert(self, alert: Alert) -> None: ...
    def get_pending(self) -> List[Alert]: ...    # sorted by priority desc, then created_at
    def flush(self) -> List[Alert]: ...          # pending alerts, and clear the queue
    def remove_ids(self, alert_ids) -> int: ...
    def count(self) -> int: ...
    def sweep_expired(self) -> int: ...
```

`get_alert_queue_service()` returns the node's single instance. At startup the node creates the queue, wires the LED to `on_change` and the button to read-out-and-flush, then starts the agent scheduler and hands it the queue with `set_alert_queue()`. From then on the scheduler adds each agent's `get_alerts()` after every run.

## Building an alert-only agent

An alert-only agent sets `include_in_context = False`, returns an empty dict from `get_context_data()`, and builds its alerts in `run()`:

```python
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from jarvis_command_sdk import AgentSchedule, Alert, IJarvisAgent, IJarvisSecret


class ExampleAlertAgent(IJarvisAgent):
    def __init__(self) -> None:
        self._alerts: List[Alert] = []

    @property
    def name(self) -> str:
        return "example_alert"

    @property
    def description(self) -> str:
        return "Example alert-only agent"

    @property
    def schedule(self) -> AgentSchedule:
        return AgentSchedule(interval_seconds=300, run_on_startup=False)

    @property
    def required_secrets(self) -> List[IJarvisSecret]:
        return []

    @property
    def include_in_context(self) -> bool:
        return False

    async def run(self) -> None:
        self._alerts = []
        something_happened = True  # check your external source here
        if something_happened:
            self._alerts.append(Alert(
                source_agent=self.name,
                title="Something happened",
                summary="Details about what happened",
                priority=2,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            ))

    def get_context_data(self) -> Dict[str, Any]:
        return {}

    def get_alerts(self) -> List[Alert]:
        return self._alerts
```

## Best practices

1. **Set an appropriate TTL.** Too short and the alert is missed; too long and it clutters the queue.
2. **Use priority 3 sparingly.** It is spoken aloud without being asked. If everything is high priority, nothing is.
3. **Keep titles stable.** The node's queue deduplicates by title: use "Low disk space", not "Low disk space (8%)", or every change makes a new alert. Set `dedupe_key` too.
4. **Keep `get_alerts()` fast.** Build the alerts in `run()` and just return them.
5. **Don't raise from `get_alerts()`.** The scheduler catches it, but you lose that run's alerts.

## Source files

| File | Description |
|------|-------------|
| `jarvis-command-sdk/jarvis_command_sdk/agent.py` | `Alert` dataclass |
| `jarvis-node-setup/services/alert_queue_service.py` | `AlertQueueService` |
| `jarvis-node-setup/core/alert_announcer.py` | Speaks priority-3 alerts |
| `jarvis-node-setup/services/agent_scheduler_service.py` | Collects `get_alerts()` after each run |
