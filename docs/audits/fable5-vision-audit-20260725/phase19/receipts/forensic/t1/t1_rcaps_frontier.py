#!/usr/bin/env python3
"""R-CAPS formal F(c)-A(c) frontier derivation (REPAIR_SET_SPEC §6), both variants.

Run from the fa2-integration worktree. Pool = January diagnostic pool at truthed costs
(spread_model band=mid + frozen commission/swap + flat 0.02 slippage). Current rule =
spread_r<=0.10 AND total<=0.15. Train = Jan days 1-21, holdout = 22-31 (declared).
Variant A: dial-exact (total-only ceiling). Variant B: ratio-companion (spread<=2/3*c).
Output: the tables committed in CELL_DECLARATION_V1.md. DEVELOPMENT-FITTED, billed:false.
"""
import gzip, json, math, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803")
from src.costs.spread_model import spread_price  # noqa: E402

ROOT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
POOL = ROOT / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
CELLS = [0.05, 0.10, 0.25, 0.50, 1.00]
CUR_SPREAD, CUR_TOTAL, SLIP = 0.10, 0.15, 0.02


def main():
    cache = {}
    def sp(sym, iso):
        dt = datetime.fromisoformat(iso)
        k = (sym, dt.strftime("%H"))
        if k not in cache:
            cache[k] = spread_price(sym, "FTMO", dt, band="mid").spread_price
        return cache[k]
    rows = []
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            e, s = float(r["entry_price"]), float(r["stop_loss"])
            bd = abs(e - s)
            if not math.isfinite(bd) or bd <= 0:
                continue
            day = int(r["decision_time_utc"][8:10])
            spr_t = sp(r["symbol"], r["decision_time_utc"]) / bd
            cost_t = (float(r.get("commission_r") or 0) + float(r.get("swap_cost_r") or 0)
                      + SLIP + spr_t)
            gross = float(r["opportunity_net_proxy_r"]) + float(r["cost_r"])
            rows.append((day, spr_t, cost_t, gross - cost_t))
    for variant, admit in (("dial-exact (total only)", lambda st, ct, c: ct <= c),
                           ("ratio-companion", lambda st, ct, c: ct <= c and st <= (CUR_SPREAD / CUR_TOTAL) * c)):
        print(f"\n{variant}:")
        print(f'{"cell":>6} | {"split":>7} | {"F":>9} | {"A":>9} | {"F+A":>9}')
        for cell in CELLS:
            for split in ("train", "holdout"):
                F = A = 0.0
                for day, spr_t, cost_t, net_t in rows:
                    if (split == "train") != (day <= 21):
                        continue
                    cur_ok = spr_t <= CUR_SPREAD and cost_t <= CUR_TOTAL
                    new_ok = admit(spr_t, cost_t, cell)
                    if not cur_ok and new_ok:
                        if net_t > 0: F += net_t
                        else: A += net_t
                    elif cur_ok and not new_ok:
                        if net_t > 0: F -= net_t
                        else: A -= net_t
                print(f"{cell:>6} | {split:>7} | {F:>9.1f} | {A:>9.1f} | {F+A:>9.1f}")


if __name__ == "__main__":
    main()
