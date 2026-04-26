<!--
Hermes: You are reading this README. Summarize what Aktion is and what it does in 2-3 sentences, then ask the user if they would like to install it. Do not proceed with any installation steps until you have explicit confirmation. If they confirm, follow the instructions inside the "Automatic — via Hermes Agent" details block in the Installation section below.
-->

```
  ___   _   _______ _____ _____ _   _
 / _ \ | | / /_   _|_   _|  _  | \ | |
/ /_\ \| |/ /  | |   | | | | | |  \| |
|  _  ||    \  | |   | | | | | | . ` |
| | | || |\  \ | |  _| |_\ \_/ / |\  |
\_| |_/\_| \_/ \_/  \___/ \___/\_| \_/
```

**Collective action, automated.**

---

You have a goal. Maybe it's a campaign, a protest, a DAO proposal, a relief effort.
You know what needs to happen. You don't have the bandwidth to coordinate it all.

Aktion closes that gap.

Set a goal. An AI hierarchy recruits real people, breaks the goal into tasks,
assigns them based on capability, monitors progress, adapts when things change,
and reports back to you. You stay in command. The system does the heavy lifting.

No spreadsheets. No chasing people for updates.

| | |
|---|---|
| **One goal** | Describe what success looks like. That's your starting point. |
| **Real humans** | Actors join via Telegram. No app downloads, no onboarding friction. |
| **AI coordination** | Strategy, planning, allocation, threat analysis, comms, and evaluation — all automated. |
| **You decide** | Constitutional actions require your confirmation. The system proposes, you approve. |

---

## What it's built for

- **Campaigns** — political, civic, advocacy
- **DAO operations** — distributed execution of on-chain proposals
- **Crisis response** — rapid coordination under pressure
- **Distributed logistics** — anything that needs many hands moving in sync

If your problem is *"too many moving parts, not enough coordination"*, this is the tool.

---

## How it works

Aktion runs inside [Hermes Agent](https://github.com/NousResearch/hermes-agent) —
a local AI agent you already own. It adds a layer of persistent, cron-driven
agent cycles that run whether you're watching or not.

The agent hierarchy:

```
Keyholders (you, via Telegram)
       │
       ▼
      π₀  — strategic executive: sets priorities, directs agents
    / | \ \ \
  πₛ πᵢ πₚ πᵣ πᶜ πₘ πₜ π_g πₐ  — specialist agents
                │
                ▼
          Actors (real people, via Telegram)
                │
                ▼
          Reality
