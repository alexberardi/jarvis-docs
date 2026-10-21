# Your First Command

You have installed the server and finished the [setup wizard](../install/setup-wizard.md). This page checks that the server is up, adds a voice node, and sends Jarvis its first request.

`<host>` below is the machine the server runs on, or `localhost` on that machine.

## 1. Check the server

### In the admin

Open `http://<host>:7710/admin/dashboard` and sign in with the account you made in the wizard. The **Dashboard** shows the server (**System**), its **Health check**, the **Models** it runs and its **Nodes**. Each model you picked in the wizard should show as installed; a large one may still be downloading.

### In a terminal

On the server:

```bash
jarvisd service status    # is the service running, and does it answer?
jarvisd doctor            # can phones, nodes and other computers reach it?
```

`jarvisd doctor` prints one line per check with its fix; [The jarvisd command](../operate/cli.md) explains both commands, and [Troubleshooting](../troubleshooting/index.md#start-with-jarvisd-doctor) each check.

To ask the server directly:

```bash
curl -s http://<host>:7700/health             # {"status":"ok"}
curl -s http://<host>:7700/services/health    # every part of the server, and whether it answers
```

The server is one program, so there is one log for all of it: see [Read the log](../troubleshooting/index.md#read-the-log), or the admin's **Logs** page.

## 2. Chat from a browser

The quickest first command needs no hardware. Open the web app's **Chat**:

```text
http://<host>:7710/chat
```

Type a request, such as "what is 5 plus 3", and press Enter. Any member of the household can sign in here, not only the admin. The chat goes through the same steps as a voice request, minus the speech, so it is a good way to check the server before you set up audio.

## 3. Add a voice node

Voice nodes are added from the [mobile app](../install/mobile-app.md), not from the server:

1. Install the node software on the Pi: [Voice node](../install/voice-node.md).
2. In the app, set your server's address (`http://<host>:7700`) and sign in.
3. Tap **Add Node** and follow the steps. The app joins the node's Wi-Fi hotspot, gives it your Wi-Fi and the server's address, and the node joins your household.

The new node shows on the admin's **Nodes** page and in the app. [Provisioning](../clients/provisioning.md) walks through each step.

## 4. Say your first command

Say "Hey Jarvis", wait for the node to show it is listening, then "what is 5 plus 3". The node sends what you said to the server, and the answer comes back as speech.

Inside the server, the request goes through speech-to-text, the language model, which picks the `calculate` command, the command itself, and text-to-speech. [Voice pipeline](../architecture/voice-pipeline.md) describes each step.

## 5. Add commands and their keys

Jarvis ships with built-in commands (timers, reminders, lists, jokes and more; see the [home page](../index.md#built-in-commands)). Others, such as weather, news or email, are packages you install from the [Pantry](../mobile/pantry.md) in the mobile app.

Some commands need an API key or a sign-in. Set them in the mobile app: open the node on the **Nodes** tab, then its settings, where each command lists the secrets it needs. See [Nodes](../mobile/nodes.md#node-settings).

## Something not working?

- **The server doesn't answer:** run `jarvisd service status` and `jarvisd doctor`, then [read the log](../troubleshooting/index.md#read-the-log).
- **Phones or the node can't connect:** usually the firewall; see [Phones and nodes can't connect](../troubleshooting/index.md#phones-and-nodes-cant-connect-but-it-works-on-the-server).
- **No answer from the language model:** check on the admin's **Models** page that a language model is installed and in use.
- **Everything else:** [Troubleshooting](../troubleshooting/index.md).

## Next steps

- [Configure the server: the jarvisd command and its env file](../operate/cli.md#the-data-directory-and-the-env-file)
- [Build your own command](../commands/tutorial-simple.md)
- [Browse the Pantry for community commands](../mobile/pantry.md)
