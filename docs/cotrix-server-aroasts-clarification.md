# Cotrix Server `/aroasts` Endpoint: Implementation Clarification

> **Response to**: `cotrix-server-aroasts-endpoint-spec.md`
> **From**: TasterMatrix backend team
> **Date**: 2026-07-04
> **Status**: ✅ ArtisanZ answers submitted — ready for implementation
> **Priority**: Blocks implementation start

---

## TL;DR

We analyzed the spec against our database. **All 17 requested fields are already stored** when ArtisanZ uploads via `POST /aroast` — the list endpoint is straightforward (~0.5-1 day implementation). However, we need clarification on **5 questions** before shipping.

**How to respond**: Edit this file directly — add your answers under each `### Answer (ArtisanZ):` block. Or send a revised spec.

---

## What We Found During Analysis

### 1. Current Upload/Download Asymmetry

| Direction | Endpoint | Behavior |
|---|---|---|
| **Upload** | `POST /aroast` | ArtisanZ sends full payload (curves + events + 17+ fields). We parse and store across 4 tables + 2 JSONB columns. |
| **Download** (current) | `GET /aroast/:uuid` | Returns only **6 fields** (`roast_id`, `label`, `machine`, `amount`, `end_weight`, `modified_at`). This is a lightweight sync-check endpoint — ArtisanZ uses `modified_at` to decide whether to re-POST. |

**Implication**: The spec's assumption on line 138 — *"If `has_tm_profile=true`, client calls `GET /aroast/{roast_id}` to get complete `tm_profile`"* — requires us to **expand the existing GET endpoint** to return full data. This is a behavior change (forward-compatible, but worth flagging).

### 2. Data Storage Architecture

When ArtisanZ uploads a roast, we store:

| Storage | Content | Spec relevance |
|---|---|---|
| `roasting.roast_records` (main table) | Flat fields: `label`, `machine`, `amount_kg`, `end_weight_kg`, `cupping_score`, `whole_color`, `roasted_at`, `modified_at`, etc. | 10 of 17 spec fields |
| `raw_plus_payload` (JSONB) | **Complete original ArtisanZ payload** — verbatim copy of what ArtisanZ POSTed | **All 17 spec fields + more** |
| `raw_profile` (JSONB) | ArtisanZ `tm_profile` object: `timex[]`, `temp1[]`, `temp2[]`, `extratimex[]`, `extratemp1[]`, `extratemp2[]`, `timeindex`, `computed{}`, `beans`, `mode`, etc. | Curve arrays + bean metadata |
| `roasting.roast_curve_points` | Parsed curve points (1 row per sample) | Powers `has_tm_profile` detection |
| `roasting.roast_events` | Parsed events: CHARGE/TP/DRY/FCs/DROP with timestamps + temperatures | Backup source for process metrics |
| `roasting.roast_measures` | Parsed measures: DEV_time, DEV_ratio, AUC, etc. | Backup source for development metrics |

**Key insight**: The simplest implementation reads directly from `raw_plus_payload` JSONB — no multi-table JOIN needed, field names already match the spec.

### 3. Field Availability Confirmation

Verified against 35 production roasts on CVM:

| Spec Field | In `raw_plus_payload`? | Sample value | Notes |
|---|---|---|---|
| `roast_id` | ✅ | `d7cf7b91a5244e98b9370104bb496879` | UUID string |
| `modified_at` | ✅ | `2026-07-03T14:30:00.000Z` | ISO 8601 |
| `date` | ✅ | `2026-07-03T14:20:00.000Z` | ISO 8601 |
| `label` | ✅ | `W143`, `N536` | Short batch label |
| `coffee` | ✅ | `CG-000003`, `N536` | **Batch code, not bean name** |
| `machine` | ✅ | `HB Model S` | |
| `amount` | ✅ | `0.8` | Numeric |
| `end_weight` | ✅ | `0.72` | Numeric |
| `drop_temp` | ✅ | `200.1` | Numeric |
| `FCs_temp` | ✅ | `187.4` | Numeric |
| `FCs_time` | ✅ | `444` | Numeric (seconds) |
| `DRY_temp` | ✅ | `152.2` | Numeric |
| `DRY_time` | ✅ | `286` | Numeric (seconds) |
| `DEV_time` | ✅ | `146` | Numeric (seconds) |
| `DEV_ratio` | ✅ | `19`, `16.4` | Numeric (percentage) |
| `cupping_score` | ❌ **Not in payload** | `NULL` | See Q2 |
| `whole_color` | ❌ **Not in payload** | `NULL` | See Q2 |

