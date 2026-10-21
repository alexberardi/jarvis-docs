# Coding Standards

## Working style

**Be a scalpel, not a hammer.**

- Ask questions early when stuck or uncertain, rather than repeatedly trying the same approach.
- If something fails two or three times, step back and re-evaluate.
- Precision over persistence: one well-aimed question beats five failed attempts.

## Languages

| Where | Language | Notes |
|---|---|---|
| `jarvis-server` (jarvisd, jarvis-agent) | **Go 1.27** (`go.mod`: `go 1.27.1`) | Built with `CGO_ENABLED=0` always. Native libraries (sherpa-onnx, onnxruntime) are loaded at run time through purego, not linked. |
| `jarvis-server/web/admin` | TypeScript (React) | The admin web app, embedded in the binary by `make jarvisd`. Its own rules are in `web/admin/CLAUDE.md`. |
| `jarvis-node-setup` | Python 3.10+ | The Python voice node and its commands |
| `jarvis-pantry` | Python 3.11+ | The Pantry API |
| `jarvis-command-sdk`, `jarvis-developer-toolkit` | Python | Packages and `jdt` |
| `jarvis-node-mobile` | TypeScript (React Native) | The mobile app |

## Go (jarvis-server)

- **Format and vet.** Code is `gofmt`-formatted and passes `go vet` for Linux, macOS and Windows. `scripts/check` runs
  both, so a build break on another OS shows up before CI.
- **No cgo in builds.** `CGO_ENABLED=0` for every build. Only the race detector needs cgo, so tests run with
  `CGO_ENABLED=1 go test -race`.
- **Errors** are returned, not logged and swallowed. Add context when you pass one up
  (`fmt.Errorf("load node %s: %w", id, err)`) so callers can still match it with `errors.Is` and `errors.As`.
- **Logging** uses the standard library's `log/slog`. jarvisd sets up the logger once
  (`internal/platform/logging`): records go to stderr and, in batches, into the built-in logs module, which the admin
  web app's **Logs** page reads. Take the `*slog.Logger` your module is given, and log with key-value pairs:

  ```go
  m.log.Info("node paired", "node_id", nodeID, "household_id", hh)
  m.log.Error("tool call failed", "tool", name, "err", err)
  ```

  There is no `print`-style logging and no separate log service.
- **Read the design first.** Behaviour that the old Python services had is specified in jarvis-server's `docs/`
  (for example `docs/cc/` for the command center), and parity with it is proven by the contract suite (see
  [Testing](testing.md#the-contract-suite)), not by reading the old code. Don't port what the plan's cut lists drop.

## Adding to a module

jarvisd is one process made of modules under `internal/modules/` (`auth`, `cc`, `llm`, `stt`, `tts`, `logs`,
`notifications`, `recipes` and others). Each implements the `Module` interface in `internal/platform/module`. New server
work goes into a module; there are no new services. A change usually touches some of these:

1. **A migration** when it needs a table or column: a goose SQL file in
   `internal/modules/<module>/migrations/<NNNNN>_<what>.sql`, numbered above the module's highest, with a real
   `-- +goose Down`. Tables carry the module's prefix (`cc_`, `auth_`, …) because every module shares one SQLite file.
   Migrations are embedded in the binary and run when `jarvisd serve` starts; `jarvisd migrate status` shows them.
   Keep them additive within a release series (new tables, nullable columns or columns with defaults): a drop or rename
   breaks rolling back to the previous release.
2. **A setting** when behaviour should be configurable: a `settings.Definition` (from `internal/platform/settings`)
   next to the code that reads it, registered with the module's definitions. Give it a dotted, lowercase key prefixed by
   its area (`pantry.enabled`, `cc.compaction.threshold`), a type, a default and a description (the admin web app shows
   it). Declare only keys that code reads, and use `EnvFallback` only for secrets and URLs. A read cascades from the
   most specific scope (user, node, household) to the system value, then the env fallback, then the default.
3. **An access tier** for every new `/api` route on the admin gateway: who may call it (superuser, any signed-in user,
   or open) is recorded in `internal/modules/admin/tiers.go`. `TestEveryAPIRouteHasATier` fails on a route nobody
   classified, and the tier tests check each route as an anonymous caller, a member, a power user, a household admin,
   a superuser and another household's member. A change to the access rules, or a route below `superuser`, is reviewed
   by the maintainer before it merges.
4. **Tests** in the module's own `_test.go` files, and the contract suite when a response's shape changes.
5. **Docs**: the subsystem's design note in jarvis-server's `docs/`, and a file in `docs/decisions/` for a design
   choice a later reader would otherwise have to rediscover.

## Python repositories

The Python voice node, the SDK, `jdt` and the Pantry keep their Python conventions. Each repository's `CLAUDE.md` has
the details; the shared rules:

- **Imports** at the top of the file, grouped standard library, third-party, local.
- **Type hints** on every function's parameters and return value; prefer `X | None` over `Optional[X]`.
- **Exceptions:** never a bare `except:`; catch specific types and keep the exception (`except httpx.HTTPError as e`).
- **Lint:** `ruff`, configured in each repository's `pyproject.toml` (`line-length = 79` in jarvis-node-setup,
  `line-length = 132` in jarvis-pantry).
- **Tests:** `pytest`, written first. See [Testing](testing.md#python-repositories).

### Logging in the Python node

The Python node (jarvis-node-setup) still logs through `jarvis-log-client`, which sends its records to the server.
No `print()` in production code; CLI scripts and tests are the exception.

```python
from jarvis_log_client import JarvisLogger

logger = JarvisLogger("my-command")
logger.info("Processing command", extra={"command": command_name})
```

## Before you commit

| Repository | Gate |
|---|---|
| `jarvis-server` | `scripts/check` (gofmt and `go vet` for three OSes on what changed, race tests of the changed packages, the admin web app's typecheck and tests when `web/admin/` changed), then `CGO_ENABLED=1 go test -race ./...` |
| Python repositories | `ruff check .` and `pytest` in that repository |

See [Testing](testing.md) for the suites behind these.
