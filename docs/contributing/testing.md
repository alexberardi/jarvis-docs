# Testing

## TDD Workflow

Test-driven development is mandatory for all Jarvis code. Every feature starts with a failing test.

1. **RED** -- Write a test that defines the expected behavior. Run it and confirm it fails.
2. **GREEN** -- Write the minimum code to make the test pass.
3. **REFACTOR** -- Clean up the implementation while keeping all tests green.

```bash
# 1. Write the test in tests/test_new_feature.py
# 2. Run it (should fail)
pytest tests/test_new_feature.py -v

# 3. Implement the feature
# 4. Run again (should pass)
pytest tests/test_new_feature.py -v

# 5. Refactor, run again (should still pass)
```

## Running Tests

### Via the Jarvis CLI

The `./jarvis test` command handles virtual environment activation and test configuration for each service:

```bash
# Run tests for a specific service
./jarvis test jarvis-auth
./jarvis test jarvis-command-center

# Run tests for all services
./jarvis test --all
```

### Directly with pytest

Each Python service uses pytest. Activate the service's virtual environment first:

```bash
cd jarvis-auth
source .venv/bin/activate
pytest -v --tb=short
```

For the mobile app:

```bash
cd jarvis-node-mobile
npm test
npm run test:coverage
```

## Coverage Targets

- **Target: 80%+ coverage** for all services
- Current coverage by service:

| Service | Coverage |
|---------|----------|
| jarvis-config-service | 93% |
| jarvis-tts | 98% |
| jarvis-notifications | 77% |
| jarvis-auth | Good |
| jarvis-command-center | Good |

Use `--cov` to check coverage:

```bash
pytest -v --tb=short --cov=app --cov-report=term-missing
```

## E2E Tests

End-to-end tests validate the full voice pipeline from text input through command execution.

### Command Parsing Tests

Tests intent classification and parameter extraction (the "front half" of the pipeline):

```bash
cd jarvis-node-setup

# List all available tests
python test_command_parsing.py -l

# Run all tests
python test_command_parsing.py

# Run specific tests by index
python test_command_parsing.py -t 5 7 11

# Run tests for specific commands
python test_command_parsing.py -c calculate get_weather

# Custom output file
python test_command_parsing.py -o results.json
```

**Required services:** Command Center (7703), LLM Proxy (7704)

### Multi-Turn Conversation Tests

Tests tool execution, validation flow, and context preservation (the "back half"):

```bash
cd jarvis-node-setup

# Fast mode (text only, no audio pipeline)
python test_multi_turn_conversation.py

# Full mode (TTS + Whisper audio pipeline)
python test_multi_turn_conversation.py --full

# Run a specific category
python test_multi_turn_conversation.py -c validation

# Save audio artifacts
python test_multi_turn_conversation.py --full -t 0 1 2 --save-audio ./audio/
```

**Test categories:** `tool_execution`, `validation`, `result_incorporation`, `context`, `error_handling`, `complex`

**Required services:** Command Center (7703), LLM Proxy (7704). For full mode: TTS (7707), Whisper API (7706).

## CI Integration Testing

