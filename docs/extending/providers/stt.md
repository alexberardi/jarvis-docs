# Speech-to-Text Providers

An STT provider implements `IJarvisSpeechToTextProvider` to convert audio files into text. The node calls the provider after recording audio from the microphone.

## Interface Reference

```python
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class TranscriptionResult:
    text: str                           # The transcribed text
    speaker_user_id: int | None         # Identified user ID (if speaker ID is enabled)
    speaker_confidence: float           # Confidence score for speaker identification (0.0-1.0)

class IJarvisSpeechToTextProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique name for this provider. Example: 'jarvis_whisper'."""
        ...

    @abstractmethod
    def transcribe(self, audio_path: str) -> Optional[str]:
        """Transcribe an audio file to text. Returns None if transcription fails."""
        ...

    def transcribe_with_speaker(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio and identify the speaker.

        Default implementation wraps transcribe() with no speaker identification.
        Override this to add speaker ID support.
        """
        text = self.transcribe(audio_path)
        return TranscriptionResult(
            text=text or "",
            speaker_user_id=None,
            speaker_confidence=0.0,
        )
```

The `transcribe_with_speaker` method has a default implementation that delegates to `transcribe()`. You only need to override it if your STT backend supports speaker identification.

## Built-in Implementations

### JarvisWhisperClient

The primary STT provider. Proxies audio through the Command Center's media endpoint, which forwards it to the `jarvis-whisper-api` service for transcription.

```python
class JarvisWhisperClient(IJarvisSpeechToTextProvider):
    provider_name = "jarvis_whisper"

    def transcribe(self, audio_path: str) -> Optional[str]:
        result = self.transcribe_with_speaker(audio_path)
        return result.text if result.text else None

    def transcribe_with_speaker(self, audio_path: str) -> TranscriptionResult:
        # 1. Read the audio file
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        # 2. Upload as multipart form data to Command Center
        response = self.jcc_client.post(
            "/api/v0/media/stt/transcribe",
            files={"audio": ("audio.wav", audio_data, "audio/wav")},
        )

        # 3. Parse response (includes speaker identification if available)
        data = response.json()
        return TranscriptionResult(
            text=data.get("text", ""),
            speaker_user_id=data.get("speaker", {}).get("user_id"),
            speaker_confidence=data.get("speaker", {}).get("confidence", 0.0),
        )
```

**Speaker identification:** When voice profiles are enrolled on the Whisper API, the response includes a `speaker` object with `user_id` and `confidence`. This enables personalized responses and user-specific memories.

### KeyboardProvider

A development/testing provider that reads text from standard input instead of processing audio:

```python
class KeyboardProvider(IJarvisSpeechToTextProvider):
    provider_name = "keyboard"

    def transcribe(self, audio_path: str) -> Optional[str]:
        # Ignores the audio file entirely
        text = input("You: ")
        return text.strip() if text.strip() else None
```

This is useful for testing commands without a microphone or audio setup. Set `"stt_provider": "keyboard"` in your node config to use it.

## Writing a Custom Provider

Here is an example that uses OpenAI's Whisper API (cloud):

```python
from stt_providers.base import IJarvisSpeechToTextProvider, TranscriptionResult
from typing import Optional
import httpx

class OpenAIWhisperProvider(IJarvisSpeechToTextProvider):
    @property
    def provider_name(self) -> str:
        return "openai_whisper"

    def __init__(self):
        self._api_key = self.secret_service.get_secret("OPENAI_API_KEY")

    def transcribe(self, audio_path: str) -> Optional[str]:
        if not self._api_key:
            return None

        with open(audio_path, "rb") as f:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": ("audio.wav", f, "audio/wav")},
                data={"model": "whisper-1"},
            )

        if response.status_code == 200:
            return response.json().get("text")
        return None
```

Save as `stt_providers/openai_whisper_provider.py`, then set `"stt_provider": "openai_whisper"` in your node config.

## Audio Format

STT providers receive a file path to a WAV audio file. The node's audio recording system handles format conversion before calling the provider, so you can assume:

- **Format:** WAV (PCM)
- **Sample rate:** 16000 Hz
- **Channels:** Mono (1 channel)
- **Bit depth:** 16-bit
