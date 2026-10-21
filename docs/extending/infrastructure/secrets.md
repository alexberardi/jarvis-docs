# Secret Service

Secrets are the API keys, tokens and options a household sets for a package from the mobile app. A package reads and writes them through the SDK's `JarvisStorage`; on the Python node they live in the node's encrypted database.

!!! tip "Declaring secrets vs. reading secrets"
    This page covers the **runtime API** for reading and writing secrets. For how to declare what secrets your command needs, see [Secrets Deep Dive](../../commands/secrets.md).

## Reading and writing secrets

```python
from jarvis_command_sdk import JarvisStorage

storage = JarvisStorage("get_weather")  # your command's name

api_key = storage.get_secret("OPENWEATHER_API_KEY")         # integration scope (the default)
email = storage.get_secret("GMAIL_ADDRESS", scope="user")    # the current user's own value

storage.set_secret("LAST_CITY", "Denver")                     # stored as a string
storage.set_secret("RETRIES", "3", value_type="int")
storage.delete_secret("LAST_CITY")
```

`get_secret` returns the value as a string, or `None` when it isn't set. Values are always strings: convert an `int` or `bool` yourself. With no storage backend registered (tests, Pantry validation) `get_secret` returns `None` and the writes do nothing.

To make `"user"` the default scope for an instance, pass it once: `JarvisStorage("gmail", secret_scope="user")`.

## Scopes

A secret has one of two scopes. Any other value raises `ValueError` when the `JarvisSecret` is declared.

| Scope | One value per | Use for |
|-------|---------------|---------|
| `"integration"` | Household | API keys, service URLs, shared preferences such as units |
| `"user"` | Household member | Personal accounts and credentials, such as one person's email |

For a `"user"` secret, `JarvisStorage` looks up the user from the request that is running, so each member gets their own value. Outside a request (an agent's background run, for example) there is no current user: store a household member's id in a `value_type="user"` secret and act for that member.

## Value types

| Type | Stored as | Mobile app field |
|------|-----------|------------------|
| `"string"` | Text | Text field (a picker with `enum_values`) |
| `"int"` | Text, convert with `int()` | Number |
| `"bool"` | `"true"` / `"false"` | Toggle |
| `"user"` | A user id as text | Household-member picker |

The type is metadata for the settings screen; every value is stored as text.

## Typical usage in a command

```python
from typing import List

from jarvis_command_sdk import (
    CommandExample,
    CommandResponse,
    IJarvisCommand,
    JarvisParameter,
    JarvisSecret,
    JarvisStorage,
    RequestInformation,
)


class GetStockPrice(IJarvisCommand):
    @property
    def command_name(self) -> str:
        return "get_stock_price"

    @property
    def description(self) -> str:
        return "Get the current price of a stock"

    @property
    def keywords(self) -> List[str]:
        return ["stock", "price", "shares"]

    @property
    def parameters(self) -> List[JarvisParameter]:
        return [JarvisParameter("symbol", "string", required=True, description="Ticker symbol")]

    @property
    def required_secrets(self) -> List[JarvisSecret]:
        return [
            JarvisSecret("FINANCE_API_KEY", "Financial data API key",
                         "integration", "string", friendly_name="API Key"),
            JarvisSecret("DEFAULT_CURRENCY", "Default display currency",
                         "integration", "string",
                         required=False, is_sensitive=False, friendly_name="Currency"),
        ]

    def generate_prompt_examples(self) -> List[CommandExample]:
        return [CommandExample("What's Apple trading at?", {"symbol": "AAPL"}, is_primary=True)]

    def generate_adapter_examples(self) -> List[CommandExample]:
        return self.generate_prompt_examples()

    def run(self, request_info: RequestInformation, **kwargs) -> CommandResponse:
        storage = JarvisStorage(self.command_name)
        api_key = storage.get_secret("FINANCE_API_KEY")
        if not api_key:
            return CommandResponse.error_response(error_details="Set the API key in the mobile app first.")
        currency = storage.get_secret("DEFAULT_CURRENCY") or "USD"  # optional

        symbol = kwargs["symbol"]
        price = 123.45  # call your price API with api_key here
        return CommandResponse.success_response(
            context_data={"message": f"{symbol} is trading at {price} {currency}"}
        )
```

The command's name is the `command_name` property. A host may also refuse to run a command whose required secrets are missing (the SDK's `execute()` raises `MissingSecretsError` when it is given the secrets), but check for `None` anyway: the household may not have set a value yet.

## On the Python node

`JarvisStorage` on a Pi is backed by the node's own `services/secret_service.py` (in `jarvis-node-setup`). The node's built-in commands call it directly; packages should not, since a computer doesn't have it.

| Function | Does |
|----------|------|
| `get_secret_value(key, scope, user_id=None)` | The value, or `None` |
| `get_secret_value_int(key, scope, user_id=None)` | The value as an `int`, or `None` |
| `set_secret(key, value, scope, value_type="string", user_id=None)` | Insert or update |
| `delete_secret(key, scope, user_id=None)` | Delete |
| `get_all_secrets(scope, user_id=None)` | Every secret in a scope |
| `ensure_secret_exists(key, scope, value_type)` | Create an empty row if missing |
| `seed_command_secrets(secrets)` | Empty rows for a command's declared secrets (skips `"user"` ones); existing values are kept |

Each call opens and closes its own database session, so it is safe from any thread. Rows hold `key`, `value`, `scope`, `value_type` and, for user-scoped secrets, `user_id`.

On the node, `python scripts/install_command.py --all` seeds empty rows for every command's secrets (it is safe to re-run), and `--list` lists them.

The database is SQLCipher (`sqlcipher3`). Its key is `~/.jarvis/db.key`, created the first time the database is opened, and the file is `./jarvis_node.db` in the node's working directory (or `$JARVIS_NODE_DB`). Without the key the database is unreadable.
