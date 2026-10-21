# Testing

## Test first

Every change starts with a failing test.

1. **Red:** write a test that describes the behaviour you want. Run it and see it fail.
2. **Green:** write the least code that makes it pass.
3. **Refactor:** tidy up while every test stays green.

In jarvis-server, run the one package you are working on while you iterate:

```bash
CGO_ENABLED=1 go test -race ./internal/modules/cc/ -run TestPantryGateRefusesWhenOff
```

## Running the tests (jarvis-server)

| Command | What it runs | When |
|---|---|---|
| `scripts/check` | gofmt on the changed Go files; `go vet` for Linux, macOS and Windows (contract files included); race tests of the changed packages; the admin web app's typecheck and vitest when `web/admin/` changed | Before every commit |
| `CGO_ENABLED=1 go test -race ./...` | The whole suite under the race detector | Before every commit |
| `scripts/check --all` | The same gate, race-testing every package | Before a large change |
| `scripts/contract.sh` | The contract suite against a running jarvisd | When a response's shape changes |
| `scripts/e2e web`, `scripts/e2e mobile` | The admin web app's Playwright tests and the mobile app's Maestro flows against sandboxes the script brings up | When you change an admin page or a mobile screen |

"Changed" in `scripts/check` means everything that differs from the merge base with `origin/main`, committed or not;
`--base REF` compares with another branch. Builds stay `CGO_ENABLED=0`; the race detector is the only reason tests use
cgo. A few packages need extra files: run `scripts/fetch-sherpa-libs.sh` once, and `scripts/fetch-test-models.sh` for
the voice integration tests (`JARVIS_SHERPA_MODELS=$PWD/.models`).

### The contract suite

`contract/` is a black-box suite in Go that speaks only HTTP and MQTT to a running server and freezes the wire
contracts: status codes, JSON keys and types, and the error details clients branch on. The same tests ran against the
old Python services, and a test only counts once it passed there; it is what proves that jarvisd answers the nodes and
the mobile app the way they expect.

```bash
cp .contract.env.example .contract.env   # the target host and credentials; never a production server
scripts/contract.sh -run 'TestAuth|TestConfig'
```

Every file has the `contract` build tag, so `go test ./...` skips the package; `scripts/check` still vets it. Details
are in jarvis-server's `docs/contract/README.md`.

### End-to-end tests

`scripts/e2e` brings up its own sandboxes (a seeded household with a scripted model, and an empty install for the
first-run setup), runs the suites and writes a report to `.e2e/<run>/report.md`. A new admin page or mobile screen needs
an entry in `e2e/coverage.json`, and CI fails without one. See jarvis-server's `docs/dev/e2e.md`.

### Conversations and the voice loop

To test what a voice user hears without a microphone, start a sandbox and talk to it as its seeded node:

```bash
scripts/sandbox up --name me
go run ./tools/pipeline say -v "turn on the kitchen lights"   # one conversation; -v prints each model call
go run ./tools/pipeline run --filter timers                    # replay the scenarios in tools/pipeline/scenarios/
```

Every model call (prompt, tools, reply) is logged to `.sandbox/<name>/llm.jsonl`. With `scripts/sandbox up --voice`,
`pipeline say --voice` speaks each turn, transcribes it as a node would and checks what was heard.

## CI (jarvis-server)

`.github/workflows/ci.yml` runs on every pull request and every push to `main`:

| Job | What it proves |
|---|---|
| `build` | `go vet` and a `CGO_ENABLED=0` build for linux/amd64, linux/arm64, darwin/arm64 and windows/amd64, then `CGO_ENABLED=1 go test -race ./...` |
| `admin` | The admin web app's lint, typecheck, tests and build |
| `native-voice` | The bundled speech libraries load and run real models on each OS |
| `agent` | The desktop agent's tests on Linux, macOS and Windows |
| `service` | jarvisd registers with each OS's service manager, serves `/health` and comes back after being killed |
| `upgrade`, `agent-upgrade` | Self-update end to end from fake signed releases, including a rollback |
| `install`, `install-from-app`, `deb`, `inno`, `macos-dmg` | The install scripts and the Linux, Windows and macOS installers, installed and removed for real |

Two lanes call real models and run on pushes to `main`, weekly and by hand, not on pull requests:

- `anthropic-live.yml`: a chat, a tool round trip and a streamed tool call against the Anthropic API (it warns and
  passes when the repository has no API key).
- `transformers-live.yml`: the Transformers engine with a small model, on the CPU.

!!! note "The old integration-test lanes"
    The lanes in `jarvis-integration-tests` (fast, behaviour and from-source) tested the old Docker services, and
    nothing in jarvis-server triggers them. They are described on the Legacy page
    [Integration Tests](../legacy/contributing/integration-tests.md).

## Python repositories

The Python voice node, the SDK, `jdt` and the Pantry test with `pytest`. CI runs it on pull requests in jarvis-node-setup,
jarvis-pantry and jarvis-command-sdk; for `jdt`, run it locally.

```bash
cd jarvis-node-setup        # or jarvis-pantry, jarvis-command-sdk, jarvis-developer-toolkit
pytest tests/test_new_feature.py -v
```

A command package is checked with [`jdt test`](../extending/toolkit/test.md) before it goes to the Pantry; see also
[Testing commands](../commands/testing.md).

### Acoustic tests for the Python node

To test the whole voice path with a real wake word and real audio, use `tools/acoustic_test/` in
[`jarvis-node-setup`](https://github.com/alexberardi/jarvis-node-setup). Home Assistant speaks `Hey Jarvis, <phrase>`
through a speaker placed near the node, and the tool reads the node's log to report, per phrase, the wake score,
transcript, route, reply and the time from the end of recording to the first audio. The audio is identical on every
run, so settings can be compared on the same phrases.

```bash
export HA_URL=http://homeassistant.local:8123 HA_TOKEN_FILE=~/.ha-token
export PLAYER_ENTITY=media_player.kitchen_speaker NODE_SSH=pi@jarvis-node.local

echo '["what time is it", {"utt": "did you feed the dog", "wake": ""}]' \
  | python -m tools.acoustic_test.run --out runs.jsonl --volume 0.3
python -m tools.acoustic_test.mic_level 0.15 0.35
```

- A phrase that should be answered is `answered`, `miss` (the wake model did not fire), `dropped` (woke, but judged not
  addressed to the node) or `error`.
- A phrase with `"wake": ""` is chatter that should **not** be answered: it is `ignored` when the node did not answer it
  and `false_answer` when it did.
- The speaker fetches the generated speech from Home Assistant Cloud's address by default; set `HA_MEDIA_BASE_URL` to an
  address the speaker can reach to keep it local. Log windows are corrected for clock skew between machines.
- Check the level first with `mic_level`: speech whose peak is at or below the room's noise floor is not heard by the wake
  model, and a loud speaker next to the microphone flatters every result.
- Identical audio can score very differently between runs (speaker start-up clipping, household noise), so use a few
  dozen phrases and compare settings across several runs.

## Voice latency

What matters most to a voice user is the time to the first spoken word. A turn is: wake word on the node, speech to
text, the command (the language model's tool loop, and any commands the node runs), and the spoken answer, streamed
while the rest is still being synthesised. [Voice pipeline](../architecture/voice-pipeline.md) describes each step and
what keeps it fast.
