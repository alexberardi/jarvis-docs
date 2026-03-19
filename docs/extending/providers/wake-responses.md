# Wake Response Providers

A wake response provider implements `IJarvisWakeResponseProvider` to control what Jarvis says immediately after hearing the wake word ("Hey Jarvis"). This is the acknowledgment before the actual command response.

## Interface Reference

```python
from abc import ABC, abstractmethod
from typing import Optional

class IJarvisWakeResponseProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique name for this provider. Example: 'jarvis_tts_wake'."""
        ...

    @abstractmethod
    def fetch_next_wake_response(self) -> Optional[str]:
        """Return the next wake response text, or None for the default.

        Returns:
            A string to speak (e.g., "What can I do for you?"), or None
            to fall back to the hardcoded default greeting.
        """
        ...
```

The interface is intentionally minimal --- one method, one return value.

## How Wake Responses Work

When the wake word is detected, the node follows this sequence:

1. Play the chime sound (always)
2. Call `fetch_next_wake_response()` on the active provider
3. If the provider returns a string, speak it via the TTS provider
4. If the provider returns `None`, speak the hardcoded default ("Yes?")
5. Begin listening for the user's command

The wake response is spoken while the microphone is arming for the next recording, so it does not add latency to the interaction.

## Built-in Implementations

### JarvisTTSWakeResponseProvider

Fetches LLM-generated wake responses from the Command Center. This produces varied, natural-sounding acknowledgments instead of the same phrase every time.

```python
class JarvisTTSWakeResponseProvider(IJarvisWakeResponseProvider):
    provider_name = "jarvis_tts_wake"

    def fetch_next_wake_response(self) -> Optional[str]:
        try:
            response = self.jcc_client.get(
                "/api/v0/media/tts/generate-wake-response"
            )
            if response.status_code == 200:
                return response.json().get("text")
        except Exception:
            pass
        return None  # Fall back to default
```

**How it works:** The Command Center endpoint calls the LLM proxy to generate a short, contextual greeting. The LLM is prompted to produce varied responses like:

- "What's on your mind?"
- "I'm listening."
- "How can I help?"
- "Go ahead."

The endpoint is lightweight --- it returns a single short phrase, typically cached or pre-generated to avoid adding latency.

### StaticWakeResponseProvider

Always returns `None`, which causes the node to use the hardcoded default greeting. This is the simplest option --- no network calls, no variability.

```python
class StaticWakeResponseProvider(IJarvisWakeResponseProvider):
    provider_name = "static_wake"

    def fetch_next_wake_response(self) -> Optional[str]:
        return None
```

## Writing a Custom Provider

### Time-Aware Greetings

A provider that changes the greeting based on time of day:

```python
from wake_response_providers.base import IJarvisWakeResponseProvider
from typing import Optional
from datetime import datetime

class TimeAwareWakeProvider(IJarvisWakeResponseProvider):
    @property
    def provider_name(self) -> str:
        return "time_aware"

    def fetch_next_wake_response(self) -> Optional[str]:
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning. What do you need?"
        elif hour < 17:
            return "Good afternoon. How can I help?"
        elif hour < 21:
            return "Good evening. What can I do for you?"
        else:
            return "Still up? What do you need?"
```

### Random Response Pool

A provider that picks from a custom list:

```python
from wake_response_providers.base import IJarvisWakeResponseProvider
from typing import Optional
import random

class RandomWakeProvider(IJarvisWakeResponseProvider):
    RESPONSES = [
        "At your service.",
        "What do you need?",
        "Ready when you are.",
        "I'm all ears.",
        "Go ahead.",
        "What's up?",
    ]

    @property
    def provider_name(self) -> str:
        return "random_pool"

    def fetch_next_wake_response(self) -> Optional[str]:
        return random.choice(self.RESPONSES)
```

Save either example in `wake_response_providers/` and update your node config:

```json
{
    "wake_response_provider": "time_aware"
}
```

## Design Considerations

**Keep it fast.** The wake response is spoken during the transition between wake word detection and command listening. If `fetch_next_wake_response()` takes too long (network timeout, slow LLM call), it delays the entire interaction. Return `None` as a fallback if your source is slow.

**Return `None` on failure.** The system handles `None` gracefully by using the default greeting. Never raise exceptions from `fetch_next_wake_response()` --- catch them internally and return `None`.

**Keep it short.** Wake responses should be 2--6 words. The user is waiting to give a command, not listen to a speech.
