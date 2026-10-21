# Blog

Notes on self-hosted voice, local LLMs, and how Jarvis is built — written for people who run their own infrastructure.

!!! note "Docker-stack releases (note added 21 October 2026)"
    These posts were written for the old Docker/microservice install, which is now retired. The 0.2.0 and 0.3.0 releases they announce are Docker-stack releases, not versions of Jarvis Automation, the single-binary server that replaced it. To install today, see [Install](../install/index.md).

---

## [Jarvis starts paying attention](jarvis-starts-paying-attention.md)

*<time datetime="2026-08-21">21 August 2026</time>* · Jarvis 0.3.0 stops only answering when spoken to and starts *noticing* — you heading out for an appointment, arriving home, a game ending — then reacts, quietly and on your terms. A "leave by 2:55" nudge that does the math on your node, presence that shares only home/away, plain-English automations, and a voice loop that talks back in about two seconds.

---

## [Jarvis picks up the phone](jarvis-picks-up-the-phone.md)

*<time datetime="2026-08-07">7 August 2026</time>* · Jarvis 0.2.0 can make real phone calls on your behalf — book a table, ask a shop if they've got the thing, call the vet. The hard part wasn't the phone; it was the manners. Plus errands you describe out loud, a scheduler, and a Jarvis that finally has a personality you get to pick.

---

## [Everything was green](everything-was-green.md)

*<time datetime="2026-07-13">13 July 2026</time>* · Three weeks before shipping, almost every serious bug had the same shape: a system reporting success while doing nothing. A `/health` returning 200 while every completion failed, a `destroy` that exited 0 and destroyed nothing, twenty-six passing tests over a function that always crashed — and what we built to stop believing our own green checks.

---

## [Self-hosted voice assistants in the LLM era](llm-era-voice-assistant.md)

*<time datetime="2026-06-24">24 June 2026</time>* · An honest look at the landscape — what Rhasspy, OVOS and Home Assistant Assist each actually do in 2026 — and what we built Jarvis to close: an assistant that knows *who* is talking, no outbound connections by default, and a package store for voice capabilities.
