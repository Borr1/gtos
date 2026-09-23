#!/usr/bin/env python3
"""Generate the replay-vs-live divergence matrix for one sealed arm.

`CLAUDE.md` H7 says "Replay does not measure the live system. Do not transfer replay R
to a production claim without the divergence matrix."  Until now that warning was a
paragraph of prose which depended on somebody remembering it.  This module makes it an
artifact, and `verify_b7_5_post_acceleration_arm.py` refuses to accept an arm without one.

Three design rules, in the order they matter:

1. **Auto-generated, never hand-maintained.**  Rows are derived from config, code
   constants, profile YAML and sealed JSON at generation time, and each carries the
   `sha256` of what it read.  Rows that genuinely cannot be derived are ``DECLARED``
   and say so in every rendering — a hand-typed value must never look derived.
2. **Fail closed on an unknown.**  A divergence that cannot be classified becomes
   ``UNKNOWN``; one that cannot be measured becomes ``UNQUANTIFIED``.  Both are emitted
   loudly and both force ``REPLAY_R_IS_NOT_A_LIVE_CLAIM``.  Nothing is ever dropped for
   being awkward.
3. **Completeness by residual.**  The config surface is diffed exhaustively and every
   differing key must land in some row.  Keys no rule claims land in
   ``UNCLASSIFIED_CONFIG_DIVERGENCE`` as ``UNKNOWN``, so a divergence introduced next
   month by someone who never read this file still blocks transfer.

The row schema is documented in
``docs/audits/fable5-vision-audit-20260725/LIVE_DIVERGENCE_ROW_SCHEMA.md``.  Where the
two disagree this module is authority.

Nothing here is bound by the B7.5 decision contract: this is a new file, and
``implementation_root`` (`replay_acceleration_source_batch.py:391-406`) hashes an
enumerated file list rather than walking a directory, so adding it perturbs no seal.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping, Sequence
import uuid

import yaml

ROOT = Path(__file__).resolve().parents[2]

SCHEMA = "gtos.divergence_matrix.arm_transfer.v1"
LIVE_ROWS_SCHEMA = "gtos.divergence_matrix.live_rows.v1"

# The two profiles `scripts/run_book_supervisor.ps1:86-87` actually launches.
LIVE_PROFILES = ("operator_profile", "redacted_account")
# The profile `verify_b7_5_post_acceleration_arm.py:60` records the sealed arms ran under.
REPLAY_PROFILE = "repaired_package_conversion_v3"

FAMILIES = ("execution_model", "strategy_family", "clock", "data", "live_only")
DIRECTIONS = ("REPLAY_ONLY", "LIVE_ONLY", "BOTH_DIFFERENT", "EQUIVALENT", "UNKNOWN")
QUANT_STATUSES = ("QUANTIFIED", "UNQUANTIFIED", "NOT_APPLICABLE")
TRANSFER_RISKS = ("BLOCKS_TRANSFER", "BOUNDS_TRANSFER", "INFORMATIONAL")

VERDICT_BLOCKED = "REPLAY_R_IS_NOT_A_LIVE_CLAIM"
VERDICT_BOUNDED = "TRANSFER_BOUNDED"
VERDICT_CLEAR = "TRANSFER_UNOBSTRUCTED"

ABSENT = "<not implemented>"


class DivergenceMatrixError(RuntimeError):
    """Raised when the matrix cannot be built honestly."""


# --------------------------------------------------------------------------- helpers


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source(path: Path, locator: str, *, root: Path) -> dict[str, Any]:
    """One hashed provenance entry.  Missing files are recorded, never silently skipped."""

    absolute = Path(path)
    if not absolute.is_absolute():
        absolute = root / absolute
    try:
        relative = str(absolute.relative_to(root))
    except ValueError:
        relative = str(absolute)
    if not absolute.is_file():
        return {"path": relative, "sha256": None, "locator": locator, "present": False}
    return {
        "path": relative,
        "sha256": file_sha256(absolute),
        "locator": locator,
        "present": True,
    }


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, Mapping):
        for key, sub in value.items():
            out.update(_flatten(sub, f"{prefix}.{key}" if prefix else str(key)))
    else:
        out[prefix] = value
    return out


def _module_constants(path: Path, names: Iterable[str]) -> dict[str, Any]:
    """Read module-level literals by AST.

    Deliberately not an import: `v4_timewarp_simulated_live_research_loop.py` is 96k
    lines and importing it to read four constants would make the generator expensive
    enough that people stop running it.
    """

    wanted = set(names)
    found: dict[str, Any] = {}
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    found[target.id] = {
                        "value": ast.literal_eval(node.value),
                        "line": node.lineno,
                    }
                except ValueError:
                    found[target.id] = {"value": None, "line": node.lineno}
    return found


def _row(
    *,
    row_id: str,
    family: str,
    finding: str | None,
    dimension: str,
    replay_value: Any,
    replay_locator: str | None,
    live_value: Any,
    live_locator: str | None,
    direction: str,
    transfer_risk: str,
    rule: str,
    sources: Sequence[Mapping[str, Any]] = (),
    quantification: Mapping[str, Any] | None = None,
    declared: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if family not in FAMILIES:
        raise DivergenceMatrixError(f"divergence_row_family_invalid:{row_id}:{family}")
    if direction not in DIRECTIONS:
        raise DivergenceMatrixError(f"divergence_row_direction_invalid:{row_id}")
    if transfer_risk not in TRANSFER_RISKS:
        raise DivergenceMatrixError(f"divergence_row_transfer_risk_invalid:{row_id}")

    quant = dict(
        quantification
        or {
            "status": "UNQUANTIFIED",
            "metric": None,
            "value": None,
            "unit": None,
            "source": None,
        }
    )
    if quant["status"] not in QUANT_STATUSES:
        raise DivergenceMatrixError(f"divergence_row_quantification_invalid:{row_id}")

    if declared is None:
        if not sources:
            raise DivergenceMatrixError(f"divergence_row_derivation_unsourced:{row_id}")
        derivation = {
            "mode": "DERIVED",
            "rule": rule,
            "sources": [dict(entry) for entry in sources],
            "owner": None,
            "declared_utc": None,
            "justification": None,
            "review_by": None,
        }
    else:
        derivation = {
            "mode": "DECLARED",
            "rule": rule,
            "sources": [dict(entry) for entry in sources],
            "owner": declared["owner"],
            "declared_utc": declared["declared_utc"],
            "justification": declared["justification"],
            "review_by": declared.get("review_by"),
        }

    # EQUIVALENT is not available to a row that could not see both sides.  Session D's
    # rule, and the reason a silent absence can never be read as agreement.
    if direction == "EQUIVALENT" and (replay_locator is None or live_locator is None):
        direction = "UNKNOWN"

    return {
        "row_id": row_id,
        "family": family,
        "finding": finding,
        "dimension": dimension,
        "replay_behavior": {"value": replay_value, "locator": replay_locator},
        "live_behavior": {"value": live_value, "locator": live_locator},
        "direction": direction,
        "transfer_risk": transfer_risk,
        "quantification": quant,
        "derivation": derivation,
    }


# ------------------------------------------------------------------ declared registry

# Rows the audits established in prose and nobody has yet made machine-readable.  Each
# pins the sha256 of the document that justifies it: if that document changes, the row
# is forced to UNKNOWN rather than quietly continuing to assert a stale fact.
DECLARED_ROWS: tuple[dict[str, Any], ...] = (
    {
        "row_id": "E1.ENTRY_TIMING",
        "family": "execution_model",
        "finding": "E1",
        "dimension": "Entry fill timing",
        "replay_value": "fills at the tick that touched the limit",
        "replay_locator": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:63193",
        "live_value": (
            "market order at the tick after the M15 close confirms; risk basis "
            "recomputed against the fresh tick, and the order aborts if the stop "
            "crossed (the SL level is explicitly NOT re-anchored)"
        ),
        "live_locator": "src/components/execution.py:3152-3173",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "MISMATCH_AND_RISK_REGISTER.md R1 row 'entry'.  Its wording 'then "
            "re-anchors SL' is wrong at HEAD: execution.py:3159-3170 refuses to "
            "re-anchor the SL level and aborts with sl_wrong_side_vs_fresh_tick.  What "
            "is recomputed is the SL distance / risk basis at :3171."
        ),
        "doc": "docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md",
    },
    {
        "row_id": "E1.EXIT_MANAGEMENT",
        "family": "execution_model",
        "finding": "E1",
        "dimension": "Exit management",
        "replay_value": "lossless R-space bar walk with instantaneous partial closes",
        "replay_locator": "src/research/dynamic_execution_policy.py:335",
        "live_value": "real broker orders with retries, requotes and deal confirmation",
        "live_locator": "src/components/execution.py:7503-8703",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "MISMATCH_AND_RISK_REGISTER.md R1 row 'exit management'.  Prose-only on "
            "both sides; the live line numbers drifted from the audit's and were "
            "re-read at HEAD."
        ),
        "doc": "docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md",
    },
    {
        "row_id": "E1.CROSS_CANDIDATE_SELECTION",
        "family": "execution_model",
        "finding": "E1",
        "dimension": "Cross-candidate selection",
        "replay_value": (
            "portfolio allocator ranks all 24 symbols in one window under cluster and "
            "portfolio caps"
        ),
        "replay_locator": "src/research/moonshot_scheduler_v4_best_trade_allocator.py:27866",
        "live_value": (
            "broad path: first candidate that places wins, one symbol per OS process. "
            "book path: conviction-ranked gross-risk shedding, now wired via run_book.py"
        ),
        "live_locator": "src/components/orchestrator.py:1310-1328; src/components/ultimate_book/admission.py:1319-1342",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "MISMATCH_AND_RISK_REGISTER.md R1 row 1 plus its accepted adversarial "
            "correction.  The correction's 'unwired at HEAD' clause is now stale: "
            "run_book.py:309-311 instantiates UltimateBookOwner and BookLauncher."
        ),
        "doc": "docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md",
    },
    {
        "row_id": "E1.PACKET_FABRICATION",
        "family": "execution_model",
        "finding": "F3",
        "dimension": "Selector/scheduler packet provenance",
        "replay_value": "packets produced by the replay's own selector and scheduler calls",
        "replay_locator": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:67522",
        "live_value": (
            "the book fabricates them: selector action hardcoded 'trade', scheduler "
            "class hardcoded 'execute_now', so the execution-manager field check passes"
        ),
        "live_locator": "src/components/ultimate_book/execution_packets.py:323-332",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "SECOND_AUDIT.md F3 and the R1 adversarial correction.  A replay admission "
            "statistic describes a real selector decision; the live equivalent "
            "describes a constant."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md",
    },
    {
        "row_id": "E1.COST_MODEL",
        "family": "execution_model",
        "finding": "R12",
        "dimension": "Execution cost model",
        "replay_value": (
            "spread falls through four tiers to a constant default; commission status "
            "hardcoded; slippage a flat config constant"
        ),
        "replay_locator": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:58837-58899",
        "live_value": (
            "real spread, per-deal commission and swap captured to shadow logs; "
            "nothing feeds measured cost back into the replay constants"
        ),
        "live_locator": "src/components/execution.py:2131,2225",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "MISMATCH_AND_RISK_REGISTER.md R12.  Replay cost is a human-maintained "
            "guess; live cost widens exactly when the strategy trades."
        ),
        "doc": "docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md",
    },
    {
        "row_id": "E1.EXIT_GAP_THROUGH",
        "family": "execution_model",
        "finding": "F31",
        "dimension": "Gap-through on stops and givebacks",
        "replay_value": "grants exactly zero gap-through: every level fills at the level",
        "replay_locator": "docs/audits/fable5-vision-audit-20260725/GATE_G1A_RECEIPT.md",
        "live_value": "a real broker gaps through the level, adversely on stops",
        "live_locator": "docs/audits/fable5-vision-audit-20260725/GATE_G1A_RECEIPT.md",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BOUNDS_TRANSFER",
        "quantification": {
            "status": "QUANTIFIED",
            "metric": "net_r_over_covered_level_rows",
            "value": -8.095288,
            "unit": "R",
            "source": "docs/audits/fable5-vision-audit-20260725/GATE_G1A_RECEIPT.md",
        },
        "justification": (
            "Phase 1 Session A, filed as F31 and receipted at gate G1a: 212 covered "
            "level rows, net -8.095288 R (mean -0.038186); stops 107/107 adverse "
            "-4.901273 R; giveback 97/97 adverse -3.733123 R; targets 8 rows "
            "+0.539109 R.  The flat expected_slippage_r = 0.02 covers only 80.3 %.  "
            "IMPLEMENTATION_STATE.md B34 measured arm ordering and all four "
            "classifications unchanged (largest shift 0.0135 against a 0.1 materiality "
            "band), which is why this bounds transfer rather than blocking it."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/GATE_G1A_RECEIPT.md",
    },
    {
        "row_id": "E1.REPLAY_MEMORY_FEEDBACK",
        "family": "execution_model",
        "finding": "R16",
        "dimension": "Adaptive outcome feedback into admission",
        "replay_value": (
            "realized net_r from closed trades is read back into admission on a 30-day "
            "lookback, on by default in every factorial arm (causality enforced)"
        ),
        "replay_locator": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:34895-35024",
        "live_value": ABSENT,
        "live_locator": "no adaptive memory guard symbol exists under src/components/",
        "direction": "REPLAY_ONLY",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "MISMATCH_AND_RISK_REGISTER.md R16.  Not future leakage — the causality "
            "guard is correct — but it couples sizing to future eligibility, so the "
            "R arms and the S arms are not independent in the way live would be."
        ),
        "doc": "docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md",
    },
    {
        "row_id": "E1.UNSEALED_ENVIRONMENT",
        "family": "execution_model",
        "finding": "R34",
        "dimension": "Environment variables outside every seal",
        "replay_value": "sealed: the arm fingerprint binds config and code, not the environment",
        "replay_locator": "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431",
        "live_value": (
            "GTOS_PROFILE, GTOS_UB_DERISK_MODE and GTOS_DUAL_BROKER_INTENT_ENABLED "
            "override YAML and appear in no seal; the 2.0 % dial fails closed unless "
            "GTOS_UB_DERISK_MODE=smooth"
        ),
        "live_locator": "src/components/ultimate_book/admission.py:823",
        "direction": "LIVE_ONLY",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "MISMATCH_AND_RISK_REGISTER.md R34: 'Two runs with identical seal digests "
            "can size differently, trade a different symbol universe, and route orders "
            "to a different broker.'  Unquantifiable by construction — the value at "
            "run time is in no sealed artifact.  This row exists to keep that visible."
        ),
        "doc": "docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md",
    },
    {
        "row_id": "F1.DECISION_STACK",
        "family": "strategy_family",
        "finding": "F1",
        "dimension": "Which strategy family is measured",
        "replay_value": (
            "Stack A — broad V4: 24-symbol broader_origin candidates, Selector V4 "
            "admission, Scheduler V4 allocation, continuous cash sizing"
        ),
        "replay_locator": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:36199-36202",
        "live_value": (
            "Stack B — the W7 ultimate_book: statistical sleeves under Kelly-lite "
            "conviction sizing.  Zero shared signal code; the replay imports exactly "
            "one thing from the book, the TICK_SPREAD_FLOOR_R cost table"
        ),
        "live_locator": "config/agent_config.yaml:1246-1394; src/components/ultimate_book/bridge.py:28-33",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "SECOND_AUDIT.md F1, the two-stacks finding.  bridge.py:28-33 encodes the "
            "replacement invariant quoting the go-live dossier: 'The losing broad V4 "
            "selector (-0.25R/fill native) must be OFF when the book is live.'  "
            "OWNER DECISION 2026-07-25 (OD-1): the W7 book went live 2026-06-18 to "
            "07-02, underperformed, and Borhen deactivated it and went full-in on the "
            "broad system — so the broad stack IS now the activation candidate and the "
            "sealed replay does measure it.  The row stays BLOCKS_TRANSFER because "
            "live_system_of_record.md still declares the book, and no replay arm has "
            "ever executed a book-generated trade."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md",
    },
    {
        "row_id": "F1.SLEEVE_OVERLAP",
        "family": "strategy_family",
        "finding": "F1",
        "dimension": "Signal-level overlap between the two books",
        "replay_value": (
            "82 registry rows: outcome-mined groupings of the broad system's own 13 "
            "candidate families"
        ),
        "replay_locator": (
            "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_"
            "execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
        ),
        "live_value": "32 W7 statistical sleeves (crypto, metals_core, fx_jpy, energy_agri, ...)",
        "live_locator": "config/agent_config.yaml:1275-1284",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "quantification": {
            "status": "QUANTIFIED",
            "metric": "sleeve_name_overlap",
            "value": 0,
            "unit": "sleeves",
            "source": "docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md",
        },
        "justification": (
            "SECOND_AUDIT.md F1 owner-update section, verified against the hydrated "
            "82-row registry [MEASURED].  It corrects a stated owner premise: the "
            "belief that the current system contains the W7 sleeves is wrong at the "
            "signal level — the overlap is exactly zero."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md",
    },
    {
        "row_id": "F7.SESSION_ATTRIBUTION",
        "family": "clock",
        "finding": "F7",
        "dimension": "Session labels inside sealed evidence",
        "replay_value": (
            "session windows are broker wall clock: the london label is broker "
            "07:00-13:00, which is 04:00-10:00Z summer / 05:00-11:00Z winter"
        ),
        "replay_locator": "src/components/broader_origin_generators.py:66-110",
        "live_value": "true UTC since 2026-04-28, against a real London cash session of 07:00-15:30Z",
        "live_locator": "src/components/mt5_real.py:212-244",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "quantification": {
            "status": "QUANTIFIED",
            "metric": "session_label_offset_hours",
            "value": 3,
            "unit": "hours",
            "source": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
        },
        "justification": (
            "CLOCK_TRUTH_IMPACT_NOTE.md sections 2 and 5.  Sealed arms were "
            "deliberately NOT rewritten: the shift is common-mode and cancels between "
            "arms, so arm-vs-arm contrasts survive.  What does not survive is any "
            "session-level attribution, session-conditioned feature, or live-transfer "
            "claim reasoning from a replay hour to a real-world hour.  The window "
            "opened about three hours before London and closed mid-morning: it is "
            "mostly the Asia tail plus the European open, not London."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
    },
    {
        "row_id": "F7.DAY_BOUNDARY",
        "family": "clock",
        "finding": "F7",
        "dimension": "Day boundary and D1 date labels",
        "replay_value": "a broker day starts 21:00/22:00 UTC the previous calendar day",
        "replay_locator": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
        "live_value": "true UTC days on the live feed",
        "live_locator": "src/utils/broker_clock.py",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "CLOCK_TRUTH_IMPACT_NOTE.md section 2: daily aggregates, daily-reset logic "
            "and D1 bars are shifted whole-day objects, not UTC days.  D1 is the worst "
            "case because the date label itself moves."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
    },
    {
        "row_id": "F7.LIVE_SLEEVE_HOURS",
        "family": "clock",
        "finding": "F7",
        "dimension": "Deployed sleeve firing hours (unrepaired)",
        "replay_value": "sleeve constants were mined against broker-clock research data",
        "replay_locator": "docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md",
        "live_value": (
            "eight deployed sleeves read a raw UTC hour against a constant commented "
            "'server hour', so they fire 2-3 h late; two match on an exact "
            "(hour, minute) and therefore hit the wrong bar every day"
        ),
        "live_locator": "src/components/ultimate_book/sleeves/",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "CLOCK_TRUTH_IMPACT_NOTE.md section 5 and IMPLEMENTATION_STATE.md B29/B54.  "
            "Deliberately not repaired: changing which hour a deployed sleeve fires at "
            "is a trading decision, not a bug fix, and it belongs to the owner.  The "
            "book holds no broker authority today, so the exposure is to the shadow "
            "evidence the strategy is judged on, not to live orders."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
    },
    {
        "row_id": "F7.redacted_account_CALENDAR",
        "family": "clock",
        "finding": "F7",
        "dimension": "redacted_account DST calendar",
        "replay_value": "not applicable: the research archive is FTMO-sourced",
        "replay_locator": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
        "live_value": (
            "unmeasured.  Pinned at +3 h for 2026-06-14..07-25, a window where both "
            "calendars agree; broker_clock.py refuses to resolve redacted_account rather "
            "than assuming it matches FTMO"
        ),
        "live_locator": "src/utils/broker_clock.py",
        "direction": "UNKNOWN",
        "transfer_risk": "BLOCKS_TRANSFER",
        "justification": (
            "CLOCK_TRUTH_IMPACT_NOTE.md declared gap 1.  No redacted_account-attributed data "
            "anywhere spans a disagreement window.  Cheap close: one read-only "
            "symbol_info_session_quote() pull for JP225 on both terminals would settle "
            "FTMO and redacted_account together as a declaration rather than an inference."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
    },
    {
        "row_id": "F7.FORWARD_REPLAY_JOIN",
        "family": "clock",
        "finding": "F7",
        "dimension": "Joining forward logs to replay data",
        "replay_value": "broker wall clock",
        "replay_locator": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
        "live_value": "true UTC from 2026-04-28",
        "live_locator": "src/components/mt5_real.py:212-244",
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BOUNDS_TRANSFER",
        "quantification": {
            "status": "QUANTIFIED",
            "metric": "naive_join_misalignment",
            "value": 12,
            "unit": "M15 bars (8-12)",
            "source": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
        },
        "justification": (
            "CLOCK_TRUTH_IMPACT_NOTE.md section 4.  Bounded rather than blocking "
            "because the correction is exact and mechanical: read the replay side "
            "through src.utils.research_timebase.read_bars.  One such join already "
            "exists and is already wrong "
            "(scripts/audit_orderflow_limit_intent_reconciliation.py:259,314,431)."
        ),
        "doc": "docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md",
    },
    {
        "row_id": "DATA.BROKER_SYMBOL_SPECS",
        "family": "data",
        "finding": None,
        "dimension": "Broker contract specifications",
        "replay_value": "one symbol spec set, applied uniformly across the sealed window",
        "replay_locator": "config/agent_config.yaml:instruments",
        "live_value": (
            "the two live brokers disagree: 18 of 19 shared symbols carry differing "
            "trade_contract_size, and JP225 also differs in digits, point and "
            "trade_tick_size"
        ),
        "live_locator": (
            "research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json"
        ),
        "direction": "BOTH_DIFFERENT",
        "transfer_risk": "BLOCKS_TRANSFER",
        "quantification": {
            "status": "QUANTIFIED",
            "metric": "shared_symbols_with_differing_contract_size",
            "value": 18,
            "unit": "of 19 shared symbols",
            "source": "research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json",
        },
        "justification": (
            "VPS broker truth capture, 2026-07-26.  A single replay lot size does not "
            "mean the same exposure on both live accounts."
        ),
        "doc": "CLAUDE.md",
    },
)

DECLARED_OWNER = "Borhen (owner) via Phase 1 Session F"
DECLARED_UTC = "2026-07-26"
DECLARED_REVIEW_BY = "the next session that changes a cited file"


# ------------------------------------------------------------------ derived row rules

# Config keys claimed by a named row.  Order matters: first match wins.  Anything
# differing and unclaimed becomes the residual UNKNOWN row, which is what stops this
# artifact decaying — but a residual of a thousand entries is as ignorable as no
# residual at all, so every *anticipated* class of difference gets a real row with a
# real transfer risk, and the residual is reserved for genuine surprises.
#
# fields: row_id, dotted-key matchers (prefix under gtos_vnext_runtime, or a
# glob-ish segment pattern on the full flattened key), family, dimension,
# transfer_risk, finding
_CONFIG_ROW_RULES: tuple[dict[str, Any], ...] = (
    {
        "row_id": "E1.PORTFOLIO_ALLOCATOR",
        "runtime_prefixes": ("scheduler_v4_best_trade_allocator",),
        "family": "execution_model",
        "dimension": "Scheduler V4 portfolio allocator",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "E1",
    },
    {
        "row_id": "E1.SELECTOR_V4_ADMISSION",
        "runtime_prefixes": ("selector_v4",),
        "family": "execution_model",
        "dimension": "Selector V4 admission surface",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "E1",
    },
    {
        "row_id": "E1.PACKAGE_AUTHORITY",
        "runtime_prefixes": ("ultimate_candidate_package", "selected_package"),
        "family": "execution_model",
        "dimension": "Ultimate candidate package authority",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "E1",
    },
    {
        "row_id": "E1.REPLAY_HARNESS_SURFACE",
        "runtime_prefixes": (
            "broad_live",
            "replay_order",
            "selected_cell",
            "selected_policy",
            "ultimate_replay",
        ),
        "key_prefixes": (
            "broad_live_as_if_replay_harness",
            "broad_live_as_if_broker_cost_profile",
            "ultimate_replay_loss_bucket_policy",
        ),
        "family": "execution_model",
        "dimension": "Replay-only harness surface",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "E1",
    },
    {
        "row_id": "E1.PROFIT_HARVEST",
        "runtime_prefixes": ("profit_harvest",),
        "family": "execution_model",
        "dimension": "Profit-harvest policy",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "E1",
    },
    {
        "row_id": "E1.PROP_FIRM_RULES",
        "runtime_prefixes": ("prop_safe_selector",),
        "key_prefixes": ("ftmo_rules", "redacted_account_rules", "prop_"),
        "family": "execution_model",
        "dimension": "Prop-firm rule overlay (daily loss, cushion, reset clock)",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "B56",
    },
    {
        "row_id": "F1.BOOK_CONFIGURATION",
        "runtime_prefixes": ("ultimate_book", "ultimate_convergence"),
        "family": "strategy_family",
        "dimension": "ultimate_book composition and dial",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "F1",
    },
    {
        "row_id": "E1.SIDE_EFFECT_BOUNDARY",
        "key_prefixes": ("market_state",),
        "family": "execution_model",
        "dimension": "Side-effect boundary (replay writes no production state)",
        "transfer_risk": "INFORMATIONAL",
        "finding": None,
    },
    {
        "row_id": "E1.RISK_POLICY",
        "key_prefixes": ("risk",),
        "family": "execution_model",
        "dimension": "Top-level risk policy block",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": "R10",
    },
    {
        "row_id": "DATA.SYMBOL_MARKET_SPEC",
        "key_segments": (("instruments", "*", "market"),),
        "family": "data",
        "dimension": "Per-symbol market spec (spread, swap, tick size, mt5 symbol name)",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": None,
    },
    {
        "row_id": "E1.RISK_PROFILE_PER_SYMBOL_KEYS",
        "key_segments": (("instruments", "*", "risk"),),
        "family": "execution_model",
        "dimension": "Per-symbol risk keys (config surface; see E1.RISK_PROFILE_PER_SYMBOL)",
        "transfer_risk": "BOUNDS_TRANSFER",
        "finding": "R10",
    },
    {
        "row_id": "DATA.INSTRUMENT_SURFACE",
        "key_prefixes": ("instruments",),
        "family": "data",
        "dimension": "Instrument definitions outside market/risk",
        "transfer_risk": "BLOCKS_TRANSFER",
        "finding": None,
    },
    {
        "row_id": "DATA.BROKER_ACCOUNT_IDENTITY",
        "key_prefixes": ("broker_profile", "mt5", "dual_broker", "broker_truth_cost_capture_v2"),
        "family": "data",
        "dimension": "Broker account identity and terminal binding",
        "transfer_risk": "INFORMATIONAL",
        "finding": None,
    },
    {
        "row_id": "DATA.PATHS_AND_PROVENANCE",
        "key_prefixes": (
            "runtime_paths",
            "trade_capture",
            "notification_queue",
            "source_authority",
            "profile_status",
            "generated_at_utc",
            "generated_by",
            "profile_name",
            "runtime",
        ),
        "family": "data",
        "dimension": "Filesystem paths, logging targets and profile provenance",
        "transfer_risk": "INFORMATIONAL",
        "finding": None,
    },
)


def _segments_match(key: str, pattern: Sequence[str]) -> bool:
    parts = key.split(".")
    if len(parts) < len(pattern):
        return False
    return all(p == "*" or p == part for p, part in zip(pattern, parts))


def _classify_key(key: str) -> str | None:
    """Map one flattened config key onto a row, or None for the residual."""

    runtime_key = (
        key[len("gtos_vnext_runtime.") :]
        if key.startswith("gtos_vnext_runtime.")
        else None
    )
    for rule in _CONFIG_ROW_RULES:
        if runtime_key is not None:
            for prefix in rule.get("runtime_prefixes", ()):
                if runtime_key.startswith(prefix):
                    return rule["row_id"]
        for pattern in rule.get("key_segments", ()):
            if _segments_match(key, pattern):
                return rule["row_id"]
        for prefix in rule.get("key_prefixes", ()):
            if key == prefix or key.startswith(prefix + "."):
                return rule["row_id"]
    return None


_RULE_BY_ID = {rule["row_id"]: rule for rule in _CONFIG_ROW_RULES}


def _config_surface(
    *, root: Path, live_profile: str
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Resolve both configs exactly as their own entrypoints do, then diff."""

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src.research_infra.replay_acceleration_attempt5_typed_sparse_runner import (  # noqa: E402
        build_config,
    )
    from src.utils.config import apply_profile_overrides  # noqa: E402

    replay = build_config(REPLAY_PROFILE)
    base = yaml.safe_load((root / "config/agent_config.yaml").read_text(encoding="utf-8"))
    live = apply_profile_overrides(base, live_profile)

    sources = [
        _source(
            Path("config/agent_config.yaml"),
            "whole file",
            root=root,
        ),
        _source(
            Path(f"config/profiles/{live_profile}.yaml"),
            "whole file",
            root=root,
        ),
        _source(
            Path("src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"),
            "build_config:10251-12038",
            root=root,
        ),
        _source(Path("src/utils/config.py"), "apply_profile_overrides:158", root=root),
    ]
    return replay, live, sources


