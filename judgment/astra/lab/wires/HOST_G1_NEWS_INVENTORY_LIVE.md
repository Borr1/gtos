# HOST G1 — news inventory on live A1 + haircut

Scout G1. Wire the **existing** `news_inventory_at` reader into Challenge
live observe / compose. Do **not** invent `NEWS_PROTOCOL`. Do **not**
implement G2 (writer `READ`) or G3 (prompt rewrite). Never place / remint
/ flatten.

Shadow `challenge_shadow.py` already did
`extra.update(news_inventory_at(host_events, as_of))` then
`compose_shadow(..., extra=extra)`. Live A1 did not:

- `maybe_observe_ub_plc_017` / `maybe_observe_fluid_at_place` extras were
  cost_skip / spread only
- `observe` / `observe_fluid_inventory` called `compose_shadow` **without**
  `extra=`
- `haircut_challenge_unit` called `compose_shadow(..., ticket=ticket)` with
  no extra

So `_calendar_honest` never saw `host_news_source` /
`host_news_inventory_status` on the live fire path. JSON-axis covering
stayed true even while the host writer stamped `NOT_READ`.

## What Chair copies

1. Copy `src/judgment/` (especially `host_events.py`, `a1_log.py`,
   `apply_size.py`). Keep the existing splice — do **not** wholesale-copy
   GitHub `book_owner.py` onto the ~10069-line dirty host.
2. Point live at the Challenge host writer tape **when present**:

```
GTOS_JEV_HOST_EVENTS=host-local\redacted_host\repo\shadow_logs\f5_minimal\operator\events.jsonl
```

If that file already sits at repo-relative
`shadow_logs/f5_minimal/operator/events.jsonl`, env is optional.
Lab `judgment/astra/lab/challenge_shadow_20260917/events_since_20260915.jsonl`
stays the **shadow / research** default. Live never falls back to it.

3. Env otherwise unchanged: `GTOS_JEV_ALIVE_SHADOW=1`
   `GTOS_JEV_APPLY_LIVE=1` `GTOS_JEV_A1_LOG=1`. TypeSafe fp `00000000`.
4. Restart **only** `GTOS_F5_FTMO`. No remint. No flatten. No place from Jev.

## What live now stamps

Same five fields shadow already used:

| Field | Writer present + unread | No writer row |
|---|---|---|
| `host_news_source` | `challenge_host_news_writer` | `unassembled` |
| `host_news_inventory_status` | `NOT_READ` / `UNKNOWN` / `None` | `None` |
| `calendar_honest` (FLUID-ADM-009) | **false** | JSON-axis fallback (unchanged) |

This tape: writer is emitting and **never `READ`**. G1 makes that fact
visible on live A1 / haircut compose. `calendar_honest=true` still needs
G2 (host writer actually reads the 13-event spine). Do not invert
`spine_empty`.

Physical lots stay **flow × cost**. This is a LABEL. Envelope walls stay
integers. SEL-V4-002 stays research-only.
