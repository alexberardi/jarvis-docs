# Models and hardware

Jarvis Automation runs its models on your own machine: a language model that understands what you say and calls the right tool, plus speech-to-text, a voice, embeddings and speaker recognition. This page lists the models Jarvis can download for you and which language model to pick for your hardware.

Jarvis Automation is a **pre-release** (release candidate rc18.8). The catalog below is the one rc18's server ships; it can change between release candidates.

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

## Use a cloud model instead

If your machine is too slow for a local model, Jarvis can send its language-model requests to a cloud provider instead. Speech-to-text, the voice and speaker recognition stay on your machine. From rc18.8, Google Gemini, OpenAI and Anthropic work without extra setup, and each is tested against the real provider before every release.

!!! warning "What leaves your machine"
    The text of every request for that label goes to the provider: what you said, the conversation so far, Jarvis's instructions and the list of tools it can use. Use a provider you trust.

### Walkthrough: Gemini 3.1 Flash-Lite

1. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. In the admin, open **Models**, find **Live (voice replies)** and set **Runs** to **Remote endpoint**.
3. Fill in:

    | Field | Value |
    |---|---|
    | Base URL | `https://generativelanguage.googleapis.com` |
    | API | auto |
    | Model name | `gemini-3.1-flash-lite` |
    | API key | your AI Studio key |

    Jarvis adds Google's `/v1beta/openai` path itself; pasting the full URL works too.
4. Save. Under **Prompt and model behaviour**, the prompt should now read **Cloud**. If it shows a different prompt marked **set by you**, click **Use the model's (Cloud)**.
5. Say something to a node, such as "add milk to my todo list".

**Background (memory, planning)** keeps its own setting: leave it on this machine, or point it at the same provider the same way.

### Other providers

| Provider | Base URL | Model name (tested) |
|---|---|---|
| Google Gemini | `https://generativelanguage.googleapis.com` | `gemini-3.1-flash-lite` |
| OpenAI | `https://api.openai.com/v1` | `gpt-5-nano` |
| Anthropic | `https://api.anthropic.com` | `claude-haiku-4-5-20251001` |

Leave **API** on auto: Jarvis uses Anthropic's own API for `api.anthropic.com` and the OpenAI-compatible one for everything else, so any other OpenAI-compatible service works too.

### If it doesn't answer

- **Busy or rate-limited:** when the provider answers 429 or 5xx (Google's "This model is currently experiencing high demand"), Jarvis retries twice, after 1 s and 3 s, and then gives up on that turn.
- **Requests hang:** preview models, such as some Gemini 3.x ones, sometimes hang on the provider's side. Try a model listed above.
- **Error from the provider:** Jarvis passes on the provider's own message, such as a 400 for an unknown model name or a 401 for a wrong key.

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
