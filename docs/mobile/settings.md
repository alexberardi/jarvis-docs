# Settings

Access Settings by tapping the gear icon in the Home screen header.

## Account

- Your display name, which you can edit.
- **Log Out**.
- **Danger Zone**: **Delete Account** permanently deletes your account and all its data. The app asks for your password to confirm.

## Household

Manage your household membership:

- **Switch households** --- Tap a household to make it active
- **Edit household** --- Admins and power users tap the pencil icon to rename, manage members, or configure household features
- **Join Another Household** --- Enter an **Invite Code** from that household's admin; the app shows which household you will join. Tap **Join**.
- **Create New Household** --- Enter a **Household name** and tap **Create**
- **Leave household** --- In **Edit household**, when you belong to more than one household

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

## Voice

- **Voice Profile**: enroll your voice so Jarvis recognizes you.
- **Command Feedback**: rate recent voice commands, which helps Jarvis learn your patterns.
- **Memories**: what Jarvis remembers about you; review, edit or forget it.
- **Phonebook**: businesses Jarvis can call, with numbers, notes and do-not-call.
- **Call details**: your details Jarvis can use on a call (name, callback number, insurance). Private ones are held back unless asked for.

## Appearance

Toggle between **Light**, **Dark**, and **System** themes.

## Chat

- **Auto-play responses** --- Automatically speak Jarvis responses aloud

## Security

### Biometric Login

Toggle biometric session restore under **Settings → Security**. The card appears only on devices with biometrics.

| Setting | Description |
|---------|-------------|
| **Biometric login** | When on, a cold-boot launch requires Face ID, Touch ID, or Android biometrics before restoring your session. When off, the password form is shown directly. |

Toggling re-keys the stored refresh token immediately — you do not need to log out and back in for the change to take effect.

**Scope:** only cold-boot session restore is gated. Background token refresh, device-control calls, and K2 node-encryption keys are never gated by biometrics and never prompt mid-session.

**Platform:** iOS uses Face ID or Touch ID via the Secure Enclave. Android biometric support requires an app build that includes the `USE_BIOMETRIC` permission; the enroll checkbox will not appear on older APKs.

## Privacy

- **Push notifications** --- When on, alerts are delivered through Expo's push service. Turn it off for a fully local experience; the app then can't receive alerts from outside your Wi-Fi.

## Connection

Shows whether the app is connected to a **Local** server (Jarvis running on your network) or **Cloud**, and the addresses it found from your server URL. **Re-check Connection** reconnects to your server URL and reloads those addresses; use it after changing Wi-Fi.

## Smart Home

- **Primary Node** --- the node that handles device discovery for your household. A computer running the desktop agent can't find smart-home devices and runs routines only while it is on.
- **Use External Devices** --- show devices from your device manager (read-only): live state from Home Assistant or another hub instead of Jarvis's local copy.

To connect Home Assistant, use **Set Up Smart Home** on the **Success!** screen at the end of adding a node; it opens **Smart Home Setup** with **Connect Home Assistant**.

## Config Service URL

The address of your Jarvis server, for example `http://192.168.1.100:7700`. It is required: the app doesn't search the network for it. Enter it and tap **Save & Connect**; **Clear server URL** removes it. Saving a new address logs you out and clears local data, so be ready to sign in again.
