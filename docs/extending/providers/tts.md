# Text-to-Speech Providers

A text-to-speech (TTS) provider speaks Jarvis's replies, announcements and prompts on the node's speaker.

!!! note "Built into the node"
    Providers are not package components: Pantry and `jdt` can't install one. You add a provider by editing the node's source (`jarvis-node-setup`). See [Providers](index.md).

## Interface reference

`core/ijarvis_text_to_speech_provider.py`:

```python
from abc import ABC, abstractmethod

from core.platform_audio import platform_audio

CHIME_PATH = "sounds/chime.wav"  # resolved next to the node's code


class IJarvisTextToSpeechProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The name the node config selects, e.g. 'jarvis-tts-api'."""

    @abstractmethod
    def speak(self, include_chime: bool, text: str) -> None:
        """Turn text into speech and play it. Returns when playback ends."""

    def play_chime(self):
        platform_audio.play_chime(CHIME_PATH)
```

A provider synthesises **and plays** the audio. For playback, use the node's `platform_audio` (`core/platform_audio.py`): `play_audio_file(path)` plays a WAV file on the node's output device.

A provider may also offer `speak_stream(text) -> bool`, which plays audio as it arrives and returns `False` to let the caller fall back to `speak`. It is optional and not part of the interface; `jarvis-tts-api` has one.

## Built-in implementations

### `jarvis-tts-api` (JarvisTTS)

The default. It sends the text to your Jarvis Automation server with `POST /api/v0/media/tts/speak` (JSON `{"text": …}`, authenticated as the node), gets a WAV back and plays it. `speak_stream` uses `POST /api/v0/media/tts/speak/stream`, which returns raw PCM with its format in the `X-Audio-Sample-Rate`, `X-Audio-Channels` and `X-Audio-Sample-Width` headers.

jarvisd synthesises in-process with **Kokoro**, the only engine it has (Piper was cut). The voice and speed are server settings (`tts.kokoro_voice`, `tts.kokoro_speed`); the node side doesn't change.

```json
{ "tts_provider": "jarvis-tts-api" }
```

### `espeak` (EspeakTTS)

Speaks with the local `espeak` program. Robotic, but needs no server: useful for offline testing.

```json
{ "tts_provider": "espeak" }
```

## Writing a custom provider

An example that uses macOS system voices (`say`), for a node run on a Mac. Save it as `tts_providers/macos_say_provider.py` in the node's checkout:

```python
import subprocess

from core.ijarvis_text_to_speech_provider import IJarvisTextToSpeechProvider


class MacOSSayProvider(IJarvisTextToSpeechProvider):
    @property
    def provider_name(self) -> str:
        return "macos_say"

    def speak(self, include_chime: bool, text: str) -> None:
        if include_chime:
            self.play_chime()
        subprocess.run(["say", "-v", "Samantha", text], check=True)
```

A cloud API that returns WAV audio, playing it through the node:

```python
import os
import tempfile

import requests

from core.ijarvis_text_to_speech_provider import IJarvisTextToSpeechProvider
from core.platform_audio import platform_audio
from services.secret_service import get_secret_value


class CloudTTSProvider(IJarvisTextToSpeechProvider):
    @property
    def provider_name(self) -> str:
        return "cloud_tts"

    def speak(self, include_chime: bool, text: str) -> None:
        api_key = get_secret_value("CLOUD_TTS_API_KEY", "integration")
        if not api_key:
            raise RuntimeError("CLOUD_TTS_API_KEY is not set")

        response = requests.post(
            "https://tts.example.com/v1/speak",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"text": text, "format": "wav"},
            timeout=30,
        )
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(response.content)
            path = tmp.name
        try:
            if include_chime:
                self.play_chime()
            platform_audio.play_audio_file(path)
        finally:
            os.unlink(path)
```

Then set `"tts_provider"` to your provider's name in the node's `config.json` and restart the node. Store any key in the node's secret store first (see [Speech-to-Text Providers](stt.md#writing-a-custom-provider)).

The node instantiates every provider class it finds with no arguments, so keep `__init__` cheap and argument-free.

## Chime behavior

`include_chime=True` asks for the chime before the speech; the node passes it for alert announcements, and `False` for most spoken replies and prompts. Call `self.play_chime()` when it is `True`. The chime is `sounds/chime.wav` in the node's checkout; override `play_chime()` to use another sound.