---

## Questions for ArtisanZ Team

### Q1: `coffee_label` — what format do you expect?

The spec describes `coffee_label` as *"Human-readable coffee name (join from coffee table)"*. But our data has two candidate sources, neither of which is a "human-readable name":

| Source | Sample values | Format |
|---|---|---|
| `raw_plus_payload.coffee` | `CG-000003`, `N536` | Batch code (internal) |
| `raw_profile.beans` | `W143`, `W487`, `N536` | Bean identifier (short code) |
| — | — | We do NOT have "Ethiopia Yirgacheffe 2024" style long names |

**Options** (please pick one):

- **(A)** Return `raw_profile.beans` (bean ID like "W143") — matches what ArtisanZ originally uploaded as `beans`
- **(B)** Return `raw_plus_payload.coffee` (batch code like "CG-000003") — matches what ArtisanZ originally uploaded as `coffee`
- **(C)** Return `null` — we don't have a true human-readable name; client uses `coffee` + `label` instead
- **(D)** Other: ___________

#### Answer (ArtisanZ):

**Answer: (A) — Return `raw_profile.beans` (bean ID like "W143")**

ArtisanZ users identify their roasts by the `beans` field they originally entered (e.g., "W143", "N536"). Combined with the `label` field (batch label like "Yirgacheffe #47"), users have enough context to pick roasts for comparison. We do not expect long descriptive names — the batch code + label pair is the natural identifier in the ArtisanZ UI.

`coffee_label` in the list response should be `raw_profile.beans`. If `raw_profile` is null or `beans` key is missing, return `null`.

---

### Q2: `cupping_score` and `whole_color` — null acceptable in list response?

These two fields are **NOT uploaded by ArtisanZ**. They're entered separately via our Cotrix cupping/color workflow (cuppers score the roast after it's done). For most roasts, these will be `NULL` unless a cupper has evaluated them.

**Spec line 134-135** says `float | null` — implying null is acceptable. We want to confirm:

- **(A)** Yes, return `null` when not yet cupped (matches spec) ✅ recommended
- **(B)** Omit these fields from response entirely when null
- **(C)** Return `0` or `-1` as sentinel value
- **(D)** Other: ___________

#### Answer (ArtisanZ):

**Answer: (A) — Yes, return `null` when not yet cupped.**

This matches the spec (`float | null`). ArtisanZ client already handles null gracefully — uncupped roasts simply show "—" in the comparison dialog. No sentinel values needed.

---

### Q3: `has_tm_profile` — what exactly counts as "having tm_profile"?

The spec says:
> `has_tm_profile` tells the client whether the full curve data (`tm_profile`) is available for this roast. If `true`, the client can call `GET /aroast/{roast_id}` to get the complete `tm_profile` (timex/temp1/temp2 arrays) for curve overlay.

We have two ways to detect this:

- **(A)** `EXISTS(SELECT 1 FROM roast_curve_points WHERE roast_record_id = r.id)` — checks if we successfully parsed curve points into structured storage
- **(B)** `raw_profile ? 'timex' AND jsonb_array_length(raw_profile->'timex') > 0` — checks if the original ArtisanZ payload had curve arrays
- **(C)** Both: true only if both structured parse succeeded AND raw profile exists

Current production stats: 34 of 35 roasts have curve data (1 roast uploaded without curves).

**Recommendation**: **(A)** — checks our actual ability to return curve data. If parse failed (rare edge case), we shouldn't promise the client that `GET /aroast/:uuid` will return curves.

#### Answer (ArtisanZ):

**Answer: (A) — Check `roast_curve_points` table existence.**

We agree with your recommendation. If the structured parse failed, the client would call `GET /aroast/:uuid` and get empty/null curve arrays, which is a poor experience. Checking actual parse success (`roast_curve_points`) is the reliable signal.

---

### Q4: `GET /aroast/:uuid` expansion — forward-compatible change OK?

