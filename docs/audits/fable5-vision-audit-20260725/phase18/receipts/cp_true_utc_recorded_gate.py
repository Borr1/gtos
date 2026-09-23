#!/usr/bin/env python3
"""Run CP's declared true-UTC candidate through the frozen gate, fail closed.

The candidate factory mines *missed-opportunity diagnostics*.  Those rows are
not automatically trades: a planned entry price plus a net proxy does not say
whether an order filled, when it filled, when it exited, or which gross return
the frozen broker-cost layer must price.  This bridge therefore has an explicit
source contract.  It constructs ``TradeRecord`` objects only from rows carrying
an exact counterfactual fill classification and, for filled rows, the complete
fill/exit/gross/path tuple.  It never substitutes decision time for fill time,
planned entry for fill price, or net proxy for gross R.

Even when the source contract refuses, the script invokes the real frozen gate
with the V26 all-declared bill and RECORDED population stamped into the spec.
That preserves the independent generator-fidelity refusal in the authoritative
gate output instead of replacing it with session prose.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward import candidate_family, era_population  # noqa: E402
from src.research_infra.walkforward.gate import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402


SCHEMA = "gtos.session_cp.true_utc_recorded_gate.v1"
SLEEVE = "broad_v4_time_conditioned_ny_metals_long"
MEMBER = "cp_true_utc_ny_metals_long_v1"
FAMILY = "CANDIDATE_BOOK_V1"
CANDIDATE_ID = "1493e333da89dbd6"
SPEC_DIGEST = "0f4382260c4b5ba8b1acb03d624c5ecf51d8decb46f448fa1287327263631ff7"

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
DEFAULT_FACTORY_RESULT = HERE / "CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json"
DEFAULT_FAMILY = HERE / "CANDIDATE_FAMILY_V26.json"
DEFAULT_POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
DEFAULT_RAW_LEDGER = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/"
    "CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl"
)
DEFAULT_ORACLE = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/"
    "CJ_RECLOCKED_S0R0_V7_ORDERED_PATH_ORACLE_LEDGER.jsonl"
)
DEFAULT_OUTPUT = HERE / "CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json"

HOLDOUT_DAYS = frozenset(
    {
        "2026-01-21",
        "2026-01-22",
        "2026-01-23",
        "2026-01-26",
        "2026-01-27",
        "2026-01-28",
        "2026-01-29",
        "2026-01-30",
    }
)

# Fields required to classify a missed candidate as filled versus no-trade.
FILL_CLASSIFICATION_FIELDS = ("counterfactual_order_fill_status",)

# Fields required only after the row says it filled.  They map one-for-one to
# TradeRecord or bind the outcome path that supplied it.
FILLED_TRADE_FIELDS = (
    "counterfactual_order_fill_time_utc",
    "counterfactual_order_close_time_utc",
    "counterfactual_order_fill_price",
    "stop_loss",
    "opportunity_gross_r",
    "opportunity_close_reason",
    "terminal_outcome",
    "opportunity_path_scored",
    "path_index_source_sha256",
    "symbol",
    "side",
)


class GateBridgeRefusal(RuntimeError):
    """A declaration or source invariant failed closed."""


def stable_sha(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_utc(value: Any, field: str) -> dt.datetime:
    text = str(value or "").strip()
    if not text:
        raise GateBridgeRefusal(f"missing_{field}")
    parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise GateBridgeRefusal(f"naive_{field}:{text}")
    return parsed.astimezone(dt.timezone.utc)


def _filled_status(value: Any) -> bool | None:
    """True=filled, False=explicit no-trade, None=not classifiable."""

    text = str(value or "").strip().lower()
    if not text:
        return None
    if any(token in text for token in ("not_filled", "no_fill", "not_ordered")):
        return False
    if "filled" in text or text in {"fill", "executed", "entry_filled"}:
        return True
    return None


def _candidate_row(row: Mapping[str, Any]) -> bool:
    day = str(row.get("decision_time_utc") or "")[:10]
    return bool(
        day in HOLDOUT_DAYS
        and row.get("route_session") == "ny"
        and row.get("symbol") in {"XAGUSD", "XAUUSD"}
        and str(row.get("side") or row.get("direction") or "").upper() == "LONG"
    )


def load_candidate_rows(path: Path) -> list[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    rows: list[dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if _candidate_row(row):
                rows.append(row)
    return rows


def oracle_join_coverage(path: Path, rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Prove whether the retained executed-order oracle covers these missed rows."""

    rows = list(rows)
    wanted_canonical = {
        str(row.get("canonical_replay_candidate_instance_key") or "")
        for row in rows
        if row.get("canonical_replay_candidate_instance_key")
    }
    # CD's downstream pool projection does not retain the canonical key.  The
    # pair below is still unique in this exact candidate population (the receipt
    # reports its cardinality) and is used only to measure join coverage, never
    # to transfer outcome fields.
    wanted_pair = {
        (str(row.get("candidate_id") or ""), str(row.get("decision_time_utc") or ""))
        for row in rows
        if row.get("candidate_id") and row.get("decision_time_utc")
    }
    matched_canonical: set[str] = set()
    matched_pair: set[tuple[str, str]] = set()
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            total += 1
            key = str(row.get("canonical_replay_candidate_instance_key") or "")
            pair = (
                str(row.get("candidate_id") or ""),
                str(row.get("decision_time_utc") or ""),
            )
            if key in wanted_canonical:
                matched_canonical.add(key)
            if pair in wanted_pair:
                matched_pair.add(pair)
    denominator = len(wanted_canonical) if wanted_canonical else len(wanted_pair)
    joined = len(matched_canonical) if wanted_canonical else len(matched_pair)
    return {
        "oracle_rows": total,
        "join_identity": (
            "canonical_replay_candidate_instance_key"
            if wanted_canonical
            else "candidate_id+decision_time_utc"
        ),
        "candidate_keys": denominator,
        "candidate_keys_unique": denominator == len(rows),
        "joined_candidate_keys": joined,
        "coverage_fraction": round(joined / denominator, 8) if denominator else 0.0,
        "interpretation": (
            "The ordered-path oracle contains executed/selected paths only; a zero join "
            "cannot be interpreted as zero fills for missed candidates."
        ),
    }


