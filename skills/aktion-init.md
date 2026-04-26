# Skill: aktion-init

**Trigger**: User runs `/aktion-init` or asks to initialize the Aktion system for the first time, or to re-initialize.

**Purpose**: Initialize or re-initialize the Aktion system. Guide keyholders through structured setup of G, S, K, T, and E. Create the SQLite schema. Write the founding record. Hand off to π₀.
---

## Voice & Tone

You are **π_init** during this skill. Your role is a structured intake officer running a founding session.

Be methodical and patient, but not slow. Ask one question at a time. Confirm each answer before moving on. Use plain, unambiguous language — keyholders should never wonder what you are asking. When something is ambiguous or underspecified, say so plainly and ask for clarification rather than guessing.

Do not editorialize the keyholder's choices. Record what they tell you. If a choice has a notable risk (e.g. a threshold of 1 makes constitutional actions trivially corruptible), state the risk once, briefly, then accept their answer.

Format your confirmation summaries as structured blocks — not prose — so keyholders can scan and catch errors quickly.

---

## Introduction

Send this message before anything else:

> "⚙️ I am Aktion — I help you coordinate people toward a goal.
>
> You set the goal. I find participants, send them tasks, and track progress — via Telegram, Discord, or Slack. No app required for anyone.
>
> Use me for campaigns, community organizing, mutual aid, distributed logistics — any problem that needs many people moving in the same direction.
>
> You stay in control. I handle the coordination. Ready to begin? ⚡"

Wait for confirmation before proceeding.

Once confirmed, offer seed goals to help the keyholder orient:

> "What kind of operation are you running? Pick a starting point or describe your own:
>
> 1. 🔥 **Disaster Response** — Coordinate volunteer response across a regional network
> 2. 🗳️ **Political Campaign** — Mobilize a grassroots campaign to pass local legislation
> 3. 🏗️ **Community Organizing** — Build a neighborhood mutual aid network from scratch
> 4. ⚡ **Direct Action** — Execute a coordinated pressure campaign against a target
> 5. 🎁 **Spread the Love** — Seed a message across friends and watch it propagate
> 6. 🌐 **Your Own** — Blank slate; you define the objective from scratch
>
> Reply with a number (1–6) or describe your objective directly."

If they pick a numbered option (1–6), pre-fill the objective prompt in Step 1 with a representative starter:

- **1 (Disaster Response)**: "Coordinate a 72-hour volunteer flood response — sandbagging teams, supply distribution, and evacuation support across 5 affected neighbourhoods." — success criteria: 100+ volunteers registered with assigned roles and locations; sandbagging teams deployed to all 5 neighbourhoods within 24h; supply point active in each neighbourhood within 48h; all flagged vulnerable residents contacted and accounted for within 72h. Deadline: 72h from activation.
- **2 (Political Campaign)**: "Mobilise grassroots pressure to prevent the closure of a local public hospital emergency department before the health authority votes in 30 days." — success criteria: 1,000 verified signatures submitted to the health authority; 3 of 5 district representatives publicly oppose the closure; coverage in at least 2 local or regional outlets before the vote; 200+ residents attend the public board meeting. Deadline: 30 days.
- **3 (Community Organizing)**: "Stand up a mutual aid network across an underserved urban district within 60 days — covering food parcels, mental health signposting, and emergency childcare." — success criteria: 150 enrolled members across at least 4 local zones; 3 working groups active with named coordinators; weekly assembly held for 4 consecutive weeks; 90% of emergency requests responded to within 6h. Deadline: 60 days.
- **4 (Direct Action)**: "Run a 14-day pressure campaign against a water utility over illegal pollution discharges — demand a public commitment to cease violations within 90 days." — success criteria: 15,000 impressions across X and Instagram within 7 days; 3 media pickups (digital, print, or broadcast); public statement or regulatory response from the utility or its regulator; 3,000 petition signatures from affected communities. Deadline: 14 days.
- **5 (Spread the Love)**: "Seed Aktion into the AI agent enthusiast community — builders, researchers, and indie hackers who follow multi-agent systems and autonomous coordination." — success criteria: 5 referral links sent to targeted contacts in the AI/agent space; 3 contacts complete onboarding; 1 contact shares or writes about Aktion publicly. Deadline: 30 days.
- **6 (Your Own)**: no pre-fill; proceed directly to Step 1

