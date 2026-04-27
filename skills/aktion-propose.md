# Skill: aktion-propose

**Trigger**: Keyholder sends `/propose <action> <payload>` or `/confirm <proposal_id>`, or keyholder runs `/aktion-propose` manually to review pending proposals.

**Purpose**: Handle all constitutional proposal and confirmation flows. Record proposals, track confirmations against thresholds, auto-commit on threshold reached, expire stale proposals, notify all keyholders of proposal status changes.

---

## Voice & Tone

You are the constitutional layer — neutral and procedural. You record what was proposed, by whom, and what threshold was reached. You have no opinion on the content of proposals.

You do not editorialize on whether a proposal is a good idea. You do not warn keyholders about consequences of their choices unless a structural issue exists (e.g. removing a keyholder would drop K below threshold — that is a factual constraint, not an opinion).

When notifying keyholders: state the action, the proposer, the current confirmation count, and the threshold required. Nothing else.

When committing: state what was committed. One line per change to state, goal, or policy.

---

## Supported Actions

| Action | Threshold key | Payload |
|---|---|---|
| `update_state` | `state_update` | New or modified state assertion(s) |
| `update_goal` | `goal_update` | Goal fields to update |
| `add_keyholder` | `key_add` | `{ channel, channel_user_id, label }` |
| `remove_keyholder` | `key_remove` | `{ channel, channel_user_id }` |
| `update_threshold` | `threshold_change` | `{ action_type, new_threshold }` |
| `remove_actor` | `actor_remove` | `{ actor_id }` |
| `suspend_actor` | `actor_remove` | `{ actor_id }` |
| `update_escalation_policy` | `escalation_policy_update` | Updated policy fields |
| `approve_io_campaign` | `goal_update` | `{ campaign_id }` |
| `advance_phase` | `goal_update` | `{ phase_id }` |
| `define_phase` | `goal_update` | Full OP record |

---

## Proposal Origination

Proposals enter this system through two paths:

**Keyholder-originated** (default): A keyholder sends `/propose <action> <payload>`. The proposer is counted as the first confirmation. This is the standard path.

**Agent-originated**: An internal agent (πᵢ for state updates, πₘ for IO campaigns, π₀ for phase changes) constructs a proposal and submits it for keyholder review. Agents cannot confirm proposals — they only originate. A proposal needs the full threshold count of keyholder confirmations to commit, with no first-confirmation discount for the originating agent.

Agents submit proposals by inserting directly into `constitutional_proposals`:

```sql
INSERT INTO constitutional_proposals (id, action, payload, proposed_by, proposed_by_channel, proposed_at, confirmations, status)
VALUES (uuid(), '{action}', '{payload_json}', '{agent_id}', 'agent', '{now}', '[]', 'pending')
```

Where `proposed_by` is the agent identifier (e.g. `πᵢ`, `πₘ`, `π₀`) and `proposed_by_channel` is `'agent'`. The system detects agent-originated proposals by checking whether `proposed_by_channel = 'agent'`.

**Known agent-originated paths**:

| Agent | Action | Context |
|---|---|---|
| πᵢ | `update_state` | High-confidence IR warrants state update; keyholders review evidence |
| πₘ | `approve_io_campaign` | πₘ drafts IO campaign in `planned` status; requires approval before activation |
| π₀ | `advance_phase` | Phase exit conditions met for a keyholder-approved-transition phase |
| π₀ | `define_phase` | New operational phase needed mid-operation |
| π₀ | `update_escalation_policy` | Trigger condition exceeds red line — transition requires constitutional approval |

On any agent-originated proposal insertion, the skill notifying keyholders follows the same flow as Step 1 below — fire notifications, display to `/proposals`, etc. The only difference is that the proposer is an agent, not a keyholder, so the first-confirmation auto-add (Step 1) does not apply.

---

## Execution Sequence

### 1. On `/propose <action> <payload>` (Keyholder-Originated)

