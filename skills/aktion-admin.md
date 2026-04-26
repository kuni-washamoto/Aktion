# Skill: aktion-admin

**Trigger**: Keyholder sends `/aktion-admin <command>` or `/aktion-reset`.

**Purpose**: Administrative CRUD interface for keyholders. View and manage participants, goals, tasks, and the activity log. Reset the system. All operations are read-only except reset and purge — which require explicit confirmation.

---

## Voice & Tone

Neutral and procedural. Output is structured data. No commentary.

---

## Commands

### `/aktion-admin goals`

List all goals with status:

```python
import sqlite3, json
conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))  # path from system_config if different
rows = conn.execute("""
  SELECT id, description, status, priority, deadline
  FROM goals
  ORDER BY priority ASC, status ASC
""").fetchall()
conn.close()
```

Output:
```
GOALS

[{id_short}] {description truncated to 60 chars}
  Status: {status}  Priority: {N}  Deadline: {date or none}

{repeat}

Total: N
```

---

### `/aktion-admin participants`

List all participants with status and last directive:

```python
import sqlite3, json
conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))
rows = conn.execute("""
  SELECT a.id, a.channel, a.channel_username, a.status,
         a.trust_tier, a.registered_at,
         pl.directives_received, pl.directives_completed, pl.quality_score,
         pl.status_recommendation
  FROM actors a
  LEFT JOIN performance_ledger pl ON pl.actor_id = a.id
  ORDER BY a.status ASC, a.registered_at DESC
""").fetchall()
conn.close()
```

Output:
```
PARTICIPANTS

[{id_short}] @{username or channel_user_id} ({channel})
  Status: {status}  Trust: {tier}  Registered: {date}
  Tasks: {received} received / {completed} completed  Score: {quality_score:.2f}
  Recommendation: {status_recommendation}

{repeat}

Total: N active / N flagged / N suspended / N inactive
```

---

### `/aktion-admin tasks [--status pending|delivered|complete|failed] [--limit N]`

List tasks, optionally filtered. Default: pending and delivered, limit 20.

```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))
rows = conn.execute("""
  SELECT d.id, d.type, d.status, d.payload, d.deadline,
         d.issued_at, a.channel_username, a.channel
  FROM directives d
  LEFT JOIN actors a ON a.id = d.target_actor_id
  WHERE d.status IN ('pending','delivered')  -- adjust per args
  ORDER BY d.issued_at DESC
  LIMIT 20
""").fetchall()
conn.close()
```

Output:
```
TASKS

[{id_short}] {type} → @{username} ({channel})
  Status: {status}  Issued: {date}  Deadline: {date or none}
  Payload: {truncated to 80 chars}

{repeat}

Showing N of N total matching
```

---

### `/aktion-admin log [N]`

Show last N entries from the activity log. Default N=10, max 50.

```python
import sqlite3, json
conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))
rows = conn.execute("""
  SELECT id, event_type, agent, timestamp, payload
  FROM canonical_log
  ORDER BY timestamp DESC
  LIMIT ?
""", (n,)).fetchall()
conn.close()
```

Output:
```
ACTIVITY LOG (last N)

#{id} [{timestamp}] {event_type} — {agent}
  {payload summary — first 100 chars of JSON}

{repeat}
```

---

### `/aktion-admin broadcast <message>`

Send a message to all active participants across all channels.

```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))
rows = conn.execute("""
  SELECT id, channel, channel_chat_id, channel_username
  FROM actors
  WHERE status = 'active' AND onboarding_status = 'complete'
  ORDER BY channel ASC
""").fetchall()
conn.close()
```

Send `<message>` to each `channel_chat_id` via Hermes. Hermes routes to the correct platform adapter automatically.

Track successes and failures. After all sends complete, report to keyholder:

```
BROADCAST COMPLETE

Sent:    N
Failed:  N  {list failed channel_user_ids if any}
Message: "{first 60 chars of message}..."
```

Append to canonical log:
```json
{
  "event_type": "broadcast_sent",
  "payload": {
    "message_preview": "{first 60 chars}",
    "recipients": N,
    "failures": N
  },
  "agent": "🔧 admin",
  "timestamp": "ISO8601"
}
```

---

### `/aktion-admin purge-participant <actor_id>`

Reply to keyholder first:
> "This will permanently delete participant `{actor_id}` and their ledger record. Their tasks will be left in place but unassigned. Type **CONFIRM** to proceed."

Wait for CONFIRM. On anything else: abort.

On CONFIRM:
```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))
conn.execute("DELETE FROM performance_ledger WHERE actor_id = ?", (actor_id,))
conn.execute("DELETE FROM social_media_actor_profiles WHERE actor_id = ?", (actor_id,))
conn.execute("DELETE FROM referral_tokens WHERE actor_id = ?", (actor_id,))
conn.execute("UPDATE directives SET target_actor_id = NULL, status = 'pending' WHERE target_actor_id = ? AND status IN ('pending','delivered')", (actor_id,))
conn.execute("DELETE FROM actors WHERE id = ?", (actor_id,))
conn.commit()
conn.close()
```

Append to canonical log:
```json
{
  "event_type": "participant_purged",
  "payload": { "actor_id": "..." },
  "agent": "🔧 admin",
  "timestamp": "ISO8601"
}
```

Confirm: "Participant `{actor_id}` purged."

---

### `/aktion-reset`

Wipe and reinitialize the entire system. Maximum destructive operation.

Confirm in two steps:

Step 1 — reply:
> "⚠️ This will permanently delete ALL data — goals, participants, tasks, activity log, proposals, everything. This cannot be undone.
>
> Type **RESET** to continue to the final confirmation."

Wait for RESET. On anything else: abort.

Step 2 — reply:
> "Last chance. Type **CONFIRM RESET** to wipe the system."

Wait for CONFIRM RESET. On anything else: abort.

On CONFIRM RESET — execute via Python using /opt/homebrew/bin/python3 (required for sqlite-vec):

```python
import sqlite3
import sqlite_vec

conn = sqlite3.connect(os.path.expanduser('~/.aktion/aktion.db'))
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

tables = [
  'goals', 'state_entities', 'state_relations', 'state_assertions',
  'actors', 'keyholders', 'directives', 'performance_ledger',
  'escalation_policy', 'posture_log', 'referral_tokens',
  'collection_requirements', 'intelligence_reports', 'canonical_log',
  'constitutional_proposals', 'intelligence_sources', 'io_campaigns',
  'social_media_actor_profiles', 'operational_phases', 'system_config',
  'embeddings'
]
for table in tables:
    conn.execute(f"DROP TABLE IF EXISTS {table}")
conn.commit()
conn.close()
```

Confirm: "System wiped. Run `/aktion-init` to reinitialize."

---

## Notes

- DB path: `~/.aktion/aktion.db` — read from `system_config` if a different path was set at init time. Fall back to this default.
- Always use `/opt/homebrew/bin/python3` for any operation that touches the `embeddings` table (requires sqlite-vec). For read-only queries on other tables, system python is fine.
- All destructive operations (purge, reset) require double confirmation before execution.
- No writes to canonical log for read-only commands — log only purge and reset events.
