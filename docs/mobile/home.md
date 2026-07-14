# Home & Chat

The Home tab is the main chat interface for interacting with Jarvis. Type or speak commands, and Jarvis responds with structured data and natural language.

## Chat Interface

The chat shows a conversation thread with your messages on the right (purple) and Jarvis responses on the left (gray). Responses can include formatted text with bold, lists, and structured data.

### Quick Actions

When the conversation is empty, quick action chips appear with common commands. Tap any chip to send that command immediately. Available actions depend on which commands are installed on the selected node.

### Node Selector

The node selector at the top left shows which Pi Zero node is active. Tap it to switch between nodes in your household.

### Text Input

Type a message in the input field and tap the send arrow. Jarvis processes it through the command center, which routes it to the appropriate command on the selected node.

The composer (text field, microphone, and send button) stays disabled until the selected node is confirmed online in your household **and** its tools have finished loading. The placeholder text walks you through the states:

| Placeholder | Meaning |
|||
| *Select a node first* | No node selected yet |
| *Waiting for node…** | Node selected but not yet confirmed as an online member of this household |
| Loading tools…** | Node is online but tools haven't reported yet |
| *Message Jarvis...* | Ready to chat |

### Voice Input

Tap the microphone icon to record a voice message. The audio is transcribed by the Whisper service and processed as text.

### Auto-Play TTS

When enabled in Settings, Jarvis responses are automatically spoken aloud via the TTS service. A speaker icon appears on responses that have been played.

## Empty State

When no nodes are paired, the Home screen shows a welcome message with a prompt to add your first node.

## Tool Loading

The status chip below the node selector shows the current tool state:

- **Loading tools…** (spinner) --- the node is online but its tool list hasn't arrived yet. This is normal immediately after pairing: a freshly-provisioned node goes online before its command discovery finishes. The app polls in the background and updates automatically --- no app restart needed.
- **N tools loaded** --- tools are ready. Tap the chip to see the full tool list.

### Pull-to-Refresh

Pull down on the Home screen to refresh both the node list and the tool list. Useful if a node just came online or if you installed a new command and want to pick it up immediately.