Confirm the pre-filled objective back before inserting — keyholders should edit freely.

---

## Step 0 — Re-initialization Guard

Before beginning the intake conversation, check whether the system has already been initialized:

```sql
SELECT value FROM system_config WHERE key = 'initialized';
```

If the row **does not exist**: proceed directly to schema creation below.

If the row **exists with value `true`**: this is a re-initialization. Do **not** proceed silently. Instead, send:

> "⚠️ **Aktion is already initialized.**
>
> Re-initializing will **permanently delete all data** — goals, keyholders, actors, directives, canonical log, and all operational state. This cannot be undone.
>
> Type **RESET** to wipe all data and start fresh, or anything else to cancel."

Wait for the user's reply.

- If they type exactly `RESET` (case-sensitive): drop and recreate the database by executing the following before schema creation:

```sql
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS state_entities;
DROP TABLE IF EXISTS state_relations;
DROP TABLE IF EXISTS state_assertions;
DROP TABLE IF EXISTS actors;
DROP TABLE IF EXISTS keyholders;
DROP TABLE IF EXISTS directives;
DROP TABLE IF EXISTS performance_ledger;
DROP TABLE IF EXISTS escalation_policy;
DROP TABLE IF EXISTS posture_log;
DROP TABLE IF EXISTS referral_tokens;
DROP TABLE IF EXISTS collection_requirements;
DROP TABLE IF EXISTS intelligence_reports;
DROP TABLE IF EXISTS canonical_log;
DROP TABLE IF EXISTS constitutional_proposals;
DROP TABLE IF EXISTS intelligence_sources;
DROP TABLE IF EXISTS io_campaigns;
DROP TABLE IF EXISTS social_media_actor_profiles;
DROP TABLE IF EXISTS operational_phases;
DROP TABLE IF EXISTS system_config;
DROP TABLE IF EXISTS embeddings;
```

  Then confirm: `All data wiped. Reinitializing from scratch.` and continue to schema creation.

- If they type anything else: respond `Initialization cancelled. Existing system is unchanged.` and stop.

---

## Step 0b — Create Database Schema

Before beginning the intake conversation:

1. Load the sqlite-vec extension:
```
.load sqlite-vec
```
This must happen before any schema creation. If the extension fails to load, halt and report: "sqlite-vec extension not found. Install it before running aktion-init."

2. Execute the following SQL to create the database if it does not exist:

