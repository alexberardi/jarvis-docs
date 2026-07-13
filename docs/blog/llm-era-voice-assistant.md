---
title: "Self-hosted voice assistants in the LLM era"
description: "What we built with Jarvis and why: speaker recognition, an assistant-first architecture, a package store for voice capabilities, and no outbound connections by default."
---

# Self-hosted voice assistants in the LLM era: what we built, and why

Mycroft shut down in May 2023. That was supposed to be the moment the open-source voice assistant community rallied around something new.

Three years on, the landscape is healthier than that sounds — but there's still a gap, and it isn't the one people usually name. This post is about what that gap actually is, what we built to close it, and the parts where the honest answer is "somebody else already does this."

---

## Let's get the landscape right first

A lot of "why our voice assistant is different" posts start by claiming everything else is a dumb pattern matcher. That was true a few years ago. It isn't anymore, and pretending otherwise is a good way to lose the audience in the first paragraph.

**Rhasspy and OVOS are intent-based.** You define phrases, they match them, they run a handler. They're good at that — predictable, fast, light on resources. But intent matching is a ceiling: you can extend the phrases they recognize, you can't teach them to reason.

**Home Assistant Assist is not.** HA has shipped [LLM conversation agents with tool calling](https://developers.home-assistant.io/docs/core/llm/) since 2024.6. Custom intents are exposed to the model *as tools*, and its "prefer handling commands locally" setting runs the fast deterministic matcher first and falls back to the LLM when nothing matches. If you've read a post claiming HA Assist can only handle preprogrammed sentences, it was out of date.

So "we use an LLM and they don't" is not our differentiator, and we're not going to pretend it is. **Jarvis also runs a fast pre-route pass before falling back to the model** — that's a good design, and HA arrived at the same one.

The gap is somewhere else.

---

## The gap: nobody knows who's talking

Every self-hosted voice assistant we could find answers the question *"what was said?"* — and then stops.

None of them answer *"who said it?"*

That sounds like a detail until you live with a household assistant. "Remind me to take my meds" is a different reminder depending on who says it. "Play my playlist" is a different playlist. "What's on my calendar" is a different calendar. Without speaker identity, a household assistant is really a single-user assistant that several people take turns using, and every piece of personal context has to be re-stated out loud.

Jarvis identifies the speaker from their voice and scopes everything to that person: memories, preferences, command context, and what they're allowed to do. Enrolled voice profiles live per household member. It is, as far as we can tell, the only self-hosted option that does this — HA Assist and Rhasspy both have it as an open feature request rather than a shipped feature.

This is the thing we'd point at first.

---

## The second gap: assistant-first, not home-automation-first

Home Assistant is a home automation platform with an excellent voice interface attached. Its LLM API is oriented around the home: entities, areas, intents.

Jarvis is an *assistant* that happens to control your home. Memory, routines, timers, reminders, email, calendar, drive time, medication tracking, web search — the smart home is one capability among many, not the center of gravity. That's a different product, not a better Home Assistant, and the distinction matters when you're deciding which one you want.

To be explicit about it: **we're not trying to replace Home Assistant.** There's a Jarvis package for HA, and if you already run it, Jarvis talks to your existing devices through it. Jarvis also ships its own device layer — Hue, Kasa, LIFX, Nest, Govee, Schlage, SimpliSafe, Z-Wave, HomeKit, Home Connect, Resideo, Apple TV — so HA is optional in either direction. Run both, run one, run neither.

---

## What Jarvis actually does

**Speaker recognition.** Covered above. It's the headline.

**A voice pipeline that's local end to end.** Wake word on the node, speech-to-text via whisper.cpp, inference via llama.cpp / vLLM / MLX, speech synthesis via Piper or Kokoro. All of it on your hardware.

**No outbound connections by default — including update checks.** This is the part self-hosters tend to care about and nobody advertises. Jarvis makes no calls off your network unless you turn them on. The update checker is opt-in and off by default: with it off, the server never contacts GitHub at all. Turn it on and updates are cryptographically signed (minisign) and verified before anything is executed. You can point the LLM proxy at a cloud API — Claude, GPT, Ollama all work — and if you do, your transcripts go to that provider. That's a real trade, and it should be your call, made deliberately, rather than a default you discover later.

**A package store for voice capabilities.** The core ships with conversation, memories, timers, reminders, routines, web search, smart-home control, and node administration. Another **25+ packages** are one click away in the [Pantry](https://pantry.jarvisautomation.io): weather, news, sports, music (Spotify, Pandora, Music Assistant), calendar, email, drive time, movies, and the device integrations above. Each is a standalone repo you can fork, modify, or replace. Adding your own means implementing one Python interface.

There's plenty of prior art for distributing *integrations* — HACS does it well. We're not aware of anyone distributing *voice capabilities* with a sandboxed container-test pipeline in front of them, which is what the Pantry submission flow runs before anything is published.

**The AI Forge (experimental).** Describe a capability in plain English — "a command that checks the price of any stock ticker" — and the Forge generates a complete package: implementation, manifest, README, license. It runs static analysis and an automated safety review, then a full containerized test run before it can be published. Under the hood the SDK introspects its own interfaces to build the model's prompt, so the contracts it generates against are always current instead of drifting from a hand-maintained prompt.

Treat this as an experiment, not a promise. It works, it's genuinely useful, and it will also sometimes hand you code you need to fix. As with any package store — AUR, npm, PyPI — we screen and sandbox, but installing a community package is ultimately a decision you're making.

**Cheap voice nodes.** A Raspberry Pi Zero 2 W with a ReSpeaker 2-Mics HAT and a small speaker is roughly $15–25 per room, headless-provisioned from the mobile app. Pi 4 and Pi 5 work too.

**Multi-household.** One install serves more than one household — each gets isolated voice profiles, devices, and routines. Useful if you're hosting for family or roommates and don't want to run separate hardware per group.

---

## What it's not

**Not turnkey.** You need Docker and a machine to run it on. The setup wizard handles the rest — hardware detection, service selection, model download — and a fresh install takes about six minutes on a Mac mini including pulling an LLM and a Whisper model. But it's still a self-hosted stack, and it expects a self-hoster.

**Not a home automation platform.** If what you want is a visual automation editor and a decade of device integrations, that's Home Assistant, and it's very good at it. Use both.

**Not finished.** It's a beta. The Forge is experimental. Some rough edges are documented, some aren't yet.

---

## Getting started

<!-- jarvis:install-cmd:start -->
```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-admin/main/install.sh | sh
```
<!-- jarvis:install-cmd:end -->

Open `http://localhost:7711` and the wizard takes it from there. If piping curl into a shell isn't your thing — entirely fair — the [installation guide](https://docs.jarvisautomation.dev/getting-started/installation/) covers the manual path.

Docs: [docs.jarvisautomation.dev](https://docs.jarvisautomation.dev). Package store: [pantry.jarvisautomation.io](https://pantry.jarvisautomation.io). Source: [github.com/alexberardi/jarvis](https://github.com/alexberardi/jarvis).

Licensing is split: the server-side services are **AGPL-3.0**, and the SDK, client libraries, command/device packages, and mobile apps are **Apache-2.0** — so you can build and ship your own commands and integrations without copyleft obligations. No paywalled features, no open-core holdbacks.

---

*If I've got something wrong about Rhasspy, OVOS, or Home Assistant — and the HA ecosystem in particular moves fast — tell me and I'll fix the post. I'd rather this be accurate than flattering.*
