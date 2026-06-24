# Pantry

The Pantry is the community package store for Jarvis. It is where contributors publish commands, routines, and supporting components so that other installations can discover and install them. Each published package is a self-contained bundle: source code, a manifest describing what it provides, and any routines or system-package declarations it needs.

Before anything reaches the store, every submission runs through a validation pipeline. The pipeline performs static analysis of command source, manifest validation, repository-structure checks, routine (JSON component) checks, APT and post-install operation allow-list checks, and dependency/lockfile resolution. Each stage looks for problems that would make a package unsafe, unverifiable, or incompatible with the runtime.

When a check fails, the result is not a free-form error message. Every blocking failure (and some non-blocking warnings) is reported as a structured finding carrying a stable reason code. Those codes, what they mean, why we flag them, and how to fix them are documented on the [Rejection codes](rejections.md) page. If your submission was rejected and you followed a link here, start with the [Rejection codes](rejections.md) reference to find the specific code attached to your finding.