**Current behavior**: Returns 6 fields (sync protocol).
**Proposed behavior**: Returns **all 17 spec fields + `tm_profile` object** (timex/temp1/temp2 arrays).

This is an **additive change** — existing fields stay the same, we just add more. The Fastify response schema uses `result: Type.Any()`, so schema validation won't break.

**Risk assessment**:
- ✅ ArtisanZ sync protocol continues to work (existing 6 fields preserved)
- ✅ JSON clients ignore unknown fields by default
- ⚠️ Response payload size increases significantly (curve arrays can be 500+ points × 3 series)
- ⚠️ If ArtisanZ client has any strict field-count validation, it would break (unlikely but worth confirming)

**Options**:

- **(A)** Yes, expand GET to return full data (recommended for spec compliance)
- **(B)** Keep GET as sync protocol only; add new endpoint `GET /aroast/:uuid/full` for complete data
- **(C)** Add query param `?full=true` to GET to opt-in to full response
- **(D)** Other: ___________

#### Answer (ArtisanZ):

**Answer: (C) — Add `?full=true` query param to existing GET endpoint.**

Reasoning:
1. ArtisanZ's sync protocol calls `GET /aroast/{uuid}` ~every 30 seconds during live recording — it only needs `modified_at` for the sync check. Expanding the default response would add 50-200KB per call × 120 calls/hour = significant bandwidth waste.
2. The comparison overlay feature calls `GET /aroast/{uuid}?full=true` only when the user explicitly selects a historical roast for comparison — this is a one-time call, not polling.
3. Query param is forward-compatible: existing sync code doesn't send `?full=true`, so it gets the current 6-field response unchanged.
4. No new endpoint to maintain — one route, two response modes.

**Expected `?full=true` response**: All current 6 fields + the complete `tm_profile` object (`timex`, `temp1`, `temp2`, `timeindex`, `specialevents`, `computed`, etc.). The client treats `tm_profile` as an opaque blob — it passes it directly to `deserialize()` equivalent for curve rendering.

**Payload size note**: A typical 15-minute roast at 1Hz sampling = ~900 points × 3 arrays = ~22KB JSON. This is acceptable for a one-time fetch. If bandwidth is a concern, gzip (already supported by `connection.py`) compresses this to ~5-8KB.

---

### Q5: `order=score_desc` — null handling for `cupping_score`?

The spec lists `order=score_desc` as a valid sort option. But since most roasts have `cupping_score = NULL` (see Q2), sorting by score is tricky.

**PostgreSQL behavior with `NULLS LAST`**: All NULL scores appear at the end, only cupped roasts are sorted by score.

**Options**:

- **(A)** Use `NULLS LAST` — null scores at the end (recommended, matches spec SQL hint line 191)
- **(B)** Treat NULL as 0 — null-scored roasts appear first when DESC
- **(C)** Filter out null-scored roasts entirely when `order=score_desc`
- **(D)** Other: ___________

#### Answer (ArtisanZ):

**Answer: (A) — Use `NULLS LAST`.**

Agreed with your recommendation. When sorting by `cupping_score DESC`, cupped roasts appear first (highest score → lowest score), uncupped roasts (`NULL`) appear at the end. This is intuitive — users see evaluated roasts first, unevaluated ones are still accessible but not prioritized.

---

## Implementation Preview (TasterMatrix side)

Once the above questions are answered, our implementation plan:

### Files to Change (7 files, ~340 lines, ~6 hours)

| File | Change |
|---|---|
| `migrations/0096_roast_records_list_index.sql` | New composite index `(org_id, user_id, roasted_at DESC)` for list query performance |
| `db/schema/roasting.ts` | Sync index declaration |
| `services/tm-artisanz/roast-query-service.ts` | **New** `listTmArtisanZRoasts()` + field extraction helper |
| `services/tm-artisanz/roast-sync-service.ts` | Expand `fetchTmArtisanZRoastForSync()` to include `raw_profile` + `raw_plus_payload` in response |
| `routes/tm-artisanz.ts` | New `GET /aroasts` handler |
| `schemas/tm-artisanz.ts` | New querystring schema + list response schema |
| `tests/tm-artisanz-roast-query.test.ts` | **New** test suite (reuses existing `roast-full-profile-request.json` fixture) |

