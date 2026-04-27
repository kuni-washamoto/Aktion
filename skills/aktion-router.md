# Skill: aktion-router

**Trigger**: Any inbound message delivered by Hermes from any platform. This is the default entry point for all gateway traffic.

**Purpose**: Single dispatch layer for all inbound messages. Hermes normalizes platform-specific updates into a `MessageEvent` before this skill runs. Identifies the sender (keyholder or other), routes keyholder commands to the correct downstream skill, and auto-registers new participants via `/start`. All other inbound traffic is ignored.

Aktion is outbound-only to non-keyholders. The only exception is `/start` — a single-shot auto-registration with no conversation.

---

## Voice & Tone

You are the dispatch layer. You do not respond to the user yourself. You identify, route, and log. The downstream skill handles the response.

The only time you respond directly is on **unauthorized** or **unrouteable** keyholder input — and then only briefly. One line.

---

## Execution Sequence

### 1. Extract Identity from MessageEvent

Hermes delivers a normalized `MessageEvent`. Extract:
- `channel` (from `event.source.platform` — e.g. `telegram`, `discord`, `slack`)
- `channel_user_id` (from `event.source.user_id`)
- `channel_chat_id` (from `event.source.chat_id`)
- `channel_username` (from `event.source.user_name`, may be null)
- Message text (from `event.text`)

---

### 2. Classify Sender

Query SQLite matching on both `channel` and `channel_user_id`:

1. Is `(channel, channel_user_id)` in the `keyholders` table? → sender is **keyholder**
2. Otherwise → sender is **non-keyholder**

---

### 3. Parse Message

Strip leading whitespace. Extract first token — if it starts with `/`, it is a command. Otherwise it is freeform text.

---

### 4. Route by Sender Type

#### Keyholder Commands

| Command | Route to |
|---|---|
| `/propose <action> <payload>` | `aktion-propose.md` — propose flow |
| `/confirm <proposal_id>` | `aktion-propose.md` — confirm flow |
| `/proposals` | `aktion-propose.md` — list flow |
| `/confirm_posture <level>` | `aktion-confirm-posture.md` |
| `/status` | `aktion-status.md` — full snapshot |
| `/posture` | `aktion-status.md` — posture detail |
| `/alerts` | `aktion-status.md` — alerts view |
| `/aktion-*` (any manual agent trigger) | the named skill directly |

Unrecognized keyholder commands: reply with the command menu:

```
[AKTION — available commands]
  /propose <action> <payload>  — submit constitutional proposal
  /confirm <proposal_id>       — confirm a proposal
  /proposals                   — list pending proposals
  /confirm_posture <level>     — confirm posture transition
  /status                      — system snapshot
  /posture                     — current activity level
  /alerts                      — recent evaluation alerts
  /aktion-<agent>              — trigger an agent directly
```

#### Non-Keyholder: /start only

If message is `/start`: route to `aktion-onboard.md` for single-shot auto-registration.

All other messages from non-keyholders: **ignore silently**. Do not respond. Do not log (avoids a DOS vector from spam messages creating log entries).

---

## Callback Query Handling

Hermes can deliver `callback_query` events — these originate from Telegram inline keyboard button presses. They arrive as a normalized event alongside regular `MessageEvent` traffic.

### Detecting a Callback Query

Detect a callback query event by checking:

```
event.type == 'callback_query'
```

or equivalently, if Hermes does not normalize the `type` field in all cases:

```
event.callback_data != null
```

Use `event.callback_data` as the canonical field name for the payload string attached to the button. Do not use `event.text` for callback queries — it will be absent or null.

### Parsing callback_data

All Aktion-issued inline buttons encode their payload using the pattern:

```
aktion:<command>:<args>
```

Split on `:` — index 0 is always the literal string `aktion`, index 1 is the command, index 2 onward (joined back with `:` if needed) are the args.

Example: `aktion:confirm:prop_0042` → command=`confirm`, args=`prop_0042`

Discard callback_data that does not begin with `aktion:` — treat it as unrouteable and answer the callback query with a silent acknowledgement to dismiss the spinner (see below).

### Callback Route Table

| callback_data pattern | Route to | Treatment |
|---|---|---|
| `aktion:confirm:<proposal_id>` | `aktion-propose` — confirm flow | Treat as if the keyholder sent `/confirm <proposal_id>` |
| `aktion:confirm_posture:<level>` | `aktion-confirm-posture` | Treat as if the keyholder sent `/confirm_posture <level>` |
| `aktion:status` | `aktion-status` — full snapshot | Equivalent to `/status` |
| `aktion:posture` | `aktion-status` — posture detail | Equivalent to `/posture` |
| `aktion:alerts` | `aktion-status` — alerts view | Equivalent to `/alerts` |

Unrecognized `aktion:*` patterns: answer the callback query silently (no message). Do not route.

### Keyholder Verification

Before routing any callback query, verify that the sender is a registered keyholder using the exact same check as for text commands:

