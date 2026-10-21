# Wake Response Providers

A wake response provider decides what Jarvis says to acknowledge the wake word ("Hey Jarvis"), before you give your command. It doesn't answer at wake time: it supplies the text for the **next** acknowledgment, which the node prepares in advance so it plays instantly.

!!! note "Built into the node"
    Providers are not package components: Pantry and `jdt` can't install one. You add a provider by editing the node's source (`jarvis-node-setup`). See [Providers](index.md).

## Interface reference

`core/ijarvis_wake_response_provider.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional


class IJarvisWakeResponseProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The name the node config selects, e.g. 'jarvis-tts-api'."""

    @abstractmethod
    def fetch_next_wake_response(self) -> Optional[str]:
        """The next acknowledgment's text, or None to keep the bundled ones."""
```

## How wake responses work

After each completed interaction, while the node is idle, it calls the provider's `fetch_next_wake_response()`. When that returns text, the node:

1. saves the text,
2. asks the server to synthesise it (`POST /api/v0/media/tts/speak`), and
3. caches the audio.

On the next wake word the node plays, in order of preference:

1. the **cached audio** of that text, if it is there;
2. otherwise a **bundled acknowledgment**, a WAV picked at random from `sounds/wake/`;
3. as a last resort, **live TTS** of the saved text, or "Yes?".

So a slow provider never delays a wake: the work happens between interactions. Pre-generation is skipped when the node's `wake_ack_audio_enabled` config is `false`.

## Built-in implementations

### `jarvis-tts-api` (JarvisTTSWakeResponseProvider)

The default. It calls `POST /api/v0/wake-response` on your Jarvis Automation server, authenticated as the node, and returns the `text` of the reply. jarvisd asks its LLM for a one-to-three-word greeting, and answers with a fixed fallback phrase when there is no LLM or the call fails.

```json
{ "wake_response_provider": "jarvis-tts-api" }
```

### `static` (StaticWakeResponseProvider)

Always returns `None`, so the node keeps playing its bundled acknowledgments: no network calls. Leaving `wake_response_provider` out of the config has the same effect.

```json
{ "wake_response_provider": "static" }
```

## Writing a custom provider

Save either example in `wake_response_providers/` in the node's checkout, set `"wake_response_provider"` to its name in `config.json`, and restart the node.

### Time-aware greetings

```python
from datetime import datetime
from typing import Optional

from core.ijarvis_wake_response_provider import IJarvisWakeResponseProvider


class TimeAwareWakeProvider(IJarvisWakeResponseProvider):
    @property
    def provider_name(self) -> str:
        return "time_aware"

    def fetch_next_wake_response(self) -> Optional[str]:
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning."
        if hour < 17:
            return "Good afternoon."
        if hour < 21:
            return "Good evening."
        return "Still up?"
```

The text is chosen when the previous interaction ends, not at the next wake, so "Good morning" can still play shortly after noon.

### Random response pool

```python
import random
from typing import Optional

from core.ijarvis_wake_response_provider import IJarvisWakeResponseProvider


class RandomWakeProvider(IJarvisWakeResponseProvider):
    RESPONSES = [
        "At your service.",
        "What do you need?",
        "Ready when you are.",
        "I'm all ears.",
        "Go ahead.",
    ]

    @property
    def provider_name(self) -> str:
        return "random_pool"

    def fetch_next_wake_response(self) -> Optional[str]:
        return random.choice(self.RESPONSES)
```

## Design considerations

**Return `None` on failure.** The node falls back to its bundled acknowledgments. Catch your own exceptions rather than raising.

**Keep it short.** An acknowledgment of one to five words; the user is waiting to talk.

**Keep it reasonably fast.** The call runs while the node is idle, but the node isn't listening for the wake word until it returns.