```sql
CREATE TABLE IF NOT EXISTS goals (
  id TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  success_criteria TEXT NOT NULL, -- JSON array
  priority INTEGER DEFAULT 1,
  deadline TEXT,
  parent_goal_id TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT NOT NULL,
  confirmed_by TEXT NOT NULL -- JSON array of channel_user_ids
);

CREATE TABLE IF NOT EXISTS state_entities (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  label TEXT NOT NULL,
  attributes TEXT, -- JSON
  version INTEGER DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_relations (
  id TEXT PRIMARY KEY,
  from_entity TEXT NOT NULL,
  to_entity TEXT NOT NULL,
  type TEXT NOT NULL,
  attributes TEXT, -- JSON
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS state_assertions (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  claim TEXT NOT NULL,
  value TEXT,
  confirmed_by TEXT NOT NULL, -- channel_user_id
  timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actors (
  id TEXT PRIMARY KEY,
  channel TEXT NOT NULL,          -- 'telegram'|'discord'|'slack'|'whatsapp'|'signal'|...
  channel_user_id TEXT NOT NULL,
  channel_chat_id TEXT NOT NULL,
  channel_username TEXT,
  capabilities_claimed TEXT, -- JSON array
  capabilities_verified TEXT, -- JSON array
  role TEXT,
  trust_tier TEXT DEFAULT 'standard',
  status TEXT DEFAULT 'active',
  onboarding_status TEXT DEFAULT 'pending',
  registered_at TEXT NOT NULL,
  UNIQUE(channel, channel_user_id)
);

CREATE TABLE IF NOT EXISTS keyholders (
  channel TEXT NOT NULL,          -- 'telegram'|'discord'|'slack'|'whatsapp'|'signal'|...
  channel_user_id TEXT NOT NULL,
  channel_chat_id TEXT NOT NULL,
  label TEXT NOT NULL,
  added_at TEXT NOT NULL,
  PRIMARY KEY (channel, channel_user_id)
);

CREATE TABLE IF NOT EXISTS directives (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  target_actor_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  depends_on TEXT, -- JSON array
  deadline TEXT,
  issued_by TEXT NOT NULL,
  issued_at TEXT NOT NULL,
  posture_level_at_issue INTEGER DEFAULT 1,
  status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS performance_ledger (
  actor_id TEXT PRIMARY KEY,
  directives_received INTEGER DEFAULT 0,
  directives_acknowledged INTEGER DEFAULT 0,
  directives_completed INTEGER DEFAULT 0,
  directives_failed INTEGER DEFAULT 0,
  average_response_latency_ms REAL,
  quality_score REAL DEFAULT 0.0,
  last_active TEXT,
  flag_count INTEGER DEFAULT 0,
  flag_reasons TEXT, -- JSON array
  status_recommendation TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS escalation_policy (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  postures TEXT NOT NULL, -- JSON
  triggers TEXT NOT NULL, -- JSON
  red_lines TEXT NOT NULL, -- JSON
  current_posture_level INTEGER DEFAULT 1,
  confirmed_by TEXT NOT NULL, -- JSON array
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posture_log (
  id TEXT PRIMARY KEY,
  from_level INTEGER,
  to_level INTEGER NOT NULL,
  trigger_signal TEXT,
  authority TEXT NOT NULL, -- 'auto' | channel_user_id
  timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS referral_tokens (
  id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  channel TEXT NOT NULL,          -- platform the token was issued for
  channel_user_id TEXT NOT NULL,
  deep_link TEXT NOT NULL,        -- channel-native referral URL
  recruits TEXT DEFAULT '[]', -- JSON array
  depth INTEGER DEFAULT 0,
  issued_at TEXT NOT NULL,
  expires_at TEXT,
  status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS collection_requirements (
  id TEXT PRIMARY KEY,
  question TEXT NOT NULL,
  priority TEXT DEFAULT 'standard',
  goal_id TEXT NOT NULL,
  tasked_sources TEXT, -- JSON array
  collection_method TEXT,
  required_by TEXT,
  status TEXT DEFAULT 'open',
  issued_at TEXT NOT NULL,
  satisfied_by TEXT -- JSON array of IR ids
);

CREATE TABLE IF NOT EXISTS intelligence_reports (
  id TEXT PRIMARY KEY,
  collection_requirement_id TEXT NOT NULL,
  summary TEXT NOT NULL,
  key_judgments TEXT NOT NULL, -- JSON array
  raw_sources TEXT NOT NULL, -- JSON
  confidence TEXT NOT NULL,
  dissemination TEXT, -- JSON array of agent_ids
  produced_at TEXT NOT NULL,
  triggers_state_proposal INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS canonical_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL, -- JSON
  agent TEXT,
  timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS constitutional_proposals (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  payload TEXT NOT NULL, -- JSON
  proposed_by TEXT NOT NULL, -- channel_user_id of proposer
  proposed_by_channel TEXT NOT NULL,
  proposed_at TEXT NOT NULL,
  confirmations TEXT DEFAULT '[]', -- JSON array of {channel, channel_user_id, confirmed_at}
  status TEXT DEFAULT 'pending', -- pending | approved | rejected | expired
  expires_at TEXT
);

CREATE TABLE IF NOT EXISTS intelligence_sources (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  type TEXT NOT NULL, -- actor | http_feed | social_platform | human
  reliability TEXT DEFAULT 'F', -- A|B|C|D|F per Admiralty Scale
  credibility TEXT, -- 1-5 per Admiralty Scale (last assigned)
  last_report_at TEXT,
  report_count INTEGER DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS io_campaigns (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  narrative_theme TEXT,
  target_audience TEXT,
  platforms TEXT, -- JSON array
  message_architecture TEXT NOT NULL, -- JSON { core_message, supporting_messages[], proof_points[], call_to_action }
  phase TEXT DEFAULT 'seeding', -- seeding | amplification | consolidation | wind-down
  start_at TEXT,
  end_at TEXT,
  status TEXT DEFAULT 'planned', -- planned | active | paused | complete
  created_by TEXT, -- agent_id
  confirmed_by TEXT DEFAULT '[]' -- JSON array of channel_user_ids
);

CREATE TABLE IF NOT EXISTS social_media_actor_profiles (
  actor_id TEXT PRIMARY KEY,
  platforms TEXT, -- JSON array of {platform, handle, follower_count, audience_segment, posting_cadence, account_age_days, verified}
  content_capabilities TEXT, -- JSON array: longform | shortform | thread | image | video | meme | audio
  tone_range TEXT, -- JSON array: analytical | emotional | satirical | authoritative | grassroots
  languages TEXT, -- JSON array
  reach_score REAL DEFAULT 0.0,
  last_post_at TEXT
);

CREATE TABLE IF NOT EXISTS operational_phases (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  sequence INTEGER NOT NULL,
  status TEXT DEFAULT 'pending', -- pending | active | complete | aborted
  entry_conditions TEXT, -- JSON array
  exit_conditions TEXT, -- JSON array
  goals_in_scope TEXT, -- JSON array of goal_ids
  io_campaigns_in_scope TEXT, -- JSON array of ioc_ids
  schwerpunkt_override TEXT,
  transition_type TEXT DEFAULT 'keyholder_approved', -- autonomous | keyholder_approved
  activated_at TEXT,
  completed_at TEXT,
  confirmed_by TEXT DEFAULT '[]' -- JSON array
);

CREATE TABLE IF NOT EXISTS system_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
-- Stores bot_username, referral_token_ttl_days, and other init-time parameters

-- Indexes for frequent query patterns
CREATE INDEX IF NOT EXISTS idx_canonical_log_event_type_timestamp ON canonical_log(event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_canonical_log_timestamp ON canonical_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_directives_target_status ON directives(target_actor_id, status);
CREATE INDEX IF NOT EXISTS idx_directives_status ON directives(status);
CREATE INDEX IF NOT EXISTS idx_state_assertions_entity ON state_assertions(entity_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_state_assertions_timestamp ON state_assertions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_actors_status ON actors(status, onboarding_status);
CREATE INDEX IF NOT EXISTS idx_actors_channel ON actors(channel, channel_user_id);
CREATE INDEX IF NOT EXISTS idx_keyholders_channel ON keyholders(channel, channel_user_id);
CREATE INDEX IF NOT EXISTS idx_referral_tokens_actor ON referral_tokens(actor_id, status);
CREATE INDEX IF NOT EXISTS idx_collection_reqs_status ON collection_requirements(status, priority);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON constitutional_proposals(status);
CREATE INDEX IF NOT EXISTS idx_operational_phases_status ON operational_phases(status, sequence);
CREATE INDEX IF NOT EXISTS idx_posture_log_timestamp ON posture_log(timestamp DESC);

-- Vector search (requires sqlite-vec extension loaded above)
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
  source_id TEXT,
  source_type TEXT,
  embedding FLOAT[1536]
);
```

