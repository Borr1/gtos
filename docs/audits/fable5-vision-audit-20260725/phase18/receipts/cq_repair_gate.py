#!/usr/bin/env python3
"""Session CQ: bill and gate the one surviving path-complete repair family.

The frozen grid selected one predeclared cell: invert current-breaker re-entry,
hold entry fixed, target 5D, stop 0.25D. This driver does not search. It verifies
that exact materialized trade set, bills its already-logged selection once through
the training-lane graduation ratchet, applies the standing RECORDED population,
and calls the sealed B_balanced alpha-0.10 gate at FTMO mid-band costs.

The repaired identity has no direct live-recall measurement. Its pure per-bar
structure therefore receives only the register's conservative transferred-class
rate, never another sleeve's recall. The surviving fail-closed boundary is sample
coverage: one evaluable chronological fold where the frozen gate requires three.
A NOT_EVALUABLE result is an exact capture requirement, not permission to soften
the gate.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.training_lane.append_only import (  # noqa: E402
    atomic_write_json,
    read_rows,
)
from src.research_infra.training_lane.graduation import (  # noqa: E402
    DEFAULT_GRADUATION_LEDGER,
    Candidate,
    graduate,
)
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    DEFAULT_ITERATION_LEDGER,
    candidate_id,
    spec_digest,
)
from src.research_infra.walkforward import era_population  # noqa: E402
from src.research_infra.walkforward.gate import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402


AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUDIT / "phase18/receipts"
REPAIR_RECEIPT = HERE / "CQ_CURRENT_BREAKER_REPAIR_V1.json"
REPAIR_TRADES = HERE / "pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz"
BASE_DECLARATION = AUDIT / "phase15/receipts/CANDIDATE_FAMILY_V25.json"
OUT_DECLARATION = HERE / "CQ_CANDIDATE_FAMILY_V26.json"
OUT_GATE = HERE / "CQ_CURRENT_BREAKER_RATIFIED_GATE_V1.json"
COSTS = AUDIT / "phase17/activation_carry_live_cost_truth/files/BROKER_TRUE_COSTS_V1.json"

SCHEMA = "gtos-session-cq-current-breaker-ratified-gate-v1"
TRADE_SCHEMA = "gtos-session-cq-current-breaker-repair-trade-v1"
SLEEVE = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
TRANSFORM_ID = "cq_current_breaker_inverted_target_5d_stop_0p25d_v1"
EXPECTED_COST_SHA256 = "bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd"
LOOK_SPEC = {
    "kind": "frozen_geometry",
    "arm": "S0R0",
    "orientation": "inverted",
    "target_distance_D": 5.0,
    "stop_distance_D": 0.25,
}
LOOK_MECHANISM = "true_utc_path_complete_geometry"
LOOK_SLEEVE = "S0R0"


class CQGateRefusal(RuntimeError):
    """A binding, billing, or boundary check failed closed."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _self_bound(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stated = payload.get("self_sha256")
    actual = _canonical_sha256(
        {key: value for key, value in payload.items() if key != "self_sha256"}
    )
    if stated != actual:
        raise CQGateRefusal(f"self_hash_invalid:{path}:{stated}!={actual}")
    return payload


def _parse_utc(value: Any) -> dt.datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise CQGateRefusal(f"invalid_timestamp:{value}") from exc
    if parsed.tzinfo is None:
        raise CQGateRefusal(f"naive_timestamp:{value}")
    return parsed.astimezone(dt.timezone.utc)


