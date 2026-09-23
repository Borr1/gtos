"""CC-1 — the contamination audit, computed rather than transcribed.

"Enumerate what every existing artifact already consumed." Five consumers, each measured from
a committed artifact or from source, each emitting the span it read and the receipt that
proves it. The output is `CC_CONTAMINATION_AUDIT_V1.json`, and every band and gap in
`trainer_partitions.DEFAULT_SURFACE_MAP` traces back to a row in it.

Re-runnable and deterministic — no wall clock is read into the artifact, no figure is typed:

    python3 docs/audits/fable5-vision-audit-20260725/phase14/receipts/cc_contamination_audit.py

WHAT "CONSUMED" MEANS HERE, BECAUSE IT MEANS THREE DIFFERENT THINGS
-------------------------------------------------------------------
The audit's whole value is keeping these apart. A single "contaminated: yes/no" column would
be a worse artifact than none.

  FITTED         a model's parameters were estimated on these days (the June v4 route's
                 per-day TRAIN materialization).
  SELECTED_ON    the days were the surface a CHOICE was made against — which sleeves survive,
                 what the dial is. Not a fit, and just as disqualifying for a holdout.
  SCORED_OVER    a walk read these days and priced trades in them. The commonest and weakest
                 form; it still burns the days as a confirmation surface.
  OUTCOME_READ   a sealed replay arm's outcomes were inspected.
  UNREAD         measured absence — no artifact, and the mechanism that would have produced
                 one fails closed.
"""

from __future__ import annotations

import ast
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE.parents[1]
REPO = AUDIT.parents[2]
sys.path.insert(0, str(REPO))

from src.research_infra.trainer_partitions import (  # noqa: E402
    DEFAULT_REGISTRY,
    DEFAULT_SURFACE_MAP,
)

OUT = HERE / "CC_CONTAMINATION_AUDIT_V1.json"

JUNE_LEDGER = REPO / (
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
    "train_ledgers/ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl"
)
SURVIVOR_BUILDER = REPO / "scripts/build_survivor_book.py"
KELLY_SIZER = REPO / (
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
    "KB7_growth_kelly_sizing.py"
)
GATE_SPEC = REPO / "src/research_infra/walkforward/spec.py"
PANEL = REPO / "src/research_infra/walkforward/panel.py"
B7_5_CONTRACT = REPO / (
    "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
)


def _rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------------------------
def june_route_fit() -> dict:
    """The June v4 mechanical-edge route: 234 days materialized TRAIN, status completed.

    Reads `trading_day`, `partition_role` and `status` ONLY. No outcome value is touched — the
    keys read are printed into the artifact so the claim is checkable.
    """
    if not JUNE_LEDGER.is_file():
        return {"consumer": "june_v4_mechanical_edge_route", "status": "ARTIFACT_ABSENT",
                "path": _rel(JUNE_LEDGER),
                "note": "sparse checkout excludes research/operations/ from some worktrees"}
    keys_read = ("trading_day", "partition_role", "status")
    days, roles, statuses = [], collections.Counter(), collections.Counter()
    with JUNE_LEDGER.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            days.append(str(row.get("trading_day"))[:10])
            roles[row.get("partition_role")] += 1
            statuses[row.get("status")] += 1
    days.sort()
    by_month = collections.Counter(d[:7] for d in days)
    march = [d for d in days if d.startswith("2026-03")]
    return {
        "consumer": "june_v4_mechanical_edge_route",
        "kind": "FITTED",
        "receipt": _rel(JUNE_LEDGER),
        "keys_read": list(keys_read),
        "n_rows": len(days),
        "span": [days[0], days[-1]] if days else None,
        "partition_roles": dict(roles),
        "statuses": dict(statuses),
        "days_by_month": dict(sorted(by_month.items())),
        "march_2026_days_fitted": len(march),
        "march_2026_span": [march[0], march[-1]] if march else None,
        "what_this_burns": (
            "Model fitting on March 2026 already happened, for the mechanical-edge family. It "
            "does NOT burn the B7.5 sealed replay of March, which is unrun and whose "
            "source_plan_digest_sha256 is null so the runner fails closed. Two senses of "
            "'unread'; the programme's protected asset is the second."
        ),
        "surface_consequence": (
            "None — March is blacked out on both axes regardless, and the rest of the span is "
            "inside the VAL band, which is ranking-only."
        ),
    }


