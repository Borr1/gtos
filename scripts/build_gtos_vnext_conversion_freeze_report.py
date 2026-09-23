from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder"
MASTER_LEDGER_PATH = BUILDER_DIR / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"
MASTER_SUMMARY_PATH = BUILDER_DIR / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json"
BATCH_LEDGER_PATH = BUILDER_DIR / "GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"
BATCH_SUMMARY_PATH = BUILDER_DIR / "GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json"
FREEZE_LEDGER_PATH = BUILDER_DIR / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_CLASSIFICATION_LEDGER_2026-05-23.jsonl"
FREEZE_SUMMARY_PATH = BUILDER_DIR / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_SUMMARY_2026-05-23.json"
FREEZE_REPORT_PATH = BUILDER_DIR / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_REPORT_2026-05-23.md"
CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"

FREEZE_CLASSES = {
    "DIRECT_RUNTIME_CONVERSION_REQUIRED",
    "TESTED_SOURCE_REPAIR_OR_GUARD_REQUIRED",
    "REPLAY_ATTRIBUTION_ONLY_PARK",
    "LEGACY_OR_STALE_NON_OVERRIDE_PARK",
    "WRAPPER_SUPPORT_CHILDREN_ALREADY_HANDLED_KILL",
    "DUPLICATE_OR_SUPERSEDED_KILL",
    "NEEDS_USER_DECISION_BEFORE_RUNTIME",
}

ROW_BEARING_SUFFIXES = {".csv", ".gz", ".json", ".jsonl", ".parquet"}
TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}
SYMBOL_TOKENS = ("XAUUSD", "XAGUSD", "GBPJPY", "GBPUSD", "USDJPY", "US30", "US30_cash", "NAS100", "NDX100")
TIMEFRAME_TOKENS = ("M1", "M5", "M15", "H1", "H4", "D1")
SESSION_TOKENS = ("london", "ny", "tokyo", "asia", "kill_zone", "kz")
SIDE_TOKENS = ("LONG", "SHORT", "bullish", "bearish")
ENTRY_EXIT_TOKENS = ("entry", "exit", "target", "stop", "sl", "tp", "fill", "nofill", "pending")
SOURCE_TOKENS = ("source_component", "source_repair", "source_capture", "source_acquisition", "missing_denominator")

WRAPPER_SUPPORT_TOKENS = (
    "manifest",
    "readme",
    "verify",
    "verifier",
    "validation_result",
    "output_manifest",
    "completion_audit",
    "methodology_report",
    "methodology",
    "runbook",
    "checklist",
    "playbook",
    "brief",
    "handoff",
    "audit",
    "report",
    "summary",
)
LEGACY_TOKENS = (
    "legacy",
    "v2",
    "v3",
    "v4",
    "phase_1",
    "phase1",
    "cascade",
    "k54",
    "k55",
    "a1_",
    "a4_",
    "t7",
    "old_",
)
REPLAY_ATTRIBUTION_TOKENS = (
    "shadow",
    "monitoring",
    "observation",
    "observer",
    "forward_capture",
    "source_capture",
    "live_monitoring",
    "trade_journal",
    "replay",
)
USER_DECISION_TOKENS = (
    "deploy",
    "deployment",
    "approval",
    "operator",
    "ceo",
    "decision",
    "pre_deploy",
    "sunday_monday",
)
DIRECT_RUNTIME_TOKENS = (
    "risk",
    "gate",
    "selector",
    "route",
    "entry",
    "exit",
    "target",
    "stop",
    "nofill",
    "pending",
    "ai_",
    "framework",
)
SOURCE_REPAIR_TOKENS = (
    "source_repair",
    "source_acquisition",
    "missing_denominator",
    "source_capture",
    "field_closure",
    "source_gap",
)


def _windows_extended_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    resolved = path.resolve()
    raw = str(resolved)
    if raw.startswith("\\\\?\\"):
        return Path(raw)
    if raw.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + raw[2:])
    return Path("\\\\?\\" + raw)


def _local_path_for_io(path: Path) -> Path:
    return _windows_extended_path(path)


def _local_path_exists(path: Path) -> bool:
    return _local_path_for_io(path).exists()