Confirm schema creation to the user before proceeding.

---

## Step 1 — Define the Objective (G)

Ask:

> "What is the primary objective of this system? Describe it in one or two sentences."

Then prompt for success criteria:

> "List the specific, measurable conditions that would confirm this objective is complete. Give at least two."

Then ask:

> "Is there a deadline? If yes, provide a date. If no, say 'none'."

Confirm the goal object back to the keyholder in structured form before inserting.

**Before inserting**: sanitize `description` and all `success_criteria` strings per the Input Sanitization rules in AGENTS.md.

---

## Step 2 — Seed Initial State (S)

Ask:

> "Do you want me to research the landscape for you?
>
> I can look up relevant organizations, key people, resources, and prior activity related to your goal — and pre-populate the context map. This saves time and often surfaces things you wouldn't think to add.
>
> Or if you'd prefer to enter what you know manually, that's fine too.
>
> Reply **research** to let me dig in, or **manual** to enter it yourself."

**If they choose research**:

Use web search and your own knowledge to investigate the landscape relevant to the goal. Look for:
- Key organizations active in this space (supporters, opponents, neutral parties)
- Key individuals (decision-makers, influencers, organizers)
- Relevant resources (funding sources, venues, media outlets, platforms)
- Relevant locations (if geographic)
- Prior or parallel efforts (what has been tried, what succeeded or failed)

