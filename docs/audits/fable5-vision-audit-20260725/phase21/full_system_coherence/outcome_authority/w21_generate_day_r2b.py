#!/usr/bin/env python3
"""Wave-21 lane day generator, r2b — partial-day tolerance (prereg APRMAY V1.1).

r2 inherited February's strict 24-symbol assumption; on days where the lane
resolver legitimately excludes a symbol (holiday/thin-session M1-floor drop —
the resolver and ReplayClock both tolerate this by design), r2 crashed inside
``lane._with_loader_component_authority``, which iterates the fixed
``RAW_CAMPAIGN_SYMBOLS`` constant against the partial sources dict (observed:
2026-04-02, GER40 absent). r2b differs from r2 ONLY on partial days:

  * component authority is bound over the RESOLVED symbols (the module constant
    is patched to the resolved tuple strictly around that one call);
  * the per-day denominator check records ``missing_symbols`` in run_summary
    instead of refusing (>=1 resolved symbol still required, fail-closed);
  * expected decision-stream coverage is computed from the resolved surface.

On full-resolution days every code path is identical to r2 (2026-04-01's root,
produced by r2, is byte-equivalent to what r2b produces). No model, selection,
gate, cost, or truth-mode behavior changes.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
REGISTRY = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/"
    "evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/"
    "LANE_INPUT_REGISTRY.json"
)
sys.path.insert(0, str(REPO))

from src.research_infra import lane_rematerialization as lane
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.train_engine import guard

_PROFILE_FILES = {
    "merge-ftmo": ("config/profiles/ftmo.yaml", "merge"),
    "broker-only": ("config/profiles/ftmo.yaml", "broker"),
    "merge-310": ("config/profiles/operator_profile.yaml", "merge"),
    "broker-310": ("config/profiles/operator_profile.yaml", "broker"),
}


def _deep_merge(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _config_for(mode: str) -> dict:
    config = copy.deepcopy(timewarp.load_config(REPO / "config/agent_config.yaml"))
    if mode != "none":
        import yaml

        if mode not in _PROFILE_FILES:
            raise SystemExit(f"unknown mode: {mode}")
        rel, how = _PROFILE_FILES[mode]
        profile = yaml.safe_load((REPO / rel).read_text(encoding="utf-8")) or {}
        if not isinstance(profile, dict):
            raise SystemExit("profile payload not a mapping")
        if how == "merge":
            config = _deep_merge(config, copy.deepcopy(profile))
        else:
            if not isinstance(profile.get("broker_profile"), dict):
                raise SystemExit("profile has no broker_profile block")
            config["broker_profile"] = copy.deepcopy(profile["broker_profile"])
    config.setdefault("gtos_vnext_runtime", {})[
        "wave21_full_flow_truth_mode_enabled"
    ] = True
    return config


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: w21_generate_day_r2b.py WINDOW_ID YYYY-MM-DD OUTPUT_ROOT MODE"
        )
    window_id, day, output_root_text, mode = sys.argv[1:5]
    output_root = Path(output_root_text).resolve()
    day_root = output_root / day
    compact_root = day_root / "compact_events"
    if day_root.exists() or day_root.is_symlink():
        raise SystemExit(f"output day must be new: {day_root}")
    day_root.mkdir(parents=True, exist_ok=False)

    inputs = lane.LaneInputRegistry(
        REGISTRY,
        allow_registered_march_metadata=True,
    ).resolve(
        window_id=window_id,
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    if day not in inputs.window.days:
        raise SystemExit(f"day outside {window_id} authority: {day}")

    config = _config_for(mode)
    campaign = timewarp.CampaignConfig(
        name=f"wave21_market_top_choice_validation_{day.replace('-', '')}",
        phase="wave21_market_top_choice_validation",
        days=(day,),
        pending_expiry_minutes=120,
        use_repaired_pending_expiry=True,
        partial_be_runner=True,
        max_candidates_per_symbol_window=0,
        run_smoke_subset=False,
        materialize_packet_sidecars=False,
        materialize_semantic_diagnostics=False,
    )

    # The resolved-symbol patch must span the ENTIRE generation block: the
    # component-authority binder (:2992), the successor witness (:3162), and
    # runtime_bindings' own exit-time stream validation (:2108) all iterate the
    # module constant against the resolver's legitimately partial sources dict.
    original_symbols = lane.RAW_CAMPAIGN_SYMBOLS
    resolved = ()
    missing_symbols = []
    try:
        with inputs.runtime_bindings():
            resolver = lane._resolver_for(inputs)
            sources = resolver.build_sources_for_days(
                (day,),
                symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
                source_authority_days=(day,),
            )
            resolved = tuple(
                symbol
                for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
                if symbol in sources
            )
            missing_symbols = sorted(
                set(timewarp.GTOS_24_SYMBOL_SURFACE) - set(resolved)
            )
            if not resolved:
                raise RuntimeError(f"no symbols resolved for {day}")
            lane.RAW_CAMPAIGN_SYMBOLS = resolved
            sources = lane._with_loader_component_authority(inputs, sources)
            for symbol, frames in sources.items():
                frame_missing = {"D1", "H4", "H1", "M15", "M1"} - set(frames)
                if frame_missing:
                    raise RuntimeError(
                        f"source missing: {symbol}: {sorted(frame_missing)}"
                    )

            sink = ReplayCompactEventSink(root=compact_root)
            try:
                with (
                    lane._RAW_CAMPAIGN_WITNESS_LOCK,
                    lane._installed_raw_campaign_successor_witness(
                        sources
                    ) as used_streams,
                ):
                    result = timewarp.run_campaign(
                        campaign=campaign,
                        config=config,
                        sources=sources,
                        compact_event_sink=sink,
                        prepared_day_pack=None,
                    )
            except BaseException:
                sink.abort()
                raise
    finally:
        lane.RAW_CAMPAIGN_SYMBOLS = original_symbols

    expected_streams = len(resolved) * len(lane.RAW_CAMPAIGN_DECISION_TIMEFRAMES)
    authority = result["compact_event_sink_authority"]
    # A day whose lane substrate carries no decision bars (full market holiday,
    # e.g. Good Friday / Easter Monday) legitimately consumes zero decision
    # streams and emits zero ECONOMIC rows — the `decision` ledger still logs
    # per-window stand-down bookkeeping (measured on 2026-04-03: only
    # decision-00000.zstf in the sink). Any OTHER coverage shortfall fails closed.
    economic_ledgers = ("candidate", "missed", "order", "trade", "oracle", "scorecard")
    economic_rows = sum(
        int(authority["row_counts"].get(key) or 0) for key in economic_ledgers
    )
    stand_down_day = len(used_streams) == 0 and economic_rows == 0
    if not stand_down_day and len(used_streams) != expected_streams:
        raise RuntimeError(
            f"decision source stream coverage mismatch: {len(used_streams)} != {expected_streams}"
        )
    summary = {
        "day": day,
        "window_id": window_id,
        "generator": "w21_generate_day_r2b",
        "profile_mode": mode,
        "resolved_symbols": len(resolved),
        "missing_symbols": missing_symbols,
        "stand_down_day": stand_down_day,
        "expected_decision_streams": expected_streams,
        "compact_root": str(compact_root),
        "authority_root_sha256": authority["authority_root_sha256"],
        "row_counts": authority["row_counts"],
        "source_manifest_root_sha256": inputs.source_manifest[
            "manifest_root_sha256"
        ],
        "used_decision_streams": len(used_streams),
    }
    (day_root / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("W21_DAY_R2B=" + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