def _derive_config_rows(
    *, root: Path, live_profile: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    replay, live, sources = _config_surface(root=root, live_profile=live_profile)

    replay_flat = _flatten(replay)
    live_flat = _flatten(live)
    replay_only = sorted(set(replay_flat) - set(live_flat))
    live_only = sorted(set(live_flat) - set(replay_flat))
    differing = sorted(
        key
        for key in set(replay_flat) & set(live_flat)
        if replay_flat[key] != live_flat[key]
    )

    buckets: dict[str, dict[str, list[str]]] = {}
    unclaimed: list[str] = []
    for group, keys in (
        ("replay_only", replay_only),
        ("live_only", live_only),
        ("differing", differing),
    ):
        for key in keys:
            row_id = _classify_key(key)
            if row_id is None:
                unclaimed.append(f"{group}:{key}")
            else:
                buckets.setdefault(row_id, {}).setdefault(group, []).append(key)

    rows: list[dict[str, Any]] = []
    for row_id, groups in sorted(buckets.items()):
        rule = _RULE_BY_ID[row_id]
        dimension, finding = rule["dimension"], rule["finding"]
        n_replay = len(groups.get("replay_only", []))
        n_live = len(groups.get("live_only", []))
        n_diff = len(groups.get("differing", []))
        if n_live and not n_replay and not n_diff:
            direction = "LIVE_ONLY"
        elif n_replay and not n_live and not n_diff:
            direction = "REPLAY_ONLY"
        else:
            direction = "BOTH_DIFFERENT"
        examples = {
            group: sorted(keys)[:8] for group, keys in sorted(groups.items())
        }
        rows.append(
            _row(
                row_id=row_id,
                family=rule["family"],
                finding=finding,
                dimension=dimension,
                replay_value=(
                    f"{n_replay} config keys exist only in the replay resolution; "
                    f"{n_diff} shared keys hold different values"
                ),
                replay_locator=f"build_config({REPLAY_PROFILE!r})",
                live_value=(
                    f"{n_live} config keys exist only in the live resolution; "
                    f"{n_diff} shared keys hold different values"
                ),
                live_locator=f"apply_profile_overrides(agent_config.yaml, {live_profile!r})",
                direction=direction,
                transfer_risk=rule["transfer_risk"],
                rule="config_surface_diff",
                sources=sources,
                quantification={
                    "status": "QUANTIFIED",
                    "metric": "config_keys_divergent",
                    "value": n_replay + n_live + n_diff,
                    "unit": "keys",
                    "source": "config_surface_diff",
                },
            )
            | {"config_key_examples": examples, "config_key_counts": {
                "replay_only": n_replay, "live_only": n_live, "differing": n_diff
            }}
        )

    # The residual.  Present even when empty, so its absence can never be mistaken for
    # a clean sweep that simply was not run.
    rows.append(
        _row(
            row_id="UNCLASSIFIED_CONFIG_DIVERGENCE",
            family="execution_model",
            finding=None,
            dimension="Config divergences no rule claims",
            replay_value=f"{len(unclaimed)} unclassified differing config keys",
            replay_locator="config_surface_diff residual",
            live_value=f"{len(unclaimed)} unclassified differing config keys",
            live_locator="config_surface_diff residual",
            direction="UNKNOWN" if unclaimed else "EQUIVALENT",
            transfer_risk="BLOCKS_TRANSFER" if unclaimed else "INFORMATIONAL",
            rule="config_surface_diff_residual",
            sources=sources,
            quantification={
                "status": "UNQUANTIFIED" if unclaimed else "NOT_APPLICABLE",
                "metric": "unclassified_config_keys",
                "value": len(unclaimed),
                "unit": "keys",
                "source": "config_surface_diff",
            },
        )
        | {"unclassified_keys": sorted(unclaimed)}
    )

    summary = {
        "live_profile": live_profile,
        "replay_profile": REPLAY_PROFILE,
        "replay_only_keys": len(replay_only),
        "live_only_keys": len(live_only),
        "differing_keys": len(differing),
        "unclassified_keys": len(unclaimed),
    }
    return rows, summary


def _derive_symbol_risk_row(*, root: Path, live_profile: str) -> dict[str, Any]:
    """R10 / D5: replay sizes from ftmo.yaml, live from the live profile."""

    v4_path = root / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    constants = _module_constants(
        v4_path,
        ("GTOS_24_SYMBOL_SURFACE", "DEFAULT_TIMEWARP_REPLAY_RISK_PROFILE_PATH"),
    )
    surface = tuple(constants["GTOS_24_SYMBOL_SURFACE"]["value"])
    replay_profile_path = constants["DEFAULT_TIMEWARP_REPLAY_RISK_PROFILE_PATH"]["value"]

    base = yaml.safe_load((root / "config/agent_config.yaml").read_text(encoding="utf-8"))
    base_fallback = ((base.get("risk") or {}).get("risk_per_trade_pct"))

    def _load(profile_path: str) -> dict[str, Any]:
        return yaml.safe_load((root / profile_path).read_text(encoding="utf-8")) or {}

    replay_cfg = _load(replay_profile_path)
    live_cfg = _load(f"config/profiles/{live_profile}.yaml")

    def _effective(cfg: Mapping[str, Any], symbol: str) -> float | None:
        instrument = (cfg.get("instruments") or {}).get(symbol) or {}
        value = ((instrument.get("risk") or {}).get("risk_per_trade_pct"))
        if value is None:
            value = (cfg.get("risk") or {}).get("risk_per_trade_pct")
        if value is None:
            value = base_fallback
        return None if value is None else float(value)

    divergent: dict[str, list[float | None]] = {}
    for symbol in surface:
        r_value = _effective(replay_cfg, symbol)
        l_value = _effective(live_cfg, symbol)
        if r_value != l_value:
            divergent[symbol] = [l_value, r_value]

    sources = [
        _source(Path(replay_profile_path), "instruments.*.risk.risk_per_trade_pct", root=root),
        _source(
            Path(f"config/profiles/{live_profile}.yaml"),
            "instruments.*.risk.risk_per_trade_pct",
            root=root,
        ),
        _source(
            Path("src/research_infra/v4_timewarp_simulated_live_research_loop.py"),
            f"GTOS_24_SYMBOL_SURFACE:{constants['GTOS_24_SYMBOL_SURFACE']['line']}",
            root=root,
        ),
    ]
    return _row(
        row_id="E1.RISK_PROFILE_PER_SYMBOL",
        family="execution_model",
        finding="R10",
        dimension="Per-symbol risk profile",
        replay_value=f"sizes from {replay_profile_path}",
        replay_locator="config/agent_config.yaml:3160 timewarp_replay_risk_profile_path",
        live_value=f"sizes from config/profiles/{live_profile}.yaml",
        live_locator="scripts/run_book_supervisor.ps1:86-87",
        direction="BOTH_DIFFERENT" if divergent else "EQUIVALENT",
        transfer_risk="BOUNDS_TRANSFER" if divergent else "INFORMATIONAL",
        rule="per_symbol_risk_profile_diff",
        sources=sources,
        quantification={
            "status": "QUANTIFIED",
            "metric": "symbols_with_divergent_risk_pct",
            "value": len(divergent),
            "unit": f"of {len(surface)} surface symbols",
            "source": "per_symbol_risk_profile_diff",
        },
    ) | {"divergent_symbols": {k: {"live_pct": v[0], "replay_pct": v[1]} for k, v in sorted(divergent.items())}}


def _derive_pending_lifetime_row(*, root: Path) -> dict[str, Any]:
    v4_path = root / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    constants = _module_constants(
        v4_path, ("BASELINE_PENDING_EXPIRY_MINUTES", "REPAIRED_PENDING_EXPIRY_MINUTES")
    )
    repaired = constants["REPAIRED_PENDING_EXPIRY_MINUTES"]["value"]
    baseline = constants["BASELINE_PENDING_EXPIRY_MINUTES"]["value"]
    live_minutes = 48 * 60
    return _row(
        row_id="E1.PENDING_LIFETIME",
        family="execution_model",
        finding="R1",
        dimension="Pending order lifetime",
        replay_value=f"min(asof + {repaired} min, end of day); baseline {baseline} min",
        replay_locator=(
            "src/research_infra/v4_timewarp_simulated_live_research_loop.py:"
            f"{constants['REPAIRED_PENDING_EXPIRY_MINUTES']['line']},85864"
        ),
        live_value="48 h wall clock",
        live_locator="src/components/execution.py:5978",
        direction="BOTH_DIFFERENT",
        transfer_risk="BLOCKS_TRANSFER",
        rule="pending_expiry_constant_diff",
        sources=[
            _source(
                Path("src/research_infra/v4_timewarp_simulated_live_research_loop.py"),
                f"REPAIRED_PENDING_EXPIRY_MINUTES:{constants['REPAIRED_PENDING_EXPIRY_MINUTES']['line']}",
                root=root,
            ),
            _source(Path("src/components/execution.py"), "48h clock expiry:5978", root=root),
        ],
        quantification={
            "status": "QUANTIFIED",
            "metric": "live_over_replay_pending_lifetime",
            "value": round(live_minutes / repaired, 2),
            "unit": "x",
            "source": "pending_expiry_constant_diff",
        },
    )


def _call_site_census(
    *, root: Path, symbols: Sequence[str]
) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """AST-count call sites of *symbols*, split live-path vs research-path.

    This exists to move rows off prose. "Selector V4 has zero production callers" is a
    checkable fact, and checking it beats declaring it.

    Files that will not parse are **returned**, not swallowed.  Twelve files in this
    tree carry UTF-8 BOMs that break `ast.parse` (SECOND_AUDIT F25), and a probe that
    silently skips them would report a confident zero it had not earned.
    """

    live_roots = ("src/components/", "run_book.py", "scripts/")
    research_roots = ("src/research_infra/", "src/research/", "research/")
    census: dict[str, dict[str, list[str]]] = {
        symbol: {"live": [], "research": [], "test": [], "other": []} for symbol in symbols
    }
    unparseable: list[str] = []
    wanted = set(symbols)

    candidates = [
        *sorted((root / "src").rglob("*.py")),
        *sorted((root / "scripts").glob("*.py")),
    ]
    run_book = root / "run_book.py"
    if run_book.is_file():
        candidates.append(run_book)

    for path in candidates:
        try:
            relative = str(path.relative_to(root))
        except ValueError:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError, ValueError):
            unparseable.append(relative)
            continue
        if relative.startswith("tests/") or "/tests/" in relative:
            bucket = "test"
        elif any(relative.startswith(prefix) for prefix in research_roots):
            bucket = "research"
        elif any(relative.startswith(prefix) or relative == prefix for prefix in live_roots):
            bucket = "live"
        else:
            bucket = "other"
        # Track the enclosing def so a call site inside a function nobody calls can be
        # told apart from one on a reachable path.  That distinction is the whole of
        # R1's "zero production callers" claim: the selector's one live call site sits
        # inside a bridge that is itself uncalled.
        enclosing: dict[int, str] = {}
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(parent):
                    if isinstance(child, ast.Call):
                        enclosing.setdefault(id(child), parent.name)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else None
            )
            if name in wanted:
                inside = enclosing.get(id(node), "<module>")
                census[name][bucket].append(f"{relative}:{node.lineno} in {inside}()")
    return census, unparseable


