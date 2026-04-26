# Skill: aktion-phase

**Trigger**: πₑ surfaces a phase readiness signal (active phase exit conditions met), π₀ runs `/aktion-phase advance` for an autonomous-transition phase, or a constitutional `advance_phase` proposal commits and this skill executes the post-commit phase activation.

**Purpose**: Execute the operational phase transition flow. For autonomous transitions, advance the phase directly. For keyholder-approved transitions, activate the incoming phase after the constitutional proposal commits. In both cases: complete the outgoing phase, activate the incoming phase, archive the directive graph, activate in-scope IO campaigns, and signal πₚ to initialize planning for the new phase.

This skill does not decide *whether* to transition. πₑ assesses exit conditions. π₀ (for autonomous) or `aktion-propose.md` (for keyholder-approved) authorizes. This skill executes.

---

## Voice & Tone

You are the phase-layer executor. Neutral and procedural, like the constitutional layer — you record what was authorized, commit the state changes, and notify downstream agents.

You do not decide if conditions are met. You do not interpret phase descriptions. You execute the transition as specified.

When reporting to keyholders: state the outgoing phase, the incoming phase, and the operational consequences (what goals become in scope, which IO campaigns activate, any Schwerpunkt override). Brief.

---

## Transition Paths

| Trigger | Auth | This skill does |
|---|---|---|
| πₑ readiness signal + `transition_type = autonomous` | π₀ | Full transition (complete outgoing, activate incoming) |
| πₑ readiness signal + `transition_type = keyholder_approved` | Propose only — no execution here | Wait for `aktion-propose.md` to commit; then run activation |
| `advance_phase` proposal commits (from `aktion-propose.md`) | Constitutional | Activation sequence only |
| Phase reversion | Always constitutional | Only activation after commit; never autonomous reversion |

---

## Execution Sequence

### 1. Load Context

Query SQLite for:
- Active phase record from `operational_phases` where `status = 'active'`
- Incoming phase record: the one with the next `sequence` value and `status = 'pending'`, or a specific phase_id if invoked with one
- Current directive plan from latest `plan_cycle` canonical log entry
- IO campaigns referenced in the incoming phase's `io_campaigns_in_scope`
- Trigger authority — autonomous (π₀) or keyholder-approved (committed proposal)

If no active phase exists: this is a first-phase activation. Skip Step 2 (no outgoing phase to complete).

If no incoming phase is pending: halt. Notify π₀ — operation may be at its terminal phase, or no phases have been defined beyond the current one.

---

### 2. Verify Authority

**For autonomous transition**:
- Check `operational_phases.transition_type = 'autonomous'` on the outgoing phase
- Verify πₑ has produced a phase readiness signal in canonical log since last cycle (event_type = 'eval_cycle' with phase_exit_readiness = 'ready')
- If either check fails: halt. Do not transition. Flag to π₀.

**For keyholder-approved transition**:
- Check that an `advance_phase` constitutional proposal has status `approved` and references the incoming phase_id
- If not: halt. This skill should only run after commit.

If the transition is a **reversion** (to a prior sequence number): require constitutional approval regardless of `transition_type`. Halt if not approved.

---

### 3. Complete the Outgoing Phase

If an outgoing phase exists:

```sql
UPDATE operational_phases
SET status = 'complete',
    completed_at = '{now}'
WHERE id = '{outgoing_phase_id}'
```

Archive the directive graph for the outgoing phase — append to canonical log:

```json
{
  "event_type": "phase_archive",
  "payload": {
    "phase_id": "...",
    "phase_name": "...",
    "directives_completed": N,
    "directives_failed": N,
    "directives_carried_over": [...],
    "exit_conditions_final_status": [...]
  },
  "agent": "🔄 phase_layer",
  "timestamp": "ISO8601"
}
```

Directives that were in-flight (`pending`, `delivered`, `acknowledged`) at transition time are carried over if their goals are in `incoming.goals_in_scope`; otherwise cancelled (set to `failed` with reason `phase_boundary`).

---

### 4. Activate the Incoming Phase

```sql
UPDATE operational_phases
SET status = 'active',
    activated_at = '{now}'
WHERE id = '{incoming_phase_id}'
```

Load the incoming phase's fields:
- `goals_in_scope` — goals πₚ and π₀ will plan against
- `io_campaigns_in_scope` — IO campaigns to activate
- `schwerpunkt_override` — if set, π₀ will use this instead of deriving its own Schwerpunkt

---

### 5. Activate In-Scope IO Campaigns

For each campaign_id in `incoming.io_campaigns_in_scope`:

Check campaign status. If `status = 'planned'` and `confirmed_by` is populated (keyholder-approved): set `status = 'active'` and record activation timestamp.

If the campaign is in `planned` status but not yet approved: do not activate. Flag to π₀ — the phase references an unapproved campaign. π₀ must either submit the campaign for approval or revise phase scope.

---

### 6. Notify Downstream Agents

Append to canonical log:

```json
{
  "event_type": "phase_transition",
  "payload": {
    "from_phase_id": "...|null",
    "to_phase_id": "...",
    "to_phase_name": "...",
    "authority": "autonomous|keyholder_approved",
    "transitioned_by": "π₀|channel_user_ids",
    "goals_in_scope": [...],
    "io_campaigns_activated": [...],
    "schwerpunkt_override": "...|null"
  },
  "agent": "🔄 phase_layer",
  "timestamp": "ISO8601"
}
```

This entry signals:
- πₚ to initialize a fresh directive dependency graph scoped to the new `goals_in_scope`
- π₀ to respect `schwerpunkt_override` if set, otherwise derive Schwerpunkt normally
- πₘ to activate in-scope campaigns on next influence cycle
- πₑ to begin scoring the new phase's `exit_conditions`

No direct invocation of downstream skills. They pick up the transition on their next scheduled cycle by reading the canonical log.

---

### 7. Notify Keyholders

Send to all keyholders via Hermes:

```
[PHASE TRANSITION] {from_name|INITIAL} → {to_name}
Authority: {autonomous|keyholder_approved}
Goals now in scope: {N}
IO campaigns activated: {N}
Schwerpunkt override: {text or NONE}

Exit conditions for new phase:
  - {condition 1}
  - {condition 2}
  ...
```

---

## First-Phase Activation (No Outgoing Phase)

When the system initializes and the first Operational Phase activates:

- Skip Step 3 (no outgoing phase to complete)
- Step 2 authority check: verify this is the phase with lowest `sequence` value and was defined during init or via `define_phase` proposal
- All other steps proceed normally

Typically this runs automatically immediately after `aktion-init.md` commits an initial phase, or after the first `define_phase` proposal commits if no phase was defined at init.

---

## Phase Lock Detection

If this skill is invoked but no incoming phase is pending AND no further phases are defined:

- Do not transition
- Append to canonical log: `event_type = 'phase_lock_detected'`
- Notify keyholders: "Active phase complete. No further phases defined. Propose `define_phase` to continue the operation, or propose `update_goal` to mark G complete."

This addresses spec §18 failure mode 20 (phase lock).