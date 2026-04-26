# Skill: aktion-router

**Trigger**: Any inbound message delivered by Hermes from any platform. This is the default entry point for all gateway traffic.

**Purpose**: Single dispatch layer for all inbound messages. Hermes normalizes platform-specific updates into a `MessageEvent` before this skill runs. Identifies the sender (keyholder or other), routes keyholder commands to the correct downstream skill, and auto-registers new participants via referral token. All other inbound traffic is ignored.

Aktion is outbound-only to non-keyholders. The only exception is `/start <token>` — a single-shot auto-registration with no conversation.

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

If message is `/start <token>`: route to `aktion-onboard.md` for single-shot auto-registration.

All other messages from non-keyholders: **ignore silently**. Do not respond. Do not log (avoids a DOS vector from spam messages creating log entries).

---

### 5. Invoke Downstream Skill

**Skill name lookup** — use these exact names with `skill_view`:

| Command | skill_view name |
|---|---|
| `/propose`, `/confirm`, `/proposals` | `aktion-propose` |
| `/confirm_posture` | `aktion-confirm-posture` |
| `/status`, `/posture`, `/alerts` | `aktion-status` |
| `/start <token>` | `aktion-onboard` |
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
  /start <token>      → aktion-onboard (auto-registration, no conversation)
  anything else       → ignore silently
```
