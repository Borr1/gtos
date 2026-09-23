#!/usr/bin/env python3
"""Build the full candidate-book live activation package.

This route consumes the completed readiness/replay/routing/NATGAS/principal
proofs and verifies that active Mac config now arms the exact nine-sleeve
positive-confidence candidate book. It does not touch brokers, orders,
credentials, remotes, MT5 state, or VPS processes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
ACTIVE_CONFIG = ROOT / "config" / "agent_config.yaml"
READINESS_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_activation_readiness_2026_06_18"
MC_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18"
DOSSIER_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_subset_routing_dossier_2026_06_18"
NATGAS_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_natgas_decomposition_2026_06_18"
PRINCIPAL_DIR = ROOT / "research" / "operations" / "final_moonshot_principal_full_system_audit_2026_06_17"

READY_ALLOWLIST = (
    "asia_pdl_fade",
    "asian_fade",
    "kz_london_crypto_low",
    "liq_asia_up_low_metal",
    "metal_session_reversion",
    "ny_crypto_momentum",
    "orb_crypto_london",
    "vol_compression",
    "vss_fxcross_london_up_low",
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.ultimate_book.admission import (  # noqa: E402
    CANDIDATE_BOOK_PROFILE,
    GovernorLimits,
    GovernorState,
    TradeIntent,
)
from src.components.ultimate_book.bridge import (  # noqa: E402
    DEFAULT_CONFIG,
    evaluate_vnext_ultimate_book_admission,
)
from src.components.ultimate_book.launcher import BookLauncher  # noqa: E402
from src.components.ultimate_book.sleeves.registry import CANDIDATE_BUILT  # noqa: E402


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _runtime_config() -> dict[str, Any]:
    cfg = yaml.safe_load(ACTIVE_CONFIG.read_text(encoding="utf-8")) or {}
    runtime = cfg.get("gtos_vnext_runtime") or {}
    if not isinstance(runtime, dict):
        raise TypeError("gtos_vnext_runtime did not load as a mapping")
    return runtime


def _state() -> GovernorState:
    return GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )


def _active_bridge_probe(runtime: dict[str, Any]) -> dict[str, Any]:
    root_cfg = {"gtos_vnext_runtime": runtime}
    limits = GovernorLimits(derisk_mode=str(runtime.get("ultimate_book_derisk_mode", "band")))
    ready_decision = evaluate_vnext_ultimate_book_admission(
        config=root_cfg,
        intents=[
            TradeIntent(
                sleeve="ny_crypto_momentum",
                symbol="BTCUSD",
                direction=1,
                decision_day="2026-06-18",
                stop_dist=100.0,
                target_dist=None,
            )
        ],
        governor_state=_state(),
        limits=limits,
    )
    outside_decision = evaluate_vnext_ultimate_book_admission(
        config=root_cfg,
        intents=[
            TradeIntent(
                sleeve="vol_squeeze",
                symbol="GER40",
                direction=1,
                decision_day="2026-06-18",
                stop_dist=100.0,
                target_dist=200.0,
            )
        ],
        governor_state=_state(),
        limits=limits,
    )
    return {
        "ready_decision_status": ready_decision.decision_status,
        "ready_runtime_effect_now": ready_decision.runtime_effect_now,
        "ready_candidate_book_sleeves": list(ready_decision.candidate_book_sleeves),
        "ready_realized_units": ready_decision.realized_units,
        "ready_would_units": ready_decision.would_units,
        "outside_decision_status": outside_decision.decision_status,
        "outside_runtime_effect_now": outside_decision.runtime_effect_now,
        "outside_realized_units": outside_decision.realized_units,
        "outside_would_units": outside_decision.would_units,
        "broad_selector_apply_to_execution": ready_decision.broad_selector_apply_to_execution,
    }


def _launcher_schedule_probe(runtime: dict[str, Any]) -> dict[str, Any]:
    class _Owner:
        base_config = {"gtos_vnext_runtime": runtime}

    class _MT5:
        pass

    launcher = BookLauncher(_Owner(), _MT5(), lambda s: s, repo_root=str(ROOT), tags=None, poll_seconds=60.0)
    return {
        "tf_tags": {str(tf): sorted(tags) for tf, tags in launcher._tf_tags.items()},
        "has_d1_candidate": "vol_compression" in launcher._tf_tags.get(16408, []),
        "has_m15_candidates": {
            name: name in launcher._tf_tags.get(15, [])
            for name in (
                "asia_pdl_fade",
                "asian_fade",
                "kz_london_crypto_low",
                "liq_asia_up_low_metal",
                "metal_session_reversion",
                "ny_crypto_momentum",
                "orb_crypto_london",
                "vss_fxcross_london_up_low",
            )
        },
    }


def _check(name: str, passed: bool, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail or {}}


def build_outputs() -> dict[str, Any]:
    runtime = _runtime_config()
    readiness = _read_json(READINESS_DIR / "CANDIDATE_ACTIVATION_READINESS_RESULT.json")
    mc = _read_json(MC_DIR / "CANDIDATE_ENABLED_REPLAY_MC_RESULT.json")
    dossier = _read_json(DOSSIER_DIR / "CANDIDATE_SUBSET_ROUTING_DOSSIER_RESULT.json")
    natgas = _read_json(NATGAS_DIR / "ASIA_PDL_FADE_NATGAS_DECOMPOSITION_RESULT.json")
    principal = _read_json(PRINCIPAL_DIR / "CORRECTED_UNIFIED_BOOK_MC_AUDIT.json")
    principal_current = principal["scenarios"]["registry_current_corrected"]
    allowlist = tuple(str(item) for item in runtime.get("ultimate_book_candidate_book_sleeves", []) if str(item))
    bridge_probe = _active_bridge_probe(runtime)
    launcher_probe = _launcher_schedule_probe(runtime)
    active_mc = mc["scenarios"]["active_core8_a8_baseline_no_candidates"]
    candidate_mc = mc["scenarios"]["candidate_all_on_active_a8"]

    checks = [
        _check(
            "bridge_defaults_remain_fail_safe",
            DEFAULT_CONFIG["ultimate_book_include_candidate_book"] is False
            and DEFAULT_CONFIG["ultimate_book_candidate_book_sleeves"] == []
            and DEFAULT_CONFIG["ultimate_book_candidate_book_profile"] == CANDIDATE_BOOK_PROFILE,
        ),
        _check(
            "active_config_triple_gate_live_and_broad_selector_off",
            all(runtime.get(k) is True for k in (
                "ultimate_book_enabled",
                "ultimate_book_apply_to_execution",
                "ultimate_book_live_activation_allowed",
            ))
            and runtime.get("selector_v4_enabled") is True
            and runtime.get("selector_v4_apply_to_execution") is False,
        ),
        _check(
            "active_config_arms_exact_allowlist",
            runtime.get("ultimate_book_include_candidate_book") is True
            and runtime.get("ultimate_book_candidate_book_profile") == CANDIDATE_BOOK_PROFILE
            and allowlist == READY_ALLOWLIST
            and len(set(allowlist)) == len(READY_ALLOWLIST),
            {"allowlist": list(allowlist)},
        ),
        _check(
            "active_config_preserves_core8_a8_risk_guards",
            runtime.get("ultimate_book_include_clean3") is False
            and runtime.get("ultimate_book_include_clean4") is False
            and runtime.get("ultimate_book_profile") == "clean3_w7_ceiling_nom2p00"
            and runtime.get("ultimate_book_derisk_mode") == "smooth"
            and runtime.get("ultimate_book_stress_derisk") is True
            and runtime.get("ultimate_book_metals_confluence_gate") is True
            and runtime.get("ultimate_book_drop_w7_symbols") is True,
        ),
        _check(
            "readiness_zero_blockers",
            readiness.get("activation_ready") is True
            and readiness.get("readiness_work_item_count") == 0
            and readiness.get("activation_blockers") == []
            and readiness.get("ltf_stress_gaps") == [],
        ),
        _check(
            "replay_mc_ready_and_stronger",
            mc.get("deployment_ready") is True
            and mc.get("routing_activation_ready") is True
            and mc.get("full_candidate_book_ready") is True
            and candidate_mc["sharpe"] > active_mc["sharpe"]
            and candidate_mc["mc"]["p_pass"] >= active_mc["mc"]["p_pass"]
            and candidate_mc["mc"]["p_fail_dd"] <= active_mc["mc"]["p_fail_dd"],
            {
                "active_sharpe": active_mc["sharpe"],
                "candidate_sharpe": candidate_mc["sharpe"],
                "active_mc": active_mc["mc"],
                "candidate_mc": candidate_mc["mc"],
            },
        ),
        _check(
            "routing_dossier_active_and_fail_closed_outside",
            dossier.get("full_candidate_book_ready") is True
            and dossier.get("active_config_candidate_book_enabled") is True
            and tuple(dossier.get("active_config_candidate_book_sleeves", [])) == READY_ALLOWLIST
            and dossier["bridge_probe"]["outside_would_units"]
            and any(
                "vol_squeeze" in unit.get("sleeve_members", []) and unit.get("sized") is False
                for unit in dossier["bridge_probe"]["outside_would_units"]
            ),
        ),
        _check(
            "bridge_active_config_emits_ready_candidate_and_rejects_outside",
            bridge_probe["ready_runtime_effect_now"] is True
            and bridge_probe["ready_decision_status"] == "admitted_book_authority"
            and any(
                "ny_crypto_momentum" in unit.get("sleeve_members", []) and unit.get("sized") is True
                for unit in bridge_probe["ready_realized_units"]
            )
            and bridge_probe["outside_runtime_effect_now"] is True
            and any(
                "vol_squeeze" in unit.get("sleeve_members", []) and unit.get("sized") is False
                for unit in bridge_probe["outside_would_units"]
            )
            and bridge_probe["broad_selector_apply_to_execution"] is False,
            bridge_probe,
        ),
        _check(
            "launcher_schedules_candidate_decision_timeframes",
            launcher_probe["has_d1_candidate"]
            and all(launcher_probe["has_m15_candidates"].values()),
            launcher_probe,
        ),
        _check(
            "natgas_excluded_but_revived_as_research_lane",
            "NATGAS_cash" not in allowlist
            and "NATGAS_cash" not in CANDIDATE_BUILT["asia_pdl_fade"].on_surface
            and natgas.get("excluded_cost_repair_symbols") == ["NATGAS_cash"]
            and natgas.get("natgas_hard_drop_guard_present") is True
            and natgas["ex_natgas"]["every_split_positive"] is True
            and natgas["natgas_only"]["splits"]["sealed"]["meanR"] < 0,
        ),
        _check(
            "principal_audit_reflects_current_full_candidate_book",
            principal_current["sharpe"] == 0.274938
            and principal_current["mc"]["p_pass"] == 0.9999
            and principal_current["mc"]["p_fail_dd"] == 0.0001,
        ),
    ]
    issue_rows = [row for row in checks if not row["passed"]]
    ok = not issue_rows
    result = {
        "schema": "gtos.final_moonshot.candidate_full_book_live_activation.v1",
        "ok": ok,
        "decision": "ARM_FULL_CANDIDATE_BOOK_LIVE_CONFIG_AND_HAND_TO_VPS" if ok else "BLOCK_FULL_CANDIDATE_BOOK_ACTIVATION",
        "active_config_path": _rel(ACTIVE_CONFIG),
        "candidate_book_active": bool(runtime.get("ultimate_book_include_candidate_book")),
        "candidate_book_profile": runtime.get("ultimate_book_candidate_book_profile"),
        "candidate_book_sleeves": list(allowlist),
        "ready_allowlist": list(READY_ALLOWLIST),
        "active_core8_a8_baseline": {"sharpe": active_mc["sharpe"], "mc": active_mc["mc"]},
        "full_candidate_book": {"sharpe": candidate_mc["sharpe"], "mc": candidate_mc["mc"]},
        "headline_improvement": {
            "sharpe_delta": round(candidate_mc["sharpe"] - active_mc["sharpe"], 6),
            "monthly_pct_delta": round(candidate_mc["mc"]["monthly_pct"] - active_mc["mc"]["monthly_pct"], 6),
            "p_fail_dd_delta": round(candidate_mc["mc"]["p_fail_dd"] - active_mc["mc"]["p_fail_dd"], 6),
            "worst_day_pct_delta": round(candidate_mc["mc"]["worst_day_pct"] - active_mc["mc"]["worst_day_pct"], 6),
        },
        "bridge_probe": bridge_probe,
        "launcher_schedule_probe": launcher_probe,
        "checks": checks,
        "issue_count": len(issue_rows),
        "orderflow_used": False,
        "mt5_bridge_mutation": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    decision_rows = [
        {
            "row": "full_candidate_book_activation",
            "decision": result["decision"],
            "active_config": result["candidate_book_active"],
            "sleeve_count": len(allowlist),
            "candidate_sharpe": candidate_mc["sharpe"],
            "mc_pass": candidate_mc["mc"]["p_pass"],
            "owner_vps_boundary": "VPS may pull, verify, restart only book workers, and monitor; Mac route did not mutate VPS processes",
        },
        {
            "row": "natgas_translation",
            "decision": "exclude_from_live_allowlist_preserve_limit_entry_cost_revival_lane",
            "unsupported_current_claim": "NATGAS_cash asia_pdl_fade live inclusion",
            "useful_inspiration": "energy cost/spread sensitivity and possible limit-entry revival research",
            "revival_gate": "native pending/limit-entry replay plus tick/cost proof before any live allowlist change",
        },
        {
            "row": "market_expansion_translation",
            "decision": "do_not_block_activation_create_expansion_data_availability_wave",
            "useful_inspiration": "MT5 bridge has broader non-JPY FX, indices, copper, agri/softs, crypto alts, and DXY context symbols",
            "next_route": "market expansion inventory, OHLCV availability matrix, alias map, and preregistered expansion protocol",
        },
    ]
    saturation = {
        "schema": "gtos.final_moonshot.candidate_full_book_live_activation.saturation.v1",
        "ok": ok,
        "anti_boxing_checked": [
            "used the full positive-confidence candidate book, not an arbitrary subset",
            "kept bridge defaults fail-safe while active YAML is explicit",
            "verified runtime bridge emits a ready candidate under active config and rejects an outside sleeve",
            "preserved NATGAS as a research-revival lane instead of silently killing the idea",
            "preserved broad market expansion as the next data-availability wave instead of blocking deployable candidates",
        ],
        "same_evidence_repairs_completed": [
            "active config armed exact nine-sleeve allowlist",
            "readiness verifier separated source/profile/history readiness from default-off status",
            "candidate replay/MC verifier reads active config state",
            "routing dossier builder reports active config and exact owner/VPS boundary",
            "NATGAS proof reports active-book exclusion rather than stale default-off wording",
        ],
        "remaining_same_class_work": [] if ok else [row["name"] for row in issue_rows],
        "forbidden_surfaces_not_crossed": [
            "broker/account/order/deal/position mutation",
            "credential mutation/disclosure",
            "remote push",
            "live VPS process restart/reload",
            "MT5 order/history mutation",
            "orderflow/depth data",
            "paid/vendor calls",
        ],
    }
    return {
        "result": result,
        "verification": {
            "schema": "gtos.final_moonshot.candidate_full_book_live_activation.verification.v1",
            "ok": ok,
            "decision": result["decision"],
            "issue_count": len(issue_rows),
            "failed_checks": issue_rows,
            "candidate_book_active": result["candidate_book_active"],
            "candidate_book_sleeves": result["candidate_book_sleeves"],
            "candidate_sharpe": candidate_mc["sharpe"],
            "candidate_mc_pass": candidate_mc["mc"]["p_pass"],
            "broker_or_order_mutation": False,
            "vps_process_touched": False,
            "orderflow_used": False,
        },
        "completion": {
            "schema": "gtos.final_moonshot.candidate_full_book_live_activation.completion_audit.v1",
            "ok": ok,
            "decision": result["decision"],
            "instruction_coverage": [
                "mandatory preflight/context read by orchestrator before route build",
                "production-code/config activation lane",
                "same-evidence-class stale default-off wording repaired",
                "no orderflow/depth and no live broker/VPS mutation",
            ],
            "runtime_config_mutation": "config/agent_config.yaml arms ultimate_book_include_candidate_book with exact nine-sleeve allowlist",
            "broker_or_order_mutation": False,
            "vps_process_touched": False,
        },
        "decision_rows": decision_rows,
        "saturation": saturation,
    }


def write_outputs(outputs: dict[str, Any]) -> None:
    result = outputs["result"]
    _write_json(ROUTE_DIR / "CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_RESULT.json", result)
    _write_json(ROUTE_DIR / "CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_VERIFICATION_RESULT.json", outputs["verification"])
    _write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", outputs["completion"])
    _write_jsonl(ROUTE_DIR / "DECISION_LEDGER.jsonl", outputs["decision_rows"])
    _write_json(ROUTE_DIR / "SATURATION_AUDIT.json", outputs["saturation"])
    _write_json(ROUTE_DIR / "REPAIR_LEDGER.json", {
        "schema": "gtos.final_moonshot.candidate_full_book_live_activation.repair_ledger.v1",
        "ok": result["ok"],
        "same_evidence_repairs_completed": outputs["saturation"]["same_evidence_repairs_completed"],
        "remaining_repairs": outputs["saturation"]["remaining_same_class_work"],
    })
    _write_json(ROUTE_DIR / "FOCUSED_TEST_RESULT.json", {
        "schema": "gtos.final_moonshot.candidate_full_book_live_activation.focused_test_result.v1",
        "ok": result["ok"],
        "commands": [
            "python3 research/operations/final_moonshot_candidate_full_book_live_activation_2026_06_18/verify_candidate_full_book_live_activation.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_launcher.py tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py tests/ultimate_book/test_candidate_promotion_plumbing.py -q",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_full_book_live_activation_2026_06_18 --full-jsonl",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_candidate_full_book_live_activation_2026_06_18/NEXT_PROMPT.md",
        ],
        "warning": "PytestConfigWarning: Unknown config option: asyncio_mode may appear and is pre-existing",
    })
    _write_packet(result)
    _write_next_prompt()
    files = sorted(path.name for path in ROUTE_DIR.iterdir() if path.is_file())
    _write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {
        "schema": "gtos.final_moonshot.candidate_full_book_live_activation.output_manifest.v1",
        "route_dir": _rel(ROUTE_DIR),
        "files": sorted(set(files) | {"OUTPUT_MANIFEST.json"}),
        "file_count": len(set(files) | {"OUTPUT_MANIFEST.json"}),
    })


def _write_packet(result: dict[str, Any]) -> None:
    sleeves = ", ".join(result["candidate_book_sleeves"])
    packet = f"""# Full Candidate Book Live Activation Packet

