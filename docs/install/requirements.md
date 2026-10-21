# Requirements and choosing a model

What the server needs (operating system, memory, disk, GPU) and how to pick the language model that fits your hardware. See also [Models and hardware](../models/index.md).

Jarvis Automation is a **pre-release** (release candidate rc18). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Choosing a model

The language model you run sets how quick and how accurate Jarvis feels, so pick it by your machine's memory:

- **Mac with 16 GB:** Qwen 3 4B (Q4_K_M).
- **Mac with 24 GB or more:** Qwen 3.5 9B (Q4_K_M, vision).
- **PC or Linux box with a GPU:** the largest model the setup wizard marks **Fits**.
- **No usable GPU:** Qwen 3 4B (Q4_K_M).

The setup wizard suggests one and you can change it later. [Models and hardware](../models/index.md) has the full catalog, the engines and the reasons; [Benchmarks](../reference/benchmarks.md) has the numbers.

The operating system, memory and disk requirements are still being written up.
