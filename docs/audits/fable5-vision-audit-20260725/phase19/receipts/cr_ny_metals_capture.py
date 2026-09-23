#!/usr/bin/env python3
"""Session CR: close CP's fidelity gap and fail closed on incomplete path capture.

This is an offline research tool.  It authenticates the already-declared V27 candidate,
measures generator recall by identity against CJ's independently emitted January semantic
rerun, registers that measurement under an explicit ``replay_reference`` stamp, and checks
whether an exact all-era RECORDED executable population exists before the frozen gate may
run.

The boundary is deliberately stronger than a post-parse filter: a JSONL line's declared day
is extracted from text before ``json.loads`` is called.  February and March lines therefore
raise before any economic field on the line can be decoded.  The current inputs are explicit
January-only paths; no directory discovery is used.

This tool never imports a broker module, reads config, contacts a VPS, or invokes ``run_gate``
on a partial population.  Its current NOT_EVALUABLE result is a source-contract verdict, not
an economic look.  Once a complete broad-V4 capture exists, the same V27 spec seal recorded
here is the gate to invoke without another graduation bill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.train_engine import cuts  # noqa: E402
from src.research_infra.walkforward import candidate_family, era_population  # noqa: E402
from src.research_infra.walkforward.fidelity import (  # noqa: E402
    FidelityClass,
    FidelityReference,
    clear_direct_fidelity_measurements,
    register_direct_fidelity_measurement,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402


SCHEMA = "gtos.session_cr.ny_metals_capture_result.v1"
FIDELITY_SCHEMA = "gtos.session_cr.generator_fidelity.v1"
MEMBER = "cp_true_utc_ny_metals_long_v1"
SLEEVE = "broad_v4_time_conditioned_ny_metals_long"
FAMILY = "CANDIDATE_BOOK_V1"
CANDIDATE_ID = "1493e333da89dbd6"
SPEC_DIGEST = "0f4382260c4b5ba8b1acb03d624c5ecf51d8decb46f448fa1287327263631ff7"
FROZEN_OPTION = "B_balanced"
FROZEN_BAND = "mid"
FROZEN_ALPHA = 0.10
FIDELITY_FLOOR = 0.50

AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUDIT / "phase19/receipts"
DEFAULT_PROTOCOL = HERE / "CR_NY_METALS_CAPTURE_PROTOCOL_V1.json"
DEFAULT_FIDELITY = HERE / "CR_GENERATOR_FIDELITY_V1.json"
DEFAULT_OUTPUT = HERE / "CR_NY_METALS_CAPTURE_RESULT_V1.json"
DEFAULT_CP_GATE_RECEIPT = (
    AUDIT / "phase18/receipts/CP_TRUE_UTC_NY_METALS_LONG_RECORDED_GATE_V1.json"
)
DEFAULT_FAMILY = AUDIT / "phase18/receipts/CANDIDATE_FAMILY_V27.json"
DEFAULT_RAW_LEDGER = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/"
    "CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl"
)
DEFAULT_SEMANTIC_LEDGER = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7.semantic-diagnostic/"
    "CJ_RECLOCKED_S0R0_V7_SEMANTIC_CANDIDATE_LEDGER.jsonl"
)
DEFAULT_JANUARY_MANIFEST = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/"
    "manifests/january_2026.json"
)
SPREAD_MODEL_GIT_PATH = (
    "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
)

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
POLICY_SYMBOLS = frozenset({"XAGUSD", "XAUUSD"})

# Only an identity/time field is needed to decide whether decoding a line is permitted.
# Both CJ ledgers put one of these fields on every row.  The regex runs on the raw line,
# before a JSON decoder could expose any outcome field.
_DAY_RE = re.compile(
    r'"(?:decision_time_utc|trading_day)"\s*:\s*"(\d{4}-\d{2}-\d{2})'
)

CAPTURE_CLASSIFICATION_FIELDS = (
    "entry_fill_executable",
    "fill_realism_class",
)
CAPTURE_FILLED_FIELDS: dict[str, tuple[str, ...]] = {
    "fill_utc": ("counterfactual_order_fill_time_utc", "limit_first_fill_time_utc"),
    "fill_price": ("counterfactual_order_fill_price", "limit_first_entry_price"),
    "exit_utc": (
        "opportunity_close_time_utc",
        "profit_harvest_policy_close_time_utc",
        "selected_execution_policy_replay_exit_time_utc",
        "counterfactual_order_close_time_utc",
    ),
    "pre_cost_gross_r": ("opportunity_gross_r", "exit_composition_terminal_gross_r"),
    "terminal_reason": ("opportunity_close_reason", "terminal_outcome"),
    "path_source": ("path_index_source_path", "path_source"),
    "path_sha256": ("path_index_source_sha256",),
}


class CRCaptureRefusal(RuntimeError):
    """A safety boundary, declaration, or evidence contract failed closed."""


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
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


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _write_rooted_json(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    payload["content_sha256"] = canonical_sha256(payload)
    rendered = json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
    return payload


def declared_day_before_decode(line: str, *, context: str) -> str:
    """Extract and authorize a line's day before any JSON outcome can be decoded."""
    match = _DAY_RE.search(line)
    if match is None:
        raise CRCaptureRefusal(f"date_not_visible_before_decode:{context}")
    day = match.group(1)
    if day.startswith("2026-02"):
        raise CRCaptureRefusal(f"february_economics_forbidden_before_decode:{context}:{day}")
    if day.startswith("2026-03"):
        raise CRCaptureRefusal(f"march_outcomes_forbidden_before_decode:{context}:{day}")
    if not day.startswith("2026-01"):
        raise CRCaptureRefusal(f"non_january_input_refused_before_decode:{context}:{day}")
    return day