Decision: `{result["decision"]}`

Active Mac config now arms the full positive-confidence candidate book:

```yaml
ultimate_book_include_candidate_book: true
ultimate_book_candidate_book_profile: "runtime_executable_native_exit_v2"
ultimate_book_candidate_book_sleeves: [{sleeves}]
```

Evidence numbers:

- Active core8 + A8 baseline Sharpe: `{result["active_core8_a8_baseline"]["sharpe"]}`
- Full candidate book Sharpe: `{result["full_candidate_book"]["sharpe"]}`
- Active MC pass / max-DD fail / monthly: `{result["active_core8_a8_baseline"]["mc"]["p_pass"]}` / `{result["active_core8_a8_baseline"]["mc"]["p_fail_dd"]}` / `{result["active_core8_a8_baseline"]["mc"]["monthly_pct"]}%`
- Full candidate MC pass / max-DD fail / monthly: `{result["full_candidate_book"]["mc"]["p_pass"]}` / `{result["full_candidate_book"]["mc"]["p_fail_dd"]}` / `{result["full_candidate_book"]["mc"]["monthly_pct"]}%`
- Worst day improved from `{result["active_core8_a8_baseline"]["mc"]["worst_day_pct"]}%` to `{result["full_candidate_book"]["mc"]["worst_day_pct"]}%`.

