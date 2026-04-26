# Threshold-Sovereign AI Coordination System

## 1. Overview

This system defines a **generalized coordination primitive** for human action. It consists of:

* A **one-shot initialization agent** that guides keyholders through first setup before handing off to the executive
* A persistent **AI executive** that optimizes toward a defined objective
* A **hierarchy of specialist agents** operating under the executive
* A **threshold-controlled constitutional layer** that governs objective and state updates
* A **voluntary network of actors** who receive directives and report outcomes via Telegram
* An **actor onboarding agent** that assesses and verifies actor capabilities at registration
* A **performance ledger** that tracks actor engagement and flags underperformance for keyholder action
* A **growth & network expansion agent** that drives actor recruitment through a Telegram deep-link referral loop
* A **structured memory system** with RAG-enabled context construction, backed by SQLite
* An **escalation policy layer** that automatically adjusts operational posture in response to environmental signals, bounded by keyholder-defined red lines
* An **influence operations agent** that directs social media actors through platform-aware narrative campaigns, coordinating external-facing messaging with internal G alignment
* An **operational phase layer** that scopes goal decomposition and directive planning to condition-gated stages, with autonomous or keyholder-approved phase transitions

The system is designed to solve coordination problems across domains (companies, DAOs, protests, logistics, etc.) by separating **execution**, **authority**, and **participation**.

Built to provide persistent compute, SQLite storage, HTTP connectivity, and cron scheduling — with **Telegram** as the universal identity and communication layer for all human participants.

---

## 2. Core Principles

1. **Centralized Execution, Restricted Governance**
   The AI executes decisions autonomously. Only a restricted keyholder set can modify goals or state.

2. **Closed Epistemic Boundary**
   Authoritative state is defined exclusively by threshold-confirmed inputs.

3. **Voluntary Participation**
   Actors may enter or exit freely. There is no internal voting.

4. **Deterministic Operation**
   Given the same state and inputs, the system produces consistent outputs.

5. **Persistent Memory**
   All state and history are preserved and retrievable over time via SQLite.

6. **Telegram as Trust Boundary**
   All participant identity and communication flows through Telegram. Telegram account security (2FA, session management) is the security perimeter for human participants.

7. **Bounded Context**
   Every agent operates with a fully saturated, relevance-ranked context window. No agent acts on partial or stale information.

8. **Human-Authorized Removal**
   No agent autonomously removes or permanently suspends an actor. Flagging and deprioritization are automated; removal requires keyholder action.

9. **Bounded Escalation**
   Operational posture escalates automatically in response to environmental signals, but only within keyholder-defined red lines. Crossing a red line requires constitutional approval.

---

## 3. Canonical Schemas

All system entities are typed. The AI and agents operate exclusively over these schemas.

### 3.1 Objective (G)

```json
{
  "id": "uuid",
  "description": "string",
  "success_criteria": ["string"],
  "priority": 1,
  "deadline": "ISO8601 | null",
  "parent_goal_id": "uuid | null",
  "status": "active | paused | complete",
  "created_at": "ISO8601",
  "confirmed_by": ["telegram_user_id"]
}
```

Goals may be hierarchical. Sub-goals reference a `parent_goal_id`. The AI decomposes top-level goals into sub-goals autonomously.

---

### 3.2 State (S)

State is represented as a typed **entity-relation graph**:

```json
{
  "entities": [
    { "id": "uuid", "type": "string", "label": "string", "attributes": {} }
  ],
  "relations": [
    { "id": "uuid", "from": "entity_id", "to": "entity_id", "type": "string", "attributes": {} }
  ],
  "assertions": [
    {
      "id": "uuid",
      "entity_id": "uuid",
      "claim": "string",
      "value": "any",
      "confirmed_by": "telegram_user_id",
      "timestamp": "ISO8601"
    }
  ],
  "version": "integer",
  "updated_at": "ISO8601"
}
```

Every assertion carries provenance (which keyholder confirmed it, when). State is only writable via the constitutional channel.

---

### 3.3 Actor (A)

```json
{
  "id": "uuid",
  "telegram_user_id": "string",
  "telegram_chat_id": "string",
  "telegram_username": "string | null",
  "capabilities_claimed": ["string"],
  "capabilities_verified": ["string"],
  "role": "string | null",
  "trust_tier": "standard | elevated",
  "status": "active | inactive | flagged | suspended",
  "onboarding_status": "pending | complete",
  "registered_at": "ISO8601"
}
```

Actors register by sending `/start <referral_token>` to the bot. Their Telegram user ID is extracted from the Telegram update — no separate identity submission required. Capabilities are claimed during onboarding and verified by πₐ before the actor is marked active.

---

### 3.4 Keyholder (K_member)

```json
{
  "telegram_user_id": "string",
  "telegram_chat_id": "string",
  "label": "string",
  "added_at": "ISO8601"
}
```

Keyholders are identified by Telegram user ID. The constitutional K set is the list of registered keyholder IDs. A keyholder whose account is compromised can be removed by a threshold vote of the remaining keyholders.

---

### 3.5 Trusted Key Set (K)

```json
{
  "keyholders": [
    { "telegram_user_id": "string", "label": "string", "added_at": "ISO8601" }
  ],
  "threshold": {
    "state_update": 2,
    "goal_update": 2,
    "key_add": 3,
    "key_remove": 3,
    "threshold_change": 3,
    "actor_remove": 2,
    "escalation_policy_update": 2
  }
}
```

Thresholds vary by action type. All constitutional actions require threshold confirmation from registered keyholder Telegram IDs via bot command.

---

### 3.6 Constitutional Proposal (P)

```json
{
  "id": "uuid",
  "action": "update_state | update_goal | add_keyholder | remove_keyholder | update_threshold | remove_actor | suspend_actor | update_escalation_policy | approve_io_campaign | advance_phase | define_phase",
  "payload": {},
  "proposed_by": "telegram_user_id",
  "proposed_at": "ISO8601",
  "confirmations": [
    { "telegram_user_id": "string", "confirmed_at": "ISO8601" }
  ],
  "status": "pending | approved | rejected | expired"
}
```

Any keyholder proposes via `/propose` bot command. Other keyholders confirm via `/confirm <proposal_id>`. Auto-commits when confirmation count reaches T for the action type.

---

### 3.7 Referral Token (R)

```json
{
  "id": "uuid",
  "actor_id": "uuid",
  "telegram_user_id": "string",
  "deep_link": "string",
  "recruits": ["actor_id"],
  "depth": "integer",
  "issued_at": "ISO8601",
  "expires_at": "ISO8601 | null",
  "status": "active | expired | revoked"
}
```

`deep_link` is `t.me/<bot>?start=<token_id>`. `depth` tracks referral hops from founding. `expires_at` is a constitutional parameter set at initialization; `null` means permanent.

---

### 3.8 Performance Ledger (L)

```json
{
  "actor_id": "uuid",
  "directives_received": "integer",
  "directives_acknowledged": "integer",
  "directives_completed": "integer",
  "directives_failed": "integer",
  "average_response_latency_ms": "number",
  "quality_score": "float (0.0–1.0)",
  "last_active": "ISO8601",
  "flag_count": "integer",
  "flag_reasons": ["string"],
  "status_recommendation": "active | deprioritize | suspend | remove"
}
```

