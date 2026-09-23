"""Session AU (B1585) — rebuild `sub_mid_dn_revert`'s exit frontier on the RE-CLOCKED population.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_submid_frontier.py

THE DEBT (AQ handoff 4)

AM repaired `substrate._session_hour` -- it compared a raw UTC hour against broker-hour session
constants, mis-bucketing **50.04 %** of this sleeve's 370,808 archive H4 bars -- and measured the A/B
but never regenerated the artifacts downstream of it. AQ built the artifact of record
(`AQ_ESTATE_TRADES_V2.json.gz`, 503 -> 533 trades, jaccard 0.293, mean R 0.3996 -> 0.4784) and listed
four artifacts still on the defect clock, of which `EXIT_FRONTIER_V1.json` is the one that needs a
re-run rather than arithmetic. Every session since has had to remember the substitution by hand.

WHY A WRAPPER AND NOT AN EDIT TO AD's RECEIPT

`ad_exit_sweep.main()` reads `AA_ESTATE_TRADES.json.gz` at module scope and gates its baseline against
`AA_ESTATE_WALK.json` for parity. Editing that file would (a) change a committed wave-7 receipt whose
whole value is that it reproduces AA, and (b) mean any future reader could not tell which population a
given `EXIT_FRONTIER_V1*.json` was built on. So this substitutes the input and nothing else: AD's
`plan_for` / `resimulate` / `summarize` run byte-identically, which is the property AK relied on when
it wrote *"any difference between this frontier and AD's is a difference in the sleeve, not in the
instrument."*

Output: `EXIT_FRONTIER_V1_SUBMID_V2.json` beside AD's, which `ad_frontier_analysis.py` merges by glob
with later files winning per sleeve -- AD's own designed mechanism for exactly this
("a re-run of two sleeves cannot destroy a 24-sleeve sweep", `ad_exit_sweep.py:130-131`).

THE PARITY LINE, AND WHAT IT DOES *NOT* SAY

AD's baseline parity check compares its own re-gate against `AA_ESTATE_WALK.json`, and on the re-clocked
population `sub_mid_dn_revert` must differ. It reports SEVEN sleeves moved -- and asserting "exactly one
moved" would have been asserting something false about someone else's artifact. MEASURED instead: AD's
own committed frontier, on AA's UNMODIFIED input, already reports SIX moved (26/32 identical). Seven
here is that pre-existing set plus exactly this sleeve, so `moved_by_this_swap` is the assertion and it
is `[sub_mid_dn_revert]`. The six pre-existing ones are a standing discrepancy between AD's re-gate and
AA's stored walk that this session did not create and does not resolve.

BOUNDARY. Offline and pure; AD's own instrument, one input swapped.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
P11 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(P7))

SUBMID = "sub_mid_dn_revert"
V2 = P11 / "AQ_ESTATE_TRADES_V2.json.gz"
RECEIPT = HERE / "AU_SUBMID_FRONTIER_V1.json"


def main() -> int:
    os.environ.setdefault("AD_ONLY", SUBMID)
    os.environ.setdefault("AD_OUT_SUFFIX", "_SUBMID_V2")

    import ad_exit_sweep as AD

    # AQ's V2 estate IS AA's with this sleeve's population replaced and every other sleeve
    # byte-identical, so it is a drop-in for AD's input. Verified here rather than trusted.
    v2 = json.load(gzip.open(V2, "rt"))
    aa = json.load(gzip.open(P6 / "AA_ESTATE_TRADES.json.gz", "rt"))
    differ = sorted(s for s in aa["trades"]
                    if json.dumps(aa["trades"][s], sort_keys=True)
                    != json.dumps((v2["trades"] or {}).get(s), sort_keys=True))
    if differ != [SUBMID]:
        raise RuntimeError(f"AQ_ESTATE_TRADES_V2 differs from AA on {differ}, expected exactly "
                           f"[{SUBMID!r}]. Refusing to swap an input whose scope is not what the "
                           f"artifact claims.")
    n_before, n_after = len(aa["trades"][SUBMID]), len(v2["trades"][SUBMID])
    print(f"input control: only {SUBMID} differs; {n_before} -> {n_after} trades", flush=True)

    # Point AD's module-level input at AQ's committed V2 artifact. The first version of this wrote
    # the substituted estate to a temp file, and `ad_exit_sweep` stamps `AA_IN.relative_to(REPO)` into
    # its own provenance -- so it ran the whole 58-cell sweep and then died on the write. The temp file
    # was never needed: `AQ_ESTATE_TRADES_V2.json.gz` IS AA's estate with this sleeve replaced, which
    # the control above verifies rather than assumes, and it lives in the repo so the provenance stamp
    # names a path a reader can open.
    AD.AA_IN = V2
    AD.OUT = P7 / "EXIT_FRONTIER_V1_SUBMID_V2.json"
    print(f"running AD's sweep on {SUBMID} with the re-clocked population -> "
          f"{AD.OUT.relative_to(REPO)}", flush=True)

    doc = AD.main()

    frontier = json.loads(AD.OUT.read_text(encoding="utf-8"))
    sl = (frontier.get("sleeves") or {}).get(SUBMID) or {}
    parity = frontier.get("baseline_parity_vs_aa") or {}
    moved = sorted((parity.get("moved") or {}))
    # THE CONTROL FOR THE PARITY LINE, and it is a read rather than an argument. AD's own committed
    # frontier -- built on AA's UNMODIFIED input -- already reports six sleeves as moved against
    # `AA_ESTATE_WALK.json` (26/32 identical). So "seven moved here" is that pre-existing set plus
    # exactly this sleeve, which is the shape the swap should produce. Asserting `moved == [SUBMID]`
    # (the first version) would have been asserting something false about someone else's artifact.
    ad_committed = json.loads((P7 / "EXIT_FRONTIER_V1.json").read_text(encoding="utf-8"))
    pre_existing = sorted((ad_committed.get("baseline_parity_vs_aa") or {}).get("moved") or {})
    delta = sorted(set(moved) - set(pre_existing))
    receipt = {
        "schema": "gtos.au.submid_frontier.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
                        "au_submid_frontier.py",
        "session": "AU", "block": "B1585",
        "closes_repair_row": "REBUILD_THE_DOWNSTREAM_ARTIFACTS_ON_THE_REPAIRED_CLOCK",
        "instrument": "ad_exit_sweep.main() unmodified; only AA_IN and OUT substituted",
        "population": str(V2.relative_to(REPO)),
        "n_trades_before": n_before, "n_trades_after": n_after,
        "input_control_only_this_sleeve_differs": True,
        "out": str(AD.OUT.relative_to(REPO)),
        "merges_via": ("ad_frontier_analysis.py globs EXIT_FRONTIER_V1*.json, later files winning "
                       "per sleeve (ad_exit_sweep.py:130-131)"),
        "baseline_parity_moved": moved,
        "baseline_parity_moved_in_ADs_committed_frontier_on_the_unmodified_input": pre_existing,
        "moved_by_this_swap": delta,
        "baseline_parity_shape_is_as_expected": (delta == [SUBMID]),
        # AD's per-sleeve schema, not AK's V2 one -- my first draft read AK's key names off the
        # wrong artifact and published a block of nulls, which is the silent-null class this
        # programme has now logged four times. Read the keys, then report them.
        "frontier": {
            "available": sl.get("available"), "timeframe": sl.get("timeframe"),
            "n_trades_as_walked": sl.get("n_trades_as_walked"),
            "n_cells_gated": frontier.get("n_cells_gated"),
            "live_exit_contract": sl.get("live_exit_contract"),
            "live_time_stop_in_own_bars": sl.get("live_time_stop_in_own_bars"),
            "zero_carry_ceiling": sl.get("zero_carry_ceiling"),
            "best_cell_at_spread_bands": sl.get("best_cell_at_spread_bands"),
            "native_target_convention": sl.get("native_target_convention"),
            "n_cells_for_this_sleeve": len(sl.get("cells") or {}),
        },
        "caveat": ("AD's frontier is at the FLAT 37-day cost snapshot on ALL_ERAS at the historical "
                   "69-look family — the two qualifications AO and AR established. This rebuild "
                   "restores comparability with the rest of AD's frontier; it is NOT a verdict at "
                   "the ratified rule. AQ §3 carries this sleeve's ratified-rule band table "
                   "(REJECT at all four bands, p 0.0252 flat -> 0.1635 mid)."),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=1, default=str), encoding="utf-8")
    print(json.dumps(receipt["frontier"], indent=1))
    print(f"parity moved: {moved}")
    print(f"  pre-existing in AD's own frontier: {pre_existing}")
    print(f"  moved BY THIS SWAP: {delta} (expected exactly ['{SUBMID}'])")
    print(f"wrote {RECEIPT.relative_to(REPO)}")
    if delta != [SUBMID]:
        raise RuntimeError(f"the swap moved {delta}, expected exactly [{SUBMID!r}]. An input that "
                           f"differs on one sleeve cannot move another; refusing to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
