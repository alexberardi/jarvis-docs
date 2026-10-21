# Contributing

Jarvis Automation is open source and welcomes contributions. The server, `jarvisd`, is one Go binary in
[`jarvis-server`](https://github.com/alexberardi/jarvis-server); most contributions land there. This section covers how
it is built, tested and reviewed, with short pointers for the Python repos.

## The repositories

| Repository | What it is | Language |
|---|---|---|
| [`jarvis-server`](https://github.com/alexberardi/jarvis-server) | `jarvisd` (the server, with the admin web app) and `jarvis-agent` (the desktop agent and the Go voice node) | Go, TypeScript for `web/admin/` |
| [`jarvis-node-setup`](https://github.com/alexberardi/jarvis-node-setup) | The Python voice node and the built-in node commands | Python |
| [`jarvis-command-sdk`](https://github.com/alexberardi/jarvis-command-sdk) | The [Command SDK](../libraries/command-sdk.md): the interfaces a package implements | Python |
| [`jarvis-developer-toolkit`](https://github.com/alexberardi/jarvis-developer-toolkit) | [`jdt`](../extending/toolkit/index.md): scaffold, test and deploy a package | Python |
| [`jarvis-pantry`](https://github.com/alexberardi/jarvis-pantry) | The [Pantry](../pantry/index.md) package store's API | Python |
| [`jarvis-node-mobile`](https://github.com/alexberardi/jarvis-node-mobile) | The mobile app | TypeScript (React Native) |

Every repository has its own `CLAUDE.md` and `README.md`. Read them before you work in it: they hold the setup, the
rules and the test commands for that repository.

## Getting started on jarvisd

1. Read jarvis-server's `CLAUDE.md`, then `docs/STATUS.md`: where the project is and what is next. Design notes are in
   its `docs/` (the README's **Documentation** table lists them); a design choice gets its own file in
   `docs/decisions/`.
2. Follow the [Coding Standards](coding-standards.md).
3. Write the test first, as described in [Testing](testing.md).

## Build and run

You need Go 1.27 (jarvis-server uses `mise exec go@1.27 -- go …`) and, for the admin web app, Node.

```bash
git clone https://github.com/alexberardi/jarvis-server
cd jarvis-server
scripts/fetch-sherpa-libs.sh                      # once: the native speech libraries
make jarvisd                                      # with the admin web app (needs Node), or:
CGO_ENABLED=0 go build -o jarvisd ./cmd/jarvisd   # without it (a placeholder page)

CGO_ENABLED=1 go test -race ./...                 # the whole test suite
scripts/check                                     # the pre-commit gate
```

Builds never use cgo; only the race detector needs it, so tests run with `CGO_ENABLED=1`.

To run your build:

- **`scripts/sandbox up --name <you>`** starts a seeded jarvisd for your checkout on its own ports and data, seeded with
  demo data (`--profile minimal|rich|empty`). `scripts/sandbox up --llm scripted` answers from scripted model replies, so it needs no
  model at all. Stop it with `scripts/sandbox down --name <you> --purge`.
- **`scripts/dev-run.sh`** runs your build in place of an installed jarvisd, on that install's data, and starts the
  installed service again when you press Ctrl-C. Without an installed service it runs on `~/.jarvisd`; `--home DIR` runs
  a fresh instance in `DIR`.

To install a released build instead, see [Install](../install/index.md).

## Key principles

- **Ask early.** A question in the issue costs less than a pull request in the wrong direction.
- **Test first.** Write a failing test, make it pass, then tidy up.
- **Keep the change small.** One pull request does one thing, and its description says what was tested and what was
  not.
- **New server work is a module change, not a service.** jarvisd has no separate services: a feature lives in a module
  under `internal/modules/` (with its own goose migrations), and anything configurable is a setting. See
  [Coding Standards](coding-standards.md#adding-to-a-module).

## Where to start

- **New command:** a command normally ships as a [Pantry](../pantry/index.md) package, written in Python against the
  [Command SDK](../libraries/command-sdk.md) and built with [`jdt`](../extending/toolkit/index.md). See
  [Building Commands](../commands/index.md). Tools that run inside the server itself are Go, in `internal/modules/cc`.
- **Server feature or setting:** a module change in jarvis-server; see
  [Coding Standards](coding-standards.md#adding-to-a-module).
- **Bug fix:** write a test that fails on the bug, then fix it.
- **Documentation:** this site is [`jarvis-docs`](https://github.com/alexberardi/jarvis-docs); jarvisd's design notes
  are in jarvis-server's `docs/`.

## Pull requests

Work on a topic branch and open a pull request against `main`. Run the gate first (`scripts/check` and
`CGO_ENABLED=1 go test -race ./...` in jarvis-server; each Python repo's own checks, see
[Coding Standards](coding-standards.md#python-repositories)). CI runs on every pull request, and pull requests are
squash-merged.

## Further reading

- [Coding Standards](coding-standards.md): Go and Python rules, logging, adding to a module
- [Testing](testing.md): the test suites, the contract suite, the harness and CI
