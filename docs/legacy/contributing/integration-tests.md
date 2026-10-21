# Integration Tests

`jarvis-integration-tests` is the cross-service behavior test harness for the Jarvis ecosystem. It routes a voice-command corpus through command-center's **real** `ChatGPTOpenAI` provider + llm-proxy's REST backend + a live cloud model, proving that the full voice pipeline selects the correct tools.

This is distinct from the per-service unit CI suites (which verify wiring against fakes). The behavior lane answers: *does a real model, given real tool schemas, route real utterances correctly through the real code path?*

## Repository

[alexberardi/jarvis-integration-tests](https://github.com/alexberardi/jarvis-integration-tests) — migrated from `jarvis-node-setup`.

## What the corpus covers

The **command-center behavior corpus** lives in `tests/behavior/`:

- **`tools.cc.yaml`** — command-center's real built-in tool schemas, transcribed from the command sources via the SDK's `to_openai_tool_schema()`. Covers the 8 built-in commands available on a baseline node (`reminder`, `get_current_time`, `get_weather`, `calculate`, `convert_measurement`, and others), plus near-neighbour tools so routing *disambiguation* is exercised.
- **`corpus.cc.yaml`** — 29 utterances: 26 routing cases + 3 negative cases (small talk that must **not** trigger a tool). Each entry specifies the expected tool and optional argument matchers (`equals` / `contains` / `in` / `any_of`).

!!! note
    Optional `jarvis-cmd-*` packages (weather plugins, music, news) are excluded — a baseline node may not have them. The llm-proxy behavior corpus in `jarvis-llm-proxy-api` uses a **fictional** stand-in toolset with different names and argument shapes; the two corpora are not interchangeable.

## How the test works

`tests/test_cc_behavior_corpus.py` orchestrates via Docker Compose:

1. A compose overlay (`compose/ci-overlays/llm-proxy-behavior.yaml`) boots llm-proxy's model service (`:7705`) + API (`:7704`) in `REST → gpt-4.1-nano` mode.
2. `compose/seed.sh` registers the proxy with config-service so CC's discovery finds it.
3. CC's `llm.interface` is flipped to `ChatGPTOpenAI` via the settings API.
4. For each corpus utterance: `POST /api/v0/conversation/start` → `POST /api/v0/voice/command` (blocking). The response's tool selection and argument values are checked against the corpus matchers.

The test is **gated on `CC_URL` + node credentials** — it skips automatically in the per-service fast CI lane when those environment variables are absent.

Model is pinned to **`gpt-4.1-nano-2025-04-14`** at `temperature=0` for deterministic, reproducible routing.

## One-time setup

The nightly CI job stays idle until the OpenAI API key secret is set. Run this once:

```bash
# Mint a usage-capped key in the OpenAI dashboard first (the corpus costs pennies/run)
gh secret set OPENAI_API_KEY --repo alexberardi/jarvis-integration-tests
```

## Triggering the behavior lane

The workflow runs nightly on a staggered schedule, or on demand:

```bash
gh workflow run behavior-corpus.yml --repo alexberardi/jarvis-integration-tests --ref main
```

Or via the GitHub UI: **Actions → Behavior lane (nightly) → Run workflow**.

If `OPENAI_API_KEY` is not set, the job emits a warning and passes (no-op) rather than failing nightly builds.

## How it fits in the test hierarchy

| Suite | Repo | What it proves |
|---|---|---|
| Per-service unit CI | Each `jarvis-*` repo | Wiring against fakes — fast, no keys, gates every PR |
| llm-proxy behavior lane | `jarvis-llm-proxy-api` | REST backend tool passthrough, fictional corpus |
| **CC behavior lane** | `jarvis-integration-tests` | Full voice pipeline routing — real provider, real corpus, real model |

A regression in the CC behavior lane means the utterance → tool-selection → command path is broken at the real-model level, not just at the wiring level.