def _repo_git_dir_for(path: Path) -> Path | None:
    for parent in (path.resolve().parent, *path.resolve().parents):
        git_path = parent / ".git"
        if git_path.is_dir():
            return git_path
        if git_path.is_file():
            try:
                content = git_path.read_text(encoding="utf-8").strip()
            except OSError:
                return None
            prefix = "gitdir:"
            if content.casefold().startswith(prefix):
                raw = content[len(prefix):].strip()
                target = Path(raw)
                if not target.is_absolute():
                    target = parent / target
                return target
    return None


def _resolve_local_git_lfs_pointer(path: Path) -> Path | None:
    try:
        with _local_path_for_io(path).open("rb") as fh:
            first = fh.readline().strip()
            if first.startswith(b"\xef\xbb\xbf"):
                first = first[3:]
            if first != b"version https://git-lfs.github.com/spec/v1":
                return None
            oid_line = fh.readline().strip().decode("ascii", errors="ignore")
    except OSError:
        return None

    prefix = "oid sha256:"
    if not oid_line.startswith(prefix):
        return None
    oid = oid_line[len(prefix):].strip()
    if len(oid) != 64 or any(ch not in "009abcdefABCDEF" for ch in oid):
        return None

    git_dir = _repo_git_dir_for(path)
    if git_dir is None:
        return None
    obj = git_dir / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    return _local_path_for_io(obj) if _local_path_exists(obj) else None


def _read_text(path: Path, *, errors: str = "strict") -> str:
    read_path = _resolve_local_git_lfs_pointer(path) or _local_path_for_io(path)
    return read_path.read_text(encoding="utf-8", errors=errors)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in _read_text(path).splitlines()
        if line.strip()
    ]


def _read_json(path: Path) -> dict:
    return json.loads(_read_text(path))


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _nonempty_line_count(path: Path) -> int | None:
    if not _local_path_exists(path) or _local_path_for_io(path).is_dir():
        return None
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return 1
    if suffix == ".gz":
        return 1
    try:
        return sum(1 for line in _read_text(path, errors="replace").splitlines() if line.strip())
    except OSError:
        return None


def _sample_text(path: Path, limit: int = 200_000) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return ""
    try:
        return _read_text(path, errors="replace")[:limit]
    except OSError:
        return ""


def _has_any(haystack: str, tokens: tuple[str, ...]) -> bool:
    folded = haystack.casefold()
    return any(token.casefold() in folded for token in tokens)


def _anchor_flags(path_text: str, sample: str) -> dict[str, bool]:
    haystack = f"{path_text}\n{sample}"
    return {
        "symbol": _has_any(haystack, SYMBOL_TOKENS),
        "timeframe": _has_any(haystack, TIMEFRAME_TOKENS),
        "session": _has_any(haystack, SESSION_TOKENS),
        "side": _has_any(haystack, SIDE_TOKENS),
        "entry_or_exit": _has_any(haystack, ENTRY_EXIT_TOKENS),
        "source_component_or_repair": _has_any(haystack, SOURCE_TOKENS),
    }


