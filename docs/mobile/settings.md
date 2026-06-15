# Settings

Access Settings by tapping the gear icon in the Home screen header.

## Account

Shows your username and provides a **Log Out** button.

## Household

Manage your household membership:

- **Switch households** --- Tap a household to make it active
- **Edit household** --- Tap the pencil icon to rename, manage members, or create invite codes
- **Join another household** --- Enter an invite code to join
- **Create new household** --- Create a fresh household
- **Leave household** --- Available when you belong to multiple households

### Member Management (Admin)

Admins can manage household members:

- Change member roles (Member, Power User, Admin)
- Remove members from the household
- Create and revoke invite codes

## Appearance

Toggle between **Light**, **Dark**, and **System** themes.

## Chat

- **Auto-play responses** --- Automatically speak Jarvis responses via TTS

## Smart Home

Configure smart home integration:

- Select a primary node for device discovery
- Toggle external device protocols
- Connect to Home Assistant

## Connection

Shows whether the app is connected to a local or cloud Jarvis instance.

### Server URL

Use **Set server URL** (available on the Landing screen before login, and here after login) to pin the app to a specific Jarvis config-service URL.

**Pinned URL is authoritative.** When a URL is set, the app resolves exclusively against that server — it will not fall through to mDNS/LAN auto-discovery. If the pinned server is unreachable, the app surfaces an explicit error:

> Can't reach the server at `<url>`. Check the URL or your connection, or clear it to search your local network.

To return to automatic local-network discovery, clear the server URL field.
