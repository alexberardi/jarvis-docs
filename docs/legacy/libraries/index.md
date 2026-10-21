# Libraries

Jarvis includes several shared Python libraries that provide common functionality across services. These are installed as packages (typically via `pip install -e .`) rather than running as standalone services.

## Library Inventory

| Library | Package | Description |
|---------|---------|-------------|
| [Log Client](log-client.md) | `jarvis-log-client` | Structured logging via `JarvisLogger` |
| [Config Client](config-client.md) | `jarvis-config-client` | Service URL discovery via config service |
| [Settings Client](settings-client.md) | `jarvis-settings-client` | Runtime settings reader |
| [Auth Client](auth-client.md) | `jarvis-auth-client` | Auth validation middleware and helpers |
| [Web Scraper](web-scraper.md) | `jarvis-web-scraper` | Web content extraction for LLM consumption |

## Installation

Libraries are installed as editable packages during service development:

```bash
cd jarvis-<service>
pip install -e "../jarvis-log-client"
pip install -e "../jarvis-config-client"
```

Most services list these as dependencies in their `pyproject.toml` or `setup.py`.

## Design Principles

- **Graceful degradation** -- if the backing service is unavailable, libraries fall back to safe defaults (e.g., log client falls back to console output)
- **Minimal dependencies** -- libraries keep their dependency footprint small
- **Consistent interface** -- all libraries follow similar initialization and configuration patterns
