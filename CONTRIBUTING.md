# Contributing to Aktion

Aktion has no code. The system is its agents — skill files, system context, and the principles that govern them. Contributions are changes to those artifacts.

---

## What You Can Contribute

- **New skills** — new agent capabilities (`skills/aktion-*.md`)
- **Improvements to existing skills** — better prompting, tighter logic, corrected behavior
- **Dashboard** — the read-only local web UI (`dashboard/app.py`): new views, better data presentation, performance charts, UX improvements
- **AGENTS.md** — schema additions, new tables, updated dispatch logic, agent hierarchy changes
- **SOUL.md** — refinements to shared principles or π₀ voice (high bar — read the section below)
- **README.md** — installation, usage, architecture clarity
- **Vision documents** — proposals for where the system should go (`vision/`)

---

## Before You Start

Read [SOUL.md](SOUL.md) and [AGENTS.md](AGENTS.md) fully. They define the system's operating principles, constitutional rules, and agent hierarchy. Contributions that violate these — even subtly — will be rejected.

The core invariants:

- Constitutional actions require threshold-confirmed keyholder approval. No skill bypasses this.
- πₑ is independent. Nothing routes through or reports to π₀.
- The canonical log is append-only. No skill edits history.
- Actors are the interface to reality. Their capacity is finite and must be protected.

If your contribution would require relaxing any of these, propose it as a vision document first.

---

## Skill Files

Each skill file is a prompt that runs inside Hermes Agent. The file *is* the agent.

**Structure**: Look at an existing skill before writing one. Each file defines the agent's identity, its inputs, its decision logic, its outputs, and any state it reads or writes.

**Voice**: Match the voice defined for that agent in AGENTS.md. Do not inject SOUL.md into skills that aren't `aktion-π0` or `aktion-query` — it collapses the distinctions between agents.

**State discipline**: Agents read from and write to SQLite via the schema in AGENTS.md. If your skill needs new tables or columns, update AGENTS.md and `aktion-init.md` together.

**Constitutional boundaries**: Skills flag, recommend, and propose. They do not self-confirm, self-escalate past the red line, or modify G/S/K/E unilaterally.

---

## Dashboard

The dashboard (`dashboard/app.py`) is a read-only local web UI. It surfaces state from the SQLite DB — it does not write to it, issue directives, or participate in the agent hierarchy.

**Scope**: views, charts, and data presentation only. No mutations. If you want to add a feature that writes to the DB, that belongs in a skill, not the dashboard.

**Data access**: read directly from `~/.aktion/aktion.db` via the same schema defined in AGENTS.md. Do not introduce separate data pipelines or secondary caches.

**Dependencies**: keep it minimal. The current stack is intentionally lightweight. New Python packages require a clear justification.

**Read-only is a hard constraint.** The dashboard must never expose any endpoint that modifies DB state — even indirectly.

---

## Proposing Changes to SOUL.md

SOUL.md is the constitutional layer. Changes here affect every agent and every deployment. The bar is high.

A change to SOUL.md is appropriate when:
- A principle is ambiguous in a way that produces real operational failures
- A new invariant is necessary and cannot be expressed at the skill level

A change to SOUL.md is not appropriate for:
- Stylistic preference
- Adapting to a specific deployment's needs (handle that in your own skill files)
- Adding operational detail that belongs in a specific agent

---

## Submitting

1. Fork the repository
2. Make your changes
3. Open a pull request with a clear description of what changed and why — especially how it aligns with or extends the vision
4. Reference the relevant principle or architectural constraint your change addresses

---

## What Gets Rejected

- Skills that bypass constitutional boundaries
- Changes that collapse agent voice distinctions
- Additions that increase actor cognitive load without commensurate mission value
- Speculative features not grounded in the system's current architecture
- Anything that introduces ambiguity into the constitutional rules