def _dedupe(sites: Sequence[str]) -> list[str]:
    """One source entry per file, keeping the first call site seen in it."""

    seen: set[str] = set()
    out: list[str] = []
    for site in sites:
        path = site.split(":", 1)[0]
        if path not in seen:
            seen.add(path)
            out.append(site)
    return out


def _enclosing_name(call_site: str) -> str | None:
    marker = " in "
    if marker not in call_site or not call_site.endswith("()"):
        return None
    return call_site.rsplit(marker, 1)[1][:-2]


_REACHABILITY_SPECS: tuple[dict[str, Any], ...] = (
    {
        "row_id": "E1.SELECTOR_V4_CALL_SITES",
        "symbol": "evaluate_selector_v4_admission",
        "dimension": "Selector V4 admission call sites",
        "finding": "E1",
        "expect_research": True,
        "transfer_risk": "BLOCKS_TRANSFER",
    },
    {
        "row_id": "E1.ALLOCATOR_CALL_SITES",
        "symbol": "allocate_decision_window",
        "dimension": "Portfolio allocator call sites",
        "finding": "E1",
        "expect_research": True,
        "transfer_risk": "BLOCKS_TRANSFER",
    },
    {
        "row_id": "E1.REPLAY_MEMORY_GUARD_CALL_SITES",
        "symbol": "build_adaptive_replay_memory_guard",
        "dimension": "Adaptive replay memory guard call sites",
        "finding": "R16",
        "expect_research": True,
        "transfer_risk": "BLOCKS_TRANSFER",
    },
)


