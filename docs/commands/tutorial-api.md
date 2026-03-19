# Tutorial: API Integration Command

This tutorial builds a stock price command that calls an external API. You will learn how to manage API keys with `JarvisSecret`, make HTTP requests in `run()`, handle errors gracefully, and use `associated_service` and `antipatterns` for a polished integration.

**Prerequisites:** Completed the [Simple Command Tutorial](tutorial-simple.md).

## The Plan

We will build a `get_stock_price` command that:

- Accepts a stock ticker symbol
- Looks up the current price via a financial data API
- Requires an API key stored as a secret
- Groups with other financial commands in the mobile settings UI
- Distinguishes itself from the web search command

## Step 1: File and Imports

Create `jarvis-node-setup/commands/stock_price_command.py`:

```python
from typing import List

import httpx
from jarvis_log_client import JarvisLogger

from core.ijarvis_command import IJarvisCommand, CommandExample, CommandAntipattern
from core.ijarvis_parameter import JarvisParameter
from core.ijarvis_secret import IJarvisSecret, JarvisSecret
from core.command_response import CommandResponse
from core.request_information import RequestInformation
from services.secret_service import get_secret_value

logger = JarvisLogger(service="jarvis-node")
```

Notable additions compared to the dice command:

- `httpx` for HTTP requests (or use `requests`)
- `JarvisLogger` for structured logging (never use `print()`)
- `get_secret_value` for reading secrets at runtime
- `CommandAntipattern` for disambiguation

## Step 2: Declare Secrets

This command needs an API key. We declare it as a `JarvisSecret`:

```python
class StockPriceCommand(IJarvisCommand):

    @property
    def required_secrets(self) -> List[IJarvisSecret]:
        return [
            JarvisSecret(
                key="FINANCE_API_KEY",
                description="API key for the financial data provider",
                scope="integration",
                value_type="string",
                required=True,
                is_sensitive=True,
                friendly_name="API Key",
            ),
            JarvisSecret(
                key="FINANCE_DEFAULT_CURRENCY",
                description="Default currency for prices (e.g., USD, EUR)",
                scope="integration",
                value_type="string",
                required=False,
                is_sensitive=False,
                friendly_name="Default Currency",
            ),
        ]
```

Key choices:

- **`scope="integration"`** means this key is shared across all nodes in the household. Use `"node"` for per-node config (like a default location).
- **`is_sensitive=True`** for the API key means it won't appear in settings snapshots sent to the mobile app. The currency preference uses `is_sensitive=False` so the mobile app can display it.
- **`friendly_name`** is what users see in the mobile settings UI instead of the raw key name.

## Step 3: Properties and Parameters

```python
    @property
    def command_name(self) -> str:
        return "get_stock_price"

    @property
    def description(self) -> str:
        return (
            "Get current stock price by ticker symbol. "
            "For company research, earnings, or financial news, use search_web instead."
        )

    @property
    def keywords(self) -> List[str]:
        return ["stock", "price", "ticker", "shares", "market", "quote"]

    @property
    def parameters(self) -> List[JarvisParameter]:
        return [
            JarvisParameter(
                "ticker",
                "string",
                required=True,
                description="Stock ticker symbol (e.g., AAPL, GOOGL, TSLA)",
            ),
        ]
```

## Step 4: Associated Service

Group this command with other financial commands in the mobile settings UI:

```python
    @property
    def associated_service(self) -> str | None:
        return "Financial Data"
```

If you later add a `get_stock_news` command with the same `associated_service`, they will appear together in the mobile app's settings screen, sharing the same API key configuration section.

## Step 5: Antipatterns

Tell the LLM what NOT to use this command for:

```python
    @property
    def antipatterns(self) -> List[CommandAntipattern]:
        return [
            CommandAntipattern(
                command_name="search_web",
                description=(
                    "Company research, earnings reports, financial news, "
                    "market analysis. Use search_web for those."
                ),
            ),
        ]
```

This helps the LLM distinguish between "What's Apple's stock price?" (this command) and "What were Apple's Q3 earnings?" (web search).

## Step 6: Examples

```python
    def generate_prompt_examples(self) -> List[CommandExample]:
        return [
            CommandExample(
                voice_command="What's Apple's stock price?",
                expected_parameters={"ticker": "AAPL"},
                is_primary=True,
            ),
            CommandExample(
                voice_command="How is Tesla doing?",
                expected_parameters={"ticker": "TSLA"},
            ),
            CommandExample(
                voice_command="Check the price of Google stock",
                expected_parameters={"ticker": "GOOGL"},
            ),
        ]

    def generate_adapter_examples(self) -> List[CommandExample]:
        return [
            CommandExample("What's Apple's stock price?", {"ticker": "AAPL"}, is_primary=True),
            CommandExample("How is Tesla doing?", {"ticker": "TSLA"}),
            CommandExample("Check the price of Google", {"ticker": "GOOGL"}),
            CommandExample("What's Amazon trading at?", {"ticker": "AMZN"}),
            CommandExample("Microsoft stock price", {"ticker": "MSFT"}),
            CommandExample("How much is NVIDIA stock?", {"ticker": "NVDA"}),
            CommandExample("Give me a quote on Meta", {"ticker": "META"}),
            CommandExample("Stock price for Disney", {"ticker": "DIS"}),
            CommandExample("What's the share price of Netflix?", {"ticker": "NFLX"}),
            CommandExample("Check SPY", {"ticker": "SPY"}),
        ]
```

