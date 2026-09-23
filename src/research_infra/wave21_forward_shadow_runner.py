"""Wave-21 forward-shadow runner: the frozen funnel on live data, zero mutation.

Runs the full decision path of MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1 forward,
each M15 close, on the live FTMO feed:

  closed-bar snapshot (successor witness)  ->  production candidate generators
  (truth mode)  ->  predecision enrichment + limit fillability  ->  LIVE
  four-component pretrade costs (fail-closed)  ->  frozen 43-feature row  ->
  frozen ridge model (portable JSON artifact, no sklearn)  ->  MARKET-top-
  abstain selection with same-symbol occupancy  ->  decision-packet JSONL +
  would-be-order log  ->  modelled M1 lifecycle to terminal.

Hard lines:
  * NO ``order_send``, NO activation token, NO book interaction, no reads of
    the live book's state, no writes outside its own namespace directory.
  * The namespace guard refuses to start on any collision with the live
    book's trees.
  * Every broker mutation surface in the adapter raises.

Run:  python -m src.research_infra.wave21_forward_shadow_runner \
          --config config/wave21_forward_shadow.yaml [--once] [--asof ISO]
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research_infra.wave21_forward_shadow.feature_contract import (
    FeatureContractError,
    LANE_GENERAL,
    LANE_SCOPED_LSR,
    LSR_FAMILY,
    RULE_PAYLOAD_SHA256,
    at_utc,
    eligible,
    expiry_for_decision,
    shadow_feature_row,
)
from src.research_infra.wave21_forward_shadow.mt5_read_only import (
    ShadowReadOnlyMT5Adapter,
)
from src.research_infra.wave21_forward_shadow.namespace_guard import (
    claim_namespace,
    release_namespace,
)
from src.research_infra.wave21_forward_shadow.ridge_artifact import load_model
from src.research_infra.wave21_forward_shadow.runner_config import (
    ShadowRunnerConfig,
    build_decision_config,
    load_shadow_config,
)
from src.research_infra.wave21_forward_shadow.daily_refit import (
    DAILY_ARTIFACT_TEMPLATE,
    DailyRefitError,
    collect_forward_training_rows,
    load_frozen_corpus,
    refit_payload,
    write_daily_artifact,
)
from src.research_infra.wave21_forward_shadow.decision_transforms import (
    apply_dynamic_target_geometry,
    apply_ledger_session_aliases,
    mint_occurrence_identity,
    stamp_preselector_admission,
)
from src.research_infra.wave21_forward_shadow.shadow_costs import (
    preflight_cost_authority,
    stamp_live_pretrade_cost,
)
from src.research_infra.wave21_forward_shadow.shadow_lifecycle import (
    WouldBeOrder,
    resolve_would_be_order,
    spread_series,
)
from src.research_infra.wave21_forward_shadow.shadow_select import (
    occupancy_end_for_selection,
    select_market_top_abstain,
)
from src.research_infra.wave21_forward_shadow.state import ShadowState

RUNNER_SCHEMA = "gtos.wave21.forward_shadow.decision_packet.v1"
WINDOW_ID_PREFIX = "forward_shadow"

# Raw candidate keys preserved verbatim in the decision packet — the exact
# surface the frozen research feature builder consumes (parity harness input).
RAW_CONSUMED_KEYS = (
    "canonical_replay_candidate_instance_key",
    "candidate_id",
    "symbol",
    "side",
    "origin_family",
    "session_bucket",
    "session",
    "decision_time_utc",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "risk_reward_ratio",
    "predecision_features",
    "predecision_limit_fillability",
    "poi_state",
    "poi_mitigation_status",
    "poi_age_hours",
    "poi_distance_to_midpoint_atr",
    "poi_distance_to_zone_atr",
    "poi_touch_count",
)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    """NaN/Inf -> None recursively (packets are allow_nan=False JSONL)."""

    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


class ForwardShadowRunner:
    def __init__(
        self,
        config: ShadowRunnerConfig,
        *,
        mt5_module: Any,
        clock: Any = None,
    ):
        self.config = config
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        # Heavy production imports happen once, here — not at module import —
        # so unit tests can exercise the pieces without the full stack.
        from src.components.broader_origin_generators import (
            generate_live_broader_origin_candidates,
        )
        from src.components.data_ingestion import (
            DataIncompleteError,
            SourceChronologyError,
            SourceTimebaseError,
            ingest_live_data,
        )
        from src.components.market_state import compute_market_state
        from src.research_infra import (
            v4_timewarp_simulated_live_research_loop as timewarp,
        )

        self._timewarp = timewarp
        self._generate = generate_live_broader_origin_candidates
        self._ingest = ingest_live_data
        self._compute_market_state = compute_market_state
        self._source_errors = (DataIncompleteError,)
        self._terminal_source_errors = (SourceTimebaseError, SourceChronologyError)

        self.decision_config, self.config_fingerprints = build_decision_config(
            config, load_config=timewarp.load_config
        )
        server = str(self.decision_config["broker_profile"]["server"])
        self.adapter = ShadowReadOnlyMT5Adapter(mt5_module, server=server)
        # Day-zero model: the committed flat V1 artifact.  Under the daily
        # refit (owner directive 2026-08-12, ON by default) it is replaced at
        # each day's first cycle by that day's prequential fit; with zero
        # observed forward rows the refit provably reproduces it, so V1 is
        # used directly until the first outcome exists.
        self.model = load_model(config.model_artifact_path)
        self._model_day: str | None = None
        self._frozen_corpus = None
        self._frozen_corpus_sha: str | None = None
        if config.daily_refit_enabled:
            try:
                import sklearn  # noqa: F401 — fail fast; the refit needs it
            except ImportError as exc:
                raise DailyRefitError(
                    "daily_refit_enabled but scikit-learn is not installed — "
                    "add scikit-learn==1.8.0 to the shadow venv (runbook §1)"
                ) from exc
            self._frozen_corpus_path = (
                config.frozen_corpus_path
                or config.model_artifact_path.parent / "FROZEN_TRAINING_CORPUS_V1.npz"
            )
            if not self._frozen_corpus_path.is_file():
                raise DailyRefitError(
                    f"frozen training corpus missing: {self._frozen_corpus_path}"
                )
            self._models_dir = config.models_dir or (config.namespace_dir / "models")
        self.symbols = tuple(config.symbols) or tuple(timewarp.GTOS_24_SYMBOL_SURFACE)
        # Fail fast on a cost authority that cannot price the surface.  The
        # four-component rule refuses candidate-by-candidate, so this defect is
        # otherwise invisible: the lane runs, logs, heartbeats and measures
        # nothing.  Same posture as the frozen-corpus check above.
        self.cost_preflight = preflight_cost_authority(
            config=self.decision_config, symbols=self.symbols
        )
        self.state = ShadowState(config.namespace_dir)
        now = self.clock()
        self.open_orders: dict[str, WouldBeOrder] = {
            order.candidate_occurrence_key: order
            for order in self.state.load_open_orders()
        }
        # Two independent occupancy states — one per selection lane.  The
        # scoped_lsr lane is the bar-3-ratified primary deployable object and
        # must evolve under its OWN occupancy, not the general lane's.
        self.occupancy: dict[str, dict[str, datetime]] = {
            LANE_GENERAL: self.state.load_occupancy(now_utc=now, lane=LANE_GENERAL),
            LANE_SCOPED_LSR: self.state.load_occupancy(
                now_utc=now, lane=LANE_SCOPED_LSR
            ),
        }
        self._spread_cache: dict[tuple[str, datetime], float] = {}
        self._symbol_configs: dict[str, dict[str, Any]] = {}
        self._stopping = False

    # ------------------------------------------------------------------
    def _symbol_config(self, symbol: str) -> dict[str, Any]:
        cached = self._symbol_configs.get(symbol)
        if cached is None:
            cached = self._timewarp.replay_symbol_config(self.decision_config, symbol)
            # The shadow writes NOTHING outside its namespace: market-state
            # side-effect writes (pipeline_state snapshot, structure shadow
            # log) are observational outputs, not MSO inputs — the replay's
            # exact-cache guard requires them off for the same reason
            # (ReplayFeed._timeframe_state_provider).
            market_state = cached.setdefault("market_state", {})
            if isinstance(market_state, dict):
                market_state["side_effect_writes_enabled"] = False
                market_state["structure_shadow_log_enabled"] = False
            self._symbol_configs[symbol] = cached
        return copy.deepcopy(cached)

    def _broker_symbol(self, symbol: str) -> str:
        market = self._timewarp._broker_symbol_market_config(
            self.decision_config, symbol
        )
        return str(market.get("mt5_symbol") or self._timewarp.ftmo_symbol(symbol))

    # ------------------------------------------------------------------
    def snapshot_symbols(self, asof: datetime) -> tuple[dict, dict, dict, dict]:
        raw_by_symbol: dict[str, Any] = {}
        mso_by_symbol: dict[str, Any] = {}
        metadata_by_symbol: dict[str, Any] = {}
        stand_downs: dict[str, dict[str, Any]] = {}
        for symbol in self.symbols:
            symbol_config = self._symbol_config(symbol)
            try:
                raw = self._ingest(self.adapter, symbol_config, now_utc=asof)
                mso = self._compute_market_state(raw, symbol_config)
            except self._terminal_source_errors as exc:
                stand_downs[symbol] = {
                    "status": "source_terminal",
                    "reason": getattr(exc, "terminal_status", "NOT_EVALUABLE"),
                    "detail": str(exc)[:300],
                }
                continue
            except self._source_errors as exc:
                stand_downs[symbol] = {
                    "status": "source_incomplete",
                    "detail": str(exc)[:300],
                }
                continue
            except Exception as exc:  # noqa: BLE001 — mirror replay stand-down
                stand_downs[symbol] = {
                    "status": "market_state_failed",
                    "detail": f"{type(exc).__name__}: {exc}"[:300],
                }
                continue
            raw_by_symbol[symbol] = raw
            mso_by_symbol[symbol] = mso
            metadata_by_symbol[symbol] = {
                "latest_closed_m15": (raw.get("data_quality") or {}).get(
                    "latest_closed_m15_time_utc"
                ),
            }
        return raw_by_symbol, mso_by_symbol, metadata_by_symbol, stand_downs

    # ------------------------------------------------------------------
    def generate_window_candidates(
        self, asof: datetime, raw_by_symbol: dict, mso_by_symbol: dict
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        cross_asset = {"raw_data_by_symbol": raw_by_symbol}
        asof_iso = _iso(asof)
        window_id = f"{WINDOW_ID_PREFIX}:{asof_iso}"
        trading_day = asof.date().isoformat()
        expiry_iso = expiry_for_decision(asof).isoformat()
        all_rows: list[dict[str, Any]] = []
        generation_status: dict[str, dict[str, Any]] = {}
        quote_by_symbol: dict[str, Any] = {}
        for symbol in self.symbols:
            raw = raw_by_symbol.get(symbol)
            if raw is None:
                continue
            audit: dict[str, Any] = {}
            try:
                candidates = self._generate(
                    dict(raw),
                    mso_by_symbol[symbol],
                    self.decision_config,
                    symbol,
                    self._timewarp.derive_session(symbol, asof),
                    cross_asset_raw_data=cross_asset,
                    now_utc=asof,
                    generation_audit=audit,
                )
            except ValueError as exc:
                generation_status[symbol] = {
                    "status": "generation_refused",
                    "detail": str(exc)[:300],
                }
                continue
            generation_status[symbol] = {
                "status": str(audit.get("status") or "no_audit"),
                "generated": len(candidates),
            }
            if not candidates:
                continue
            enriched = self._timewarp.enrich_candidates_with_predecision_market_snapshot(
                candidates, raw, asof_utc=asof_iso
            )
            if symbol not in quote_by_symbol:
                try:
                    quote_by_symbol[symbol] = self.adapter.live_cost_quote(
                        self._broker_symbol(symbol)
                    )
                except Exception as exc:  # noqa: BLE001 — quote gap is fail-closed
                    quote_by_symbol[symbol] = None
                    generation_status[symbol]["quote_error"] = str(exc)[:200]
            for candidate in enriched:
                # The frozen funnel rows are POST-dynamic-geometry candidates
                # with quality-contract identity — apply the same transforms.
                candidate = dict(candidate)
                candidate.setdefault("decision_time_utc", asof_iso)
                try:
                    candidate = stamp_preselector_admission(candidate)
                except ValueError as exc:
                    all_rows.append(
                        {
                            "raw": {
                                "symbol": candidate.get("symbol"),
                                "origin_family": candidate.get("origin_family"),
                                "candidate_id": candidate.get("candidate_id"),
                                "decision_window_id": window_id,
                                "trading_day": trading_day,
                            },
                            "eligible": False,
                            "eligibility_reason": "occurrence_admission_invalid",
                            "identity_status": str(exc)[:200],
                        }
                    )
                    continue
                candidate = apply_dynamic_target_geometry(
                    candidate, config=self.decision_config
                )
                candidate = apply_ledger_session_aliases(
                    candidate, decision_time_utc=asof_iso
                )
                candidate = mint_occurrence_identity(
                    candidate, decision_time_utc=asof_iso
                )
                row = self.build_shadow_row(
                    candidate,
                    window_id=window_id,
                    trading_day=trading_day,
                    asof_iso=asof_iso,
                    expiry_iso=expiry_iso,
                    live_quote=quote_by_symbol.get(symbol),
                )
                all_rows.append(row)
        return all_rows, generation_status

    # ------------------------------------------------------------------
    def build_shadow_row(
        self,
        candidate: Mapping[str, Any],
        *,
        window_id: str,
        trading_day: str,
        asof_iso: str,
        expiry_iso: str,
        live_quote: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        fillability = self._timewarp.candidate_predecision_limit_fillability_signal(
            candidate
        )
        cost = stamp_live_pretrade_cost(
            candidate,
            config=self.decision_config,
            live_quote=live_quote,
            asof_utc=asof_iso,
            max_tick_staleness_seconds=self.config.max_tick_staleness_seconds,
        )
        raw = {key: candidate.get(key) for key in RAW_CONSUMED_KEYS if key in candidate}
        raw["predecision_limit_fillability"] = fillability
        raw["decision_time_utc"] = asof_iso
        raw["limit_first_expiry_utc"] = expiry_iso
        raw["decision_window_id"] = window_id
        raw["trading_day"] = trading_day
        raw["cost_r"] = cost["cost_r"]
        raw["spread_r"] = cost["spread_r"]
        raw["expected_slippage_r"] = cost["expected_slippage_r"]
        raw["swap_cost_r"] = cost["swap_cost_r"]
        raw["commission_r"] = cost["commission_r"]
        record: dict[str, Any] = {
            "raw": raw,
            "cost_complete": bool(cost["complete"]),
            "cost_quote_authority": cost.get("quote_authority"),
            "cost_packet": cost.get("packet"),
        }
        if not cost["complete"]:
            record["cost_refusal_reason"] = cost.get("refusal_reason")
        key = str(raw.get("canonical_replay_candidate_instance_key") or "")
        if not key.startswith("candidate_occurrence_") or len(key) != 85:
            record["eligible"] = False
            record["eligibility_reason"] = "occurrence_identity_unmintable"
            record["identity_status"] = candidate.get(
                "candidate_instance_identity_status"
            )
            return record
        try:
            features = shadow_feature_row(raw)
        except FeatureContractError as exc:
            record["feature_contract_error"] = str(exc)[:300]
            record["eligible"] = False
            record["eligibility_reason"] = "feature_contract_violation"
            return record
        record["features"] = features
        is_eligible, reason = eligible(features, cost_complete=bool(cost["complete"]))
        record["eligible"] = is_eligible
        if reason:
            record["eligibility_reason"] = reason
        return record

    # ------------------------------------------------------------------
    def ensure_model_for_day(self, asof: datetime) -> None:
        """Prequential daily refit at each new trading day's first cycle.

        Semantics = the sealed reads': refit the rule's ridge on the frozen
        corpus + every shadow-observed resolved-eligible outcome row logged
        before this day's first decision.  Zero forward rows -> the committed
        V1 artifact (provably identical to the refit).  A same-day artifact on
        disk is reused (restart idempotency).  Refit failure aborts the cycle
        loudly rather than deciding on a stale model.
        """

        if not self.config.daily_refit_enabled:
            return
        day = asof.date().isoformat()
        if self._model_day == day:
            return
        artifact_path = self._models_dir / DAILY_ARTIFACT_TEMPLATE.format(day=day)
        if artifact_path.is_file():
            self.model = load_model(artifact_path)
            self._model_day = day
            self._log_refit_event(
                day, event="reused_existing_daily_artifact", artifact_path=artifact_path
            )
            return
        forward_rows = collect_forward_training_rows(
            self.config.namespace_dir, until_utc=asof
        )
        if not forward_rows:
            self.model = load_model(self.config.model_artifact_path)
            self._model_day = day
            self._log_refit_event(
                day,
                event="day_zero_v1_artifact_no_forward_rows",
                artifact_path=self.config.model_artifact_path,
            )
            return
        if self._frozen_corpus is None:
            self._frozen_corpus = load_frozen_corpus(self._frozen_corpus_path)
            import hashlib

            digest = hashlib.sha256()
            with self._frozen_corpus_path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            self._frozen_corpus_sha = digest.hexdigest()
        payload = refit_payload(
            self._frozen_corpus,
            forward_rows,
            day=day,
            frozen_corpus_sha256=self._frozen_corpus_sha or "",
        )
        written = write_daily_artifact(payload, models_dir=self._models_dir, day=day)
        self.model = load_model(written)
        self._model_day = day
        self._log_refit_event(
            day,
            event="refit_daily_artifact",
            artifact_path=written,
            forward_rows=len(forward_rows),
        )

    def _log_refit_event(
        self,
        day: str,
        *,
        event: str,
        artifact_path: Path,
        forward_rows: int | None = None,
    ) -> None:
        binding = self.model.training_binding
        record = {
            "at_utc": _iso(self.clock()),
            "refit_event": event,
            "model_day": day,
            "artifact_path": str(artifact_path),
            "model_artifact_sha256": self.model.artifact_sha256,
            "training_rows": binding.get("training_rows"),
            "forward_rows": (
                forward_rows
                if forward_rows is not None
                else binding.get("forward_rows", 0)
            ),
        }
        self.state.write_heartbeat(record)
        if self.config.heartbeat_echo:
            print("SHADOW_REFIT=" + json.dumps(record, sort_keys=True), flush=True)

    # ------------------------------------------------------------------
    def run_cycle(self, asof: datetime) -> dict[str, Any]:
        cycle_started = self.clock()
        asof = asof.astimezone(timezone.utc)
        asof_iso = _iso(asof)
        window_id = f"{WINDOW_ID_PREFIX}:{asof_iso}"
        trading_day = asof.date().isoformat()
        if window_id in self.state.processed_window_ids(trading_day=trading_day):
            return {"window_id": window_id, "status": "already_processed"}
        self.ensure_model_for_day(asof)
        self.adapter.set_cycle_context(asof=asof)

        raw_by_symbol, mso_by_symbol, _metadata, stand_downs = self.snapshot_symbols(asof)
        rows, generation_status = self.generate_window_candidates(
            asof, raw_by_symbol, mso_by_symbol
        )

        eligible_records = [record for record in rows if record.get("eligible")]
        predictions = [
            self.model.predict_row(record["features"]) for record in eligible_records
        ]
        for record, prediction in zip(eligible_records, predictions):
            record["predicted_net_r"] = float(prediction)

        # Dual selection each window (bar-3 ratification): the GENERAL rule and
        # the same rule restricted to the liquidity_sweep_reclaim family, each
        # under its own occupancy state.  A candidate chosen by both lanes is
        # tracked once with both lanes on its would-be order.
        lane_choices: dict[str, dict[str, Any] | None] = {}
        selection: dict[str, Any] = {}
        dispositions: dict[str, dict[str, int]] = {}
        for lane in (LANE_GENERAL, LANE_SCOPED_LSR):
            if lane == LANE_SCOPED_LSR:
                lane_records = [
                    record
                    for record in eligible_records
                    if record["features"]["origin_family"] == LSR_FAMILY
                ]
            else:
                lane_records = eligible_records
            lane_predictions = [
                record["predicted_net_r"] for record in lane_records
            ]
            if lane_records:
                chosen, lane_dispositions, self.occupancy[lane] = (
                    select_market_top_abstain(
                        [record["features"] for record in lane_records],
                        lane_predictions,
                        active=self.occupancy[lane],
                        decision_at=asof,
                    )
                )
            else:
                chosen, lane_dispositions = None, {"no_eligible_candidates": 1}
                self.occupancy[lane] = {
                    symbol: end
                    for symbol, end in self.occupancy[lane].items()
                    if end > asof
                }
            lane_choices[lane] = chosen
            dispositions[lane] = lane_dispositions
            selection[lane] = (
                None
                if chosen is None
                else {
                    "candidate_occurrence_key": chosen["candidate_occurrence_key"],
                    "symbol": chosen["symbol"],
                    "side": chosen["side"],
                    "origin_family": chosen["origin_family"],
                    "proposed_order_type": chosen["proposed_order_type"],
                    "predicted_net_r": float(chosen["predicted_net_r"]),
                    "cost_r": float(chosen["cost_r"]),
                    "expiry_utc": chosen["expiry_utc"],
                }
            )

        chosen_lanes_by_key: dict[str, list[str]] = {}
        for lane, chosen in lane_choices.items():
            if chosen is not None:
                chosen_lanes_by_key.setdefault(
                    str(chosen["candidate_occurrence_key"]), []
                ).append(lane)
        for key, lanes in chosen_lanes_by_key.items():
            chosen_record = next(
                record
                for record in eligible_records
                if record["features"]["candidate_occurrence_key"] == key
            )
            chosen_row = lane_choices[lanes[0]]
            assert chosen_row is not None
            self._open_would_be_order(
                chosen_record, chosen_row, asof, lanes=tuple(lanes)
            )

        scoped_key = (
            str(lane_choices[LANE_SCOPED_LSR]["candidate_occurrence_key"])
            if lane_choices[LANE_SCOPED_LSR] is not None
            else None
        )
        general_key = (
            str(lane_choices[LANE_GENERAL]["candidate_occurrence_key"])
            if lane_choices[LANE_GENERAL] is not None
            else None
        )
        for record in rows:
            features = record.get("features") or {}
            raw = record.get("raw") or {}
            record["origin_family"] = str(
                features.get("origin_family") or raw.get("origin_family") or ""
            )
            key = str(features.get("candidate_occurrence_key") or "")
            record["scoped_lsr_selected"] = bool(scoped_key and key == scoped_key)
            if not record.get("eligible"):
                record["disposition"] = "ineligible"
            elif general_key and key == general_key:
                record["disposition"] = "trade"
            else:
                record["disposition"] = "not_top_or_abstained"

        outcomes = self.track_lifecycles(asof)

        packet = {
            "schema": RUNNER_SCHEMA,
            "decision_window_id": window_id,
            "decision_time_utc": asof_iso,
            "trading_day": trading_day,
            "rule_payload_sha256": RULE_PAYLOAD_SHA256,
            "model_artifact_sha256": self.model.artifact_sha256,
            "model": {
                "mode": self.model.training_binding.get("mode", "flat_v1"),
                "day": self.model.training_binding.get("day"),
                "training_rows": self.model.training_binding.get("training_rows"),
                "forward_rows": self.model.training_binding.get("forward_rows", 0),
            },
            "config_fingerprints": self.config_fingerprints,
            "symbols_evaluated": sorted(raw_by_symbol),
            "symbol_stand_downs": stand_downs,
            "generation_status": generation_status,
            "candidate_count": len(rows),
            "eligible_count": len(eligible_records),
            "dispositions": dispositions,
            "selection": selection,
            "active_symbols": {
                lane: {
                    symbol: end.isoformat()
                    for symbol, end in sorted(lane_active.items())
                }
                for lane, lane_active in self.occupancy.items()
            },
            "lifecycle_events": outcomes,
            "cycle_seconds": round(
                (self.clock() - cycle_started).total_seconds(), 3
            ),
            "candidates": rows,
        }
        self.state.write_decision_packet(_json_safe(packet))
        heartbeat = {
            "at_utc": _iso(self.clock()),
            "decision_window_id": window_id,
            "symbols": len(raw_by_symbol),
            "stand_downs": len(stand_downs),
            "candidates": len(rows),
            "eligible": len(eligible_records),
            "dispositions": dispositions,
            "selected_general": bool(selection.get(LANE_GENERAL)),
            "selected_scoped_lsr": bool(selection.get(LANE_SCOPED_LSR)),
            "open_would_be_orders": len(self.open_orders),
            "cycle_seconds": packet["cycle_seconds"],
        }
        self.state.write_heartbeat(heartbeat)
        if self.config.heartbeat_echo:
            print("SHADOW_HEARTBEAT=" + json.dumps(heartbeat, sort_keys=True), flush=True)
        return packet

    # ------------------------------------------------------------------
    def _open_would_be_order(
        self,
        record: Mapping[str, Any],
        chosen: Mapping[str, Any],
        asof: datetime,
        *,
        lanes: tuple[str, ...],
    ) -> WouldBeOrder:
        features = record["features"]
        deductible = sum(
            float(value)
            for value in (
                features["expected_slippage_r"],
                features["swap_cost_r"],
                features["commission_r"],
            )
            if isinstance(value, float) and math.isfinite(value)
        )
        raw = record["raw"]
        order = WouldBeOrder(
            candidate_occurrence_key=str(features["candidate_occurrence_key"]),
            decision_window_id=str(features["decision_window_id"]),
            trading_day=str(features["trading_day"]),
            symbol=str(features["symbol"]),
            side=str(features["side"]),
            proposed_order_type=str(features["proposed_order_type"]),
            submission_utc=asof,
            expiry_utc=at_utc(features["expiry_utc"]),
            entry_price=float(raw["entry_price"]),
            stop_loss=float(raw["stop_loss"]),
            take_profit_1=float(raw["take_profit_1"]),
            deductible_cost_r=deductible,
            predicted_net_r=float(chosen["predicted_net_r"]),
            cost_r=float(features["cost_r"]),
            origin_family=str(features["origin_family"]),
            lanes=lanes,
        )
        self.open_orders[order.candidate_occurrence_key] = order
        occupancy_end = occupancy_end_for_selection(features)
        for lane in lanes:
            self.occupancy[lane][order.symbol] = occupancy_end
        self.state.write_would_be_order(
            order,
            context={
                "evidence_class": "forward_shadow_would_be_order_not_transmitted",
                "broker_mutation": False,
                "scoped_lsr_selected": LANE_SCOPED_LSR in lanes,
            },
        )
        return order

    # ------------------------------------------------------------------
    def track_lifecycles(self, asof: datetime) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for key in sorted(self.open_orders):
            order = self.open_orders[key]
            broker_symbol = self._broker_symbol(order.symbol)
            try:
                m1_rows = self.adapter.get_candles(
                    broker_symbol, 1, self.config.m1_fetch_bars
                )
            except Exception as exc:  # noqa: BLE001 — keep tracking next cycle
                events.append(
                    {
                        "candidate_occurrence_key": key,
                        "phase": "m1_fetch_error",
                        "detail": f"{type(exc).__name__}: {exc}"[:200],
                    }
                )
                continue
            from src.components.ultimate_book.primitives import Bar

            times = [at_utc(row["time_utc"]) for row in m1_rows]
            bars = [
                Bar(
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                )
                for row in m1_rows
            ]
            spreads = spread_series(order.symbol, times, cache=self._spread_cache)
            resolution = resolve_would_be_order(
                order,
                m1_times=times,
                m1_bars=bars,
                spreads=spreads,
                now_utc=asof,
            )
            if resolution.get("final"):
                self.state.write_order_outcome(order, _json_safe(resolution))
                del self.open_orders[key]
                end_text = resolution.get("occupancy_end_utc")
                if end_text:
                    end = at_utc(end_text)
                    for lane in order.lanes:
                        current = self.occupancy.get(lane, {}).get(order.symbol)
                        if current is not None:
                            self.occupancy[lane][order.symbol] = min(current, end)
                events.append(
                    {
                        "candidate_occurrence_key": key,
                        "phase": resolution.get("phase"),
                        "lifecycle_label_status": resolution.get(
                            "lifecycle_label_status"
                        ),
                        "terminal_net_r": resolution.get("terminal_net_r"),
                    }
                )
            else:
                events.append(
                    {
                        "candidate_occurrence_key": key,
                        "phase": resolution.get("phase"),
                    }
                )
        return events

    # ------------------------------------------------------------------
    def next_cycle_time(self, now: datetime) -> datetime:
        grid = self.config.cycle_grid_minutes
        minute_block = (now.minute // grid + 1) * grid
        base = now.replace(second=0, microsecond=0, minute=0) + timedelta(
            minutes=minute_block
        )
        return base

    def run_forever(self) -> None:
        def _stop(_signum, _frame):
            self._stopping = True
            print("SHADOW_STOP_REQUESTED", flush=True)

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)
        while not self._stopping:
            now = self.clock()
            boundary = self.next_cycle_time(now)
            wake = boundary + timedelta(seconds=self.config.settle_delay_seconds)
            while not self._stopping and self.clock() < wake:
                time.sleep(min(1.0, max(0.05, (wake - self.clock()).total_seconds())))
            if self._stopping:
                break
            try:
                self.run_cycle(boundary)
            except Exception:  # noqa: BLE001 — a cycle failure must not kill the lane
                self.state.write_heartbeat(
                    {
                        "at_utc": _iso(self.clock()),
                        "decision_window_id": f"{WINDOW_ID_PREFIX}:{_iso(boundary)}",
                        "cycle_error": traceback.format_exc()[-1500:],
                    }
                )
                print("SHADOW_CYCLE_ERROR — logged, continuing", flush=True)


def _connect_mt5(config: ShadowRunnerConfig) -> Any:
    import MetaTrader5 as mt5  # deferred: research machines lack the module

    kwargs: dict[str, Any] = {}
    if config.mt5_terminal_path:
        kwargs["path"] = config.mt5_terminal_path
    if not mt5.initialize(**kwargs):
        raise RuntimeError(f"MetaTrader5 initialize failed: {mt5.last_error()!r}")
    return mt5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/wave21_forward_shadow.yaml")
    parser.add_argument("--once", action="store_true", help="run one cycle and exit")
    parser.add_argument(
        "--asof",
        default=None,
        help="pin the decision time for --once (ISO, aware UTC); default: last grid boundary",
    )
    args = parser.parse_args(argv)

    config = load_shadow_config(args.config, repo_root=_REPO_ROOT)
    lock_path = claim_namespace(config.namespace_dir, repo_root=config.repo_root)
    try:
        mt5 = _connect_mt5(config)
        runner = ForwardShadowRunner(config, mt5_module=mt5)
        print(
            "SHADOW_START="
            + json.dumps(
                {
                    "namespace": str(config.namespace_dir),
                    "model_artifact_sha256": runner.model.artifact_sha256,
                    "rule_payload_sha256": RULE_PAYLOAD_SHA256,
                    "config_fingerprints": runner.config_fingerprints,
                    "symbols": len(runner.symbols),
                    "resumed_open_orders": len(runner.open_orders),
                    "broker_mutation": False,
                    "cost_preflight": runner.cost_preflight,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if args.once:
            if args.asof:
                asof = at_utc(args.asof)
            else:
                now = datetime.now(timezone.utc)
                grid = config.cycle_grid_minutes
                asof = now.replace(
                    second=0, microsecond=0, minute=(now.minute // grid) * grid
                )
            packet = runner.run_cycle(asof)
            print(
                "SHADOW_ONCE="
                + json.dumps(
                    {
                        "window": packet.get("decision_window_id"),
                        "candidates": packet.get("candidate_count"),
                        "eligible": packet.get("eligible_count"),
                        "dispositions": packet.get("dispositions"),
                    },
                    sort_keys=True,
                    default=str,
                ),
                flush=True,
            )
        else:
            runner.run_forever()
        return 0
    finally:
        release_namespace(lock_path)


if __name__ == "__main__":
    raise SystemExit(main())