def _classify_open_row(row: dict) -> dict:
    path_text = str(row["source_artifact_path"])
    source_path = REPO_ROOT / path_text
    lower = path_text.casefold()
    suffix = source_path.suffix.lower()
    row_count = _nonempty_line_count(source_path)
    sample = _sample_text(source_path)
    anchors = _anchor_flags(path_text, sample)
    row_bearing = suffix in ROW_BEARING_SUFFIXES and bool(row_count)
    has_usable_anchor = any(anchors.values())
    stale_or_legacy = _has_any(path_text, LEGACY_TOKENS)
    wrapper_support = (
        _has_any(path_text, WRAPPER_SUPPORT_TOKENS)
        or (suffix == ".py" and "/research/" in f"/{lower}")
        or lower.endswith(".md")
    )
    source_repair_candidate = (
        row_bearing
        and has_usable_anchor
        and _has_any(f"{path_text}\n{sample[:20_000]}", SOURCE_REPAIR_TOKENS)
        and not stale_or_legacy
    )
    direct_candidate = (
        row_bearing
        and has_usable_anchor
        and _has_any(f"{path_text}\n{sample[:20_000]}", DIRECT_RUNTIME_TOKENS)
        and not stale_or_legacy
    )

    candidate_signal = "source_repair_or_guard" if source_repair_candidate else (
        "direct_runtime_surface" if direct_candidate else ""
    )

    if wrapper_support:
        freeze_class = "WRAPPER_SUPPORT_CHILDREN_ALREADY_HANDLED_KILL"
        closure_action = "kill_with_computed_evidence"
        reason = (
            "Wrapper, doc, manifest, verifier, script, audit, report, summary, runbook, or support residue has no independent "
            "admitted runtime surface after its row-bearing children were converted or explicitly parked by freeze classification."
        )
    elif stale_or_legacy:
        freeze_class = "LEGACY_OR_STALE_NON_OVERRIDE_PARK"
        closure_action = "park_without_runtime_pressure"
        reason = (
            "Legacy, stale, or old-research material cannot override fresher CP280/CP281/CP282, Main Orch, READY8, expanded-market, "
            "source-bound, or newer moonshot evidence; keep it out of runtime pressure."
        )
    elif _has_any(path_text, REPLAY_ATTRIBUTION_TOKENS):
        freeze_class = "REPLAY_ATTRIBUTION_ONLY_PARK"
        closure_action = "park_for_replay_measurement"
        reason = (
            "Diagnostic, monitoring, shadow, source-capture, or replay residue is useful only for later replay/shadow attribution; "
            "it must not cast route, risk, gate, selector, AI, entry, exit, no-fill, FOLLOW, AVOID, or MIXED pressure."
        )
    elif _has_any(path_text, USER_DECISION_TOKENS):
        freeze_class = "NEEDS_USER_DECISION_BEFORE_RUNTIME"
        closure_action = "park_pending_user_decision"
        reason = (
            "Operational or decision residue requires explicit user direction before it can be considered for runtime behavior."
        )
    else:
        freeze_class = "LEGACY_OR_STALE_NON_OVERRIDE_PARK"
        closure_action = "park_without_runtime_pressure"
        reason = (
            "General residue lacks full admission proof for current runtime conversion and is parked without runtime pressure."
        )

    admission = {
        "row_bearing": row_bearing,
        "concrete_runtime_decision_surface": bool(candidate_signal),
        "usable_anchor": has_usable_anchor,
        "not_duplicated_by_converted_fresher_wave": False,
        "cannot_override_fresher_evidence": True,
        "changes_runtime_behavior_now": False,
        "replay_or_shadow_measurement_path": True,
        "verifiable_without_broadening": True,
    }
    return {
        "schema_version": "gtos_vnext_final_conversion_freeze_classification_v1",
        "unit_id": row["intelligence_unit_id"],
        "execution_position": row["execution_position"],
        "source_artifact_path": path_text,
        "source_artifact_hash": row.get("source_artifact_hash", ""),
        "source_artifact_hash_algorithm": row.get("source_artifact_hash_algorithm", ""),
        "pre_freeze_conversion_state": row["conversion_state"],
        "pre_freeze_evidence_family": row.get("evidence_family", ""),
        "pre_freeze_runtime_surface": row.get("affected_runtime_surface", ""),
        "freeze_class": freeze_class,
        "closure_action": closure_action,
        "post_freeze_candidate_signal": candidate_signal,
        "row_count": row_count,
        "row_bearing": row_bearing,
        "anchor_flags": anchors,
        "has_usable_anchor": has_usable_anchor,
        "admission_rule": admission,
        "runtime_pressure_allowed": False,
        "candidate_use_allowed_now": False,
        "broker_operation_permitted": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "legacy_support_override_allowed": False,
        "follow_avoid_mixed_pressure_allowed": False,
        "exact_reason": reason,
        "tests_verifier": (
            "scripts/build_gtos_vnext_conversion_freeze_report.py --check; "
            "tests/test_gtos_vnext_conversion_freeze.py"
        ),
        "post_freeze_action": (
            "Do not convert in this session. Use the freeze report as replay/ablation handoff; "
            "future runtime work requires a fresh explicit admission review."
        ),
    }


