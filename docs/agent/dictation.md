# Dictation

Dictation types what you say into the window in front or into an app you name ("tell claude to run the tests", "type hello in Notes"), and presses Enter, Escape, Tab or the arrows to answer dialogs ("press enter", "click OK"). Nothing is typed into a window the agent can't confirm has focus.

By default Jarvis asks before anything is sent ("Send … to Claude?"): before pressing Enter, a click or a fill that submits. The `confirm_dictation` [setting](updates-settings.md#settings) changes that: `off` never asks, `all` asks before every keystroke too.

Typing presses keys, as you would. In a terminal app with key bindings (Vim in normal mode, `less`, `htop`) they run as commands, so switch it to insert mode first.

On a Mac, dictation needs the **Accessibility** [permission](macos-permissions.md), and typing into a named app needs **Automation (System Events)**.

## Dictation on Linux

Dictation (typing what you say, "press enter", "click OK") works out of the box on Hyprland, sway and other wlroots compositors, and on X11.

**GNOME and KDE on Wayland** need a one-time permission. Click **Allow typing** on the setup page, or run:

```bash
jarvis-agent dictation allow
```

Your desktop asks once: choose **Allow** (it may say **Share**) and keep its "remember" option on. `jarvis-agent dictation status` shows the grant and `jarvis-agent dictation revoke` forgets it. On GNOME and KDE, Jarvis types into the window in front; it can't switch to an app you name first.

Reading the screen works on Hyprland and sway and needs `grim` installed. It isn't available on GNOME, KDE or X11 yet.
