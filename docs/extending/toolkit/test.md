# `jdt test` --- Validate a Package

Runs the full three-phase validation pipeline locally. This is the same pipeline that Pantry runs on submission, so passing locally guarantees your package will pass review.

## Usage

```bash
jdt test [path] [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `path` | No | Package directory (default: current directory) |

### Options

| Option | Description |
|--------|-------------|
| `-v`, `--verbose` | Show all check results, not just failures |
| `--install-deps` | Auto-install pip dependencies before import checks |

## Examples

```bash
jdt test                     # Test current directory
jdt test /path/to/package    # Test a specific package
jdt test . -v                # Verbose --- show passing checks too
jdt test . --install-deps    # Install missing pip packages first
```

## The Three Phases

### Phase 1: Manifest Validation

Checks `jarvis_package.yaml` for correctness:

- File exists and is valid YAML
- Schema version is present
- Version follows semver (`X.Y.Z`)
- Required fields: `name`, `description`, `version`
- Categories are from the valid set
- Component types are valid
- Component paths exist on disk

If the manifest fails, phases 2 and 3 are skipped.

### Phase 2: Static Analysis

AST-based analysis of each component's Python source:

**Structural checks:**

- Class inherits from the correct SDK base (e.g., `IJarvisCommand`)
- Required methods and properties are implemented

**Security checks:**

- No forbidden imports: `subprocess`, `os`, `shutil`, `ctypes`, `importlib`
- No dangerous calls: `eval()`, `exec()`, `os.system()`, `subprocess.run()`
- No raw database access: `sqlite3`, `sqlalchemy`, `psycopg2`
- No SQL mutation patterns in string literals

**Namespace checks:**

- Shared directories don't use generic names (`shared/`, `lib/`, `helpers/`) that would collide between packages on the node

### Phase 3: Import Checks

Actually imports and instantiates each component:

- Module imports without errors
- SDK subclass is found in the module
- Class instantiation succeeds
- Properties return correct types (`str`, `list`, etc.)
- For commands: `generate_prompt_examples()` and `generate_adapter_examples()` return lists

!!! tip "Use `--install-deps` if imports fail"
    If your package declares pip dependencies in the manifest, Phase 3 will fail if they aren't installed locally. Use `--install-deps` to auto-install them first.

## Output

**Passing:**

```
$ jdt test .
Validating manifest... OK
Static analysis...
Import checks...

PASS - 5/5 checks passed
```

**Failing:**

```
$ jdt test .
Validating manifest... OK
Static analysis...
  commands/my_cmd/command.py ... FAIL
    x Dangerous import: subprocess
Import checks...
  my_cmd import ... FAIL
    x Class does not inherit from IJarvisCommand

FAIL - 1/4 checks passed
```

## Exit Code

- `0` --- all checks passed
- `1` --- one or more checks failed

This makes `jdt test` usable in CI pipelines and pre-commit hooks.
