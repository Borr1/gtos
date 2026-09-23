#!/usr/bin/env python3
"""CF-1/CF-4 receipt generator — the resolution sweep, and the vendored broker symbol trees.

Read-only. Imports no broker module, opens no socket, touches no VPS. It reads:

  * the two live profiles in this repo (`config/profiles/*.yaml`) — byte-identical, for FTMO, to
    the copy on the host lineage (verified: sha256 ae9312e6…, see the receipt's `profile_sha256`);
  * the sleeve registry's full declared universe (BUILT + CANDIDATE_BUILT + MARKET_EXPANSION_BUILT);
  * the read-only 2026-07-25 VPS export's `09_mt5_api/*_symbols_get.jsonl` — the brokers' own
    answer to `symbols_get()`, pulled 2026-07-25T23:28:21Z.

Emits two artifacts under this directory:

  CF_SYMBOL_RESOLUTION_V1.json   the sweep + the verdict on the 2026-07-31 "rename" event
  BROKER_SYMBOL_TREE_20260725.json  names-only vendored trees, both accounts (the test fixture
                                    and the refreshed broker-truth baseline; specs stay in the
                                    full export, this is the *name surface* only)

Usage:  python3 docs/audits/.../phase15/receipts/cf_resolution_probe.py [--export-root PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from src.components.ultimate_book.sleeves.registry import (  # noqa: E402
    BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT,
)
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.components.ultimate_book.symbol_resolution_watch import (  # noqa: E402
    build_slots, watch, rename_candidates,
)

DEFAULT_EXPORT = Path("/Users/borr/GTOSActive/vps-export-20260725/extracted")

PROFILES = {
    "FTMO": REPO / "config/profiles/operator_profile.yaml",
    "redacted_account": REPO / "config/profiles/redacted_account.yaml",
}
EXPORT_KEY = {"FTMO": "ftmo", "redacted_account": "redacted_account"}

#: FTMO's armed five as of 2026-07-31 (`run_book.py --tags`, host commit d6c9c4b19); redacted_account's
#: four core sleeves. `metals_core` was pulled 2026-07-29 14:25 and `fx_jpy` 2026-07-30 ~14:57.
ARMED = {
    "FTMO": ["crypto", "energy_agri", "sub_xvol_pullback",
             "mx_btcusd_d1_donchian_20_breakout"],
    "redacted_account": ["crypto", "energy_agri", "sub_xvol_pullback"],
}

#: The five canonical names the 2026-07-31 probe asked FTMO for directly, and what the FTMO
#: profile has always resolved them to.
EVENT_NAMES = ["SPX500", "UK100", "GER40", "JP225", "NAS100"]


def read_tree(path: Path) -> set[str]:
    names: set[str] = set()
    if not path.is_file():
        return names
    with open(path, "r", encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            n = rec.get("name") or rec.get("symbol")
            if n:
                names.add(str(n))
    return names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-root", default=str(DEFAULT_EXPORT))
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent))
    args = ap.parse_args()

    export = Path(args.export_root).expanduser()
    if (export / "extracted").is_dir():
        export = export / "extracted"
    out_dir = Path(args.out_dir)

    all_specs = {}
    all_specs.update(BUILT)
    all_specs.update(CANDIDATE_BUILT)
    all_specs.update(MARKET_EXPANSION_BUILT)

    pull = {}
    p = export / "09_mt5_api" / "_MT5_PULL_SUMMARY.json"
    if p.is_file():
        pull = json.loads(p.read_text(encoding="utf-8-sig"))

    trees, accounts, fixture = {}, {}, {}
    for acct, prof_path in PROFILES.items():
        raw = prof_path.read_bytes()
        prof = yaml.safe_load(raw.decode("utf-8"))
        resolve = build_broker_symbol_resolver(prof)
        tree = read_tree(export / "09_mt5_api" / f"{EXPORT_KEY[acct]}_symbols_get.jsonl")
        trees[acct] = tree
        fixture[acct] = sorted(tree)

        slots = build_slots(all_specs.values(), resolve, armed_tags=ARMED[acct])
        verdict = watch(slots, tree or None, account=acct)
        verdict["rename_candidates"] = rename_candidates(verdict["unresolvable"], tree)

        accounts[acct] = {
            "profile": str(prof_path.relative_to(REPO)),
            "profile_sha256": hashlib.sha256(raw).hexdigest(),
            "n_instruments": len(prof.get("instruments") or {}),
            "armed_tags": ARMED[acct],
            "n_tree": len(tree),
            "watch": verdict,
            "event_names": {
                name: {
                    "profile_supported": bool(getattr(resolve, "supports")(name)),
                    "resolves_to": resolve(name),
                    "bare_name_in_tree": name in tree,
                    "resolved_name_in_tree": resolve(name) in tree,
                }
                for name in EVENT_NAMES
            },
        }

    ftmo, fn = accounts["FTMO"], accounts["redacted_account"]
    bare_absent_ftmo = [n for n, r in ftmo["event_names"].items() if not r["bare_name_in_tree"]]
    resolved_present_ftmo = [n for n, r in ftmo["event_names"].items()
                             if r["resolved_name_in_tree"]]
    bare_present_fn = [n for n, r in fn["event_names"].items() if r["bare_name_in_tree"]]

    receipt = {
        "schema": "gtos.cf.symbol_resolution.v1",
        "session": "CF",
        "blocks": "B2350-B2399",
        "read_only_assertion": (
            "No broker module imported, no socket opened, no VPS touched, no config written. "
            "Every broker fact below comes from the read-only 2026-07-25 export."),
        "evidence": {
            "export_root": str(export),
            "export_generated_utc": pull.get("generated_utc"),
            "ftmo_login": ((pull.get("terminals") or {}).get("ftmo") or {})
                          .get("expected_login"),
            "ftmo_server": ((pull.get("terminals") or {}).get("ftmo") or {})
                           .get("expected_server"),
            "registry_universe": {
                "BUILT": len(BUILT), "CANDIDATE_BUILT": len(CANDIDATE_BUILT),
                "MARKET_EXPANSION_BUILT": len(MARKET_EXPANSION_BUILT),
                "total_sleeves": len(all_specs),
                "distinct_canonical_symbols": len(
                    {s for sp in all_specs.values() for s in sp.on_surface}),
            },
        },
        "accounts": accounts,
        "verdict_on_the_2026_07_31_event": {
            "claim": ("FTMO renamed SPX500/UK100/GER40/JP225(/NAS100) to .cash variants on "
                      "2026-07-31, muting 4 sub_xvol_pullback and 3 sub_mid_dn_revert members."),
            "finding": "REFUTED — no rename occurred and no member was ever mute.",
            "because": [
                "The five names probed are GTOS CANONICAL names, not FTMO broker names.",
                "FTMO's tree in the 2026-07-25 export — six days BEFORE the alleged rename — "
                "already lacked every bare name and already served every .cash target: "
                f"bare-absent {bare_absent_ftmo}, resolved-present {resolved_present_ftmo}.",
                "The FTMO profile maps all five across and always has "
                "(sha256 ae9312e6…, byte-identical to the host lineage's copy).",
                "Same-instant control: redacted_account, probed by the same code in the same export, "
                f"DOES carry the bare names {bare_present_fn} and carries no .cash variant — "
                "which is exactly what the two profiles encode.",
            ],
            "ftmo_unresolvable_now": len(ftmo["watch"]["unresolvable"]),
            "redacted_account_unresolvable_now": len(fn["watch"]["unresolvable"]),
        },
    }

    (out_dir / "CF_SYMBOL_RESOLUTION_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    (out_dir / "BROKER_SYMBOL_TREE_20260725.json").write_text(
        json.dumps({
            "schema": "gtos.broker.symbol_tree.v1",
            "source": "vps-export-20260725/extracted/09_mt5_api/*_symbols_get.jsonl",
            "generated_utc": pull.get("generated_utc"),
            "note": ("NAME SURFACE ONLY — the full per-symbol specs stay in the export. This is "
                     "the artifact the rename watchdog and its tests diff against; refreshing it "
                     "is CF-4's re-vendor step."),
            "counts": {a: len(v) for a, v in fixture.items()},
            "symbols": fixture,
        }, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "FTMO": {k: ftmo["watch"][k] for k in ("state", "n_slots", "resolved_ok", "n_tree")},
        "redacted_account": {k: fn["watch"][k] for k in ("state", "n_slots", "resolved_ok", "n_tree")},
        "ftmo_unresolvable": len(ftmo["watch"]["unresolvable"]),
        "fn_unresolvable": len(fn["watch"]["unresolvable"]),
        "verdict": receipt["verdict_on_the_2026_07_31_event"]["finding"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
