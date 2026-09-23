"""B9 step 2b — every sleeve with a favourable-carry credit, per account, and whether any carry
tier moves.

The sleeve-level unit is deliberately **credit / charge**, not an absolute R. Both terms come from
the same trades, the same stops and the same swap table, so the ratio needs no population bridge to
`SURVIVOR_BOOK_V1.json` — which is a different population (162 rows vs the walk's 67 for
`energy_agri`) and would otherwise be mixed silently. The artifact's own `break_even_nights` then
restates as

    BE_restated = BE_published / (1 - credit/charge)

because the break-even is (edge / swap-per-night) and the credit reduces the denominator by exactly
that fraction. A tier moves only if `BE_restated` crosses the sleeve's own `horizon_mean_nights`.

Writes B9_SLEEVE_RESTATEMENT_V1.json.
"""
from __future__ import annotations

import gzip
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
EXPORT = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")
SB = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
VERIFIED = (REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
                   "VERIFIED_BROKER_SYMBOL_SPECS.json")
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")


def table(fname: str, account_key: str) -> dict:
    out = {}
    for line in (EXPORT / fname).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "swap_long" not in r:
            continue
        rec = {"swap_long": r["swap_long"], "swap_short": r.get("swap_short"),
               "swap_mode": r.get("swap_mode"), "point": r.get("point")}
        n = str(r.get("name"))
        out[n] = out[n.replace(".", "_")] = rec
    v = json.loads(VERIFIED.read_text())
    for canon, rec in (v.get("symbols") or {}).items():
        native = rec.get(f"{account_key}_native")
        if native in out:
            out.setdefault(canon, out[native])
    return out


def per_night(rec, direction, price):
    """(magnitude per night in price units, favourable?) or (None, None)."""
    swap = rec.get("swap_long") if direction > 0 else rec.get("swap_short")
    mode = rec.get("swap_mode")
    if swap is None or mode is None:
        return None, None
    mode = int(float(mode))
    if mode == 1:
        pt = rec.get("point")
        return (abs(float(swap)) * float(pt), float(swap) >= 0) if pt else (None, None)
    if mode in (5, 6) and price:
        return float(price) * (abs(float(swap)) / 100.0) / 360.0, float(swap) >= 0
    return None, None


def main() -> int:
    sb = json.loads(SB.read_text())
    est = json.loads(gzip.open(ESTATE, "rt").read())
    tabs = {"FTMO": table("ftmo_symbols_get.jsonl", "ftmo"),
            "redacted_account": table("redacted_account_symbols_get.jsonl", "redacted_account")}

    out = {
        "basis": {
            "swap_table": "vps-export-20260725 symbols_get (2026-07-25), the most recent read",
            "trades": str(ESTATE),
            "published": str(SB),
            "formula": "BE_restated = BE_published / (1 - credit/charge)",
            "tier_rule": "a tier moves iff BE_restated crosses horizon_mean_nights",
        },
        "accounts": {},
        "tier_moves": [],
    }
    for acct, tab in tabs.items():
        rows = {}
        for sleeve, pub in sb["accounts"][acct]["sleeves"].items():
            cred = chg = 0.0
            n = 0
            for t in est["trades"].get(sleeve, []):
                rec = tab.get(t.get("symbol_canonical")) or tab.get(t.get("symbol"))
                sld = t.get("sl_distance_price")
                if not rec or not sld:
                    continue
                mag, fav = per_night(rec, int(t.get("direction", 0)), t.get("entry_price"))
                if mag is None:
                    continue
                n += 1
                if fav:
                    cred += mag / float(sld)
                else:
                    chg += mag / float(sld)
            if not n or chg <= 0:
                continue
            ratio = cred / chg
            be, hz, mx = pub.get("break_even_nights"), pub.get("horizon_mean_nights"), pub.get("max_nights")
            be2 = be / (1 - ratio) if (be is not None and ratio < 1) else None
            moved = None
            if be is not None and be2 is not None and hz is not None:
                moved = (be >= hz) != (be2 >= hz)
                if moved:
                    out["tier_moves"].append({"account": acct, "sleeve": sleeve,
                                              "from": pub.get("survivor_tier")})
            rows[sleeve] = {
                "n_trades_priced": n,
                "armed_2026_08_11": sleeve in ARMED,
                "survivor_tier_published": pub.get("survivor_tier"),
                "credit_over_charge": ratio,
                "credit_r_per_trade_total": cred,
                "charge_r_per_trade_total": chg,
                "break_even_nights_published": be,
                "break_even_nights_restated": be2,
                "horizon_mean_nights": hz,
                "max_nights": mx,
                "tier_moves": moved,
                "gap_to_horizon_closed_pct": (
                    None if (be is None or be2 is None or hz is None or hz == be)
                    else 100.0 * (be2 - be) / (hz - be)
                ),
            }
        out["accounts"][acct] = rows

    (HERE / "B9_SLEEVE_RESTATEMENT_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    print(f"{'account':<11}{'sleeve':<20}{'tier':<34}{'cred/chg':>9}{'BE pub':>9}{'BE restated':>13}"
          f"{'horizon':>9}{'tier moves':>12}")
    for acct, rows in out["accounts"].items():
        for s, v in sorted(rows.items(), key=lambda kv: -kv[1]["credit_over_charge"]):
            if v["credit_over_charge"] <= 0:
                continue
            be = v["break_even_nights_published"]
            be2 = v["break_even_nights_restated"]
            hz = v["horizon_mean_nights"]
            print(
                f"{acct:<11}{s:<20}{str(v['survivor_tier_published']):<34}"
                f"{100 * v['credit_over_charge']:>8.1f}%"
                f"{('%.2f' % be if be is not None else 'n/a'):>9}"
                f"{('%.2f' % be2 if be2 is not None else 'n/a'):>13}"
                f"{('%.2f' % hz if hz is not None else 'n/a'):>9}"
                f"{('YES' if v['tier_moves'] else 'no'):>12}"
                f"{'  *ARMED*' if v['armed_2026_08_11'] else ''}"
            )
    print(f"\ntier moves across both accounts: {len(out['tier_moves'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
