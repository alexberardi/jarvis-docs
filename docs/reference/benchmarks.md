# Benchmarks

LLM benchmarks for Jarvis are tracked in the `docs/benchmarks/` directory of the main repository. These benchmarks measure command parsing accuracy, latency, and memory usage across different models and backends.

## What Is Measured

- **Command parsing accuracy** -- Does the LLM correctly identify the intended command and extract the right parameters from a voice transcription?
- **Latency** -- Time from receiving the transcription to returning a tool call (inference time).
- **Memory usage** -- VRAM and RAM consumption for different model sizes and quantization levels.

## Tested Configurations

Benchmarks cover multiple dimensions:

| Dimension | Variants |
|-----------|----------|
| Models | Qwen 2.5 (7B, 14B), Qwen 3 (14B, 32B), Llama 3.1 8B, Hermes 3 8B, others |
| Backends | MLX (macOS Metal), GGUF (llama.cpp), vLLM (CUDA) |
| Quantization | Q4_K_M, Q6_K, FP16 |
| Adapters | Base model vs LoRA fine-tuned |

## Where to Find Them

Benchmark results and comparison tables are maintained in:

```
docs/benchmarks/
```

Each benchmark run records the model, backend, quantization level, hardware, test suite version, and per-command accuracy breakdown.

## Running Benchmarks

Use the E2E command parsing test suite to generate benchmark data:

```bash
cd jarvis-node-setup

# Run all command parsing tests
python test_command_parsing.py -o benchmark_results.json

# Run for specific commands
python test_command_parsing.py -c calculate get_weather send_email -o benchmark_results.json
```

Results include per-command success rates, average response times, and a confusion matrix showing which commands get misclassified.