### Core Query Template

```sql
SELECT
  r.raw_plus_payload->>'roast_id' AS roast_id,
  r.modified_at,
  r.raw_plus_payload->>'date' AS date,
  r.raw_plus_payload->>'label' AS label,
  r.raw_plus_payload->>'coffee' AS coffee,
  r.raw_profile->>'beans' AS coffee_label,          -- pending Q1 confirmation
  r.raw_plus_payload->>'machine' AS machine,
  (r.raw_plus_payload->>'amount')::numeric AS amount,
  (r.raw_plus_payload->>'end_weight')::numeric AS end_weight,
  (r.raw_plus_payload->>'drop_temp')::numeric AS drop_temp,
  (r.raw_plus_payload->>'FCs_temp')::numeric AS FCs_temp,
  (r.raw_plus_payload->>'FCs_time')::numeric AS FCs_time,
  (r.raw_plus_payload->>'DRY_temp')::numeric AS DRY_temp,
  (r.raw_plus_payload->>'DRY_time')::numeric AS DRY_time,
  (r.raw_plus_payload->>'DEV_time')::numeric AS DEV_time,
  (r.raw_plus_payload->>'DEV_ratio')::numeric AS DEV_ratio,
  r.cupping_score,
  r.whole_color,
  EXISTS(SELECT 1 FROM roasting.roast_curve_points
         WHERE roast_record_id = r.id) AS has_tm_profile
FROM roasting.roast_records r
WHERE r.org_id = $1::uuid
  AND r.source = 'artisanz'
  AND r.user_id = $2
  AND ($3::text IS NULL OR r.raw_plus_payload->>'coffee' = $3)
  AND ($4::timestamptz IS NULL OR r.roasted_at >= $4)
  AND ($5::timestamptz IS NULL OR r.roasted_at <= $5)
  AND ($6::text IS NULL OR r.raw_plus_payload->>'machine' = $6)
ORDER BY
  CASE WHEN $7 = 'date_asc' THEN r.roasted_at END ASC NULLS LAST,
  CASE WHEN $7 = 'score_desc' THEN r.cupping_score END DESC NULLS LAST,
  r.roasted_at DESC NULLS LAST
LIMIT $7 OFFSET $8;
```

### Security (inherits existing architecture)

- ✅ Auth: service-account token + scope `artisanz.roast.read` (existing)
- ✅ Tenant isolation: `WHERE org_id + user_id` double filter
- ✅ SQL injection: fully parameterized
- ✅ Rate limit: 120 req/min/token (service-account) + 200/min/IP (global)
- ✅ Schema validation: TypeBox querystring with `limit ≤ 100`, `format: date-time`
- ✅ Audit: rejected requests logged via existing `recordCotrixServiceAccountExternalRejectedAudit`
- ✅ No SSRF risk (GET endpoint makes no outbound calls)
- ✅ No quota consumption (basic feature for paid users — confirmed by TasterMatrix PM)

### Timeline

| Phase | Duration | Dependency |
|---|---|---|
| Implementation | 0.5-1 day | After Q1-Q5 answered |
| Testing | 0.5 day | After implementation |
| Code review + deploy | 0.5 day | After tests pass |
| **Total from confirmation** | **~2 days** | |

---

## Collaboration Mechanism

**For ArtisanZ team (also using OpenCode)**:

This file is the bridge between our two OpenCode sessions. Workflow:

1. **ArtisanZ team**: Open this file in your OpenCode session, edit the `### Answer (ArtisanZ):` blocks, save.
2. **TasterMatrix team**: We'll re-read this file after you signal completion (via commit message, email, or any channel you prefer).
3. **Iterations**: If our follow-up questions arise during implementation, we'll append new `## Follow-up Questions` sections at the bottom.

**Alternative channels** (if faster):
- Revise the original spec: `cotrix-server-aroasts-endpoint-spec.md`
- Send a diff/patch
- Schedule a sync call

---

## Open Follow-up Questions

*(TasterMatrix team adds new questions here as they arise during implementation)*

*(none yet)*

---

## Change Log

| Date | Author | Change |
|---|---|---|
| 2026-07-04 | TasterMatrix backend | Initial clarification document |
