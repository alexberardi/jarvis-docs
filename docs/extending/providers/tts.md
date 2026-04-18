# Text-to-Speech Providers

A TTS provider implements `IJarvisTextToSpeechProvider` to speak text aloud through the node's audio output. The node calls the provider after receiving a response from the Command Center.

## Interface Reference

```python
from abc import ABC, abstractmethod

class IJarvisTextToSpeechProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique name for this provider. Example: 'jarvis_tts'."""
        ...

    @abstractmethod
    def speak(self, include_chime: bool, text: str) -> None:
        """Speak the given text aloud.

        Args:
            include_chime: If True, play a chime sound before speaking.
            text: The text to synthesize and play.
        """
        ...

    def play_chime(self) -> None:
        """Play the built-in chime sound (sounds/chime.wav).

        This is a helper method available to all providers. Call it from
        your speak() implementation when include_chime is True.
        """
        ...
```

The `play_chime()` method is a built-in helper that plays `sounds/chime.wav` through the system audio. You do not need to implement chime logic yourself --- just call `self.play_chime()` when `include_chime` is `True`.

## Built-in Implementations

### JarvisTTS

The primary TTS provider. Proxies text through the Command Center's media endpoint, which forwards it to the `jarvis-tts` service. `jarvis-tts` itself can run multiple backends (Piper default, Kokoro optional) selected via the `tts.provider` setting — the node side is unchanged. Supports streaming PCM audio for low latency.

```python
class JarvisTTS(IJarvisTextToSpeechProvider):
    provider_name = "jarvis_tts"

    def speak(self, include_chime: bool, text: str) -> None:
        if include_chime:
            self.play_chime()

        # Request streaming PCM audio from the TTS service
        response = self.jcc_client.post(
            "/api/v0/media/tts/synthesize",
            json={"text": text},
            stream=True,
        )

        # Play PCM audio chunks as they arrive (low latency)
        for chunk in response.iter_bytes():
            self.audio_player.play_pcm(chunk)
```

**Streaming:** `JarvisTTS` uses streaming PCM to minimize time-to-first-audio. The TTS service begins sending audio data before the entire text is synthesized, so the user hears the beginning of the response while the rest is still being generated.

### EspeakTTS

A local fallback provider that uses the `espeak` command-line tool. No network connection required --- useful for offline operation or as a lightweight alternative.

```python
class EspeakTTS(IJarvisTextToSpeechProvider):
    provider_name = "espeak"

    def speak(self, include_chime: bool, text: str) -> None:
        if include_chime:
            self.play_chime()

        # Generate WAV to a temp file using espeak
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        subprocess.run(
            ["espeak", "-w", tmp_path, text],
            check=True,
        )

        # Play the generated audio file
        self.audio_player.play_file(tmp_path)
        os.unlink(tmp_path)
```

**Trade-offs:** `espeak` produces robotic-sounding speech but works offline, requires no API keys, and has near-zero latency. It is a good fallback when the Jarvis TTS service is unavailable.

## Writing a Custom Provider

Here is an example that uses macOS system voices via the `say` command:

```python
from tts_providers.base import IJarvisTextToSpeechProvider
import subprocess

class MacOSSayProvider(IJarvisTextToSpeechProvider):
    @property
    def provider_name(self) -> str:
        return "macos_say"

    def speak(self, include_chime: bool, text: str) -> None:
        if include_chime:
            self.play_chime()

        # Use macOS built-in "say" command with the Samantha voice
        subprocess.run(
            ["say", "-v", "Samantha", text],
            check=True,
        )
```

Save as `tts_providers/macos_say_provider.py`, then set `"tts_provider": "macos_say"` in your node config.

Here is a more advanced example using a cloud TTS API with audio streaming:

```python
from tts_providers.base import IJarvisTextToSpeechProvider
import httpx
import tempfile
import os

class ElevenLabsProvider(IJarvisTextToSpeechProvider):
    @property
    def provider_name(self) -> str:
        return "elevenlabs"

    def __init__(self):
        self._api_key = self.secret_service.get_secret("ELEVENLABS_API_KEY")
        self._voice_id = self.secret_service.get_secret("ELEVENLABS_VOICE_ID") or "default"

    def speak(self, include_chime: bool, text: str) -> None:
        if not self._api_key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return

        if include_chime:
            self.play_chime()

        response = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}",
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
            },
        )

        if response.status_code != 200:
            logger.error(f"ElevenLabs API error: {response.status_code}")
            return

        # Write audio to temp file and play
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        self.audio_player.play_file(tmp_path)
        os.unlink(tmp_path)
```

## Chime Behavior

The `include_chime` parameter is `True` when Jarvis is responding to a voice command (indicating "I heard you, here is my response"). It is `False` for proactive speech (announcements, timers, etc.) where a chime would be unexpected.

The built-in chime file is located at `sounds/chime.wav`. To use a custom chime, replace this file or override `play_chime()` in your provider.