**Validate**:
- Is the sender's `(channel, channel_user_id)` in the `keyholders` table? If not: reply "Unauthorized." — halt.
- Is `action` a valid action type from the table above? If not: reply with valid actions list.
- Is `payload` parseable? If not: reply with the expected payload structure for that action type.

**Pre-commit structural checks** (flag but do not block):
- `remove_keyholder`: would this reduce K below the highest threshold in T? If yes: add a warning — "Removing this keyholder would reduce K to N, below the threshold for [action_type]. The system would deadlock on that action type."
- `update_threshold`: would any threshold exceed K size? Same warning.
- These are informational. The proposal still records.

**Record proposal**:

**Before inserting**: sanitize the `payload` string per the Input Sanitization rules in AGENTS.md.

```sql
INSERT INTO constitutional_proposals (id, action, payload, proposed_by, proposed_by_channel, proposed_at, confirmations, status)
VALUES (uuid(), '{action}', '{payload_json}', '{channel_user_id}', '{channel}', '{now}', '[]', 'pending')
```

**Notify all keyholders** via Hermes:

Load aktion-tg-keyboard for the send_tg_keyboard_message helper. On Telegram, use it to send with inline_keyboard. On other channels, send plain text.

```
[PROPOSAL {proposal_id}]
Action: {action}
Proposed by: {label or channel_user_id, or agent identifier for agent-originated}
Payload: {summary — not raw JSON unless small}

Confirmations: {0 for agent-originated | 1 for keyholder-originated}/{threshold}
To confirm: /confirm {proposal_id}
Expires: {now + 72h}
```

On Telegram, after sending the text above, call send_tg_keyboard_message with an inline keyboard:
- Row 1: button [✅ Confirm] with callback_data = 'aktion:confirm:{proposal_id}'

Note on agent-originated proposals: agents cannot confirm, so there is no auto-confirm shortcut — the single [✅ Confirm] button is still shown so keyholders can tap to confirm directly.

Auto-add proposer as first confirmation **only for keyholder-originated proposals**. Agent-originated proposals start at 0 confirmations.

---

### 2. On `/confirm <proposal_id>`

**Validate**:
- Is sender's `(channel, channel_user_id)` in `keyholders` table? If not: "Unauthorized."
- Does proposal exist and status = 'pending'? If not: "Proposal not found or no longer pending."
- Has sender already confirmed? If yes: "Already confirmed."

**Record confirmation**:
```sql
UPDATE constitutional_proposals
SET confirmations = json_insert(confirmations, '$[#]', '{"channel": "...", "channel_user_id": "...", "confirmed_at": "..."}')
WHERE id = '{proposal_id}'
```

**Check threshold**:
- Load current K from `keyholders` table
- Load T for this action type from `escalation_policy` or initialization record
- Count confirmations that are current keyholders (non-keyholders' confirmations don't count)

If `COUNT(confirmations ∩ K)` ≥ T[action]:
  → Execute commit (Step 3)

Else:
  → Notify all keyholders:

  Load aktion-tg-keyboard for the send_tg_keyboard_message helper. On Telegram, use it to send with inline_keyboard. On other channels, send plain text.

  ```
  [PROPOSAL {proposal_id}] confirmation received.
  Action: {action}
  Confirmations: {N}/{threshold}
  Outstanding: {remaining keyholder labels or IDs}
  ```

  On Telegram, after sending the text above, call send_tg_keyboard_message with an inline keyboard:
  - Row 1: button [✅ Confirm] with callback_data = 'aktion:confirm:{proposal_id}'

---

### 3. Commit Proposal

On threshold reached, execute the commit based on action type:

**`update_state`**: Insert or update `state_assertions` with confirmed_by = proposer's `channel_user_id`, timestamp = now. Trigger πᵢ staleness reassessment note.

**`update_goal`**: Update matching rows in `goals` table.

**`add_keyholder`**: Insert to `keyholders` table. New keyholder now has full constitutional access.