Cross-service integration tests live in [`jarvis-integration-tests`](https://github.com/alexberardi/jarvis-integration-tests). There are three lanes, each serving a different purpose:

| Lane | Workflow | Trigger | What it proves |
|------|----------|---------|----------------|
| **Fast** | `integration-runner.yml` | Every PR (via `repository_dispatch`) | Core stack wiring — all three services faked |
| **Behavior** | `behavior-corpus.yml` | Nightly + manual | Real tool routing via ChatGPTOpenAI against gpt-4.1-nano (requires `OPENAI_API_KEY`) |
| **From-source** | `from-source-services.yml` | Every PR in llm-proxy / whisper / tts (via `repository_dispatch`) | Real service contract — PR source built into the live stack |

### From-source lanes (T9)

The fast lane always fakes the LLM, whisper, and TTS services. The **from-source lanes** give a PR in `jarvis-llm-proxy-api`, `jarvis-whisper-api`, or `jarvis-tts` a real cross-service signal: the service under test is built from the PR's source and wired into the real CC + auth + config stack, with only the *other two* services remaining faked.

No `OPENAI_API_KEY` is required — `jarvis-llm-proxy-api` runs the deterministic MOCK backend; `jarvis-whisper-api` and `jarvis-tts` bake their CPU model/voice weights at Docker build time.

**Trigger manually:**

```bash
gh workflow run from-source-services.yml \
  --repo alexberardi/jarvis-integration-tests --ref main \
  -f service=jarvis-tts \
  -f source_ref=main
```

Replace `service` with one of: `jarvis-llm-proxy-api`, `jarvis-whisper-api`, or `jarvis-tts`. Use `source_ref` to pin a branch or SHA instead of `main`.

**Auto-trigger (PR path):** each service repo's `integration-trigger.yml` fires `repository_dispatch [from-source-integration]` at `jarvis-integration-tests` on PRs, carrying the PR's head SHA and number so results are posted back as a PR comment. Requires `INTEGRATION_DISPATCH_TOKEN` to be set on the originating service repo (green-idle until set).

### Case catalog

| Case | Lane | What it tests |
|------|------|---------------|
| CASE-001..003 | Fast | Fakes-only smoke — no real stack |
| CASE-101..215 | Fast | Full CC + auth + config round-trips (all three services faked) |
| CASE-301 | From-source (llm-proxy) | Real proxy `/health` proxies to the model service — proves the API→model-service internal hop |
| CASE-302 | From-source (llm-proxy) | CC routes a voice command through the real proxy (MOCK backend, no key) |
| CASE-311 | From-source (tts) | CC streams a voice reply through real Piper TTS — asserts real audio (`> 1 KB`, not the fake's 32 bytes) |
| CASE-321 | From-source (whisper) | CC proxies audio through real whisper — asserts `{text, segments, speaker}` shape |

### seed.sh discovery parameters

`compose/seed.sh` registers each service in the config-service discovery table so CC routes to it. The from-source lanes override the default host-fake targets by passing environment variables before calling the script:

| Variable | Default | From-source override |
|----------|---------|----------------------|
| `LLM_PROXY_HOST` | `host.docker.internal` | `jarvis-llm-proxy-api` (compose service name) |
| `LLM_PROXY_PORT` | `7705` | `7704` |
| `WHISPER_HOST` | `host.docker.internal` | `jarvis-whisper-api` |
| `WHISPER_PORT` | `7706` | `7706` |
| `TTS_HOST` | `host.docker.internal` | `jarvis-tts` |
| `TTS_PORT` | `7707` | `7707` |

These env vars determine which host CC's config-service discovery row points at — since config-service discovery takes precedence over CC's env fallback (`JARVIS_WHISPER_URL` / `JARVIS_TTS_URL`), setting these correctly is what actually routes CC to the real container.


## Cross-Repo Integration Tests

When a feature spans multiple repos (e.g. a change to `jarvis-command-center` that depends on a concurrent change to `jarvis-llm-proxy-api`), the **cross-repo integration lane** in `jarvis-integration-tests` builds all affected services from source and tests them together as a unit.

### Declaring Linked PRs

Add one `Linked-PR:` marker per sibling PR in your PR body:

```
Linked-PR: jarvis-llm-proxy-api@feat/streaming
Linked-PR: jarvis-llm-proxy-api@a1b2c3d   # a SHA is reproducible; a branch resolves at clone time
```

The trigger workflow (`cross-repo-trigger.yml`) in each participating repo reads these markers and fires the `cross-repo-integration` dispatch at `jarvis-integration-tests`. Every repo in the feature computes the same sorted `feature_key` from all participants, so only one integration run executes per feature — duplicates are deduplicated by the receiver's concurrency group.

**PRs with no `Linked-PR:` markers are unaffected** — the existing single-repo fast lane (`integration-trigger.yml`) still runs as normal.

### Requirements

- The `INTEGRATION_DISPATCH_TOKEN` repository secret must be configured on each participating repo. This is a fine-grained PAT scoped to `repository_dispatch` (write) on `alexberardi/jarvis-integration-tests`. Until the token is set, the trigger warns and passes without dispatching.
- Adding a `Linked-PR:` marker after the PR is opened (via an edit) re-fires the cross-repo lane automatically (`edited` event is included).

### Symmetric by design

Both sides of a cross-repo feature should carry the `Linked-PR:` markers pointing at each other. Because the `feature_key` is a sorted union of all participating repo slugs, both PRs resolve to the same key and the receiver deduplicates them to a single run.


## Test Results

E2E test results are written to JSON files containing:

- Summary with pass/fail counts, success rate, and response times
- Per-test results with expected vs actual output
- Analysis with command success rates and a confusion matrix
- Recommendations for improving low-performing commands

## Performance Target

Total end-to-end voice latency target: **under 5 seconds**, including:

- Whisper transcription (speech-to-text)
- Date context extraction
- Command inference (tool routing)
- Command execution and response generation
