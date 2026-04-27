# Skill: aktion-confirm-posture

**Trigger**: Keyholder sends `/confirm_posture <level>` in response to a π₀ alert requesting posture transition confirmation.

**Purpose**: Handle keyholder confirmation of posture transitions that require human approval because the trigger had `auto_execute: false` — but the target level is still within the red line. This is distinct from constitutional posture changes that exceed the red line (those go through `aktion-propose.md` as `update_escalation_policy`).

A pending non-auto transition exists in the `posture_log` as a row with `authority = 'pending_keyholder'` and `to_level` set but not yet committed to `escalation_policy.current_posture_level`.

---

## Voice & Tone

Neutral and procedural — like `aktion-propose.md`. Record the confirmation, check threshold, commit or wait.

You do not opine on whether the posture transition is warranted. πᵢ and π₀ have already judged the signals. Keyholders are confirming the operational response, not debating the evidence.

When notifying keyholders: state the pending transition, the target level, the remaining confirmations required, and the trigger signal that prompted the alert.

---

## Supported Transitions

| Path | Handler |
|---|---|
| Auto trigger + within red line | `aktion-π0.md` commits immediately |
| Non-auto trigger + within red line | **This skill** — requires `T[escalation_policy_update]` keyholder confirmations via `/confirm_posture` |
| Any trigger + exceeds red line | `aktion-propose.md` — constitutional `update_escalation_policy` proposal |

The threshold used here is the same as `escalation_policy_update` in `T`. Use that value for consistency — posture transitions and policy edits share a governance tier.

---

## Execution Sequence

### 1. On `/confirm_posture <level>`

**Validate**:
- Is the sender's Telegram user ID in `keyholders`? If not: reply "Unauthorized." — halt.
- Is `level` a valid posture level defined in current `escalation_policy.postures`? If not: reply with valid levels.
- Is there a pending non-auto transition matching this level? Query `posture_log` for the most recent row where `authority = 'pending_keyholder'` and `to_level = <level>`. If none: reply "No pending posture transition to level {N}." — halt.
- Has the sender already confirmed this pending transition? Check an `acting_confirmations` JSON array on the pending row. If yes: "Already confirmed."

---

### 2. Record Confirmation

Update the pending `posture_log` row:

```sql
UPDATE posture_log
SET acting_confirmations = json_insert(
  COALESCE(acting_confirmations, '[]'),
  '$[#]',
  json_object('channel', '{channel}', 'channel_user_id', '{sender_id}', 'confirmed_at', '{now}')
)
WHERE id = '{pending_row_id}'
```

(If `acting_confirmations` column does not exist in the schema as originally created: store confirmations in a parallel JSON row in canonical log and count them there. Both approaches work — use whichever the init schema supports. Flag any schema gap to keyholders.)

---

### 3. Check Threshold

Load `T[escalation_policy_update]` from the current escalation policy (or from the initialization record).

Count confirmations on the pending row whose `(channel, channel_user_id)` is currently in `keyholders`.

If `COUNT(valid confirmations) >= T[escalation_policy_update]`:
  → Commit transition (Step 4)

Else:
  → Load aktion-tg-keyboard for the send_tg_keyboard_message helper. On Telegram, use it with inline_keyboard. On other channels, plain text.

  → Notify all keyholders:

```
[POSTURE TRANSITION PENDING] L{from} → L{to}
Trigger: {signal_type}: {condition}
Confirmations: {N}/{threshold}
Outstanding: {remaining keyholder labels}

To confirm: /confirm_posture {level}
```

On Telegram, attach an inline keyboard to each keyholder notification:

```
inline_keyboard:
  - row 1: [✅ Approve L{level}]  callback_data: "aktion:confirm_posture:{level}"
```

---

### 4. Commit the Transition

Execute the transition:

```sql
UPDATE escalation_policy
SET current_posture_level = {to_level},
    updated_at = '{now}'
WHERE id = (SELECT id FROM escalation_policy ORDER BY version DESC LIMIT 1)
```

Update the pending posture_log row:
```sql
UPDATE posture_log
SET authority = 'keyholder_confirmed'
WHERE id = '{pending_row_id}'
```

Append to canonical log:

```json
{
  "event_type": "posture_transition",
  "payload": {
    "from_level": N,
    "to_level": N,
    "trigger_signal": "...",
    "authority": "keyholder_confirmed",
    "confirming_keyholders": ["channel_user_ids"],
    "within_red_line": true
  },
  "agent": "📜 constitutional_layer",
  "timestamp": "ISO8601"
}
```

Call `aktion-embed` with `source_type = posture_transition`, `source_id` = the posture_log row id, and text: `"Posture transition L{from_level} → L{to_level}. Trigger: {trigger_signal}. Authority: keyholder_confirmed."`

Load aktion-tg-keyboard for the send_tg_keyboard_message helper. On Telegram, use it with inline_keyboard. On other channels, plain text.

Notify all keyholders (send with NO inline keyboard buttons):

```
[POSTURE TRANSITION COMMITTED] L{from} → L{to}
Confirmed by: {labels}
Operational parameters now in effect:
  Tempo: ×{multiplier}
  Capability floor: {standard|elevated}
  Max parallel directives: {N|unlimited}

No further action required.
```

π₀ will pick up the new posture level on its next strategic cycle and scale operations accordingly.

---

### 5. Expiry

If a pending non-auto transition has been sitting in `posture_log` for more than 24h without reaching threshold:

- Update the row: `authority = 'expired'`
- Append to canonical log: trigger condition was flagged, transition was not confirmed in time, system remains at current posture
- Notify keyholders: "[POSTURE TRANSITION EXPIRED] L{from} → L{to} — not confirmed within 24h. System remains at L{from}. πᵢ will re-evaluate trigger on next intel cycle."

The short TTL is deliberate — posture transitions are time-sensitive. A transition that doesn't get confirmed in a day is almost certainly not going to be confirmed at all, and the trigger conditions may have already shifted.