# Web Scraper

The web scraper library extracts clean text content from web pages, optimized for LLM consumption. It was extracted from the recipes server's `html_fetcher.py` into a standalone reusable library.

## Quick Reference

| | |
|---|---|
| **Package** | `jarvis-web-scraper` |
| **Source** | `jarvis-web-scraper/` |
| **Tests** | 27 tests |

## Usage

```python
from jarvis_web_scraper import WebScraper

scraper = WebScraper()

# Extract clean text from a URL
result = scraper.scrape(url="https://example.com/article")
print(result.text)       # Clean extracted text
print(result.title)      # Page title
print(result.metadata)   # Extracted metadata
```

## Features

- Extracts main content, stripping navigation, ads, and boilerplate
- Returns clean text suitable for LLM context windows
- Handles common web page structures and formats
- Configurable extraction strategies

## Consumers

- **jarvis-command-center** -- deep research tool (web search, scrape, summarize)
- **jarvis-recipes-server** -- URL recipe import (HTML parsing)