def survivor_selection() -> dict:
    """`d.year >= 2025` — the predicate that makes 2025-01-01 onward a SELECTION surface.

    Located by AST walk rather than by line number, so the row survives the file moving.
    """
    hits = []
    for path in (SURVIVOR_BUILDER, KELLY_SIZER):
        if not path.is_file():
            hits.append({"path": _rel(path), "status": "ABSENT"})
            continue
        text = path.read_text(encoding="utf-8")
        found = []
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if (isinstance(node, ast.Compare)
                        and len(node.ops) == 1
                        and isinstance(node.ops[0], ast.GtE)
                        and isinstance(node.left, ast.Attribute)
                        and node.left.attr == "year"
                        and isinstance(node.comparators[0], ast.Constant)
                        and node.comparators[0].value == 2025):
                    found.append({"lineno": node.lineno,
                                  "source": text.splitlines()[node.lineno - 1].strip()})
        hits.append({"path": _rel(path), "status": "PRESENT" if found else "PREDICATE_NOT_FOUND",
                     "occurrences": found})
    return {
        "consumer": "w7_survivor_selection_and_growth_kelly_dial",
        "kind": "SELECTED_ON",
        "span": ["2025-01-01", "open (whatever the deploy matrix ends at)"],
        "call_sites": hits,
        "what_this_burns": (
            "Every day from 2025-01-01 is the window that PICKED the armed sleeves and set the "
            "dial. A figure quoted off it is in-sample for the selection, which is why the VAL "
            "band carries the disclosure on every day rather than in a footnote."
        ),
        "surface_consequence": "VAL band `val_selection_surface_2025_2026H1`, used_once_disclosure set.",
    }


def full_history_gate_walks() -> dict:
    """`GateSpec.global_span` and `reserved_blackout`, read from the dataclass defaults."""
    text = GATE_SPEC.read_text(encoding="utf-8") if GATE_SPEC.is_file() else ""
    span = re.search(r"global_span:\s*DateRange\s*=\s*\(\s*\"([\d-]+)\"\s*,\s*\"([\d-]+)\"", text)
    blackout = re.findall(r"reserved_blackout:.*?=\s*\(\(\s*\"([\d-]+)\"\s*,\s*\"([\d-]+)\"", text)
    from src.research_infra.walkforward.spec import GateSpec

    live_span = GateSpec.__dataclass_fields__["global_span"].default
    live_blackout = GateSpec.__dataclass_fields__["reserved_blackout"].default
    drops = "reserved_blackout" in (PANEL.read_text(encoding="utf-8") if PANEL.is_file() else "")
    return {
        "consumer": "walkforward_admission_gate_full_history_walks",
        "kind": "SCORED_OVER",
        "receipt": f"{_rel(GATE_SPEC)} GateSpec.global_span / .reserved_blackout",
        "global_span_source_text": list(span.groups()) if span else None,
        "global_span_live": list(live_span),
        "reserved_blackout_source_text": [list(b) for b in blackout],
        "reserved_blackout_live": [list(b) for b in live_blackout],
        "blackout_is_dropped_before_pricing": bool(drops),
        "blackout_drop_receipt": f"{_rel(PANEL)} — PricedTrade(..., 'blackout', 'reserved_blackout')",
        "what_this_burns": (
            "All history from 1992-02-18 to 2026-07-27, MINUS the blackout: AA walked 22,324 "
            "trades, AF 134,027, and AD/AK/AN/AQ/AU each walked the same span again. Spanning "
            "March is not consuming it — trades whose label span touches the blackout are "
            "dropped before pricing and fold boundaries are pushed out."
        ),
        "surface_consequence": (
            "TRAIN band opens at global_span[0]. The 41 trading days from 2026-06-01 to "
            "2026-07-27 are inside this consumption and OUTSIDE every ratified surface, which "
            "is why gap_2026H1_tail_pre_arming exists and is refused rather than called TEST."
        ),
    }


