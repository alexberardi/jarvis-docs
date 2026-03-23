# Getting Started

Jarvis is a microservice-based voice assistant you can self-host. This section walks you through installation, sending your first command, and understanding the configuration system.

## Prerequisites

- **Docker** and **Docker Compose** (v2+)

For GPU-accelerated LLM inference:

- **macOS**: Apple Silicon (M1+) for Metal/MLX
- **Linux**: NVIDIA GPU with CUDA drivers and nvidia-docker

!!! note
    Python and Git are only needed if you're [installing from source](installation.md#option-5-from-source-developers).

## What You'll Learn

1. **[Installation](installation.md)** — Multiple install options: one-liner, npx, Docker, or from source
2. **[Your First Command](first-command.md)** — Register a node and send a test voice command
3. **[Configuration](configuration.md)** — Network modes, environment variables, and service discovery
