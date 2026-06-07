# Pantry Runner

> **Comprehensive reference in [jarvis-docs#11](https://github.com/alexberardi/jarvis-docs/pull/11).** This stub exists to track runner#6 for idempotency. Merge whichever comprehensive runner draft you accept first, then integrate the Troubleshooting section below.

## Troubleshooting

### `harness produced no output | harness did not write JSON`

This error appears in the submission UI when the pantry store callback receives an empty harness artifact. The pre-stage step runs the install inside a throwaway container using a single-quoted shell string:

```sh
docker run ... sh -c '<run block contents>'
```

A literal apostrophe anywhere in that block — including inside a comment — closes the outer single quote and causes bash to exit with a parse error **before pip runs**. The harness container is never started, the output artifact is never written, and the pantry store reports the misleading `harness produced no output` envelope back to the submitter.

**Known root causes and status:**

| Cause | Clue in GHA log | Fixed in |
|---|---|---|
| Apostrophe inside single-quoted pre-stage `run:` block | `syntax error near unexpected token ')'`, pre-stage exits 2 | runner#6 (2026-05-22) |
| Missing `git` in `python:3.11-slim` pre-stage container | `Cannot find command 'git'` | runner#4 (2026-05-20) |
| `--only-binary=:all:` blocking sdist-only deps | pip exits non-zero before harness starts | runner#5 (2026-05-22) |

#### Pre-stage shell quoting guard

`test_pre_stage_run_block_is_valid_bash` (added in runner#6) runs `bash -n` over the pre-stage `run:` content on every PR. Any unbalanced quote, brace, or parenthesis now fails the test suite at PR time instead of surfacing as a fake harness rejection downstream.
