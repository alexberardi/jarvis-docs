# Why Jarvis?

## The Short Version

Jarvis is a voice assistant you own completely. It runs on your home network, your data never leaves your house, and you can teach it to do anything you want. Think of it as a private, hackable Alexa that you control from top to bottom.

---

## The Longer Version

### The Problem

Every mainstream voice assistant -- Alexa, Google Home, Siri -- works the same way: your voice goes to a corporate server, gets processed, and comes back. You bought the hardware, but the company decides what it does.

**They control what you can do with your own device.**

- **Someone is always listening.** Your voice data lives on servers you don't control. Amazon employees have [listened to Alexa recordings](https://www.theverge.com/2019/4/10/18305378/amazon-alexa-ai-voice-assistant-annotation-listen-recordings). Apple contractors [heard Siri conversations](https://www.theguardian.com/technology/2019/jul/26/apple-contractors-regularly-hear-confidential-details-on-siri-recordings) including medical details and private moments. This is the business model -- your voice is their training data.

- **They pick which devices work.** Want to connect a smart device? It needs to be "Works with Alexa" certified or support Apple HomeKit. That certification costs manufacturers money and limits your choices. A perfectly good WiFi lightbulb might be locked out because the company didn't pay for a partnership. You can't just connect to anything on your network -- you can only use what they've approved.

- **You can't customize it.** Want Alexa to check your home server's API? Query your own database? Run a custom script? You're limited to whatever "skills" the vendor publishes in their store -- and those skills have to follow their rules, their review process, and their terms of service. Your device, their permission.

- **Features disappear when they decide.** Google killed their entire smart home API and forced everyone to migrate. Amazon [removes Alexa features](https://arstechnica.com/gadgets/2023/09/amazon-hikes-alexa-powered-device-prices-as-ai-plans-falter/) and pushes subscriptions for things that used to be free. Apple limits Siri's capabilities to what fits their ecosystem strategy. You have no say and no recourse -- you don't own the software.

- **They use your data to sell you things.** Alexa suggests products to buy. Google uses your queries to refine ad targeting. These assistants aren't just helping you -- they're monetizing you. Every interaction is a data point in someone's revenue model.

- **They stop working without internet.** No WiFi? No assistant. Your "smart" speaker becomes a paperweight if your ISP has an outage or if the company's cloud servers go down -- which happens more often than you'd think.

### What Jarvis Does Differently

Jarvis runs entirely on hardware you own. A small Pi Zero with a microphone sits in your kitchen or office. When you speak, your voice travels across your home WiFi to a server in your closet (or just your laptop). Everything -- the speech recognition, the AI that understands what you asked, the text-to-speech that responds -- runs locally.

**Nothing leaves your network unless you want it to.**

### What Can It Do?

Out of the box:

- **Ask questions and have conversations** -- powered by an AI model running on your own hardware
- **Set timers, reminders, and alarms** -- "Remind me to check the oven in 20 minutes"
- **Control smart home devices** -- lights, thermostats, locks via Home Assistant, or write custom commands that talk directly to any device API on your network
- **Get weather, news, sports scores** -- installable from the community package store
- **Play music, check your calendar, send emails** -- all as add-on packages
- **Run multi-step routines** -- "Good morning" can turn on lights, read the weather, and check your calendar

### What Makes It Special?

**It remembers you.** Jarvis can identify who's speaking and remember your preferences. "I like my coffee black" -- it'll know that next time, and it knows it's *your* preference, not your partner's.

**It's extensible.** If you can write a few lines of Python, you can teach Jarvis anything. There's a single interface to implement, and the community [Pantry](../architecture/cloud.md#pantry-command-store) has a growing library of ready-made packages you can install with one click.

**Use it however you want.** Talk to a Pi Zero node on your counter. Text from the [mobile app](../mobile/index.md) on your phone. Chat from a [web browser](../services/admin.md) on your laptop. They all connect to the same backend -- same commands, same memories, same smart home controls.

**It runs on modest hardware.** The Pi Zero nodes cost about $50 each (board + mic + speaker). The server can be any computer with a decent GPU. Jarvis was developed and tested on a machine with a 3080 Ti and gets responsive voice interactions -- you don't need cutting-edge hardware.

### Do I Need to Be Technical?

**To install it?** No. The [setup wizard](installation.md) walks you through everything in a browser. Pick your services, download a model, create an account -- it handles Docker, databases, and networking for you.

**To use it day-to-day?** Absolutely not. It's a voice assistant. You talk to it.

**To extend it?** A little. Adding new commands requires basic Python. But the Pantry has pre-built packages for most common needs, and the [Forge](../architecture/cloud.md#forge) lets you describe what you want in plain English and generates the code for you.

### How Is This Different from Home Assistant?

Home Assistant is great at device control and automation. Jarvis is great at voice interaction and AI-powered conversation. They complement each other -- in fact, Jarvis has a [Home Assistant integration](../extending/devices/index.md) so you can control all your HA devices by voice through Jarvis.

Think of it this way: Home Assistant is your smart home's control panel. Jarvis is the voice you talk to.

### What Does It Cost?

The software is free and open source. Your costs are just hardware:

| What | Cost | Notes |
|------|------|-------|
| Pi Zero node (per room) | ~$50 | Pi Zero W + USB microphone + speaker |
| Mobile app | Free | iOS/Android -- voice and text from your phone |
| Web chat | Free | Browser-based, works from any device |
| Server | $0 - $500 | Any computer works; an old PC with a GPU is ideal |
| Electricity | ~$5-10/mo | Running a small server 24/7 |

No subscriptions. No cloud fees. No one selling your data.

### I'm Convinced. How Do I Start?

Head to the [Installation guide](installation.md). The one-liner gets you up and running in about 10 minutes:

```bash
curl -fsSL https://raw.githubusercontent.com/alexberardi/jarvis-admin/main/install.sh | sh
```
