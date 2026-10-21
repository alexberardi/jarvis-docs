# Benchmarks

How well each language model picks the right action for what you say, and how long it takes, measured on the Jarvis Automation server (jarvisd). These are the numbers behind the picks in [Models and hardware](../models/index.md).

Jarvis Automation is a **pre-release** (release candidate rc18). The numbers below were measured on rc18-era builds and will be re-measured as the prompt and the models change.

## Results

Accuracy is the share of utterances where the model's first tool call is the right one (with the right arguments, where the corpus checks them). Prompt tokens are what the model reads per turn.

### On a 16 GB Mac

Qwen 3 4B (Q4_K_M), measured by the project's author on 2026-10-21 on a Mac mini M4 with 16 GB, with the 80-utterance corpus. This was an informal run: unlike the experiments below, it has no written record in jarvis-server yet. A cold turn is the first one after a restart, before the prompt is cached.

| Accuracy | Warm turn | Cold turn |
|---|---|---|
| 98.8 % | about 1.2 s | about 15 s |

### Prompt-diet experiment

Measured on 2026-10-20 for jarvis-server's prompt-diet decision, on the 80-utterance corpus:

| Model | Accuracy | Prompt tokens |
|---|---|---|
| Qwen 3 4B (Q4_K_M) | 100 % | 4,619 |
| Qwen 3.5 9B (Q4_K_M, vision) | 98.8 % | 4,790 |

And on the hard scenarios, the first turn of each of the server's pipeline scenarios (`tools/pipeline/scenarios/`): the right tool, then the right tool with the right arguments.

| Model | Right tool | With arguments |
|---|---|---|
| Qwen 3.5 9B (Q4_K_M, vision) | 91.3 % | 79.7 % |
| Qwen 3 4B (Q4_K_M) | 88.4 % | 77.5 % |

On a MacBook Pro (M2 Max) in the same experiment, the first tool call from Qwen 3 4B after a restart took about 5 s, and about 0.5 s once the prompt was cached.

### MLX

On the same 16 GB Mac, Qwen 3.5 9B (MLX 4-bit) called a tool on 88.8 % of the tool benchmark, against 100 % for the Qwen 3.5 9B GGUF: it answers arithmetic itself instead. So Jarvis does not suggest it. The larger MLX models are not measured yet.

!!! note "Where the numbers come from"
    "Prompt-diet experiment" is jarvis-server's decision record `docs/decisions/2026-10-20-prompt-diet.md`, measured on the captured prompts before the change was ported; the record does not name the machine for its accuracy runs. The MLX figure is from the catalog's note on that model. Older benchmark tables measured on the retired Docker stack do not apply to jarvisd and are not repeated here.

## How it is measured

The benchmark is `scripts/toolbench` in [jarvis-server](https://github.com/alexberardi/jarvis-server). It replays the exact prompt the server sends, so the numbers reflect what the model sees in real use:

1. **Capture.** `scripts/toolbench capture` starts a sandbox server from the checkout, says "hello" as a voice node and as a desktop node, and saves each request the model received: system prompt, tool list and sampling settings, byte for byte.
2. **Replay.** `scripts/toolbench run` sends each case to the model with the captured prompt, the case's utterance in place of "hello".
3. **Score.** Only the first tool call counts: the right tool, then the right arguments (numbers by value, text case-insensitively, patterns by regular expression). Prompt tokens and latency come from the model's response.

Without `--corpus`, the cases are the desktop toolset's examples and the first turn of each pipeline scenario (the hard scenarios). With `--corpus`, they are the 80 utterances of `install-e2e/gpu/bench_corpus.cc.yaml`, played on the voice node. That corpus lives in the legacy [jarvis](https://github.com/alexberardi/jarvis) repository.

### Run it yourself

From a jarvis-server checkout, with a server running the model you want to measure:

```bash
scripts/toolbench capture
scripts/toolbench run \
  --corpus ../jarvis/install-e2e/gpu/bench_corpus.cc.yaml \
  --url http://<host>:<port> --model live \
  --repeat 3 --out results.json
```

Without `--url`, it measures the installed server the jarvis-server dev harness points at. `--url` takes any OpenAI-compatible endpoint, called without credentials; `--model` is the label or model name to ask for (default `live`). Reading the YAML corpus needs PyYAML; pass a `.json` copy of it where that is missing. When you publish a result, record the machine, the model, the engine, the date, the corpus and the repeat count.
