# Web Scraper

The web scraper library extracts clean text content from web pages, optimized for LLM consumption. It was extracted from the recipes server's `html_fetcher.py` into a standalone reusable library.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-web-scraper` |
| **Source** | `jarvis-web-scraper/` |
| **Tests** | 70 tests |

## Usage

!!! warning "Async API"
    All methods are async and must be awaited.

```python
from jarvis_web_scraper import WebScraper

scraper = WebScraper()

# Extract clean text from a single URL
result = await scraper.fetch_and_extract(url="https://example.com/article")

if result.ok:
    print(result.text_content)   # Clean extracted text
    print(result.title)          # Page title
    print(result.word_count)     # Word count of extracted text
    print(result.fetch_time_ms)  # Fetch + extraction latency
else:
    print(result.error)          # Error message if fetch/parse failed
```

## Batch Fetching

Fetch multiple URLs concurrently with `batch_fetch()`:

```python
urls = ["https://example.com/page1", "https://example.com/page2"]
results = await scraper.batch_fetch(urls, max_concurrent=3)
# Returns list[ScrapedPage] in the same order as input
```

## ScrapedPage Fields

| Field | Type | Description |
|-------|------|-------------|
| `url` | str | Final URL after redirects |
| `title` | str \| None | Page `<title>` |
| `text_content` | str | Clean extracted text, stripped of nav/ads/boilerplate |
| `word_count` | int | Word count of `text_content` |
| `fetch_time_ms` | int | Total latency in milliseconds |
| `error` | str \| None | Error message if the request failed |
| `ok` | bool | `True` if fetch succeeded and content was extracted |

## Configuration

Pass a `FetchConfig` to customize scraping behavior:

```python
from jarvis_web_scraper import WebScraper, FetchConfig

config = FetchConfig(
    timeout=15,
    max_chars=8000,
    block_private_hosts=True,
    user_agent="Jarvis/1.0",
)
scraper = WebScraper(config=config)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout` | `15` | Request timeout in seconds |
| `max_chars` | `8000` | Maximum characters returned per page (truncates at word boundary) |
| `max_redirects` | `5` | Maximum HTTP redirects to follow |
| `block_private_hosts` | `True` | Block requests to private/loopback IP ranges and reject redirects to private hosts (SSRF protection — see below) |
| `user_agent` | *(default UA)* | User-Agent header |
| `headers` | `{}` | Additional HTTP headers |

## SSRF Protection

When `block_private_hosts=True` (the default), the scraper enforces SSRF protection at every step of a request.

**Host validation** — every hostname is DNS-resolved before connecting. If *any* resolved address is private, the request is rejected. Unresolvable hosts are also rejected (fail-closed). Blocked ranges:

| Range | Example |
|-------|---------|
| Loopback | `127.0.0.0/8`, `::1` |
| Private | `10/8`, `172.16/12`, `192.168/16` |
| Link-local | `169.254/16`, `fe80::/10` (includes cloud metadata `169.254.169.254`) |
| NAT64 / CGNAT | `64:ff9b::/96`, `100.64/10` |
| IPv4-mapped IPv6 | `::ffff:…` — judged as its embedded IPv4 |
| Multicast / unspecified | `224/4`, `::` |

**Per-hop redirect validation** — every `3xx` redirect hop is re-validated against the same blocklist before following. A public URL that redirects to a private address is blocked, not followed. `Authorization` and `Cookie` headers are stripped on cross-origin hops. The maximum number of hops is controlled by `max_redirects`.

**Jina fallback** — when the primary fetch fails and the `r.jina.ai` reader is used as a fallback, the *original* URL is DNS-validated first. The fallback will not proxy a private-host URL out to Jina.

To disable SSRF protection (for trusted internal targets only):

```python
config = FetchConfig(block_private_hosts=False)
```

## Features

- Extracts main content, stripping navigation, ads, and boilerplate
- Returns clean text suitable for LLM context windows
- Handles common web page structures and formats
- Per-hop SSRF protection covers redirect chains, IPv6, NAT64, and IPv4-mapped addresses

## Consumers

- **jarvis-command-center** — deep research tool (web search → scrape → summarize)
- **jarvis-recipes-server** — URL recipe import (HTML parsing)