def decode_january_line(line: str, *, context: str) -> dict[str, Any]:
    day = declared_day_before_decode(line, context=context)
    row = json.loads(line)
    decoded_day = str(row.get("decision_time_utc") or row.get("trading_day") or "")[:10]
    if decoded_day != day:
        raise CRCaptureRefusal(
            f"predecode_and_decoded_day_disagree:{context}:{day}!={decoded_day}"
        )
    return row


def load_january_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise CRCaptureRefusal(f"january_source_missing:{path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            rows.append(
                decode_january_line(line, context=f"{path.name}:{line_number}")
            )
    return rows


def is_policy_candidate(row: Mapping[str, Any]) -> bool:
    day = str(row.get("decision_time_utc") or "")[:10]
    return bool(
        day in HOLDOUT_DAYS
        and row.get("route_session") == "ny"
        and row.get("symbol") in POLICY_SYMBOLS
        and str(row.get("side") or row.get("direction") or "").upper() == "LONG"
    )


def candidate_identity(row: Mapping[str, Any]) -> tuple[str, str]:
    candidate = str(row.get("candidate_id") or "")
    decision = str(row.get("decision_time_utc") or "")
    if not candidate or not decision:
        raise CRCaptureRefusal("candidate_identity_incomplete")
    return candidate, decision