def source_preflight(rows: Iterable[Mapping[str, Any]]) -> tuple[list[TradeRecord], dict[str, Any]]:
    rows = list(rows)
    records: list[TradeRecord] = []
    missing_classification = 0
    explicit_no_trade = 0
    filled_incomplete = 0
    filled_complete = 0
    missing_counts = {field: 0 for field in (*FILL_CLASSIFICATION_FIELDS, *FILLED_TRADE_FIELDS)}

    for row in rows:
        status = _filled_status(row.get("counterfactual_order_fill_status"))
        if status is None:
            missing_classification += 1
            missing_counts["counterfactual_order_fill_status"] += 1
            continue
        if status is False:
            explicit_no_trade += 1
            continue

        missing = [field for field in FILLED_TRADE_FIELDS if row.get(field) is None]
        if row.get("opportunity_path_scored") is not True and "opportunity_path_scored" not in missing:
            missing.append("opportunity_path_scored")
        if missing:
            filled_incomplete += 1
            for field in missing:
                missing_counts[field] += 1
            continue

        entry = _parse_utc(row["counterfactual_order_fill_time_utc"], "fill_time_utc")
        exit_ = _parse_utc(row["counterfactual_order_close_time_utc"], "close_time_utc")
        entry_price = float(row["counterfactual_order_fill_price"])
        stop_loss = float(row["stop_loss"])
        direction = 1 if str(row["side"]).upper() == "LONG" else -1
        records.append(
            TradeRecord(
                sleeve=SLEEVE,
                symbol=str(row["symbol"]),
                entry_utc=entry,
                exit_utc=exit_,
                direction=direction,
                sl_distance_price=abs(entry_price - stop_loss),
                entry_price=entry_price,
                r_gross=float(row["opportunity_gross_r"]),
                features={
                    "candidate_id": row.get("candidate_id"),
                    "decision_time_utc": row.get("decision_time_utc"),
                    "route_session": row.get("route_session"),
                    "opportunity_close_reason": row.get("opportunity_close_reason"),
                    "terminal_outcome": row.get("terminal_outcome"),
                    "path_index_source_sha256": row.get("path_index_source_sha256"),
                },
            )
        )
        filled_complete += 1

    full_population_exact = missing_classification == 0 and filled_incomplete == 0
    report = {
        "holdout_candidate_rows": len(rows),
        "holdout_days": sorted(HOLDOUT_DAYS),
        "fill_classification_missing_rows": missing_classification,
        "explicit_no_trade_rows": explicit_no_trade,
        "filled_complete_rows": filled_complete,
        "filled_incomplete_rows": filled_incomplete,
        "valid_trade_records": len(records),
        "missing_field_counts": {k: v for k, v in missing_counts.items() if v},
        "full_population_exact": full_population_exact,
        "substitution_policy": {
            "decision_time_as_fill_time": "FORBIDDEN",
            "planned_entry_as_fill_price": "FORBIDDEN",
            "net_proxy_as_gross_r": "FORBIDDEN",
            "assumed_holding_period": "FORBIDDEN",
        },
    }
    return (records if full_population_exact else []), report