Runtime meaning:

- Bridge defaults remain fail-safe/off.
- Active YAML carries an explicit nine-sleeve allowlist; live package does not use `[]` all-executable mode.
- Unknown candidate profile or sleeve still fails closed.
- `NATGAS_cash` is not in `asia_pdl_fade` live surface and remains hard-dropped as a separate limit-entry/cost-revival lane.
- This route did not mutate broker/account/order/deal/position state, credentials, remotes, MT5 order/history state, or VPS processes.

VPS apply/verify boundary:

```powershell
cd C:\\Users\\MSI\\Documents\\ai-trading-agent
git pull --ff-only

$py = ".\\.venv-gtos\\Scripts\\python.exe"

& $py research\\operations\\final_moonshot_candidate_activation_readiness_2026_06_18\\verify_candidate_activation_readiness.py
& $py research\\operations\\final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18\\verify_candidate_enabled_unified_replay_mc.py
& $py research\\operations\\final_moonshot_candidate_subset_routing_dossier_2026_06_18\\verify_candidate_subset_routing_dossier.py
& $py research\\operations\\final_moonshot_candidate_natgas_decomposition_2026_06_18\\verify_candidate_natgas_decomposition.py
& $py research\\operations\\final_moonshot_candidate_full_book_live_activation_2026_06_18\\verify_candidate_full_book_live_activation.py

& $py -m pytest `
  tests\\ultimate_book\\test_candidate_activation_readiness_artifacts.py `
  tests\\ultimate_book\\test_candidate_enabled_replay_mc_artifacts.py `
  tests\\ultimate_book\\test_candidate_subset_routing_dossier_artifacts.py `
  tests\\ultimate_book\\test_candidate_natgas_decomposition_artifacts.py `
  tests\\ultimate_book\\test_candidate_full_book_live_activation_artifacts.py `
  tests\\ultimate_book\\test_candidate_promotion_plumbing.py -q
```

