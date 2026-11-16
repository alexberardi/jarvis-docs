# Slack

Talk to Jarvis from Slack: in a direct message with your own Slack app, or in one channel of your workspace. This page takes you from nothing to a first answer. [Chat channels](index.md) explains what a channel is and what every channel can do.

Setting it up has three parts: make a Slack app, install the package on a node, then link your account.

!!! note "Before you start"
    - You need a Slack workspace where you may create and install apps, and a node that stays on (see [Chat channels](index.md)).
    - Steps 1 to 3 are done once, by a household **admin** or **power user**. Step 4 is for every member.
    - The app has **two** tokens. Treat both like passwords and enter them only in the Jarvis app.

## 1. Create the Slack app

The quick way is a manifest, which sets every option below in one step.

1. Open [api.slack.com/apps](https://api.slack.com/apps) and choose **Create New App**, then **From a manifest**.
2. Pick your workspace, choose **YAML** and paste this:

    ```yaml
    display_information:
      name: Jarvis
    features:
      app_home:
        messages_tab_enabled: true
        messages_tab_read_only_enabled: false
      bot_user:
        display_name: Jarvis
      slash_commands:
        - command: /jarvis
          description: Jarvis commands
          usage_hint: link CODE | new | node NAME | notify on|off | status
    oauth_config:
      scopes:
        bot:
          - chat:write
          - im:history
          - im:write
          - reactions:write
          - files:read
          - commands
          - channels:history
    settings:
      event_subscriptions:
        bot_events:
          - message.im
          - message.channels
      socket_mode_enabled: true
    ```

3. Review the summary and choose **Create**.

??? note "Setting it up by hand instead"
    Choose **From scratch**, then set each of these on the app's pages:

    | Page | What to set |
    |---|---|
    | **Socket Mode** | Turn it on |
    | **OAuth & Permissions**, Bot Token Scopes | `chat:write`, `im:history`, `im:write`, `reactions:write`, `files:read`, `commands`, `channels:history` |
    | **Event Subscriptions** | Turn events on; subscribe the bot to `message.im` and `message.channels` |
    | **Slash Commands** | Create `/jarvis` |
    | **App Home** | Turn the **Messages** tab on and allow people to send messages from it |

For a **private** channel, use `groups:history` and `message.groups` in place of `channels:history` and `message.channels`, or add them beside the public ones.

## 2. Get the two tokens

| Token | Where to get it | Starts with |
|---|---|---|
| **App token** | **Basic Information**, **App-Level Tokens**, **Generate Token and Scopes**. Add the `connections:write` scope. | `xapp-` |
| **Bot token** | **Install App**, **Install to Workspace**, then copy the **Bot User OAuth Token** | `xoxb-` |

The app token lets the node hold a connection to Slack, so nothing has to reach in to your network. The bot token lets it read and send messages.

## 3. Install the package and enter the tokens

1. In the Jarvis app, open the **Pantry** tab, find **Slack** and install it on the node that should run it.
2. Open the package's settings on that node and fill in:

    | Setting | What to enter |
    |---|---|
    | **Bot token** | The `xoxb-` token |
    | **App token** | The `xapp-` token |
    | **Jarvis channel ID** | Optional: the one channel Jarvis answers in. Leave it empty for direct messages only. |

To use a channel, invite the app to it (`/invite @Jarvis`), then open the channel's details in Slack: the channel ID is at the bottom.

## 4. Link your account

Each person does this once.

1. In the Jarvis app, open **Settings** and find **Chat channels**. Slack should say **Running**.
2. Make a link code.
3. In Slack, open a direct message with the Jarvis app and send `/jarvis link CODE`, with your code in place of `CODE`.

Jarvis answers "Linked." Now send the app a direct message, or write in the Jarvis channel.

## Using it

- **Direct messages** are one running conversation. `/jarvis new` starts a fresh one.
- **In the Jarvis channel**, Jarvis answers each message in a thread under it. Keep talking in the thread to continue that conversation.
- **Photos and voice clips** work in both places, from the desktop and phone apps. See [what you can send](index.md#what-you-can-send).
- **While Jarvis works** you see a reaction on your message, then a check mark when the answer is in. Someone who isn't linked sees none of this.

The commands are `/jarvis link CODE`, `/jarvis new`, `/jarvis node NAME`, `/jarvis notify on`, `/jarvis notify off` and `/jarvis status`. [Commands](index.md#commands) says what each does.

## If something is wrong

| What you see | What to do |
|---|---|
| `/jarvis` answers "dispatch_failed", or nothing | The app isn't connected. Check both tokens, that **Socket Mode** is on, and that the node is on. |
| The card says **Not running** | A token is missing or wrong. The package needs both. |
| "Sending messages to this app has been turned off" | Turn the **Messages** tab on under **App Home**, then reload Slack. |
| No answer in the channel, but direct messages work | Invite the app to the channel, check the **Jarvis channel ID**, and check the app has the history scope for that kind of channel (public or private). |
| Photos or voice clips are ignored | The app lacks the `files:read` scope. Add it, then reinstall the app to the workspace. |
| A change to scopes or events did nothing | Slack applies those only after **Reinstall to Workspace**. |
| "I only work in direct messages and in the Jarvis channel." | You ran a command in another channel. |

More causes that apply to every channel are in [Chat channels](index.md#if-something-is-wrong).
