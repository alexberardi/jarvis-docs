---
title: "Everything was green"
description: "Three weeks before shipping a self-hosted voice assistant, almost every serious bug we found had the same shape: a system reporting success while doing nothing at all."
---

# Everything was green

In the three weeks before we shipped Jarvis, we found a lot of bugs. Almost all of the serious ones had the same shape, and it took an embarrassingly long time to notice.

None of them were crashes. Nothing threw. CI was green, health checks were green, containers were healthy, the UI said the operation succeeded. And underneath, the system was doing nothing at all.

Here is what that looked like, over and over.

---

## `/health` said 200 while every completion failed

The LLM proxy is two processes: an API server and a model service that owns the weights. The model service loaded both models at **module import**. When the background 32B model failed to load, the import crashed before uvicorn could bind its port. The launcher backgrounded it with `&` and nothing supervised it, so it stayed dead.

And the API's `/health` returned **HTTP 200** with `"degraded"` in the *body*. Docker's healthcheck only fails on non-2xx. So the container reported healthy, continuously, while 100% of chat completions 500'd — for seven hours.

Three separate mistakes had to line up: an eager import-time load with no fault isolation, a backgrounded process with no supervisor, and a health endpoint whose *status code* didn't reflect its own body. Any one of them alone is survivable. Together they produce a service that is confidently, persistently wrong.

The fix wasn't just "load lazily." It was per-slot fault isolation (a failed model marks that slot `failed` and 503s, rather than killing the process), a retry loop with exponential cooldown, a supervised launcher that respawns the model service, and — most importantly — **status codes that mean something**. `503` when the live slot is dead. `200 "initializing"` during a slow load, but only inside a grace window. If the healthcheck can't distinguish "loading a 32B model" from "the model service has been dead for an hour," it isn't a healthcheck. It's a liveness probe for the HTTP framework.

## `docker compose pull` did nothing, and that was our idea

We pinned every first-party image by `@sha256` digest. Textbook supply-chain hygiene: a GHCR tag can be overwritten, a digest can't.

Then `docker compose pull` became **inert** — by design, and we hadn't thought it through. A stale digest map pinned GPU services to older builds. Twice, a routine recreation silently downgraded a box: on one, speech-to-text went from ~90ms to ~16 seconds, because the pins pulled a CPU build of Whisper onto a GPU host.

It got worse. The admin's *reconcile* generator reconstructs its state from `.env` — and nothing recorded the GPU backend choices. So every regenerate silently reverted Whisper to the CPU image and stripped TTS's GPU passthrough. We shipped a "reconcile" button that quietly downgraded your hardware.

We reversed it. Floating tags are the default again; digest pinning is an opt-in checkbox. The reasoning, written down at the time:

> Default pins made `docker compose pull` inert and caused both silent-downgrade incidents; a stuck non-expert deletes the product.

This is the counter-lesson to everything else in this post, and it's worth sitting with. **Fail-closed is not automatically correct.** The safest-sounding default produced two outages that a laxer default would not have. Security postures have to be evaluated against the failure modes they actually create, not the ones they theoretically prevent.

The same lesson landed in auth. Refresh-token rotation revoked the *entire token family* on any replay of a rotated token — the textbook response to token theft. But the grace-window cache was an in-process dict, so a **process restart guaranteed a cache miss**, which looked exactly like a replay. Deploying jarvis-auth silently logged out every live session. The security-textbook answer is right only when replay is rare; here, the dominant cause of replay was our own restart semantics.

## The build flag became a no-op, and it looked like a network bug

The ROCm image built llama.cpp with `-DGGML_HIPBLAS=on`. Upstream had **renamed** that flag to `GGML_HIP`, with no compatibility alias. CMake ignores unknown `-D` variables **without error**.

So `:latest-rocm` shipped as a CPU-only build. The symptom, three layers downstream: `httpx.ReadTimeout` on completions. It looked like a networking problem. It was a build flag that had silently become a no-op months earlier.