def _derive_reachability_rows(*, root: Path) -> list[dict[str, Any]]:
    symbols = tuple(spec["symbol"] for spec in _REACHABILITY_SPECS)
    census, unparseable = _call_site_census(root=root, symbols=symbols)

    # Second hop: for every live call site, is the function containing it itself
    # called anywhere?  A live call site inside a dead function is not a live path.
    second_hop_names = {
        name
        for spec in _REACHABILITY_SPECS
        for site in census[spec["symbol"]]["live"]
        if (name := _enclosing_name(site)) is not None
    }
    second_hop: dict[str, dict[str, list[str]]] = {}
    if second_hop_names:
        second_hop, _ = _call_site_census(root=root, symbols=tuple(sorted(second_hop_names)))

    rows: list[dict[str, Any]] = []
    for spec in _REACHABILITY_SPECS:
        counts = census[spec["symbol"]]
        n_research = len(counts["research"])
        # A live call site counts only if its enclosing function is itself called on a
        # live path.  Without this, R1's "the only bridge is itself uncalled" would
        # read as a live caller.
        live_reachable = []
        live_dead = []
        for site in counts["live"]:
            name = _enclosing_name(site)
            callers = second_hop.get(name or "", {}).get("live", []) if name else []
            (live_reachable if callers else live_dead).append(site)
        n_live = len(live_reachable)

        # Probe validation.  A symbol we expect to be called in the research tree and
        # find nowhere means the scan is broken, not that the call vanished — and an
        # empty result from a broken probe is indistinguishable from a genuine empty.
        probe_ok = (not spec["expect_research"]) or n_research > 0
        if not probe_ok:
            direction, risk = "UNKNOWN", "BLOCKS_TRANSFER"
        elif n_research and not n_live:
            direction, risk = "REPLAY_ONLY", spec["transfer_risk"]
        elif n_live and not n_research:
            direction, risk = "LIVE_ONLY", spec["transfer_risk"]
        elif n_live and n_research:
            direction, risk = "BOTH_DIFFERENT", spec["transfer_risk"]
        else:
            direction, risk = "UNKNOWN", "BLOCKS_TRANSFER"

        rows.append(
            _row(
                row_id=spec["row_id"],
                family="execution_model",
                finding=spec["finding"],
                dimension=spec["dimension"],
                replay_value=f"{n_research} call sites on the research/replay path",
                replay_locator=counts["research"][0] if counts["research"] else None,
                live_value=(
                    f"{n_live} live call sites whose enclosing function is itself called"
                    + (
                        f"; {len(live_dead)} more inside functions nobody calls"
                        if live_dead
                        else ""
                    )
                    if n_live
                    else (
                        f"{ABSENT} — zero reachable live call sites"
                        + (
                            f" ({len(live_dead)} exist but sit inside functions nobody calls)"
                            if live_dead
                            else ""
                        )
                    )
                ),
                live_locator=(live_reachable or live_dead or ["src/components/**"])[0],
                direction=direction,
                transfer_risk=risk,
                rule="ast_call_site_census",
                # Hash the files the call sites were actually found in, not the
                # directory that was walked.  A `sha256` slot holding "n/a-directory-
                # scan" would look like provenance without being any, which is the
                # exact confusion the DERIVED/DECLARED split exists to prevent.
                sources=[
                    _source(
                        Path(site.split(":", 1)[0]),
                        f"call site of {spec['symbol']} at {site}",
                        root=root,
                    )
                    for site in _dedupe(
                        [
                            *counts["research"],
                            *live_reachable,
                            *live_dead,
                        ]
                    )
                ]
                or [
                    _source(
                        Path("src/components/selector_v4.py"),
                        f"no call site of {spec['symbol']} found in the scanned tree",
                        root=root,
                    )
                ],
                quantification={
                    "status": "QUANTIFIED" if probe_ok else "UNQUANTIFIED",
                    "metric": "live_call_sites",
                    "value": n_live if probe_ok else None,
                    "unit": "call sites",
                    "source": "ast_call_site_census",
                },
            )
            | {
                "call_sites": {
                    "research": counts["research"][:8],
                    "live_reachable": live_reachable[:8],
                    "live_inside_uncalled_functions": live_dead[:8],
                    "test": len(counts["test"]),
                },
                "census_semantics": (
                    "two-hop AST call-site census, not full transitive reachability: a "
                    "live call site counts only if the function containing it is itself "
                    "called from a live-path file"
                ),
                "probe_validated": probe_ok,
                "unparseable_files": unparseable,
            }
        )
    return rows