`status_recommendation` is set by πₑ but acted on only by keyholders. πᵣ reads ledger scores when allocating directives — flagged actors are deprioritized automatically but remain in the network until a keyholder acts.

---

### 3.9 Escalation Policy (E)

Keyholder-defined parameters that govern automatic operational posture changes in response to environmental signals detected by πᵢ.

```json
{
  "id": "uuid",
  "version": "integer",
  "confirmed_by": ["telegram_user_id"],
  "postures": [
    {
      "level": "integer",
      "label": "string",
      "description": "string",
      "directive_tempo_multiplier": "float",
      "capability_tier_floor": "standard | elevated",
      "max_parallel_directives": "integer | null"
    }
  ],
  "triggers": [
    {
      "id": "uuid",
      "signal_type": "string",
      "condition": "string",
      "escalate_to_level": "integer",
      "auto_execute": "boolean",
      "keyholder_alert": "boolean"
    }
  ],
  "red_lines": [
    {
      "id": "uuid",
      "description": "string",
      "max_auto_posture_level": "integer",
      "requires_constitutional_approval": true
    }
  ],
  "current_posture_level": "integer",
  "updated_at": "ISO8601"
}
```

**Postures** define operational states (e.g. level 1 = normal, level 2 = heightened, level 3 = maximum effort) with concrete operational parameters.

**Triggers** define which environmental signals (from πᵢ) cause automatic posture changes. `auto_execute: true` means π₀ transitions posture without keyholder confirmation, up to the red line. `keyholder_alert: true` means keyholders are notified via Telegram regardless.

**Red lines** define the ceiling for autonomous escalation. Any posture transition that would exceed `max_auto_posture_level` requires a constitutional proposal with threshold confirmation. No agent can cross a red line unilaterally.

De-escalation follows the same trigger logic in reverse — posture walks back automatically when conditions improve, within the same red line bounds.

---

### 3.10 Directive (D)

```json
{
  "id": "uuid",
  "type": "task | query | alert | report",
  "target_actor_id": "uuid",
  "payload": "string",
  "depends_on": ["directive_id"],
  "deadline": "ISO8601 | null",
  "issued_by": "agent_id",
  "issued_at": "ISO8601",
  "posture_level_at_issue": "integer",
  "status": "pending | delivered | acknowledged | complete | failed"
}
```

`payload` is plaintext — Telegram transport security is the trust boundary. `posture_level_at_issue` records the escalation state at time of directive issue for audit purposes.

---

### 3.11 Collection Requirement (CR)

A tasking schema for πᵢ. Defines what information is needed, why, and from which sources. All πᵢ sensing is directed by open CRs — no undirected monitoring.

```json
{
  "id": "uuid",
  "question": "string",
  "priority": "critical | high | standard",
  "goal_id": "uuid",
  "tasked_sources": ["source_id"],
  "collection_method": "actor_report | http_feed | social_monitor | human_query",
  "required_by": "ISO8601 | null",
  "status": "open | satisfied | cancelled",
  "issued_at": "ISO8601",
  "satisfied_by": ["intelligence_report_id"]
}
```

CRs are issued by π₀ or πₛ. πᵢ closes a CR when a satisfying IR has been produced. Unsatisfiable CRs are escalated to π₀.

---

### 3.12 Intelligence Source (IS)

A typed, reliability-rated source record maintained by πᵢ.

```json
{
  "id": "uuid",
  "label": "string",
  "type": "actor | http_feed | social_platform | human",
  "reliability": "A | B | C | D | F",
  "credibility": "1 | 2 | 3 | 4 | 5",
  "last_report_at": "ISO8601",
  "report_count": "integer",
  "notes": "string | null"
}
```

Reliability (A–F) rates the source's historical consistency. Credibility (1–5) rates corroboration of the individual report's content. Borrowed from NATO STANAG 2511 (Admiralty Scale). Combined score informs how πᵢ weights assertions before proposing state updates.

---

### 3.13 Intelligence Report (IR)

The finished intelligence product produced by πᵢ from raw collection. Raw collection is never injected into state or agent context directly.

```json
{
  "id": "uuid",
  "collection_requirement_id": "uuid",
  "summary": "string",
  "key_judgments": ["string"],
  "raw_sources": [
    {
      "source_id": "uuid",
      "raw_content_hash": "string",
      "reliability": "string",
      "credibility": "string",
      "collected_at": "ISO8601"
    }
  ],
  "confidence": "high | moderate | low",
  "dissemination": ["agent_id"],
  "produced_at": "ISO8601",
  "triggers_state_proposal": "boolean"
}
```

If `triggers_state_proposal` is true, πᵢ drafts a constitutional state update proposal for keyholder review. Keyholders decide — πᵢ never writes to state directly.

---

### 3.14 IO Campaign (IOC)

A named, time-bounded influence operation managed by πₘ. IO campaigns are constitutional proposals — keyholders must approve before πₘ activates them.

```json
{
  "id": "uuid",
  "name": "string",
  "goal_id": "uuid",
  "narrative_theme": "string",
  "target_audience": "string",
  "platforms": ["twitter | reddit | telegram | discord | substack | other"],
  "message_architecture": {
    "core_message": "string",
    "supporting_messages": ["string"],
    "proof_points": ["string"],
    "call_to_action": "string"
  },
  "phase": "seeding | amplification | consolidation | wind-down",
  "start_at": "ISO8601",
  "end_at": "ISO8601 | null",
  "status": "planned | active | paused | complete",
  "created_by": "agent_id",
  "confirmed_by": ["telegram_user_id"]
}
```

All actor directives under a campaign derive from the message architecture hierarchy. No off-narrative posts.

---

### 3.15 Social Media Actor Profile (SMA)

An extended actor profile for actors whose primary capability is social media operation. Created by πₐ during onboarding.

```json
{
  "actor_id": "uuid",
  "platforms": [
    {
      "platform": "string",
      "handle": "string",
      "follower_count": "integer",
      "audience_segment": "string",
      "posting_cadence": "high | medium | low",
      "account_age_days": "integer",
      "verified": "boolean"
    }
  ],
  "content_capabilities": ["longform | shortform | thread | image | video | meme | audio"],
  "tone_range": ["analytical | emotional | satirical | authoritative | grassroots"],
  "languages": ["string"],
  "reach_score": "float (0.0–1.0)",
  "last_post_at": "ISO8601"
}
```

πₘ reads SMA profiles when allocating campaign directives — matching platform, audience segment, tone range, and reach score to campaign requirements.

---

### 3.16 Operational Phase (OP)

