# Rejection codes

When a package is submitted to the Pantry it runs through a validation pipeline, and any blocking failure (plus some non-blocking warnings) is reported as a structured finding rather than a free-form message. Each finding carries a stable snake_case `reason_code`, a severity (`error` blocks publication; `warning` does not), and a link to the matching section below. A reason code identifies exactly why a rejection or warning was raised, so you can map it directly to a fix. Reason codes are append-only: they are never renamed or repurposed once published, because submitters and tooling rely on them as stable wire identifiers.

## Disallowed primitive in source {#static_analysis_disallowed_primitive}

**Reason code:** `static_analysis_disallowed_primitive` · **Severity:** error

### What this means

A command's Python source uses a dynamic-execution primitive such as `eval`, `exec`, `compile`, `__import__`, or `getattr`-style dynamic dispatch. These let code do things the analyzer cannot verify ahead of time.

### Why we flag it

Dynamic execution can sidestep every other static check and run arbitrary code at runtime, which is a direct security risk to the host installation.

### How to fix

Remove the dynamic primitive and call the target directly. Replace `eval`/`exec` with explicit logic, replace `getattr(obj, name)()` with a normal attribute access or an explicit dispatch table, and import modules with ordinary `import` statements.

## Raw database import {#static_analysis_raw_db_import}

**Reason code:** `static_analysis_raw_db_import` · **Severity:** error

### What this means

The command imports the datastore or database layer directly instead of going through the sanctioned command data-store API.

### Why we flag it

Direct datastore access bypasses the isolation and validation the data-store API enforces, letting a command read or corrupt data belonging to the platform or other commands.

### How to fix

Remove the direct import and use the command data-store API provided to your command. Persist and read state only through that API.

## Direct SQL mutation {#static_analysis_sql_mutation}

**Reason code:** `static_analysis_sql_mutation` · **Severity:** error

### What this means

The source contains a raw SQL mutation: an `INSERT`, `UPDATE`, `DELETE`, or DDL statement (such as `CREATE`/`DROP`/`ALTER`).

### Why we flag it

Raw SQL mutations bypass the data-store API's access controls and can damage shared schema or data, and they are a common vector for injection.

### How to fix

Remove raw SQL writes and perform all data changes through the command data-store API instead of issuing SQL directly.

## Cross-command access {#static_analysis_cross_command_access}

**Reason code:** `static_analysis_cross_command_access` · **Severity:** error

### What this means

The command reaches into another command's module or data instead of staying within its own boundary.

### Why we flag it

Commands must remain isolated so they can be installed, updated, and removed independently; cross-command access creates hidden coupling and can leak or corrupt another command's state.

### How to fix

Remove imports of, and references to, other commands' modules and data. If you need shared behavior, factor it into your own command or use a supported public interface.

## Shadows a built-in directory {#static_analysis_shadows_builtin_dir}

**Reason code:** `static_analysis_shadows_builtin_dir` · **Severity:** error

### What this means

A file or package in your submission has a name that collides with a reserved or built-in directory name.

### Why we flag it

Shadowing a reserved name can override platform internals at import time, producing unpredictable behavior or breaking the runtime.

### How to fix

Rename the offending file or package to something that does not collide with a reserved or built-in directory name, and update any imports that referenced it.

## Python syntax error {#static_analysis_syntax_error}

**Reason code:** `static_analysis_syntax_error` · **Severity:** error

### What this means

The analyzer could not parse a Python source file in your submission.

### Why we flag it

Source that does not parse cannot be analyzed for safety and cannot run, so it cannot be published.

### How to fix

Open the reported file, fix the syntax error, and confirm it parses cleanly (for example, run `python -m py_compile <file>`) before resubmitting.

## Missing command base class {#static_analysis_missing_base_class}

**Reason code:** `static_analysis_missing_base_class` · **Severity:** error

### What this means

A command class does not subclass the required command base class.

### Why we flag it

The base class defines the contract the runtime uses to load and invoke a command; without it the command cannot be registered or run safely.

### How to fix

Make your command class inherit directly from the required command base class and import it from its sanctioned location.

## Transitive base-class inheritance {#static_analysis_transitive_inheritance}

**Reason code:** `static_analysis_transitive_inheritance` · **Severity:** error

### What this means

Your command class only reaches the required base class transitively, through one or more intermediate classes, rather than inheriting from it directly.

### Why we flag it

The static analyzer cannot safely verify an indirect inheritance chain, so it cannot confirm the command implements the required contract.

### How to fix

Have your command class inherit directly from the required base class rather than through an intermediate subclass, so the inheritance is verifiable.

## Invalid semantic version {#manifest_bad_semver}

**Reason code:** `manifest_bad_semver` · **Severity:** error

### What this means

The `version` value in your manifest is not a valid semantic version.

### Why we flag it

The store relies on valid, ordered semantic versions to compare releases and resolve upgrades; an invalid version breaks ordering.

### How to fix

