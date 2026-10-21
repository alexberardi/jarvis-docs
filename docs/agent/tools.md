# What it can do

The agent gives Jarvis a set of tools for this computer. Jarvis picks one when what you ask needs it ("open Steam", "turn it down to 30", "close the Slack window"). The agent offers a tool only while this computer can do it: no screen reading where the desktop doesn't allow it, no browser tools without the [extension](browser.md). `jarvis-agent status` shows what works right now.

| Area | Tools | What you can ask |
|---|---|---|
| Apps and links | `desktop_open`, `desktop_list_apps` | "open Steam", "open github.com", "do I have Blender?" |
| Volume | `desktop_get_volume`, `desktop_set_volume` | "what's the volume?", "set the volume to 30" |
| Windows | `desktop_list_windows`, `desktop_focus_window`, `desktop_minimize_window`, `desktop_close_window` | "what's open?", "switch to Firefox", "minimise Slack" |
| Dictation and keys | `desktop_type_text`, `desktop_press_key`, `desktop_confirm` | "tell claude to run the tests", "press enter" ([Dictation](dictation.md)) |
| The screen | `desktop_read_screen` | "what does this error say?", "what's on my screen?" |
| The browser | `browser_list_tabs`, `browser_open`, `browser_navigate`, `browser_switch_tab`, `browser_close_tab`, `browser_read_page`, `browser_find`, `browser_fill`, `browser_click`, `browser_scroll`, `browser_media` | "close the YouTube tab", "fill in username abcde", "pause the video" ([Browser control](browser.md)) |

`desktop_open` opens web and mail links, and the apps installed on the computer by name. It never opens a file path or another kind of link, so a misheard command can't run a program you didn't name. `desktop_close_window` asks a window to close as its close button would; the app may ask to save, and nothing is force-quit.

Pantry packages run on the agent too: install one from the mobile app as you would on a voice node. See [Where your code runs](../extending/where-code-runs.md).

Computer control and recording macros are [in progress](index.md#in-progress).