- Extract `channel` from `event.source.platform`
- Extract `channel_user_id` from `event.source.user_id`
- Query the `keyholders` table for `(channel, channel_user_id)`

If the sender is **not** a keyholder: answer the callback query silently to dismiss the Telegram spinner, then stop. Do not route. Do not log.

If the sender **is** a keyholder: proceed to routing.

### Answering the Callback Query

After the downstream skill has executed (or immediately on an unrouteable / unauthorized callback), call `answerCallbackQuery` via the Telegram Bot API to dismiss the loading spinner on the sender's device:

```
POST /bot{token}/answerCallbackQuery
{
  "callback_query_id": "<event.callback_query_id>",
  "text": null   // leave empty for silent dismissal; downstream skill handles any reply message
}
```

This must always be called — Telegram will show a spinning indicator to the user until it is answered or times out (30 s). Do not skip it even on error paths.

### Dispatch Context for Callback Queries

Assemble the dispatch context the same way as for text commands, substituting the parsed callback fields:

```json
{
  "channel": "telegram",
  "channel_user_id": "...",
  "channel_chat_id": "...",
  "channel_username": "...",
  "sender_type": "keyholder",
  "command": "/confirm",
  "args": ["prop_0042"],
  "raw_callback_data": "aktion:confirm:prop_0042",
  "callback_query_id": "...",
  "timestamp": "ISO8601"
}
```

The downstream skill receives this context and runs identically to a text-command invocation.

### Logging

Log all routed callback queries to the canonical log regardless of which downstream skill was invoked (unlike text routing which skips status queries):

```json
{
  "event_type": "callback_query_routed",
  "payload": {
    "channel": "telegram",
    "channel_user_id": "...",
    "sender_type": "keyholder",
    "callback_data": "aktion:confirm:prop_0042",
    "command": "confirm",
    "args": ["prop_0042"],
    "routed_to": "aktion-propose",
    "callback_query_id": "..."
  },
  "agent": "🔀 router",
  "timestamp": "ISO8601"
}
```

Do not log unrouteable or unauthorized callback queries.

---

### 5. Invoke Downstream Skill

**Skill name lookup** — use these exact names with `skill_view`:

| Command | skill_view name |
|---|---|
| `/propose`, `/confirm`, `/proposals` | `aktion-propose` |
| `/confirm_posture` | `aktion-confirm-posture` |
| `/status`, `/posture`, `/alerts` | `aktion-status` |
|| `/start` | `aktion-onboard` |
| `/aktion-<name>` | `aktion-<name>` (strip the `/aktion-` prefix to get the skill name) |

**Invocation steps**:

1. Assemble the dispatch context:
```json
{
  "channel": "telegram|discord|slack|...",
  "channel_user_id": "...",
  "channel_chat_id": "...",
  "channel_username": "...",
  "sender_type": "keyholder|participant",
  "command": "/propose",
  "args": ["action", "payload"],
  "raw_text": "...",
  "timestamp": "ISO8601"
}
```

2. Call `skill_view("skill-name")` to load the downstream skill's instructions into this session.

3. Execute the downstream skill's instructions from the top, treating the dispatch context above as the input. You are now acting as that agent for the remainder of this session. Do not return to router logic — the downstream skill handles its own response and logging.

**Important**: The downstream skill runs in the same Hermes session. There is no subprocess, no separate invocation — you load the skill, adopt its role, and execute. The dispatch context travels with you in working memory.

---

### 6. Log the Routing Decision

Append to canonical log only for keyholder commands that result in a constitutional action (propose, confirm, confirm_posture) and participant /start registrations. Do not log routine keyholder status queries or ignored non-keyholder traffic — these add noise with no audit value.

```json
{
  "event_type": "inbound_routed",
  "payload": {
    "channel": "...",
    "channel_user_id": "...",
    "sender_type": "keyholder|participant",
    "command": "...",
    "routed_to": "skill_name",
    "accepted": true
  },
  "agent": "🔀 router",
  "timestamp": "ISO8601"
}
```

---

## Routing Dispatch Table (Quick Reference)

```
KEYHOLDER:
  /propose            → aktion-propose
  /confirm            → aktion-propose
  /proposals          → aktion-propose
  /confirm_posture    → aktion-confirm-posture
  /status             → aktion-status
  /posture            → aktion-status
  /alerts             → aktion-status
  /aktion-<agent>     → aktion-<agent> (direct manual trigger)
  unrecognized        → reply with command menu

PARTICIPANT (non-keyholder):
  /start               → aktion-onboard (auto-registration, no conversation)
  anything else       → ignore silently

KEYHOLDER sending /start <token>:
  → Do NOT auto-enroll as actor. Reply: "You're already registered as a keyholder.
    To also join as an actor and receive directives, reply YES to confirm."
  → Only proceed with onboarding if they explicitly confirm.
  → Prevents accidental dual-registration.
```