## Step 7: Implement `run()`

```python
    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        ticker = kwargs.get("ticker", "").upper().strip()
        if not ticker:
            return CommandResponse.error_response(
                error_details="Please specify a stock ticker symbol",
            )

        api_key = get_secret_value("FINANCE_API_KEY", "integration")
        if not api_key:
            return CommandResponse.error_response(
                error_details="Finance API key is not configured. Set it in your node settings.",
            )

        currency = get_secret_value("FINANCE_DEFAULT_CURRENCY", "integration") or "USD"

        try:
            response = httpx.get(
                f"https://api.example.com/v1/quote/{ticker}",
                params={"apikey": api_key, "currency": currency},
                timeout=10.0,
            )

            if response.status_code == 404:
                return CommandResponse.error_response(
                    error_details=f"Ticker '{ticker}' not found. Check the symbol and try again.",
                    context_data={"ticker": ticker, "error": "not_found"},
                )

            response.raise_for_status()
            data = response.json()

            price = data.get("price")
            change = data.get("change")
            change_pct = data.get("change_percent")
            name = data.get("name", ticker)

            logger.info("Stock price fetched", ticker=ticker, price=price)

            return CommandResponse.final_response(
                context_data={
                    "ticker": ticker,
                    "name": name,
                    "price": price,
                    "change": change,
                    "change_percent": change_pct,
                    "currency": currency,
                    "message": (
                        f"{name} ({ticker}) is at {currency} {price}, "
                        f"{'up' if change >= 0 else 'down'} {abs(change_pct):.1f}%"
                    ),
                }
            )

        except httpx.TimeoutException:
            logger.error("Stock API timeout", ticker=ticker)
            return CommandResponse.error_response(
                error_details="The financial data service is not responding. Try again in a moment.",
            )
        except httpx.HTTPStatusError as e:
            logger.error("Stock API error", ticker=ticker, status=e.response.status_code)
            return CommandResponse.error_response(
                error_details=f"Failed to fetch stock data: HTTP {e.response.status_code}",
            )
        except Exception as e:
            logger.error("Stock price fetch failed", ticker=ticker, error=str(e))
            return CommandResponse.error_response(
                error_details=f"Unable to fetch stock price: {str(e)}",
            )
```

### Error Handling Best Practices

1. **Check for missing secrets early** -- return a clear error message pointing to settings
2. **Handle specific HTTP errors** -- 404 for bad tickers, timeouts, general HTTP errors
3. **Always use `logger`** -- structured logging with context, never `print()`
4. **Return user-friendly error messages** -- the LLM uses these to generate spoken responses
5. **Include `context_data` even in errors** -- helps debugging and lets the LLM provide context

## Step 8: Install and Test

```bash
# Install (seeds secret rows in the DB)
python scripts/install_command.py get_stock_price

# Set the API key
python utils/set_secret.py FINANCE_API_KEY "your-api-key-here" integration

# Test with E2E
python test_command_parsing.py -c get_stock_price
```

## Adding Rules

If the LLM makes common mistakes, add rules:

```python
    @property
    def rules(self) -> List[str]:
        return [
            "Extract the ticker symbol from company names (Apple -> AAPL, Google -> GOOGL)",
            "If the user says a company name, use the common ticker for that company",
        ]

    @property
    def critical_rules(self) -> List[str]:
        return [
            "The ticker parameter must be a valid stock symbol, not a company name",
        ]
```

## Adding Post-Processing

If the LLM sometimes passes a company name instead of a ticker, you can fix it:

```python
    _COMPANY_TO_TICKER = {
        "apple": "AAPL", "google": "GOOGL", "tesla": "TSLA",
        "amazon": "AMZN", "microsoft": "MSFT", "meta": "META",
    }

    def post_process_tool_call(self, args: dict, voice_command: str) -> dict:
        ticker = args.get("ticker", "")
        # If the LLM passed a company name, map it to a ticker
        mapped = self._COMPANY_TO_TICKER.get(ticker.lower())
        if mapped:
            args["ticker"] = mapped
        return args
```

## What's Next

- [OAuth Command Tutorial](tutorial-oauth.md) -- for commands needing user authorization
- [Secrets Deep Dive](secrets.md) -- advanced secret patterns (scopes, config variants)
- [Response Patterns](responses.md) -- follow-up flows, interactive buttons
