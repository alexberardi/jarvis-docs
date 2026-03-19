# Agent Scheduling

The `AgentSchedulerService` is responsible for running [agents](index.md) on their configured schedules, caching their context data, and forwarding their [alerts](alerts.md) to the alert queue. It runs in a dedicated daemon thread with its own asyncio event loop, keeping agent execution off the main thread.

## AgentSchedule Dataclass

Every agent declares its schedule via the `schedule` property, which returns an `AgentSchedule`:

```python
from dataclasses import dataclass


@dataclass
class AgentSchedule:
    interval_seconds: int       # Minimum interval between runs
    run_on_startup: bool = True # Whether to run immediately when scheduler starts
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `interval_seconds` | `int` | (required) | Minimum seconds between runs. The scheduler checks every 10 seconds, so effective granularity is ~10 seconds. |
| `run_on_startup` | `bool` | `True` | If `True`, the agent runs immediately when the scheduler starts, before the periodic loop begins. |

### Choosing an Interval

| Agent Type | Suggested Interval | Reasoning |
|------------|-------------------|-----------|
| Device state (Home Assistant) | 300s (5 min) | Devices change infrequently; 5 minutes balances freshness vs API load |
| Calendar events | 300s (5 min) | Events are relatively static; 5 minutes catches new/changed events |
| News/RSS feeds | 1800s (30 min) | RSS feeds update slowly; frequent polling wastes resources |
| Email checking | 300s (5 min) | Matches typical IMAP push notification latency |
| Token refresh | 3300s (55 min) | Refresh 5 minutes before a 60-minute token expires |
| System monitoring | 60s (1 min) | System stats change quickly; 1 minute gives reasonable resolution |

## Scheduler Architecture

```
┌─────────────────────────────────────────────────┐
│  Main Thread                                     │
│                                                   │
│  main.py startup                                  │
│    │                                              │
│    ├── initialize_agent_scheduler()               │
│    │     │                                        │
│    │     ├── AgentDiscoveryService.get_all_agents()│
│    │     │     → {name: agent, ...}               │
│    │     │                                        │
│    │     └── scheduler.start()                    │
│    │           │                                  │
│    │           └── Creates daemon thread ─────────┼──┐
│    │                                              │  │
│    ▼                                              │  │
│  Voice loop (reads context via                    │  │
│  get_aggregated_context())                        │  │
│                                                   │  │
└───────────────────────────────────────────────────┘  │
                                                       │
┌───────────────────────────────────────────────────┐  │
│  Scheduler Daemon Thread                          │◄─┘
│                                                   │
│  asyncio event loop                               │
│    │                                              │
│    ├── _run_startup_agents()                      │
│    │     └── asyncio.gather(agent1.run(),         │
│    │                        agent2.run(), ...)    │
│    │                                              │
│    └── _scheduler_loop() [every 10s]              │
│          │                                        │
│          ├── For each agent:                      │
│          │   if (now - last_run) >= interval:     │
│          │     await agent.run()                  │
│          │     cache context_data (with lock)     │
│          │     collect alerts → AlertQueueService │
│          │                                        │
│          └── Wait 10s or stop signal              │
│                                                   │
└───────────────────────────────────────────────────┘
```

### Key Design Decisions

**Dedicated daemon thread with asyncio loop.** The scheduler creates a new `asyncio.AbstractEventLoop` in a daemon thread. This allows agents to use `async/await` for network I/O without blocking the main thread. The daemon flag ensures the thread dies when the main process exits.

**10-second check interval.** The scheduler does not use per-agent timers. Instead, it wakes up every 10 seconds and checks which agents are due based on `(now - last_run) >= interval_seconds`. This keeps the implementation simple and avoids timer drift issues.

**Startup agents run concurrently.** Agents with `run_on_startup=True` are executed concurrently via `asyncio.gather()` during startup. This means a slow agent (e.g., one that takes 5 seconds to fetch from an API) does not delay other startup agents.

**Thread-safe context access.** The `_context_cache` dict is protected by a `threading.Lock`. The scheduler thread writes to it after each agent run, and the main thread reads from it during voice requests via `get_aggregated_context()`.

## Startup Sequence

When `initialize_agent_scheduler()` is called during `main.py` startup:

1. **Agent discovery:** `AgentDiscoveryService.get_all_agents()` scans the `agents/` directory for `IJarvisAgent` implementations
2. **Secret validation:** Each agent's `validate_secrets()` is called; agents with missing secrets are logged and skipped
3. **Thread creation:** A daemon thread is created with a new asyncio event loop
4. **Startup agents:** All agents with `schedule.run_on_startup = True` run concurrently via `asyncio.gather()`
5. **Periodic loop:** The scheduler enters its 10-second check loop

```python
# In main.py
from services.agent_scheduler_service import initialize_agent_scheduler
from services.alert_queue_service import get_alert_queue_service