You cannot unit-test your way to that. The image builds. The container starts. Inference *works* — it just runs at about one token per second on hardware that should do sixty.

## So we started asserting on what ggml actually did

This is the piece I'm proudest of, and it exists specifically because of the bug above.

Every signal we had — containers up, `/health` green, compose valid, GHCR tag exists — is **identical** whether inference runs on the GPU or silently falls back to CPU. There was no way to tell the difference from the outside. So we stopped trying to.

The GPU end-to-end lane rents a real GPU from the Vast.ai spot marketplace, provisions it, generates the *actual* compose file the installer ships, brings the stack up **remotely over `DOCKER_HOST=ssh://`**, tunnels the ports back, and re-runs the unchanged CPU test suite against `localhost`. The CI runner stays the brain; the rented box is a disposable Docker daemon.

Then it does the part that matters. It greps the container logs for ggml's backend-init markers, and for this:

```
offloaded (\d+)/\d+ layers to GPU
```

and asserts **N > 0**.

A green `/health` with zero layers offloaded is exactly the `:latest-rocm` bug, and now it fails the build. It also does a real chat completion against the local GGUF, and a TTS→Whisper round trip: synthesize speech, transcribe it back, assert the words survive. A full audio pipeline test, in CI, with no microphone.

A detail that only shows up when you actually run this: llama-cpp-python **suppresses those log lines unless verbose is on**. The first run had a passing chat completion and total silence from the markers. The test that exists to catch silent fallback almost silently fell back.

## The harness caught something on its first real outing

A seed migration had inserted a global `model.main.backend = VLLM` row. Settings resolve DB → env → default, so that row **silently overrode** the `JARVIS_MODEL_BACKEND=GGUF` the installer's compose sets. On the GGUF images, the model service booted vLLM against a GGUF file, the engine crashed, the port never bound, and chat 500'd — behind a green container.

It was found by the new GPU lane, on a rented RTX 3090, not by a human. A settings-precedence rule turned a *seed row* into a config landmine that no unit test could see, because no unit test runs the real install.

## "Destroy" exited 0 and destroyed nothing

The GPU lane rents real hardware, so it has to give it back.

`vastai destroy instance` **prompts interactively**. In CI the prompt gets no answer, defaults to *no* — and the CLI **still exits 0**. Our "Destroy instance" step was green every single night while the instances kept billing. Twenty-nine leaked instances before anyone noticed the account draining.

The naive fix — check the exit code — is precisely the thing that had failed. So the rewrite treats the CLI as untrustworthy end to end: feed `y` on stdin, then **verify the instance is actually gone** by polling for it, retry, and raise if it survives. (With a wrinkle: slow hosts take over a minute to reap a destroyed contract, which produced *false* "it survived!" alarms. So: a three-minute verification window.) Instance creation had the same disease — `create` can exit 0 with empty stdout while the instance *is* created — so the run label became the source of truth instead of parsed output.

And then the part that actually fixes the class of bug: a final **clean gate** that turns the job red if the run left anything alive.

> A green job must *mean* a clean account.

That sentence is the whole post, really. A green check is only worth what it asserts.

