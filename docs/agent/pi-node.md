# Raspberry Pi node (preview)

!!! warning "Preview"
    The Raspberry Pi node is the newest part of the agent and is not at parity with the Python node yet (the setup hotspot and Pantry and Home Assistant packages, among others). The [Python voice node](../install/voice-node.md) is still the supported Pi node, and it works with Jarvis Automation.

The same `jarvis-agent` runs as a voice node on a Raspberry Pi with the ReSpeaker 2-mics HAT: the voice pipeline, the HAT's LEDs and its button. It needs 64-bit Raspberry Pi OS (arm64) and the ReSpeaker 2-mics HAT v2.0.

## Install it

Download `install-pi.sh` from the newest release on the [releases page](https://github.com/alexberardi/jarvis-server/releases), copy it to the Pi, and run it there:

```bash
sudo sh install-pi.sh                 # --user NAME (default pi), --version <tag>
/opt/jarvis-agent/jarvis-agent enroll --server <server> --room kitchen   # as the node's user
sudo sh install-pi.sh --activate      # make the Go node the one that runs (--deactivate goes back)
```

The script does the system setup the Python node's installer does (the HAT overlay, ALSA, PulseAudio, networking) and installs `jarvis-agent.service` turned off, since only one node may own the HAT. It can sit next to the Python node; `--activate` switches to the Go node and `--deactivate` goes back.

`enroll` shows a pairing code: approve it in the web app or the mobile app as for a computer ([Pairing](pairing.md)). Reboot when the script says so (after HAT or audio changes).

The design and build log is [go-pi-node.md](https://github.com/alexberardi/jarvis-server/blob/main/docs/agent/go-pi-node.md) in jarvis-server.
