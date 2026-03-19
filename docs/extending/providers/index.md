# Providers

Jarvis has pluggable providers for speech-to-text, text-to-speech, and wake responses. These are simpler than commands or agents --- typically one or two methods to implement.

Unlike commands and agents, providers are **not auto-discovered**. You specify which provider to use in your node's config file (`config.json`). But the implementation pattern is the same: subclass the ABC, implement the required methods, done.

## Provider Types

| Provider Type | Interface | Directory | Built-in Implementations |
|--------------|-----------|-----------|--------------------------|
| Speech-to-Text | `IJarvisSpeechToTextProvider` | `stt_providers/` | `JarvisWhisperClient`, `KeyboardProvider` |
| Text-to-Speech | `IJarvisTextToSpeechProvider` | `tts_providers/` | `JarvisTTS`, `EspeakTTS` |
| Wake Responses | `IJarvisWakeResponseProvider` | `wake_response_providers/` | `JarvisTTSWakeResponseProvider`, `StaticWakeResponseProvider` |

## Configuration

Providers are selected in the node config file:

```json
{
    "stt_provider": "jarvis_whisper",
    "tts_provider": "jarvis_tts",
    "wake_response_provider": "jarvis_tts_wake"
}
```

The node's initialization code instantiates the matching provider class. There is no discovery service scanning --- the mapping is explicit.

## When to Write a Provider

**STT provider** --- You want to use a different speech-to-text backend. Examples: local Whisper (without the Jarvis Whisper API), Google Cloud STT, Azure Speech, or a custom model.

**TTS provider** --- You want to use a different voice synthesis engine. Examples: Coqui TTS, Bark, a cloud TTS API, or system voices (macOS `say`, Windows SAPI).

**Wake response provider** --- You want to change what Jarvis says after hearing the wake word. Examples: time-aware greetings ("Good morning"), random responses from a custom list, or silence (no acknowledgment).

## Guides

- [Speech-to-Text Providers](stt.md)
- [Text-to-Speech Providers](tts.md)
- [Wake Response Providers](wake-responses.md)
