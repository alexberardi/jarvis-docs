# `jdt validate` --- Quick Manifest Check

Fast, lightweight validation that only checks the manifest file. No AST parsing, no imports, no Python execution. Use this for quick sanity checks while editing `jarvis_package.yaml`.

## Usage

```bash
jdt validate [path]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Package directory (default: current directory) |

## Examples

```bash
jdt validate              # Check current directory
jdt validate /path/to/pkg # Check a specific package
```

## What It Checks

- Manifest file exists (`jarvis_package.yaml`)
- Valid YAML syntax
- Required fields present: `name`, `description`, `version`
- Version follows semver (`X.Y.Z`)
- Component types are valid
- Component paths exist on disk
- Categories are from the valid set
- Secret scopes are valid

## Output

**Passing:**

```
$ jdt validate .
PASS — Manifest valid (2 component(s))
```

**Failing:**

```
$ jdt validate .
FAIL — Manifest validation failed:

  x version '1.0' is not valid semver (expected X.Y.Z)
  x component path 'commands/foo/command.py' does not exist
```

## When to Use `validate` vs `test`

| | `jdt validate` | `jdt test` |
|---|---|---|
| **Speed** | Instant | ~2 seconds |
| **Manifest** | Yes | Yes |
| **AST analysis** | No | Yes |
| **Import checks** | No | Yes |
| **Use case** | Quick feedback loop | Full pre-submission check |

Use `validate` while editing the manifest. Use `test` before deploying or submitting to Pantry.
