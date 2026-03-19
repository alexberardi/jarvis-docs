# Alert System

Alerts are time-sensitive notifications produced by [agents](index.md). While context agents inject data into the system prompt for every voice request, alert agents push discrete notifications into an in-memory queue that the voice thread can flush at appropriate moments.

## The Alert Dataclass

Defined in `jarvis-node-setup/core/alert.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class Alert:
    source_agent: str       # Name of the agent that created this alert
    title: str              # Short title (also used for deduplication)
    summary: str            # Longer description for display/voice
    created_at: datetime    # When the alert was created (UTC)
    expires_at: datetime    # When the alert should be discarded (UTC)
    priority: int = 2       # 1=low, 2=medium, 3=high
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_agent": self.source_agent,
            "title": self.title,
            "summary": self.summary,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `source_agent` | `str` | The `name` of the agent that produced this alert. Used for log attribution. |
| `title` | `str` | Short identifier. Also used as the **deduplication key** --- alerts with the same title (case-insensitive) are considered duplicates. |
| `summary` | `str` | Detailed description. This is what gets read aloud or displayed to the user. |
| `created_at` | `datetime` | Creation timestamp in UTC. Used for ordering within the same priority level. |
| `expires_at` | `datetime` | Expiration timestamp in UTC. After this time, `is_expired` returns `True` and the alert is filtered out of pending lists. |
| `priority` | `int` | Priority level: **1** = low, **2** = medium (default), **3** = high. Higher priority alerts are returned first. |
| `id` | `str` | Auto-generated UUID. Unique identifier for this alert instance. |

### Priority Levels

| Priority | Value | Use For | Example |
|----------|-------|---------|---------|
| Low | 1 | Informational, no urgency | "Package delivered" |
| Medium | 2 | Worth mentioning soon | "Breaking news: market update" |
| High | 3 | Needs immediate attention | "Meeting starts in 5 minutes", "Memory at 95%" |

### Expiration (TTL)

Every alert has an `expires_at` timestamp. Once expired, the alert is filtered out of `get_pending()` and `flush()` results. Choose TTL based on how long the information remains actionable:

| Agent Type | Suggested TTL | Reasoning |
|------------|---------------|-----------|
| Calendar alerts | 5--15 minutes | Event is imminent; stale after it starts |
| News alerts | 1--2 hours | Breaking news has a short relevance window |
| Email alerts | 30--60 minutes | User likely checks email within this window |
| System alerts | 5--10 minutes | Transient conditions resolve or escalate |

## AlertQueueService

The `AlertQueueService` is a thread-safe in-memory queue that sits between agents (which produce alerts on the scheduler thread) and the voice thread (which consumes them). Defined in `jarvis-node-setup/services/alert_queue_service.py`.

### Architecture

```
Scheduler Thread                          Voice Thread
─────────────────                         ────────────
Agent.run()                               Voice request arrives
  │                                         │
  ▼                                         ▼
Agent.get_alerts()                        alert_queue.flush()
  │                                         │
  ▼                                         ▼
alert_queue.add_alert(alert)              Returns pending alerts
  │                                       Clears the queue
  ▼                                         │
  [───── Thread-safe queue ─────]           ▼
  [  dedup by title             ]         Alerts injected into
  [  max 50 alerts              ]         voice response
  [  TTL expiration             ]
```

### Key Features

**Thread safety:** All operations are protected by a `threading.Lock`. The scheduler thread adds alerts and the voice thread reads/flushes them without races.

**Deduplication by title:** When `add_alert()` is called, it checks existing alerts for a case-insensitive title match. If a duplicate is found, the new alert is silently dropped. This prevents repeated agent runs from flooding the queue with identical alerts.

**Maximum capacity (50 alerts):** If the queue exceeds 50 alerts after an add, it drops the lowest-priority, oldest alerts first. The eviction sort key is `(priority, -created_at)` --- low priority gets evicted before high priority, and within the same priority, older alerts are evicted first.

**TTL expiration:** `get_pending()` and `flush()` automatically filter out expired alerts. You do not need to manually clean up stale alerts.

**Change callback:** The optional `on_change` callback fires whenever the pending alert count changes (after `add_alert` or `flush`). This can be used to trigger UI updates or LED indicators on the node.

### API

```python
class AlertQueueService:
    on_change: Optional[Callable[[int], None]]  # Called with pending count

    def add_alert(self, alert: Alert) -> None:
        """Add alert. Dedup by title, cap at 50."""

    def get_pending(self) -> List[Alert]:
        """Return non-expired alerts sorted by priority desc, then created_at."""

    def flush(self) -> List[Alert]:
        """Return pending alerts and clear the queue."""

    def count(self) -> int:
        """Count non-expired alerts."""
```

### Usage

```python
from services.alert_queue_service import get_alert_queue_service

queue = get_alert_queue_service()

# Check if there are pending alerts
if queue.count() > 0:
    alerts = queue.flush()  # Get and clear
    for alert in alerts:
        print(f"[{alert.priority}] {alert.title}: {alert.summary}")
```

### Singleton Access

The service uses a module-level singleton pattern:

```python
from services.alert_queue_service import get_alert_queue_service

queue = get_alert_queue_service()  # Always returns the same instance
```

### Wiring to the Scheduler

The `AgentSchedulerService` needs to know about the alert queue so it can forward alerts after each agent run. This is wired during initialization:

```python
from services.agent_scheduler_service import get_agent_scheduler_service
from services.alert_queue_service import get_alert_queue_service

scheduler = get_agent_scheduler_service()
alert_queue = get_alert_queue_service()
scheduler.set_alert_queue(alert_queue)
scheduler.start()
```

After this, every time an agent's `run()` completes, the scheduler calls `agent.get_alerts()` and adds each alert to the queue.

## Building an Alert-Only Agent

Alert-only agents set `include_in_context = False` and return an empty dict from `get_context_data()`. Their only output is `Alert` objects.

```python
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from core.alert import Alert
from core.ijarvis_agent import AgentSchedule, IJarvisAgent
from core.ijarvis_secret import IJarvisSecret


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
        return False  # Do not inject into system prompt

    async def run(self) -> None:
        self._alerts = []
        # ... check external source ...
        if some_condition:
            self._alerts.append(Alert(
                source_agent=self.name,
                title="Something happened",
                summary="Details about what happened",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                priority=2,
            ))

    def get_context_data(self) -> Dict[str, Any]:
        return {}  # No context data

    def get_alerts(self) -> List[Alert]:
        return self._alerts
```

## Best Practices

1. **Set appropriate TTL.** An alert that expires too soon might be missed; one that never expires clutters the queue. Match TTL to the actionability window of the information.

2. **Use priority levels correctly.** Reserve priority 3 for things that genuinely need immediate attention. If everything is high priority, nothing is.

3. **Deduplicate with title matching.** The queue deduplicates by title, so use consistent titles for the same type of alert. For example, always use "High memory usage" rather than "High memory usage (93%)" --- otherwise each percentage change creates a new alert.

4. **Keep `get_alerts()` fast.** Build alert objects during `run()` and store them. The `get_alerts()` method should just return the pre-built list, not compute anything.

5. **Do not raise exceptions from `get_alerts()`.** The scheduler wraps alert collection in a try/except, but returning a clean list is better than relying on error handling.

## Source Files

| File | Description |
|------|-------------|
| `jarvis-node-setup/core/alert.py` | `Alert` dataclass |
| `jarvis-node-setup/services/alert_queue_service.py` | `AlertQueueService` implementation |
| `jarvis-node-setup/services/agent_scheduler_service.py` | Scheduler integration (calls `get_alerts()` after each run) |