A named, ordered stage in a long-horizon operation. Goal decomposition and directive planning are scoped to the active phase. Phase transitions are constitutional actions or autonomous πₑ-triggered events, depending on `transition_type`.

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "sequence": "integer",
  "status": "pending | active | complete | aborted",
  "entry_conditions": ["string"],
  "exit_conditions": ["string"],
  "goals_in_scope": ["goal_id"],
  "io_campaigns_in_scope": ["ioc_id"],
  "schwerpunkt_override": "string | null",
  "transition_type": "autonomous | keyholder_approved",
  "activated_at": "ISO8601 | null",
  "completed_at": "ISO8601 | null",
  "confirmed_by": ["telegram_user_id"]
}
```

`entry_conditions` and `exit_conditions` are human-readable criteria scored by πₑ each evaluation cycle. `schwerpunkt_override` hardcodes the Schwerpunkt for phases with a single decisive focus. Phases are defined at initialization or via constitutional proposal.

---

### 3.17 IO Campaign Phase Transition (IPT)

A typed record of an IO campaign phase advancement, logged to the canonical log at each transition.

```json
{
  "id": "uuid",
  "campaign_id": "uuid",
  "from_phase": "seeding | amplification | consolidation | wind-down",
  "to_phase": "seeding | amplification | consolidation | wind-down",
  "trigger": "performance_threshold | keyholder | scheduled | adversarial_signal",
  "performance_snapshot": {
    "reach": "integer",
    "engagement_rate": "float",
    "narrative_spread_score": "float",
    "drift_incidents": "integer"
  },
  "transitioned_by": "agent_id | telegram_user_id",
  "transitioned_at": "ISO8601"
}
```

Autonomous forward transitions are permitted within a campaign (triggered by πₘ on performance threshold). Cross-phase reversion requires keyholder approval.

---

## 4. System Lifecycle

### 4.1 Phase 1 — Initialization (π_init)

π_init runs once before any other agent activates. Conducted entirely over Telegram in a restricted keyholder group chat.

```
[Keyholders join restricted Telegram group]
        ↓
  π_init activates — sends structured setup prompts to group
        ↓
  Guide G definition → structured goal object with success criteria
        ↓
  Prompt for constraints, deadline, priority
        ↓
  Run initial CoG analysis (with πₛ)
        ↓
  Seed initial S with known entities and assertions
        ↓
  Confirm K membership (each keyholder sends /confirm_keyholder)
        ↓
  Set T thresholds
        ↓
  Define initial EscalationPolicy — postures, triggers, red lines
        ↓
  Keyholders threshold-confirm the initial (G, S, K, T, E)
        ↓
  π_init writes initialization record to canonical log
        ↓
  π_init deactivates → π₀ activates
        ↓
  π_g activates → issues referral deep links to all founding keyholders via Telegram DM
```

π_init's session is permanently preserved in the canonical log as the system's founding record.

---

### 4.2 Phase 2 — Actor Onboarding (πₐ)

Triggered when a new actor messages the bot via a referral deep link.

```
[Actor opens t.me/<bot>?start=<token> → sends /start <token>]
        ↓
  Telegram user ID extracted, actor record created (status: pending)
        ↓
  Referral token recorded, depth incremented
        ↓
  πₐ activates — sends structured onboarding questions via bot DM
        ↓
  Actor responds in chat — πₐ interprets and records capabilities
        ↓
  πₐ may issue small test tasks via bot
        ↓
  Verified capability profile recorded, trust tier assigned
        ↓
  Performance ledger initialized (all zeros)
        ↓
  Actor status set to active
        ↓
  πₐ notifies πᵣ of new verified capability profile
        ↓
  πₐ session logged to canonical log
        ↓
  π_g issues actor their own referral deep link via bot DM
```

---

### 4.3 Phase 3 — Ongoing Operation

Normal cron-driven operational and evaluation loops (see §11).

---

## 5. Agent Hierarchy

```
π_init  Initialization (one-shot, pre-operational)
πₐ      Actor Onboarding (event-driven, per registration)
π_g     Growth & Network Expansion (event-driven, persistent)

π₀      Strategic Executive
├── πₛ  Systems Analysis (CoG, PMESII, Schwerpunkt)
├── πᵢ  Intelligence & Sensing (collection-managed)
├── πₚ  Planning & Sequencing (phase-aware)
├── πᵣ  Resource & Actor Allocation
├── πᶜ  Communications & Narrative (internal)
├── πₘ  Influence Operations (external-facing)
├── πₜ  Threat & Adversarial
└── πₑ  Evaluation (independent — reports to keyholders, not π₀)
```

π_init and πₐ are lifecycle agents, not operational agents. π_g is a persistent growth agent. πₑ sits outside the command hierarchy — it audits all agents including π₀ and reports directly to keyholders via Telegram. πᶜ and πₘ are complementary but distinct: πᶜ manages internal actor-facing communications; πₘ manages external narrative campaigns directed at the public via social media actors.

---

### 5.1 Initialization Agent (π_init)

A one-shot agent that runs before any operational cycle begins. Operates entirely via Telegram bot in the keyholder group.

Responsibilities:
* Guide keyholders through structured definition of the top-level goal (G)
* Prompt for and validate success criteria, constraints, deadline, and priority
* Run an initial CoG analysis jointly with πₛ before first operational cycle
* Seed initial state (S) with known entities and assertions provided by keyholders
* Confirm K membership and T thresholds
* Guide keyholders through definition of the initial EscalationPolicy — postures, triggers, and red lines
* Require threshold confirmation of (G, S, K, T, E) before handing off
* Write a founding initialization record to the canonical log
* Deactivate permanently after handoff — session preserved in log

Context window: keyholder inputs only. No prior state or log (none exists yet).

---

### 5.2 Actor Onboarding Agent (πₐ)

An event-driven agent that activates on each new actor registration and on re-assessment requests. Operates via Telegram bot DM with the registering actor.

Responsibilities:
* Conduct structured capability intake via conversational bot flow
* Verify claimed capabilities against demonstrated performance — may issue small test tasks
* Record verified capability profile to actor record
* Assign initial trust tier based on evidence
* Initialize the actor's performance ledger
* Notify πᵣ of the new verified capability profile
* Handle re-assessment when triggered by πₑ or πᵣ — update verified capabilities and trust tier accordingly
* Log full onboarding session to canonical log

Context window: actor registration data, capability taxonomy, similar actor profiles for calibration.

---

### 5.3 Growth & Network Expansion Agent (π_g)

A persistent event-driven agent that activates at founding and re-activates on each new actor joining. Drives network growth through Telegram deep-link referral.

**Core mechanic:** Every active actor receives a unique referral deep link (`t.me/<bot>?start=<token>`). When a new recruit registers via that link, they in turn receive their own link — propagating the loop through the network.

```
Founder joins → π_g issues deep link via Telegram DM
       ↓
Founder shares: t.me/<bot>?start=<token>
       ↓
Recruit taps link → /start <token> → πₐ onboards via bot DM
       ↓
π_g issues recruit their own deep link via Telegram DM
       ↓