scheduler = initialize_agent_scheduler()
scheduler.set_alert_queue(get_alert_queue_service())
```

## Context Aggregation

After each successful agent run, the scheduler caches the agent's context data:

```python
# Inside _run_agent_safe():
if agent.include_in_context:
    context = agent.get_context_data()
    with self._context_lock:
        self._context_cache[agent.name] = context
```

The voice thread retrieves a snapshot of all cached context:

```python
def get_aggregated_context(self) -> Dict[str, Dict[str, Any]]:
    with self._context_lock:
        return self._context_cache.copy()
```

This returns a dict mapping agent names to their context data:

```python
{
    "home_assistant": {
        "light_controls": {...},
        "device_controls": {...},
        "floors": {...},
    },
    "system_monitor": {
        "cpu_percent": 23.5,
        "memory_percent": 67.2,
        ...
    },
}
```

The voice thread places this into `node_context["agents"]` before sending to the Command Center.

## Error Handling

The scheduler is designed to never crash from a single agent failure:

- **Agent exceptions are caught:** If `run()` raises an exception, the scheduler logs the error and caches an error state instead of context data:

    ```python
    self._context_cache[agent.name] = {
        "last_error": str(e),
        "error_time": "2026-03-17T12:00:00+00:00",
    }
    ```

- **Alert collection is wrapped:** If `get_alerts()` raises, the error is logged but does not affect the context cache or other agents.

- **The loop continues:** After an error, the scheduler continues checking and running other agents on their normal schedules. The failed agent will be retried on its next interval.

## Public API

### `start()`

Start the scheduler. Discovers agents, creates the daemon thread, and begins the scheduling loop. Idempotent --- calling `start()` when already running logs a warning and returns.

### `stop()`

Stop the scheduler gracefully. Signals the event loop to exit and waits up to 5 seconds for the daemon thread to finish.

### `run_agent_now(name: str) -> bool`

Trigger an immediate run of a specific agent, regardless of its schedule. Returns `True` if the agent was found and the run was scheduled, `False` otherwise. The run is asynchronous --- it is submitted to the event loop and executes when the loop is free.

```python
scheduler.run_agent_now("home_assistant")  # True
scheduler.run_agent_now("nonexistent")     # False
```

### `get_agent_status() -> Dict[str, Dict[str, Any]]`

Get status information for all registered agents:

```python
{
    "home_assistant": {
        "name": "home_assistant",
        "description": "Pre-fetches Home Assistant device states",
        "interval_seconds": 300,
        "last_run": "2026-03-17T12:00:00+00:00",
        "next_run": "2026-03-17T12:05:00+00:00",
        "include_in_context": True,
    },
    "token_refresh": {
        "name": "token_refresh",
        "description": "Refreshes OAuth tokens before expiry",
        "interval_seconds": 3300,
        "last_run": None,
        "next_run": "pending",
        "include_in_context": False,
    },
}
```

### `get_aggregated_context() -> Dict[str, Dict[str, Any]]`

Get a thread-safe snapshot of all cached agent context data. This is the primary interface for the voice thread.

### `set_alert_queue(queue: AlertQueueService) -> None`

Wire the alert queue so agent alerts are collected after each run. Must be called before `start()` if you want alert forwarding.

## Singleton Access

The scheduler uses a singleton pattern with two accessors:

```python
from services.agent_scheduler_service import (
    get_agent_scheduler_service,    # Get the singleton (lazy init)
    initialize_agent_scheduler,     # Get + start (call once at startup)
)
```

`get_agent_scheduler_service()` returns the singleton instance without starting it. `initialize_agent_scheduler()` returns the singleton and calls `start()`. Use the latter in `main.py` at startup; use the former everywhere else to access the running instance.

## Source Files

| File | Description |
|------|-------------|
| `jarvis-node-setup/services/agent_scheduler_service.py` | `AgentSchedulerService` implementation |
| `jarvis-node-setup/core/ijarvis_agent.py` | `AgentSchedule` dataclass, `IJarvisAgent` ABC |
| `jarvis-node-setup/services/alert_queue_service.py` | `AlertQueueService` (wired via `set_alert_queue`) |
| `jarvis-node-setup/utils/agent_discovery_service.py` | Agent discovery (used by scheduler at startup) |
