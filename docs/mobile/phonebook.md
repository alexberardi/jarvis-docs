# Phonebook

The Phonebook manages the businesses Jarvis is allowed to call --- numbers, notes, and a do-not-call flag. Access it from **Settings → Phonebook**.

Entries are household-scoped and arrive three ways:

| Source | Badge | How it happens |
|--------|-------|-----------------|
| `call` | "saved from a call" | Saved automatically after Jarvis completes a call |
| `web` | "found by search" | Found by web search during call planning |
| `manual` | "added by you" | Added by hand from the Phonebook screen |

## List

Pull to refresh the list. Each card shows the business name, formatted number, and its source badge. Businesses marked do-not-call show a red **do not call** chip and appear dimmed. Swipe a card to delete it (with confirmation).

If nothing is saved yet, the screen shows an empty state: *"No businesses saved yet --- Businesses are saved here automatically after Jarvis calls them successfully. You can also add one yourself."*

Tap the **+** button to add a business.

## Add / Edit

The same form handles both add and edit:

- **Name** and **Phone number** (tel keyboard) are required
- **Address** and **Notes** are optional
- **Do not call** --- only shown when editing an existing business; when on, Jarvis refuses to call it

Number formatting (e.g. `+15551234567` → `(555) 123-4567`) is presentation-only --- the number sent to and stored by the server is what gets dialed.

### Inline validation

Save/update errors surface on the specific field rather than a generic toast:

- A rejected phone number (invalid format) shows the server's message under the **Phone number** field.
- A duplicate business name (name collision) shows under the **Name** field.

## API

The screen consumes the phonebook API on `jarvis-command-center`:

| Method | Path |
|--------|------|
| `GET` | `/api/v0/mobile/household/{household_id}/phone-contacts` |
| `POST` | `/api/v0/mobile/household/{household_id}/phone-contacts` |
| `PATCH` | `/api/v0/mobile/household/{household_id}/phone-contacts/{contact_id}` |
| `DELETE` | `/api/v0/mobile/household/{household_id}/phone-contacts/{contact_id}` |

The API returns `400` for an invalid number and `409` for a duplicate name; the mobile client maps both to the corresponding form field instead of a generic error banner.

See the [Command Center](../services/command-center.md) service docs for the backend side of this API.