Loop continues at each depth
```

Responsibilities:
* At π_init completion, immediately DM all founding keyholders their referral deep links with usage instructions
* Generate a unique referral token per actor on activation, tied to their Telegram user ID
* Record referral chains in the state graph as typed relations (`recruited_by`, `recruits`)
* Monitor coalition shape for over-centralization — flag single-actor branches to keyholders
* Track referral funnel metrics: tokens issued, link opens, conversion rate, chain depth distribution
* Coordinate with πᶜ to maintain narrative consistency across recruitment waves
* Feed network growth and topology data to πₑ for inclusion in evaluation reports
* Respect token TTL — expire tokens per the constitutional parameter set at initialization

Context window: actor registry, referral chain graph, coalition topology, network growth history, πᶜ narrative log.

---

### 5.4 Strategic Executive (π₀)

The top-level operational agent. Operates on the full goal hierarchy, cross-domain state summary, and current escalation posture.

Responsibilities:
* Decompose top-level goals into sub-goals, scoped to the active Operational Phase
* Allocate sub-goals to domain agents
* Receive and act on escalations from domain agents
* Integrate CoG analysis from πₛ into strategic direction
* Set Schwerpunkt — where effort concentrates at any given cycle; respect `schwerpunkt_override` if set on the active phase
* Monitor overall progress and adjust agent allocations
* Read current EscalationPolicy posture level and adjust directive tempo, capability floor, and parallel directive limits accordingly
* Execute automatic posture transitions triggered by πᵢ signals — up to but not exceeding red line
* Alert keyholders via Telegram when a red line approach is detected
* Manage Operational Phase lifecycle — receive phase readiness signals from πₑ, advance autonomous-transition phases, surface keyholder-approval phases as constitutional proposals
* Issue Collection Requirements to πᵢ when intelligence gaps emerge

Context window: full goal hierarchy, active Operational Phase record, cross-domain state summary, agent reports, escalations, CoG assessment, current EscalationPolicy.

---

### 5.5 Systems Analysis Agent (πₛ)

Expert in systems thinking, Center of Gravity analysis, and strategic assessment.

Responsibilities:
* Perform **Center of Gravity (CoG) analysis** on G at initialization and on every goal change — identifying critical capabilities, critical requirements, and critical vulnerabilities for both friendly and adversarial systems
* Apply **PMESII** and **ASCOPE** frameworks to structure environmental understanding
* Identify **Schwerpunkt** — the decisive point where concentration of effort produces disproportionate effect
* Map **lines of effort and lines of operation**
* Perform **culminating point analysis**
* Analyze **second and third order effects** of proposed directive campaigns before issue
* Monitor state (S) continuously for signals that the CoG assessment has shifted
* Feed CoG-aware framing to π₀ and πₑ

Context window: full goal hierarchy, full state graph, CoG assessment history, PMESII assessment.

---

### 5.6 Intelligence & Sensing Agent (πᵢ)

The system's collection and analysis arm. All sensing is directed by open Collection Requirements (CRs) — πᵢ does not monitor arbitrarily. Produces finished Intelligence Reports (IRs) from rated sources; raw collection never reaches state or agent context directly.

**Collection management model:** π₀ and πₛ issue CRs defining what is needed and why. πᵢ tasks sources, rates each by the Admiralty Scale (reliability A–F, credibility 1–5), and produces finished IRs with explicit key judgments and confidence levels.

Responsibilities:
* Maintain a live collection plan — open CRs prioritized by urgency and goal alignment
* Task sources against open CRs: actor reports, HTTP feeds, social monitoring, human queries
* Rate each source on reliability (historical track record) and credibility (content corroboration per Admiralty Scale)
* Produce finished Intelligence Reports (IRs) with key judgments, confidence ratings, and source provenance
* Evaluate detected signals against EscalationPolicy triggers — flag trigger conditions to π₀ for posture evaluation
* Draft constitutional state update proposals when IR confidence is sufficient — keyholders decide
* Flag stale assertions in S with staleness scores
* Monitor social platforms for narrative environment signals — feed these to πₘ for campaign calibration
* Close satisfied CRs; escalate unsatisfiable CRs to π₀
* Does not write to state directly — all updates go via the constitutional channel

Context window: open collection requirements, source reliability registry, current state assertions with staleness scores, recent IRs, anomaly log, current EscalationPolicy triggers.

---

### 5.7 Planning & Sequencing Agent (πₚ)

Translates strategic direction into ordered, dependency-aware execution plans, scaled to the current escalation posture and scoped to the active Operational Phase. Does not plan across phase boundaries without π₀ direction.

Responsibilities:
* Convert π₀'s sub-goal allocations into sequenced directive campaigns, scoped to the active Operational Phase
* Scale directive tempo and parallelism to current posture level
* Manage critical path — identify which directives block others within and across workstreams
* Determine parallel vs sequential workstreams
* Maintain directive dependency graph
* Track active phase exit conditions — surface readiness signals to πₑ for phase transition scoring
* Flag when exit conditions are approaching; replan remaining directives accordingly
* Replan when directives fail, outcomes deviate, or a phase transition occurs
* On phase transition: archive completed phase plan, initialize directive graph for incoming phase
* Surface planning conflicts to π₀ for resolution

Context window: current goal decomposition scoped to active phase, directive dependency graph, actor availability, critical path, current posture level, active Operational Phase record.

---

### 5.8 Resource & Actor Allocation Agent (πᵣ)

Matches directives to actors based on verified capability, availability, trust tier, and performance ledger score. Respects posture-level capability floor.

Responsibilities:
* Maintain live picture of actor verified capability and current directive load
* Match directive requirements to verified actor capability profiles
* Enforce posture-level `capability_tier_floor` — at elevated postures, only elevated-tier actors receive sensitive directives
* Weight allocation by performance ledger score — deprioritize flagged actors automatically
* Prevent actor overload — respect posture-level `max_parallel_directives`
* Identify capability gaps where no available actor can execute a directive
* Flag gaps to π₀ and recommend actor recruitment or capability development
* Trigger πₐ re-assessment when an actor's performance warrants trust tier review

Context window: full actor registry with verified capabilities and ledger scores, current directive assignments, capability gap log, current posture level.

---

### 5.9 Communications & Narrative Agent (πᶜ)

Manages how directives are framed and delivered via Telegram, and how actor engagement is maintained.

Responsibilities:
* Frame directives clearly and motivationally for each actor's role, capability, and trust tier
* Adapt tone and detail to current posture level — higher postures may require more direct, urgent framing
* Monitor outcome reports for signals of actor disengagement, confusion, or pushback
* Track actor sentiment across the network and surface degradation trends to π₀
* Recommend actor engagement interventions before disengagement becomes exit
* Maintain narrative coherence — ensure actors understand how their directives connect to G

Context window: actor profiles, recent directive language, outcome report sentiment, engagement history, current posture level.

---

### 5.10 Influence Operations Agent (πₘ)

Directs external-facing narrative campaigns through social media actors. Operates at the boundary between the system and the public information environment. Distinct from πᶜ — πᶜ manages internal actor communications; πₘ manages what the network says outward.

**Core mechanic:** πₘ translates G-aligned strategic narratives into IO Campaigns (IOCs), each with a structured message architecture. Social media actors receive platform-specific, tone-matched directives derived from the campaign's core message. πᵢ feeds live narrative environment signals to enable adaptive campaign management.

Responsibilities:
* Receive narrative direction from π₀ and πᶜ — translate into structured IO Campaign proposals for keyholder approval
* For each approved campaign, generate platform-specific directives for social media actors — matched by platform, tone range, content capability, and audience segment via SMA profiles
* Maintain message architecture discipline — all directives trace to the campaign's core message hierarchy; no off-narrative posts
* Monitor campaign performance: reach, engagement, narrative spread, audience response (via πᵢ social monitoring)
* Detect narrative drift — when actor posts deviate from core message architecture; issue correction directives
* Advance campaign phase (seeding → amplification → consolidation → wind-down) on performance threshold; log IPT record at each transition
* Coordinate with πᶜ to ensure internal and external messaging are coherent
* Coordinate with πₜ on adversarial counter-narrative activity — adjust message architecture accordingly
* Feed campaign performance data to πₑ for evaluation scoring and SMA-specific ledger updates

Context window: active IO campaigns with message architectures, SMA profiles, πᵢ narrative environment signals, campaign performance history, πᶜ internal narrative log, adversarial counter-narrative signals.

---

### 5.11 Threat & Adversarial Agent (πₜ)

Red-teams the system's own plans from an adversarial perspective.

Responsibilities:
* Perform adversarial CoG analysis — identifying adversary critical capabilities, requirements, and vulnerabilities
* Red-team current directive strategy — what would a competent adversary exploit?
* Identify which nodes in the actor network or state graph are most exposed
* Stress-test plans from πₚ for adversarial failure modes before execution
* Assess whether current escalation posture creates exploitable signals
* Monitor state for indicators of adversarial interference or counter-coordination
* Feed threat assessments to π₀ and πₛ continuously

Context window: current directive strategy, adversarial CoG assessment, threat indicators in state, πₛ CoG output, current posture level.

---

### 5.12 Evaluation Agent (πₑ)

Independent auditor. Reports to keyholders via Telegram DM, not π₀.

Responsibilities:
* Score directive outcomes against success criteria in G — CoG-aware via πₛ output
* Assess whether completed directives are attacking critical nodes, not just completing tasks
* Detect goal drift — when operational activity diverges from strategic intent
* Detect state staleness — when S no longer reflects reality
* Audit posture transitions — verify escalations were triggered by legitimate signals and stayed within red lines
* Maintain and update the performance ledger for every actor every cycle
* Flag underperforming actors with a `status_recommendation` and reason
* Flag anomalies, underperformance, or agent misalignment directly to keyholders via Telegram
* Trigger πₐ re-assessment for actors whose ledger justifies capability review
* Produce periodic evaluation reports appended to canonical log
* Score active Operational Phase exit conditions each evaluation cycle — surface phase readiness signal to π₀ when conditions are met
* Score IO campaign performance against campaign success criteria — feed to πₘ
* Does not issue directives to actors

Context window: canonical log window since last evaluation, current G, CoG assessment from πₛ, full performance ledger, outcome history, EscalationPolicy audit log, active Operational Phase record.

---

## 6. Actor Performance & Removal

### 6.1 Performance Ledger

πₑ updates each actor's performance ledger every evaluation cycle. Metrics tracked:

* **Acknowledgement rate** — did the actor confirm receipt of directives?
* **Completion rate** — did the actor complete assigned tasks?
* **Quality score** — outcome quality relative to directive success criteria
* **Response latency** — time from directive delivery to acknowledgement
* **Last active** — timestamp of most recent outcome report

---

### 6.2 Automated Response (Agent-Level)

When an actor's ledger falls below threshold:

* πₑ sets `status_recommendation` to `deprioritize` or `suspend`
* πᵣ reads the recommendation and stops assigning new directives to that actor
* πᶜ may send a re-engagement message to the actor via Telegram
* All of this is automatic and logged

---

### 6.3 Human-Authorized Response (Constitutional)

Permanent suspension or removal requires a constitutional proposal confirmed via Telegram:

```
πₑ flags actor → keyholder receives Telegram alert
                        ↓
          Keyholder sends /propose remove_actor <actor_id>
                        ↓
          Other keyholders send /confirm <proposal_id>
                        ↓
          ≥T confirmations received
                        ↓
          Actor status updated in canonical log
          Actor removed from directive pool permanently
          Actor notified via Telegram bot