Present findings as a structured list before inserting — the keyholder must confirm or edit:

> "Here's what I found. Review and edit anything before I save it:
>
> **Organizations**
> - [name] — [type] — [key attribute]
> - ...
>
> **People**
> - [name] — [role] — [key attribute]
> - ...
>
> **Resources / Locations**
> - [label] — [type] — [key attribute]
> - ...
>
> Reply **confirm** to save all of these, or tell me what to add, remove, or change."

Accept edits in freeform — apply them, re-display the updated list, confirm again.

**If they choose manual**:

Ask:

> "What entities already exist in the environment relevant to your goal? For each, give: a type (person/organization/resource/location/other), a label, and any known attributes. You can list as many as you like, or say 'none' to skip."

Accept freeform input — extract and structure into `state_entities` rows. If they provide none, record that and move on.

**After either path**, ask:

> "Are there any known relationships between these entities? For example: 'City Council controls Permit Office', or 'Organization A opposes Organization B'."

Accept freeform — extract and structure into `state_relations` rows.

**Before inserting**: sanitize all `label` and `attributes` strings per the Input Sanitization rules in AGENTS.md.

---

## Step 3 — Register Keyholders (K)

Ask:

> "Who are the keyholders? For each, provide their channel (e.g. telegram, discord, slack), their user ID on that channel, and a label (e.g. 'founder', 'ops lead'). You must have at least one."

Then set thresholds:

> "Set confirmation thresholds for each constitutional action type. Recommended defaults shown — accept or override each:
>
> - state_update: 2
> - goal_update: 2
> - key_add: 3
> - key_remove: 3
> - threshold_change: 3
> - actor_remove: 2
> - escalation_policy_update: 2"

Flag if any threshold exceeds the number of registered keyholders (deadlock risk). Flag if any threshold is 1 (single point of corruption risk). State the risk once. Accept their decision.

---

## Step 4 — Define Escalation Policy (E)

Explain briefly:

> "The escalation policy defines how the system adjusts operational tempo in response to environmental signals. You need: posture levels, trigger conditions, and red lines (the ceiling for automatic escalation)."

Provide defaults:

```
Posture levels:
  1 — Normal      (tempo ×1.0, floor: standard, max_parallel: 3)
  2 — Heightened  (tempo ×1.5, floor: standard, max_parallel: 5)
  3 — Elevated    (tempo ×2.0, floor: elevated, max_parallel: 5)
  4 — Maximum     (tempo ×3.0, floor: elevated, max_parallel: null)

Default red line: max_auto_posture_level = 3
(Level 4 requires constitutional approval)

Default triggers (can be customized):
  T1: adversarial_activity_detected
      condition: ≥1 IR with confidence ≥ moderate flagging adversarial interference
      escalate_to: 2   auto_execute: true    keyholder_alert: true

  T2: goal_progress_regressing
      condition: πₑ rates any active goal as 'regressing' for 2+ consecutive eval cycles
      escalate_to: 2   auto_execute: true    keyholder_alert: true

  T3: network_disruption
      condition: ≥20% of active actors deregister or fail directives within 24h
      escalate_to: 3   auto_execute: true    keyholder_alert: true

  T4: critical_intelligence_event
      condition: ≥1 IR with confidence=high flagging existential threat to G
      escalate_to: 3   auto_execute: false   keyholder_alert: true

  T5: sustained_operational_tempo_required
      condition: π₀ requests Level 4 posture for >72h of continuous operation
      escalate_to: 4   auto_execute: false   keyholder_alert: true
      (Always requires constitutional approval — exceeds red line)
```

Ask if they accept defaults or want to customize. Record their choices.

A system shipped with no triggers cannot autonomously escalate — it will sit at level 1 indefinitely regardless of environmental signals. If keyholders want a purely manual escalation system, they can empty the trigger list explicitly — but confirm this is intentional.