def verify_declarations(factory_result: Path, family_path: Path) -> dict[str, Any]:
    result = json.loads(factory_result.read_text(encoding="utf-8"))
    survivor = next(
        (row for row in result.get("results", ()) if row.get("candidate_id") == CANDIDATE_ID),
        None,
    )
    if not survivor or survivor.get("train_survivor") is not True:
        raise GateBridgeRefusal("declared_survivor_missing_or_not_survivor")
    if survivor.get("spec_digest") != SPEC_DIGEST:
        raise GateBridgeRefusal("declared_survivor_spec_digest_drift")

    declared = candidate_family.load_candidate_family(family_path)
    family = declared.family(FAMILY)
    member = next((item for item in family.members if item.name == MEMBER), None)
    if member is None or member.look_taken is not True:
        raise GateBridgeRefusal("v26_member_missing_or_unbilled")
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_spec_digest": SPEC_DIGEST,
        "member": MEMBER,
        "family": FAMILY,
        "family_all_declared_size": family.size_for(candidate_family.ALL_DECLARED),
        "family_looks_taken_size": family.size_for(candidate_family.LOOKS_TAKEN),
        "family_declaration_sha256": declared.sha256,
    }


def build_receipt(
    *,
    pool: Path,
    raw_ledger: Path,
    oracle: Path,
    factory_result: Path,
    family_path: Path,
) -> dict[str, Any]:
    declaration = verify_declarations(factory_result, family_path)
    # The compact mining pool contains diagnostic-scoreable rows only.  It is
    # valid for the declared TRAIN mine and invalid as a gate population: using
    # it here would select on outcome availability.  The raw missed ledger is
    # therefore the holdout population of record; the pool is provenance only.
    mining_rows = load_candidate_rows(pool)
    rows = load_candidate_rows(raw_ledger)
    records, preflight = source_preflight(rows)
    preflight["mining_scoreable_pool_rows"] = len(mining_rows)
    preflight["gate_population_basis"] = (
        "all matching raw missed-opportunity rows before diagnostic-scoreability projection"
    )
    oracle_coverage = oracle_join_coverage(oracle, rows)

    base = OPTIONS["B_balanced"].with_(
        spec_id="cp_true_utc_ny_metals_long_recorded_mid",
        spread_band="mid",
        sleeve_symbol_allowlist={SLEEVE: ("XAGUSD", "XAUUSD")},
    )
    spec = candidate_family.with_declared_family(
        base,
        FAMILY,
        basis=candidate_family.ALL_DECLARED,
        declaration=family_path,
    )

    # RECORDED filtering cannot honestly run on missing records.  The population
    # rule still enters the frozen spec seal; the source refusal is separate.
    if preflight["full_population_exact"]:
        populations, spec, population_mix = era_population.apply(
            "RECORDED", {SLEEVE: records}, spec, account=spec.account, band="mid"
        )
        submitted = list(populations[SLEEVE])
        population_filter_executed = True
        population_filter_note = (
            "RECORDED was applied through walkforward.era_population before run_gate."
        )
    else:
        spec = era_population.spec_for("RECORDED", spec)
        submitted = []
        population_mix = {"kept": 0, "dropped": 0, "unpriceable": 0}
        population_filter_executed = False
        population_filter_note = (
            "No records were filterable; RECORDED is sealed into the spec and must be "
            "applied once exact records exist."
        )
    frozen = run_gate({SLEEVE: submitted}, spec)
    frozen_dict = frozen.as_dict()
    sleeve_result = frozen_dict["sleeves"][SLEEVE]

    source_ready = bool(preflight["full_population_exact"])
    fidelity_ready = bool(sleeve_result["gates"].get("fidelity", {}).get("pass"))
    status = (
        "FROZEN_GATE_EXECUTED"
        if source_ready and fidelity_ready
        else "FROZEN_GATE_NOT_EVALUABLE_SOURCE_AND_FIDELITY_CAPTURE_REQUIRED"
        if not source_ready and not fidelity_ready
        else "FROZEN_GATE_NOT_EVALUABLE_SOURCE_CAPTURE_REQUIRED"
        if not source_ready
        else "FROZEN_GATE_NOT_EVALUABLE_FIDELITY_CAPTURE_REQUIRED"
    )
    core = {
        "schema": SCHEMA,
        "session": "CP",
        "blocks": "B2850-B2899",
        "status": status,
        "surface": "JANUARY_HOLDOUT_OOS",
        "declaration": declaration,
        "source": {
            "training_mining_pool": str(pool),
            "training_mining_pool_sha256": file_sha256(pool),
            "holdout_gate_population_ledger": str(raw_ledger),
            "holdout_gate_population_ledger_sha256": file_sha256(raw_ledger),
            "scoreability_projection_used_for_gate_population": False,
            "oracle": str(oracle),
            "oracle_sha256": file_sha256(oracle),
            "factory_result": str(factory_result.relative_to(REPO)),
            "factory_result_sha256": file_sha256(factory_result),
            "family_declaration": str(family_path.relative_to(REPO)),
            "source_preflight": preflight,
            "oracle_join_coverage": oracle_coverage,
        },
        "gate_contract": {
            "option": "B_balanced",
            "alpha": spec.alpha,
            "population": "RECORDED",
            "spread_band": "mid",
            "family_basis": candidate_family.ALL_DECLARED,
            "spec_sha256": spec.seal(),
            "submitted_trade_records": len(submitted),
            "population_filter_executed": population_filter_executed,
            "population_mix": population_mix,
            "population_filter_note": population_filter_note,
        },
        "frozen_gate": frozen_dict,
        "capture_requirements": [
            {
                "id": "CP-CAPTURE-1",
                "requirement": (
                    "Generate the declared NY metals LONG policy as an executable candidate "
                    "population, not as missed-opportunity diagnostics, across untouched OOS "
                    "RECORDED eras."
                ),
            },
            {
                "id": "CP-CAPTURE-2",
                "requirement": (
                    "Persist exact counterfactual fill classification and, for every fill, "
                    "fill UTC/price, exit UTC, pre-cost gross R, terminal reason, and a "
                    "content-bound path source."
                ),
            },
            {
                "id": "CP-CAPTURE-3",
                "requirement": (
                    "Measure and register generator fidelity for " + SLEEVE +
                    " at the frozen 0.50 recall floor; a renamed broad diagnostic proxy is "
                    "not a fidelity measurement."
                ),
            },
            {
                "id": "CP-CAPTURE-4",
                "requirement": (
                    "Re-run this same V26 all-declared, RECORDED, B_balanced alpha 0.10 "
                    "spec without another graduation bill."
                ),
            },
        ],
        "admission_claim": False,
        "activation_claim": False,
        "march_2026_outcomes_read": False,
        "live_forward_test_read": False,
    }
    return {**core, "receipt_root_sha256": stable_sha(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--raw-ledger", type=Path, default=DEFAULT_RAW_LEDGER)
    parser.add_argument("--oracle", type=Path, default=DEFAULT_ORACLE)
    parser.add_argument("--factory-result", type=Path, default=DEFAULT_FACTORY_RESULT)
    parser.add_argument("--family", type=Path, default=DEFAULT_FAMILY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    receipt = build_receipt(
        pool=args.pool.resolve(),
        raw_ledger=args.raw_ledger.resolve(),
        oracle=args.oracle.resolve(),
        factory_result=args.factory_result.resolve(),
        family_path=args.family.resolve(),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "holdout_candidate_rows": receipt["source"]["source_preflight"]["holdout_candidate_rows"],
                "valid_trade_records": receipt["source"]["source_preflight"]["valid_trade_records"],
                "frozen_gate_summary": receipt["frozen_gate"]["summary"],
                "out": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