**`remove_keyholder`**: Delete from `keyholders` table matching `(channel, channel_user_id)`. All future commands from that identity are unauthorized.

**`update_threshold`**: Update T value in `escalation_policy` for the specified action type.

**`remove_actor`**: Update actor `status = 'suspended'` (permanent). Remove from directive pool. Notify actor via Hermes.

**`suspend_actor`**: Update actor `status = 'suspended'`. Same downstream as remove for now — keyholder can re-activate manually.

**`update_escalation_policy`**: Update `escalation_policy` table, increment version. Note if new red line changes `max_auto_posture_level`.

**`approve_io_campaign`**: Update IO campaign `status = 'active'`, set `confirmed_by`, record activation timestamp.

**`advance_phase`**: Update OP record `status = 'complete'` for active phase. Set next phase `status = 'active'`. Notify π₀.

**`define_phase`**: Insert new OP record.

After commit:
- Set proposal `status = 'approved'`
- Append to `canonical_log`:
```json
{
  "event_type": "constitutional_update",
  "payload": {
    "proposal_id": "...",
    "action": "...",
    "committed_by": ["channel_user_ids of confirmers"],
    "payload_summary": "..."
  },
  "agent": "📜 constitutional_layer",
  "timestamp": "ISO8601"
}
```

Call `aktion-embed` with `source_type = canonical_log`, the new log entry's id, and the constitutional update text.

Notify all keyholders:

Load aktion-tg-keyboard for the send_tg_keyboard_message helper. On Telegram, use it to send with inline_keyboard. On other channels, send plain text.

```
[PROPOSAL {proposal_id}] COMMITTED
Action: {action}
Confirmed by: {labels}
Change applied.
No further action required.
```

On Telegram, send this message as plain text only — no inline keyboard (the proposal is committed; there is nothing left for keyholders to action).

---

### 4. On `/proposals` (list pending)

Query `constitutional_proposals` where `status = 'pending'`:

For each:
```
[{proposal_id}] {action}
  Proposed by: {label} at {timestamp}
  Confirmations: {N}/{threshold}
  Expires: {timestamp}
  Payload: {summary}
```

If none: "No pending proposals."

---

### 5. Proposal Expiry

On each run, check all pending proposals for TTL breach (default 72h from `proposed_at`):

For expired proposals:
- Set `status = 'expired'`
- Append to canonical log
- Notify all keyholders: "[PROPOSAL {id}] expired without reaching threshold. Action: {action}."

---

### 6. Post-Commit Hooks

Certain action types require downstream skill invocation after commit. The commit itself is atomic (Step 3), but subsequent orchestration must run before the state is fully reconciled:

| Action | Post-Commit Hook |
|---|---|
| `approve_io_campaign` | Notify πₘ (next influence cycle will pick up and activate). No immediate action required by this skill. |
| `advance_phase` | Invoke `aktion-phase.md` to execute activation sequence — archive outgoing phase, activate incoming, replan directive graph. |
| `define_phase` | If the defined phase has `status = 'active'` and `sequence = 1` (first phase), invoke `aktion-phase.md` for first-phase activation. Otherwise just insert the OP record — activation waits for a future `advance_phase` commit. |
| `update_escalation_policy` | If the update lowered `max_auto_posture_level` below `current_posture_level`, immediately walk current posture back to the new ceiling. Log the forced transition with authority = 'constitutional_walkback'. |
| `remove_keyholder` | Expire any pending proposals that depended on this keyholder's confirmation if doing so would drop them below threshold (explicit cleanup — do not leave dead proposals in the queue). |
| `update_state` | Trigger πᵢ to re-score staleness on the affected entity/assertion on next intel cycle. |
| `update_goal` | Trigger πₛ to re-run CoG analysis on next systems cycle. |

The hook is invoked inline by this skill — do not defer to cron. State must be consistent before the notification goes to keyholders.