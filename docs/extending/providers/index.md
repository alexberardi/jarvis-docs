# Providers

The Python node has pluggable providers for speech-to-text, text-to-speech and wake responses. Each is a small class: one or two methods.

!!! warning "Providers are not package components"
    Providers are built into the node. A package can't ship one: Pantry and `jdt` install commands, agents, device protocols and device managers, never providers. To add a provider you edit the node's source (`jarvis-node-setup`) on that Pi, and a node update replaces your edit. Providers exist only on the Python node; the desktop agent and the Go voice node don't load them.

## Provider types

| Provider type | Interface (`core/`) | Directory | Built in |
|---------------|---------------------|-----------|----------|
| Speech-to-text | `ijarvis_speech_to_text_provider.IJarvisSpeechToTextProvider` | `stt_providers/` | `jarvis-whisper-api`, `keyboard` |
| Text-to-speech | `ijarvis_text_to_speech_provider.IJarvisTextToSpeechProvider` | `tts_providers/` | `jarvis-tts-api`, `espeak` |
| Wake responses | `ijarvis_wake_response_provider.IJarvisWakeResponseProvider` | `wake_response_providers/` | `jarvis-tts-api`, `static` |

The names in the last column are each provider's `provider_name`.

## Configuration

The node's config file (`config.json`) picks one provider of each type by name:

```json
{
    "stt_provider": "jarvis-whisper-api",
    "tts_provider": "jarvis-tts-api",
    "wake_response_provider": "jarvis-tts-api"
}
```

At startup the node imports every module in the provider's directory, instantiates each subclass of the interface and keeps the one whose `provider_name` matches the config. A name that matches nothing raises `ValueError` ("STT provider '…' not found.") when the node first asks for that provider. `wake_response_provider` is optional; without it the node uses its bundled acknowledgments.

The `jarvis-*` providers send the work to your Jarvis Automation server (jarvisd), which transcribes and synthesises in-process.

## When to write a provider

**Speech-to-text:** a different transcription backend, such as a cloud speech API or a local model on the Pi.

**Text-to-speech:** a different voice engine, such as a cloud TTS API or system voices.

**Wake response:** a different acknowledgment after the wake word, such as time-of-day greetings or your own list of phrases.

## Guides

- [Speech-to-Text Providers](stt.md)
- [Text-to-Speech Providers](tts.md)
- [Wake Response Providers](wake-responses.md)
