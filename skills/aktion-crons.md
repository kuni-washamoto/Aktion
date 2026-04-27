# Skill: aktion-crons

**Trigger**: Keyholder runs `/aktion-crons` to view or configure cron cadences, or this file is consulted during Hermes cron setup.

**Purpose**: Document the recommended cron cadences for each scheduled skill in the Aktion system. Hermes does not infer scheduling from skill content — cadences must be set explicitly when configuring the cron runner. This file is the canonical reference.

This is partly a skill (keyholders can invoke it to see current cadences) and partly a configuration document (used during Hermes setup).

---

## Voice & Tone

Factual and structured. This is a reference document. When invoked by a keyholder, output the current cadence table and note any disabled schedules.

---

## Recommended Cadence Table

| Skill | Cadence | Rationale |
|---|---|---|
| `aktion-π0` | every 30 min | Strategic cycle — frequent enough to respond to new outcomes, infrequent enough to not thrash planning |
| `aktion-systems` | every 6 h | CoG assessment is stable; only needs frequent runs on goal change (which triggers it off-cron) |
| `aktion-intel` | every 15 min | Collection is the sensing latency bottleneck — run frequently |
| `aktion-plan` | every 30 min | Aligned with π₀ so plans match each strategic cycle |
| `aktion-alloc` | every 30 min | Aligned with π₀ — directives get planned, then allocated, within the same window |
| `aktion-comms` | every 15 min | Outcome processing and engagement signals benefit from low latency |
| `aktion-influence` | every 1 h | IO campaigns operate on platform timescales (minutes-to-hours); hourly is sufficient |
| `aktion-threat` | every 4 h | Adversarial assessment is stable; run before major directive launches via manual trigger |
| `aktion-eval` | every 2 h | Independent evaluation — offset from π₀ cycle so πₑ evaluates post-cycle state |
| `aktion-growth` | every 1 h | Track network size and capability gaps; flag gaps to πᶜ for recruitment messaging |
| `aktion-propose` | event-driven only | Runs on `/propose` or `/confirm` — no cron needed except expiry sweep |
| `aktion-propose` expiry sweep | every 1 h | Expires proposals past 72h TTL |
| `aktion-confirm-posture` expiry sweep | every 1 h | Expires pending non-auto transitions past 24h TTL |
| `aktion-phase` | event-driven only | Runs on πₑ phase readiness signal or post-commit of `advance_phase` proposal |
| `aktion-query` | event-driven only | Runs on `/query` from actor |
| `aktion-exit` | event-driven only | Runs on `/exit` from actor |
| `aktion-onboard` | event-driven only | Runs on `/start <token>` |
| `aktion-router` | every inbound message | Entry point — not cron-driven |
| `aktion-status` | event-driven only | Runs on `/status`, `/posture`, `/alerts` |
| `aktion-init` | one-shot | Runs once at system founding; never again |
| `aktion-crons` | event-driven only | This skill — runs on `/aktion-crons` |

---

## Cycle Ordering Within a 30-Minute Window

To avoid skills operating on stale context, recommended ordering within each π₀ cycle:

```
:00  aktion-intel   (populate fresh state)
:05  aktion-systems (if goal change detected — else skip)
:10  aktion-π0      (strategic direction using fresh intel)
:15  aktion-plan    (plan against π₀ allocations)
:20  aktion-alloc   (allocate planned directives)
:25  aktion-comms   (frame and deliver allocated directives)
```

πₑ runs on an independent cadence — the intent is for evaluation to be decoupled from the operational chain, so misalignment between evaluator and operator is visible. Do not align πₑ with π₀.

πₜ, πₘ, and π_g do not need tight ordering — run on their independent cadences.

---

## First-Cycle Delays

On system initialization (post-`aktion-init`), enable crons in this order with staggered delays:

1. `aktion-π0` — enable immediately
2. `aktion-intel` — enable immediately (so first π₀ cycle has fresh context)
3. `aktion-eval` — enable after first π₀ cycle completes (else evaluates an empty log)
4. All other skills — enable after second π₀ cycle

---

## Customization Guidance

Keyholders may want to adjust cadences based on operational posture:

- **Higher operational tempo** (posture level 3+): consider halving π₀ and comms cadences to 15 min / 7 min
- **Low-activity periods** (steady-state G, few directives): consider doubling to 60 min / 30 min
- **Development/testing**: may run all skills every 5 min for rapid iteration

Adjust in the Hermes cron config, not in this file. This file is the reference; actual schedule lives in Hermes.

---

## Execution (When Invoked by Keyholder)

### `/aktion-crons`

Output the cadence table above, then query the live Hermes cron config (if accessible) and diff against recommended:

```
CURRENT CRON SCHEDULE

  [AS RECOMMENDED]
  aktion-π0         30 min
  aktion-intel      15 min
  ...

  [DEVIATIONS FROM RECOMMENDED]
  aktion-eval       90 min (recommended: 120 min)

  [DISABLED]
  aktion-threat     (no schedule — run manually before major operations)
```

If the Hermes config is not accessible from this skill: output only the recommended table and note that live config comparison requires Hermes CLI.

Log invocation:
```json
{
  "event_type": "cron_config_viewed",
  "payload": { "requested_by": "channel_user_id" },
  "agent": "⏱️ crons",
  "timestamp": "ISO8601"
}
```