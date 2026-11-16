# Chat channels

A chat channel lets the people in your household talk to Jarvis from a chat app they already use, at home or away, with no VPN and no port opened on your router. Jarvis answers in the same app: in a direct message, or in one channel you choose.

Two channels exist today:

| Channel | Set it up |
|---|---|
| **Discord** | [Discord](discord.md) |
| **Slack** | [Slack](slack.md) |

Each one is a package from the [Pantry](../../mobile/pantry.md). You create your own bot in the chat service, install the package on one of your nodes, and give it the bot's token. The bot is yours alone: nobody else's Jarvis uses it, and your messages go between the chat service and your own node.

!!! note "Before you start"
    - Chat channels need the first server and mobile app builds released after 15 November 2026.
    - The household's Pantry must be on (it is **off by default**; see [Pantry](../../pantry/index.md)).
    - You need a node that stays on: a computer running the [desktop agent](../../agent/index.md), or a [Raspberry Pi node](../../agent/pi-node.md). The channel works only while that node is running.
    - Installing the package takes a household **admin** or **power user**. After that, every member links their own account.

## How it works

1. **The package runs on one node.** It holds the bot's connection to the chat service. Nothing connects in to your network: the node connects out, the way a chat app on your phone does.
2. **Each person links their own account.** In the Jarvis app they make a one-time code and send it to the bot. From then on Jarvis knows that chat account is them: their memories, their calendar, their permissions.
3. **You message the bot.** Jarvis runs the request as it would from the mobile app and answers where you asked.
4. **Everyone else is ignored.** An account that isn't linked gets no reply, no reaction and no sign that a bot is listening.

A household runs each channel on **one node only**. Installing the same channel on a second node is refused, because two copies of one bot would both answer.

## Link your account

Every member does this once per channel, after the package is installed and running.

1. In the Jarvis app, open **Settings**. A **Chat channels** card lists each channel with **Running** or **Not running** beside it.
2. Make a link code for the channel. The code is eight characters, works once and lasts ten minutes.
3. In the chat app, send the code to the bot with the link command: `/jarvis link` in Discord, `/jarvis link CODE` in Slack.

The card then shows the channel as linked. **Unlink** on the same card removes the link; so does linking a different account.

If your household has several nodes, the card also asks which node Jarvis should **Answer through**. That node's tools and devices are the ones a chat message can reach.

## What you can send

| You send | Jarvis does |
|---|---|
| A message | Answers in text. In the Jarvis channel each message is answered in its own thread, and the thread is one conversation. |
| A photo | Looks at it and answers. Up to four photos per message, 10 MB together. |
| A voice clip | Transcribes it and answers in text, with what it heard quoted above the answer so you can spot a mishearing. Two minutes at most. |

Jarvis keeps a separate conversation for each person in each place: your direct messages are one, and each thread in the channel is another.

## Commands

Every channel has the same commands. Their answers are shown only to you.

| Command | What it does |
|---|---|
| `link` | Links this chat account with a code from the Jarvis app |
| `new` | Starts a fresh conversation in this place |
| `node` | Chooses the node Jarvis answers through, by name |
| `notify on` / `notify off` | Sends your reminders, alarms and timers to your direct messages, or stops |
| `status` | Shows how this account is linked |

## Reminders

Reminder messages are **off** until you turn them on, with `notify on` or the **Send me reminders, alarms and timers** switch on the app's card. Once on, a reminder, alarm or timer that fires for you also arrives as a direct message from the bot. Jarvis starts no other conversation on its own.

## Privacy

- Messages you send pass through the chat service (Discord or Slack) on their way to your node, as any message in that app does. Jarvis sends nothing else there.
- The bot's token is stored on the node that runs the package, with the node's other secrets. Never paste it into a chat.
- Replies never mention or ping anyone, whatever the text says.
