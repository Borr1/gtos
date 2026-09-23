"""B9 step 5a — the swap time series that Lane 5 said did not exist.

Lane 5 §2.3(v): *"there is no swap time series anywhere on this machine"* and therefore
*"the swap snapshot is a single point in time applied to years of history"* is the binding
blocker. That is refutable: the machine holds **four** independent captures of the same
broker's `symbol_info` swap fields at three distinct instants, and they disagree materially.

Captures reconciled here (each is an independent read of MT5 `symbol_info`, not a copy):

  2026-06-02  research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/
              FTMO_SYMBOL_SPEC_LEDGER.jsonl                      (FTMO only, 24 symbols)
  2026-06-02  config/profiles/operator_profile.yaml         (generated_at_utc 2026-06-01T18:01Z)
              config/profiles/redacted_account.yaml                     -- the RESEARCH cost table
  2026-06-10  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
              VERIFIED_BROKER_SYMBOL_SPECS.json                   (both accounts)
  2026-07-25  /Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/
              {ftmo,redacted_account}_symbols_get.jsonl                 -- the source behind
              BROKER_TRUE_COSTS_V1.json, i.e. the `src/costs/model.py` cost table

Writes B9_SWAP_PERSISTENCE_V1.json.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
EXPORT = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")


def from_profile(rel: str) -> dict:
    d = yaml.safe_load((REPO / rel).read_text())
    out = {}
    for sym, v in (d.get("instruments") or {}).items():
        m = (v or {}).get("market") or {}
        if "swap_long" in m:
            out[str(m.get("mt5_symbol") or sym)] = {
                "gtos_symbol": sym,
                "swap_long": m.get("swap_long"),
                "swap_short": m.get("swap_short"),
                "swap_mode": m.get("swap_mode"),
                "point": m.get("point"),
            }
    return out


def from_spec_ledger(rel: str) -> dict:
    out = {}
    for line in (REPO / rel).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = str(r.get("mt5_symbol") or r.get("name"))
        if "swap_long" not in r:
            continue
        out[key] = {
            "gtos_symbol": r.get("name"),
            "swap_long": r.get("swap_long"),
            "swap_short": r.get("swap_short"),
            "swap_mode": r.get("swap_mode"),
            "point": r.get("point"),
        }
    return out


def from_verified_specs(rel: str, account_key: str) -> dict:
    d = json.loads((REPO / rel).read_text())
    out = {}
    for gsym, rec in (d.get("symbols") or {}).items():
        side = rec.get(account_key) or {}
        if "swap_long" not in side:
            continue
        native = rec.get(f"{account_key}_native") or gsym
        out[str(native)] = {
            "gtos_symbol": gsym,
            "swap_long": side.get("swap_long"),
            "swap_short": side.get("swap_short"),
            "swap_mode": side.get("swap_mode"),
            "point": side.get("point"),
        }
    return out, d.get("measured_at_utc")


def from_export(fname: str) -> dict:
    out = {}
    for line in (EXPORT / fname).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        n = r.get("name") or r.get("symbol")
        if n is None or "swap_long" not in r:
            continue
        out[str(n)] = {
            "gtos_symbol": None,
            "swap_long": r.get("swap_long"),
            "swap_short": r.get("swap_short"),
            "swap_mode": r.get("swap_mode"),
            "point": r.get("point"),
            "quote_time_epoch": r.get("time"),
        }
    return out


def main() -> int:
    ver_ft, ver_at = from_verified_specs(
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/VERIFIED_BROKER_SYMBOL_SPECS.json",
        "ftmo",
    )
    ver_fn, _ = from_verified_specs(
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/VERIFIED_BROKER_SYMBOL_SPECS.json",
        "redacted_account",
    )
    series = {
        "FTMO": [
            ("2026-06-01T18:01Z", "config/profiles/operator_profile.yaml",
             from_profile("config/profiles/operator_profile.yaml")),
            ("2026-06-02", "FTMO_SYMBOL_SPEC_LEDGER.jsonl",
             from_spec_ledger("research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/FTMO_SYMBOL_SPEC_LEDGER.jsonl")),
            (str(ver_at), "VERIFIED_BROKER_SYMBOL_SPECS.json", ver_ft),
            ("2026-07-25", "vps-export-20260725 ftmo_symbols_get.jsonl", from_export("ftmo_symbols_get.jsonl")),
        ],
        "redacted_account": [
            ("2026-06-01/02", "config/profiles/redacted_account.yaml", from_profile("config/profiles/redacted_account.yaml")),
            (str(ver_at), "VERIFIED_BROKER_SYMBOL_SPECS.json", ver_fn),
            ("2026-07-25", "vps-export-20260725 redacted_account_symbols_get.jsonl", from_export("redacted_account_symbols_get.jsonl")),
        ],
    }

    out = {
        "claim_refuted": (
            "LANE_5_UNEXPLORED_ALPHA_SPACE_V1.md 2.3(v): 'there is no swap time series anywhere "
            "on this machine'. Three distinct capture instants exist for FTMO and are reconciled "
            "here; they disagree materially, including sign flips."
        ),
        "captures": {a: [{"date": d, "source": s, "n_symbols": len(m)} for d, s, m in v]
                     for a, v in series.items()},
        "per_symbol": {},
        "summary": {},
    }

    for acct, caps in series.items():
        syms = sorted({s for _, _, m in caps for s in m})
        rows, n_moved, n_sign_flip, n_side_flip = {}, 0, 0, 0
        for s in syms:
            obs = [(d, src, m[s]) for d, src, m in caps if s in m]
            if len(obs) < 2:
                continue
            longs = [(d, o.get("swap_long")) for d, _, o in obs]
            shorts = [(d, o.get("swap_short")) for d, _, o in obs]
            lv = [v for _, v in longs if v is not None]
            sv = [v for _, v in shorts if v is not None]
            if not lv or not sv:
                continue
            moved = (max(lv) != min(lv)) or (max(sv) != min(sv))
            lsign = {(v >= 0) for v in lv}
            ssign = {(v >= 0) for v in sv}
            sign_flip = len(lsign) > 1 or len(ssign) > 1
            # "favourable side" = the side with swap >= 0 (or the less-negative one)
            fav = [("LONG" if l >= sh else "SHORT") for (_, l), (_, sh) in zip(longs, shorts)
                   if l is not None and sh is not None]
            side_flip = len(set(fav)) > 1
            n_moved += moved
            n_sign_flip += sign_flip
            n_side_flip += side_flip
            first_l, last_l = lv[0], lv[-1]
            rows[s] = {
                "gtos_symbol": next((o.get("gtos_symbol") for _, _, o in obs if o.get("gtos_symbol")), None),
                "observations": [{"date": d, "source": src, "swap_long": o.get("swap_long"),
                                  "swap_short": o.get("swap_short")} for d, src, o in obs],
                "n_observations": len(obs),
                "moved": moved,
                "sign_flip_on_either_side": sign_flip,
                "favourable_side_flipped": side_flip,
                "favourable_side_sequence": fav,
                "swap_long_first": first_l,
                "swap_long_last": last_l,
                "swap_long_pct_change": (
                    None if first_l == 0 else (last_l - first_l) / abs(first_l) * 100.0
                ),
                "ever_favourable_long": any(v >= 0 for v in lv),
                "ever_favourable_short": any(v >= 0 for v in sv),
                "always_favourable_long": all(v >= 0 for v in lv),
                "always_favourable_short": all(v >= 0 for v in sv),
            }
        out["per_symbol"][acct] = rows
        ever_fav = [s for s, r in rows.items() if r["ever_favourable_long"] or r["ever_favourable_short"]]
        always_fav = [s for s, r in rows.items() if r["always_favourable_long"] or r["always_favourable_short"]]
        out["summary"][acct] = {
            "symbols_with_2plus_observations": len(rows),
            "moved_at_all": n_moved,
            "sign_flipped_on_a_side": n_sign_flip,
            "favourable_side_flipped": n_side_flip,
            "ever_favourable": len(ever_fav),
            "always_favourable": len(always_fav),
            "favourable_but_not_persistently": sorted(set(ever_fav) - set(always_fav)),
        }

    (HERE / "B9_SWAP_PERSISTENCE_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    for acct in series:
        s = out["summary"][acct]
        print(f"\n=== {acct} === captures: " + ", ".join(c["date"] for c in out["captures"][acct]))
        print(f"  symbols with >=2 obs: {s['symbols_with_2plus_observations']}   moved: {s['moved_at_all']}"
              f"   sign flipped: {s['sign_flipped_on_a_side']}   favourable side flipped: {s['favourable_side_flipped']}")
        print(f"  ever favourable: {s['ever_favourable']}   PERSISTENTLY favourable: {s['always_favourable']}")
        print(f"  favourable but NOT persistently: {s['favourable_but_not_persistently']}")
        interesting = sorted(out["per_symbol"][acct].items(),
                             key=lambda kv: -abs(kv[1]["swap_long_pct_change"] or 0))[:12]
        print(f"  {'symbol':<14}{'swap_long series':<44}{'%chg':>10}  fav-side seq")
        for sym, r in interesting:
            seq = " -> ".join(f"{o['swap_long']:g}" for o in r["observations"])
            pc = r["swap_long_pct_change"]
            print(f"  {sym:<14}{seq:<44}{(f'{pc:+.1f}' if pc is not None else 'n/a'):>10}  {'/'.join(r['favourable_side_sequence'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