*(A footnote with a nice shape: the machine that reaps leaked instances is now itself broken — Vast deprecated the API version it queries, so it lists nothing, reaps nothing, and reports "no live instances" regardless. The janitor is currently a system that reports success while doing nothing. We're aware of the irony.)*

## `create_all()` creates tables. It does not alter them.

One service wasn't running Alembic migrations. It called `Base.metadata.create_all()`, which creates missing tables — and **never ALTERs existing ones**.

So a migration that added a column shipped inside the image and never reached the database. `/services` started 500ing **fleet-wide**. The install harness stayed green throughout, because it only probed a shallow `/health` endpoint that never touches the DB.

The test we added doesn't check that the service responds. It asks the database, in-container, **what migration revision it is actually at**, and asserts it equals head. For every service that ships migrations.

The fix had a trap in it, too. You can't simply add `alembic upgrade head` — legacy databases built by `create_all()` already have every table but an *empty* `alembic_version`, so `upgrade head` would try to CREATE what already exists. They have to be **stamped** at the right revision first, and the right revision depends on whether that one column happens to be present. The upgrade path for the boxes that already exist is always more interesting than the one for a fresh install.

## The tests were guarding the bug

A provisioned node whose WiFi was slow to join at boot would wait 85 seconds for the command center, conclude it had never been set up, and enter WiFi **access-point mode** — which stops NetworkManager permanently. It stranded itself, in a basement, requiring a physical power-cycle. Twice in two days.

The root cause is a single conflated question: `is_provisioned()` treated *"the command center is unreachable"* as *"I have never been set up."*

There was a safety net — a watcher that was supposed to detect AP mode and recover. It probed the command center **by hostname**. But the AP's own captive DNS resolves *every* hostname to the node itself. The watcher was **structurally incapable of ever succeeding**. It had no tests.

And the provisioning logic *did* have tests. From the punchlist, written during the incident:

> the AP-trap had tests asserting the bug as correct.

That is the most uncomfortable sentence in this project's history, and I think it's the most useful one. A test suite doesn't encode truth. It encodes what someone believed when they wrote it. Green means "consistent with my previous assumptions," which is exactly the thing you need to doubt when the system is lying to you.

## Twenty-six passing tests over a function that always crashed

The mobile app's Argon2 implementation declared a 64-byte buffer and then wrote 72 bytes into it — an 8-byte stack overflow that trips the stack canary and aborts the process on **every single hash**. Password-protected key backup and import had been crashing, deterministically, since the feature shipped.

Twenty-six Jest tests covered it. All green. Jest **mocks the native crypto module**.

It was caught by a new end-to-end flow that drives the *real* native path — provision, back up with a password, copy, re-import — which crashed on its first run.

## A voice assistant that reports healthy and cannot hear you

The wake-word engine downloads its models into its own site-packages directory. The CI tarball's bundled virtualenv doesn't contain them, and rebuilding the venv wipes them. So **every update lost the wake models**. Model autodownload had been made opt-in and defaulted off. The listener raised, the fallback needed a TTY that doesn't exist under systemd, and the voice loop exited permanently.

MQTT: connected. Heartbeats: green. Tools: registered. `/health`: fine.

The node was deaf. It took out the kitchen unit for a day, monitoring-green the entire time.

---

## What we actually changed

Not "write more tests." We had tests. The Argon2 function had twenty-six of them.

**Test the artifact, not the repository.** The install harness stands up the *exact* compose file the installer generates, on a clean runner, from the real GHCR images. Not a dev-mode approximation. Every service repo fires the harness on push to `main`, and a dispatched run switches to the `dev` image track so it tests *that service's* fresh build. A commit that breaks the install is caught in minutes.

**Assert against the running system, not the thing you generated.** When we fixed an unauthenticated Loki (bound to `0.0.0.0`, holding every voice transcript — found the day before launch), the unit test asserted the emitted compose *string*. The e2e test `docker inspect`s the **live container's port bindings**. Only one of those two tests could have caught it if the generator were right and the runtime were wrong.

**Assert on the mechanism, not the outcome.** "Inference returned 200" and "the GPU did the work" are different claims. Only one of them is what you're actually paying for.

**Make green mean something.** The clean gate exists so that a passing job *asserts* the account is clean. Not "no errors were raised" — an actual, verified claim about the world.

**And know when fail-closed is wrong.** Digest pinning and whole-family token revocation are both textbook-correct and both caused outages that laxer defaults would not have. The question is never "is this the secure option." It's "what does this do on the worst day of a stranger's install."

---

The thread running through all of it is the same. A health check that returns 200 tells you the HTTP framework is alive. A green CI job tells you nothing raised. A passing test tells you the code agrees with what you believed when you wrote it.

None of those are the system working. They're just the system not complaining — and by the end, the bugs I was most afraid of weren't the ones that crashed. They were the ones that reported success.