def _load_repair_trades() -> tuple[list[TradeRecord], dict[str, Any]]:
    receipt = _self_bound(REPAIR_RECEIPT)
    expected = receipt.get("trade_records") or {}
    digest = _sha256_file(REPAIR_TRADES)
    if digest != expected.get("sha256"):
        raise CQGateRefusal(
            f"repair_trade_hash_mismatch:{digest}!={expected.get('sha256')}"
        )
    records: list[TradeRecord] = []
    source_keys: set[tuple[str, str]] = set()
    broker_symbols: set[str] = set()
    with gzip.open(REPAIR_TRADES, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CQGateRefusal(f"repair_trade_json_invalid:{line_number}") from exc
            if not isinstance(row, Mapping) or row.get("schema") != TRADE_SCHEMA:
                raise CQGateRefusal(f"repair_trade_schema_invalid:{line_number}")
            if (
                row.get("sleeve") != SLEEVE
                or row.get("candidate_transform_id") != TRANSFORM_ID
                or row.get("decision_split") not in {"TRAIN", "HOLDOUT"}
            ):
                raise CQGateRefusal(f"repair_trade_identity_invalid:{line_number}")
            entry = _parse_utc(row.get("entry_utc"))
            exit_utc = _parse_utc(row.get("exit_utc"))
            if not (
                entry.year == 2026
                and entry.month == 1
                and exit_utc.year == 2026
                and exit_utc.month == 1
                and entry < exit_utc <= entry + dt.timedelta(minutes=120)
            ):
                raise CQGateRefusal(f"repair_trade_time_boundary_invalid:{line_number}")
            key = (str(row.get("source_candidate_id") or ""), entry.isoformat())
            if not key[0] or key in source_keys:
                raise CQGateRefusal(f"repair_trade_join_key_invalid:{line_number}:{key}")
            source_keys.add(key)
            broker_symbol = str(row.get("broker_symbol") or "")
            if not broker_symbol:
                raise CQGateRefusal(f"repair_trade_broker_symbol_missing:{line_number}")
            broker_symbols.add(broker_symbol)
            records.append(
                TradeRecord(
                    sleeve=SLEEVE,
                    symbol=broker_symbol,
                    entry_utc=entry,
                    exit_utc=exit_utc,
                    direction=int(row["direction"]),
                    sl_distance_price=float(row["sl_distance_price"]),
                    entry_price=float(row["entry_price"]),
                    r_gross=float(row["r_gross"]),
                    features=dict(row.get("features") or {}),
                )
            )
    if len(records) != int(expected.get("rows") or -1):
        raise CQGateRefusal(
            f"repair_trade_count_mismatch:{len(records)}!={expected.get('rows')}"
        )
    return records, {
        "receipt_self_sha256": receipt["self_sha256"],
        "trade_file_sha256": digest,
        "rows": len(records),
        "unique_source_join_keys": len(source_keys),
        "broker_symbols": sorted(broker_symbols),
        "all_january_2026": True,
    }


def _look_provenance() -> dict[str, Any]:
    expected_id = candidate_id(
        mechanism=LOOK_MECHANISM,
        sleeve=LOOK_SLEEVE,
        spec=LOOK_SPEC,
    )
    expected_digest = spec_digest(LOOK_SPEC)
    matches = [
        row
        for row in read_rows(DEFAULT_ITERATION_LEDGER)
        if row.get("candidate_id") == expected_id
        and row.get("spec_digest") == expected_digest
        and row.get("session") == "CQ"
    ]
    if len(matches) != 1:
        raise CQGateRefusal(
            f"selected_look_provenance_count:{len(matches)}!=1:{expected_id}"
        )
    row = matches[0]
    if (
        row.get("surface") != "VAL"
        or bool(row.get("billed"))
        or row.get("spec") != LOOK_SPEC
        or (row.get("extra") or {}).get("cell_id")
        != "inverted|target_5D|stop_0.25D"
    ):
        raise CQGateRefusal("selected_look_provenance_boundary_invalid")
    if any(
        str(day).startswith(("2026-02", "2026-03"))
        for day in (row.get("date_span") or [])
    ):
        raise CQGateRefusal("selected_look_crosses_forbidden_month")
    return {
        "candidate_id": expected_id,
        "spec_digest": expected_digest,
        "surface": row["surface"],
        "billed_before_graduation": bool(row["billed"]),
        "date_span": row["date_span"],
        "receipt": row.get("receipt"),
        "look_id": (row.get("extra") or {}).get("look_id"),
        "selection_arm_sleeve": LOOK_SLEEVE,
        "gate_sleeve": SLEEVE,
        "identity_note": (
            "The declared look is keyed to frozen arm S0R0; its named population inside "
            "that look is CURRENT_BREAKER_RE_ENTRY. Graduation carries the resulting "
            "repair as its own gate sleeve without inventing a second selection look."
        ),
    }


def _graduate(provenance: Mapping[str, Any]):
    declaration = BASE_DECLARATION.relative_to(REPO)
    if OUT_DECLARATION.exists():
        existing = json.loads(OUT_DECLARATION.read_text(encoding="utf-8"))
        members = ((existing.get("families") or {}).get("CANDIDATE_BOOK_V1") or {}).get(
            "members"
        ) or []
        if not any(row.get("name") == SLEEVE for row in members):
            raise CQGateRefusal(
                f"existing_successor_missing_expected_member:{OUT_DECLARATION}"
            )
        declaration = OUT_DECLARATION.relative_to(REPO)
    candidate = Candidate(
        candidate_id=str(provenance["candidate_id"]),
        name=SLEEVE,
        sleeve=SLEEVE,
        spec_digest=str(provenance["spec_digest"]),
        basis=(
            "Session CQ's predeclared S0R0 true-UTC January path grid: inverted "
            "current-breaker re-entry, fixed entry, target 5D, stop 0.25D."
        ),
        source=str(REPAIR_RECEIPT.relative_to(REPO)),
        proposed_by="Session CQ",
        note=(
            "Selected from all 198 declared cells only after requiring positive net "
            "economics on both the frozen TRAIN and HOLDOUT partitions."
        ),
    )
    return graduate(
        candidate,
        family_id="CANDIDATE_BOOK_V1",
        basis="all_declared",
        declaration=declaration,
        out_declaration=OUT_DECLARATION.relative_to(REPO),
        declared_at="2026-08-01",
        session="Session CQ (wave 18)",
        blocks="B2900-B2949",
        why=(
            "One already-logged repair hypothesis reaches the ratified gate. This bills "
            "exactly one look; the other 197 geometry cells and three mechanism looks "
            "remain unbilled VAL exploration."
        ),
    )


def _write_result(payload: dict[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body["self_sha256"] = _canonical_sha256(body)
    atomic_write_json(OUT_GATE, body, indent=1)
    return body


def main() -> int:
    # The training-lane biller deliberately preserves the path spelling it receives.
    # Run from the repository root so the canonical ledger stays portable even when
    # this driver itself is invoked by absolute path from another working directory.
    os.chdir(REPO)
    records, trade_binding = _load_repair_trades()
    provenance = _look_provenance()
    graduation = _graduate(provenance)

    costs_sha256 = _sha256_file(COSTS)
    if costs_sha256 != EXPECTED_COST_SHA256:
        raise CQGateRefusal(
            f"broker_true_cost_artifact_drift:{costs_sha256}!={EXPECTED_COST_SHA256}"
        )
    costs = load_broker_true_costs(COSTS)
    base = OPTIONS["B_balanced"].with_(
        spec_id="wf_gate_option_B_balanced_cq_current_breaker_repair_mid",
        account="FTMO",
        cost_artifact_sha256=costs_sha256,
        spread_band="mid",
        sleeve_symbol_allowlist={SLEEVE: tuple(trade_binding["broker_symbols"])},
    )
    spec = graduation.apply_to_spec(base)
    population, spec, population_mix = era_population.apply(
        "RECORDED",
        {SLEEVE: records},
        spec,
        account="FTMO",
        band="mid",
    )
    gate = run_gate(
        population,
        spec,
        costs=costs,
        diagnose=True,
        server="FTMO-Server3",
    )
    gate_result = gate.as_dict()
    verdict = gate_result["sleeves"].get(SLEEVE) or {}
    member_graduations = [
        row
        for row in read_rows(DEFAULT_GRADUATION_LEDGER)
        if row.get("member_name") == SLEEVE
        and row.get("family_id") == "CANDIDATE_BOOK_V1"
    ]
    total_billed_looks = sum(int(row.get("billed_looks") or 0) for row in member_graduations)
    if total_billed_looks != 1:
        raise CQGateRefusal(
            f"repair_graduation_bill_count:{total_billed_looks}!=1"
        )
    if verdict.get("verdict") == "ADMIT":
        ceremony = {
            "status": "QUEUE_ELIGIBLE_NOT_ARMED",
            "queue": "orchestrator activation-candidate ceremony queue",
            "arming_authority": False,
        }
    else:
        ceremony = {
            "status": "NOT_QUEUED",
            "reason": verdict.get("reasons") or ["no admitting verdict"],
            "arming_authority": False,
        }
    result = _write_result(
        {
            "schema": SCHEMA,
            "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
            "source_head": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip(),
            "surface": "VAL_TO_RATIFIED_GATE",
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "broker_live_authority": False,
            "broker_module_imported": False,
            "token_bound_config_bytes_read": False,
            "repair_trade_binding": trade_binding,
            "selected_look_provenance": provenance,
            "graduation": {
                **graduation.as_dict(),
                "billed_looks_this_call": graduation.billed_looks,
                "total_billed_looks_for_member": total_billed_looks,
                "member_graduation_rows": len(member_graduations),
                "graduation_ledger": str(Path(DEFAULT_GRADUATION_LEDGER).relative_to(REPO)),
                "graduation_ledger_sha256": _sha256_file(Path(DEFAULT_GRADUATION_LEDGER)),
                "successor_declaration": str(OUT_DECLARATION.relative_to(REPO)),
            },
            "gate_contract": {
                "population": "RECORDED",
                "option": "B_balanced",
                "alpha": 0.10,
                "multiplicity_basis": "CANDIDATE_BOOK_V1/all_declared",
                "spread_band": "mid",
                "account": "FTMO",
                "server_clock": "FTMO-Server3",
                "cost_artifact": str(COSTS.relative_to(REPO)),
                "cost_artifact_sha256": costs_sha256,
                "population_mix": population_mix,
                "records_before_population": len(records),
                "records_after_population": len(population.get(SLEEVE, ())),
            },
            "gate_result": gate_result,
            "repair_queue": gate.repair_queue(
                server="FTMO-Server3",
                run_label="Session CQ current-breaker path-complete repair",
                extra={
                    "population": "RECORDED",
                    "spread_band": "mid",
                    "candidate_transform_id": TRANSFORM_ID,
                },
            ),
            "ceremony": ceremony,
            "status": (
                "RATIFIED_GATE_ADMIT_NOT_ARMED"
                if verdict.get("verdict") == "ADMIT"
                else "RATIFIED_GATE_NOT_EVALUABLE_OR_REJECTED"
            ),
        }
    )
    print(
        json.dumps(
            {
                "output": str(OUT_GATE.relative_to(REPO)),
                "self_sha256": result["self_sha256"],
                "candidate_family_size": graduation.declared_family_size,
                "candidate_family_looks": graduation.looks_taken_size,
                "billed_looks": graduation.billed_looks,
                "population_mix": population_mix,
                "verdict": verdict.get("verdict"),
                "reasons": verdict.get("reasons"),
                "ceremony": ceremony["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
