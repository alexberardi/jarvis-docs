# Models and hardware

Jarvis Automation runs its models on your own machine: a language model that understands what you say and calls the right tool, plus speech-to-text, a voice, embeddings and speaker recognition. This page lists the models Jarvis can download for you and which language model to pick for your hardware.

Jarvis Automation is a **pre-release** (release candidate rc18). The catalog below is the one rc18's server ships; it can change between release candidates.

## Which language model to pick

The language model is the choice that matters: it decides how often Jarvis picks the right action and how long you wait for an answer. The others have sensible defaults.

| Your machine | Pick | Why |
|---|---|---|
| Mac with 16 GB | **Qwen 3 4B (Q4_K_M)** | 98.8 % right, about 1.2 s per warm turn. |
| Mac with 24 GB or more | **Qwen 3.5 9B (Q4_K_M, vision)** | Headroom for harder requests; reads images. |
| Mac with 32 GB or more | Qwen 3.5 9B, or try **Qwen 3.5 27B** or **35B-A3B (MLX 4-bit)** | Larger, text-only, not benchmarked yet. |
| PC or Linux box with a GPU | The largest model whose badge says **Fits** | **Qwen 3.8 27B** needs a 24 GB card. |
| No usable GPU (CPU only) | **Qwen 3 4B (Q4_K_M)** | The smallest; still slow on a CPU. |

The 16 GB figures come from an informal run by the project's author on a Mac mini M4 (16 GB) on 2026-10-21, not yet written up in jarvis-server: 98.8 % on the 80-utterance benchmark, about 1.2 s per warm turn and about 15 s for the first turn after a restart. On a CPU even the 4B is slow, so a language model on another machine may be worth it. [Benchmarks](../reference/benchmarks.md) has all the numbers and how they were measured.

### What the setup wizard suggests

The setup wizard (`http://<host>:7710/setup`) and the **Models** page of the admin estimate, for each model, whether it fits the hardware Jarvis detected, and show it as a badge:

| Badge | Meaning |
|---|---|
| Fits | Fits one GPU (or a Mac's memory) at its default context. |
| Tight | Fits, but within 10 % of the card's memory. |
| Needs 2+ GPUs | Only fits split across several cards. |
| Runs on CPU | No usable GPU, so it runs in system RAM. |
| Too big | Does not fit the card, or the RAM on the CPU, or the machine has less memory than the model asks for. |
| Built in | Runs inside the server itself (the voice and speaker recognition). |

The suggestion is the largest model that fits, which is not always the fastest, and it can differ from the table above:

- **On a Mac** (Apple silicon), the wizard looks at the MLX models first and suggests the largest one that fits; only if none fits does it suggest a llama.cpp (GGUF) model. The MLX 9B is never suggested, and the 27B and 35B-A3B MLX models need 32 GB, so on a Mac with 32 GB or more the suggestion is usually **Qwen 3.5 35B-A3B (MLX 4-bit)**, which is not benchmarked yet.
- **On a Mac with less than 32 GB**, it suggests the largest GGUF model that fits, which may be larger than the 9B the table recommends.

So on a Mac, pick by hand: Qwen 3 4B on 16 GB, Qwen 3.5 9B (Q4_K_M) on 24 GB or more, even if the wizard suggests a larger model. You can change the model on the **Models** page at any time.

## The catalog

Sizes are the download sizes. A model needs that much memory plus room for its context, which the fit badge accounts for.

### Language models

Jarvis uses a language model for two jobs: **live** (answering you) and **background** (work nobody is waiting on, such as memory). Both use the same model unless you set them apart. The MLX models run on MLX (Apple Silicon only), the others on llama.cpp; the default context is 16,384 tokens, 32,768 for the Qwen 3.5 9B models.

| Model | Download | Notes |
|---|---|---|
| Qwen 3 4B (Q4_K_M) | 2.5 GB | The pick for 16 GB Macs and CPU-only machines. |
| Qwen 3 8B (Q4_K_M) | 5.0 GB | |
| Qwen 3.5 9B (Q4_K_M, vision) | 5.7 GB + 0.9 GB projector | Reads images; the projector downloads with it. |
| Qwen 3 14B (Q4_K_M) | 9.0 GB | |
| Qwen 3.8 27B (UD-Q4_K_M, vision) | 16.5 GB + 0.9 GB projector | Needs a 24 GB card. For long contexts, give it a second card or use a q8_0 KV cache. |
| Qwen 3.5 9B (MLX 4-bit, Apple Silicon) | 5.1 GB | Text-only. Not suggested: it called a tool on 88.8 % of the tool benchmark, against 100 % for the 9B GGUF. |
| Qwen 3.5 27B (MLX 4-bit, Apple Silicon) | 15.2 GB | Text-only. Needs a Mac with 32 GB or more. |
| Qwen 3.5 35B-A3B (MLX 4-bit, Apple Silicon) | 19.7 GB | Text-only. Needs a Mac with 32 GB or more. |

### Speech, voice and the rest

| Model | Download | Used for |
|---|---|---|
| Whisper large-v3-turbo | 1.6 GB | Speech-to-text. Suggested on a GPU when it fits next to the language model. |
| Whisper large-v3-turbo (Q5_0) | 574 MB | Speech-to-text. The same model, quantized. |
| Whisper small.en | 488 MB | Speech-to-text. Suggested otherwise. |
| Whisper base.en | 148 MB | Speech-to-text. Suggested on a CPU with under 8 GB of RAM. |
| Kokoro v1.0 multi-language | 350 MB | Jarvis's voice. Default voice bm_george (British English) at 1.25× speed. Built in. |
| all-MiniLM-L6-v2 embeddings | 46 MB | Memory search. |
| 3D-Speaker ERes2Net | 26 MB | Speaker recognition. Built in. |

## Engines

An engine is the program that runs a language model. Jarvis downloads and starts it for you.

| Engine | Runs | Status |
|---|---|---|
| llama.cpp | GGUF models, on macOS, Windows and Linux; on the GPU (Metal, CUDA, ROCm or Vulkan) or the CPU | Ready |
| MLX (mlx-lm) | MLX models, on Apple Silicon only | Ready |
| vLLM | Hugging Face models on NVIDIA GPUs | In progress |
| Transformers | Hugging Face models | In progress |

vLLM and Transformers appear in the admin, but they are in progress: use llama.cpp or MLX for now.

## See also

- [Benchmarks](../reference/benchmarks.md): the accuracy and latency numbers behind the picks.
- [Requirements and choosing a model](../install/requirements.md): what the server needs before you install.
