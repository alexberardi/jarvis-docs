# Contributing

Jarvis is open source and welcomes contributions. This section covers the development standards, testing approach, and workflow for contributing to the project.

## Getting Started

1. Clone the repository and read the top-level `CLAUDE.md` for a full architecture overview
2. Check the service's own `CLAUDE.md` or `README.md` before working on it -- each service may have unique setup requirements
3. Follow the [Coding Standards](coding-standards.md) for all code changes
4. Write tests using the [Testing](testing.md) approach (TDD is mandatory)

## Development Setup

```bash
# Bootstrap everything (generates tokens, creates .env files, starts infra, runs migrations)
./jarvis quickstart

# Or step by step:
./jarvis init          # Generate credentials and .env files
./jarvis start --all   # Start all services in dependency order
./jarvis health        # Verify everything is running
```

See [Installation](../getting-started/installation.md) for detailed setup instructions.

## Key Principles

- **Be a scalpel, not a hammer** -- Ask questions early rather than repeatedly trying failing approaches
- **TDD always** -- Write tests first (RED), implement (GREEN), refactor (IMPROVE)
- **Type everything** -- Every function parameter, return type, and variable gets a type hint
- **Log correctly** -- Use `JarvisLogger` from `jarvis-log-client`, never `print()`
- **Docker first** -- New services should run in Docker containers

## Where to Start

- **New command**: Implement `IJarvisCommand` in `jarvis-node-setup/commands/` (see [Building Commands](../commands/index.md))
- **New service**: Follow existing patterns (FastAPI + Uvicorn, Docker Compose, Alembic migrations)
- **Bug fix**: Check the service's test suite, write a failing test for the bug, then fix it
- **Documentation**: Service-level docs live in each service's `CLAUDE.md`

## Further Reading

- [Coding Standards](coding-standards.md) -- Style rules, import ordering, type hints
- [Testing](testing.md) -- TDD workflow, test commands, coverage targets