Use a valid `MAJOR.MINOR.PATCH` version like `1.2.0` in your manifest's `version` field.

## Missing required manifest field {#manifest_missing_required_field}

**Reason code:** `manifest_missing_required_field` · **Severity:** error

### What this means

A field that the manifest is required to define is absent.

### Why we flag it

Required fields carry information the store and runtime cannot operate without, so a missing one makes the package unusable.

### How to fix

Add the named required field to your manifest with a valid value, then resubmit. The finding names the specific field that is missing.

## Invalid manifest field type {#manifest_invalid_field_type}

**Reason code:** `manifest_invalid_field_type` · **Severity:** error

### What this means

A manifest field is present but has the wrong type (for example a string where a list or number is expected).

### Why we flag it

Fields of the wrong type cannot be parsed or used as intended and would fail unpredictably at runtime.

### How to fix

Correct the field to the expected type as named in the finding (for example, use a list instead of a single string), and resubmit.

## Unknown manifest category {#manifest_unknown_category}

**Reason code:** `manifest_unknown_category` · **Severity:** error

### What this means

The manifest declares a category that is not one of the recognized Pantry categories.

### Why we flag it

Categories drive discovery and grouping in the store; an unrecognized category cannot be placed and may indicate a typo.

### How to fix

Set the `category` field to one of the supported category values. Check for typos against the documented category list.

## Unknown parameter type {#manifest_unknown_param_type}

**Reason code:** `manifest_unknown_param_type` · **Severity:** error

### What this means

A command parameter in the manifest declares a type the platform does not recognize.

### Why we flag it

The runtime validates and coerces inputs by parameter type, so an unknown type cannot be processed.

### How to fix

Change the parameter's `type` to a supported parameter type, correcting any typos against the documented parameter types.

## Unknown secret scope {#manifest_unknown_secret_scope}

**Reason code:** `manifest_unknown_secret_scope` · **Severity:** error

### What this means

The manifest requests a secret using a scope that is not a recognized secret scope.

### Why we flag it

Secret scopes govern what credentials a command may access; an unknown scope cannot be granted and may signal an attempt to over-reach.

### How to fix

Use one of the supported secret scopes for each declared secret, and remove or correct any scope that is not recognized.

## Manifest parse error {#manifest_parse_error}

**Reason code:** `manifest_parse_error` · **Severity:** error

### What this means

The manifest file itself could not be parsed (for example, malformed YAML/JSON).

### Why we flag it

If the manifest cannot be parsed, none of its declarations can be read, so the package cannot be validated or installed.

### How to fix

Fix the syntax of the manifest file so it parses cleanly (check indentation, quoting, and brackets), then resubmit.

## Missing README {#repo_missing_readme}

**Reason code:** `repo_missing_readme` · **Severity:** warning

### What this means

The repository does not contain a README file.

### Why we flag it

A README helps other users understand what the package does and how to use it; its absence does not block publication but lowers quality.

### How to fix

Add a `README` (for example `README.md`) at the repository root describing the package and how to use it.

## Missing LICENSE {#repo_missing_license}

**Reason code:** `repo_missing_license` · **Severity:** error

### What this means

The repository does not contain a LICENSE file.

### Why we flag it

Without a license, others have no legal terms under which to use or redistribute the package, so it cannot be published to the store.

### How to fix

Add a `LICENSE` file at the repository root stating the license terms for your package, then resubmit.

## No components found {#repo_no_components_found}

**Reason code:** `repo_no_components_found` · **Severity:** error

### What this means

The validator found no installable components (such as commands or routines) in the repository.

### Why we flag it

A package with no components has nothing to install and would publish an empty entry.

### How to fix

Ensure your components are present and discoverable in the expected locations, and that the manifest references them. Resubmit once at least one valid component is found.

## Component file missing {#repo_component_file_missing}

**Reason code:** `repo_component_file_missing` · **Severity:** error

### What this means

The manifest references a component file that does not exist in the repository.

### Why we flag it

A declared component that has no file behind it cannot be installed and signals a broken or out-of-sync submission.

### How to fix

Add the missing file at the path the manifest references, or correct the path in the manifest to point at the existing file.

## Unknown component type {#repo_unknown_component_type}

**Reason code:** `repo_unknown_component_type` · **Severity:** error

### What this means

A component declares a type the platform does not recognize.

### Why we flag it

The store installs and runs each component according to its type, so an unknown type cannot be handled.

### How to fix

Set each component's type to one of the supported component types, fixing any typos against the documented component types.

## Routine missing steps {#routine_missing_steps}

**Reason code:** `routine_missing_steps` · **Severity:** error

### What this means

A routine component does not define any steps.

### Why we flag it

A routine with no steps does nothing when triggered and is almost certainly an authoring mistake.

### How to fix

Add a non-empty `steps` list to the routine, with at least one step that the routine should perform.

## Routine missing trigger phrases {#routine_missing_trigger_phrases}

**Reason code:** `routine_missing_trigger_phrases` · **Severity:** error

### What this means

