# Speech-to-Text Providers

A speech-to-text (STT) provider turns the audio the node recorded after the wake word into text.

!!! note "Built into the node"
    Providers are not package components: Pantry and `jdt` can't install one. You add a provider by editing the node's source (`jarvis-node-setup`). See [Providers](index.md).

## Interface reference

`core/ijarvis_speech_to_text_provider.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TranscriptionResult:
    text: str
    speaker_user_id: int | None = None      # who spoke, when the provider can tell
    speaker_confidence: float = 0.0
    segments: list[dict[str, Any]] = field(default_factory=list)  # t0_ms, t1_ms, text
    affect: dict[str, Any] | None = None    # opaque tone read, passed on to the server


class IJarvisSpeechToTextProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The name the node config selects, e.g. 'jarvis-whisper-api'."""

    @abstractmethod
    def transcribe(self, audio_path: str) -> Optional[str]:
        """Transcribe the WAV file at audio_path. None on failure."""

    def transcribe_with_speaker(
        self,
        audio_path: str,
        *,
        speaker_audio_path: Optional[str] = None,
    ) -> TranscriptionResult:
        """Text plus speaker identity. The default wraps transcribe()."""
        text = self.transcribe(audio_path)
        return TranscriptionResult(text=text or "")
```

`transcribe` is the only method you must write. Override `transcribe_with_speaker` if your backend can tell household members apart; `speaker_audio_path`, when given, is a longer clip (wake word plus command) for the speaker pass only.

## Built-in implementations

### `jarvis-whisper-api` (JarvisWhisperClient)

The default. It uploads the audio to your Jarvis Automation server with `POST /api/v0/media/whisper/transcribe` (multipart, field `file`, plus `speaker_audio` and `conversation_id` when it has them), authenticated as the node. jarvisd transcribes in-process with whisper.cpp and, when the household has turned speaker identification on, matches the voice against enrolled voice profiles.

```json
{ "stt_provider": "jarvis-whisper-api" }
```

### `keyboard` (KeyboardProvider)

Ignores the audio and reads a line from the terminal (`You: `). For development without a microphone.

```json
{ "stt_provider": "keyboard" }
```

## Writing a custom provider

An example that sends the audio to OpenAI's transcription API. Save it as `stt_providers/openai_whisper_provider.py` in the node's checkout:

```python
from typing import Optional

import requests

from core.ijarvis_speech_to_text_provider import IJarvisSpeechToTextProvider
from services.secret_service import get_secret_value


class OpenAIWhisperProvider(IJarvisSpeechToTextProvider):
    @property
    def provider_name(self) -> str:
        return "openai_whisper"

    def transcribe(self, audio_path: str) -> Optional[str]:
        api_key = get_secret_value("OPENAI_API_KEY", "integration")
        if not api_key:
            return None
        try:
            with open(audio_path, "rb") as f:
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": ("audio.wav", f, "audio/wav")},
                    data={"model": "whisper-1"},
                    timeout=30,
                )
        except requests.RequestException:
            return None
        if response.status_code != 200:
            return None
        return response.json().get("text")
```

Then:

1. Store the key on the node: `python -c 'from services.secret_service import set_secret; set_secret("OPENAI_API_KEY", "sk-…", "integration")'` from the node's directory (or any other way you put secrets in its store).
2. Set `"stt_provider": "openai_whisper"` in the node's `config.json`.
3. Restart the node. Providers are loaded once.

The node instantiates every provider class it finds with no arguments, so keep `__init__` cheap and argument-free, and read secrets when you need them.

## Audio

The provider gets the path of a WAV file the node recorded and wrote to disk. Read it, don't delete it: the node manages its own recording files.
