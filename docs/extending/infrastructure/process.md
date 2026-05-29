# Process Introspection

`process_alive(pid, expected_comm=None)` checks whether a process exists at a given PID and optionally whether the binary at that PID matches a name you expect.

It is in `jarvis_command_sdk` because the naive PID-liveness check used by hand-rolled pidfile code (`os.kill(pid, 0)`) is unsafe across reboots: when the kernel recycles the PID, your daemon-keepalive logic can silently report the wrong process as "still running" and never re-spawn.

## When you need it

Use `process_alive` when your command, agent, or device protocol spawns a long-running background daemon and tracks it through a pidfile that survives the parent process. Typical patterns:

- A music or media bridge daemon (Spotify Connect, MPD, Snapcast)
- A pairing helper that holds open a Bluetooth or zeroconf advertisement
- Any subprocess started with `start_new_session=True` that you intend to keep alive across node restarts

If your daemon is bound to the lifetime of `jarvis-node` itself --- a `subprocess.Popen` held in an instance attribute and torn down when the service stops --- you do not need this helper. PID reuse only matters when the PID is read back from disk after the original process has gone.

## API

```python
from jarvis_command_sdk import process_alive

def process_alive(pid: int, expected_comm: str | None = None) -> bool: ...
```

| Parameter | Meaning |
|-----------|---------|
| `pid` | The PID to check, typically read from a pidfile your daemon writes. |
| `expected_comm` | Optional binary name (e.g. `"go-librespot"`). When set, also validates that the running binary at `pid` matches. Matched against the basename; Linux truncates `comm` to 15 characters, so longer binary names should be passed truncated. |

Returns `True` only if the PID is live **and**, when `expected_comm` is given, the binary at that PID matches. Returns `False` for a gone PID, or when comm validation is requested but fails.

The function reads `/proc/<pid>/comm` on Linux and falls back to `ps -p` on macOS. `PermissionError` from `os.kill` on a different-uid process is correctly treated as "process exists" rather than "process gone" --- `/proc/<pid>/comm` remains world-readable so comm validation still works across uids.

## Example: pidfile-tracked daemon

```python
from pathlib import Path
from jarvis_command_sdk import process_alive

PIDFILE = Path.home() / ".jarvis" / "my_daemon" / "my_daemon.pid"
BINARY = "my-daemon"


def _read_pid() -> int | None:
    try:
        return int(PIDFILE.read_text().strip())
    except (OSError, ValueError):
        return None


def ensure_running() -> int:
    """Return the live daemon PID, spawning if needed."""
    pid = _read_pid()
    if pid is not None and process_alive(pid, expected_comm=BINARY):
        return pid
    # PID is stale (gone, or recycled to another process). Spawn fresh.
    return _spawn_and_write_pidfile()
```

Without `expected_comm`, after a node reboot the daemon's previous PID is often reused by an unrelated process (in practice, frequently a thread of the parent Python service that comes up under the same uid), and `ensure_running` would never re-spawn the daemon. The comm gate closes that gap.

## Reference implementation

The Spotify command uses this in [`spotify_shared/go_librespot_manager.py`](https://github.com/jarvis-pantry/jarvis-cmd-spotify) (`_process_alive`) to gate every entry point into the `go-librespot` lifecycle --- `start`, `stop`, `status`, and `ensure_running_unpaused`. The same `spotify_keepalive` agent runs every 5 minutes and on startup, so the fast path is "PID is alive and is go-librespot --- do nothing." The slow path --- spawning a fresh daemon and overwriting the pidfile --- only runs when the comm check rejects the stale PID.
