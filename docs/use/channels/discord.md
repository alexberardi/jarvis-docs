# Discord

Talk to Jarvis from Discord: in a direct message with your own bot, or in one channel of your own server. This page takes you from nothing to a first answer. [Chat channels](index.md) explains what a channel is and what every channel can do.

Setting it up has three parts: make a bot in Discord, install the package on a node, then link your account.

!!! note "Before you start"
    - You need a Discord account, and a node that stays on (see [Chat channels](index.md)).
    - Steps 1 to 4 are done once, by a household **admin** or **power user**. Step 5 is for every member.
    - Treat the bot's token like a password. Enter it only in the Jarvis app.

## 1. Make a server for Jarvis

A bot can only message people it shares a server with, so Jarvis needs one, even if you only plan to use direct messages.

1. In Discord, choose **Add a Server**, then **Create My Own**. A private server for your household is enough.
2. Invite the household members who will use Jarvis.
3. Optional: create a text channel for Jarvis, for example `#jarvis`. Skip it if you only want direct messages.

## 2. Create the bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and choose **New Application**. Name it; the name is what people see in Discord.
2. Open the **Bot** tab and set these:

    | Setting | Set it to | Why |
    |---|---|---|
    | **Token** | **Reset Token**, then copy it | The package signs in with it. Discord shows it once. |
    | **Public Bot** | Off | Nobody else can add your bot to their server |
    | **Message Content Intent** | On | Without it the bot cannot read what people type, and never connects |

    Leave the other two intents off.

!!! warning "Message Content Intent is the step people miss"
    With it off, the `/jarvis` commands still appear in Discord, but every one answers "The application did not respond", because the bot never came online.

## 3. Invite the bot to your server

1. Open **OAuth2**, then **URL Generator**.
2. Under **Scopes**, tick `bot` and `applications.commands`.
3. Under **Bot Permissions**, tick:
    - View Channels
    - Send Messages
    - Create Public Threads
    - Send Messages in Threads
    - Read Message History
    - Add Reactions
4. Open the generated URL, pick your server and authorize.

The bot now appears in the server's member list, offline until step 4 is done.

## 4. Install the package and enter the token

1. In the Jarvis app, open the **Pantry** tab, find **Discord** and install it on the node that should run it.
2. Open the package's settings on that node and fill in:

    | Setting | What to enter |
    |---|---|
    | **Bot token** | The token from step 2 |
    | **Jarvis channel ID** | Optional: the one channel Jarvis answers in. Leave it empty for direct messages only. |

To get a channel's ID, turn on **Developer Mode** in Discord (**User Settings**, **Advanced**), then right-click the channel and choose **Copy Channel ID**.

Within a minute the bot shows as online in your server.

## 5. Link your account

Each person does this once.

1. In the Jarvis app, open **Settings** and find **Chat channels**. Discord should say **Running**.
2. Make a link code.
3. In Discord, type `/jarvis link` and enter the code.

Jarvis answers "Linked." Now send the bot a direct message, or write in the Jarvis channel.

## Using it

- **Direct messages** are one running conversation. `/jarvis new` starts a fresh one.
- **In the Jarvis channel**, each message you post gets a thread of its own, named after what you asked. Keep talking in the thread to continue that conversation.
- **Photos and voice messages** work in both places. See [what you can send](index.md#what-you-can-send).
- **While Jarvis works** you see a reaction on your message and the typing indicator, then a check mark when the answer is in. Someone who isn't linked sees none of this.

The commands are `/jarvis link`, `/jarvis new`, `/jarvis node`, `/jarvis notify` and `/jarvis status`. [Commands](index.md#commands) says what each does.