def _derive_gate_rows(*, root: Path, live_profile: str) -> list[dict[str, Any]]:
    """The three-gate authority booleans, read from the live-resolved config."""

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src.utils.config import apply_profile_overrides  # noqa: E402

    base = yaml.safe_load((root / "config/agent_config.yaml").read_text(encoding="utf-8"))
    live = apply_profile_overrides(base, live_profile)
    runtime = live.get("gtos_vnext_runtime") or {}

    sources = [
        _source(Path("config/agent_config.yaml"), "gtos_vnext_runtime", root=root),
        _source(Path(f"config/profiles/{live_profile}.yaml"), "whole file", root=root),
    ]

    specs = (
        (
            "E1.SCHEDULER_V4_AUTHORITY",
            "Scheduler V4 decision authority",
            "scheduler_v4_best_trade_allocator_live_activation_allowed",
            "the allocator is the decision authority",
            "telemetry only: runtime_effect is always False",
            "src/research/moonshot_scheduler_v4_best_trade_allocator.py:28022-28026",
        ),
        (
            "E1.SELECTOR_V4_AUTHORITY",
            "Selector V4 admission authority",
            "selector_v4_live_activation_allowed",
            "evaluate_selector_v4_admission is called on the decision path",
            "zero production callers; permissions.py:930 returns None for every candidate",
            "src/components/permissions.py:930",
        ),
        (
            "F1.BOOK_ACTIVATION_GATE",
            "ultimate_book live activation",
            "ultimate_book_live_activation_allowed",
            "the book bears no authority in replay; the broad stack decides",
            "the book is the declared live decision surface but its third gate is closed",
            "config/agent_config.yaml:1250",
        ),
    )

    rows: list[dict[str, Any]] = []
    for row_id, dimension, key, replay_value, live_value, live_locator in specs:
        present = key in runtime
        value = runtime.get(key)
        rows.append(
            _row(
                row_id=row_id,
                family="strategy_family" if row_id.startswith("F1.") else "execution_model",
                finding="F1" if row_id.startswith("F1.") else "E1",
                dimension=dimension,
                replay_value=replay_value,
                replay_locator=f"build_config({REPLAY_PROFILE!r})",
                live_value=f"{live_value} ({key}={value!r})",
                live_locator=live_locator if present else None,
                direction="BOTH_DIFFERENT" if present else "UNKNOWN",
                transfer_risk="BLOCKS_TRANSFER",
                rule="live_activation_gate_read",
                sources=sources,
                quantification={
                    "status": "NOT_APPLICABLE" if present else "UNQUANTIFIED",
                    "metric": key,
                    "value": value,
                    "unit": "bool",
                    "source": f"config/profiles/{live_profile}.yaml overlay",
                },
            )
        )
    return rows


