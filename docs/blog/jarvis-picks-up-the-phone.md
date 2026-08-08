---
title: "Jarvis picks up the phone"
description: "Jarvis 0.2.0 can make real phone calls on your behalf, plan and schedule errands, and speak in a voice you actually chose — here's the fun stuff, and the decisions behind it."
---

# Jarvis picks up the phone

Every version so far, Jarvis has lived inside your house. It listens on a little Pi on the counter, it turns your lights off, it tells you the weather, it reminds you when the dog needs his medication. Useful. Bounded. Politely domestic.

**0.2.0 lets it out of the house.**

The headline feature of this release is that Jarvis can now **make phone calls for you** — call a restaurant to book a table, call a shop to ask if they have the thing, call the vet. And once we'd built the machinery to plan and carry out a real-world task with a stranger on the other end, a bunch of other things fell out of it: errands you can just describe out loud, a scheduler, and a Jarvis that finally has a personality you get to pick.

Let's get into it.

---

## "Can you call them for me?"

Here's the thing nobody tells you about giving a voice assistant a phone: the hard part isn't the phone. It's the manners.

The actual calling is a live loop — your words in, Jarvis's voice out, a real conversation with a real person at the pizza place. That part is *engineering*, and it's the kind of engineering we enjoy. But we spent most of the effort somewhere else entirely: making sure the thing behaves like a guest you'd be willing to send in your name.

So, the rules Jarvis follows on a call, none of which are optional:

- **It says it's an AI. Out loud. First.** The disclosure (and that the call may be recorded) is the very first thing spoken, and it is not skippable. If text-to-speech isn't available to say it, Jarvis doesn't dial. No exceptions, no clever workarounds.
- **It won't volunteer your secrets.** You can tell Jarvis things it's allowed to share *if asked* — a callback number, an insurance ID — and it will hand those over when the person asks, and never before. A guard inspects every sentence before it's spoken and fails closed. (An early version got a little too helpful with details nobody had asked for. It does not do that anymore.)
- **It won't pretend to be you**, and it won't pretend to *do* things. If the call needs a decision Jarvis can't make, it escalates instead of winging it. No "sure, let me just check on that" theater.
- **It knows when you're free.** Booking something? Jarvis pulls your real calendar availability into the call brief, so it's offering times you can actually make — not a 6am haircut because your morning happened to be empty.
- **A booking counts only when the business confirms it.** Not when Jarvis *thinks* it went well. The other side has to actually say yes.

You manage all of this from the app: a **phonebook** of who Jarvis is allowed to call, and a one-time **call-details** editor so you're not re-typing your name and number every time. When a call happens, it lands in your inbox as a card you can review, revise, or confirm — with the recording right there to play back.

We think this is the most exciting thing Jarvis has ever done. We also think the reason it's *okay* for it to do it is the boring list above. Both things are true.

---

## "Just handle it"

The phone stuff needed a brain that could take a fuzzy goal and turn it into a concrete plan. Once that brain existed, it turned out to be good at a lot more than calls.

Say what you want done — *"order more dog food and remind me Friday to check the mail"* — and Jarvis **plans it out over the commands your node actually has installed**, then shows you an editable card. You can run it, cancel it, tweak the goal and have it re-plan, or just talk to it: *"actually, make it Saturday."* The card updates in place.

Under the hood it's a durable, multi-step workflow engine that can **pause, ask, and re-plan from where it left off** — so a long errand that hits a fork doesn't fall on its face, it checks in. And you can **schedule** any of it: one-time or recurring, by voice, with a sensible default of 9am when you don't say a time. There's a new **Scheduled Errands** screen in the app to see what's queued and cancel anything you've changed your mind about.

It's the difference between an assistant that answers questions and one that *does the thing*.

---

## Give Jarvis a personality

For a long time Jarvis had exactly one voice: competent, faintly butler-ish. Fine. A little samey.

Now your household gets to choose. There's a **Voice** editor in settings — pick a starter (Warm & folksy, Terse, Dry & witty, or Classic Jarvis) or just write your own description of how you want it to talk. It threads through everything Jarvis says.

And in a genuinely fun bit of plumbing, the speech model can now **read the room** — an opt-in acoustic affect check picks up on the energy in your voice (are you stressed? excited?) and passes that along as a per-turn hint, so responses can land with the right tone instead of the same flat cheer every time. It's off by default and never touches the transcript, but flip it on and Jarvis gets a little more emotionally literate.

---

## The little things that make it feel faster

A release full of big features is nice, but the stuff you *feel* every day is latency. This round got a real scrub:

- Jarvis now **ends a conversation cleanly** when it knows you're done, instead of sitting there listening at you for four awkward seconds.
- The voice model uses native tool-calling and a warmed-up cache, shaving close to a second off every command that does something.
- Speech synthesis **streams sentence-by-sentence** now, so long answers start talking almost immediately instead of thinking in silence first.

And on the app side: **Face ID / Touch ID** sign-in, smoother sessions, device pairing straight through your node (HomeKit included), and over-the-air updates for your nodes you can enable from your pocket.

---

## Getting it

0.2.0 is a coordinated release — a new service (the phone gateway), new wiring, the works — so it's meant to be moved as a set rather than cherry-picked. Update from the admin dashboard the usual way, add the optional **phone gateway** service when you're ready to give Jarvis a phone number, and you're off.

A small honesty note, since it's on-brand for this blog: we're calling this **0.2.0**, and we mean the `0.`. It's a real, tested release we're proud of, and it's also early — we're pre-1.0 on purpose. Expect the occasional rough edge, tell us when you find one, and enjoy the part where your voice assistant offers to call the pizza place.

We built the machinery. Now go give it something to do.
