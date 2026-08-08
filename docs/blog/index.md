# Blog

Notes on self-hosted voice, local LLMs, and how Jarvis is built — written for people who run their own infrastructure.

---

## [Jarvis picks up the phone](jarvis-picks-up-the-phone.md)

Jarvis 0.2.0 can make real phone calls on your behalf — book a table, ask a shop if they've got the thing, call the vet. The hard part wasn't the phone; it was the manners. Plus errands you describe out loud, a scheduler, and a Jarvis that finally has a personality you get to pick.

---

## [Everything was green](everything-was-green.md)

Three weeks before shipping, almost every serious bug had the same shape: a system reporting success while doing nothing. A `/health` returning 200 while every completion failed, a `destroy` that exited 0 and destroyed nothing, twenty-six passing tests over a function that always crashed — and what we built to stop believing our own green checks.

---

## [Self-hosted voice assistants in the LLM era](llm-era-voice-assistant.md)

An honest look at the landscape — what Rhasspy, OVOS and Home Assistant Assist each actually do in 2026 — and what we built Jarvis to close: an assistant that knows *who* is talking, no outbound connections by default, and a package store for voice capabilities.