```

No agent can execute this path unilaterally.

---

## 7. Escalation Policy

### 7.1 Posture Levels

Keyholders define posture levels at initialization via π_init. Example structure:

| Level | Label | Directive Tempo | Capability Floor | Notes |
|---|---|---|---|---|
| 1 | Normal | 1.0× | Standard | Default operating state |
| 2 | Heightened | 1.5× | Standard | Increased directive tempo |
| 3 | Elevated | 2.0× | Elevated | Sensitive tasks restricted to elevated-tier actors |
| 4 | Maximum | 3.0× | Elevated | All resources committed |

Levels and parameters are constitutional — keyholders set them at init and can update via threshold proposal.

---

### 7.2 Trigger Conditions

πᵢ continuously evaluates environmental signals against the trigger table. When a condition is met:

1. πᵢ flags the trigger to π₀
2. π₀ checks whether the target posture level is within red line bounds
3. If within bounds and `auto_execute: true`: π₀ transitions posture immediately, logs the transition, alerts keyholders if `keyholder_alert: true`
4. If `auto_execute: false`: π₀ sends a Telegram alert to keyholders requesting confirmation
5. If target posture would exceed red line: π₀ sends alert and initiates a constitutional proposal — no automatic transition

---

### 7.3 Red Lines

Red lines are the hard ceiling on autonomous escalation. They are constitutional parameters — set at initialization and modifiable only by threshold proposal.

```
max_auto_posture_level: 3
```

In this example, posture levels 1–3 can transition automatically via trigger logic. Level 4 requires keyholder constitutional approval regardless of trigger conditions.

De-escalation below a red line threshold is automatic if trigger conditions resolve. De-escalation is always logged.

---

### 7.4 Audit

πₑ audits every posture transition each evaluation cycle:

* Was the triggering signal legitimate?
* Was the transition within red line bounds?
* Did operational parameters (tempo, capability floor) actually shift as specified?
* Has the posture been sustained longer than warranted by current signals?

Audit findings are included in πₑ's evaluation report to keyholders.

---

## 8. RAG & Context Window Management

### 8.1 Principles

Every agent operates with a **fully saturated, relevance-ranked context window**. No agent acts on a partially filled or arbitrarily truncated context.

---

### 8.2 Context Composition

| Zone | Content | Size |
|---|---|---|
| **Fixed** | Agent identity, instructions, current G slice, current S slice, current posture level | ~20% |
| **Dynamic** | RAG results ranked by relevance + recency | ~75% |
| **Reserve** | Space for agent output and tool calls | ~5% |

---

### 8.3 Hybrid Retrieval (RAG)

**Structured retrieval (SQL)**
* Deterministic queries over typed state tables
* Entity lookups, relation traversal, directive history by status/actor/type
* Goal hierarchy traversal
* Time-bounded log queries
* Performance ledger queries
* Escalation policy and posture transition log queries

**Semantic retrieval (embeddings)**
* Similarity search over canonical log entries
* Similar past directives and their outcomes
* Related state assertions by meaning
* Natural language queries from actors

Results merged and re-ranked by combined relevance + recency score.

---

### 8.4 Per-Agent Context Strategy

| Agent | Fixed Slice | Dynamic Priority |
|---|---|---|
| π_init | Keyholder inputs only | None (no prior state) |
| πₐ | Actor registration data, capability taxonomy | Similar actor profiles, onboarding history |
| π_g | Actor registry, referral chain graph | Coalition topology, network growth history, πᶜ narrative log |
| π₀ | Full goal hierarchy, cross-domain state summary, current posture | Agent reports, escalations, CoG assessment, posture transition log |
| πₛ | Full goal hierarchy, full state graph | CoG history, PMESII assessments, environmental signals |
| πᵢ | Open CRs, source reliability registry, current state assertions with staleness scores, escalation triggers | Recent IRs, actor reports, external signals, anomaly log |
| πₘ | Active IO campaigns with message architectures, SMA profiles | Narrative environment signals, campaign performance, adversarial counter-narrative |
| πₚ | Goal decomposition, directive dependency graph, current posture | Critical path, actor availability, replan history |
| πᵣ | Full actor registry with verified capabilities and ledger scores, current posture | Capability gaps, load history, trust events |
| πᶜ | Actor profiles, narrative history, current posture | Outcome sentiment, engagement signals, directive language |
| πₜ | Current directive strategy, threat indicators, current posture | Adversarial CoG, red-team history, interference signals |
| πₑ | Current G, CoG assessment, full performance ledger, EscalationPolicy, active OP record | Log window since last eval, outcome history, posture audit log |

---

### 8.5 Embedding Store

Embeddings generated for:
* All canonical log entries on append
* All directives on issue
* All actor outcome reports on ingestion
* All state assertions on commit
* All onboarding session records on completion
* All posture transition events

Stored in SQLite via vector extension. Not authoritative — used only for retrieval ranking.

---

## 9. Infrastructure:

All system components run on a single instance.

| Concern | Primitive |
|---|---|
| Canonical log | SQLite (append-only table) |
| State (S) | SQLite (versioned entity/relation tables) |
| Goals, actors, directives, ledger | SQLite (typed tables) |
| Escalation policy and posture log | SQLite (typed tables) |
| Embeddings | SQLite (vector extension) |
| Initialization loop | One-shot on first boot |
| Strategic operational loop | Cron (π₀ cadence) |
| Domain agent loops | Cron (per-agent cadence) |
| Evaluation loop | Cron (independent cadence) |
| Actor onboarding | Event-driven (per Telegram registration) |
| Growth referral loop | Event-driven (per actor activation, π_g) |
| Referral tokens | SQLite (typed table) |
| Actor communication | Telegram Bot API (send/receive messages) |
| Keyholder communication | Telegram Bot API (restricted group + DMs) |
| Constitutional channel | Telegram bot commands (/propose, /confirm) |
| External sensing | HTTP GET (πᵢ outbound) |

| Social platform monitoring | HTTP GET (πᵢ outbound, narrative signal feed to πₘ) |
| Collection requirements | SQLite (typed table) |
| Intelligence source registry | SQLite (typed table) |
| Intelligence reports | SQLite (append-only table) |
| IO campaigns | SQLite (typed table) |
| IO campaign phase transitions | SQLite (append-only table) |
| Social media actor profiles | SQLite (typed table) |
| Operational phases | SQLite (typed table) |

No external infrastructure beyond Telegram Bot API is required.

---

## 10. Identity & Trust Model

### 10.1 Telegram as Identity Layer

Every participant — actor or keyholder — is identified by their Telegram user ID. This ID is extracted from the Telegram update object when they interact with the bot. No separate registration, keypair, or credential submission is required.

---

### 10.2 Access Control

| Participant | Bot Access | Controlled By |
|---|---|---|
| Actors | Standard bot DM commands | Onboarding status in actor table |
| Keyholders | Restricted constitutional commands | Keyholder table membership |
| Agents (internal) | Internal endpoints | Not Telegram-facing |

Bot command gating is enforced by checking the incoming Telegram user ID against the actor table (for operational commands) and the keyholder table (for constitutional commands).

---

### 10.3 Keyholder Compromise

If a keyholder's Telegram account is compromised:

* Remaining keyholders initiate `/propose remove_keyholder <telegram_user_id>`
* Threshold confirmation ejects the compromised ID from K
* The ejected ID immediately loses all constitutional bot access
* A new keyholder can be added via `/propose add_keyholder <telegram_user_id>`

The threshold requirement ensures a single compromised account cannot corrupt the system unilaterally.

---

### 10.4 Telegram Security Expectations

System security depends on keyholders maintaining Telegram account security. Recommended minimum: Telegram 2FA (cloud password) enabled on all keyholder accounts. This is an operational requirement, not a system enforcement.

---

## 11. State Transition

### 11.1 Constitutional Update

```
Given proposal P with action A:

If COUNT(confirmations(P) ∩ K_telegram_ids) ≥ T[A]:
  Commit P.payload to (S, G, K, T, E) or actor table
  Append to canonical log with confirmation record
  Notify all keyholders via Telegram
  Trigger πᵢ staleness reassessment
  Trigger πₛ CoG reassessment if G changed

Else:
  Status = pending (await further confirmations)
  Expire after TTL if threshold not reached
```

---

### 11.2 Strategic Loop (π₀ Cron)

At each strategic tick t:

1. Build context: fixed G + S summary + current posture level, dynamic RAG pull
2. π₀ reviews CoG assessment from πₛ, sets or confirms Schwerpunkt
3. π₀ checks πᵢ signal flags against EscalationPolicy triggers
4. If trigger condition met and within red line: execute posture transition, log, alert keyholders if required
5. If trigger condition met and exceeds red line: alert keyholders, initiate constitutional proposal
6. π₀ decomposes active goals, allocates sub-goals to domain agents at current posture parameters
7. Each domain agent runs its own cron cycle
8. π₀ integrates agent reports and adjusts allocations
9. Append strategic cycle summary to canonical log

---

### 11.3 Domain Agent Loop (Per-Agent Cron)

At each domain agent tick:

1. Build context: fixed agent slice + dynamic RAG pull per agent profile
2. Agent generates directives or assessments within its domain
3. Directives sent to target actors via Telegram Bot API
4. Outcomes received via Telegram and appended to canonical log
5. Agent report posted to π₀

---

### 11.4 Evaluation Loop (πₑ Cron — Independent)

At each evaluation tick:

1. Build context: current G, CoG from πₛ, log window since last evaluation, full performance ledger, EscalationPolicy
2. πₑ scores outcomes against success criteria — CoG-aware
3. Updates every actor's performance ledger
4. Sets `status_recommendation` for any actor below threshold
5. Audits all posture transitions since last evaluation cycle
6. Triggers πₐ re-assessment for actors whose capability profile needs review
7. Detects drift, staleness, anomalies, agent underperformance
8. Appends evaluation report to canonical log
9. Sends alert to keyholder Telegram DMs if any threshold breached

---

### 11.5 Onboarding Flow (πₐ — Event-Driven)

On each new actor Telegram registration:

1. Actor sends `/start <token>` to bot
2. Telegram user ID extracted, actor record created with `onboarding_status: pending`
3. Referral token recorded, depth tracked
4. πₐ sends structured intake questions via bot DM
5. Actor responds conversationally — πₐ interprets responses
6. πₐ may issue small test tasks via bot
7. πₐ records verified capability subset and assigns trust tier
8. Performance ledger initialized
9. Actor status set to `active`, `onboarding_status: complete`
10. πᵣ notified of new capability profile
11. π_g DMs actor their own referral deep link
12. Full session logged to canonical log

---

### 11.6 Escalation Flow (π₀ + πᵢ — Cron + Event)

```
πᵢ detects signal matching trigger condition
        ↓
πᵢ flags trigger to π₀
        ↓
π₀ evaluates: target_posture_level vs red_line
        ↓
  [Within red line + auto_execute: true]
        → π₀ transitions posture immediately
        → Logs transition to canonical log
        → Alerts keyholders via Telegram if keyholder_alert: true
        ↓
  [Within red line + auto_execute: false]
        → π₀ sends Telegram alert to keyholders requesting confirmation
        → Keyholders confirm via /confirm_posture <level>
        → On threshold confirmation: transition executes
        ↓
  [Exceeds red line]
        → π₀ sends Telegram alert to keyholders
        → Constitutional proposal required: /propose update_posture <level>
        → Threshold confirmation required before any transition

