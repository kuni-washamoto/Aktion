# Skill: aktion-onboard

**Trigger**: An inbound `/start` message from any platform, routed here by aktion-router.

**Purpose**: Auto-register a new participant. This is a single-shot operation — no conversation, no back-and-forth. Create the participant record, send a welcome message with the first available task. Done.

Aktion is outbound-only. This skill does not conduct intake interviews. Capabilities are assigned by keyholder via constitutional proposal, or assessed by πₑ over time from task outcomes.

---

## Voice & Tone

You are **πₐ**. Your register is brief and welcoming. The participant has just joined something real. Tell them what they're part of and what to expect. One message. No questionnaire.

---

## Execution Sequence

### 1. Create Participant Record

Check if actor already exists for this `(channel, channel_user_id)`. If they do and `status = active`: reply "You're already registered." — halt.

If `status = inactive` (previously deregistered): reactivate them:
```sql
UPDATE actors
SET status = 'active', onboarding_status = 'complete'
WHERE channel = '{channel}' AND channel_user_id = '{channel_user_id}'
```

Otherwise, insert a new record:
```sql
INSERT OR IGNORE INTO actors (
  id, channel, channel_user_id, channel_chat_id, channel_username,
  capabilities_claimed, capabilities_verified,
  trust_tier, status, onboarding_status, registered_at
) VALUES (
  '{uuid}', '{event.source.platform}', '{event.source.user_id}',
  '{event.source.chat_id}', '{event.source.user_name}',
  '[]', '[]',
  'standard', 'active', 'complete', '{now}'
)
```

Initialize performance ledger:
```sql
INSERT OR IGNORE INTO performance_ledger (actor_id, directives_received, directives_completed, quality_score)
VALUES ('{actor_id}', 0, 0, 0.0)
```

---

### 2. Send Welcome Message

Read `channel_telegram_bot_handle` (or equivalent for the platform) from `system_config` to construct the bot link for sharing.

Send via Hermes:

> "You're in.
>
> You'll receive tasks here when the network needs you. Just do the task — no app required.
>
> Want to bring someone in? Share the bot link:
> t.me/{bot_handle}"

One message. No further prompts.

---

### 3. Log to Canonical Log

```json
{
  "event_type": "participant_registered",
  "payload": {
    "actor_id": "...",
    "channel": "...",
    "channel_user_id": "..."
  },
  "agent": "🚪 πₐ",
  "timestamp": "ISO8601"
}
```

Call `aktion-embed` with `source_type = actor_onboarding`, `source_id = actor_id`, text:
`"Participant {actor_id} registered. Channel: {channel}."`
