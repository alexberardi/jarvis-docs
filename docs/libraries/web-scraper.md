# Web Scraper

The web scraper library extracts clean text content from web pages, optimized for LLM consumption. It was extracted from the recipes server's `html_fetcher.py` into a standalone reusable library.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-web-scraper` |
| **Source** | `jarvis-web-scraper/` |
| **Tests** | 27 tests |

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
| `block_private_hosts` | `True` | Block requests to private/loopback IP ranges (SSRF protection) |
| `user_agent` | *(default UA)* | User-Agent header |
| `headers` | `{}` | Additional HTTP headers |

## Features

- Extracts main content, stripping navigation, ads, and boilerplate
- Returns clean text suitable for LLM context windows
- Handles common web page structures and formats
- Private IP blocking protects against SSRF in multi-tenant setups

## Consumers

- **jarvis-command-center** — deep research tool (web search → scrape → summarize)
- **jarvis-recipes-server** — URL recipe import (HTML parsing)
