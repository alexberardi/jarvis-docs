# Using Claude Code with `jdt`

Claude Code is a natural fit for Jarvis package development. The `jdt` scaffold generates a `CLAUDE.md` that gives Claude the context it needs, and the validation pipeline gives Claude a tight feedback loop to iterate against.

## Quick Start

```bash
# Scaffold a package
jdt init my_weather --type command --category weather

# Open Claude Code in the package directory
cd my_weather
claude
```

Claude Code reads the generated `CLAUDE.md` and understands:

- What component types are in the package
- The SDK interfaces and how to use them
- The `jdt` commands for testing and deploying
- Key rules (logging pattern, error handling, shared code naming)

From there, you can describe what you want in natural language:

> "Implement a weather command that uses the OpenWeatherMap API. It should accept a city and optional units parameter."

Claude will write the implementation, declare the right secrets and parameters, and validate with `jdt test`.

## The Generated CLAUDE.md

Every `jdt init` scaffold includes a `CLAUDE.md` tailored to the package. It contains:

**Development commands:**

```bash
jdt test .              # Run Pantry-compatible tests
jdt test . -v           # Verbose output
jdt test . --install-deps  # Auto-install pip deps before testing
jdt validate .          # Fast manifest-only check
jdt manifest .          # Regenerate manifest from code
jdt deploy local .      # Install to local node
```

**SDK quick reference** for `CommandResponse`, `JarvisStorage`, `JarvisParameter`, and `JarvisSecret` --- the classes Claude needs most often.

**Package rules** that prevent common mistakes:

- Use the `try: from jarvis_log_client` logging pattern
- Never raise from `run()` --- return error responses
- Use `JarvisStorage` for secrets and data, not raw database access
- Name shared directories `{package}_shared/` to avoid path collisions
- Put spoken output in `context_data["message"]`

## Effective Prompts

### Implementing a command

> "Implement the weather command. Use httpx to call the OpenWeatherMap current weather API. Accept city (required) and units (optional, default imperial). Return the temperature and conditions as a spoken sentence."

Claude will:

1. Read the stub in `commands/my_weather/command.py`
2. Implement `run()` with the API call
3. Update `required_secrets` with the API key
4. Update `parameters` with city and units
5. Write natural-language prompt examples
6. Run `jdt test .` to validate

### Adding a component to an existing package

> "Add a background agent that checks for severe weather alerts every 5 minutes and pushes a notification if there's a warning for the user's city."

Claude will:

1. Create `agents/weather_alerts/agent.py` with an `IJarvisAgent` implementation
2. Run `jdt manifest . --non-interactive` to update the manifest
3. Run `jdt test .` to validate the new component

### Fixing validation failures

> "Run jdt test and fix any failures."

Claude will:

1. Run `jdt test .`
2. Read the error messages
3. Fix the issues (wrong base class, missing property, dangerous import, etc.)
4. Re-run until all checks pass

### Deploying

> "Deploy this to my local node."

Claude runs `jdt deploy local .` and reports the result.

## Workflow with Claude Code

The most productive workflow uses Claude Code as the primary interface, with `jdt` as the validation backbone:

```
You describe what you want
         │
         ▼
Claude writes the implementation
         │
         ▼
Claude runs `jdt test .`
         │
    ┌────┴────┐
    │         │
  PASS      FAIL
    │         │
    ▼         ▼
 Deploy    Claude reads errors
    │      and fixes them
    ▼         │
  Done        └──► Re-run `jdt test .`
```

### Tips for working with Claude Code

1. **Start from a scaffold.** Always `jdt init` first. The `CLAUDE.md` gives Claude the context it needs, and the working stubs give it a valid starting point to iterate from.

2. **Let Claude run `jdt test`.** Rather than reviewing code line by line, let the validation pipeline catch issues. Claude can read the error output and fix problems faster than explaining them to you.

3. **Describe behavior, not implementation.** "Accept a city and return the forecast as a spoken sentence" is better than "Create a function that calls the API at this URL with these headers." Claude knows the SDK patterns.

4. **Use `jdt manifest` after adding secrets or dependencies.** Claude can run `jdt manifest . --non-interactive` to keep the manifest in sync with code changes.

5. **Chain commands.** Ask Claude to "test and deploy if it passes" --- it will run `jdt test . && jdt deploy local .` in one shot.

## Multi-Component Packages

Claude Code handles multi-component bundles well. The `CLAUDE.md` lists all component types, and Claude can work across files:

> "Create a Govee smart lights package with a voice command for control, a device protocol for LAN communication, and an agent that polls device states every 30 seconds."

Claude will scaffold all three components, implement each one, wire up shared state between the agent and protocol, and validate the full bundle.

## Forge Integration

The Jarvis Forge (AI package builder in the Pantry web UI) uses the same SDK context and validation pipeline as `jdt`. Packages built in Forge and packages built with Claude Code + `jdt` are fully interchangeable --- they use the same manifest format, the same validation rules, and deploy the same way.

The difference is workflow preference:

| | Claude Code + `jdt` | Forge |
|---|---|---|
| **Interface** | Terminal / IDE | Browser split-pane |
| **AI model** | Your Claude Code model | BYOK (6 models) |
| **Context** | Full codebase access | Single package scope |
| **Best for** | Complex packages, multi-repo work | Quick prototypes, one-off commands |
| **Publishing** | Manual GitHub push → Pantry submit | One-click GitHub publish |
