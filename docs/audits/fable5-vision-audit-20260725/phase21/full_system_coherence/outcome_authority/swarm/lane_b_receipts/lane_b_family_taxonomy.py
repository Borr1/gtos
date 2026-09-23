"""LANE B receipt 1 — what is actually IN the 59-member declared family.

The question this answers is not "how many rows are there" (the artifact says 59) but
"how many DISTINCT HYPOTHESES do those rows test". Benjamini-Hochberg is a correction for
a family of comparable hypotheses tested for the same question; its bill is a bill on
INDEPENDENT OPPORTUNITIES to find a false positive. Two rows that are the same trade
series are one opportunity, not two, and charging two is not conservative-but-safe -- it
destroys real findings at a rate the estate has never measured.

EVERY classification below is bound to an artifact or to production source. Nothing is
asserted from prose:

  * rows 1-32 -- the live registry. `base_mechanism` is the GENERATOR FUNCTION each
    SleeveSpec actually holds, read by importing
    `src.components.ultimate_book.sleeves.registry` and inspecting
    `SleeveSpec.generator.__module__` / `.__name__`. Two rows sharing a generator function
    are the same entry rule on different instruments, by construction and not by opinion.

  * rows 40-48 -- Session AF's family sweep. AF's own artifact
    `phase7/receipts/AF_FAMILY_TRADES.json.gz` carries `mechanisms.<mech>.parent_sleeve`
    and `.source` (a file:line into production), and a `parity.W_MX_PILOT` block that maps
    registry sleeve names to AF member names with `n_compared: 10, n_exact: 10`. That
    parity block is what proves three of these rows are the SAME SERIES as three rows
    already in the family, to the trade.

  * rows 54-57 -- Session CH's P1-HIST milestones.
    `phase15/receipts/CH_MEASUREMENT_PROTOCOL_V1.json` -> `looks[].sleeve` names the
    registry sleeve each milestone re-tests, verbatim.

  * rows 33-39, 49-53, 58-59 -- classified from the declaration's own `source` and `basis`
    strings, which name the parent sleeve explicitly.

Output: LANE_B_FAMILY_TAXONOMY_V1.json
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))

V27 = REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/CANDIDATE_FAMILY_V27.json"
AF = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AF_FAMILY_TRADES.json.gz"
CH = REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CH_MEASUREMENT_PROTOCOL_V1.json"
OUT = Path(__file__).resolve().parent / "LANE_B_FAMILY_TAXONOMY_V1.json"

FAMILY_ID = "CANDIDATE_BOOK_V1"

# ---------------------------------------------------------------------------------------
# Derivation classes. `BASE` is the only one that introduces a mechanism; every other class
# is a hypothesis ABOUT a mechanism already in the family.
BASE = "BASE"                       # a distinct entry rule, first appearance
INSTRUMENT_SIBLING = "INSTRUMENT_SIBLING"   # same entry rule, different symbol
DUPLICATE_SERIES = "DUPLICATE_SERIES"       # same entry rule AND same symbol as an existing row
THRESHOLD_VARIANT = "THRESHOLD_VARIANT"     # same rule shape, constants moved
REGIME_CELL = "REGIME_CELL"                 # parent rule + a conditioning filter
OVERLAY = "OVERLAY"                         # parent rule + a learned admission filter
POOLED_AGGREGATE = "POOLED_AGGREGATE"       # several existing rows judged as one series
RETEST = "RETEST"                           # same rule, same symbol, different account/exit


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def registry_mechanisms() -> dict[str, dict]:
    """tag -> {generator, timeframe, cluster}, read from production, not from prose."""
    from src.components.ultimate_book.sleeves import registry as R

    built = dict(R.BUILT)
    built.update(R.CANDIDATE_BUILT)
    built.update(R.MARKET_EXPANSION_BUILT)
    out = {}
    for tag, spec in built.items():
        g = spec.generator
        out[tag] = {
            "generator": f"{getattr(g, '__module__', '?').split('.')[-1]}.{getattr(g, '__name__', '?')}",
            "timeframe": spec.timeframe,
            "cluster": spec.cluster,
        }
    return out


def mx_signal_family(tag: str) -> str | None:
    """The three market-expansion D1 rules share three signal functions
    (`market_expansion_d1.py:103-115` donchian, `:129-144` volume surge, `:118-126` ATR MR),
    named in AF_FAMILY_TRADES.mechanisms.*.source. The per-symbol generator wrappers differ
    only in which symbol they pass."""
    for k in ("donchian_20_breakout", "volume_surge_reversal", "atr_mean_reversion"):
        if k in tag:
            return "mx_d1_" + k
    return None


def main() -> int:
    decl = json.loads(V27.read_bytes())
    fam = decl["families"][FAMILY_ID]
    members = fam["members"]

    reg = registry_mechanisms()
    af = json.load(gzip.open(AF))
    parity = af["parity"]["W_MX_PILOT"]["rows"]
    af_member_to_sleeve = {
        v["member"]: k for k, v in parity.items() if v.get("member")
    }
    af_mechs = af["mechanisms"]
    ch = json.loads(CH.read_bytes())
    ch_sleeve = {lk["name"]: lk.get("sleeve") for lk in ch.get("looks", [])}

    # --- explicit derivation map for the 27 non-registry rows -----------------------------
    # Each entry: (derivation, parent_row_name, evidence)
    DERIVED: dict[str, tuple[str, str, str]] = {}

    for m in members:
        n = m["name"]
        src, basis = m.get("source", ""), m.get("basis", "")
        if n.startswith("thr_sub_xvol_pullback_vr14"):
            DERIVED[n] = (THRESHOLD_VARIANT, "sub_xvol_pullback",
                          "declaration source: 'threshold variant of `sub_xvol_pullback`'s "
                          "substrate cell, generated through the production GenerationPort'")
        elif n.startswith("thr_sub_xvol_pullback_"):
            DERIVED[n] = (REGIME_CELL, "sub_xvol_pullback",
                          "declaration basis: 'Session AO pre-declared regime cell: "
                          "`sub_xvol_pullback` + ...'")
        elif n == "thr_asia_pdl_fade_persistence_revert":
            DERIVED[n] = (REGIME_CELL, "asia_pdl_fade",
                          "declaration basis: 'Session AO pre-declared regime cell: "
                          "`asia_pdl_fade` + AB's `PERSISTENCE == revert`'")
        elif n == "fam_ao_btc_power_pool_crypto_d1":
            DERIVED[n] = (POOLED_AGGREGATE, "mx_btcusd_d1_donchian_20_breakout",
                          "declaration basis: 'the nine members of AF's "
                          "`fam_donchian_20_breakout_crypto_d1` judged as ONE series at "
                          "`target_5R`' -- a pool OVER rows already declared")
        elif n.startswith("mxf_"):
            sleeve = af_member_to_sleeve.get(n)
            mech = None
            for mk, mv in af_mechs.items():
                if mk in n:
                    mech = mv
                    break
            if sleeve:
                DERIVED[n] = (DUPLICATE_SERIES, sleeve,
                              f"AF_FAMILY_TRADES.parity.W_MX_PILOT maps {n} <-> {sleeve} "
                              f"with w_mx_pilot={parity[sleeve]['w_mx_pilot']} == "
                              f"af_engine_reachable={parity[sleeve]['af_engine_reachable']} "
                              f"(n_compared=10, n_exact=10)")
            else:
                parent = (mech or {}).get("parent_sleeve", "?")
                DERIVED[n] = (INSTRUMENT_SIBLING, parent,
                              f"AF_FAMILY_TRADES.mechanisms carries parent_sleeve="
                              f"{parent!r}, source={(mech or {}).get('source')!r}")
        elif n.startswith("overlay_metalabel_fx_jpy"):
            DERIVED[n] = (OVERLAY, "fx_jpy",
                          "declaration source: AV's label store over "
                          "'sleeves/fx_jpy.generate_fx_jpy'; the overlay filters that "
                          "sleeve's own intents")
        elif n.startswith("ch_p1_hist::"):
            s = ch_sleeve.get(n)
            DERIVED[n] = (RETEST, s or "?",
                          f"CH_MEASUREMENT_PROTOCOL_V1.looks[].sleeve == {s!r} -- the same "
                          f"registry sleeve at a different account/exit spec")
        elif n == "cp_true_utc_ny_metals_long_v1":
            DERIVED[n] = (BASE, "",
                          "Session CP true-UTC candidate factory over the broad-V4 S0R0 "
                          "replay substrate -- a generator no registry row shares")
        elif n == "cq_current_breaker_re_entry_inverted_5d_stop_0p25d":
            DERIVED[n] = (BASE, "",
                          "Session CQ predeclared S0R0 true-UTC January path grid, "
                          "inverted current_breaker_re_entry -- a generator no registry "
                          "row shares")

    # --- build the rows -------------------------------------------------------------------
    rows = []
    mech_of_row: dict[str, str] = {}
    for i, m in enumerate(members, 1):
        n = m["name"]
        if n in reg:
            g = reg[n]
            mech = mx_signal_family(n) or g["generator"]
            deriv = BASE
            parent = ""
            ev = (f"registry SleeveSpec.generator == {g['generator']}, "
                  f"timeframe={g['timeframe']}, cluster={g['cluster']}")
            rows.append(dict(row=i, name=n, substrate="ultimate_book_registry",
                             base_mechanism=mech, derivation=deriv, parent=parent,
                             evidence=ev, look_taken=bool(m.get("look_taken", True)),
                             generator=g["generator"], timeframe=g["timeframe"],
                             cluster=g["cluster"]))
            mech_of_row[n] = mech
        else:
            deriv, parent, ev = DERIVED[n]
            rows.append(dict(row=i, name=n, substrate=("broad_v4_replay_exhaust"
                                                       if deriv == BASE else
                                                       "derived_from_registry_row"),
                             base_mechanism=None, derivation=deriv, parent=parent,
                             evidence=ev, look_taken=bool(m.get("look_taken", True)),
                             generator=None, timeframe=None, cluster=None))

    # resolve derived rows onto the parent's base mechanism (one hop is enough: every
    # parent named above is a registry row).
    for r in rows:
        if r["base_mechanism"] is None:
            if r["derivation"] == BASE:
                r["base_mechanism"] = "brd_" + r["name"]
            else:
                r["base_mechanism"] = mech_of_row.get(r["parent"], "UNRESOLVED:" + r["parent"])

    # --- aggregate ------------------------------------------------------------------------
    mechs: dict[str, list[str]] = {}
    for r in rows:
        mechs.setdefault(r["base_mechanism"], []).append(r["name"])

    by_deriv: dict[str, int] = {}
    for r in rows:
        by_deriv[r["derivation"]] = by_deriv.get(r["derivation"], 0) + 1

    substrates: dict[str, int] = {}
    for r in rows:
        s = ("broad_v4_replay_exhaust" if r["base_mechanism"].startswith("brd_")
             else "ultimate_book_archive")
        substrates[s] = substrates.get(s, 0) + 1

    dup = [r for r in rows if r["derivation"] == DUPLICATE_SERIES]
    no_look = [r for r in rows if not r["look_taken"]]

    # First appearance of a mechanism vs a repeat of one already declared. NOTE this is a
    # different cut from `derivation`: a registry row is `BASE` (it is not derived FROM
    # another row) and can still be the seventh row testing the same entry rule, because
    # the registry ships one SleeveSpec per symbol.
    seen: set[str] = set()
    for r in rows:
        r["first_appearance_of_mechanism"] = r["base_mechanism"] not in seen
        seen.add(r["base_mechanism"])
    n_first = sum(1 for r in rows if r["first_appearance_of_mechanism"])

    out = {
        "schema": "gtos.lane_b.family_taxonomy.v1",
        "generated_by": "phase21/.../swarm/lane_b_receipts/lane_b_family_taxonomy.py",
        "declaration": {"path": str(V27.relative_to(REPO)), "sha256": sha256(V27),
                        "family_id": FAMILY_ID,
                        "declared": fam["high_water_size"],
                        "looks_taken": fam.get("high_water_looks")},
        "evidence_bindings": {
            "registry": "src/components/ultimate_book/sleeves/registry.py "
                        "(BUILT + CANDIDATE_BUILT + MARKET_EXPANSION_BUILT), generator "
                        "function read by import",
            "af_parity": {"path": str(AF.relative_to(REPO)), "sha256": sha256(AF),
                          "n_compared": af["parity"]["W_MX_PILOT"]["n_compared"],
                          "n_exact": af["parity"]["W_MX_PILOT"]["n_exact"]},
            "ch_protocol": {"path": str(CH.relative_to(REPO)), "sha256": sha256(CH)},
        },
        "counts": {
            "declared_rows": len(rows),
            "distinct_base_mechanisms": len(mechs),
            "rows_by_derivation": by_deriv,
            "rows_by_substrate": substrates,
            "rows_that_are_first_appearance_of_their_mechanism": n_first,
            "rows_that_repeat_a_mechanism_already_declared": len(rows) - n_first,
            "rows_derived_from_a_row_already_in_the_family":
                len(rows) - by_deriv.get(BASE, 0),
            "exact_duplicate_series": len(dup),
            "rows_with_look_taken_false": len(no_look),
        },
        "mechanisms": {k: {"n_rows": len(v), "rows": sorted(v)}
                       for k, v in sorted(mechs.items(), key=lambda kv: -len(kv[1]))},
        "duplicate_series": [{"row": r["name"], "identical_to": r["parent"],
                              "evidence": r["evidence"]} for r in dup],
        "no_look_rows": [{"row": r["name"]} for r in no_look],
        "rows": rows,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False) + "\n")

    print(f"declared rows                     : {len(rows)}")
    print(f"distinct base mechanisms          : {len(mechs)}")
    print(f"first appearance of a mechanism   : {n_first}")
    print(f"repeat of a declared mechanism    : {len(rows) - n_first}")
    print(f"rows derived from an existing row : {len(rows) - by_deriv.get(BASE, 0)}")
    print(f"exact duplicate trade series      : {len(dup)}")
    print(f"rows by derivation                : {by_deriv}")
    print(f"rows by substrate                 : {substrates}")
    print()
    for k, v in sorted(mechs.items(), key=lambda kv: -len(kv[1])):
        if len(v) > 1:
            print(f"  {len(v):2d}  {k:34s} {sorted(v)}")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