def measure_generator_fidelity(
    reference_rows: Sequence[Mapping[str, Any]],
    semantic_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    reference = [row for row in reference_rows if is_policy_candidate(row)]
    reference_ids = [candidate_identity(row) for row in reference]
    if len(set(reference_ids)) != len(reference_ids):
        raise CRCaptureRefusal("reference_candidate_identity_not_unique")

    semantic_holdout = [
        row
        for row in semantic_rows
        if str(row.get("decision_time_utc") or row.get("trading_day") or "")[:10]
        in HOLDOUT_DAYS
    ]
    semantic_identity_rows = [candidate_identity(row) for row in semantic_holdout]
    semantic_ids = set(semantic_identity_rows)
    if len(semantic_ids) != len(semantic_identity_rows):
        raise CRCaptureRefusal("semantic_candidate_identity_not_unique")
    agreed = sum(identity in semantic_ids for identity in reference_ids)
    reference_only = len(reference_ids) - agreed
    semantic_fields = sorted({key for row in semantic_holdout for key in row})
    policy_fields = {"route_session", "symbol", "side", "direction"}
    precision_supported = policy_fields.issubset(semantic_fields)
    if len(reference_ids) != 249:
        raise CRCaptureRefusal(
            f"cp_reference_population_drift:{len(reference_ids)}!=249"
        )
    return {
        "identity": ["candidate_id", "decision_time_utc"],
        "reference_rows": len(reference_ids),
        "reference_unique_identities": len(set(reference_ids)),
        "semantic_holdout_rows": len(semantic_holdout),
        "semantic_holdout_unique_identities": len(semantic_ids),
        "agreed": agreed,
        "reference_only": reference_only,
        "reference_recall": agreed / len(reference_ids),
        "generated_only": None,
        "precision": None,
        "precision_supported": precision_supported,
        "semantic_projection_fields": semantic_fields,
        "caveat": (
            "Direct deterministic generator-recall measurement against an independently "
            "emitted replay-reference artifact from the same code lineage. It is not a "
            "live-record comparison and does not establish generator correctness. The "
            "semantic projection omitted the CP policy fields, so generated-only precision "
            "cannot be filtered honestly and is not imputed."
        ),
    }


def assess_executable_capture(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    missing_classification = Counter()
    missing_filled = Counter()
    filled = 0
    no_fill = 0
    class_counts: Counter[str] = Counter()
    for row in rows:
        executable = row.get("entry_fill_executable")
        if not isinstance(executable, bool):
            missing_classification["entry_fill_executable"] += 1
            continue
        realism = str(row.get("fill_realism_class") or "")
        if not realism:
            missing_classification["fill_realism_class"] += 1
        else:
            class_counts[realism] += 1
        if not executable:
            no_fill += 1
            continue
        filled += 1
        for label, alternatives in CAPTURE_FILLED_FIELDS.items():
            if not any(row.get(field) is not None for field in alternatives):
                missing_filled[label] += 1

    classification_complete = not missing_classification
    filled_tuple_complete = not missing_filled
    return {
        "candidate_rows": len(rows),
        "classification": {
            "complete": classification_complete,
            "filled": filled,
            "no_fill": no_fill,
            "missing": dict(sorted(missing_classification.items())),
            "fill_realism_classes": dict(sorted(class_counts.items())),
        },
        "filled_trade_tuple": {
            "complete": filled_tuple_complete,
            "required": {key: list(value) for key, value in CAPTURE_FILLED_FIELDS.items()},
            "missing_rows_by_requirement": dict(sorted(missing_filled.items())),
        },
        "row_contract_complete": classification_complete and filled_tuple_complete,
    }


def verify_declaration(cp_gate_receipt: Path, family_path: Path) -> dict[str, Any]:
    """Authenticate CP through its commissioned gate receipt, never its VAL/factory estate."""
    cp_gate = json.loads(cp_gate_receipt.read_text(encoding="utf-8"))
    if cp_gate.get("schema") != "gtos.session_cp.true_utc_recorded_gate.v1":
        raise CRCaptureRefusal("cp_gate_receipt_schema_drift")
    cp_declaration = cp_gate.get("declaration") or {}
    if cp_declaration.get("candidate_id") != CANDIDATE_ID:
        raise CRCaptureRefusal("declared_candidate_missing_or_drifted")
    if cp_declaration.get("candidate_spec_digest") != SPEC_DIGEST:
        raise CRCaptureRefusal("declared_survivor_spec_digest_drift")
    if cp_declaration.get("member") != MEMBER:
        raise CRCaptureRefusal("declared_member_drift")

    declaration = candidate_family.load_candidate_family(family_path)
    family = declaration.family(FAMILY)
    member = next((row for row in family.members if row.name == MEMBER), None)
    if member is None or member.look_taken is not True:
        raise CRCaptureRefusal("v27_member_missing_or_not_billed")
    all_declared = family.size_for(candidate_family.ALL_DECLARED)
    looks_taken = family.size_for(candidate_family.LOOKS_TAKEN)
    if (all_declared, looks_taken) != (59, 57):
        raise CRCaptureRefusal(
            f"v27_multiplicity_drift:{all_declared}/{looks_taken}!=59/57"
        )
    return {
        "candidate_id": CANDIDATE_ID,
        "spec_digest": SPEC_DIGEST,
        "member": MEMBER,
        "family": FAMILY,
        "family_all_declared": all_declared,
        "family_looks_taken": looks_taken,
        "candidate_already_billed": True,
        "new_hypothesis_looks": 0,
        "new_graduation_bills": 0,
        "candidate_authority": _repo_path(cp_gate_receipt),
        "candidate_authority_sha256": file_sha256(cp_gate_receipt),
        "family_declaration": _repo_path(family_path),
        "family_declaration_sha256": declaration.sha256,
    }


def frozen_spec(family_path: Path) -> dict[str, Any]:
    base = OPTIONS[FROZEN_OPTION].with_(
        spec_id="cp_true_utc_ny_metals_long_recorded_mid",
        spread_band=FROZEN_BAND,
        sleeve_symbol_allowlist={SLEEVE: tuple(sorted(POLICY_SYMBOLS))},
    )
    spec = candidate_family.with_declared_family(
        base,
        FAMILY,
        basis=candidate_family.ALL_DECLARED,
        declaration=family_path,
    )
    spec = era_population.spec_for("RECORDED", spec)
    if spec.alpha != FROZEN_ALPHA:
        raise CRCaptureRefusal(f"frozen_alpha_drift:{spec.alpha}!={FROZEN_ALPHA}")
    if spec.fidelity_floor != FIDELITY_FLOOR:
        raise CRCaptureRefusal(
            f"fidelity_floor_drift:{spec.fidelity_floor}!={FIDELITY_FLOOR}"
        )
    return {
        "option": FROZEN_OPTION,
        "band": FROZEN_BAND,
        "alpha": spec.alpha,
        "population": "RECORDED",
        "family_basis": candidate_family.ALL_DECLARED,
        "declared_family_size": spec.declared_family_size,
        "declared_family_id": spec.declared_family_id,
        "declared_family_sha256": spec.declared_family_sha256,
        "fidelity_floor": spec.fidelity_floor,
        "spec_sha256": spec.seal(),
        "spec": spec.as_dict(),
    }


def _git_blob(path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=REPO,
        check=True,
        stdout=subprocess.PIPE,
    )
    return completed.stdout


def recorded_era_inventory() -> dict[str, Any]:
    raw = _git_blob(SPREAD_MODEL_GIT_PATH)
    model = json.loads(raw)
    symbols: dict[str, Any] = {}
    for symbol in sorted(POLICY_SYMBOLS):
        eras = model["accounts"]["FTMO"][symbol]["eras"]
        recorded = [quarter for quarter, row in eras.items() if row.get("class") == "RECORDED"]
        symbols[symbol] = {
            "model_eras": len(eras),
            "recorded_eras": len(recorded),
            "first_recorded": recorded[0] if recorded else None,
            "last_recorded": recorded[-1] if recorded else None,
            "recorded_quarters": recorded,
        }
    return {
        "authority": SPREAD_MODEL_GIT_PATH,
        "authority_sha256": hashlib.sha256(raw).hexdigest(),
        "account": "FTMO",
        "era_field": "class == RECORDED",
        "symbols": symbols,
        "outcome_fields_read": False,
    }


def january_path_inventory(manifest_path: Path, *, authenticate_large_sources: bool) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    lane_root = manifest_path.parents[1]
    for raw in [*(manifest.get("bar_sources") or []), *(manifest.get("tick_sources") or [])]:
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        timeframe = str(raw.get("timeframe") or "")
        if symbol not in POLICY_SYMBOLS or timeframe not in {"M1", "TICK"}:
            continue
        relative = str(raw.get("lane_relpath") or "")
        path = (lane_root / relative).resolve()
        expected = str(raw.get("sha256") or "")
        if not path.is_file():
            raise CRCaptureRefusal(f"january_path_source_missing:{path}")
        actual = file_sha256(path) if authenticate_large_sources else None
        if actual is not None and actual != expected:
            raise CRCaptureRefusal(
                f"january_path_source_hash_mismatch:{relative}:{actual}!={expected}"
            )
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "first_utc": raw.get("first_utc"),
                "last_utc": raw.get("last_utc"),
                "rows": raw.get("row_count"),
                "path": relative,
                "sha256": expected,
                "hash_authenticated_now": actual is not None,
                "time_column_basis": raw.get("time_column_basis"),
            }
        )
    if {(row["symbol"], row["timeframe"]) for row in rows} != {
        (symbol, timeframe)
        for symbol in POLICY_SYMBOLS
        for timeframe in ("M1", "TICK")
    }:
        raise CRCaptureRefusal("january_metals_m1_tick_inventory_incomplete")
    return {
        "manifest": str(manifest_path),
        "manifest_sha256": file_sha256(manifest_path),
        "manifest_root_sha256": manifest.get("manifest_root_sha256"),
        "window": "2026-01",
        "sources": rows,
        "interpretation": (
            "Content-bound January M1 and ordered ticks exist for both symbols. This is a "
            "mechanical reconstruction source for the January reference only; it is not an "
            "all-era RECORDED candidate population and spans no complete historical quarter."
        ),
    }