A routine does not define any trigger phrases.

### Why we flag it

Without trigger phrases there is no way to invoke the routine, so it can never run.

### How to fix

Add one or more trigger phrases to the routine so it can be matched and invoked.

## Routine missing response instruction {#routine_missing_response_instruction}

**Reason code:** `routine_missing_response_instruction` · **Severity:** error

### What this means

A routine does not define a response instruction.

### Why we flag it

The response instruction tells the assistant how to respond when the routine runs; without it the routine has no defined output behavior.

### How to fix

Add the required response instruction field to the routine, describing how it should respond when triggered.

## Routine step missing command {#routine_step_missing_command}

**Reason code:** `routine_step_missing_command` · **Severity:** error

### What this means

A step in a routine does not specify the command it should run.

### Why we flag it

A step with no command cannot be executed, leaving the routine partially undefined.

### How to fix

Add the `command` field to each routine step, naming a valid command for that step to invoke.

## Routine has invalid JSON {#routine_invalid_json}

**Reason code:** `routine_invalid_json` · **Severity:** error

### What this means

A routine component file is not valid JSON and could not be parsed.

### Why we flag it

Routines are JSON components; if the JSON does not parse, the routine cannot be read or installed.

### How to fix

Fix the JSON syntax in the routine file (check commas, quoting, and braces) so it parses cleanly, then resubmit.

## APT package not on allow-list {#apt_package_not_on_allowlist}

**Reason code:** `apt_package_not_on_allowlist` · **Severity:** error

### What this means

The package declares an APT system package that is not on the Pantry allow-list.

### Why we flag it

System packages are installed with elevated privileges, so only vetted packages on the allow-list may be requested.

### How to fix

Remove the disallowed package, or request only allow-listed APT packages. If you need a package that is not allow-listed, propose it for review through the allow-list process.

## APT source not on allow-list {#apt_source_not_on_allowlist}

**Reason code:** `apt_source_not_on_allowlist` · **Severity:** error

### What this means

The package declares an APT source (repository) that is not on the Pantry allow-list.

### Why we flag it

Untrusted APT sources can serve arbitrary system packages, so only vetted sources may be added.

### How to fix

Remove the unapproved APT source, or use only allow-listed sources. To add a new source, submit it for review through the allow-list process.

## APT source mismatch {#apt_source_mismatch}

**Reason code:** `apt_source_mismatch` · **Severity:** error

### What this means

A declared APT source's key URL or repository line does not match the registered allow-list entry for that source.

### Why we flag it

Even an allow-listed source is only trusted with its exact registered key and repo line; a mismatch could point at a substituted or tampered repository.

### How to fix

Make your declared source's key URL and repository line match the registered allow-list entry exactly, then resubmit.

## Unknown post-install operation {#post_install_op_unknown_type}

**Reason code:** `post_install_op_unknown_type` · **Severity:** error

### What this means

A post-install operation declares an operation type the platform does not recognize.

### Why we flag it

Post-install operations run during installation; an unknown operation type cannot be executed safely or predictably.

### How to fix

Change the operation to one of the supported post-install operation types, correcting any typos against the documented operation types.

## Post-install operation missing target {#post_install_op_missing_target}

**Reason code:** `post_install_op_missing_target` · **Severity:** error

### What this means

A post-install operation does not specify the target it acts on.

### Why we flag it

Without a target the operation has nothing to act on and cannot be executed.

### How to fix

Add the required target field to the post-install operation, naming the resource or path it should operate on.

## Post-install operation not on allow-list {#post_install_op_not_on_allowlist}

**Reason code:** `post_install_op_not_on_allowlist` · **Severity:** error

### What this means

A post-install operation is not permitted by the Pantry allow-list.

### Why we flag it

Post-install operations can change the host system, so only vetted, allow-listed operations may run.

### How to fix

Remove the disallowed operation, or use only allow-listed post-install operations. To add a new operation, submit it for review through the allow-list process.

## Lockfile resolution failed {#lockfile_resolution_failed}

**Reason code:** `lockfile_resolution_failed` · **Severity:** error

### What this means

The validator could not resolve your package's dependencies into a lockfile.

### Why we flag it

A package whose dependencies cannot be resolved cannot be installed reproducibly, and an unresolvable dependency set often signals a conflict or a missing package.

### How to fix

Check your declared dependencies for conflicts, typos, or unavailable versions, resolve them so a lockfile can be produced, and resubmit.

## Resolved lockfile exceeds size cap {#resolved_lockfile_exceeds_size_cap}

**Reason code:** `resolved_lockfile_exceeds_size_cap` · **Severity:** error

### What this means

Dependency resolution succeeded, but the resulting lockfile is larger than the allowed size cap.

### Why we flag it

An oversized resolved dependency set usually means an unexpectedly large dependency tree, which increases install size, attack surface, and resolution risk.

### How to fix

Reduce your dependency footprint by removing or tightening unnecessary dependencies so the resolved lockfile fits within the size cap, then resubmit.