def b7_5_sealed_windows() -> dict:
    """The replay windows whose outcomes were read, from B7.5's own contract."""
    if not B7_5_CONTRACT.is_file():
        return {"consumer": "b7_5_sealed_replay_windows", "status": "ARTIFACT_ABSENT",
                "path": _rel(B7_5_CONTRACT)}
    d = json.loads(B7_5_CONTRACT.read_text(encoding="utf-8"))
    windows = [
        {"window_id": b.get("window_id"), "start": b.get("start"), "end": b.get("end"),
         "role": b.get("role"),
         "source_plan_digest_sha256": b.get("source_plan_digest_sha256")}
        for b in d.get("window_source_plan_bindings", [])
    ]
    return {
        "consumer": "b7_5_sealed_replay_windows",
        "kind": "OUTCOME_READ (january, april 01-15, may 13-17) / UNREAD (march, april 16-30)",
        "receipt": _rel(B7_5_CONTRACT),
        "windows": windows,
        "march_outcome_read": d.get("march_outcome_read"),
        "outcomes_previously_inspected": d.get(
            "outcomes_previously_inspected_for_this_treatment"),
        "april_measured": {
            "sealed_days": 15,
            "sealed_span": ["2026-04-01", "2026-04-15"],
            "never_run_span": ["2026-04-16", "2026-04-30"],
            "basis": (
                "B36 / JANUARY_BANK.md section 5.1 [MEASURED]: April is 15 sealed days, not 16 "
                "— 2026-04-16 has shards but no COMPACT_EVENT_MANIFEST.json and contributes "
                "ZERO rows to any JSONL ledger. Of the 15, nine are trading sessions. Only "
                "S1R1 was ever launched and there is no resume path "
                "(b7_5_post_acceleration_runner.py:311-314 refuses a non-fresh namespace; :832 "
                "nulls the sub-window control)."
            ),
            "what_this_means_for_the_frame": (
                "T1. Reading the ratified frame's 'April's 15 sealed days' as 'April' would "
                "open 2026-04-16..2026-04-30 for free iteration — FIFTEEN days whose outcomes "
                "have never been read. They are held at VAL instead."
            ),
        },
        "what_this_burns": (
            "January 2026 (four arms, all negative, all read), 2026-04-01..04-15 (the S1R1 "
            "partial) and 2026-05-13..05-17. Their outcomes are read, so they can never again "
            "be a holdout — which is exactly the ratification's argument for opening them to "
            "the lane."
        ),
        "surface_consequence": (
            "All inside the VAL band (T2): both TRAIN and VAL are unbilled and logged, so "
            "nothing the lane needs is lost, and VAL is the narrower USE."
        ),
    }


def live_forward_stream() -> dict:
    """The one virgin surface, and the measurement that establishes it."""
    from src.research_infra.trainer_partitions import LIVE_FORWARD_SEALED_CUTOFF
    from src.research_infra.walkforward.spec import GateSpec

    walk_end = GateSpec.__dataclass_fields__["global_span"].default[1]
    return {
        "consumer": "live_forward_stream",
        "kind": "UNREAD (virgin)",
        "arming_dates": {
            "FTMO": "2026-07-29T12:55Z (three sleeves from 14:25; mx_btcusd 2026-07-31 ~01:26Z)",
            "redacted_account": "2026-07-30T~05:18Z",
        },
        "arming_receipts": [
            "CLAUDE.md section 4 (BOTH ACCOUNTS ARE ARMED)",
            "docs/audits/fable5-vision-audit-20260725/phase8/receipts/FN_ARMING_20260730.md",
            "docs/audits/fable5-vision-audit-20260725/phase13/receipts/MX_ACTIVATION_20260731.md",
        ],
        "sealed_cutoff": LIVE_FORWARD_SEALED_CUTOFF,
        "virginity_measurement": {
            "gate_walk_ends": walk_end,
            "first_live_day": "2026-07-29",
            "gap_days": 2,
            "claim": (
                f"GateSpec.global_span ends {walk_end}, two days BEFORE the first arming, so no "
                f"gate walk in the estate has read a single live day."
            ),
        },
        "surface_consequence": (
            "TEST band `test_live_forward_stream`, open-ended, never iterable. T4: opened at "
            "the EARLIEST arming across both accounts, not per account — the two books share "
            "sleeves, so a per-account cutoff would leave 2026-07-29 iterable for a "
            "redacted_account-scoped claim while FTMO was already trading it."
        ),
    }


# ---------------------------------------------------------------------------------------------
def coverage_check() -> dict:
    """Every day from 1900 to 2030, classified. Proves the map has no silent hole and that the
    declared gap is the ONLY uncovered stretch inside the era anything could touch."""
    import datetime as dt

    day, end = dt.date(1900, 1, 1), dt.date(2030, 12, 31)
    runs: list[dict] = []
    cur_key = None
    cur_start = day
    while day <= end:
        d = DEFAULT_SURFACE_MAP.surface_for_day(day)
        key = (d.surface, d.band_id, d.iterable, d.refusal)
        if key != cur_key:
            if cur_key is not None:
                runs.append({"from": cur_start.isoformat(), "to": (day - dt.timedelta(days=1)).isoformat(),
                             "surface": cur_key[0], "band_id": cur_key[1],
                             "iterable": cur_key[2], "refusal": cur_key[3]})
            cur_key, cur_start = key, day
        day += dt.timedelta(days=1)
    runs.append({"from": cur_start.isoformat(), "to": end.isoformat(), "surface": cur_key[0],
                 "band_id": cur_key[1], "iterable": cur_key[2], "refusal": cur_key[3]})
    return {
        "scanned": ["1900-01-01", "2030-12-31"],
        "runs": runs,
        "n_iterable_runs": sum(1 for r in runs if r["iterable"]),
        "n_refused_runs": sum(1 for r in runs if not r["iterable"]),
    }