def projection_contract() -> dict[str, Any]:
    required = {
        "counterfactual_order_fill_status",
        "counterfactual_order_fill_time_utc",
        "counterfactual_order_fill_price",
        "counterfactual_order_close_time_utc",
        "opportunity_gross_r",
        "opportunity_close_reason",
        "terminal_outcome",
        "path_index_source_path",
        "path_index_source_sha256",
    }
    missing = sorted(required - cuts.MISSED_EXECUTABLE_CAPTURE_FIELDS)
    if missing:
        raise CRCaptureRefusal(f"projection_capture_contract_incomplete:{missing}")
    return {
        "projection_stamp": cuts.MISSED_POOL_PROJECTION_STAMP,
        "preserved_capture_fields": sorted(cuts.MISSED_EXECUTABLE_CAPTURE_FIELDS),
        "required_minimum_present": True,
        "derived_exit_fields": [
            "opportunity_close_time_utc",
            "opportunity_close_time_source",
        ],
        "forward_effect": (
            "A future true-UTC broad-V4 lane rerun preserves the producer's already-computed "
            "fill, selected terminal, gross-R, and content-bound path fields instead of "
            "discarding them in the training-lane projection."
        ),
        "sealed_compatibility": "TRAINING_LANE_ONLY_SEALED_INCOMPATIBLE",
    }