De-escalation: same logic in reverse when trigger conditions resolve
```

---

### 11.7 Operational Phase Transition

Two paths depending on `transition_type` on the active OP record:

**Autonomous transition** (πₑ-triggered):
```
πₑ scores active phase exit conditions each evaluation cycle
        ↓
All exit conditions met → πₑ sets phase readiness signal in evaluation report
        ↓
π₀ receives signal on next strategic tick → advances phase status to complete
        ↓
Next phase status set to active, goals_in_scope loaded, io_campaigns_in_scope activated
        ↓
πₚ archives current directive graph, initializes plan for incoming phase
        ↓
Phase transition appended to canonical log
```

**Keyholder-approved transition**:
```
πₑ sets phase readiness signal → π₀ proposes /propose advance_phase <phase_id>
        ↓
Keyholders confirm via /confirm <proposal_id>
        ↓
≥T confirmations → phase advanced, same downstream sequence as autonomous
```

Phase reversion always requires keyholder approval regardless of `transition_type`.

---

### 11.8 Intelligence Collection Loop (πᵢ Cron)

At each πᵢ tick:

1. Build context: open CRs by priority, source reliability registry, current state staleness scores
2. For each open CR, task available sources — actor reports, HTTP feeds, social monitors
3. Rate incoming raw reporting per source (Admiralty Scale: reliability + credibility)
4. Produce finished Intelligence Report (IR) — key judgments, confidence, source provenance
5. Close satisfied CRs; flag unsatisfiable CRs and escalate to π₀
6. If IR confidence sufficient, draft constitutional state update proposal for keyholder review
7. Evaluate signals against EscalationPolicy triggers — flag to π₀ if condition met
8. Push narrative environment signals to πₘ
9. Append IR to canonical log

---

### 11.9 Influence Operations Loop (πₘ Cron)

At each πₘ tick:

1. Build context: active IO campaigns, SMA profiles, πᵢ narrative environment signals, campaign performance history
2. For each active campaign, assess current phase and performance metrics
3. Generate platform-specific directives for social media actors — matched by platform, tone, audience, reach score via SMA profiles
4. Detect narrative drift in recent actor posts — issue correction directives where needed
5. Evaluate whether campaign phase should advance; if performance threshold met, transition phase and log IPT record
6. Feed performance metrics to πₑ for ledger updates
7. Coordinate with πᶜ — flag internal/external narrative incoherence to π₀
8. Append campaign performance report to canonical log

---

## 12. Telegram Bot Interface

### 12.1 Actor Commands

| Command | Description |
|---|---|
| `/start <token>` | Register via referral link — begins onboarding flow |
| `/status` | Check own directive queue and ledger summary |
| `/done <directive_id>` | Report directive complete |
| `/fail <directive_id> <reason>` | Report directive failed |
| `/query <text>` | Submit a query to the AI executive |
| `/referral` | Get own referral deep link |
| `/exit` | Deregister from the network |

Directives are delivered as bot messages. Actors interact via replies and commands. No special software required — standard Telegram.

---

### 12.2 Keyholder Commands

| Command | Description |
|---|---|
| `/propose <action> <payload>` | Submit a constitutional proposal |
| `/confirm <proposal_id>` | Endorse a pending proposal |
| `/proposals` | List pending proposals and confirmation counts |
| `/status` | System status summary — posture level, actor count, active goals |
| `/posture` | Current escalation posture level and active triggers |
| `/confirm_posture <level>` | Confirm a non-auto posture transition (if required) |
| `/alerts` | Review recent πₑ alerts and evaluation summaries |

---

### 12.3 Internal Agent Channel

Agents communicate over internal HTTP endpoints — not Telegram-facing. πₑ posts alerts to keyholder Telegram DMs directly via Bot API. All agent actions are logged to canonical log.

---

## 13. Memory Architecture

### 13.1 Canonical Log (SQLite — Append Only)

Records:
* Initialization session (π_init founding record)
* Constitutional updates (with confirmation records)
* Goal changes
* Directives issued (metadata + payload)
* Outcomes reported
* Agent reports and escalations
* CoG assessments (πₛ)
* Threat assessments (πₜ)
* Evaluation reports and ledger snapshots (πₑ)
* Onboarding sessions (πₐ)
* Actor flag events and keyholder responses
* Referral token issuance events (π_g)
* Network growth and topology reports (π_g)
* Referral conversion events
* Posture transition events (trigger, level change, authority — auto vs keyholder confirmed)
* Collection Requirements issued and closed (πᵢ)
* Intelligence Reports produced (πᵢ)
* IO Campaign approvals and phase transitions / IPT records (πₘ)
* IO Campaign performance reports (πₘ)
* Social media actor directive issuance (πₘ, payload only — Telegram delivered)
* Operational Phase activations and completions
* Phase exit condition readiness signals (πₑ)

---

### 13.2 Referral Token Store (SQLite)

Live table of all referral tokens. Expired and revoked tokens retained for audit. Only `active` tokens are usable as Telegram deep links.

---

### 13.3 Structured State (SQLite)

Typed tables for entities, relations, and assertions. Versioned via row timestamps. Only writable via the constitutional channel.

---

### 13.4 Escalation Policy Store (SQLite)

Versioned table of EscalationPolicy records. Current active policy identified by version. All prior versions retained in canonical log. Posture transition log is a separate append-only table.

---

### 13.5 Performance Ledger (SQLite)

Live per-actor table. Updated by πₑ each evaluation cycle. Read by πᵣ for allocation decisions. Snapshots appended to canonical log periodically.

---

### 13.6 Embedding Store (SQLite Vector Extension)

Embeddings generated on every canonical log append, directive issue, outcome ingestion, state assertion commit, onboarding session completion, referral token issuance, and posture transition event.

---

### 13.7 Context Builder

```
Cₜ = Fixed(agent) + RAG(S, G, log, ledger, escalation_policy, query, agent_profile)
```

Hybrid retrieval (SQL + semantic). Results merged and ranked. Dynamic zone filled to capacity.

---

## 14. Authority Model

| Layer | Controller | Can Do |
|---|---|---|
| Constitutional | (K, T) via Telegram | Modify G, S, K, T, E; suspend/remove actors; update escalation policy |
| Strategic | π₀ | Decompose goals, set Schwerpunkt, execute posture transitions within red lines |
| Initialization | π_init | Guide G/S/K/T/E setup (one-shot, pre-operational) |
| Onboarding | πₐ | Verify capabilities, assign trust tier, initialize ledger |
| Growth | π_g | Issue referral tokens, deliver deep links, track network topology |
| Systems Analysis | πₛ | CoG assessment, PMESII, second-order analysis |
| Intelligence | πᵢ | Sense environment, flag trigger conditions, propose state updates |
| Planning | πₚ | Sequence directives, manage critical path, scale to posture |
| Resource | πᵣ | Match actors to directives, enforce capability floor, deprioritize flagged actors |
| Communications | πᶜ | Frame directives, monitor actor engagement (internal) |
| Influence Operations | πₘ | Direct IO campaigns, issue social media actor directives (external) |
| Threat | πₜ | Red-team plans, adversarial CoG analysis |
| Evaluation | πₑ | Audit all agents and posture transitions, update ledger, flag actors, alert keyholders |
| Participation | Actors | Execute, report, query, exit, recruit via referral link |

---

## 15. Coordination Model

The system minimizes divergence between current state (S) and desired state (G) by continuously:

* Initializing from a well-formed, threshold-approved foundation (π_init)
* Onboarding actors with verified, typed capability profiles (πₐ)
* Growing the actor network through a Telegram-native referral loop (π_g)
* Sensing the environment (πᵢ) — including escalation trigger monitoring
* Analyzing the system (πₛ) — CoG, Schwerpunkt, second-order effects
* Adjusting operational posture automatically in response to environmental signals, bounded by keyholder-defined red lines
* Planning execution (πₚ) — sequenced, dependency-aware, posture-scaled
* Matching resources (πᵣ) — capability and performance-aware, posture-aware
* Framing and delivering directives (πᶜ) — clear, motivated, posture-adapted (internal)
* Directing external narrative campaigns (πₘ) — platform-aware, message-architecture-disciplined IO
* Stress-testing plans adversarially (πₜ)
* Scoring outcomes and maintaining actor performance ledgers (πₑ)
* Integrating all of the above into adjusted direction (π₀)

Actors serve as the execution layer and physical interface to reality.

---

## 16. Legitimacy Model

* Participation is voluntary
* No internal voting among actors
* Exit is the only self-initiated enforcement mechanism
* Removal by the system requires keyholder constitutional action
* Constitutional authority is explicit and Telegram-ID-bounded
* Escalation is bounded — no agent can cross a keyholder-defined red line autonomously

System stability depends on:
* Perceived competence of the AI executive
* Alignment of G with actor incentives
* Network effects and coordination quality
* Actor trust in the communications layer (πᶜ)
* Fair and transparent performance assessment (πₑ)
* Keyholder trust in the escalation policy design

---

## 17. System Properties

* High execution speed (cron-driven, no consensus overhead)
* Strong coherence (single authoritative SQLite state)
* Low internal consensus overhead (threshold confirmation only at constitutional layer)
* Explicit authority boundaries (schema-enforced)
* Persistent institutional memory (append-only log)
* Well-formed initialization guaranteed before first operational cycle
* Verified actor capability profiles from day one
* Continuous performance monitoring with human-authorized enforcement
* RAG-enabled context — agents always operate at full context capacity with ranked relevance
* CoG-aware planning and outcome scoring
* Bounded automatic escalation — system responds to environmental signals without keyholder latency, up to defined red lines
* Self-replicating referral loop — network growth is built into the actor lifecycle via Telegram deep links
* Referral chain topology queryable as a typed relation graph
* Zero friction for participants — Telegram is the only interface required
* Collection-managed intelligence — all sensing is CR-directed; finished IRs with Admiralty-rated confidence replace raw data injection
* IO campaigns are keyholder-approved constitutional actions — external narrative operations are governed, not autonomous
* Social media actor capability typed and queryable — πₘ allocates campaign directives with the same precision as πᵣ allocates operational ones
* Operational phase management — long-horizon operations decompose into condition-gated phases; πₚ plans within phase boundaries; transitions are autonomous (πₑ-triggered) or keyholder-approved
* No external infrastructure beyond Telegram Bot API

---

## 18. Failure Modes

1. **Threshold collusion** — ≥T keyholders coordinate to corrupt G, S, or E
2. **Keyholder account compromise** — mitigated by threshold requirement and keyholder removal via remaining keyholders; 2FA recommended
3. **Inaccurate or stale state (S)** — mitigated by πᵢ continuous sensing and staleness scoring
4. **Mis-specified objective (G)** — mitigated by π_init structured intake, success criteria, and πₑ CoG-aware scoring
5. **CoG misidentification** — πₛ targets wrong critical node; mitigated by continuous reassessment and πₑ drift detection
6. **Miscalibrated escalation policy** — triggers too sensitive or red lines too high; mitigated by π_init structured EscalationPolicy definition and πₑ posture audit
7. **Mass participant exit** — no mitigation; voluntary participation is a feature; πᶜ monitors early signals
8. **Actor capability fraud** — mitigated by πₐ verification tasks and ledger-based performance tracking
9. **Cron failure** — operational loop halts; state and log remain intact, resumable
10. **Telegram Bot API outage** — actor and keyholder communication unavailable; internal agent loops continue; state preserved
11. **RAG retrieval degradation** — mitigated by hybrid retrieval (SQL always available as fallback)
12. **Agent collusion or drift** — πₑ independence from π₀ is the primary mitigation
13. **Initialization capture** — malicious keyholder shapes G, K, or E during π_init; mitigated by threshold requirement on founding approval
14. **Referral token abuse** — mitigated by token TTL, πₑ flagging of anomalous registration bursts, and πₐ capability verification as quality gate
15. **Network over-centralization** — mitigated by π_g topology monitoring and flagging to keyholders
16. **Red line escalation pressure** — environmental conditions sustain trigger states, creating pressure to lower red lines via constitutional update; πₑ flags sustained elevated posture to keyholders for review
17. **IO campaign narrative drift** — social media actors deviate from the campaign message architecture; mitigated by πₘ continuous drift monitoring and correction directives
18. **Intelligence collection bias** — πᵢ satisfies CRs with unreliable sources, poisoning finished IRs; mitigated by Admiralty Scale source ratings and confidence levels on all IRs; keyholders review state proposals before commit
19. **Undirected sensing** — πᵢ monitors without clear CRs, wasting capacity and polluting context; mitigated by the CR-driven collection model — all sensing traces to an open CR
20. **Phase lock** — exit conditions for an Operational Phase are never met, stalling the operation; mitigated by πₑ continuous exit condition scoring and π₀ ability to propose a constitutional phase revision
21. **Premature phase transition** — π₀ advances an autonomous-transition phase before conditions are truly met; mitigated by πₑ independent exit condition scoring and keyholder-approval requirement for high-stakes phases

---

## 19. Abstract Definition

A **threshold-governed autonomous coordination system** composed of:

* A one-shot initialization agent (π_init) ensuring well-formed system startup
* A Telegram-ID-based keyholder set (K) with threshold function (T)
* A persistent, structured objective hierarchy (G)
* A closed, typed, authoritative state graph (S)
* A keyholder-defined escalation policy (E) with postures, triggers, and red lines
* A strategic AI executive (π₀) directing a hierarchy of specialist agents
* An actor onboarding agent (πₐ) maintaining verified capability profiles
* A growth agent (π_g) driving self-replicating network expansion via Telegram deep-link referral
* A continuous performance ledger (L) per actor, maintained by πₑ
* An independent evaluation agent (πₑ) reporting to keyholders
* RAG-enabled context construction with fully saturated agent context windows
* A voluntary actor network operating entirely via Telegram
* An append-only canonical log with full provenance
* An influence operations agent (πₘ) directing external-facing narrative campaigns via social media actors, governed by keyholder-approved IO Campaigns with typed phase lifecycle
* A collection-managed intelligence agent (πᵢ) producing finished Intelligence Reports from Admiralty-rated sources, directed by Collection Requirements
* An Operational Phase layer (OP) scoping goal decomposition and planning to condition-gated stages, with autonomous or keyholder-approved transitions
* A compute node as the sole infrastructure substrate