def _runtime_artifact_rows() -> list[dict]:
    try:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except OSError:
        return []
    paths = config.get("gtos_vnext_runtime", {}).get("artifact_paths", [])
    rows: list[dict] = []
    seen: set[str] = set()
    for raw in paths:
        path = REPO_ROOT / str(raw)
        if str(path) in seen or not _local_path_exists(path) or path.suffix.lower() != ".jsonl":
            continue
        seen.add(str(path))
        for line in _read_text(path, errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload["_artifact_path"] = _rel(path)
            rows.append(payload)
    return rows


def _counter_from_rows(rows: list[dict], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "") for row in rows if str(row.get(key) or "")).items()))


def build_freeze() -> tuple[list[dict], dict, str]:
    master_rows = _read_jsonl(MASTER_LEDGER_PATH)
    master_summary = _read_json(MASTER_SUMMARY_PATH)
    batch_rows = _read_jsonl(BATCH_LEDGER_PATH)
    batch_summary = _read_json(BATCH_SUMMARY_PATH)
    open_rows = [row for row in master_rows if row.get("conversion_state") == "NOT_STARTED"]
    freeze_rows = [_classify_open_row(row) for row in open_rows]
    runtime_rows = _runtime_artifact_rows()

    class_counts = Counter(row["freeze_class"] for row in freeze_rows)
    closure_counts = Counter(row["closure_action"] for row in freeze_rows)
    row_bearing_counts = Counter("row_bearing" if row["row_bearing"] else "non_row_bearing" for row in freeze_rows)
    anchor_counts = Counter("anchored" if row["has_usable_anchor"] else "blank_or_unusable_anchor" for row in freeze_rows)
    runtime_decision_counts = _counter_from_rows(runtime_rows, "decision")
    runtime_action_counts = _counter_from_rows(runtime_rows, "action_class")
    runtime_source_counts = _counter_from_rows(runtime_rows, "source_component")
    runtime_family_counts = _counter_from_rows(runtime_rows, "evidence_family")
    runtime_symbol_counts = _counter_from_rows(runtime_rows, "symbol")
    runtime_source_symbol_counts = _counter_from_rows(runtime_rows, "source_symbol")
    runtime_timeframe_counts = _counter_from_rows(runtime_rows, "timeframe")
    runtime_session_counts = _counter_from_rows(runtime_rows, "route_session")
    runtime_side_counts = _counter_from_rows(runtime_rows, "side")
    runtime_framework_counts = _counter_from_rows(runtime_rows, "framework")

    freeze_killed = closure_counts["kill_with_computed_evidence"]
    freeze_parked = (
        closure_counts["park_without_runtime_pressure"]
        + closure_counts["park_for_replay_measurement"]
        + closure_counts["park_pending_user_decision"]
    )
    freeze_candidates = closure_counts["post_freeze_candidate"]
    total_units = int(master_summary["total_intelligence_units"])
    pre_freeze_closed = total_units - len(open_rows)
    final_classified = pre_freeze_closed + len(freeze_rows)
    summary = {
        "schema_version": "gtos_vnext_final_conversion_freeze_summary_v1",
        "current_head": "",
        "master_ledger_path": _rel(MASTER_LEDGER_PATH),
        "batch_ledger_path": _rel(BATCH_LEDGER_PATH),
        "classification_ledger_path": _rel(FREEZE_LEDGER_PATH),
        "report_path": _rel(FREEZE_REPORT_PATH),
        "total_units": total_units,
        "pre_freeze_closed_units": pre_freeze_closed,
        "pre_freeze_open_not_started_units": len(open_rows),
        "freeze_classified_units": len(freeze_rows),
        "freeze_killed_units": freeze_killed,
        "freeze_parked_units": freeze_parked,
        "freeze_post_freeze_candidate_units": freeze_candidates,
        "final_unclassified_open_units": 0,
        "final_freeze_coverage_pct": round(100.0 * final_classified / total_units, 4) if total_units else 0.0,
        "freeze_class_counts": dict(sorted(class_counts.items())),
        "closure_action_counts": dict(sorted(closure_counts.items())),
        "row_bearing_counts": dict(sorted(row_bearing_counts.items())),
        "anchor_quality_counts": dict(sorted(anchor_counts.items())),
        "master_state_counts": master_summary.get("state_counts", {}),
        "batch_open_unit_count_before_freeze": batch_summary.get("open_unit_count"),
        "batch_open_wave_count_before_freeze": batch_summary.get("open_wave_count"),
        "executed_wave_count": len(batch_summary.get("current_executed_wave_ids") or []),
        "executed_wave_ids": batch_summary.get("current_executed_wave_ids") or [],
        "generated_runtime_artifact_count": len({row["_artifact_path"] for row in runtime_rows}),
        "generated_runtime_row_count": len(runtime_rows),
        "runtime_decision_counts": runtime_decision_counts,
        "runtime_action_class_counts": runtime_action_counts,
        "runtime_evidence_family_counts": runtime_family_counts,
        "runtime_source_component_counts": runtime_source_counts,
        "markets_symbols_timeframes_sessions_sides": {
            "symbols": runtime_symbol_counts,
            "source_symbols": runtime_source_symbol_counts,
            "timeframes": runtime_timeframe_counts,
            "sessions": runtime_session_counts,
            "sides": runtime_side_counts,
            "frameworks": runtime_framework_counts,
        },
        "runtime_pressure_allowed_for_freeze_rows": False,
        "legacy_support_override_allowed": False,
        "default_off_activation_path": (
            "Keep current vNext runtime/config loaded in shadow/demo mode first; execution-effect flags remain separate from broker operations."
        ),
        "replay_ablation_handoff": (
            "Start a fresh replay/ablation session from disk using this report, current HEAD, active config, master/batch ledgers, "
            "classification ledger, and generated runtime artifact summaries. Do not run replay in the freeze session."
        ),
    }
    report = _build_report(summary, freeze_rows)
    return freeze_rows, summary, report