def build(
    *,
    protocol_path: Path = DEFAULT_PROTOCOL,
    fidelity_path: Path = DEFAULT_FIDELITY,
    output_path: Path = DEFAULT_OUTPUT,
    cp_gate_receipt: Path = DEFAULT_CP_GATE_RECEIPT,
    family_path: Path = DEFAULT_FAMILY,
    raw_ledger: Path = DEFAULT_RAW_LEDGER,
    semantic_ledger: Path = DEFAULT_SEMANTIC_LEDGER,
    january_manifest: Path = DEFAULT_JANUARY_MANIFEST,
    authenticate_large_sources: bool = True,
) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("status") != "PREDECLARED_BEFORE_JANUARY_HOLDOUT_ECONOMICS_RECONSTRUCTION":
        raise CRCaptureRefusal("predeclared_protocol_status_invalid")
    if protocol.get("candidate", {}).get("candidate_id") != CANDIDATE_ID:
        raise CRCaptureRefusal("predeclared_candidate_id_drift")

    declaration = verify_declaration(cp_gate_receipt, family_path)
    spec = frozen_spec(family_path)
    raw_rows = load_january_rows(raw_ledger)
    semantic_rows = load_january_rows(semantic_ledger)
    reference_rows = [row for row in raw_rows if is_policy_candidate(row)]
    fidelity = measure_generator_fidelity(reference_rows, semantic_rows)
    capture = assess_executable_capture(reference_rows)

    fidelity_core = {
        "schema": FIDELITY_SCHEMA,
        "session": "CR",
        "member": MEMBER,
        "sleeve": SLEEVE,
        "candidate_id": CANDIDATE_ID,
        "reference_kind": FidelityReference.REPLAY_REFERENCE.value,
        "measurement_basis": "MEASURED_DIRECT",
        "floor": FIDELITY_FLOOR,
        "pass": fidelity["reference_recall"] >= FIDELITY_FLOOR,
        "measurement": fidelity,
        "sources": {
            "reference": {
                "path": str(raw_ledger),
                "sha256": file_sha256(raw_ledger),
                "role": "fixed CP pretrade reference population",
            },
            "generated": {
                "path": str(semantic_ledger),
                "sha256": file_sha256(semantic_ledger),
                "role": "independently emitted semantic-candidate rerun",
            },
        },
        "forbidden_surfaces": {
            "february_economics": "NOT_OPENED",
            "march_outcomes": "NOT_OPENED",
            "live_forward": "NOT_OPENED",
        },
    }
    _write_rooted_json(fidelity_path, fidelity_core)
    fidelity_file_sha = file_sha256(fidelity_path)

    clear_direct_fidelity_measurements()
    registered = register_direct_fidelity_measurement(
        SLEEVE,
        agreed=int(fidelity["agreed"]),
        reference_only=int(fidelity["reference_only"]),
        generated_only=None,
        reference_kind=FidelityReference.REPLAY_REFERENCE,
        source=_repo_path(fidelity_path),
        source_sha256=fidelity_file_sha,
        cls=FidelityClass.UNKNOWN,
        note=str(fidelity["caveat"]),
    )

    eras = recorded_era_inventory()
    january_paths = january_path_inventory(
        january_manifest,
        authenticate_large_sources=authenticate_large_sources,
    )
    source_ready = False
    fidelity_ready = registered.refusal_reason(FIDELITY_FLOOR) is None
    if not fidelity_ready:
        raise CRCaptureRefusal("direct_fidelity_measurement_did_not_clear_frozen_floor")

    result = {
        "schema": SCHEMA,
        "session": "CR",
        "blocks": "B2950-B2999",
        "status": "FROZEN_GATE_NOT_EVALUABLE_RECORDED_EXECUTABLE_POPULATION_REQUIRED",
        "verdict": "NOT_EVALUABLE",
        "protocol": {
            "path": _repo_path(protocol_path),
            "sha256": file_sha256(protocol_path),
        },
        "declaration": declaration,
        "frozen_gate_contract": spec,
        "fidelity": {
            "ready": fidelity_ready,
            "receipt": _repo_path(fidelity_path),
            "receipt_sha256": fidelity_file_sha,
            "reference_kind": registered.reference_kind.value,
            "reference_recall": registered.reference_recall,
            "live_recall": None,
            "basis": registered.basis.value,
            "basis_n": registered.basis_n,
            "floor": FIDELITY_FLOOR,
            "pass": fidelity_ready,
            "ceiling_stamp": registered.ceiling_stamp(FIDELITY_FLOOR),
            "basis_note": registered.basis_note,
        },
        "january_reference_capture": {
            "role": "MECHANICAL_CAPTURE_AND_GENERATOR_REPRODUCIBILITY_ONLY",
            "raw_ledger_rows": len(raw_rows),
            "semantic_ledger_rows": len(semantic_rows),
            "policy_candidate_rows": len(reference_rows),
            "capture_assessment": capture,
            "path_sources": january_paths,
            "economic_aggregate_computed": False,
            "gate_population_substitution": False,
        },
        "recorded_population": {
            "ready": source_ready,
            "era_inventory": eras,
            "candidate_population_present": False,
            "executable_path_population_present": False,
            "aa_trade_relabelling_used": False,
            "reason": (
                "The AA estate defines RECORDED era coverage but contains ultimate-book/W7 "
                "trades, not broad-V4 CP candidates. The local exact M1/tick capture covers "
                "January only. No source-bound broad-V4 candidate population with exact "
                "fill and terminal tuples exists across the declared historical RECORDED "
                "surface."
            ),
        },
        "forward_capture_repair": projection_contract(),
        "gate_execution": {
            "invoked": False,
            "why": (
                "The predeclared gate execution condition requires both source and fidelity "
                "prerequisites. Fidelity passes; source does not. Invoking run_gate on an "
                "empty or January-only population would be a partial-population economic "
                "look and is forbidden."
            ),
            "submitted_trade_records": 0,
            "economic_outcomes_inspected_by_gate": False,
            "band_detail": {
                "low": "NOT_IN_FROZEN_SPEC_NO_LOOK",
                "mid": "NOT_EVALUABLE_RECORDED_EXECUTABLE_POPULATION_REQUIRED",
                "high": "NOT_IN_FROZEN_SPEC_NO_LOOK",
            },
        },
        "exact_remaining_capture": [
            {
                "id": "CR-CAPTURE-1",
                "requirement": (
                    "Declare untouched OOS fold dates spanning the AA/SPREAD_MODEL RECORDED "
                    "era surface for XAGUSD and XAUUSD, excluding February 2026, March 2026, "
                    "and live-forward evidence; bind that fold declaration by SHA-256."
                ),
            },
            {
                "id": "CR-CAPTURE-2",
                "requirement": (
                    "Supply true-UTC broad-V4 generator inputs for every declared fold: M15 "
                    "decision bars plus every H4/D1 and cross-symbol feature dependency. Run "
                    "the unchanged CP predicate (NY, XAGUSD/XAUUSD, LONG) and retain every "
                    "candidate before fill/scoreability selection."
                ),
            },
            {
                "id": "CR-CAPTURE-3",
                "requirement": (
                    "Supply ordered M1 or tick truth from each decision through terminal for "
                    "both metals on every fold. Emit explicit fill/no-fill for every "
                    "candidate and, for every fill, fill UTC/price, authoritative exit UTC, "
                    "pre-cost gross R, terminal reason, source path and source SHA-256."
                ),
            },
            {
                "id": "CR-CAPTURE-4",
                "requirement": (
                    "Rerun through train_lane_missed_pool_projection_v3 (or an equivalent "
                    "reader-complete export), validate one unique row per candidate, apply "
                    "RECORDED through walkforward.era_population, then invoke the sealed V27 "
                    "B_balanced mid-band alpha=0.10 spec recorded above. No new graduation "
                    "bill is due."
                ),
            },
        ],
        "safety": {
            "february_2026_economics": "NOT_READ_BY_THIS_TOOL",
            "march_2026_outcomes": "NOT_READ_BY_THIS_TOOL",
            "vps_contact": False,
            "broker_capable_script_invoked": False,
            "token_bound_config_read_or_written": False,
            "new_hypothesis_looks": 0,
        },
        "session_boundary_disclosure": {
            "committed_tool_run": (
                "No February economics or March outcomes opened; candidate authority is "
                "the explicitly commissioned CP gate receipt, and ledger decoding is "
                "January-only before json.loads."
            ),
            "operator_incidents": [
                {
                    "surface": "AA estate",
                    "violation": (
                        "An early exploratory whole-container json.load decoded the "
                        "container before a date boundary, necessarily traversing any "
                        "March outcome rows present. No March economic value was printed, "
                        "inspected, aggregated, compared, or used."
                    ),
                },
                {
                    "surface": "CP result document",
                    "violation": (
                        "A final authority-audit rg command scanned the entire result "
                        "document, including its February section. No February outcome "
                        "value was extracted, compared, or used."
                    ),
                },
            ],
        },
    }
    return _write_rooted_json(output_path, result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--fidelity-output", type=Path, default=DEFAULT_FIDELITY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-large-source-hash",
        action="store_true",
        help="Development-only: trust January manifest hashes instead of rehashing 1.9 GiB.",
    )
    args = parser.parse_args()
    result = build(
        protocol_path=args.protocol,
        fidelity_path=args.fidelity_output,
        output_path=args.output,
        authenticate_large_sources=not args.skip_large_source_hash,
    )
    print(json.dumps({
        "status": result["status"],
        "verdict": result["verdict"],
        "fidelity": result["fidelity"]["reference_recall"],
        "source_ready": result["recorded_population"]["ready"],
        "output": _repo_path(args.output),
        "content_sha256": result["content_sha256"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
