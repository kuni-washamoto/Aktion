# Skill: aktion-exit

**Trigger**: Keyholder runs `/aktion-exit <actor_id>` to deregister a participant, or as part of a `remove_actor` constitutional proposal execution.

**Purpose**: Deregister a participant. Finalize open tasks, revoke their referral token, mark them inactive, notify π_g, log the event.

Participants cannot self-deregister — there is no `/exit` command for participants. Deregistration is a keyholder action.

---

## Voice & Tone

Neutral and procedural. You do not contact the deregistered participant.

---

## Execution Sequence

### 1. Validate and Load Context

Look up participant by `actor_id`:
- If not found or `status` already `inactive` or `suspended`: reply "No active registration found for that ID." — halt.
- If found: load the actor record, open directives, performance ledger, and active referral token.

---

### 2. Finalize Open Tasks

For each directive assigned to this participant with status in (`pending`, `delivered`, `acknowledged`):

- Set `status = cancelled` with reason: `participant_removed`
- Append to canonical log for πᵣ reallocation:

```json
{
  "event_type": "task_reallocation_required",
  "payload": {
    "directive_id": "...",
    "former_actor_id": "...",
    "reason": "participant_removed"
  },
  "agent": "🚪 πₐ",
  "timestamp": "ISO8601"
}
```

---

### 3. Revoke Referral Token

```sql
UPDATE referral_tokens
SET status = 'revoked'
WHERE actor_id = '{actor_id}' AND status = 'active'
```

Participants recruited by this actor remain active. Referral chain topology is not rewritten.

---

### 4. Update Participant Record

```sql
UPDATE actors
SET status = 'inactive'
WHERE id = '{actor_id}'
```

The record is preserved for audit and possible re-activation.

---

### 5. Notify π_g

```json
{
  "event_type": "network_topology_change",
  "payload": {
    "change_type": "participant_exit",
    "actor_id": "...",
    "chain_depth": N,
    "recruits_count": N
  },
  "agent": "🚪 πₐ",
  "timestamp": "ISO8601"
}
```

---

### 6. Append Exit Event to Canonical Log

```json
{
  "event_type": "participant_exit",
  "payload": {
    "actor_id": "...",
    "channel": "...",
    "channel_user_id": "...",
    "initiated_by": "keyholder",
    "open_tasks_cancelled": N,
    "referral_token_revoked": "..."
  },
  "agent": "🚪 πₐ",
  "timestamp": "ISO8601"
}
```

Confirm to keyholder: "Participant {actor_id} deregistered. {N} open tasks cancelled and queued for reallocation."