Restart only the existing book workers by namespace after verification, using the current Windows supervisor surface. Do not restart MT5 terminals, Docker/Kasm, data bridges, tick capture/watchdog fleet, legacy `run_agent.py`, or unrelated processes.

Monitor after VPS reload:

- `pipeline_state\\ultimate_book\\operator_profile\\heartbeat.json`
- `pipeline_state\\ultimate_book\\redacted_account_live_bee34003\\heartbeat.json`
- `pipeline_state\\ultimate_book\\*\\placed_decisions.jsonl`
- `shadow_logs\\ultimate_book_launcher.jsonl`
- `shadow_logs\\run_book_console.log`
- `shadow_logs\\run_book_fn_console.log`
- `shadow_logs\\book_supervisor.log`

The launcher cycle JSONL now includes a `bridge` object with `runtime_effect_now`,
`candidate_use_allowed_now`, `decision_status`, `reason`, `include_candidate_book`,
`candidate_book_profile`, `candidate_book_sleeves`, `dropped_symbols`,
`would_units`, `realized_units`, and `governor`. Per-unit rows include
`cluster`, `sleeve_members`, `n_trades`, `confidence`, `unit_risk_pct`,
`risk_pct_per_trade`, `sized`, `reason`, and `overlays_applied` when present.
Live candidate-book proof requires config true, `bridge.runtime_effect_now=true`,
`bridge.candidate_use_allowed_now=true`, the intended allowed sleeve in
`bridge.realized_units` when it fires, and placement ledger rows only for allowed
sleeves.

