# Voice and the island

On Linux, macOS and Windows the agent listens for **"Hey Jarvis"**, records what you say next and plays Jarvis's answer, as a voice node does. Windows needs `v0.1.0-rc18.11` or later, and **Settings > Privacy & security > Microphone > Let desktop apps access your microphone** turned on; with it off, the agent hears only silence.

## Listening

Listening is on by default. Turn it on or off with **Listen for "Hey Jarvis"** on the [setup page](index.md#set-it-up) or with the toggle in the shield icon's menu. **Test my microphone** on the setup page checks that the agent hears you. On a Mac, listening needs the **Microphone** [permission](macos-permissions.md).

After a reply, Jarvis listens for a few seconds for a follow-up without the wake word (3 seconds by default). A chime plays when the wake word is heard and when something goes wrong.

The wake word's sensitivity, the follow-up window, the chimes and the microphone and speaker are [settings](updates-settings.md#settings) (`wake_threshold`, `follow_up`, `chimes`, `voice_input`, `voice_output`).

## The island

The island is a small pill at the top centre of the screen (under the notch on a Mac). It drops in when the wake word is heard, shows sound bars that follow your voice and then Jarvis's, pulses while Jarvis thinks, and counts down the follow-up window with a ring. It never takes focus or clicks and has no Dock or taskbar entry.

It shows on macOS and on Wayland desktops that support overlays (layer-shell), such as Hyprland and sway. Where the desktop can't show it (GNOME, X11, Windows for now), the agent runs without it. The `island` [setting](updates-settings.md#settings) turns it off.