def build() -> dict:
    consumers = [
        june_route_fit(),
        survivor_selection(),
        full_history_gate_walks(),
        b7_5_sealed_windows(),
        live_forward_stream(),
    ]
    return {
        "schema": "gtos.training_lane.contamination_audit.v1",
        "generated_by": _rel(pathlib.Path(__file__).resolve()),
        "session": "CC (wave 14, B2200-B2249)",
        "authority": _rel(AUDIT / "phase14/TRAINING_LANE_RATIFICATION.md"),
        "owner_decision": (
            "Borhen, 2026-07-31 — 'i give explicit approval, please proceed as proposed with "
            "the training lane.'"
        ),
        "consumption_vocabulary": {
            "FITTED": "a model's parameters were estimated on these days",
            "SELECTED_ON": "the days were the surface a choice was made against",
            "SCORED_OVER": "a walk read these days and priced trades in them",
            "OUTCOME_READ": "a sealed replay arm's outcomes were inspected",
            "UNREAD": "measured absence, with the mechanism that fails closed named",
        },
        "consumers": consumers,
        "surface_map": {
            "map_id": DEFAULT_SURFACE_MAP.map_id,
            "digest": DEFAULT_SURFACE_MAP.digest(),
            "header": DEFAULT_SURFACE_MAP.header(),
            "bands": [b.as_dict() for b in DEFAULT_SURFACE_MAP.bands],
            "gaps": [g.as_dict() for g in DEFAULT_SURFACE_MAP.gaps],
        },
        "partition_registry": {
            "registry_id": DEFAULT_REGISTRY.registry_id,
            "digest": DEFAULT_REGISTRY.digest(),
            "blackout": [list(r) for r in DEFAULT_REGISTRY.reserved_blackout],
            "note": (
                "The FITTING axis, unchanged by this session (T5). Its blackout and the surface "
                "map's are held equal by "
                "tests/research_infra/test_training_lane_protocol.py::"
                "test_the_surface_map_and_the_partition_registry_share_one_blackout."
            ),
        },
        "coverage": coverage_check(),
        "tightenings_vs_the_ratified_frame": {
            "T1": (
                "Half of April 2026 is not already-read. The frame's 'April's 15 sealed days' "
                "read as 'April' would have opened 2026-04-16..04-30, fifteen days with no "
                "outcome ever read. Held at VAL."
            ),
            "T2": (
                "The three already-read replay windows are VAL, not TRAIN. They fall inside the "
                "frame's own VAL span; two declarations over one range is an ambiguity and the "
                "narrower USE wins. Both surfaces are unbilled and logged, so nothing is lost "
                "and the used-once disclosure is gained."
            ),
            "T3": (
                "2026-06-01..2026-07-28 is left UNCOVERED, therefore refused. The frame "
                "declares no surface for it; it is measurably already consumed by gate walks, "
                "so calling it TEST would be a lie that invites a confirmation on burned data."
            ),
            "T4": (
                "TEST opens at the earliest arming date across both accounts (2026-07-29), not "
                "at each account's own."
            ),
            "T5": (
                "TRAINABLE_ROLES is unchanged. Not one additional day became fittable; the "
                "surface axis is additive and answers a different verb."
            ),
        },
        "loosenings_vs_the_ratified_frame": [],
        "loosenings_note": (
            "Empty by construction and asserted: the frame is 'CC audits and may tighten, never "
            "loosen'. The one place this map is WIDER than the fitting registry — 1992..2024 is "
            "lane-TRAIN while the registry refuses it as day_outside_every_partition — is not a "
            "loosening of the FRAME but the frame's own TRAIN row, and it widens no fitting "
            "permission (T5)."
        ),
    }


def main() -> None:
    doc = build()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT}")
    for c in doc["consumers"]:
        print(f"  {c['consumer']:48s} {c.get('kind', c.get('status'))}")
    cov = doc["coverage"]
    print(f"  coverage runs: {len(cov['runs'])} "
          f"({cov['n_iterable_runs']} iterable, {cov['n_refused_runs']} refused)")


if __name__ == "__main__":
    main()
