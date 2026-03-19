# Getting Started

Jarvis is a microservice-based voice assistant. This section walks you through installation, sending your first command, and understanding the configuration system.

## Prerequisites

- **Docker** and **Docker Compose** (v2+)
- **Python 3.11+**
- **PostgreSQL** (provided via Docker)
- **Git**

For GPU-accelerated LLM inference:

- **macOS**: Apple Silicon (M1+) for Metal/MLX
- **Linux**: NVIDIA GPU with CUDA drivers and nvidia-docker

## What You'll Learn

1. **[Installation](installation.md)** — Run `./jarvis quickstart` to bootstrap everything
2. **[Your First Command](first-command.md)** — Register a node and send a test voice command
3. **[Configuration](configuration.md)** — Network modes, environment variables, and service discovery
