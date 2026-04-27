---
name: aktion-tg-keyboard
description: >
  Reference utility for sending Telegram messages with inline keyboard buttons
  directly via the Bot API (Python/urllib). Documents callback_query data format,
  answerCallbackQuery usage, token loading, and HTML formatting. Load this skill
  whenever another skill needs to send a keyboard message on Telegram.
tags:
  - telegram
  - keyboard
  - utility
  - reference
---

# Skill: aktion-tg-keyboard

**Type**: Reference / utility — not triggered directly. Loaded by other skills that need
to send Telegram inline keyboard messages.

**Purpose**: Canonical reference for how Aktion skills send Telegram messages with
inline keyboard buttons. Covers API calls, payload structure, callback_query data
format, spinner dismissal, token loading, and HTML formatting.

---

## 1. Token Loading

The Telegram bot token is stored in `~/.hermes/.env`. Read it at runtime — never
hardcode it, never cache it across invocations.

```python
# Load TELEGRAM_BOT_TOKEN from ~/.hermes/.env
import os

def load_bot_token() -> str:
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("TELEGRAM_BOT_TOKEN not found in ~/.hermes/.env")
```

---

## 2. Inline Keyboard Payload Structure

Inline keyboards are sent as `reply_markup.inline_keyboard` — a list of rows, where
each row is a list of button objects.

```json
{
  "chat_id": 123456789,
  "text": "Choose an action:",
  "parse_mode": "HTML",
  "reply_markup": {
    "inline_keyboard": [
      [
        { "text": "Confirm", "callback_data": "aktion:confirm:abc123" },
        { "text": "Reject",  "callback_data": "aktion:reject:abc123" }
      ],
      [
        { "text": "View details", "callback_data": "aktion:details:abc123" }
      ]
    ]
  }
}
```

Each button row is a list. Buttons in the same list appear side by side. Separate
rows stack vertically.

---

## 3. Callback Data Format

All Aktion callback payloads follow this pattern:

    aktion:<command>:<args>

The router (aktion-router) matches the prefix `aktion:` and dispatches to the
appropriate skill. Keep `<args>` short — Telegram enforces a 64-byte limit on
`callback_data`.

Examples:

    aktion:confirm:<proposal_id>        -- keyholder confirms a proposal
    aktion:reject:<proposal_id>         -- keyholder rejects a proposal
    aktion:confirm_posture:<level>      -- keyholder approves a posture change
    aktion:details:<proposal_id>        -- show proposal detail inline
    aktion:ack:<directive_id>           -- participant acknowledges a task

When the router receives a `callback_query` event, it extracts `callback_data`,
splits on `:`, and routes by `command`. The `args` segment is passed as-is to the
target skill.

---

## 4. Answering Callback Queries

After handling a `callback_query`, always call `answerCallbackQuery` to dismiss the
Telegram loading spinner on the button. Failure to do this leaves the spinner
spinning for ~30 seconds on the user's end.

```python
def answer_callback_query(callback_query_id: str, text: str = "", token: str = None):
    """Dismiss the inline button spinner. Call this after every callback_query."""
    import json, urllib.request
    token = token or load_bot_token()
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text          # optional toast notification to user
        payload["show_alert"] = False   # True = modal, False = brief toast
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

---

## 5. Rich Text Formatting

Always set `parse_mode=HTML`. Telegram supports a safe subset of HTML tags:

    <b>bold</b>          <i>italic</i>         <u>underline</u>
    <s>strikethrough</s> <code>monospace</code> <pre>block</pre>
    <a href="URL">link</a>

Do not use Markdown mode — it has escaping edge cases that break on special
characters in proposal payloads and IDs. HTML is predictable.

---

## 6. Reusable Code Snippet

Copy-paste this function into any skill that needs to send a Telegram message
with inline keyboard buttons.

```python
# ---- SNIPPET: send_tg_keyboard_message ----------------------------------------
# Copy into any skill that needs to send an inline keyboard message on Telegram.
# Requires: Python 3.8+, stdlib only (no external dependencies).
# ---------------------------------------------------------------------------

import json
import os
import urllib.request
import urllib.error


def load_bot_token() -> str:
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("TELEGRAM_BOT_TOKEN not found in ~/.hermes/.env")


def send_tg_keyboard_message(
    chat_id: int | str,
    text: str,
    buttons: list[list[dict]],
    token: str = None,
) -> dict:
    """
    Send a Telegram message with an inline keyboard.

    Args:
        chat_id:  Telegram chat ID (integer) or @username string.
        text:     Message body. HTML tags are supported (parse_mode=HTML).
        buttons:  Inline keyboard as a list of rows. Each row is a list of
                  button dicts: {"text": "Label", "callback_data": "aktion:..."}
                  Buttons in the same row appear side by side.
        token:    Bot token. If None, loads from ~/.hermes/.env.

    Returns:
        Parsed JSON response from Telegram API.

    Example:
        send_tg_keyboard_message(
            chat_id=987654321,
            text="<b>[PROPOSAL abc123]</b>\nAction: update_state\nConfirmations: 0/2",
            buttons=[
                [
                    {"text": "Confirm",      "callback_data": "aktion:confirm:abc123"},
                    {"text": "Reject",       "callback_data": "aktion:reject:abc123"},
                ],
                [
                    {"text": "View details", "callback_data": "aktion:details:abc123"},
                ],
            ],
        )
    """
    token = token or load_bot_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": buttons},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Telegram API error {e.code}: {body}") from e


def answer_callback_query(
    callback_query_id: str,
    text: str = "",
    show_alert: bool = False,
    token: str = None,
) -> dict:
    """
    Dismiss the inline button spinner after handling a callback_query.
    Always call this — failure leaves the spinner active for ~30 seconds.

    Args:
        callback_query_id: From event.callback_query.id
        text:              Optional toast message shown to the user.
        show_alert:        True = modal dialog, False = brief toast.
        token:             Bot token. If None, loads from ~/.hermes/.env.
    """
    token = token or load_bot_token()
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = show_alert
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# ---- END SNIPPET ---------------------------------------------------------------
```

---

## 7. Handling Callback Events in the Router

When a `callback_query` arrives, the router extracts these fields:

    event.callback_query.id            -- pass to answerCallbackQuery
    event.callback_query.from.id       -- Telegram user ID (check against keyholders)
    event.callback_query.data          -- e.g. "aktion:confirm:abc123"
    event.callback_query.message       -- the original message object

Dispatch pattern:

```python
parts = callback_data.split(":", 2)   # ["aktion", "confirm", "abc123"]
prefix, command, args = parts[0], parts[1], parts[2] if len(parts) > 2 else ""

if prefix != "aktion":
    return  # ignore non-Aktion callbacks

# Route by command
if command == "confirm":
    handle_confirm(proposal_id=args, user_id=from_id)
elif command == "confirm_posture":
    handle_confirm_posture(level=args, user_id=from_id)
# ... etc.

# Always dismiss spinner last
answer_callback_query(callback_query_id=cq_id, text="Done.")
```
