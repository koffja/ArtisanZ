# Cotrix Server API: Roast List Endpoint Specification

> **For**: Cotrix/tastermatrix.com backend development team
> **From**: ArtisanZ client team
> **Date**: 2026-07-04
> **Priority**: Medium — enables historical roast comparison feature in ArtisanZ

## Overview

ArtisanZ needs a server-side endpoint to **list and search historical roasts** by criteria (coffee bean, date range, machine). Currently the API only supports `GET /aroast/{uuid}` (single roast by UUID), which requires the client to already know the UUID. A list/search endpoint is needed for the "Compare Historical Roasts" feature.

## Current State

| Endpoint | Method | Purpose | Limitation |
|---|---|---|---|
| `/api/tm-artisanz/v1/aroast/{uuid}` | GET | Fetch single roast by UUID | Must know UUID in advance |
| `/api/tm-artisanz/v1/aroast` | POST | Upload/update roast | Write-only |
| `/api/tm-artisanz/v1/acoffees?today=&lsrt=` | GET | List coffee stock | ✅ Precedent for list endpoint |
| `/api/tm-artisanz/v1/notifications?machine=` | GET | List notifications | ✅ Precedent for list endpoint |

**Missing**: `GET /api/tm-artisanz/v1/aroasts` (plural) — list/search roasts by criteria.

## Requested Endpoint

### `GET /api/tm-artisanz/v1/aroasts`

List roasts for the authenticated user, optionally filtered by criteria.

#### Authentication

Same as all other endpoints: `Authorization: Bearer <token>` header.

#### Query Parameters

All parameters are optional. Without parameters, returns most recent roasts.

| Parameter | Type | Description | Example |
|---|---|---|---|
| `coffee` | string | Filter by coffee bean hr_id | `coffee=eth_yirgacheffe_2024` |
| `from` | string (ISO 8601) | Start date (inclusive) | `from=2026-01-01T00:00:00Z` |
| `to` | string (ISO 8601) | End date (inclusive) | `to=2026-07-04T23:59:59Z` |
| `machine` | string | Filter by machine name | `machine=AillioBulletR1` |
| `limit` | integer | Max results (default: 20, max: 100) | `limit=15` |
| `offset` | integer | Pagination offset (default: 0) | `offset=20` |
| `order` | string | Sort order: `date_desc` (default), `date_asc`, `score_desc` | `order=date_desc` |

#### Example Request

```
GET /api/tm-artisanz/v1/aroasts?coffee=eth_yirgacheffe_2024&from=2026-06-01T00:00:00Z&to=2026-07-04T23:59:59Z&limit=15
Authorization: Bearer <token>
Accept: application/json
```

#### Response Format

Follow the existing `{success, result}` pattern used by `/acoffees` and `/notifications`.

**200 OK:**

```json
{
  "success": true,
  "result": [
    {
      "roast_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "modified_at": "2026-07-03T14:30:00.000Z",
      "date": "2026-07-03T14:20:00.000Z",
      "label": "Yirgacheffe #47",
      "coffee": "eth_yirgacheffe_2024",
      "coffee_label": "Ethiopia Yirgacheffe 2024",
      "machine": "AillioBulletR1",
      "amount": 0.8,
      "end_weight": 0.72,
      "drop_temp": 205,
      "FCs_temp": 198,
      "FCs_time": 510,
      "DRY_temp": 160,
      "DRY_time": 295,
      "DEV_time": 180,
      "DEV_ratio": 20.5,
      "cupping_score": 86.5,
      "whole_color": 62,
      "has_tm_profile": true
    },
    {
      "roast_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "modified_at": "2026-07-02T10:15:00.000Z",
      "date": "2026-07-02T10:05:00.000Z",
      "label": "Yirgacheffe #46",
      "coffee": "eth_yirgacheffe_2024",
      "coffee_label": "Ethiopia Yirgacheffe 2024",
      "machine": "AillioBulletR1",
      "amount": 0.8,
      "end_weight": 0.71,
      "drop_temp": 204,
      "FCs_temp": 196,
      "FCs_time": 495,
      "DRY_temp": 158,
      "DRY_time": 280,
      "DEV_time": 195,
      "DEV_ratio": 22.1,
      "cupping_score": 85.0,
      "whole_color": 63,
      "has_tm_profile": false
    }
  ],
  "total": 47,
  "limit": 15,
  "offset": 0
}
```

**Fields per roast item (minimal list view):**

| Field | Type | Description |
|---|---|---|
| `roast_id` | string (UUID) | Primary key — used for `GET /aroast/{uuid}` to fetch full data |
| `modified_at` | string (ISO 8601) | Last modification timestamp |
| `date` | string (ISO 8601) | Roast date |
| `label` | string | User-defined roast label |
| `coffee` | string \| null | Coffee bean hr_id |
| `coffee_label` | string \| null | Human-readable coffee name (join from coffee table) |
| `machine` | string | Machine name |
| `amount` | float | Charge weight (kg) |
| `end_weight` | float | End weight (kg) |
| `drop_temp` | int | Drop temperature |
| `FCs_temp` | int | First crack start temperature |
| `FCs_time` | int | First crack start time (seconds from CHARGE) |
| `DRY_temp` | int | DRY end temperature |
| `DRY_time` | int | DRY end time (seconds from CHARGE) |
| `DEV_time` | int | Development time (seconds) |
| `DEV_ratio` | float | Development ratio (%) |
| `cupping_score` | float \| null | Cupping score |
| `whole_color` | int \| null | Whole bean color reading |
| `has_tm_profile` | bool | Whether full time-series data (`tm_profile`) is available for this roast |

