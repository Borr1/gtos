"""B9 kill test #1 — does the broker ACTUALLY pay a credit, or is the positive `swap_long`
field a number that never becomes money?

Everything upstream of this file is a spec field. `symbol_info.swap_long > 0` is a *claim* about
what the broker will do. The only evidence that settles it is realized money: MT5's own
`history_deals_get`, where `swap` is what the account was actually credited or debited.

  positive `swap` in a deal record = the broker PAID the account
  negative `swap`                  = the broker CHARGED the account

If no deal in the record carries a positive swap, the whole credit is a fiction and the
clamp costs nothing. If positive swaps exist, and they exist on the sides the spec table
calls favourable, the credit is real money.

Sources (raw MT5 API pulls, read-only 2026-07-25 VPS export):
  09_mt5_api/ftmo_history_deals_get.jsonl        (`type` 0=BUY 1=SELL, `entry` 0=in 1=out)
  09_mt5_api/redacted_account_history_deals_get.jsonl

Writes B9_REALIZED_SWAP_V1.json.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
EXPORT = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")


def swap_table(fname: str) -> dict:
    out = {}
    for line in (EXPORT / fname).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "swap_long" in r:
            out[str(r.get("name"))] = (r.get("swap_long"), r.get("swap_short"))
    return out


def main() -> int:
    out = {"accounts": {}}
    for acct, deals_f, specs_f in (
        ("FTMO", "ftmo_history_deals_get.jsonl", "ftmo_symbols_get.jsonl"),
        ("redacted_account", "redacted_account_history_deals_get.jsonl", "redacted_account_symbols_get.jsonl"),
    ):
        tab = swap_table(specs_f)
        deals = [json.loads(l) for l in (EXPORT / deals_f).read_text().splitlines() if l.strip()]
        rows = [d for d in deals if d.get("symbol")]
        nz = [d for d in rows if float(d.get("swap") or 0.0) != 0.0]
        pos = [d for d in nz if float(d["swap"]) > 0]
        neg = [d for d in nz if float(d["swap"]) < 0]

        # A deal's `type` is the deal direction. On an EXIT deal (entry=1) the deal type is the
        # OPPOSITE of the position side: closing a LONG is a SELL. Swap is booked on the exit
        # deal, so position_side must be inverted there.
        def position_side(d):
            t = int(d.get("type", -1))
            e = int(d.get("entry", -1))
            if t not in (0, 1):
                return None
            if e == 1:
                return "SHORT" if t == 0 else "LONG"
            return "LONG" if t == 0 else "SHORT"

        by_ss = collections.defaultdict(lambda: {"n": 0, "swap_sum": 0.0, "n_pos": 0, "n_neg": 0})
        for d in nz:
            k = (d["symbol"], position_side(d))
            b = by_ss[k]
            b["n"] += 1
            b["swap_sum"] += float(d["swap"])
            b["n_pos"] += float(d["swap"]) > 0
            b["n_neg"] += float(d["swap"]) < 0

        # cross-check: does the SIGN of realized swap agree with the spec table's sign for that side?
        agree = disagree = untestable = 0
        detail = {}
        for (sym, side), b in sorted(by_ss.items(), key=lambda kv: str(kv[0])):
            spec = tab.get(sym)
            spec_val = None if spec is None or side is None else (spec[0] if side == "LONG" else spec[1])
            realized_sign = 1 if b["swap_sum"] > 0 else (-1 if b["swap_sum"] < 0 else 0)
            spec_sign = None if spec_val is None else (1 if float(spec_val) >= 0 else -1)
            ok = spec_sign is not None and spec_sign == realized_sign
            if spec_sign is None:
                untestable += 1
            elif ok:
                agree += 1
            else:
                disagree += 1
            detail[f"{sym}|{side}"] = {
                "n_nonzero_deals": b["n"],
                "realized_swap_sum_account_ccy": b["swap_sum"],
                "n_positive": b["n_pos"],
                "n_negative": b["n_neg"],
                "spec_swap_for_side_2026_07_25": spec_val,
                "spec_sign_matches_realized": ok,
            }

        out["accounts"][acct] = {
            "deals_total": len(deals),
            "deals_with_symbol": len(rows),
            "deals_nonzero_swap": len(nz),
            "deals_positive_swap": len(pos),
            "deals_negative_swap": len(neg),
            "positive_swap_total_account_ccy": sum(float(d["swap"]) for d in pos),
            "negative_swap_total_account_ccy": sum(float(d["swap"]) for d in neg),
            "positive_swap_symbols": sorted({d["symbol"] for d in pos}),
            "sign_crosscheck": {"agree": agree, "disagree": disagree, "untestable": untestable},
            "by_symbol_side": detail,
            "positive_deals": [
                {k: d.get(k) for k in ("symbol", "type", "entry", "swap", "volume", "time", "ticket")}
                for d in pos
            ],
        }

    (HERE / "B9_REALIZED_SWAP_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    for acct, v in out["accounts"].items():
        print(f"\n=== {acct} ===")
        print(f"  deals {v['deals_total']}  nonzero swap {v['deals_nonzero_swap']}"
              f"  POSITIVE {v['deals_positive_swap']}  negative {v['deals_negative_swap']}")
        print(f"  credited total {v['positive_swap_total_account_ccy']:+.2f}"
              f"   charged total {v['negative_swap_total_account_ccy']:+.2f}")
        print(f"  symbols ever credited: {v['positive_swap_symbols']}")
        cc = v["sign_crosscheck"]
        print(f"  spec-sign vs realized-sign: agree {cc['agree']}  DISAGREE {cc['disagree']}  untestable {cc['untestable']}")
        for k, r in v["by_symbol_side"].items():
            flag = "" if r["spec_sign_matches_realized"] else "   <-- MISMATCH"
            print(f"    {k:<22} n={r['n_nonzero_deals']:<3} realized {r['realized_swap_sum_account_ccy']:>+10.2f}"
                  f"  spec {str(r['spec_swap_for_side_2026_07_25']):>12}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