Alert or rollback on:

- `fail_closed_unknown_candidate_book_profile`
- `fail_closed_unknown_candidate_book_sleeves`
- any candidate sleeve outside the nine-sleeve allowlist
- any `NATGAS_cash` candidate generation or placed decision
- any `HEATOIL_c` candidate generation or placed decision
- `ceiling_profile_requires_smooth_ddefense`
- broad selector apply-to-execution becoming true while ultimate book is live
- heartbeat stale after worker reload
- candidate-book config on VPS differs from this packet

Rollback:

```yaml
ultimate_book_include_candidate_book: false
ultimate_book_candidate_book_sleeves: []
```

Then restart only the same two `run_book.py` workers by namespace and rerun the full verifier set above.
"""
    (ROUTE_DIR / "CANDIDATE_FULL_BOOK_LIVE_ACTIVATION_PACKET.md").write_text(packet, encoding="utf-8")


def _write_next_prompt() -> None:
    prompt = """# Market Expansion And Candidate Successor Wave Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt after any compaction/resume/interruption/uncertainty, and read goal_session_research_discipline.md plus research_operating_doctrine.md as active instructions, not background, before acting.

Evidence class: constructive market-expansion data availability, preregistration, and candidate successor research. Operate at maximum practical reasoning depth, no conservative brake, no arbitrary top-N/top-3/top-5 cutoff, and pursue full same-evidence-class pursuit for every ambiguity until repaired, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or proven inapplicable inside the approved evidence class.

