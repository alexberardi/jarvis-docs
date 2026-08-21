---
title: "Jarvis starts paying attention"
description: "Jarvis 0.3.0 stops only answering when spoken to and starts noticing — you heading out for an appointment, arriving home, a game ending — then reacts, quietly and on your terms. Plus a voice loop that talks back in about two seconds."
---

# Jarvis starts paying attention

Every version of Jarvis so far has been a very good listener with one small limitation: it only ever heard you when you talked to it. You said "Hey Jarvis," it woke up, it did the thing, it went back to sleep. A butler who's polite, capable, and — let's be honest — a little oblivious. It has no idea you're about to be late for the dentist unless you stop and ask.

**0.3.0 is the release where Jarvis starts to notice.**

The idea underneath it is simple: things are always happening in your home. You leave. You come back. An appointment creeps up on the calendar. Your team's game ends. In 0.3.0 those moments become **signals** — little notes about what's going on right now — and Jarvis can finally do something with them. Sometimes it just quietly keeps them in mind. Sometimes it slides a "want me to handle this?" card into your pocket. And sometimes, when you've told it to, it just takes care of it.

Where 0.2.0 taught Jarvis to *act* on the world, 0.3.0 teaches it to *pay attention* to it. Let's get into the fun stuff.

---

## "You should leave by 2:55"

Here's the moment that made all of this worth building.

It's 2:40. You have a dentist appointment at 3:30, across town. Your old assistant would happily remind you *at* 3:30 that you have a 3:30 appointment — thanks, very helpful. The new one looks at the appointment, checks what traffic actually looks like right now, does the arithmetic, and quietly sets a reminder: **leave by 2:55.**

No one had to ask. And it fires *once* — this is a helpful nudge, not a nag.

The part we're quietly proud of: it does this **without an AI guessing in the loop**. The drive-time lookup and the "when do I need to leave" math happen deterministically, right on your node — which also means your home address and your map keys never leave the house to make it work. It's the boring, dependable kind of smart. The kind you can actually trust with your morning.

---

## It knows when you're home (and only that)

A lot of the nicer tricks — reminding you to lock up as you head out, only piping up when someone's actually around — need Jarvis to know something it never used to: are you home or not?

So your phone can now be that sensor. Turn it on, and it draws a quiet geofence around home and tells Jarvis one of exactly two things: *home* or *away*. That's it. **Your actual location never leaves your phone** — not the coordinates, not a breadcrumb trail, nothing but "home / away" crosses the wire. It works even when the app is closed, and you get a little "welcome home" / "see you later" notification if you want one, plus a live status in the app so you can see what it thinks.

We spent real care here, because "my assistant knows when I'm home" is exactly the kind of sentence that should make you raise an eyebrow. The answer to the eyebrow is: it's opt-in, it's the coarsest possible signal, and the precise part stays with you.

---

## "When I leave, lock the front door"

Once Jarvis can notice things, the obvious question is: can I just *tell* it what to do about them? Yes — in plain English.

There's a new screen in the app that lists the signals your Jarvis can see, and next to each one you write an instruction the way you'd say it to a person: *"When I leave home, lock the front door."* *"When I get home, turn on the porch light."* Jarvis reads that when the moment comes and works out what to do.

And you decide how much rope it gets, per rule. Flip a switch: **Automatic** means it just does it. **Ask first** means it sends you a tap-to-confirm card before acting. Lock the door on your way out? Sure, automatic. Anything with more consequence? Make it ask. The safe default is always the cautious one.

---

## "Want me to…?"

Not everything should happen on its own, and Jarvis knows it. The other half of paying attention is knowing when to *offer* instead of act.

So there's a new kind of gentle suggestion in your inbox: a tap-to-confirm card. An appointment email lands, and instead of doing anything sneaky, Jarvis quietly asks: **"Want me to add this to your calendar?"** — with the event pre-filled and the date and time right there to nudge before you say yes. One tap and it's on your calendar. No tap and nothing happens. And if you never want that particular nudge again, there's a **"never suggest this"** button that means it.

Under the hood this is a general thing, not a one-off: any of Jarvis's background helpers can offer up an action as a card, and *nothing* can fire without your tap. Suggestions are cheap; actions are yours.

---

## The little things that make it feel faster — and calmer

Big features are fun to announce, but the thing you *feel* every day is the little moment of silence after you stop talking. This round we went after it hard.

- **Jarvis talks back in about two seconds.** From the instant you stop speaking to the first word out of the speaker is now roughly two seconds — trimmed prompts, a warmed-up cache, and moving all the background thinking off the voice path so it's not fighting your actual question for the GPU.
- **"Hey Jarvis" now works over music.** Playing something on the node? Instead of going deaf, it ducks the music for a beat, listens on a music-tuned profile, and cancels out its own audio so it can still hear you over the song.
- **It stopped answering conversations that weren't for it.** If you've ever had a kitchen speaker cheerfully chime in on a chat it was never part of — yeah. A stack of fixes now lets it tell "Hey Jarvis, set a timer" apart from two people talking near it, and back off gracefully when a wake wasn't really meant for it.

And a couple of quieter honesty fixes we think matter more than they sound:

- Telling Jarvis *"I gave the dog his medication"* now actually **logs the dose**, instead of it warmly agreeing and silently recording nothing. (This one we're a little sheepish about. It's fixed.)
- Jarvis's memory no longer **learns from its own guesses** — it remembers what *you* said, not what it once claimed, and it won't quietly decide your cat is a family member.

---

## Getting it

0.3.0 is a coordinated release. The "noticing" machinery is wired across the brain, the app, the nodes, and the developer kit, so it's meant to move as a set rather than cherry-picked — update from the admin dashboard the usual way and it all comes along.

The usual honesty note, because it's on-brand for this blog: this is **0.3.0**, and we mean the `0.`. It's real, it's tested, and it's also early on purpose — we're pre-1.0 and enjoying it. The proactive side ships deliberately shy: it asks before it acts, it stays off until you turn it on, and the private things stay private. Expect a rough edge here and there, tell us when you hit one.

0.2.0 taught Jarvis to do things. 0.3.0 taught it to notice when they need doing — and to ask first. Go live your afternoon; it's paying attention so you don't have to.