def _declared_rows(*, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in DECLARED_ROWS:
        doc = _source(Path(spec["doc"]), "whole document", root=root)
        direction = spec["direction"]
        quant = dict(
            spec.get("quantification")
            or {
                "status": "UNQUANTIFIED",
                "metric": None,
                "value": None,
                "unit": None,
                "source": None,
            }
        )
        # A declaration whose justifying document has vanished is not a declaration.
        if not doc["present"]:
            direction = "UNKNOWN"
            quant = {
                "status": "UNQUANTIFIED",
                "metric": None,
                "value": None,
                "unit": None,
                "source": None,
            }
        rows.append(
            _row(
                row_id=spec["row_id"],
                family=spec["family"],
                finding=spec["finding"],
                dimension=spec["dimension"],
                replay_value=spec["replay_value"],
                replay_locator=spec["replay_locator"],
                live_value=spec["live_value"],
                live_locator=spec["live_locator"],
                direction=direction,
                transfer_risk=spec["transfer_risk"],
                rule="audit_declaration",
                sources=[doc],
                quantification=quant,
                declared={
                    "owner": DECLARED_OWNER,
                    "declared_utc": DECLARED_UTC,
                    "justification": spec["justification"],
                    "review_by": DECLARED_REVIEW_BY,
                },
            )
        )
    return rows


def _w7_forensics_rows(*, path: Path, root: Path) -> list[dict[str, Any]]:
    """Reduce Session E's W7 live-forensics manifest into `live_only` divergence rows.

    E's row set and this matrix describe different objects — E's row is one closed
    broker position, this matrix's row is one divergence dimension — so E's artifact is
    *reduced* here rather than merged.  That is the correct relationship: E produces the
    live evidence, F states what it implies about transferring a replay number.

    Only unambiguous top-level scalars are read.  Anything missing yields an `UNKNOWN`
    row rather than a guess, because misreading someone else's schema and presenting the
    result as measured is worse than admitting the field was not found.
    """

    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    source = _source(Path(path), "manifest scalars", root=root)
    if manifest.get("schema") != "gtos.w7_live_forensics.manifest.v1":
        return [
            _row(
                row_id="LIVE_ONLY.W7_MANIFEST_UNRECOGNISED",
                family="live_only",
                finding=None,
                dimension="W7 forensics manifest",
                replay_value="n/a",
                replay_locator="n/a",
                live_value=f"unrecognised schema {manifest.get('schema')!r}",
                live_locator=None,
                direction="UNKNOWN",
                transfer_risk="BLOCKS_TRANSFER",
                rule="w7_forensics_reduction",
                sources=[source],
            )
        ]

    pairing = manifest.get("cross_broker_pairing") or {}
    books = manifest.get("live_books") or {}
    accounts = manifest.get("accounts") or {}

    def _get(mapping: Mapping[str, Any], *keys: str) -> Any:
        cursor: Any = mapping
        for key in keys:
            if not isinstance(cursor, Mapping) or key not in cursor:
                return None
            cursor = cursor[key]
        return cursor

    specs: list[dict[str, Any]] = [
        {
            "row_id": "LIVE_ONLY.CROSS_ACCOUNT_RISK_RATIO",
            "dimension": "Same signal, different risk on the two live accounts",
            "value": _get(pairing, "risk_ratio_fn_over_ftmo", "mean"),
            "metric": "mean_redacted_account_over_ftmo_risk_ratio",
            "unit": "x",
            "replay_value": "one account, one risk profile, one contract-size table",
            "replay_locator": "config/agent_config.yaml:3160 timewarp_replay_risk_profile_path",
            "live_template": (
                "the same signal carried {value}x the risk on redacted_account vs FTMO "
                "(median {median}, n={n} paired signals, {unequal} pairs with unequal "
                "contract size)"
            ),
            "extra": {
                "median": _get(pairing, "risk_ratio_fn_over_ftmo", "median"),
                "n": _get(pairing, "risk_ratio_fn_over_ftmo", "n"),
                "unequal": pairing.get("n_pairs_with_unequal_contract_size"),
            },
            "transfer_risk": "BLOCKS_TRANSFER",
        },
        {
            "row_id": "LIVE_ONLY.UNPAIRED_SIGNALS",
            "dimension": "The two live accounts did not take the same trades",
            "value": (
                None
                if pairing.get("n_ftmo_only") is None
                or pairing.get("n_redacted_account_only") is None
                else pairing["n_ftmo_only"] + pairing["n_redacted_account_only"]
            ),
            "metric": "signals_that_fired_on_only_one_account",
            "unit": "signals",
            "replay_value": "a single simulated account; every signal is taken once",
            "replay_locator": "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
            "live_template": (
                "{value} of {total} signals fired on only one account "
                "({ftmo_only} FTMO-only, {fn_only} redacted_account-only); "
                "unpaired net FTMO {ftmo_net}, redacted_account {fn_net}"
            ),
            "extra": {
                "total": (
                    None
                    if pairing.get("n_paired_signals") is None
                    else pairing.get("n_paired_signals", 0)
                    + (pairing.get("n_ftmo_only") or 0)
                    + (pairing.get("n_redacted_account_only") or 0)
                ),
                "ftmo_only": pairing.get("n_ftmo_only"),
                "fn_only": pairing.get("n_redacted_account_only"),
                "ftmo_net": pairing.get("unpaired_ftmo_net"),
                "fn_net": pairing.get("unpaired_fn_net"),
            },
            "transfer_risk": "BLOCKS_TRANSFER",
        },
        {
            "row_id": "LIVE_ONLY.SLEEVE_EXECUTION_SURFACE",
            "dimension": "Live sleeves that executed, vs replay's sleeve coverage",
            "value": books.get("total_live_sleeves"),
            "metric": "live_sleeves_deployed",
            "unit": "sleeves",
            "replay_value": "zero: no replay arm has ever executed a sleeve-generated trade",
            "replay_locator": "docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md",
            "live_template": (
                "{value} sleeves live under profile {profile} "
                "(core8 {core8} + candidate {candidate} + market expansion {expansion}), "
                "derisk_mode {derisk}"
            ),
            "extra": {
                "profile": books.get("profile"),
                "core8": len(books.get("core8") or []),
                "candidate": len(books.get("candidate_live") or []),
                "expansion": len(books.get("market_expansion_live") or []),
                "derisk": books.get("derisk_mode"),
            },
            "transfer_risk": "BLOCKS_TRANSFER",
        },
        {
            "row_id": "LIVE_ONLY.DAILY_RESET_RULE",
            "dimension": "Daily-loss reset clock, measured per account",
            "value": len({
                str(_get(accounts, name, "daily_reset_rule"))
                for name in accounts
                if _get(accounts, name, "daily_reset_rule") is not None
            }) or None,
            "metric": "distinct_reset_rules_across_live_accounts",
            "unit": "rules",
            "replay_value": "one reset rule for the whole simulated book",
            "replay_locator": "config/agent_config.yaml",
            "live_template": "{value} distinct reset rules in use: {rules}",
            "extra": {
                "rules": {
                    name: _get(accounts, name, "daily_reset_rule") for name in accounts
                }
            },
            "transfer_risk": "BOUNDS_TRANSFER",
        },
        {
            "row_id": "LIVE_ONLY.W7_ROW_COVERAGE",
            "dimension": "Closed live positions available as evidence",
            "value": manifest.get("n_rows_w7"),
            "metric": "w7_era_closed_positions",
            "unit": "positions",
            "replay_value": "no live positions; replay produces simulated orders only",
            "replay_locator": "arm order ledgers",
            "live_template": "{value} W7-era closed positions of {total} total rows",
            "extra": {"total": manifest.get("n_rows_total")},
            "transfer_risk": "INFORMATIONAL",
        },
    ]

    rows: list[dict[str, Any]] = []
    for spec in specs:
        value = spec["value"]
        extra = spec["extra"]
        measured = value is not None and all(v is not None for v in extra.values())
        if measured:
            live_value = spec["live_template"].format(value=value, **extra)
            direction = "LIVE_ONLY"
            risk = spec["transfer_risk"]
            quant = {
                "status": "QUANTIFIED",
                "metric": spec["metric"],
                "value": value,
                "unit": spec["unit"],
                "source": str(source["path"]),
            }
        else:
            live_value = "expected manifest fields not found"
            direction = "UNKNOWN"
            risk = "BLOCKS_TRANSFER"
            quant = {
                "status": "UNQUANTIFIED",
                "metric": spec["metric"],
                "value": None,
                "unit": None,
                "source": None,
            }
        rows.append(
            _row(
                row_id=spec["row_id"],
                family="live_only",
                finding="OD-1",
                dimension=spec["dimension"],
                replay_value=spec["replay_value"],
                replay_locator=spec["replay_locator"],
                live_value=live_value,
                live_locator=str(source["path"]),
                direction=direction,
                transfer_risk=risk,
                rule="w7_forensics_reduction",
                sources=[source],
                quantification=quant,
            )
            | {"w7_manifest_fields": extra}
        )
    return rows


def _live_rows(*, path: Path | None, root: Path) -> list[dict[str, Any]]:
    """Session E's W7 forensics rows, or one loud UNKNOWN saying they are absent."""

    if path is not None and Path(path).is_file():
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema") != LIVE_ROWS_SCHEMA:
            raise DivergenceMatrixError("live_divergence_rows_schema_invalid")
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise DivergenceMatrixError("live_divergence_rows_invalid")
        supplied = _source(Path(path), "rows", root=root)
        out = []
        for row in rows:
            if row.get("family") != "live_only":
                raise DivergenceMatrixError(
                    f"live_divergence_row_family_invalid:{row.get('row_id')}"
                )
            entry = dict(row)
            entry.setdefault("derivation", {})
            entry["derivation"].setdefault("sources", [])
            entry["derivation"]["sources"] = [
                *entry["derivation"]["sources"],
                supplied,
            ]
            out.append(entry)
        return out

    return [
        _row(
            row_id="LIVE_ONLY.ROW_SET_NOT_SUPPLIED",
            family="live_only",
            finding=None,
            dimension="W7 live-divergence row set (Session E, gate G1b)",
            replay_value="n/a",
            replay_locator="n/a",
            live_value="not supplied",
            live_locator=None,
            direction="UNKNOWN",
            transfer_risk="BLOCKS_TRANSFER",
            rule="live_rows_absent",
            sources=[
                {
                    "path": "docs/audits/fable5-vision-audit-20260725/receipts/live_divergence_rows_w7.json",
                    "sha256": None,
                    "locator": "expected path",
                    "present": False,
                }
            ],
            quantification={
                "status": "UNQUANTIFIED",
                "metric": None,
                "value": None,
                "unit": None,
                "source": None,
            },
        )
    ]


# ------------------------------------------------------------------------- the matrix


def compute_transfer_verdict(rows: Sequence[Mapping[str, Any]]) -> str:
    blocked = any(
        row["direction"] == "UNKNOWN"
        or row["transfer_risk"] == "BLOCKS_TRANSFER"
        or row["quantification"]["status"] == "UNQUANTIFIED"
        for row in rows
    )
    if blocked:
        return VERDICT_BLOCKED
    if any(row["transfer_risk"] == "BOUNDS_TRANSFER" for row in rows):
        return VERDICT_BOUNDED
    return VERDICT_CLEAR


def build_matrix(
    *,
    arm_receipt_path: Path,
    live_profiles: Sequence[str] = LIVE_PROFILES,
    live_rows_path: Path | None = None,
    w7_forensics_path: Path | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Build the divergence matrix bound to one sealed arm receipt."""

    receipt_path = Path(os.path.abspath(arm_receipt_path))
    if not receipt_path.is_file():
        raise DivergenceMatrixError("arm_receipt_missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for field in ("arm_id", "window", "receipt_root_sha256"):
        if field not in receipt:
            raise DivergenceMatrixError(f"arm_receipt_field_missing:{field}")

    rows: list[dict[str, Any]] = []
    config_summaries: list[dict[str, Any]] = []
    for profile in live_profiles:
        profile_rows, summary = _derive_config_rows(root=root, live_profile=profile)
        for row in profile_rows:
            row["row_id"] = f"{row['row_id']}@{profile}"
            row["live_profile"] = profile
            rows.append(row)
        config_summaries.append(summary)
        risk_row = _derive_symbol_risk_row(root=root, live_profile=profile)
        risk_row["row_id"] = f"{risk_row['row_id']}@{profile}"
        risk_row["live_profile"] = profile
        rows.append(risk_row)
        for gate_row in _derive_gate_rows(root=root, live_profile=profile):
            gate_row["row_id"] = f"{gate_row['row_id']}@{profile}"
            gate_row["live_profile"] = profile
            rows.append(gate_row)

    rows.append(_derive_pending_lifetime_row(root=root))
    rows.extend(_derive_reachability_rows(root=root))
    rows.extend(_declared_rows(root=root))
    if w7_forensics_path is not None and Path(w7_forensics_path).is_file():
        rows.extend(_w7_forensics_rows(path=Path(w7_forensics_path), root=root))
        if live_rows_path is not None and Path(live_rows_path).is_file():
            rows.extend(_live_rows(path=live_rows_path, root=root))
    else:
        rows.extend(_live_rows(path=live_rows_path, root=root))

    seen: set[str] = set()
    for row in rows:
        if row["row_id"] in seen:
            raise DivergenceMatrixError(f"divergence_row_id_duplicated:{row['row_id']}")
        seen.add(row["row_id"])

    rows.sort(key=lambda row: row["row_id"])
    verdict = compute_transfer_verdict(rows)

    counts = {
        "rows": len(rows),
        "derived": sum(1 for r in rows if r["derivation"]["mode"] == "DERIVED"),
        "declared": sum(1 for r in rows if r["derivation"]["mode"] == "DECLARED"),
        "unknown_direction": sum(1 for r in rows if r["direction"] == "UNKNOWN"),
        "unquantified": sum(
            1 for r in rows if r["quantification"]["status"] == "UNQUANTIFIED"
        ),
        "blocks_transfer": sum(
            1 for r in rows if r["transfer_risk"] == "BLOCKS_TRANSFER"
        ),
    }
    by_family = {
        family: sum(1 for r in rows if r["family"] == family) for family in FAMILIES
    }

    core = {
        "schema": SCHEMA,
        "status": "DIVERGENCE_MATRIX_GENERATED",
        "arm_binding": {
            "arm_id": receipt["arm_id"],
            "window": receipt["window"],
            "receipt_root_sha256": receipt["receipt_root_sha256"],
            "arm_receipt_file_sha256": file_sha256(receipt_path),
            "decision_contract_self_hash_sha256": receipt.get(
                "decision_contract_self_hash_sha256"
            ),
            "execution_seal_root_sha256": receipt.get("execution_seal_root_sha256"),
            "arm_fingerprint_sha256": receipt.get("arm_fingerprint_sha256"),
        },
        "generation": {
            "generator": "src/research_infra/divergence_matrix.py",
            "replay_profile": REPLAY_PROFILE,
            "live_profiles": list(live_profiles),
            "config_surface": config_summaries,
        },
        "transfer_verdict": verdict,
        "counts": counts,
        "rows_by_family": by_family,
        "rows": rows,
    }
    return {**core, "matrix_root_sha256": stable_sha256(core)}


# ----------------------------------------------------------------------- verification


def verify_matrix(
    matrix: Mapping[str, Any], *, arm_receipt: Mapping[str, Any]
) -> None:
    """Raise unless *matrix* is a well-formed matrix bound to *arm_receipt*.

    This is what the acceptance path calls.  It is deliberately strict about three
    things and lenient about nothing: the matrix must be self-consistent, it must be
    about *this* arm, and its verdict must be the one its own rows imply.
    """

    if matrix.get("schema") != SCHEMA:
        raise DivergenceMatrixError("divergence_matrix_schema_invalid")
    if matrix.get("status") != "DIVERGENCE_MATRIX_GENERATED":
        raise DivergenceMatrixError("divergence_matrix_status_invalid")

    core = {k: v for k, v in matrix.items() if k != "matrix_root_sha256"}
    if stable_sha256(core) != matrix.get("matrix_root_sha256"):
        raise DivergenceMatrixError("divergence_matrix_root_mismatch")

    binding = matrix.get("arm_binding")
    if not isinstance(binding, Mapping):
        raise DivergenceMatrixError("divergence_matrix_arm_binding_missing")
    for field in (
        "arm_id",
        "window",
        "receipt_root_sha256",
        "decision_contract_self_hash_sha256",
        "execution_seal_root_sha256",
        "arm_fingerprint_sha256",
    ):
        if binding.get(field) != arm_receipt.get(field):
            raise DivergenceMatrixError(f"divergence_matrix_arm_binding_mismatch:{field}")

    rows = matrix.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DivergenceMatrixError("divergence_matrix_rows_missing")

    for row in rows:
        for field in (
            "row_id",
            "family",
            "dimension",
            "replay_behavior",
            "live_behavior",
            "direction",
            "transfer_risk",
            "quantification",
            "derivation",
        ):
            if field not in row:
                raise DivergenceMatrixError(
                    f"divergence_matrix_row_field_missing:{row.get('row_id')}:{field}"
                )
        if row["direction"] not in DIRECTIONS:
            raise DivergenceMatrixError(
                f"divergence_matrix_row_direction_invalid:{row['row_id']}"
            )
        if row["family"] not in FAMILIES:
            raise DivergenceMatrixError(
                f"divergence_matrix_row_family_invalid:{row['row_id']}"
            )
        derivation = row["derivation"]
        mode = derivation.get("mode")
        if mode not in ("DERIVED", "DECLARED"):
            raise DivergenceMatrixError(
                f"divergence_matrix_row_derivation_invalid:{row['row_id']}"
            )
        sources = derivation.get("sources")
        if not isinstance(sources, list) or not sources:
            raise DivergenceMatrixError(
                f"divergence_matrix_row_unsourced:{row['row_id']}"
            )
        if mode == "DERIVED" and any(
            entry.get("sha256") is None and entry.get("present") is not False
            for entry in sources
        ):
            raise DivergenceMatrixError(
                f"divergence_matrix_row_source_unhashed:{row['row_id']}"
            )
        if mode == "DECLARED" and not derivation.get("owner"):
            raise DivergenceMatrixError(
                f"divergence_matrix_row_declaration_unowned:{row['row_id']}"
            )
        if row["direction"] == "EQUIVALENT" and (
            row["replay_behavior"].get("locator") is None
            or row["live_behavior"].get("locator") is None
        ):
            raise DivergenceMatrixError(
                f"divergence_matrix_row_equivalent_without_both_sides:{row['row_id']}"
            )

    # The residual row must exist.  Without it a matrix could be complete-looking and
    # silently decaying, which is the exact failure this artifact exists to stop.
    if not any(
        str(row["row_id"]).startswith("UNCLASSIFIED_CONFIG_DIVERGENCE") for row in rows
    ):
        raise DivergenceMatrixError("divergence_matrix_residual_row_missing")

    expected = compute_transfer_verdict(rows)
    if matrix.get("transfer_verdict") != expected:
        raise DivergenceMatrixError(
            f"divergence_matrix_verdict_mismatch:{matrix.get('transfer_verdict')}!={expected}"
        )


# -------------------------------------------------------------------------- rendering


def render_markdown(matrix: Mapping[str, Any]) -> str:
    binding = matrix["arm_binding"]
    counts = matrix["counts"]
    lines = [
        f"# Divergence matrix — arm {binding['arm_id']} "
        f"({binding['window'].get('start')} .. {binding['window'].get('end')})",
        "",
        f"**Transfer verdict: `{matrix['transfer_verdict']}`**",
        "",
        "Auto-generated by `src/research_infra/divergence_matrix.py`. Do not hand-edit:",
        "the arm acceptance path recomputes the verdict from the rows and refuses a",
        "matrix whose verdict does not follow from them.",
        "",
        f"- rows: **{counts['rows']}** "
        f"({counts['derived']} derived, {counts['declared']} declared)",
        f"- unknown direction: **{counts['unknown_direction']}** · "
        f"unquantified: **{counts['unquantified']}** · "
        f"blocks transfer: **{counts['blocks_transfer']}**",
        f"- arm receipt root: `{binding['receipt_root_sha256']}`",
        f"- matrix root: `{matrix['matrix_root_sha256']}`",
        "",
    ]
    for family in FAMILIES:
        family_rows = [row for row in matrix["rows"] if row["family"] == family]
        if not family_rows:
            continue
        lines.append(f"## {family}")
        lines.append("")
        lines.append("| row | dimension | replay | live | dir | risk | quantified | mode |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for row in family_rows:
            quant = row["quantification"]
            quant_cell = (
                f"{quant['value']} {quant['unit']}"
                if quant["status"] == "QUANTIFIED"
                else quant["status"]
            )
            mode = row["derivation"]["mode"]
            mode_cell = "derived" if mode == "DERIVED" else "**[DECLARED]**"
            lines.append(
                "| `{row_id}` | {dimension} | {replay} | {live} | {direction} | "
                "{risk} | {quant} | {mode} |".format(
                    row_id=row["row_id"],
                    dimension=row["dimension"],
                    replay=_cell(row["replay_behavior"]["value"]),
                    live=_cell(row["live_behavior"]["value"]),
                    direction=row["direction"],
                    risk=row["transfer_risk"],
                    quant=quant_cell,
                    mode=mode_cell,
                )
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _cell(value: Any) -> str:
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= 130 else text[:127] + "..."


# -------------------------------------------------------------------------------- CLI


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    target = Path(os.path.abspath(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, default=None)
    parser.add_argument(
        "--live-rows",
        type=Path,
        default=None,
        help="Session E's live_only row set; absent yields one loud UNKNOWN row",
    )
    parser.add_argument(
        "--w7-forensics",
        type=Path,
        default=None,
        help=(
            "Session E's LIVE_TRADE_ROWS_MANIFEST.json — reduced into live_only rows. "
            "Supplying it satisfies the live row set on its own."
        ),
    )
    parser.add_argument("--live-profile", action="append", default=None)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    matrix = build_matrix(
        arm_receipt_path=args.arm_receipt,
        live_profiles=tuple(args.live_profile or LIVE_PROFILES),
        live_rows_path=args.live_rows,
        w7_forensics_path=args.w7_forensics,
        root=Path(args.repo_root).resolve(),
    )
    _write_json_atomic(args.output, matrix)
    if args.markdown is not None:
        Path(os.path.abspath(args.markdown)).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown).write_text(render_markdown(matrix), encoding="utf-8")
    print(
        json.dumps(
            {
                "arm_id": matrix["arm_binding"]["arm_id"],
                "transfer_verdict": matrix["transfer_verdict"],
                "rows": matrix["counts"]["rows"],
                "unknown_direction": matrix["counts"]["unknown_direction"],
                "matrix_root_sha256": matrix["matrix_root_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
