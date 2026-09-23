"""B9 step 6b — differential proof that the default path is bit-identical to `origin/main`.

The unit tests pin behaviour on hand-built fixtures. This runs the REAL grid: every FTMO and
redacted_account instrument in the broker-truth artifact, both sides, four stop distances, three
holding horizons and three entry instants (a weekday, a Friday, and the triple-swap weekday), both
against `origin/main`'s bytes and against the B9 change, and compares **every key the old version
emitted**. A single difference on any of them fails.

`origin/main` is loaded by path as a second module object so the two implementations run in the
same process against the same inputs. Its imports (`rollover_nights`,
`commission_usd_per_lot_for_packet`) resolve to `src/costs/model.py`, whose default path B9 also
leaves unchanged -- so the comparison is of the cost engine, with the model held fixed.

Writes B9_BIT_IDENTITY_V1.json.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))

BTC = REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
SERVERS = {"FTMO": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}
ENTRIES = (
    "2026-07-01T10:00:00+00:00",  # Wednesday
    "2026-07-03T20:00:00+00:00",  # Friday, crosses the weekend
    "2026-06-17T09:00:00+00:00",  # Wednesday = MT5 dow 3, the common triple-swap weekday
)
STOPS = (0.05, 0.938, 12.5, 400.0)
HOLD_DAYS = (0.2, 1.0, 13.4)


def load_origin_main():
    src = subprocess.run(
        ["git", "show", "origin/main:src/components/broker_net_cost_engine.py"],
        cwd=REPO, capture_output=True, check=True,
    ).stdout
    tmp = pathlib.Path(tempfile.mkdtemp()) / "bnce_origin_main.py"
    tmp.write_bytes(src)
    spec = importlib.util.spec_from_file_location("bnce_origin_main", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    import src.components.broker_net_cost_engine as new  # the B9 tree

    old = load_origin_main()
    d = json.loads(BTC.read_text())

    cases = 0
    mismatches = []
    keys_old_total: set[str] = set()
    for acct, server in SERVERS.items():
        for sym, rec in d["accounts"][acct]["instruments"].items():
            spec_fields = dict(rec.get("spec") or {})
            price = (rec.get("spread_price") or {}).get("mid_price_median")
            packet_spec = {"fields": spec_fields}
            for side_field, sl, hold, entry in itertools.product(
                ("swap_long", "swap_short"), STOPS, HOLD_DAYS, ENTRIES
            ):
                swap = spec_fields.get(side_field)
                cfg = {
                    "selected_cell_swap_cost_default_hold_days": hold,
                    "selected_cell_swap_interest_days_per_year": 360,
                }
                kw = dict(
                    runtime_cfg=cfg, trade_params={}, spec=packet_spec, swap_value=swap,
                    entry_price=price, sl_distance=sl, entry_utc=entry, server=server,
                )
                a = old._swap_cost_packet(**kw)
                b = new._swap_cost_packet(**kw)
                cases += 1
                keys_old_total |= set(a)
                for k, v in a.items():
                    if b.get(k) != v:
                        mismatches.append(
                            {"account": acct, "symbol": sym, "side_field": side_field,
                             "sl_distance": sl, "hold_days": hold, "entry_utc": entry,
                             "key": k, "origin_main": v, "b9": b.get(k)}
                        )
    new_keys = sorted(set(new._swap_cost_packet(
        runtime_cfg={"selected_cell_swap_cost_default_hold_days": 1.0}, trade_params={},
        spec={"fields": {"swap_mode": 1.0, "point": 0.001}}, swap_value=1.0,
        entry_price=76.0, sl_distance=1.0, entry_utc=ENTRIES[0], server=SERVERS["FTMO"],
    )) - keys_old_total)

    out = {
        "what": ("every key `origin/main`'s _swap_cost_packet emits, compared value-for-value "
                 "against the B9 tree over the full broker-truth instrument grid"),
        "cases": cases,
        "keys_compared_per_case": len(keys_old_total),
        "mismatches": len(mismatches),
        "mismatch_detail": mismatches[:50],
        "keys_added_by_b9": new_keys,
        "grid": {"accounts": list(SERVERS), "sides": 2, "stops": list(STOPS),
                 "hold_days": list(HOLD_DAYS), "entries": list(ENTRIES)},
        "verdict": ("BIT-IDENTICAL on every pre-existing key" if not mismatches
                    else "DIFFERENCES FOUND -- see mismatch_detail"),
    }
    (HERE / "B9_BIT_IDENTITY_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"cases {cases}  keys/case {len(keys_old_total)}  mismatches {len(mismatches)}")
    print("keys added by B9:", new_keys)
    print(out["verdict"])
    for m in mismatches[:10]:
        print("  ", m)
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
