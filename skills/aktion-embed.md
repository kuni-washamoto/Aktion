# Skill: aktion-embed

**Trigger**: Called internally by other skills after writing to canonical_log, issuing a directive, committing a state assertion, completing an onboarding session, or committing a posture transition. Never called directly by users or keyholders.

**Purpose**: Generate an embedding for a text passage and insert it into the `embeddings` virtual table. Single shared utility — all skills call this rather than duplicating embedding logic.

---

## Interface

Caller must supply:

| Parameter | Type | Description |
|---|---|---|
| `source_id` | TEXT | The `id` (or `INTEGER` cast to TEXT) of the source row — e.g. `canonical_log.id`, `directives.id`, `actors.id` |
| `source_type` | TEXT | One of: `canonical_log`, `directive`, `state_assertion`, `actor_onboarding`, `posture_transition` |
| `text` | TEXT | The passage to embed. Compose this in the caller (see guidelines below). |

---

## Execution

1. Generate a float vector for `text` using the active embedding model (1536 dimensions — matches `text-embedding-3-small` / `ada-002` default; update dimension constant here if model changes).

2. Insert into the virtual table:

```sql
INSERT INTO embeddings (source_id, source_type, embedding)
VALUES ('{source_id}', '{source_type}', {float_vector});
```

3. No return value. If the insert fails (extension not loaded, dimension mismatch): log a warning to canonical log with `event_type = 'embed_error'` and continue — embedding failures must never block the primary write.

---

## Text Composition Guidelines (for callers)

The embedding is only as useful as the text you pass. Compose a dense, meaningful passage — not a raw JSON blob.

| source_type | Recommended text composition |
|---|---|
| `canonical_log` | `"{event_type}: {flattened payload key=value pairs}"` |
| `directive` | `"Directive {id} [{type}] to actor {target_actor_id}: {payload}. Required capability: {capability}. Deadline: {deadline}."` |
| `state_assertion` | `"Entity {entity_id}: {claim} = {value}. Confirmed by {confirmed_by}."` |
| `actor_onboarding` | `"Actor {actor_id} onboarded. Verified capabilities: {capabilities_verified}. Trust tier: {trust_tier}. Depth: {depth}."` |
| `posture_transition` | `"Posture transition L{from_level} → L{to_level}. Trigger: {trigger_signal}. Authority: {authority}."` |

---

## Semantic Query (for retrieval callers)

Skills that need semantic retrieval (e.g. `aktion-query`, `aktion-π0` context building) can call vec0 nearest-neighbour search:

```sql
SELECT e.source_id, e.source_type, e.distance
FROM embeddings e
WHERE e.embedding MATCH {query_vector}
  AND k = 10
ORDER BY e.distance;
```

Join back to the source table using `source_id` and `source_type` to retrieve the full record. Merge semantic results with SQL retrieval results; rank by combined relevance + recency.