def _top_paths(rows: list[dict], freeze_class: str, limit: int = 12) -> list[str]:
    return [
        row["source_artifact_path"]
        for row in rows
        if row["freeze_class"] == freeze_class
    ][:limit]


def _build_report(summary: dict, freeze_rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# GTOS vNext Final Conversion Freeze Report")
    lines.append("")
    lines.append(f"- Current checkpoint HEAD: `{summary['current_head'] or 'set-at-write-time'}`")
    lines.append(f"- Master ledger: `{summary['master_ledger_path']}`")
    lines.append(f"- Batch ledger: `{summary['batch_ledger_path']}`")
    lines.append(f"- Freeze classification ledger: `{summary['classification_ledger_path']}`")
    lines.append("")
    lines.append("## Final Counts")
    lines.append("")
    lines.append(f"- Total units: {summary['total_units']}")
    lines.append(f"- Pre-freeze closed units: {summary['pre_freeze_closed_units']}")
    lines.append(f"- Pre-freeze open NOT_STARTED units classified by freeze: {summary['pre_freeze_open_not_started_units']}")
    lines.append(f"- Freeze killed units: {summary['freeze_killed_units']}")
    lines.append(f"- Freeze parked units: {summary['freeze_parked_units']}")
    lines.append(f"- Post-freeze candidate units requiring fresh admission: {summary['freeze_post_freeze_candidate_units']}")
    lines.append(f"- Final unclassified open units: {summary['final_unclassified_open_units']}")
    lines.append(f"- Final classification coverage: {summary['final_freeze_coverage_pct']}%")
    lines.append("")
    lines.append("## Freeze Class Counts")
    lines.append("")
    for key, value in summary["freeze_class_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Executed Waves")
    lines.append("")
    for wave_id in summary["executed_wave_ids"]:
        lines.append(f"- {wave_id}")
    lines.append("")
    lines.append("## Runtime/System Behavior Actually Changed")
    lines.append("")
    lines.append("- Converted runtime artifacts remain the only sources allowed to affect vNext route, risk, selector, gate, no-fill, entry, exit, AI-routing, and source-acquisition behavior.")
    lines.append("- The final lifecycle checkpoint added source-acquisition guards for still-pending, wrong-side, trade-index action-required, and reset-policy lifecycle evidence without candidate-use, broker, paid API, or live-trading effect.")
    lines.append("- Freeze rows add no FOLLOW, AVOID, MIXED, risk, selector, AI, entry, exit, no-fill, gate, broker, or source-component pressure.")
    lines.append("")
    lines.append("## Code/Config/Tests Changed By Final Runtime Checkpoint")
    lines.append("")
    lines.append("- `src/components/gtos_vnext_runtime.py`")
    lines.append("- `config/agent_config.yaml`")
    lines.append("- `scripts/build_gtos_vnext_master_conversion_ledger.py`")
    lines.append("- `scripts/build_gtos_vnext_lifecycle_execution_source_guard_runtime_rows.py`")
    lines.append("- `tests/test_gtos_vnext_runtime.py`")
    lines.append("- `tests/test_gtos_vnext_master_conversion_ledger.py`")
    lines.append("- Freeze checkpoint adds this report, classification ledger, summary, builder script, and freeze tests.")
    lines.append("")
    lines.append("## Generated Runtime Artifacts")
    lines.append("")
    lines.append(f"- Generated runtime artifact count loaded from config: {summary['generated_runtime_artifact_count']}")
    lines.append(f"- Generated runtime row count loaded from config: {summary['generated_runtime_row_count']}")
    lines.append("")
    lines.append("## Markets/Symbols/Timeframes/Sessions/Sides")
    lines.append("")
    for key, value in summary["markets_symbols_timeframes_sessions_sides"].items():
        lines.append(f"- {key}: {json.dumps(value, sort_keys=True)}")
    lines.append("")
    lines.append("## Strategy Families, Entries, Exits, Filters, Gates, Risk, No-Fill, AI Paths")
    lines.append("")
    lines.append(f"- Runtime evidence families: {json.dumps(summary['runtime_evidence_family_counts'], sort_keys=True)}")
    lines.append(f"- Runtime source components: {json.dumps(summary['runtime_source_component_counts'], sort_keys=True)}")
    lines.append("- Entries/exits/no-fill/risk/gate/filter/AI paths are only those already represented in generated runtime artifacts and active config before this freeze report.")
    lines.append("")
    lines.append("## FOLLOW/AVOID/MIXED Totals")
    lines.append("")
    lines.append(f"- Runtime decision totals: {json.dumps(summary['runtime_decision_counts'], sort_keys=True)}")
    lines.append("- MIXED means scoped source-acquisition, replay attribution, context guard, or non-directional guard rows already admitted by converted runtime artifacts; freeze residue cannot add broad MIXED context.")
    lines.append("")
    lines.append("## Remaining Direct Runtime Candidates")
    lines.append("")
    direct = _top_paths(freeze_rows, "DIRECT_RUNTIME_CONVERSION_REQUIRED", 30)
    source_repair = _top_paths(freeze_rows, "TESTED_SOURCE_REPAIR_OR_GUARD_REQUIRED", 30)
    lines.append(f"- DIRECT_RUNTIME_CONVERSION_REQUIRED count: {summary['freeze_class_counts'].get('DIRECT_RUNTIME_CONVERSION_REQUIRED', 0)}")
    for path in direct:
        lines.append(f"  - `{path}`")
    lines.append(f"- TESTED_SOURCE_REPAIR_OR_GUARD_REQUIRED count: {summary['freeze_class_counts'].get('TESTED_SOURCE_REPAIR_OR_GUARD_REQUIRED', 0)}")
    for path in source_repair:
        lines.append(f"  - `{path}`")
    lines.append("")
    lines.append("## Parked/Killed Residue")
    lines.append("")
    for freeze_class in (
        "REPLAY_ATTRIBUTION_ONLY_PARK",
        "LEGACY_OR_STALE_NON_OVERRIDE_PARK",
        "NEEDS_USER_DECISION_BEFORE_RUNTIME",
        "WRAPPER_SUPPORT_CHILDREN_ALREADY_HANDLED_KILL",
        "DUPLICATE_OR_SUPERSEDED_KILL",
    ):
        lines.append(f"- {freeze_class}: {summary['freeze_class_counts'].get(freeze_class, 0)}")
        for path in _top_paths(freeze_rows, freeze_class):
            lines.append(f"  - `{path}`")
    lines.append("")
    lines.append("## Evidence Not Allowed To Affect Runtime Decisions")
    lines.append("")
    lines.append("- Every row in the freeze classification ledger has `runtime_pressure_allowed=false` and `legacy_support_override_allowed=false`.")
    lines.append("- Parked legacy/general/support/source-capture residue cannot cast FOLLOW, AVOID, MIXED, risk, selector, AI, entry, exit, no-fill, source-component, or gate pressure.")
    lines.append("- Legacy/v2/v3/v4/live-shadow/support residue cannot override CP280/CP281/CP282, Main Orch, READY8, expanded-market, source-bound, or newer moonshot evidence.")
    lines.append("")
    lines.append("## Default-Off Activation / Replay / Shadow Path")
    lines.append("")
    lines.append("- Keep actual broker operations separate.")
    lines.append("- Use current vNext runtime/config on a demo/free live account first to observe live broker cadence, retcodes, no-fill/pending lifecycle, vNext decisions, risk multipliers, route narrowing, SL/TP geometry, and logs.")
    lines.append("- Run offline replay/ablation from disk in a fresh session using active config, master/batch ledgers, runtime artifact summaries, and this freeze classification ledger.")
    lines.append("")
    lines.append("## Replay/Ablation Measurement Plan")
    lines.append("")
    lines.append("- Baseline: replay current HEAD with vNext artifacts loaded and freeze residue excluded from runtime pressure.")
    lines.append("- Ablation: compare route/risk/gate/no-fill/AI decisions with vNext artifact families disabled by family buckets, not by old file order.")
    lines.append("- Shadow: record matched artifact IDs, source components, decision class, risk multiplier, source-acquisition zero-risk blocks, no-fill lifecycle transitions, and SL/TP geometry deltas.")
    lines.append("- Report: measure decision deltas, no-fill lifecycle deltas, stop-first/fill-quality changes, risk multiplier distribution, and any blank-anchor match attempts.")
    lines.append("")
    lines.append("## Risks Before Replay")
    lines.append("")
    lines.append("- Artifact matching must be monitored for blank-anchor rows and broad context rows.")
    lines.append("- Demo/live observation must confirm broker retcodes, pending lifecycle, no-fill lifecycle, route narrowing, and logs before any funded-account consideration.")
    lines.append("- Parked residue may still contain historical insight, but it is intentionally barred from runtime pressure until a fresh explicit admission review.")
    lines.append("")
    lines.append("## Handoff Instruction")
    lines.append("")
    lines.append("Start a fresh replay/ablation session from disk using this report, current HEAD, active config, current master and batch ledgers, generated runtime artifact summaries, and the freeze classification ledger. Do not continue conversion-wave selection from old context. Do not run replay in this freeze session.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(freeze_rows: list[dict], summary: dict, report: str) -> None:
    try:
        import subprocess

        summary["current_head"] = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
        ).strip()
        report = report.replace("`set-at-write-time`", f"`{summary['current_head']}`")
    except Exception:
        pass
    with FREEZE_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as f:
        for row in freeze_rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    FREEZE_SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    FREEZE_REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")


def _check_outputs(freeze_rows: list[dict], summary: dict, report: str) -> int:
    expected_rows = "\n".join(json.dumps(row, sort_keys=True) for row in freeze_rows) + "\n"
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    try:
        existing_summary = json.loads(FREEZE_SUMMARY_PATH.read_text(encoding="utf-8"))
        if existing_summary.get("current_head"):
            summary["current_head"] = existing_summary["current_head"]
            expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
            report = report.replace("`set-at-write-time`", f"`{summary['current_head']}`")
    except (OSError, json.JSONDecodeError):
        pass
    checks = {
        FREEZE_LEDGER_PATH: expected_rows,
        FREEZE_SUMMARY_PATH: expected_summary,
        FREEZE_REPORT_PATH: report,
    }
    mismatches = [str(path) for path, expected in checks.items() if not path.exists() or path.read_text(encoding="utf-8") != expected]
    if mismatches:
        print(json.dumps({"status": "mismatch", "paths": mismatches}, sort_keys=True))
        return 1
    print(json.dumps({"status": "ok", "freeze_rows": len(freeze_rows)}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    freeze_rows, summary, report = build_freeze()
    if args.check:
        return _check_outputs(freeze_rows, summary, report)
    write_outputs(freeze_rows, summary, report)
    print(json.dumps({"freeze_rows": len(freeze_rows), "summary": summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
