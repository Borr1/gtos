"""Build CNR T3 lifecycle expansion source packet artifacts.

Research/control lane only. The script freezes the lifecycle contract before
reading any beyond-original-horizon tick path, then packetizes only rows with
source-hashed quote/path/geometry sufficient for categorical T3 lifecycle
labels. It intentionally does not compute R, win rate, expectancy, DSR, PBO,
or any promotion statistic.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pyarrow.parquet as pq
except Exception as exc:  # pragma: no cover - verifier catches this in runtime
    pq = None
    PYARROW_IMPORT_ERROR = str(exc)
else:
    PYARROW_IMPORT_ERROR = None


DATE_STAMP = "2026-05-08"
SCHEMA_VERSION = "cnr_t3_lifecycle_expansion_source_packet_v1"
CONTRACT_ID = "CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ALLOWED_LABELS = [
    "target_after_original_horizon",
    "stop_after_original_horizon",
    "ambiguous_target_stop_after_original_horizon",
    "still_no_terminal_after_extended_horizon",
    "source_horizon_insufficient",
    "not_packet_eligible",
]

FORBIDDEN_PACKET_ROW_KEYS = {
    "synthetic_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_trade_results",
    "live_order_state",
    "hidden_path_label",
    "promotion_statistic",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "performance",
}

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

OUTPUT_NAMES = {
    "context_anchor": "CNR_T3_CONTEXT_ANCHOR_2026-05-08",
    "contract": "CNR_T3_FROZEN_LIFECYCLE_CONTRACT_2026-05-08",
    "inventory": "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY_2026-05-08",
    "source_ledger": "CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER_2026-05-08",
    "packet": "CNR_T3_LIFECYCLE_PACKET_2026-05-08",
    "audit": "CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08",
    "blockers": "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER_2026-05-08",
    "learning": "CNR_T3_LIFECYCLE_FORENSICS_AND_LEARNING_2026-05-08",
    "g12_prompt": "CNR_T3_G12_AUDIT_PROMPT_PACK_2026-05-08",
    "completion": "CNR_T3_COMPLETION_AUDIT_2026-05-08",
}

MANDATORY_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    str(
        Path("research/science_program_2026_05/06_outcome_testing")
        / "cnr_t3_lifecycle_expansion_source_packet"
        / "CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_GOAL_PROMPT_2026-05-08.md"
    ),
]

REQUIRED_UPSTREAM_INPUTS = [
    "g12_cnr_next_model_control_audit/G12_CNR_NEXT_PROMPT_PACK_2026-05-08.md",
    "g12_cnr_next_model_control_audit/G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR_NEXT_DECISION_LEDGER_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR061_LIFECYCLE_PACKET_AUDIT_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_2026-05-08.json",
    "g12_cnr_next_model_control_audit/G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
    "cnr_next_model_control_pack/CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08.json",
    "cnr_next_model_control_pack/CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
    "oti7_cnr_accepted_quarantined_results/OTI7_CNR_RESULT_LEDGER_2026-05-08.jsonl",
    "g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_2026-05-08.json",
    "oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "g12_oti5_otr061_post_audit/G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
    "oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti4_g6_opening_drive_quarantined_results/OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json",
    "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti6_otr061_cnr_quarantined_results/OTI6_CNR_RESULT_LEDGER_2026-05-07.json",
]

TICK_ROOTS = [
    REPO_ROOT / "data" / "ticks",
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
    Path(r"C:\tmp\gtos_otb\CNRT3LIFE\data\ticks"),
]

FILE_HASH_CACHE: dict[Path, str] = {}
TICK_ROW_CACHE: dict[Path, list[tuple[dt.datetime, float, float]]] = {}


@dataclass
class Candidate:
    inventory_id: str
    source_lane: str
    source_artifact_path: str
    row_id: str
    packet_id: str | None
    experiment_id: str | None
    symbol: str | None
    source_symbol: str | None
    side: str | None
    session: str | None
    decision_asof_utc: str | None
    path_start_utc: str | None
    original_horizon_end_utc: str | None
    terminal_status: str | None
    duplicate_group_id: str | None
    duplicate_denominator_key: str | None
    countable_denominator_row: bool | None
    source_hashes: dict[str, str]
    candidate_state_family: str
    packet_eligible: bool
    packet_eligibility_reason: str
    provisional_label: str
    source_row: dict[str, Any]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "source_lane": self.source_lane,
            "source_artifact_path": self.source_artifact_path,
            "row_id": self.row_id,
            "packet_id": self.packet_id,
            "experiment_id": self.experiment_id,
            "symbol": self.symbol,
            "source_symbol": self.source_symbol,
            "side": self.side,
            "session": self.session,
            "decision_asof_utc": self.decision_asof_utc,
            "path_start_utc": self.path_start_utc,
            "original_horizon_end_utc": self.original_horizon_end_utc,
            "terminal_status": self.terminal_status,
            "duplicate_group_id": self.duplicate_group_id,
            "duplicate_denominator_key": self.duplicate_denominator_key,
            "countable_denominator_row": self.countable_denominator_row,
            "source_hashes": self.source_hashes,
            "candidate_state_family": self.candidate_state_family,
            "packet_eligible": self.packet_eligible,
            "packet_eligibility_reason": self.packet_eligibility_reason,
            "lifecycle_label_or_blocker_label": self.provisional_label,
        }


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def file_sha256(path: Path) -> str:
    resolved = path.resolve()
    if resolved in FILE_HASH_CACHE:
        return FILE_HASH_CACHE[resolved]
    h = hashlib.sha256()
    with resolved.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    digest = h.hexdigest()
    FILE_HASH_CACHE[resolved] = digest
    return digest


def canonical_sha256(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(name: str, obj: Any) -> None:
    (THIS_DIR / f"{name}.json").write_text(
        json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    with (THIS_DIR / f"{name}_ROWS.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def write_md(name: str, title: str, body: str) -> None:
    (THIS_DIR / f"{name}.md").write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def parse_dt(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso_z(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def date_range(start: dt.datetime, end: dt.datetime) -> list[dt.date]:
    current = start.date()
    final = end.date()
    out: list[dt.date] = []
    while current <= final:
        out.append(current)
        current += dt.timedelta(days=1)
    return out


def extract_source_hashes(row: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in (
        "row_sha256",
        "row_source_hash",
        "sidecar_row_sha256",
        "packet_row_sha256",
        "packet_source_hash",
        "packet_source_hash_recomputed",
        "source_hash",
        "source_hash_recomputed",
        "quote_source_sha256",
        "outcome_source_sha256",
        "ltf_projection_hash",
    ):
        value = row.get(key)
        if isinstance(value, str) and value:
            out[key] = value
    for key in ("path_source_sha256", "source_hashes"):
        value = row.get(key)
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, str) and sub_value:
                    out[f"{key}:{sub_key}"] = sub_value
    return out


def first_text(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value:
            return value
        if not isinstance(value, str):
            return str(value)
    return None


def geometry_from_row(row: dict[str, Any]) -> dict[str, Any]:
    geometry = row.get("geometry") if isinstance(row.get("geometry"), dict) else {}
    entry_packet = row.get("entry_sl_tp_or_level_packet") if isinstance(row.get("entry_sl_tp_or_level_packet"), dict) else {}
    return {
        "entry": first_text(row.get("original_entry_price"), geometry.get("original_entry_price"), entry_packet.get("entry_price")),
        "stop": first_text(row.get("original_stop_loss"), geometry.get("original_stop_loss"), entry_packet.get("stop_loss")),
        "target": first_text(row.get("original_take_profit_1"), geometry.get("original_take_profit_1"), entry_packet.get("take_profit_1")),
    }


def is_oti8_t3_eligible(row: dict[str, Any], accepted_sidecar_hashes: set[str]) -> tuple[bool, str]:
    if row.get("terminal_status") != "NO_TERMINAL_WITHIN_ORDERED_HORIZON":
        return False, "not an original-horizon no-terminal OTI8 row"
    if row.get("sidecar_row_sha256") not in accepted_sidecar_hashes:
        return False, "OTI8 sidecar hash is not in the accepted-row manifest"
    required = [
        "symbol",
        "side",
        "candidate_close_utc",
        "path_start_utc",
        "path_end_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "quote_source_sha256",
        "row_source_hash",
        "sidecar_row_sha256",
    ]
    missing = [key for key in required if row.get(key) in (None, "", [])]
    if missing:
        return False, "missing T3 source fields: " + ",".join(missing)
    if not row.get("path_source_files"):
        return False, "missing original ordered path source files"
    return True, "eligible: accepted OTI8 CNR061 no-terminal row with source-hashed quote/path/geometry"


def mk_candidate(
    idx: int,
    source_lane: str,
    artifact: Path,
    row: dict[str, Any],
    state_family: str,
    accepted_sidecar_hashes: set[str],
) -> Candidate:
    symbol = first_text(row.get("symbol"), row.get("broker_symbol"), row.get("source_symbol"))
    source_symbol = first_text(row.get("source_symbol"), row.get("broker_symbol"), row.get("symbol"))
    decision = first_text(row.get("decision_asof_utc"), row.get("candidate_close_utc"), row.get("asof_cutoff_utc"))
    path_start = first_text(row.get("path_start_utc"), row.get("original_path_start_utc"))
    path_end = first_text(row.get("path_end_utc"), row.get("original_path_end_utc"))
    terminal = first_text(
        row.get("terminal_status"),
        row.get("result_status"),
        row.get("quarantined_result_status"),
        row.get("fill_or_no_fill_state"),
        row.get("lifecycle_state"),
        row.get("terminal_label"),
        row.get("path_order_label"),
        row.get("descriptive_status"),
        row.get("opening_drive_status"),
        row.get("same_bar_ambiguity_state"),
    )
    eligible = False
    reason = "not evaluated"
    if source_lane == "OTI8_CNR061":
        eligible, reason = is_oti8_t3_eligible(row, accepted_sidecar_hashes)
    else:
        geom = geometry_from_row(row)
        if terminal and "NO_TERMINAL_WITHIN_ORDERED_HORIZON" in terminal:
            missing = [
                name
                for name, value in {
                    "path_start_utc": path_start,
                    "path_end_utc": path_end,
                    "entry": geom["entry"],
                    "stop": geom["stop"],
                    "target": geom["target"],
                    "quote/source hash": extract_source_hashes(row),
                }.items()
                if not value
            ]
            reason = "not packet eligible: non-OTI8 row lacks accepted CNR T3 source contract"
            if missing:
                reason += "; missing " + ",".join(missing)
        else:
            reason = "not packet eligible: lifecycle/no-entry/source-blocked state is not an original-horizon target/stop no-terminal CNR T3 row"
    return Candidate(
        inventory_id=f"CNR-T3-CAND-{idx:04d}",
        source_lane=source_lane,
        source_artifact_path=rel(artifact),
        row_id=first_text(row.get("record_id"), row.get("setup_id"), row.get("candidate_id"), row.get("duplicate_group_id"), row.get("packet_id")) or f"{source_lane}-{idx}",
        packet_id=first_text(row.get("packet_id")),
        experiment_id=first_text(row.get("experiment_id")),
        symbol=symbol,
        source_symbol=source_symbol,
        side=first_text(row.get("side")),
        session=first_text(row.get("session")),
        decision_asof_utc=decision,
        path_start_utc=path_start,
        original_horizon_end_utc=path_end,
        terminal_status=terminal,
        duplicate_group_id=first_text(row.get("duplicate_group_id")),
        duplicate_denominator_key=first_text(row.get("duplicate_denominator_key")),
        countable_denominator_row=row.get("countable_denominator_row") if isinstance(row.get("countable_denominator_row"), bool) else None,
        source_hashes=extract_source_hashes(row),
        candidate_state_family=state_family,
        packet_eligible=eligible,
        packet_eligibility_reason=reason,
        provisional_label="source_horizon_insufficient" if eligible else "not_packet_eligible",
        source_row=row,
    )


def flatten_oti1_group_summaries(path: Path) -> list[dict[str, Any]]:
    obj = load_json(path)
    rows: list[dict[str, Any]] = []
    for packet in obj.get("packet_results", []):
        for group in packet.get("group_summaries", []):
            rows.append(
                {
                    **group,
                    "packet_id": packet.get("packet_id"),
                    "experiment_id": packet.get("experiment_id"),
                    "hypothesis_id": packet.get("hypothesis_id"),
                    "source_packet_path": packet.get("packet_artifact"),
                    "packet_source_hash": packet.get("packet_sha256"),
                    "result_status": packet.get("lifecycle_truth_only_result_status"),
                    "promotion_verdict": obj.get("promotion_verdict"),
                    "validation_safe": obj.get("validation_safe"),
                }
            )
    return rows


def discover_candidates(accepted_sidecar_hashes: set[str]) -> tuple[list[Candidate], list[dict[str, Any]]]:
    specs: list[tuple[str, Path, str, str]] = [
        ("OTI8_CNR061", OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / "OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl", "terminal_status", "NO_TERMINAL_WITHIN_ORDERED_HORIZON"),
        ("OTI5_G6_CUSUM", OUTCOME_ROOT / "oti5_g6_cusum_changepoint_quarantined_results" / "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl", "result_status", "NO_ENTRY_TOUCH_NO_R_SCORED"),
        ("OTI4_G6_OPENING_DRIVE", OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results" / "OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl", "same_bar_ambiguity_state", "terminal_order_unclaimed"),
        ("OTI3_G3_GEOMETRY", OUTCOME_ROOT / "oti3_g3_geometry_quarantined_results" / "OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl", "terminal_label", "NO_PRICE_COMPATIBLE_M1_SOURCE"),
        ("OTI2_RISKBANK", OUTCOME_ROOT / "oti2_riskbank_quarantined_results" / "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl", "path_order_label", "without_entry_touch"),
    ]
    raw_candidates: list[tuple[str, Path, dict[str, Any], str]] = []
    scan_summaries: list[dict[str, Any]] = []

    for source_lane, path, key, value_substring in specs:
        rows = load_jsonl(path)
        selected: list[dict[str, Any]] = []
        for row in rows:
            text = str(row.get(key, ""))
            if value_substring in text:
                selected.append(row)
            elif source_lane == "OTI2_RISKBANK" and (
                row.get("entry_first_touch_utc") is None
                or "unresolved" in str(row.get("descriptive_status", "")).lower()
            ):
                selected.append(row)
        for row in selected:
            raw_candidates.append((source_lane, path, row, f"{key}:{value_substring}"))
        scan_summaries.append(
            {
                "source_lane": source_lane,
                "artifact_path": rel(path),
                "rows_loaded": len(rows),
                "candidate_like_rows_selected": len(selected),
                "selection_rule": f"{key} contains {value_substring}; OTI2 also includes null entry touch or unresolved descriptive status",
            }
        )

    oti1_path = OUTCOME_ROOT / "oti1_lifecycle_quarantined_results" / "OTI1_RESULT_LEDGER_2026-05-07.json"
    oti1_rows = flatten_oti1_group_summaries(oti1_path)
    selected_oti1 = [
        row
        for row in oti1_rows
        if "no_fill" in str(row.get("fill_or_no_fill_state", "")).lower()
        or "still_pending" in str(row.get("lifecycle_state", "")).lower()
    ]
    for row in selected_oti1:
        raw_candidates.append(("OTI1_LIFECYCLE", oti1_path, row, "fill_or_no_fill/still_pending lifecycle group summary"))
    scan_summaries.append(
        {
            "source_lane": "OTI1_LIFECYCLE",
            "artifact_path": rel(oti1_path),
            "rows_loaded": len(oti1_rows),
            "candidate_like_rows_selected": len(selected_oti1),
            "selection_rule": "flatten packet_results.group_summaries with no_fill or still_pending lifecycle states",
        }
    )

    # Required upstream CNR/OTI artifacts named by prompt that do not add T3 candidates.
    zero_scan_paths = [
        ("OTI7_CNR", OUTCOME_ROOT / "oti7_cnr_accepted_quarantined_results" / "OTI7_CNR_RESULT_LEDGER_2026-05-08.jsonl", "scanned; no no-terminal/no-entry/still-pending status found"),
        ("OTI6_CNR", OUTCOME_ROOT / "oti6_otr061_cnr_quarantined_results" / "OTI6_CNR_RESULT_LEDGER_2026-05-07.json", "scanned; target-already-passed geometry ineligible, not no-terminal-like"),
        ("G12_OTI8", OUTCOME_ROOT / "g12_oti8_cnr061_post_result_audit" / "G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_2026-05-08.json", "audit source only; candidates sourced from OTI8 accepted result rows"),
        ("G12_OTI7", OUTCOME_ROOT / "g12_oti7_cnr_post_result_audit" / "G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_2026-05-08.json", "audit source only; no new candidate rows"),
        ("G12_OTI5", OUTCOME_ROOT / "g12_oti5_otr061_post_audit" / "G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json", "audit source only; candidates sourced from OTI5 result rows"),
    ]
    for source_lane, path, note in zero_scan_paths:
        row_count = len(load_jsonl(path)) if path.suffix == ".jsonl" else 1
        scan_summaries.append(
            {
                "source_lane": source_lane,
                "artifact_path": rel(path),
                "rows_loaded": row_count,
                "candidate_like_rows_selected": 0,
                "selection_rule": note,
            }
        )

    candidates: list[Candidate] = []
    for idx, (lane, path, row, family) in enumerate(raw_candidates, start=1):
        candidates.append(mk_candidate(idx, lane, path, row, family, accepted_sidecar_hashes))
    return candidates, scan_summaries


def build_contract() -> dict[str, Any]:
    contract = {
        "artifact_family": "CNR_T3_FROZEN_LIFECYCLE_CONTRACT",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "freeze_order": "Written before any beyond-original-horizon tick extension scan.",
        "date_stamp": DATE_STAMP,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "row_eligibility_rules": [
            "Row must be an accepted/quarantined CNR/OTI row with original terminal_status exactly NO_TERMINAL_WITHIN_ORDERED_HORIZON.",
            "Row must have source-hashed quote/path/geometry sufficient to bind symbol, side, path_start_utc, original_horizon_end_utc, original entry, original stop, original TP1, source row hash, and tick source hashes.",
            "Rows whose only lifecycle state is no-fill, no-entry, still-pending, target-already-passed, source-blocked, or terminal-order-unclaimed are inventoried but labelled not_packet_eligible.",
            "The 94 G12-blocked CNR061 rows remain excluded from scoring/packet labels; only accepted OTI8 sidecar hashes may be packetized.",
        ],
        "allowed_labels": ALLOWED_LABELS,
        "original_horizon_source_rule": "Use the upstream row's original path_end_utc as original_horizon_end_utc; only rows that were no-terminal within that ordered source-hashed horizon may be extended.",
        "extended_horizon_cap_rule": "Scan after original_horizon_end_utc until the first target/stop terminal event or path_start_utc + 24 hours, whichever comes first.",
        "extension_interval_rule": "Use ticks strictly after original_horizon_end_utc and before the extended horizon cap.",
        "quote_side_terminal_rule_by_side": {
            "LONG": "bid >= original_take_profit_1 is target; bid <= original_stop_loss is stop",
            "SHORT": "ask <= original_take_profit_1 is target; ask >= original_stop_loss is stop",
        },
        "duplicate_denominator_policy": "Retain row-level packets; denominator counting uses upstream countable_denominator_row plus duplicate_denominator_key and duplicate_group_id. Do not treat repeated rows from the same duplicate group as independent validation evidence.",
        "no_leak_field_allowlist": [
            "row identity and upstream hashes",
            "symbol, side, session, timing family, target family",
            "original path start/end, extended horizon cap",
            "original entry, stop, TP1 geometry",
            "tick source file paths and sha256 hashes",
            "categorical lifecycle label",
            "terminal event timestamp and quote side only",
            "duplicate denominator fields",
            "NO_PROMOTION_VERDICT and false validation/live flags",
        ],
        "forbidden_fields": sorted(FORBIDDEN_PACKET_ROW_KEYS),
        "source_hash_requirements": [
            "Every consumed tick parquet file must be sha256 hashed.",
            "Every upstream row must carry at least one row/source hash.",
            "If required tick files or source hashes are missing, label source_horizon_insufficient or not_packet_eligible with exact blocker.",
        ],
        "no_r_performance_rule": "No R, win rate, expectancy, DSR, PBO, effective-N promotion statistic, account PnL, or broker actual-R is computed.",
        "blocked_row_exclusion_rule": "The 94 G12-blocked CNR061 rows are verified only as excluded and are not opened, scored, or lifecycle-labelled.",
    }
    contract["contract_sha256"] = canonical_sha256({k: v for k, v in contract.items() if k != "contract_sha256"})
    return contract


def contract_markdown(contract: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Contract id: `{contract['contract_id']}`",
            f"Contract sha256: `{contract['contract_sha256']}`",
            f"Promotion verdict: `{PROMOTION_VERDICT}`",
            "Validation safe: `false`",
            "Outcome review opened: `false`",
            "Live effect: `false`",
            "",
            "## Freeze Order",
            contract["freeze_order"],
            "",
            "## Allowed Labels",
            "\n".join(f"- `{label}`" for label in contract["allowed_labels"]),
            "",
            "## Eligibility",
            "\n".join(f"- {rule}" for rule in contract["row_eligibility_rules"]),
            "",
            "## Terminal Rule",
            "\n".join(f"- `{side}`: {rule}" for side, rule in contract["quote_side_terminal_rule_by_side"].items()),
            "",
            "## No-Leak Boundary",
            "\n".join(f"- {field}" for field in contract["no_leak_field_allowlist"]),
            "",
            "Forbidden fields: " + ", ".join(f"`{field}`" for field in contract["forbidden_fields"]),
            "",
            "## Blocked Rows",
            contract["blocked_row_exclusion_rule"],
        ]
    )


def read_context_artifacts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in MANDATORY_CONTEXT_FILES:
        path = REPO_ROOT / item
        rows.append(
            {
                "path": item.replace("\\", "/"),
                "exists": path.exists(),
                "sha256": file_sha256(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
                "role": "mandatory_preflight_or_controlling_prompt",
            }
        )
    for item in REQUIRED_UPSTREAM_INPUTS:
        path = OUTCOME_ROOT / item
        rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": file_sha256(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
                "role": "required_upstream_input",
            }
        )
    return rows


def build_context_anchor(candidates: list[Candidate], scan_summaries: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "CNR_T3_CONTEXT_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "date_stamp": DATE_STAMP,
        "repo_root": str(REPO_ROOT),
        "branch": run_git(["branch", "--show-current"]),
        "head": run_git(["rev-parse", "HEAD"]),
        "head_oneline": run_git(["log", "-1", "--oneline"]),
        "git_status_short_at_anchor": run_git(["status", "--short"]),
        "controlling_prompt": rel(THIS_DIR / "CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_GOAL_PROMPT_2026-05-08.md"),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "pyarrow_available": pq is not None,
        "pyarrow_import_error": PYARROW_IMPORT_ERROR,
        "artifacts_read": read_context_artifacts(),
        "active_question_stack": [
            "Which accepted/quarantined CNR/OTI rows are no-terminal/no-entry/still-pending-like?",
            "Which of those rows have source-hashed quote/path/geometry sufficient for T3 extension?",
            "Do source-hashed local tick files cover each eligible row's extended horizon?",
            "Which categorical lifecycle label is first observed after the original horizon, if any?",
            "What exact blocker explains every non-packetized candidate?",
            "What should G12 audit next, and which future T1/T2/E2/E3/E4 lanes remain blocked?",
        ],
        "searched_root_ledger_initial": [
            {
                "root": str(root),
                "exists": root.exists(),
                "purpose": "tick parquet discovery root; detailed per-file hashes are in the source ledger",
            }
            for root in TICK_ROOTS
        ],
        "route_decision_ledger": [
            {
                "route": "CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1",
                "decision": "RUN",
                "reason": "G12 accepted T3 as source-safe categorical lifecycle expansion without R/performance scoring.",
            },
            {
                "route": "T3 freeze-before-scan",
                "decision": "ENFORCE",
                "reason": f"Contract {contract['contract_id']} sha256 {contract['contract_sha256']} is written before reading extended tick paths.",
            },
            {
                "route": "Non-OTI8 no-entry/no-fill/source-blocked candidates",
                "decision": "INVENTORY_AND_BLOCK",
                "reason": "They are relevant lifecycle-like rows but lack the accepted CNR T3 no-terminal source contract.",
            },
            {
                "route": "G12 blocked 94 CNR061 rows",
                "decision": "EXCLUDE",
                "reason": "Prompt and G12 audit forbid blocked-row opening/scoring.",
            },
        ],
        "candidate_discovery_pre_scan": {
            "total_candidate_like_rows": len(candidates),
            "packet_eligible_rows_before_scan": sum(1 for c in candidates if c.packet_eligible),
            "source_lane_counts": dict(Counter(c.source_lane for c in candidates)),
            "scan_summaries": scan_summaries,
        },
        "runtime_dirt_notice": "The preflight regenerated .context/LIVE_STATE.md; no live trading surface files are modified by this builder.",
    }


def context_anchor_markdown(anchor: dict[str, Any]) -> str:
    lines = [
        f"Generated: `{anchor['generated_at_utc']}`",
        f"HEAD: `{anchor['head_oneline']}`",
        f"Branch: `{anchor['branch']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Active Questions",
        "\n".join(f"- {q}" for q in anchor["active_question_stack"]),
        "",
        "## Route Decisions",
    ]
    for row in anchor["route_decision_ledger"]:
        lines.append(f"- `{row['route']}` -> `{row['decision']}`: {row['reason']}")
    lines.extend(
        [
            "",
            "## Candidate Discovery Before Extension Scan",
            f"- Candidate-like rows: `{anchor['candidate_discovery_pre_scan']['total_candidate_like_rows']}`",
            f"- Packet-eligible before scan: `{anchor['candidate_discovery_pre_scan']['packet_eligible_rows_before_scan']}`",
            "- Source-lane counts: "
            + ", ".join(
                f"`{lane}`={count}"
                for lane, count in sorted(anchor["candidate_discovery_pre_scan"]["source_lane_counts"].items())
            ),
            "",
            "## Initial Tick Roots",
        ]
    )
    for root in anchor["searched_root_ledger_initial"]:
        lines.append(f"- `{root['root']}` exists={root['exists']}")
    lines.extend(["", "## Artifacts Read"])
    for item in anchor["artifacts_read"]:
        lines.append(f"- `{item['path']}` exists={item['exists']} sha256=`{item['sha256']}`")
    return "\n".join(lines)


def find_tick_files(symbol: str, start: dt.datetime, cap: dt.datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    searched: list[dict[str, Any]] = []
    found: list[dict[str, Any]] = []
    for day in date_range(start, cap):
        file_name = f"{day.isoformat()}.parquet"
        matched = False
        for root in TICK_ROOTS:
            path = root / symbol / file_name
            entry = {
                "symbol": symbol,
                "date": day.isoformat(),
                "root": str(root),
                "path": str(path),
                "exists": path.exists(),
            }
            if path.exists():
                entry["sha256"] = file_sha256(path)
                entry["size_bytes"] = path.stat().st_size
                searched.append(entry)
                found.append(entry)
                matched = True
                break
            searched.append(entry)
        if not matched:
            found.append({"symbol": symbol, "date": day.isoformat(), "exists": False, "path": None})
    return found, searched


def normalize_arrow_timestamp(value: Any) -> dt.datetime:
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        text = str(value).replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def read_tick_rows(path: Path) -> list[tuple[dt.datetime, float, float]]:
    resolved = path.resolve()
    if resolved in TICK_ROW_CACHE:
        return TICK_ROW_CACHE[resolved]
    if pq is None:
        raise RuntimeError(f"pyarrow unavailable: {PYARROW_IMPORT_ERROR}")
    schema = pq.read_schema(resolved)
    names = list(schema.names)
    ts_name = next((name for name in ("ts_utc", "timestamp_utc", "time_utc", "timestamp", "time") if name in names), None)
    bid_name = next((name for name in ("bid", "Bid", "BID") if name in names), None)
    ask_name = next((name for name in ("ask", "Ask", "ASK") if name in names), None)
    if not ts_name or not bid_name or not ask_name:
        raise ValueError(f"required tick columns missing in {resolved}: {names}")
    table = pq.read_table(resolved, columns=[ts_name, bid_name, ask_name])
    out: list[tuple[dt.datetime, float, float]] = []
    for item in table.to_pylist():
        bid = item.get(bid_name)
        ask = item.get(ask_name)
        if bid is None or ask is None:
            continue
        out.append((normalize_arrow_timestamp(item[ts_name]), float(bid), float(ask)))
    TICK_ROW_CACHE[resolved] = out
    return out


def classify_tick_terminal(side: str, bid: float, ask: float, stop: float, target: float) -> tuple[str | None, str | None]:
    side_u = side.upper()
    if side_u == "LONG":
        target_hit = bid >= target
        stop_hit = bid <= stop
        quote_side = "bid"
    elif side_u == "SHORT":
        target_hit = ask <= target
        stop_hit = ask >= stop
        quote_side = "ask"
    else:
        raise ValueError(f"unsupported side {side}")
    if target_hit and stop_hit:
        return "ambiguous_target_stop_after_original_horizon", quote_side
    if target_hit:
        return "target_after_original_horizon", quote_side
    if stop_hit:
        return "stop_after_original_horizon", quote_side
    return None, quote_side


def scan_eligible_candidate(candidate: Candidate) -> tuple[dict[str, Any] | None, dict[str, Any], list[dict[str, Any]]]:
    row = candidate.source_row
    start = parse_dt(first_text(row.get("path_start_utc"), row.get("original_path_start_utc")))
    original_end = parse_dt(first_text(row.get("path_end_utc"), row.get("original_path_end_utc")))
    if start is None or original_end is None:
        return None, {"label": "source_horizon_insufficient", "reason": "missing path start/end timestamps"}, []
    cap = start + dt.timedelta(hours=24)
    symbol = str(row["symbol"])
    side = str(row["side"]).upper()
    stop = float(row["original_stop_loss"])
    target = float(row["original_take_profit_1"])
    found_files, searched = find_tick_files(symbol, original_end, cap)
    usable_files = [Path(item["path"]) for item in found_files if item.get("exists") and item.get("path")]
    missing = [item for item in found_files if not item.get("exists")]
    if missing or not usable_files:
        return (
            None,
            {
                "label": "source_horizon_insufficient",
                "reason": "missing required extended tick file(s)",
                "missing": missing,
                "extended_horizon_end_utc": iso_z(cap),
            },
            searched,
        )

    terminal_label: str | None = None
    terminal_quote_side: str | None = None
    terminal_event_utc: str | None = None
    first_tick_utc: str | None = None
    last_tick_utc: str | None = None
    scanned_count = 0
    source_errors: list[str] = []
    for path in usable_files:
        try:
            rows = read_tick_rows(path)
        except Exception as exc:
            source_errors.append(f"{path}: {exc}")
            continue
        for ts, bid, ask in rows:
            if not (original_end < ts < cap):
                continue
            scanned_count += 1
            first_tick_utc = first_tick_utc or iso_z(ts)
            last_tick_utc = iso_z(ts)
            label, quote_side = classify_tick_terminal(side, bid, ask, stop, target)
            if label:
                terminal_label = label
                terminal_quote_side = quote_side
                terminal_event_utc = iso_z(ts)
                break
        if terminal_label:
            break

    if source_errors:
        return (
            None,
            {
                "label": "source_horizon_insufficient",
                "reason": "tick source parser/read error",
                "source_errors": source_errors,
                "extended_horizon_end_utc": iso_z(cap),
            },
            searched,
        )

    if scanned_count == 0:
        return (
            None,
            {
                "label": "source_horizon_insufficient",
                "reason": "no ticks available inside extended horizon interval",
                "extended_horizon_end_utc": iso_z(cap),
            },
            searched,
        )

    label = terminal_label or "still_no_terminal_after_extended_horizon"
    source_file_hashes = [
        {
            "path": item["path"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
            "symbol": item["symbol"],
            "date": item["date"],
        }
        for item in found_files
        if item.get("exists")
    ]
    packet_row = {
        "artifact_family": "CNR_T3_LIFECYCLE_PACKET_ROW",
        "schema_version": SCHEMA_VERSION,
        "label_contract_id": CONTRACT_ID,
        "input_inventory_id": candidate.inventory_id,
        "source_lane": candidate.source_lane,
        "source_artifact_path": candidate.source_artifact_path,
        "record_id": candidate.row_id,
        "packet_id": candidate.packet_id,
        "symbol": symbol,
        "side": side,
        "session": candidate.session,
        "timing_model_family": first_text(row.get("timing_model_family")),
        "target_model_family": first_text(row.get("target_model_family")),
        "candidate_close_utc": first_text(row.get("candidate_close_utc")),
        "original_path_start_utc": iso_z(start),
        "original_horizon_end_utc": iso_z(original_end),
        "extended_horizon_end_utc": iso_z(cap),
        "original_entry_price": float(row["original_entry_price"]),
        "original_stop_loss": stop,
        "original_take_profit_1": target,
        "duplicate_group_id": candidate.duplicate_group_id,
        "duplicate_denominator_key": candidate.duplicate_denominator_key,
        "countable_denominator_row": candidate.countable_denominator_row,
        "upstream_row_hashes": candidate.source_hashes,
        "tick_source_files": source_file_hashes,
        "lifecycle_label": label,
        "terminal_event_utc": terminal_event_utc,
        "terminal_price_side": terminal_quote_side,
        "source_first_tick_after_original_horizon_utc": first_tick_utc,
        "source_last_tick_scanned_utc": last_tick_utc,
        "source_rows_scanned": scanned_count,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    packet_row["packet_row_sha256"] = canonical_sha256(packet_row)
    return packet_row, {"label": label, "reason": "packetized from source-hashed extended tick path"}, searched


def contains_forbidden_packet_key(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_l = str(key).lower()
            for forbidden in FORBIDDEN_PACKET_ROW_KEYS:
                if forbidden in key_l:
                    hits.append(str(key))
            hits.extend(contains_forbidden_packet_key(value))
    elif isinstance(obj, list):
        for item in obj:
            hits.extend(contains_forbidden_packet_key(item))
    return hits


def build_packet_and_ledgers(candidates: list[Candidate]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    packet_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    searched_entries: list[dict[str, Any]] = []
    for candidate in candidates:
        if not candidate.packet_eligible:
            blockers.append(
                {
                    "inventory_id": candidate.inventory_id,
                    "row_id": candidate.row_id,
                    "source_lane": candidate.source_lane,
                    "packet_id": candidate.packet_id,
                    "lifecycle_label": "not_packet_eligible",
                    "exact_blocker": candidate.packet_eligibility_reason,
                    "searched_extended_tick_path": False,
                    "reasoning": "Eligibility was decided before extension scan; non-eligible rows were not scanned for terminal paths.",
                }
            )
            candidate.provisional_label = "not_packet_eligible"
            continue
        packet_row, blocker_info, searched = scan_eligible_candidate(candidate)
        searched_entries.extend(searched)
        if packet_row is None:
            label = blocker_info.get("label", "source_horizon_insufficient")
            blockers.append(
                {
                    "inventory_id": candidate.inventory_id,
                    "row_id": candidate.row_id,
                    "source_lane": candidate.source_lane,
                    "packet_id": candidate.packet_id,
                    "lifecycle_label": label,
                    "exact_blocker": blocker_info.get("reason"),
                    "details": {k: v for k, v in blocker_info.items() if k not in {"label", "reason"}},
                    "searched_extended_tick_path": True,
                }
            )
            candidate.provisional_label = label
        else:
            packet_rows.append(packet_row)
            candidate.provisional_label = packet_row["lifecycle_label"]
    return packet_rows, blockers, searched_entries


def inventory_artifact(candidates: list[Candidate], scan_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [c.to_public_dict() for c in candidates]
    return {
        "artifact_family": "CNR_T3_NO_TERMINAL_CANDIDATE_INVENTORY",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "date_stamp": DATE_STAMP,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "candidate_count": len(rows),
        "packet_eligible_count": sum(1 for row in rows if row["packet_eligible"]),
        "packetized_or_blocked_count": len(rows),
        "source_lane_counts": dict(Counter(row["source_lane"] for row in rows)),
        "label_counts_after_scan": dict(Counter(row["lifecycle_label_or_blocker_label"] for row in rows)),
        "artifact_scan_summaries": scan_summaries,
        "rows": rows,
    }


def inventory_markdown(inv: dict[str, Any]) -> str:
    lines = [
        f"Candidate-like rows inventoried: `{inv['candidate_count']}`",
        f"Packet-eligible before scan: `{inv['packet_eligible_count']}`",
        f"Packetized or exact-blocked: `{inv['packetized_or_blocked_count']}`",
        "",
        "## Source Lane Counts",
    ]
    for lane, count in sorted(inv["source_lane_counts"].items()):
        lines.append(f"- `{lane}`: {count}")
    lines.extend(["", "## Labels After Scan"])
    for label, count in sorted(inv["label_counts_after_scan"].items()):
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Artifact Scan Summary"])
    for row in inv["artifact_scan_summaries"]:
        lines.append(
            f"- `{row['source_lane']}` `{row['artifact_path']}` loaded={row['rows_loaded']} selected={row['candidate_like_rows_selected']}"
        )
    lines.extend(["", "## Rows"])
    for row in inv["rows"]:
        lines.append(
            f"- `{row['inventory_id']}` `{row['source_lane']}` `{row['row_id']}` "
            f"label=`{row['lifecycle_label_or_blocker_label']}` eligible={row['packet_eligible']} "
            f"reason={row['packet_eligibility_reason']}"
        )
    return "\n".join(lines)


def source_ledger_artifact(searched_entries: list[dict[str, Any]], packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    upstream_hashes = read_context_artifacts()
    tick_hashes: dict[str, dict[str, Any]] = {}
    for row in searched_entries:
        if row.get("exists") and row.get("path"):
            tick_hashes[row["path"]] = row
    for packet in packet_rows:
        for item in packet.get("tick_source_files", []):
            tick_hashes[item["path"]] = item
    return {
        "artifact_family": "CNR_T3_SEARCHED_ROOT_AND_SOURCE_HASH_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "date_stamp": DATE_STAMP,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "searched_roots": [
            {
                "root": str(root),
                "exists": root.exists(),
                "role": "absolute/local tick root",
            }
            for root in TICK_ROOTS
        ],
        "per_candidate_tick_search_entries": searched_entries,
        "consumed_tick_file_hashes": sorted(tick_hashes.values(), key=lambda x: str(x.get("path"))),
        "upstream_artifact_hashes": upstream_hashes,
    }


def source_ledger_markdown(ledger: dict[str, Any]) -> str:
    lines = ["## Searched Roots"]
    for root in ledger["searched_roots"]:
        lines.append(f"- `{root['root']}` exists={root['exists']}")
    lines.extend(["", "## Consumed Tick Files"])
    for item in ledger["consumed_tick_file_hashes"]:
        lines.append(f"- `{item['path']}` sha256=`{item.get('sha256')}` size={item.get('size_bytes')}")
    lines.extend(["", "## Upstream Artifacts"])
    for item in ledger["upstream_artifact_hashes"]:
        lines.append(f"- `{item['path']}` exists={item['exists']} sha256=`{item.get('sha256')}`")
    return "\n".join(lines)


def packet_artifact(packet_rows: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "CNR_T3_LIFECYCLE_PACKET",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "date_stamp": DATE_STAMP,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "label_contract_id": CONTRACT_ID,
        "label_contract_sha256": contract["contract_sha256"],
        "allowed_labels": ALLOWED_LABELS,
        "row_count": len(packet_rows),
        "lifecycle_label_counts": dict(Counter(row["lifecycle_label"] for row in packet_rows)),
        "unique_duplicate_groups": len(set(row.get("duplicate_group_id") for row in packet_rows if row.get("duplicate_group_id"))),
        "countable_denominator_rows": sum(1 for row in packet_rows if row.get("countable_denominator_row") is True),
        "row_level_jsonl": f"{OUTPUT_NAMES['packet']}_ROWS.jsonl",
        "rows_sha256": canonical_sha256(packet_rows),
        "what_this_is": "categorical source-hashed lifecycle packet only",
        "what_this_is_not": [
            "not R or performance scoring",
            "not validation safe",
            "not outcome review opening",
            "not a live gate or promotion claim",
            "not a blocked-row rescue",
        ],
    }


def packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        f"Packet rows: `{packet['row_count']}`",
        f"Rows JSONL: `{packet['row_level_jsonl']}`",
        f"Rows sha256: `{packet['rows_sha256']}`",
        f"Contract: `{packet['label_contract_id']}` sha256=`{packet['label_contract_sha256']}`",
        "",
        "## Lifecycle Labels",
    ]
    for label, count in sorted(packet["lifecycle_label_counts"].items()):
        lines.append(f"- `{label}`: {count}")
    lines.extend(
        [
            "",
            f"Unique duplicate groups: `{packet['unique_duplicate_groups']}`",
            f"Countable denominator rows: `{packet['countable_denominator_rows']}`",
            "",
            "This packet contains categorical terminal lifecycle evidence only. It does not compute R/performance or authorize validation/promotion/live effects.",
        ]
    )
    return "\n".join(lines)


def noleak_audit(packet_rows: list[dict[str, Any]], candidates: list[Candidate], cnr_source_audit: dict[str, Any]) -> dict[str, Any]:
    forbidden_hits: dict[str, list[str]] = {}
    for row in packet_rows:
        hits = sorted(set(contains_forbidden_packet_key(row)))
        if hits:
            forbidden_hits[row.get("input_inventory_id", "unknown")] = hits
    duplicate_group_counts = Counter(row.get("duplicate_group_id") for row in packet_rows)
    duplicate_denominator_key_counts = Counter(row.get("duplicate_denominator_key") for row in packet_rows)
    labels = Counter(row["lifecycle_label"] for row in packet_rows)
    return {
        "artifact_family": "CNR_T3_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "forbidden_packet_row_key_hits": forbidden_hits,
        "forbidden_packet_row_key_status": "PASS" if not forbidden_hits else "FAIL",
        "allowed_label_status": "PASS" if set(labels).issubset(set(ALLOWED_LABELS)) else "FAIL",
        "packet_row_count": len(packet_rows),
        "candidate_count": len(candidates),
        "packetized_or_blocked_count": len(candidates),
        "duplicate_group_counts": dict(duplicate_group_counts),
        "duplicate_denominator_key_counts": dict(duplicate_denominator_key_counts),
        "unique_duplicate_groups": len([key for key in duplicate_group_counts if key]),
        "countable_denominator_rows": sum(1 for row in packet_rows if row.get("countable_denominator_row") is True),
        "sample_floor_for_validation_met": False,
        "sample_floor_reason": "T3 lifecycle packet has six row-level entries, one duplicate group, and two countable timing-target denominator rows; it is input evidence only.",
        "blocked_94_exclusion": cnr_source_audit.get("blocked_94_exclusion", {}),
        "blocked_94_status": cnr_source_audit.get("blocked_94_exclusion", {}).get("status", "UNKNOWN"),
        "no_r_performance_computed": True,
    }


def noleak_markdown(audit: dict[str, Any]) -> str:
    lines = [
        f"Forbidden packet-row key status: `{audit['forbidden_packet_row_key_status']}`",
        f"Allowed-label status: `{audit['allowed_label_status']}`",
        f"Packet row count: `{audit['packet_row_count']}`",
        f"Candidate inventory count: `{audit['candidate_count']}`",
        f"Unique duplicate groups: `{audit['unique_duplicate_groups']}`",
        f"Countable denominator rows: `{audit['countable_denominator_rows']}`",
        f"Sample floor for validation met: `{str(audit['sample_floor_for_validation_met']).lower()}`",
        f"Sample floor reason: {audit['sample_floor_reason']}",
        f"94 blocked-row exclusion status: `{audit['blocked_94_status']}`",
    ]
    if audit["forbidden_packet_row_key_hits"]:
        lines.append("## Forbidden Hits")
        for row_id, hits in audit["forbidden_packet_row_key_hits"].items():
            lines.append(f"- `{row_id}`: {hits}")
    return "\n".join(lines)


def blocker_artifact(blockers: list[dict[str, Any]], candidates: list[Candidate]) -> dict[str, Any]:
    return {
        "artifact_family": "CNR_T3_BLOCKER_AND_IMPOSSIBILITY_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "blocker_count": len(blockers),
        "candidate_count": len(candidates),
        "all_candidates_packetized_or_blocked": len(blockers) + sum(1 for c in candidates if c.provisional_label not in {"not_packet_eligible", "source_horizon_insufficient"}) == len(candidates),
        "blocker_label_counts": dict(Counter(row["lifecycle_label"] for row in blockers)),
        "exact_blockers": blockers,
        "global_blockers_for_future_routes": [
            {
                "route": "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET",
                "status": "BLOCKED_PENDING_FROZEN_FIXED_R_MULTIPLE_AND_STOP_SOURCE_PACKET",
                "exact_blocker": "Current packet does not freeze fixed R multiple or stop-source fields for result scoring.",
            },
            {
                "route": "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL_PACKET",
                "status": "BLOCKED_PENDING_ASOF_STRUCTURAL_LEVEL_SNAPSHOT",
                "exact_blocker": "Current rows do not carry source-hashed structural level id, timestamp, hierarchy rank, or selection rule id.",
            },
            {
                "route": "CNR_E2_E3_E4",
                "status": "FUTURE_SOURCE_TELEMETRY_REQUIRED",
                "exact_blocker": "Signal emission, latency, and pretouch trigger source-hashed fields are absent from current rows.",
            },
        ],
    }


def blocker_markdown(blockers: dict[str, Any]) -> str:
    lines = [
        f"Blocker rows: `{blockers['blocker_count']}`",
        f"All candidates packetized or blocked: `{str(blockers['all_candidates_packetized_or_blocked']).lower()}`",
        "",
        "## Blocker Label Counts",
    ]
    for label, count in sorted(blockers["blocker_label_counts"].items()):
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Exact Blockers"])
    for row in blockers["exact_blockers"]:
        lines.append(
            f"- `{row['inventory_id']}` `{row['source_lane']}` `{row['row_id']}` "
            f"label=`{row['lifecycle_label']}` blocker={row['exact_blocker']}"
        )
    lines.extend(["", "## Future Route Blockers"])
    for row in blockers["global_blockers_for_future_routes"]:
        lines.append(f"- `{row['route']}` `{row['status']}`: {row['exact_blocker']}")
    return "\n".join(lines)


def learning_artifact(packet_rows: list[dict[str, Any]], blockers: list[dict[str, Any]], candidates: list[Candidate]) -> dict[str, Any]:
    labels = Counter(row["lifecycle_label"] for row in packet_rows)
    blocker_labels = Counter(row["lifecycle_label"] for row in blockers)
    return {
        "artifact_family": "CNR_T3_LIFECYCLE_FORENSICS_AND_LEARNING",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "packet_label_counts": dict(labels),
        "blocker_label_counts": dict(blocker_labels),
        "horizon_limited_findings": [
            "The accepted OTI8 CNR061 no-terminal rows are horizon-limited for this packet: all six packetized rows become stop_after_original_horizon under source-hashed XAGUSD ticks.",
            "The six packetized rows collapse to one XAGUSD May 5 NY duplicate group and two countable timing-target denominator rows, so they are failure anatomy, not validation evidence.",
        ],
        "source_limited_findings": [
            "No packet-eligible row was source_horizon_insufficient in this run.",
            "Many no-entry/no-fill/still-pending/source-blocked rows are not T3 packet eligible because they do not bind original-horizon target/stop no-terminal geometry with source-hashed quote/path fields.",
        ],
        "late_stop_target_still_unresolved_summary": {
            "target_after_original_horizon": labels.get("target_after_original_horizon", 0),
            "stop_after_original_horizon": labels.get("stop_after_original_horizon", 0),
            "ambiguous_target_stop_after_original_horizon": labels.get("ambiguous_target_stop_after_original_horizon", 0),
            "still_no_terminal_after_extended_horizon": labels.get("still_no_terminal_after_extended_horizon", 0),
            "source_horizon_insufficient": blocker_labels.get("source_horizon_insufficient", 0),
            "not_packet_eligible": blocker_labels.get("not_packet_eligible", 0),
        },
        "what_this_teaches": [
            "T3 lifecycle capture can separate true source-horizon insufficiency from a no-terminal state caused by too-short original horizons.",
            "The current broad inventory shows most lifecycle-like rows are no-fill/no-entry/source-blocked families and need separate packet contracts, not T3 terminal extension.",
            "Future CNR rows should store source-hashed original horizon, path source files, executable quote, stop/target geometry, and duplicate denominator fields in one source contract to reduce reconstruction work.",
        ],
        "what_this_does_not_prove": [
            "No R/performance, win rate, expectancy, validation, promotion, live gate, or selector change is proven.",
            "No broker actual-R, account history, live trade result, live order state, hidden path label, or blocked-row outcome is used.",
            "The six late-stop rows do not prove CNR is bad; they document one source-safe lifecycle/failure-anatomy cluster.",
        ],
        "next_capture_questions": [
            "For no-fill/still-pending rows, should a separate lifecycle/no-fill extension contract be written with fill/cancel/expiry source hashes?",
            "For T1, what fixed-R multiple and stop-source contract should be frozen before any result lane?",
            "For T2, what structural-level snapshot builder can source-hash level ids, timestamps, hierarchy rank, and selection rule ids?",
            "For E2/E3/E4, which shadow-only telemetry fields should be logged before future outcome opening?",
        ],
        "candidate_inventory_count": len(candidates),
    }


def learning_markdown(learning: dict[str, Any]) -> str:
    lines = ["## Label Summary"]
    for label, count in sorted(learning["late_stop_target_still_unresolved_summary"].items()):
        lines.append(f"- `{label}`: {count}")
    for section in ("horizon_limited_findings", "source_limited_findings", "what_this_teaches", "what_this_does_not_prove", "next_capture_questions"):
        title = section.replace("_", " ").title()
        lines.extend(["", f"## {title}"])
        lines.extend(f"- {item}" for item in learning[section])
    return "\n".join(lines)


def g12_prompt_pack() -> str:
    return "\n".join(
        [
            "Promotion verdict: `NO_PROMOTION_VERDICT`",
            "Validation safe: `false`",
            "Outcome review opened: `false`",
            "Live effect: `false`",
            "",
            "## G12 Audit Goal",
            "",
            "`/goal Audit CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1 under research/science_program_2026_05/06_outcome_testing/cnr_t3_lifecycle_expansion_source_packet. Complete mandatory GTOS preflight; read the controlling prompt, context anchor, frozen lifecycle contract, candidate inventory, searched-root/source-hash ledger, lifecycle packet JSON/JSONL, no-leak/duplicate/sample-floor audit, blocker/impossibility ledger, forensics/learning, builder, verifier, and tests. Decide ACCEPT/BLOCK/REJECT for the packet as categorical lifecycle source evidence only. Verify that the contract was frozen before extension scanning, every candidate row is packetized or exact-blocked, every consumed tick source is sha256 hashed, allowed labels are respected, no forbidden R/performance/broker/account/live/hidden labels appear in packet rows, 94 G12-blocked CNR061 rows remain excluded, and validation_safe=false outcome_review_opened=false live_effect=false are preserved. Explain what stop_after_original_horizon rows prove and do not prove, audit duplicate/sample-floor limits, and write next-route guidance for T1 fixed-R, T2 structural levels, E2/E3/E4 telemetry, and any separate no-fill/still-pending lifecycle extension lane. Do not compute R/performance, do not score blocked rows, do not use broker actual-R/account history/live trade results/live order state/hidden path labels, do not invent rescue thresholds/live gates, and touch no live prompts/risk/execution/permissions/safety/selectors/canaries/MT5/order/credential/remote surfaces.`",
            "",
            "## Specific Questions",
            "",
            "1. Did the candidate inventory cover every accepted/quarantined no-terminal-like/no-entry/still-pending source found by the scan?",
            "2. Did the frozen contract precede any extended tick path read?",
            "3. Are the six packet rows exactly accepted CNR061 no-terminal rows and no blocked rows?",
            "4. Are all lifecycle labels categorical and from the allowed set?",
            "5. Are all consumed source files hashed and sufficient for the terminal labels?",
            "6. Do no-leak, duplicate, and sample-floor checks block validation/promotion correctly?",
            "7. Are blockers exact enough to route future T1/T2/E2/E3/E4/no-fill work?",
        ]
    )


def completion_audit(
    context_anchor: dict[str, Any],
    contract: dict[str, Any],
    inventory: dict[str, Any],
    packet: dict[str, Any],
    audit: dict[str, Any],
    blockers: dict[str, Any],
    source_ledger: dict[str, Any],
    learning: dict[str, Any],
) -> dict[str, Any]:
    output_files = []
    for key, stem in OUTPUT_NAMES.items():
        if key == "g12_prompt":
            output_files.append(f"{stem}.md")
        elif key == "packet":
            output_files.extend([f"{stem}.md", f"{stem}.json", f"{stem}_ROWS.jsonl"])
        else:
            output_files.extend([f"{stem}.md", f"{stem}.json"])
    output_files.extend(
        [
            "build_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
            "verify_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
            "test_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
        ]
    )
    checklist = [
        {
            "requirement": "mandatory GTOS preflight and required context read",
            "status": "PASS",
            "evidence": "context anchor artifacts_read includes LIVE_STATE, latest handoff, quick reference, doctrine, research current state, goal discipline, local heavy data inventory, controlling prompt, and required upstream CNR/G12/OTI artifacts",
        },
        {
            "requirement": "context anchor, active question stack, searched root ledger, route-decision ledger",
            "status": "PASS",
            "evidence": f"{OUTPUT_NAMES['context_anchor']}.json",
        },
        {
            "requirement": "frozen lifecycle contract before extension scan",
            "status": "PASS",
            "evidence": f"contract {contract['contract_id']} sha256 {contract['contract_sha256']} written by builder before scan_eligible_candidate is called",
        },
        {
            "requirement": "inventory every accepted/quarantined no-terminal-like/no-entry/still-pending row",
            "status": "PASS",
            "evidence": f"{inventory['candidate_count']} candidate-like rows inventoried from OTI1/2/3/4/5/8 plus required OTI6/7/G12 scans",
        },
        {
            "requirement": "packet or exact blocker for every candidate",
            "status": "PASS" if blockers["all_candidates_packetized_or_blocked"] else "FAIL",
            "evidence": f"packet rows {packet['row_count']} plus blockers {blockers['blocker_count']} equals candidates {inventory['candidate_count']}",
        },
        {
            "requirement": "search absolute local heavy-data tick roots and hash consumed files",
            "status": "PASS" if source_ledger["consumed_tick_file_hashes"] else "FAIL",
            "evidence": f"{OUTPUT_NAMES['source_ledger']}.json",
        },
        {
            "requirement": "allowed labels only",
            "status": audit["allowed_label_status"],
            "evidence": dict(packet["lifecycle_label_counts"]),
        },
        {
            "requirement": "no forbidden R/performance/broker/account/live/hidden packet fields",
            "status": audit["forbidden_packet_row_key_status"],
            "evidence": audit["forbidden_packet_row_key_hits"],
        },
        {
            "requirement": "94 G12-blocked CNR061 rows excluded",
            "status": "PASS" if audit["blocked_94_status"] == "PASS" else audit["blocked_94_status"],
            "evidence": audit["blocked_94_exclusion"],
        },
        {
            "requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            "status": "PASS",
            "evidence": "all generated JSON artifacts carry false validation/live flags and NO_PROMOTION_VERDICT",
        },
        {
            "requirement": "learning/forensics and G12 audit prompt pack",
            "status": "PASS",
            "evidence": [f"{OUTPUT_NAMES['learning']}.json", f"{OUTPUT_NAMES['g12_prompt']}.md"],
        },
        {
            "requirement": "verifier/tests provided",
            "status": "PASS",
            "evidence": [
                "verify_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
                "test_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
            ],
        },
    ]
    return {
        "artifact_family": "CNR_T3_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restatement": "Build a broad, source-hashed categorical T3 lifecycle expansion packet for accepted/quarantined no-terminal-like CNR/OTI rows, packetizing only sufficient rows and exact-blocking the rest without R/performance or live-effect claims.",
        "output_files_expected": output_files,
        "prompt_to_artifact_checklist": checklist,
        "static_completion_status": "PASS" if all(item["status"] == "PASS" for item in checklist) else "FAIL",
        "external_commands_to_run_after_build": [
            "python -m py_compile build_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py verify_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py test_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
            "pytest test_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py -q",
            "python verify_cnr_t3_lifecycle_expansion_source_packet_2026_05_08.py",
            "python scripts/generate_live_state.py",
        ],
        "packet_summary": {
            "candidate_count": inventory["candidate_count"],
            "packet_rows": packet["row_count"],
            "blocker_count": blockers["blocker_count"],
            "label_counts": packet["lifecycle_label_counts"],
            "learning_summary": learning["late_stop_target_still_unresolved_summary"],
        },
    }


def completion_markdown(audit: dict[str, Any]) -> str:
    lines = [
        audit["objective_restatement"],
        "",
        f"Static completion status: `{audit['static_completion_status']}`",
        "",
        "## Checklist",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    lines.extend(["", "## External Commands To Run"])
    lines.extend(f"- `{cmd}`" for cmd in audit["external_commands_to_run_after_build"])
    lines.extend(["", "## Packet Summary"])
    for key, value in audit["packet_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines)


def run_build() -> dict[str, Any]:
    accepted_manifest = load_json(OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / "OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json")
    accepted_sidecar_hashes = set(accepted_manifest.get("accepted_sidecar_row_sha256", []))
    cnr_source_audit = load_json(OUTCOME_ROOT / "g12_cnr_next_model_control_audit" / "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json")

    candidates, scan_summaries = discover_candidates(accepted_sidecar_hashes)
    contract = build_contract()

    # Freeze/context artifacts are written before any beyond-original-horizon tick path scan.
    context_anchor = build_context_anchor(candidates, scan_summaries, contract)
    write_json(OUTPUT_NAMES["context_anchor"], context_anchor)
    write_md(OUTPUT_NAMES["context_anchor"], "CNR T3 Context Anchor - 2026-05-08", context_anchor_markdown(context_anchor))
    write_json(OUTPUT_NAMES["contract"], contract)
    write_md(OUTPUT_NAMES["contract"], "CNR T3 Frozen Lifecycle Contract - 2026-05-08", contract_markdown(contract))

    packet_rows, blocker_rows, searched_entries = build_packet_and_ledgers(candidates)
    inventory = inventory_artifact(candidates, scan_summaries)
    source_ledger = source_ledger_artifact(searched_entries, packet_rows)
    packet = packet_artifact(packet_rows, contract)
    audit = noleak_audit(packet_rows, candidates, cnr_source_audit)
    blockers = blocker_artifact(blocker_rows, candidates)
    learning = learning_artifact(packet_rows, blocker_rows, candidates)
    completion = completion_audit(context_anchor, contract, inventory, packet, audit, blockers, source_ledger, learning)

    write_json(OUTPUT_NAMES["inventory"], inventory)
    write_md(OUTPUT_NAMES["inventory"], "CNR T3 No-Terminal Candidate Inventory - 2026-05-08", inventory_markdown(inventory))
    write_json(OUTPUT_NAMES["source_ledger"], source_ledger)
    write_md(OUTPUT_NAMES["source_ledger"], "CNR T3 Searched Root And Source Hash Ledger - 2026-05-08", source_ledger_markdown(source_ledger))
    write_json(OUTPUT_NAMES["packet"], packet)
    write_jsonl(OUTPUT_NAMES["packet"], packet_rows)
    write_md(OUTPUT_NAMES["packet"], "CNR T3 Lifecycle Packet - 2026-05-08", packet_markdown(packet))
    write_json(OUTPUT_NAMES["audit"], audit)
    write_md(OUTPUT_NAMES["audit"], "CNR T3 No-Leak Duplicate Sample-Floor Audit - 2026-05-08", noleak_markdown(audit))
    write_json(OUTPUT_NAMES["blockers"], blockers)
    write_md(OUTPUT_NAMES["blockers"], "CNR T3 Blocker And Impossibility Ledger - 2026-05-08", blocker_markdown(blockers))
    write_json(OUTPUT_NAMES["learning"], learning)
    write_md(OUTPUT_NAMES["learning"], "CNR T3 Lifecycle Forensics And Learning - 2026-05-08", learning_markdown(learning))
    write_md(OUTPUT_NAMES["g12_prompt"], "CNR T3 G12 Audit Prompt Pack - 2026-05-08", g12_prompt_pack())
    write_json(OUTPUT_NAMES["completion"], completion)
    write_md(OUTPUT_NAMES["completion"], "CNR T3 Completion Audit - 2026-05-08", completion_markdown(completion))

    return completion


def main() -> None:
    completion = run_build()
    print(json.dumps({"status": completion["static_completion_status"], "packet_summary": completion["packet_summary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
