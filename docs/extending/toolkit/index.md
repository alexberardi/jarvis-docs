# Developer Toolkit (`jdt`)

The Jarvis Developer Toolkit is a CLI that handles the full package lifecycle: scaffold, validate, test, generate manifests, and deploy. It is the primary way to create, iterate on, and ship Jarvis packages.

## Installation

```bash
pip install git+https://github.com/alexberardi/jarvis-developer-toolkit.git
```

This installs the `jdt` command. Verify with:

```bash
jdt --version
```

## Commands at a Glance

| Command | What it does | Speed |
|---------|-------------|-------|
| [`jdt init`](init.md) | Scaffold a new package with working stubs | Instant |
| [`jdt test`](test.md) | Three-phase validation (manifest + AST + imports) | ~2s |
| [`jdt validate`](validate.md) | Fast manifest-only check | Instant |
| [`jdt manifest`](manifest.md) | Generate/update `jarvis_package.yaml` from code | ~1s |
| [`jdt deploy`](deploy.md) | Install to a node (local, Docker, or SSH) | ~3s |

## Typical Workflow

```bash
# 1. Create a package
jdt init my_weather --type command

# 2. Implement your logic
cd my_weather
# ... edit commands/my_weather/command.py ...

# 3. Validate as you go
jdt test .

# 4. Deploy to a node
jdt deploy local .
```

For a complete walkthrough, see the [Development Workflow](workflow.md) guide.

## What Gets Scaffolded

When you run `jdt init`, you get a complete, valid package that passes all tests out of the box:

```
my_weather/
├── commands/
│   └── my_weather/
│       ├── __init__.py
│       └── command.py        # Working IJarvisCommand stub
├── jarvis_package.yaml       # Valid manifest
├── CLAUDE.md                 # AI assistant context
├── README.md
├── LICENSE
└── .gitignore
```

The stubs are not empty shells --- they implement every required property and method with sensible defaults. You can `jdt deploy` the scaffold immediately and iterate from a working baseline.

## Component Types

`jdt` supports all six Jarvis extension types:

| Type | Flag | Interface | Entry File |
|------|------|-----------|------------|
| Command | `--type command` | `IJarvisCommand` | `command.py` |
| Agent | `--type agent` | `IJarvisAgent` | `agent.py` |
| Device Protocol | `--type protocol` | `IJarvisDeviceProtocol` | `protocol.py` |
| Device Manager | `--type manager` | `IJarvisDeviceManager` | `manager.py` |
| Routine | `--type routine` | JSON schema | `routine.json` |
| Prompt Provider | `--type prompt_provider` | `IJarvisPromptProvider` | `provider.py` |

You can combine types in a single package:

```bash
jdt init smart_lights --type command,protocol,manager
```

This creates a multi-component bundle with all three stubs and a unified manifest.

## Validation Pipeline

`jdt test` runs the same three-phase pipeline that Pantry uses for submission review. Passing locally means your package will pass Pantry validation.

```
Phase 1: Manifest Validation
  ├── Schema version, YAML syntax
  ├── Semver format (X.Y.Z)
  ├── Required fields (name, description, version)
  ├── Valid categories and component types
  └── Component paths exist on disk

Phase 2: Static Analysis (AST)
  ├── Correct base class (IJarvisCommand, etc.)
  ├── Required methods/properties present
  ├── No dangerous imports (subprocess, os, shutil)
  ├── No dangerous calls (eval, exec, os.system)
  ├── No raw database access (sqlite3, sqlalchemy)
  └── No shared directory name collisions

Phase 3: Import Checks
  ├── Module imports successfully
  ├── SDK subclass found and instantiated
  ├── Properties return correct types
  └── Examples methods return lists
```

## Next Steps

- **New to Jarvis?** Start with [`jdt init`](init.md) and the [Development Workflow](workflow.md)
- **Have existing code?** Use [`jdt manifest`](manifest.md) to generate a manifest from your code
- **Ready to ship?** Use [`jdt deploy`](deploy.md) to install to a node
- **Using Claude Code?** See the [Claude Code Integration](claude-code.md) guide
