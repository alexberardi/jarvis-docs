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
