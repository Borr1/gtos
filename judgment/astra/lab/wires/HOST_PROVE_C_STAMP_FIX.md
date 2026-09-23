# HOST PROVE-C STAMP FIX — F5 scaler, not splice order

Chair evidence `PROVE_C_STAMP_EVIDENCE_20260918.md`. Do **not** chase
haircut-after-`_UnitView`. Host splice is already haircut → headroom →
`_UnitView` → `place` (`book_owner` ~L4252–4285).

## Root cause

`haircut_challenge_unit` moved `risk_pct` (ticket **293611741**,
`dsp_shakeout_holds_run_lows`, ~2026-09-18T01:45:50Z):

- `combined_live_tilt` **0.7467** = flow 0.8485 × cost 0.88
- receipt before≠after on `risk_pct_per_trade`

Then host `execution.open_trade` `MinimalSizeScaler.scaled_risk_amount`
**replaced** dollar risk with hard `target_risk_usd` **$150** and stamped
`f5_intended_risk_usd=150`. Lots **0.35** match the unhaircutted $150
XAU class. Expected intended: `150 × 0.7467 = $112.005`.

## What Chair lands (Challenge f5-live only)

1. Copy `src/judgment/apply_size.py` (and the rest of `src/judgment/` if
   not already current).
2. **Patch host `MinimalSizeScaler.scaled_risk_amount`** — do not add a
   second scaler call, do not wholesale-copy GitHub `execution.py` /
   `book_owner.py`:

```python
from src.judgment.apply_size import honor_f5_scaler_risk

def scaled_risk_amount(self, nominal, trade_params=None):
    honored, _stamp = honor_f5_scaler_risk(
        nominal,
        scaler=self,
        trade_params=trade_params,
        login=getattr(self, "login", None),  # or mt5 login from open_trade
        ns=getattr(self, "ns", None) or "operator",
    )
    return honored
```

Keep the existing `open_trade` stamp from `scaler.last` /
`_f5_last["f5_intended_risk_usd"]`. `honor_f5_scaler_risk` writes `last`.

3. If host `open_trade` still does `risk_amount = self._f5_scaler.scaled_risk_amount(...)`
   then the patch above is enough. GitHub `execution.py` has the same hook
   gated on `_f5_scaler is not None` (W7: no-op).
4. Env unchanged: `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_APPLY_LIVE=1`
   `GTOS_JEV_A1_LOG=1`. TypeSafe fp `00000000`.
5. Restart **only** `GTOS_F5_FTMO`. No remint. No flatten. No place from Jev.

Challenge gate unchanged: APPLY_LIVE + login `0` / ns
`operator`. Leave-orig `293332188` stays $150. W7 / no scaler
stays untouched.

## Prove C on the next tilted place

1. `JEV_APPLY receipt` before≠after `risk_pct_per_trade` (already true).
2. Trade record `instrumentation.f5_intended_risk_usd` **≠ 150**.
   Tilt `0.7467` → **~$112**. Tilt `0.70` → **$105**.
3. Lots move with the new intended (not the 0.35 / $150 class).
4. Receipt still written.

Envelope walls stay integers. No NEWS_PROTOCOL. No world-news work.
