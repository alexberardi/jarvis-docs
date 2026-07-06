# Pantry

The Pantry is the community package store for Jarvis. It is where contributors publish commands, routines, and supporting components so that other installations can discover and install them. Each published package is a self-contained bundle: source code, a manifest describing what it provides, and any routines or system-package declarations it needs.

Before anything reaches the store, every submission runs through a validation pipeline. The pipeline performs static analysis of command source, manifest validation, repository-structure checks, routine (JSON component) checks, APT and post-install operation allow-list checks, and dependency/lockfile resolution. Each stage looks for problems that would make a package unsafe, unverifiable, or incompatible with the runtime.

When a check fails, the result is not a free-form error message. Every blocking failure (and some non-blocking warnings) is reported as a structured finding carrying a stable reason code. Those codes, what they mean, why we flag them, and how to fix them are documented on the [Rejection codes](rejections.md) page. If your submission was rejected and you followed a link here, start with the [Rejection codes](rejections.md) reference to find the specific code attached to your finding.

## Install Pinning: Immutable Commit SHA, Not the Tag

When a node installs a command, the download endpoint hands it a fetch ref pinned to the **immutable commit SHA** that was validated at publish time, not the git tag. A tag is mutable — an author could force-repoint `v1.0.0` to an un-reviewed commit *after* the pipeline above approved it, and every node installing `v1.0.0` afterward would silently pull the un-reviewed code. Commit SHAs can't be forged the same way, so pinning to the SHA closes that gap.

- GitHub archive URLs (the node's primary fetch path) accept a full commit SHA, so the node downloads exactly the tree Pantry reviewed.
- The response also surfaces the pinned commit explicitly as `git_commit_sha`, for any client that wants to verify `HEAD` itself.
- `manifest.version` is unaffected and still drives version display — pinning the fetch ref by SHA doesn't change what version a node reports as installed.
- Grandfathered rows published before this change with no recorded SHA still fall back to the tag; rows with neither fall back to floating `main` until resubmitted.

The node's **primary** fetch path (GitHub archive download) already handled a SHA ref correctly with no code change. But the **git-clone fallback** (hit when the archive endpoint fails) did `git clone --branch <ref>` — which git rejects for a raw SHA — then silently retried **without** `--branch`, landing on the **mutable default branch**. That reopened the very TOCTOU the SHA pin is meant to close, any time the fallback path triggered. `jarvis-node-setup` now detects a commit-SHA ref and fetches that exact object directly (`git fetch --depth 1 origin <sha>` + `checkout FETCH_HEAD`), raising an install error instead of degrading to `main` if the fetch fails. Tag/branch refs keep the existing `clone --branch` behavior and its resilient fallback.
