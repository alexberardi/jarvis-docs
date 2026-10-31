# Updates and settings

## Updates

The agent updates itself to your server's version: when your server is upgraded, its computers follow (they check at start, when the server's version changes, and once a day). It installs only a release signed with the project's key, and if the new version doesn't come up within 2 minutes it goes back to the old one. The shield icon's menu shows the progress, such as "Updated to v0.2.0".

Self-update is on by default. The `auto_update` setting below turns it off; the agent then also refuses updates sent from Jarvis Automation.

`jarvis-agent update` does the same by hand. Two cases need you:

- **Linux, from the `.deb`:** if the update asks for it, run `jarvis-agent install` once, so the agent keeps a copy it can update.
- **macOS, as a standard user** who can't write to `/Applications`: install the new `.dmg` yourself.

## Settings

The setup page and the shield icon's menu set the common choices. All of them live in one file, `agent.json`, in the agent's config folder. Every key is optional: a missing key keeps the default.

```bash
jarvis-agent config show              # every setting and its value
jarvis-agent config path              # where the file is
jarvis-agent config set island false
jarvis-agent config unset island      # back to the default
jarvis-agent restart                  # the running agent reads the file again
```

| Key | Default | What it does |
|---|---|---|
| `voice` | on | Listen for "Hey Jarvis" (Linux, macOS, Windows) |
| `island` | on | Show the [island](voice.md#the-island) |
| `tray` | on | Show the shield icon and its menu |
| `confirm_dictation` | `submit` | Ask before [dictation](dictation.md) sends anything: `off`, `submit` or `all` |
| `browser` | on | Serve the [browser extension](browser.md) |
| `chimes` | on | Play the wake and error chimes |
| `voice_input`, `voice_output` | `default` | The microphone and the speaker |
| `wake_threshold` | `0.4` | The wake word fires above this score (0 to 1) |
| `auto_update` | on | Update to the server's version by itself, and accept updates sent from Jarvis Automation |
| `follow_up` | `3` | Seconds to listen for a follow-up without the wake word (0: off; at most 3) |
| `computer_control` | off | Let Jarvis use this computer ([in progress](index.md#in-progress)) |

`jarvis-agent config show` lists the rest: the Raspberry Pi node's LED settings and the finer voice timings.