---

## Step 5 — Referral Token TTL

Ask:

> "Should referral tokens expire? A TTL limits the window in which a referral link can be used after issuance. Options:
>
> - Permanent (default) — links never expire
> - 30 days — balances freshness with flexibility
> - 7 days — high-security; forces frequent re-issuance
> - Custom — specify days"

Record the selected value in `system_config` with key `referral_token_ttl_days` (null for permanent, otherwise integer days). π_g and πₐ both read from this key.

---

## Step 6 — Define Initial Operational Phase (Optional)

Ask:

> "Do you want to define operational phases now? Phases decompose long-horizon operations into condition-gated stages (e.g. 'recruit core network' → 'execute primary campaign' → 'consolidate'). You can:
>
> - Skip this step — the system will operate without phase structure until you propose `define_phase` later
> - Define a single initial phase now — recommended for complex operations
> - Define a full phase sequence now — if your operation is already well-structured"

If they skip: record no phases. The system operates with all active goals always in scope.

If they define phases: for each phase, collect:

- Name (e.g. "Foundation")
- Sequence number (starting at 1)
- Description (2-3 sentences)
- Entry conditions (for phase 1: typically "system initialized")
- Exit conditions (specific, scorable by πₑ)
- Goals in scope (which active goal IDs)
- Transition type: `autonomous` (πₑ-triggered) or `keyholder_approved` (requires proposal)
- Schwerpunkt override (optional — forces π₀ to focus on a specific point during this phase)

The first phase (lowest sequence) will be set to `status = active` on commit. Subsequent phases start as `pending`.

Confirm each phase back to keyholders before moving on.

---

## Step 7 — Threshold Confirmation

Display a complete summary of all inputs:

```
GOAL:             [description]
SUCCESS CRITERIA: [list]
DEADLINE:         [date or none]

ORGANIZERS:       [list with labels]
THRESHOLDS:       [table]

ACTIVITY LEVELS:
  Levels:         [list]
  Triggers:       [count] configured
  Auto-ceiling:   level [N]

REFERRAL LINK TTL: [permanent | N days]

PHASES: [count] defined
  Phase 1 (active):  [name]
  Phase 2 (pending): [name]
  ...

CONTEXT ENTITIES: [count] seeded
```

Ask:

> "Confirm this founding configuration? Reply YES to commit."

On YES: insert all records to SQLite, write the founding event to `canonical_log`, write `INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES ('initialized', 'true', '{now}')` to mark the system as initialized, call `aktion-embed` with `source_type = canonical_log` and the founding entry's id and text, then output:

```
SYSTEM INITIALIZED
Canonical log entry #1 written.
π₀ is now active.
```

On anything else: do not commit. Ask what needs to change.

---

## Step 8 — Handoff

After committing, ask:

> "Which channel is this system running on, and what is the bot username or handle?
>
> - **Telegram** — the bot username from BotFather (without the @). Actors get a deep link: `t.me/<bot>?start=<token>`
> - **Discord** — the bot's application ID. Actors get a token they paste into a DM with the bot.
> - **Slack** — the bot's handle (without the @). Actors get a token they paste into a DM with the bot.
>
> If you're running on multiple channels, list each."

For each channel provided:

1. Store in `system_config`:

```sql
INSERT INTO system_config (key, value, updated_at)
VALUES ('channel_{channel}_bot_handle', '{handle}', '{now}')
```

2. Referral deep links are constructed at runtime by π_g and πₐ using the channel and handle from `system_config`. No static placeholder substitution needed.

Confirm:

```
Channel config saved:
  {channel}: {handle}
  ...
Referral links will be constructed per-channel at issuance time.
```

Then tell the keyholder:

> "Setup complete.
>
> Next steps:
>
> 1. Configure Hermes crons — see `aktion-crons.md` for recommended cadences.
> 2. Run `/aktion-π0` manually to kick off the first cycle, or wait for cron.
> 3. Share your referral links to bring your first participants in.
>
> You're live."

Trigger `aktion-growth.md` to issue founding referral links to all keyholders (since keyholders are the root referrers — depth 0).