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

## Node Settings

From a node's detail screen you can:

- View installed commands and their settings
- Configure command secrets (API keys, credentials)
- Trigger device discovery
- View node status and connection info

## Voice Settings

Each node exposes a **Voice Settings** screen where you can tune wake-word detection and response behaviour. Tap **Save Changes** to persist settings to the node.

## Data Browser

Commands that store structured records (e.g. medication lists, shopping lists, reminders) expose a **Data Browser** accessible from the node's command list. The data browser supports listing, viewing, editing, deleting, and — for commands that opt in — **adding** records.

### Adding a Record

When a command supports record creation, the record list shows a **+** floating action button (FAB). Tapping it opens an **Add Record** form pre-seeded with type-appropriate defaults.

- Fields marked `create_only` (e.g. a medication's **Visible to** scope) appear editable on the add form but are read-only on the edit form — set them once at creation.
- Ownership is always stamped server-side from your authenticated identity; the form never asks for an owner field.
- Validation errors (e.g. "at least one dose time is required") are shown inline and the record is not saved until resolved.

### Time Array Fields

For fields that hold a list of times (e.g. `dose_times` on a medication), the add and edit forms render individual time rows with a native time picker. Tap a time chip to adjust it; tap the **×** to remove a row; tap **Add time** to append a new one.

### Command Authoring

To enable the **+** button for your own command, see [Data Browser Protocol](../extending/infrastructure/datastore.md#data-browser-protocol) — specifically `data_browser_supports_create` and `data_browser_create` in the [jarvis-command-sdk](../libraries/command-sdk.md#data-browser-hooks) docs.