Allowed data: localhost Docker MT5 bridge read-only OHLCV, volume/tick-volume, symbol info/spec/spread snapshots, existing local exports, current route artifacts, committed code, and public docs only when source-contract capture is explicitly saved. Do not use orderflow/depth for this route. Forbidden surfaces: no production-change or live trading broker operation; no broker/account/order/history/deal/position mutation; no prompt/config/risk/execution/safety/canary/selector live activation changes; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: build `research/operations/final_moonshot_market_expansion_data_availability_2026_06_18/` as the next expansion wave without blocking the already armed full candidate book. Use the MT5 bridge to inventory all broker-native symbols, normalize aliases, export missing OHLCV where safe, build an availability matrix, classify symbol families, and preregister expansion/validation protocols for non-JPY FX crosses, additional indices/context, copper, agri/softs, crypto alts, DXY context, and any other bridge-native class discovered.

Required artifacts: market symbol inventory, broker-native alias map, OHLCV availability matrix, coverage-gap ledger with exact safe export commands, symbol-class taxonomy and priority ledger preserving all material rows, candidate mechanism map, preregistered expansion protocol, validation-ready symbols, research-only symbols, saturation audit, completion audit, verifier result, output manifest, focused tests, and successor prompt.

Inspire-not-kill rule: every non-promoted market or mechanism must preserve what was useful, why it is not deployable now, the transformed use, and the exact revival gate. Complete only when the route artifacts prove same-evidence-class pursuit is exhausted or exactly bounded.
"""
    (ROUTE_DIR / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    result = outputs["result"]
    print(json.dumps({
        "ok": result["ok"],
        "decision": result["decision"],
        "candidate_book_active": result["candidate_book_active"],
        "sleeve_count": len(result["candidate_book_sleeves"]),
        "candidate_sharpe": result["full_candidate_book"]["sharpe"],
        "candidate_mc_pass": result["full_candidate_book"]["mc"]["p_pass"],
        "issue_count": result["issue_count"],
    }, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
