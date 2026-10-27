# Requirements and choosing a model

What the server needs (operating system, memory, disk, GPU) and how to pick the language model that fits your hardware. See also [Models and hardware](../models/index.md).

Jarvis Automation is a **pre-release** (release candidate rc18.10). Builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Choosing a model

The language model you run sets how quick and how accurate Jarvis feels, so pick it by your machine's memory:

- **Mac with 16 GB:** Qwen 3 4B (Q4_K_M).
- **Mac with 24 GB or more:** Qwen 3.5 9B (Q4_K_M, vision).
- **PC or Linux box with a GPU:** the largest model the setup wizard marks **Fits**.
- **No usable GPU:** Qwen 3 4B (Q4_K_M).

The setup wizard suggests one and you can change it later. [Models and hardware](../models/index.md) has the full catalog, the engines and the reasons; [Benchmarks](../reference/benchmarks.md) has the numbers.

## The server

The server runs on a machine that stays on. It is one program, `jarvisd`, with its database built in: there is no Docker to install.

| System | Processor | Notes |
|---|---|---|
| **macOS** | Apple silicon (M1 or later) | Intel Macs are not supported. Models run on the GPU through Metal. |
| **Windows** | 64-bit Intel or AMD (`amd64`) | Runs as a Windows service. |
| **Linux** | 64-bit Intel or AMD (`amd64`), or ARM (`arm64`) | Needs systemd. Models run on an NVIDIA (CUDA) or AMD (ROCm, Vulkan) GPU, or on the CPU. |

Each install page lists what it needs: [macOS](macos.md), [Windows](windows.md), [Linux](linux.md). Since rc18.4 there is also a container, for [Unraid](unraid.md) or [Docker](docker.md); releases up to rc18 have no image.

### Memory

The language model takes most of the memory, so the [model you choose](#choosing-a-model) sets how much you need:

- **A Mac** shares its memory with the GPU: 16 GB runs Qwen 3 4B, 24 GB or more runs Qwen 3.5 9B.
- **A PC or Linux box with a GPU**: the model has to fit the card's memory, with room for its context. Qwen 3.8 27B, the largest GGUF model, needs a 24 GB card.
- **On the CPU**, the model runs in system RAM. Qwen 3 4B is the one to use, and it is slow.

The setup wizard reads your hardware and marks each model **Fits** or not, so you don't have to work this out by hand.

### Disk

Nothing large is downloaded until you pick the models in the setup wizard. Plan for the models you pick plus a few GB for the program, the engines it downloads with them and the database:

| Set of models | Download |
|---|---|
| Qwen 3 4B, Whisper small.en, the voice, speaker recognition and embeddings | about 3.5 GB |
| Qwen 3.5 9B (with its vision projector) and the same others | about 7.5 GB |
| Qwen 3.8 27B (with its vision projector), Whisper large-v3-turbo and the same others | about 19.5 GB |

The sizes of every model are in [the catalog](../models/index.md#the-catalog). They are stored in the server's [data directory](../operate/data-and-backups.md#where-the-data-lives).