**Note:** `has_tm_profile` tells the client whether the full curve data is available. If `true`, the client can call `GET /aroast/{roast_id}` to get the complete `tm_profile` (timex/temp1/temp2 arrays) for curve overlay.

**401 Unauthorized:** Token expired or invalid (same as existing endpoints).

**403 Forbidden:** User does not own these roasts.

**500 Internal Server Error:** `{success: false, error: "message"}`

#### Pagination Response Fields

| Field | Type | Description |
|---|---|---|
| `total` | int | Total matching roasts (before pagination) |
| `limit` | int | Applied limit |
| `offset` | int | Applied offset |

## Database Query Hints

Based on the existing sync record structure in `plus/roast.py`:

```sql
-- The roasts table likely already has these columns from the sync record
-- (sync_record_attributes in roast.py:446-526)

SELECT
    r.roast_id,
    r.modified_at,
    r.date,
    r.label,
    r.coffee,           -- hr_id
    c.label AS coffee_label,  -- join with coffees table
    r.machine,
    r.amount,
    r.end_weight,
    r.drop_temp,
    r.FCs_temp,
    r.FCs_time,
    r.DRY_temp,
    r.DRY_time,
    r.DEV_time,
    r.DEV_ratio,
    r.cupping_score,
    r.whole_color,
    EXISTS(SELECT 1 FROM roast_profiles WHERE roast_id = r.roast_id) AS has_tm_profile
FROM roasts r
LEFT JOIN coffees c ON r.coffee = c.hr_id
WHERE r.user_id = :authenticated_user_id
    AND (:coffee IS NULL OR r.coffee = :coffee)
    AND (:from IS NULL OR r.date >= :from)
    AND (:to IS NULL OR r.date <= :to)
    AND (:machine IS NULL OR r.machine = :machine)
ORDER BY
    CASE WHEN :order = 'date_asc' THEN r.date END ASC,
    CASE WHEN :order = 'score_desc' THEN r.cupping_score END DESC NULLS LAST,
    r.date DESC  -- default
LIMIT :limit OFFSET :offset;

-- Also return COUNT(*) for total
```

**Existing indexes to leverage:**
- `s_item_date` (already noted in `roast.py:142` as "added to speed up search on server side")
- `coffee` (hr_id, likely indexed for stock queries)
- `user_id` (all queries are user-scoped)

## Client-Side Integration (ArtisanZ)

Once the endpoint is live, the client will add this function to `plus/roast.py`:

```python
def query_roasts(
    coffee: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    machine: str | None = None,
    limit: int = 15,
    offset: int = 0,
) -> list[dict[str, Any]] | None:
    """Query historical roasts from Cotrix server.

    Returns list of roast summary dicts, or None on error.
    Each dict has roast_id, label, date, coffee_label, etc.
    """
    import plus.config as config
    import plus.connection as connection

    params: dict[str, Any] = {'limit': limit, 'offset': offset}
    if coffee:
        params['coffee'] = coffee
    if date_from:
        params['from'] = date_from
    if date_to:
        params['to'] = date_to
    if machine:
        params['machine'] = machine

    try:
        url = config.endpoint('aroasts')
        res = connection.getData(url, authorized=True, params=params)
        if res and res.get('success'):
            return res.get('result', [])
    except Exception:
        pass
    return None
```

And the ComparisonOverlay dialog will gain a "Cloud Search" tab that calls this function and displays results for selection.

## Security Considerations

1. **User isolation**: All queries MUST be scoped to `user_id = authenticated_user`. Never trust a client-provided user_id.
2. **Rate limiting**: Apply standard rate limits (same as `/notifications`).
3. **Input validation**: Validate ISO 8601 date format for `from`/`to`. Validate `limit` ≤ 100.
4. **SQL injection**: Use parameterized queries (same as existing endpoints).
5. **No PII in response**: The response contains roast metadata only — no user email, password, or account info.

## Testing Checklist

- [ ] Returns 200 with list for authenticated user with roasts
- [ ] Returns 200 with empty `result: []` for user with no roasts
- [ ] `coffee` filter narrows results correctly
- [ ] `from`/`to` date range filter works
- [ ] `limit` caps results, `total` reflects unfiltered count
- [ ] `offset` paginates correctly
- [ ] 401 when no/invalid token
- [ ] User A cannot see User B's roasts
- [ ] `has_tm_profile` correctly reflects tm_profile table presence

## Priority

Medium. The ArtisanZ client already has local file comparison working. This endpoint enables **cloud-based** comparison (search any past roast from any device), which is a significant UX improvement for multi-device users.
