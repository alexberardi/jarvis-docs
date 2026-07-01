---
title: "Self-hosted voice assistants in the LLM era"
description: "Why the old self-hosted voice options don't cut it in the LLM era — and how Jarvis closes the gap with speaker recognition, true zero-cloud, and an extensible command ecosystem."
---

# Self-hosted voice assistants in the LLM era: why the old options don't cut it anymore

Mycroft shut down in May 2023. That was supposed to be the moment the open-source voice assistant community rallied around something new.

Three years later, the options are mostly the same ones that existed before: Home Assistant Assist, OVOS (the Mycroft community fork), Rhasspy. They're all fine projects. But they were all designed for a world that no longer exists — a world before large language models changed what a voice assistant could actually do.

If you want a private, self-hosted voice assistant in 2026 that can hold a conversation, know who's talking, understand a question it's never been programmed to answer, and extend itself with new capabilities — the old options leave a real gap. This post is about what that gap is, and why we built Jarvis to close it.

---

## What changed when LLMs arrived

Before LLMs, a voice assistant worked like this: you said something, the system matched your words against a set of predefined intents ("turn on [device]", "set a timer for [duration]"), and ran the corresponding handler. If you said something it wasn't programmed to handle, it failed.

This worked well for home automation. It works poorly for anything else. "What was that movie with the guy from Breaking Bad?" is not an intent you can preprogram. Neither is "remind me to call the vet after I finish this meeting" or "what should I make for dinner with what's in my fridge?"

Rhasspy and OVOS are both intent-based systems. They're good at what they do — predictable phrase matching, low resource usage, excellent home automation integration. But intent matching is a ceiling. You can extend what phrases they recognize, but you can't teach them to reason.

Home Assistant Assist added Whisper for local STT and Piper for local TTS, which is genuinely great. But HA Assist is an add-on to a home automation platform. If you don't already run Home Assistant, you're installing an entire home automation system to get a voice interface. And even then, the LLM integration is limited — Assist routes recognized commands to HA entities, but it doesn't give you a general-purpose assistant backed by a model that can reason.

---

## The gap: a standalone, LLM-first, private voice assistant

What the self-hosted space has been missing since Mycroft is a project that starts from a different premise: *the LLM is the core, not an add-on*.

That means:

- The voice pipeline (STT → intent → TTS) routes through a real LLM, not a pattern matcher
- Commands are tools the LLM can call, not the entire routing system
- Unknown questions get answered, not failed
- The system can reason about context across a conversation

This is what Jarvis is built around. The architecture isn't "intent recognition with an optional LLM fallback." It's an LLM with a tool-calling pipeline that includes structured commands, device control, memories, and routines.

---

## What Jarvis actually does

A few things that don't exist anywhere else in the self-hosted space:

**Speaker recognition.** Jarvis knows who's talking. Each household member gets a voice profile, and the system routes accordingly — different preferences, different command context, different response style. You say "play my playlist" and it knows which playlist is yours. Your kids ask for a bedtime story and they get one. This is table-stakes for a household assistant and basically absent from every other self-hosted option.

**True zero-cloud when you want it.** Most "private" voice projects still phone home for STT or TTS. Jarvis runs whisper.cpp locally for speech recognition, Kokoro for synthesis, and your choice of LLM — llama.cpp, vLLM, or MLX on your own hardware. Nothing leaves your network unless you explicitly point it at a cloud API. (You can, if you want — Claude, GPT, Ollama all work. It's your call, not ours.)

**A command ecosystem that actually extends.** 30+ capabilities ship built-in: weather, timers, web search, calendar, email, Spotify, Pandora, Rotten Tomatoes, ESPN scores, drive time, Philips Hue, Govee, Nest, Schlage, SimpliSafe — the full list is in the [Pantry community store](https://pantry.jarvisautomation.io). Each one is a standalone package you can install, modify, or replace.

**The AI Forge.** This is the part nothing else has. Describe what you want in plain text — "a command that checks the price of any stock ticker using the Polygon API" — and the Forge generates a complete, tested Jarvis package: Python implementation, manifest, README, and sandbox test run. One click to publish to the community store. It's backed by the command SDK, which decorates every interface with metadata so the LLM always knows the current interface contracts without any manual prompt engineering.

**Pi Zero voice nodes.** A ~$15 Raspberry Pi Zero 2 W with a mic/speaker HAT becomes a room-scale voice endpoint. Headless-provisioned from the mobile app. No screen, no fuss.

---

## What it's not

Jarvis is not a turnkey consumer product. You need Docker, a server to run it on (8 GB RAM minimum for cloud LLM, more for local inference), and some comfort navigating a setup wizard. The self-hosted crowd can handle this. Your parents probably can't — yet.

It's also not a home automation platform. If you want to build automations in a visual editor and happen to want voice control, Home Assistant is probably the right choice. If you want a voice-first assistant that also controls your home, Jarvis is the right choice.

---

## Getting started

The fastest path is the one-line installer:

<!-- jarvis:install-cmd:start -->
```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-admin/main/install.sh | sh
```
<!-- jarvis:install-cmd:end -->

Open `http://localhost:7711` and the setup wizard handles the rest — hardware detection, service selection, account creation, model download.

Docs are at [docs.jarvisautomation.dev](https://docs.jarvisautomation.dev). The community package store is at [pantry.jarvisautomation.io](https://pantry.jarvisautomation.io). Source is at [github.com/alexberardi/jarvis](https://github.com/alexberardi/jarvis), MIT licensed.

If you're coming from Mycroft or OVOS and want to understand the differences in architecture, the [command SDK docs](https://docs.jarvisautomation.dev/extending/commands/) are a good starting point — the interface will look familiar, but the routing layer is completely different.

---

*Questions, feedback, or "you got X wrong about Rhasspy" — find me in the comments. I'd rather have this be accurate than defensive.*
