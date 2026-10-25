# Mobile app

The Jarvis Automation app (iOS and Android) connects to your server, so you can talk to Jarvis, manage devices and routines, and set up voice nodes. Install the server first and finish its [setup wizard](setup-wizard.md).

Jarvis Automation is a **pre-release** (release candidate rc18.5). Server builds are on the [releases page](https://github.com/alexberardi/jarvis-server/releases); each one is marked *Pre-release*, so open the newest and look under **Assets**.

## Get the app

- iPhone and iPad: [Jarvis Automation on the App Store](https://apps.apple.com/app/id6760924901)
- Android: [Jarvis Automation on Google Play](https://play.google.com/store/apps/details?id=com.jarvis.nodemobile)

## Connect the app to your server

The app needs one address, your server's: `http://<server>:7700`, where `<server>` is the IP address or hostname of the machine running the server.

1. Open the app and tap **Set Server URL**.
2. Enter `http://<server>:7700` (for example `http://192.168.1.100:7700`) and tap **Save**.
3. Tap **Log In** with the account you made in the setup wizard, or **Create Account**.

The app does not search the network for the server; it uses the address you entered, and nothing else. To change it, tap the address on the first screen, or go to **Settings → Config Service URL**.

## Next

- **Add a voice node:** tap **Add Node**; see [Voice node](voice-node.md).
- **Learn the app:** [Mobile App](../mobile/index.md) describes each tab.

## If the app can't reach the server

Check that the phone is on the same network as the server, then run `jarvisd doctor` on the server. It checks that nodes and phones can reach it; `sudo jarvisd doctor --fix` opens the firewall if that is what is in the way.