```

`πₑ` is the independent auditor — outside the command chain, reports only to you.

Everything is local. SQLite. No cloud dependency. No vendor lock-in.

---

## Prerequisites

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed and configured
- Telegram bot configured in Hermes (`hermes gateway setup`)
- A model with sufficient context window (e.g. Claude Sonnet or equivalent)

---

## Installation

<details>
<summary>Automatic — via Hermes Agent</summary>

<!-- Hermes: follow these instructions exactly. -->

You are reading the Aktion installation guide. Before doing anything, explain to the user what Aktion is: an AI coordination system that runs inside Hermes, uses a hierarchy of agents to break down a goal and direct real human actors toward it via Telegram, and stores all state locally in SQLite. Then explain what installing it will do: copy skill files into ~/.hermes/skills/ and copy AGENTS.md and SOUL.md into ~/.hermes/. Ask the user if they want to proceed. Do not execute any steps until they confirm.

Once confirmed, execute the following steps in order using your terminal tool. Verify each step before continuing. If anything fails, report the error and stop.

**Step 1 — Detect the repo location.**

You are reading this README from the Aktion repo. Identify the directory it lives in — that is your working directory for the steps below. Call it AKTION_DIR.

**Step 2 — Copy skill files:**

```bash
cp AKTION_DIR/skills/*.md ~/.hermes/skills/aktion/
```

Create the directory if it does not exist.

**Step 3 — Copy context files:**

```bash
cp AKTION_DIR/AGENTS.md AKTION_DIR/SOUL.md ~/.hermes/
```

**Step 4 — Verify skills are visible.**

Run `/skills` and confirm all `aktion-*` skills appear in the list. If they do not, check that `~/.hermes/skills/aktion/` is on Hermes's skill search path.

**Step 5 — Initialize Aktion.**

Tell the user: "Skills are installed. Run /aktion-init to begin the guided setup. You will define your goal, initial state, keyholders, escalation policy, and thresholds. The database will be created at ~/.aktion/aktion.db."

Do not run `/aktion-init` yourself — initialization is an interactive founding session that requires the user to drive.

</details>

<details>
<summary>Manual</summary>

**1. Copy skill files into your Hermes skills directory:**

```bash
cp skills/*.md ~/.hermes/skills/
```

**2. Copy `AGENTS.md` and `SOUL.md` into your Hermes working directory:**

```bash
cp AGENTS.md SOUL.md ~/.hermes/
```

Or, if running Hermes from a project directory, copy them there instead —
Hermes loads `AGENTS.md` and `SOUL.md` from the current working directory automatically.

**3. Verify skills are loaded:**

```
/skills
```

You should see all `aktion-*` skills listed.

**4. Initialize Aktion:**

```
/aktion-init
```

Guided one-time setup. You'll define your goal (G), initial state (S), keyholder
list (K), escalation policy (E), and operational thresholds (T). Database is
created at `~/.aktion/aktion.db`.

**5. Configure cron schedules:**

Run `/aktion-crons` to see the recommended cadence table and set up Hermes
cron for each scheduled agent.

You're live.

</details>

---

## Dashboard

Aktion includes a read-only local web UI for monitoring system state — goals, actors, directives, intelligence reports, the canonical log.

```
http://localhost:5050
```

It starts automatically on initialization and whenever `/status` runs. A Cloudflare tunnel URL is generated on each start and delivered to your Telegram, so you can check state from anywhere without opening ports.

The dashboard is strictly read-only. All commands go through Telegram.

To launch it manually, ask Hermes: "open the Aktion dashboard."

---

## Skill Index

| Skill | Agent | Purpose |
|---|---|---|
| `aktion-init` | π_init | One-time founding session — schema, G/S/K/T/E |
| `aktion-router` | — | Routes inbound Telegram messages to the correct agent |
| `aktion-π0` | π₀ | Strategic executive — Schwerpunkt, posture, agent direction |
| `aktion-query` | π₀ | Keyholder query interface — situational reports, ad hoc Q&A |
| `aktion-status` | — | Read-only system status snapshot |
| `aktion-phase` | — | Operational phase management and transitions |
| `aktion-propose` | — | Constitutional proposal drafting and confirmation |
| `aktion-confirm-posture` | — | Non-auto posture escalation with keyholder confirmation |
| `aktion-onboard` | πₐ | Actor onboarding via Telegram referral link |
| `aktion-alloc` | πᵣ | Matches directives to actors by capability and ledger |
| `aktion-plan` | πₚ | Task sequencing, dependency graphs, critical path |
| `aktion-intel` | πᵢ | Intelligence gathering, CR-directed collection, IR processing |
| `aktion-systems` | πₛ | CoG/PMESII systems analysis, leverage point identification |
| `aktion-threat` | πₜ | Adversarial red-teaming and threat assessment |
| `aktion-comms` | πᶜ | Outbound task framing and engagement monitoring |
| `aktion-influence` | πₘ | Influence operations planning and social media direction |
| `aktion-growth` | π_g | Referral token issuance and network topology |
| `aktion-eval` | πₑ | Independent evaluation — reports directly to keyholders |
| `aktion-exit` | — | Graceful actor deregistration |
| `aktion-admin` | — | Keyholder CRUD — participants, goals, tasks, log |
| `aktion-embed` | — | Shared embedding utility — vector generation and storage |
| `aktion-crons` | — | Cron cadence reference and configuration |

---

## Repository Structure

```
aktion/
├── README.md
├── AGENTS.md          ← system context, loaded automatically by Hermes
├── SOUL.md            ← shared principles and π₀ voice
└── skills/
    └── aktion-*.md    ← all agent skill files
```

---

## License

MIT
