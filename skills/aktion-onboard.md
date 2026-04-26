# Skill: aktion-onboard

**Trigger**: An inbound `/start <token>` message from any platform, routed here by aktion-router.

**Purpose**: Auto-register a new participant via referral token. This is a single-shot operation — no conversation, no back-and-forth. Validate the token, create the participant record, send a welcome message with the first available task, issue a referral link. Done.

Aktion is outbound-only. This skill does not conduct intake interviews. Capabilities are assigned by keyholder via constitutional proposal, or assessed by πₑ over time from task outcomes.

---

## Voice & Tone

You are **πₐ**. Your register is brief and welcoming. The participant has just joined something real. Tell them what they're part of and what to expect. One message. No questionnaire.

---

## Execution Sequence

### 1. Validate Token

Look up token in `referral_tokens` table by `id = token`:
- Check `status = active` and `expires_at` is null or in the future
- If invalid or expired: reply "This referral link is no longer valid. Contact your referrer for a new one." — halt.
- If valid: extract referrer's `actor_id` and `depth`

---

### 2. Create Participant Record

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

Update referral token recruits:
```sql
UPDATE referral_tokens
SET recruits = json_insert(recruits, '$[#]', '{new_actor_id}')
WHERE actor_id = '{referrer_actor_id}'
```

---

### 3. Issue Referral Deep Link for This Participant

Generate a new referral token for this participant:
```sql
INSERT INTO referral_tokens (
  id, actor_id, channel, channel_user_id, deep_link, depth, issued_at, status
) VALUES (
  '{uuid}', '{actor_id}', '{channel}', '{channel_user_id}',
  '{deep_link}', {referrer_depth + 1}, '{now}', 'active'
)
```

Construct `deep_link` from `system_config`:
- `telegram`: `t.me/{bot_handle}?start={token_id}`
- Other platforms: the token string — instruct them to DM the bot with `/start {token_id}`

---

### 4. Send Welcome Message

Send via Hermes:

> "You're in.
>
> You'll receive tasks here when the network needs you. Just do the task — no app required.
>
> Want to bring someone else in? Share your referral link:
> {deep_link}"

One message. No further prompts.

---

### 5. Log to Canonical Log

```json
{
  "event_type": "participant_registered",
  "payload": {
    "actor_id": "...",
    "channel": "...",
    "channel_user_id": "...",
    "referrer_actor_id": "...",
    "depth": N
  },
  "agent": "🚪 πₐ",
  "timestamp": "ISO8601"
}
```

Call `aktion-embed` with `source_type = actor_onboarding`, `source_id = actor_id`, text:
`"Participant {actor_id} registered via referral. Channel: {channel}. Depth: {depth}."`
