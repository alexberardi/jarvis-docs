# Settings

Access Settings by tapping the gear icon in the Home screen header.

## Account

Shows your username and provides a **Log Out** button.

## Household

Manage your household membership:

- **Switch households** --- Tap a household to make it active
- **Edit household** --- Tap the pencil icon to rename, manage members, or configure household features
- **Join another household** --- Enter a server URL and create an account to join
- **Create new household** --- Create a fresh household
- **Leave household** --- Available when you belong to multiple households

### Member Management (Admin)

Admins can manage household members:

- Change member roles (Member, Power User, Admin)
- Remove members from the household
- Create and revoke invite codes

### Web Search (Admin)

Household admins can control whether Jarvis is permitted to search the internet when answering questions. Open **Edit household** (pencil icon) to find the **Web Search** card.

| Setting | Description |
|---|---|
| **Use web search** | When enabled, Jarvis can fetch current events, prices, and recent news to supplement its answers. When off, Jarvis answers only from what it already knows — nothing leaves your network for search purposes. Default: off. |

!!! note
    Only household admins can toggle this setting. Members see the current state but cannot change it.

## Appearance

Toggle between **Light**, **Dark**, and **System** themes.

## Security

### Biometric Login

Toggle biometric session restore under **Settings → Security**.

| Setting | Description |
|---------|-------------|
| **Biometric Login** | When on, a cold-boot launch requires Face ID, Touch ID, or Android biometrics before restoring your session. When off, the password form is shown directly. |

Toggling re-keys the stored refresh token immediately — you do not need to log out and back in for the change to take effect.

**Scope:** only cold-boot session restore is gated. Background token refresh, device-control calls, and K2 node-encryption keys are never gated by biometrics and never prompt mid-session.

**Platform:** iOS uses Face ID or Touch ID via the Secure Enclave. Android biometric support requires an app build that includes the `USE_BIOMETRIC` permission; the enroll checkbox will not appear on older APKs.

## Chat

- **Auto-play responses** --- Automatically speak Jarvis responses via TTS

## Smart Home

Configure smart home integration:

- Select a primary node for device discovery
- Toggle external device protocols
- Connect to Home Assistant

## Connection

Shows whether the app is connected to a local or cloud Jarvis instance.
