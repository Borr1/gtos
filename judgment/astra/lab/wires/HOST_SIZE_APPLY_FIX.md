# HOST SIZE APPLY FIX — prove C on next Challenge place

Host dig `HOST_SIZE_APPLY_PROOF_20260917.md` = verdict **B**.
APPLY_LIVE was armed; `_scale_unit` never touched `risk_pct_per_trade`.
Tickets 293437038 / 293435759 stayed `$150` intended while A1 cost tilt was ~0.815.

This commit fixes the unit shape in `src/judgment/apply_size.py`. Chair copies
`src/judgment/` onto Challenge f5-live. Do **not** wholesale-copy GitHub
`book_owner.py` onto the 10069-line dirty host — splice `haircut_challenge_unit`.

## What changed

- `_scale_unit` / `maybe_haircut_unit` scale **`risk_pct_per_trade` and `unit_risk_pct`**
  (plus lots keys when present). Same keys AI companion already mutates.
- One-line `JEV_APPLY receipt` + `judgment/astra/lab/a1/apply_receipt.jsonl`
  (`unit_before`, `combined_live_tilt`, `unit_after`, symbol/sleeve/ticket). No secrets.
- `haircut_challenge_unit` composes with Jev `answers` (POST when a key is present).
- `_jev_noul` accepts continuous TypeSafe noul; cost tilt maps `[0,1]` → `[1.00, 0.70]`.
- GitHub `book_owner.py` splice now calls `haircut_challenge_unit` (reference only).
- Challenge gate unchanged: `GTOS_JEV_APPLY_LIVE` + login `0` / ns `operator`.
- Leave-orig `293332188` stays 1.0. Envelope walls stay integers. Never place/remint/flatten.

## Host land (Challenge f5-live only)

1. Copy `src/judgment/` (especially `apply_size.py`, `compose.py`, `a1_log.py`).
2. Replace host `compose_shadow(state, None)` + `maybe_haircut_unit` with:

```python
from src.judgment.apply_size import haircut_challenge_unit
adjusted_unit = haircut_challenge_unit(
    adjusted_unit,
    intent=intent,
    tick=tick,
    login=<mt5 login>,
    ns=self._namespace,   # must be operator
    already_admitted=True,
    evaluate_jev=True,
)
```

If you keep the old two-call splice, **still copy `apply_size.py`** — `maybe_haircut_unit`
now scales risk_pct even when compose is built locally. Prefer the helper so answers merge.
3. Env unchanged: `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1` `GTOS_JEV_A1_LOG=1`.
4. Do not set APPLY_LIVE on W7 / `run_book.py`. Confirm TypeSafe fp `00000000`.
5. Restart **only** `GTOS_F5_FTMO`. No remint. No flatten.

## Prove C on the next live place

C = hard before≠after on the F5 unit / intended risk. Not another A1 tilt row.

Baseline on this book is **$150** intended when `risk_pct_per_trade = 0.0015`
and equity ~$100k (`risk_usd = risk_pct_per_trade * equity`).

On the next `cost_skip is None` place with `combined_live_tilt ≠ 1.0`:

1. Writer log contains `JEV_APPLY receipt` with `before.risk_pct_per_trade ≠ after.risk_pct_per_trade`.
2. `apply_receipt.jsonl` last row: same snapshot, symbol/sleeve named.
3. Trade record / Telegram `f5_intended_risk_usd` (or host `risk_usd`) **≠ $150**.
   Example: tilt `0.8152` → intended ≈ `$122` (`150 * 0.8152`). Tilt `0.70` → `$105`.
4. Lots may also move (broker grid); **intended risk is the authority**, not fill lots.
5. Leave-orig / W7 ns / APPLY_LIVE off → receipt absent and risk stays baseline.

If intended stays $150 and receipt is missing, the host splice was not restarted
on the new `apply_size.py`. If receipt shows after≠before but intended is $150,
the host still sizes from a copy taken *before* haircut — splice order is wrong
(haircut must run after `adjusted_unit`, before `_UnitView` / `router.place`).

## Not C if

- Tilt is 1.0 (spread ordinary + no Jev hurt) — wait for a cost-complete row.
- Ticket is 293332188 (closed leave-orig; lock stays).
- APPLY_LIVE landed on W7.

Chair lands. No NEWS_PROTOCOL. No place from this seat.
