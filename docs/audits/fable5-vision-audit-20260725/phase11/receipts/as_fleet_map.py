#!/usr/bin/env python3
"""AS-3 — the replay fleet map: every banked-but-unrun measurement, priced and ordered.

An *executable* document. Each member declares its driver, and this file **checks the driver
exists** — a fleet map whose entries point at files nobody has written is a wish list, and the
distinction between "the grid exists, re-gate it" and "somebody has to write this first" is the
single largest term in what a measurement costs.

Each member carries:

  * `driver` — the file that runs it, and `driver_exists` measured on disk
  * `machine_hours` + `mh_basis` — the estimate AND where the estimate comes from
  * `memory_class` — `SEALED_REPLAY` (6-15 GB, NEVER parallel: H3 measured the peak is evidence
    accumulation, 60.6 % of heap, and it does not shrink), `WALKFORWARD` (light, parallel-safe),
    `ARITHMETIC` (seconds), `CAPTURE` (I/O bound, network or host)
  * `verdict_moved` — the decision it changes. A measurement that moves no verdict does not belong
    on this map at all, which is the charter's own test (§7: state which decision it changes).
  * `value` — 1-5, and `value_basis` naming what makes it that
  * `blocked_by` — what has to be true first, or null

Ordered by `value / machine_hours`. That ordering is the product: it is what the next waves are
scheduled from, and it is deliberately NOT ordered by how interesting the question is.

    python3 .../as_fleet_map.py            # writes the JSON and the markdown
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
OUT_JSON = AUDIT / "phase11/receipts/AS_FLEET_MAP_V1.json"
OUT_MD = AUDIT / "phase11/REPLAY_FLEET_MAP.md"

# H3, restated so nobody re-derives it from the wrong subsystem:
MEMORY_CLASSES = {
    "SEALED_REPLAY": {
        "gb": "6-15 (no month-arm RSS measurement exists; the 8.61 GB figure everyone quotes is a "
              "2-DAY fixture, and 15.32 GB is a second field of the same run, not a unit echo)",
        "parallel": "NEVER on this machine",
        "why": "H3: the peak is `v4_timewarp_simulated_live_research_loop.py`'s per-day row and "
               "attribution accumulation — 3,866 MB, 60.6 % of the Python heap. The source layer "
               "is 1.6 %. No source-layer work can move it, and Session G proved that by killing "
               "every source copy for no change in the arm.",
    },
    "WALKFORWARD": {
        "gb": "< 2", "parallel": "safe",
        "why": "the walkforward drivers read AA's estate (a 20 MB gzip) and resimulate over "
               "in-memory bar series; they never touch the sealed replay engine",
    },
    "ARITHMETIC": {"gb": "< 0.5", "parallel": "safe",
                   "why": "reads committed artifacts and recomputes; no bars, no engine"},
    "CAPTURE": {"gb": "n/a", "parallel": "n/a",
                "why": "I/O and host-bound; the constraint is a read-only export ceremony or a "
                       "vendor feed, not this machine"},
}

FLEET: list[dict] = [
    # ---------------------------------------------------------------------------------
    # the cheap arithmetic that unblocks other people's work
    # ---------------------------------------------------------------------------------
    {
        "id": "F1",
        "title": "Rebuild the four downstream artifacts on `sub_mid_dn_revert`'s repaired clock",
        "raised_by": "AQ handoff 4; REPAIR_QUEUE `REBUILD_THE_DOWNSTREAM_ARTIFACTS_ON_THE_"
                     "REPAIRED_CLOCK`",
        "driver": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_estate_v2.py",
        "input": "phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz (exists, 503 -> 533 trades)",
        "machine_hours": 0.5,
        "mh_basis": "AQ measured it: ~2 min for AA_ESTATE_WALK, ~27 min for EXIT_FRONTIER_V1, "
                    "then arithmetic",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "none directly — it removes a BY-HAND SUBSTITUTION three sessions have "
                         "now had to remember, and an armed sleeve's published economics are "
                         "currently on the defect clock. The next session that forgets the "
                         "substitution publishes a wrong number about live money.",
        "value": 4,
        "value_basis": "`sub_mid_dn_revert` is ARMED. Four artifacts (AA_ESTATE_WALK, "
                       "EXIT_FRONTIER_V1, AD_CARRY_TIERS_RESTATED_V1, SURVIVOR_BOOK_V1) describe "
                       "it on a population the repair superseded.",
        "blocked_by": None,
    },
    {
        "id": "F2",
        "title": "Restamp `SLEEVE_DOSSIER_V1.json`'s `time_stop_bars_m15` and its three derived "
                 "fields",
        "raised_by": "AQ completeness sweep; REPAIR_QUEUE `THE_ONE_TRUTH_PER_SLEEVE_ARTIFACT_IS_"
                     "STALE_ON_THE_REPAIRED_FIELD`",
        "driver": "docs/audits/fable5-vision-audit-20260725/phase8/receipts/ai_sleeve_dossier.py",
        "input": "the repaired `execution_packets.py` (landed B1404)",
        "machine_hours": 0.2,
        "mh_basis": "regeneration of one JSON from source constants",
        "memory_class": "ARITHMETIC",
        "verdict_moved": "none — it repairs a CURRENT CLAIM that is false for 12 sleeves. There "
                         "are no code consumers of the old value, which is exactly why it is easy "
                         "to miss and easy to publish from.",
        "value": 3,
        "value_basis": "the one-truth-per-sleeve artifact is the thing sessions cite when they do "
                       "not want to read source; a false field there propagates silently",
        "blocked_by": None,
    },
    {
        "id": "F3",
        "title": "Re-gate the five favourable-accident `mx_*` sleeves at a deliberately short "
                 "horizon",
        "raised_by": "AQ handoff 3; REPAIR_QUEUE x5 `TIME_STOP_UNIT_REPAIRED_BUT_THE_ACCIDENT_"
                     "WAS_FAVOURABLE`",
        "driver": "docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_exit_sweep.py",
        "input": "AD's D1 time-stop grid already exists; it needs re-gating at RECORDED x bands "
                 "x the declared family instead of flat/ALL_ERAS/69",
        "machine_hours": 1.5,
        "mh_basis": "AQ's contract-truth grid was 507 ledger rows over both stages; this is a "
                    "subset of that shape on 5 sleeves",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "whether `mx_us100`, `mx_us500`, `mx_ger40`, `mx_us30`, `mx_nzdjpy` get "
                         "a SHORT horizon declared on evidence. Today they carry the research "
                         "horizon and five of ten were measurably BETTER under the one-bar "
                         "accident — up to -0.5913 R/day worse at the repaired value.",
        "value": 4,
        "value_basis": "the repair AQ landed is unit-correct and, for these five, economically "
                       "the wrong direction. That is a live spec that is right about units and "
                       "wrong about the number.",
        "blocked_by": None,
    },
    {
        "id": "F4",
        "title": "Re-gate `sub_xvol_pullback @ target_4R` at the ratified rule",
        "raised_by": "AS-2 (this session) — DELIVERED, see AS_EXIT_CONTRACT_ACTIVATION_V1.json",
        "driver": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                  "as_exit_contract_activation.py",
        "input": "AA's estate + AD's harness",
        "machine_hours": 0.4,
        "mh_basis": "measured this session",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "whether an ARMED sleeve's exit contract changes. AK measured this cell "
                         "at the flat band on ALL_ERAS at family 69 — none of which is the "
                         "standard that governs the estate.",
        "value": 5,
        "value_basis": "it is the only proposed change to an ARMED sleeve's live contract",
        "blocked_by": None,
        "status": "DONE_THIS_SESSION",
    },
    # ---------------------------------------------------------------------------------
    # the walkforward grid
    # ---------------------------------------------------------------------------------
    {
        "id": "F5",
        "title": "Walk `asian_fade`'s trailing-runner x time-stop interaction",
        "raised_by": "AQ handoff 5 — the largest single labelling error in the estate",
        "driver": None,
        "driver_note": "NEEDS WRITING. `ad_exit_sweep` has a `trailing_runner` family "
                       "(EXIT_FRONTIER_V1_TRAIL.json) but nobody has crossed it with the time "
                       "stop for this sleeve.",
        "input": "AA's estate `asian_fade` rows (1,319 trades) + the M15 series",
        "machine_hours": 2.0,
        "mh_basis": "one sleeve, a 2-D grid (trail gap x time stop); AK's 58-cell single-sleeve "
                    "frontier is the cost precedent",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "why `asian_fade`'s published figure is 0.8832 R/day better than its own "
                         "live contract with a truncation fraction of ZERO. The gap is not the "
                         "time stop cutting trades short — it is the trailing-runner contract "
                         "interacting with it, and nobody has walked that interaction anywhere.",
        "value": 4,
        "value_basis": "the mechanism is unknown and it is the estate's biggest labelling error; "
                       "`metal_session_reversion` is the same policy and the second-largest "
                       "(+0.3050)",
        "blocked_by": None,
    },
    {
        "id": "F6",
        "title": "Re-gate every published gate receipt at the sleeve's LIVE exit contract",
        "raised_by": "AR handoff 2; REPAIR_QUEUE `EVERY_GATE_RECEIPT_MUST_PUBLISH_REGIME_"
                     "INFLATION_AND_IN_SAMPLE__AND_RE_GATE_AT_THE_LIVE_EXIT`",
        "driver": None,
        "driver_note": "NEEDS WRITING — but the pattern exists twice (AQ's LIVE_TRUE contract "
                       "and AR's B1480-B1483 re-gate of its own winner), so it is a sweep over a "
                       "known shape rather than a new instrument.",
        "input": "the committed gate receipts + `SLEEVE_EXIT_PROFILES`",
        "machine_hours": 3.0,
        "mh_basis": "AR's single-arm re-gate at the live time stop moved +0.33980 -> +0.14557 "
                    "R/day; this is that, over the receipt corpus",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "RETROSPECTIVE as well as prospective. AR's own winner lost 58 % of its "
                         "measured advantage when re-gated at its registry parent's live time "
                         "stop (25.04 h, not the 1,920 h research ceiling), with 97 of 122 trades "
                         "truncated. Every published R/day for a sleeve with a binding live time "
                         "stop is suspect by the same argument.",
        "value": 5,
        "value_basis": "it is the one item that can change verdicts already published, and AQ's "
                       "Side-B table already found ten sleeves whose published economics describe "
                       "a contract the book does not run",
        "blocked_by": None,
    },
    {
        "id": "F7",
        "title": "The FVG family full-sample gate",
        "raised_by": "AS-3 commission; AP's energy transfer",
        "driver": None,
        "driver_note": "NEEDS WRITING. AP measured that the transfer bought coverage (100 %) and "
                       "robustness but NOT significance, and that the FVG residual is YEARS of "
                       "sample away.",
        "input": "AP's transfer artifacts",
        "machine_hours": 2.0,
        "mh_basis": "one family gate at the ratified rule x 4 bands",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "whether the FVG family reaches an admission. AP's own measurement says "
                         "the binding constraint is SAMPLE and that the residual is years — so "
                         "the honest expected outcome is a confirmed REJECT with a named sample "
                         "requirement, not an admission.",
        "value": 2,
        "value_basis": "downgraded deliberately: AP already measured that significance is the "
                       "binding gate and that no repair on this axis closes it. Running it buys a "
                       "documented floor, not a decision.",
        "blocked_by": "AP's transfer artifacts landing in a form the gate can read",
    },
    {
        "id": "F8",
        "title": "The four M15 sleeves whose live time stop binds",
        "raised_by": "AS-3 commission; AQ Side-B table",
        "driver": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_contract_truth.py",
        "driver_note": "the LIVE_TRUE contract stage already covers these; what is missing is the "
                       "exit-frontier sweep AT the live stop rather than the A/B against it",
        "input": "AA's estate",
        "machine_hours": 1.5,
        "mh_basis": "four sleeves through AK's 58-cell shape, minus the cells the live stop rules "
                    "out",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "whether `kz_london_crypto_low` (23.4 % truncated), `ny_crypto_momentum` "
                         "(37.0 %), `liq_asia_up_low_metal` (11.5 %) and `metal_session_reversion` "
                         "want a different stop. All four are default-off; none is armed.",
        "value": 2,
        "value_basis": "real truncation, but on default-off sleeves whose published economics are "
                       "all NEGATIVE already (-0.248 to -0.872 R/day live-true). The measurement "
                       "would refine a number nobody is going to act on.",
        "blocked_by": None,
    },
    {
        "id": "F9",
        "title": "Hour-01 entry members AQ's three-mechanism re-derivation does not cover",
        "raised_by": "AS-3 commission; AQ-2",
        "driver": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/aq_entry_hour_01.py",
        "input": "the matched FTMO M15 archive (2024+)",
        "machine_hours": 1.0,
        "mh_basis": "AQ ran 42 members x 3 hours x 4 bands x 2 bills in one stage",
        "memory_class": "WALKFORWARD",
        "verdict_moved": "essentially none, and this is the honest entry on this map. AQ gated 72 "
                         "arms and ZERO admitted, best p 0.3800 — an order of magnitude from the "
                         "rank-1 bar. The convention is a COST REPAIR worth taking and it is not "
                         "an edge; extending it to more members tests the same conclusion again.",
        "value": 1,
        "value_basis": "listed because the commission named it, priced at what it is worth. Do not "
                       "schedule this ahead of F1/F3/F6.",
        "blocked_by": None,
    },
    # ---------------------------------------------------------------------------------
    # capture — not this machine's time
    # ---------------------------------------------------------------------------------
    {
        "id": "F10",
        "title": "Stamp a verified `.timebase.json` on the four pre-2024 H1 files already in "
                 "`data/`",
        "raised_by": "AQ handoff 7 — the correction its own adversarial pass forced",
        "driver": None,
        "driver_note": "NEEDS WRITING; the verification is a session-boundary scan against "
                       "`broker_clock`, the same method that measured the +7 h rule over 81 weekly "
                       "boundaries per broker.",
        "input": "`data/` H1 series for GBPUSD, USDJPY (from 2022-01-03), GBPJPY, NZDUSD (from "
                 "2023-01-16)",
        "machine_hours": 1.0,
        "mh_basis": "AQ: 'a day's work, not a capture' — the machine time is small, the care is "
                    "not",
        "memory_class": "CAPTURE",
        "verdict_moved": "widens the ratified hour-01 convention's evidence by ~2 years on 4 of 14 "
                         "cohort symbols. Given F9's result (0 of 72 admit) this buys CONFIDENCE "
                         "in a convention already ratified, not a new admission.",
        "value": 2,
        "value_basis": "cheapest open capture item by a wide margin, and it closes a requirement "
                       "that was filed as far more expensive than it is",
        "blocked_by": None,
        "hazard": "these files carry NO sidecar, which is the F7 fail-closed rule "
                  "(`generation.py:229`) doing its job. Stamping one without verifying its clock "
                  "re-creates the three-hour offset this programme has already paid for once.",
    },
    {
        "id": "F11",
        "title": "The `bridge_ftmo_deep_h4_*` fetch",
        "raised_by": "CLAUDE.md §4 — 'the cheapest thing that would sharpen OD-3'",
        "driver": None,
        "driver_note": "ORCHESTRATOR EXECUTES. A generator re-run against "
                       "`data/mt5_research_exports/bridge_ftmo_deep_h4_*`, which is ABSENT from "
                       "this machine.",
        "input": "the absent export",
        "machine_hours": 2.0,
        "mh_basis": "a generator re-run, not a sealed window — CLAUDE.md is explicit about that "
                    "distinction",
        "memory_class": "CAPTURE",
        "verdict_moved": "recovers the exit index for the three CARRY_CONDITIONAL sleeves "
                         "(`metals_softband`, `vp_euidx_pocgrav`, `sub_mid_dn_revert`) whose "
                         "carry tier is still open on one account each. `sub_mid_dn_revert` is "
                         "ARMED, which is what moved this up the list since it was first filed.",
        "value": 4,
        "value_basis": "one of the three is now on live money; a carry tier that turns on an "
                       "unmeasured hold is a live exposure, not a research gap",
        "blocked_by": "the export is not on this machine",
    },
    {
        "id": "F12",
        "title": "Tick data for the nine undecidable BTCUSD quarters, 2018Q2-2025Q3",
        "raised_by": "MX_BTCUSD_CHALLENGE_DOSSIER §5; REPAIR_QUEUE "
                     "`ADMISSION_IS_BAND_CONDITIONAL_STAMP_IT`",
        "driver": None,
        "driver_note": "a capture, then `ah_spread_scan.py` re-run over the recovered quarters",
        "input": "vendor tick data for BTCUSD over nine quarters",
        "machine_hours": 3.0,
        "mh_basis": "capture plus a spread-model re-derivation; the existing scan over "
                    "263.9 M rows is the shape",
        "memory_class": "CAPTURE",
        "verdict_moved": "closes the band caveat on the estate's ONLY standing admission. 78 of "
                         "232 `mx_btcusd` trades sit in quarters the spread model itself calls "
                         "undecidable, one with a band spanning 204,058x, and the WHOLE band "
                         "sensitivity lives in those 78. It is also the only thing that could "
                         "move the `high` band from REJECT.",
        "value": 5,
        "value_basis": "the admission is published as 'admits at two of three bands'. This is what "
                       "makes it three, or proves it is two.",
        "blocked_by": "vendor tick availability for 2018-2025 BTCUSD",
    },
    # ---------------------------------------------------------------------------------
    # the sealed engine — priced so nobody schedules it by accident
    # ---------------------------------------------------------------------------------
    {
        "id": "F13",
        "title": "Finish the parked B7.5 campaign (April + May + March)",
        "raised_by": "CLAUDE.md §4 — PARKED 2026-07-27 with a price, banked first",
        "driver": "src/research_infra/b7_5_post_acceleration_runner.py",
        "driver_note": "invoked as `python3 -m src.research_infra.b7_5_post_acceleration_runner "
                       "run-arm` with the sealed contract, execution seal, source bundle, typed "
                       "and tick-sparse caches and prepared-day-pack root; see "
                       "`docs/audits/opus5-architecture-20260725/receipts/profile_day_harness.py` "
                       "for a working annotated invocation",
        "input": "the R2 contract, the execution seal, the sealed source bundle",
        "machine_hours": 36.0,
        "mh_basis": "MEASURED: April 16.5 + May ~2.7 + March 16.5, serial. +16.5 to re-run "
                    "January for comparability if any bound file has moved.",
        "memory_class": "SEALED_REPLAY",
        "verdict_moved": "the broad-V4 selection-sizing decomposition. Promotion is "
                         "ARITHMETICALLY NEAR-FORECLOSED: pooled must exceed +0.1 from a -0.152 "
                         "start, and all four January arms are negative.",
        "value": 1,
        "value_basis": "an expiring option, not a plan. It is on this map so that its cost is "
                       "visible next to a 0.5 MH item that moves an armed sleeve — 72x the "
                       "machine time for a verdict the evidence already points at.",
        "blocked_by": "TWO HARD CONDITIONS, both unmet: (1) the pooled promote/reject/inconclusive "
                      "evaluator DOES NOT EXIST anywhere — zero threshold keys in any Python — and "
                      "must be written and SEALED first; (2) the protocol seals the thresholds but "
                      "NOT the pooling weights. Running a window without both improvises the "
                      "terminal decision post-hoc.",
        "hazard": "the option EXPIRES at the first bound-file edit. Keep March outcome-unread — it "
                  "is the only untouched month for any future broad-family treatment and the "
                  "scarcest resource in the programme.",
    },
    {
        "id": "F14",
        "title": "The RESERVE account activation plan (the inactive FTMO)",
        "raised_by": "AS-3 commission; the owner's 'after a while when tested on the 2'",
        "driver": None,
        "driver_note": "a DECISION artifact, not a measurement. What it needs is a written "
                       "evidence gate, and this map's job is to say what that gate should be.",
        "input": "the post-arming record of the two live accounts",
        "machine_hours": 0.5,
        "mh_basis": "authoring, plus reading whatever telemetry exists at the time",
        "memory_class": "ARITHMETIC",
        "verdict_moved": "when the third account gets armed. The owner set the condition in words "
                         "('after a while when tested on the 2') and nothing has turned that into "
                         "a number.",
        "value": 3,
        "value_basis": "cheap, and it converts an owner intention into a checkable condition "
                       "before the moment anyone wants to act on it — which is the only time such "
                       "a condition can be written honestly",
        "blocked_by": None,
        "proposed_gate": "the RESERVE arms when BOTH live accounts have (a) >= 30 post-arming "
                         "fills each with no S1/S2 stop condition met, (b) a measured cost "
                         "deviation within the C1 tripwire on those fills, and (c) at least one "
                         "sleeve's post-arming R/day inside its own archive confidence band. "
                         "Until (a) is reachable the condition is UNCHECKABLE, and the fleet map "
                         "says so rather than proposing a date.",
    },
    {
        "id": "F15",
        "title": "Measure the live terminal's `copy_rates` ceiling before any `mx_*` sleeve arms",
        "raised_by": "AQ B1452; REPAIR_QUEUE `THE_REPAIRED_BUDGET_MAKES_THE_BACKSTOP_INERT_IF_"
                     "THE_FEED_IS_SHORT`",
        "driver": None,
        "driver_note": "ORCHESTRATOR EXECUTES on the host — a read-only `copy_rates` probe. It is "
                       "not a research measurement and it cannot be done from this machine.",
        "input": "the live MT5 terminals",
        "machine_hours": 0.2,
        "mh_basis": "one read-only probe per terminal",
        "memory_class": "CAPTURE",
        "verdict_moved": "whether `mx_btcusd` can be armed AT ALL. After the time-stop repair an "
                         "open `mx_*` position requests 7,744 M15 bars per tick; if the terminal "
                         "returns fewer than 7,680 closed bars the count can never reach the "
                         "budget and THE TIME STOP NEVER FIRES. The backstop degrades to INERT, "
                         "not late, and the wall-clock fallback does not catch it.",
        "value": 5,
        "value_basis": "it is a PRECONDITION of the next activation, it is the cheapest item on "
                       "this map, and getting it wrong arms a sleeve with no time stop at all",
        "blocked_by": None,
    },
]


def main() -> None:
    for m in FLEET:
        d = m.get("driver")
        m["driver_exists"] = bool(d and (REPO / d).is_file()) if d else False
        if d and not m["driver_exists"]:
            raise SystemExit(
                f"{m['id']} names a driver that does not exist: {d}. A fleet map that points at "
                f"missing files is a wish list; either fix the path or set driver=None with a "
                f"driver_note saying it needs writing.")
        m["value_per_machine_hour"] = round(m["value"] / m["machine_hours"], 3)

    order = sorted(FLEET, key=lambda m: (-m["value_per_machine_hour"], m["machine_hours"]))

    doc = {
        "schema": "gtos.program.fleet_map.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/as_fleet_map.py",
        "session": "AS", "blocks": "B1540-B1549",
        "what": "every banked-but-unrun measurement, with driver, machine-hours, memory class and "
                "the verdict it moves, ordered by value per machine-hour",
        "ordering_rule": "value / machine_hours, descending; ties broken by cheaper first. NOT by "
                         "how interesting the question is.",
        "memory_classes": MEMORY_CLASSES,
        "n_members": len(FLEET),
        "n_with_a_driver_on_disk": sum(1 for m in FLEET if m["driver_exists"]),
        "n_needing_a_driver_written": sum(1 for m in FLEET if not m.get("driver")),
        "total_machine_hours": round(sum(m["machine_hours"] for m in FLEET), 1),
        "total_machine_hours_excluding_the_parked_campaign":
            round(sum(m["machine_hours"] for m in FLEET if m["id"] != "F13"), 1),
        "order": [m["id"] for m in order],
        "members": {m["id"]: m for m in FLEET},
    }
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n")

    L = ["# The replay fleet map — every banked measurement, priced and ordered", ""]
    a = L.append
    a("Generated by `phase11/receipts/as_fleet_map.py`, which **checks every driver path on disk**")
    a("and refuses to write if one is missing. The distinction it enforces is the expensive one:")
    a(f"**{doc['n_with_a_driver_on_disk']} of {doc['n_members']} members have a driver that")
    a(f"exists**; {doc['n_needing_a_driver_written']} need one written first, and that is usually")
    a("the larger cost.")
    a("")
    a(f"**{doc['total_machine_hours']} machine-hours total, of which")
    a(f"{FLEET[[m['id'] for m in FLEET].index('F13')]['machine_hours']} is the parked B7.5")
    a(f"campaign.** Excluding it the whole remaining fleet is")
    a(f"**{doc['total_machine_hours_excluding_the_parked_campaign']} machine-hours** — less than")
    a("one sealed month-window.")
    a("")
    a("## The order")
    a("")
    a("| # | id | member | value | MH | value/MH | memory | driver |")
    a("|---:|---|---|---:|---:|---:|---|---|")
    for i, m in enumerate(order, 1):
        drv = "on disk" if m["driver_exists"] else ("**needs writing**" if not m.get("driver")
                                                   else "?")
        a(f"| {i} | **{m['id']}** | {m['title']} | {m['value']} | {m['machine_hours']} | "
          f"{m['value_per_machine_hour']} | `{m['memory_class']}` | {drv} |")
    a("")
    a("## Memory classes — H3, restated so nobody re-derives it from the wrong subsystem")
    a("")
    a("| class | GB | parallel | why |")
    a("|---|---|---|---|")
    for k, v in MEMORY_CLASSES.items():
        a(f"| `{k}` | {v['gb']} | {v['parallel']} | {v['why']} |")
    a("")
    a("## The members")
    a("")
    for m in order:
        a(f"### {m['id']} — {m['title']}")
        a("")
        a(f"**Value {m['value']}/5 · {m['machine_hours']} MH · {m['value_per_machine_hour']} "
          f"value/MH · `{m['memory_class']}`**"
          + ("  ·  **" + m["status"] + "**" if m.get("status") else ""))
        a("")
        a(f"- **Raised by:** {m['raised_by']}")
        a(f"- **Driver:** " + (f"`{m['driver']}` (exists)" if m["driver_exists"]
                               else f"*{m.get('driver_note', 'none')}*"))
        if m.get("driver") and m.get("driver_note"):
            a(f"- **Driver note:** {m['driver_note']}")
        a(f"- **Input:** {m['input']}")
        a(f"- **Machine-hours basis:** {m['mh_basis']}")
        a(f"- **Verdict it moves:** {m['verdict_moved']}")
        a(f"- **Why that value:** {m['value_basis']}")
        if m.get("blocked_by"):
            a(f"- **Blocked by:** {m['blocked_by']}")
        if m.get("hazard"):
            a(f"- **Hazard:** {m['hazard']}")
        if m.get("proposed_gate"):
            a(f"- **Proposed gate:** {m['proposed_gate']}")
        a("")
    a("## Three things this ordering says out loud")
    a("")
    a("**1. The cheapest item on the map is a precondition for the next activation.** F15 — a")
    a("read-only `copy_rates` probe on the two terminals, 0.2 MH — decides whether `mx_btcusd` can")
    a("be armed at all. After AQ's time-stop repair an open `mx_*` position asks for 7,744 M15 bars")
    a("a tick, and a short feed makes the time stop **inert** rather than late. Arming before that")
    a("probe is arming a sleeve whose backstop may not exist.")
    a("")
    a("**2. The parked campaign costs 72× the item that would move an armed sleeve.** F13 is")
    a("36 MH for a verdict the evidence already points at (pooled must exceed +0.1 from −0.152;")
    a("four negative January arms), and it cannot legally run until a pooled evaluator that **does")
    a("not exist anywhere** has been written and sealed. F1 is 0.5 MH and removes a by-hand")
    a("substitution three sessions have had to remember about an **armed** sleeve. Putting both on")
    a("one page is the point of the page.")
    a("")
    a("**3. The highest-value walkforward item is retrospective.** F6 re-gates published receipts")
    a("at each sleeve's live exit contract. AR's own winner lost 58 % of its measured advantage")
    a("that way, and AQ's Side-B table already found ten sleeves whose published economics describe")
    a("a contract the book does not run. This is the only item on the map that can change a number")
    a("already in front of the owner.")
    a("")
    a("## What is deliberately NOT on this map")
    a("")
    a("Anything whose verdict is already measured. The hour-01 convention (F9, value 1) is on it")
    a("only because the commission named it: AQ gated 72 arms at 0 admits with a best p of 0.3800,")
    a("so extending it tests the same conclusion again. Breadth as the estate's cure is not on the")
    a("map at all — AF refuted it over 246 members and 134,027 trades, and re-running a refutation")
    a("is not a measurement.")
    OUT_MD.write_text("\n".join(L) + "\n")

    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    print(f"wrote {OUT_MD.relative_to(REPO)}")
    print(f"  {doc['n_members']} members, {doc['total_machine_hours']} MH total "
          f"({doc['total_machine_hours_excluding_the_parked_campaign']} excluding F13)")
    for i, m in enumerate(order[:5], 1):
        print(f"  {i}. {m['id']} {m['value_per_machine_hour']:>6} value/MH — {m['title'][:60]}")


if __name__ == "__main__":
    main()
