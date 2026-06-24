# Nodes

The Nodes tab manages your Pi Zero voice nodes --- the physical devices that capture voice commands.

## Node List

Each node card shows:

- Room name
- Node ID
- Operating mode (brief/full)

Tap a node to view its detail screen with settings, installed commands, and status.

## Adding a Node

Tap **Add Node** to start the provisioning flow:

1. **Scan** --- The app scans for nearby Jarvis nodes broadcasting a WiFi access point
2. **Connect** --- Connect to the node's AP network
3. **Configure** --- Enter your home WiFi credentials
4. **Register** --- The node registers with the command center

!!! tip
    For development, you can use **Import Key** (top right) to manually pair a node by pasting its K2 encryption key.

## K2 Encryption Key

Every node has a **K2** key --- an AES-256 key generated during provisioning and stored on your device. K2 encrypts the settings sync channel between the mobile app and the node; the command center transports the encrypted blob but cannot read it.

### Backing Up K2

After a successful provisioning, the **Success** screen offers a **Back Up Encryption Key** button. Two backup modes are available:

| Mode | Protection |
|------|------------|
| **Plain** | The raw key is encoded as a QR code. Fast, but anyone who scans it gains full access. |
| **Password-protected** | The key is encrypted with Argon2id + AES-256-GCM before encoding. You must supply the same password on import. |

!!! warning
    Keep a backup of your K2 key. If you lose your device without a backup, you cannot restore your node's settings sync channel.

### Importing K2

To import a key from a backup QR code, tap **Import Key** (key icon, top-right of the Nodes list):

1. Scan the QR code with the camera.
2. For a **password-protected** backup, enter the password when prompted --- the app decrypts the key locally using Argon2id + AES-256-GCM.
3. On success, the node is re-paired to your device.

## Node Settings

From a node's detail screen you can:

- View installed commands and their settings
- Configure command secrets (API keys, credentials)
- Trigger device discovery
- View node status and connection info
