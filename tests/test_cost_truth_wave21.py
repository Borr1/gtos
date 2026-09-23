"""Adversarial behavioural closure for the Wave-21 cost evidence defects."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.costs import (
    APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS,
    Coverage,
    CostPacketIncompleteError,
    CostTruthError,
    QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA,
    QUOTE_GEOMETRY_ROW_SCHEMA,
    SpreadAccounting,
    SpreadGeometryEvidence,
    assess_cost_packet_completeness,
    assess_post_lifecycle_component_cost,
    build_post_lifecycle_component_cost,
    component_sum_r,
    cost_r,
    elapsed_holding_hours,
    load_broker_true_costs,
    require_complete_cost_packet,
    require_complete_post_lifecycle_component_cost,
)
from src.costs.fx_conversion import (
    DEFAULT_FX_ARTIFACT,
    FxConversionError,
    HistoricalFxRates,
    load_historical_fx,
)
from src.costs.model import DEFAULT_ARTIFACT as DEFAULT_BROKER_COST_ARTIFACT
from src.costs.slippage_model import (
    DEFAULT_SLIPPAGE_ARTIFACT,
    SlippageEstimate,
    SlippageModelError,
    load_slippage_model,
)
from src.costs.spread_model import (
    DEFAULT_MODEL as DEFAULT_SPREAD_MODEL_ARTIFACT,
    SpreadModelError,
    load_spread_model,
)
from src.costs.symbols import (
    PROFILE_PATHS,
    ProfileSymbolAuthority,
    SymbolAuthorityError,
    canonical_symbol,
    profile_broker_symbols,
    resolve_account_symbol,
)
from src.research_infra.walkforward.options import OPTIONS
from src.research_infra.walkforward.panel import TradeRecord, price_trades

UTC = dt.timezone.utc
REPO = Path(__file__).resolve().parents[1]
MANIFEST = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/cost/COST_INPUTS_MANIFEST_V1.json"
)


class _ZeroSlippage:
    """Explicit component-isolation double, never a production default."""

    def estimate(self, account: str, symbol: str) -> SlippageEstimate:
        return SlippageEstimate(
            account=account,
            canonical_symbol=symbol,
            expected_adverse_price=0.0,
            coverage=Coverage.MEASURED,
            n=1,
            provenance="component-isolation test double",
            detail={},
        )


class _MissingHistoricalFx:
    def rate_at(self, currency, entry_utc, *, server):
        raise FxConversionError(
            f"missing historical FX probe for {currency} at {entry_utc} on {server}; "
            "NOT_EVALUABLE"
        )


def _geometry_evidence(tmp_path: Path, name: str, row: dict) -> SpreadGeometryEvidence:
    source = tmp_path / name
    source.write_text(json.dumps(row, sort_keys=True) + "\n")
    return SpreadGeometryEvidence(
        source_path=source,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        row_index=0,
        trade_id=row["trade_id"],
    )


def _price_improved_geometry_row(*, side: str, entry_utc: dt.datetime) -> dict:
    long_side = side == "LONG"
    return {
        "schema": QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA,
        "trade_id": f"improved-{side.lower()}",
        "account": "redacted_account",
        "symbol": "XAUUSD",
        "entry_utc": entry_utc.isoformat(),
        "side": side,
        "gross_basis": "fill_anchored_quote_geometry",
        "gross_includes_spread": True,
        "source_status": "captured",
        "bid_price": 99.4 if long_side else 100.5,
        "ask_price": 99.5 if long_side else 100.6,
        "entry_fill_price": 99.5 if long_side else 100.5,
        "stop_price": 99.0 if long_side else 101.0,
        "spread_price": 0.1,
        "coverage": "MEASURED",
        "risk_denominator_basis": (
            APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS
        ),
        "approved_entry_price": 100.0,
        "approved_stop_price": 99.0 if long_side else 101.0,
        "approved_risk_distance": 1.0,
    }


def _rehash_lifecycle_record(packet: dict) -> None:
    lifecycle = packet["lifecycle"]
    integrity = {
        key: lifecycle[key]
        for key in (
            "entry_utc",
            "exit_utc",
            "symbol",
            "account",
            "side",
            "elapsed_holding_hours",
            "entry_price",
            "exit_price",
            "sl_distance_price",
            "holding_source_status",
            "source_status",
            "provenance",
        )
    }
    integrity["quote_geometry"] = lifecycle["quote_geometry"]
    lifecycle["record_sha256"] = hashlib.sha256(
        json.dumps(integrity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _manifest_bound_copy(tmp_path, key: str, source: Path):
    root = tmp_path / f"{key}_authority"
    target = root / "inputs" / source.name
    target.parent.mkdir(parents=True)
    payload = source.read_bytes()
    target.write_bytes(payload)
    manifest = root / "COST_INPUTS_MANIFEST_V1.json"
    manifest.write_text(json.dumps({
        "schema": "gtos.phase21.cost_inputs_manifest.v1",
        "outputs": {
            key: {
                "path": str(target.relative_to(root)),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        },
    }))
    return root, manifest, target, payload


def _profile_authority_from_text(
    root: Path, *, ftmo_text: str, redacted_account_text: str
) -> ProfileSymbolAuthority:
    root.mkdir(parents=True)
    paths = {
        "FTMO": root / "ftmo.yaml",
        "redacted_account": root / "redacted_account.yaml",
    }
    paths["FTMO"].write_text(ftmo_text)
    paths["redacted_account"].write_text(redacted_account_text)
    manifest = root / "symbol_authority.json"
    manifest.write_text(json.dumps({
        "schema": "gtos.costs.symbol_authority.v1",
        "profiles": {
            account: {
                "path": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for account, path in paths.items()
        },
    }))
    return ProfileSymbolAuthority(manifest, paths)


def test_profile_alias_authority_is_hash_bound_and_read_directly():
    manifest = json.loads(MANIFEST.read_text())
    bound = manifest["source_scope"]["profile_symbol_authority"]
    for account, path in PROFILE_PATHS.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == bound[account]["sha256"]
    mappings = profile_broker_symbols()
    assert mappings["USOIL_cash"] == {"FTMO": "USOIL.cash", "redacted_account": "USOUSD"}
    assert mappings["UKOIL_cash"] == {"FTMO": "UKOIL.cash", "redacted_account": "UKOUSD"}
    # A broker alias is account-local. FTMO's US100.cash spelling cannot be used as
    # an undeclared route to redacted_account's NDX100 record.
    assert resolve_account_symbol("redacted_account", "US100.cash", {"NDX100"}) is None


def test_profile_alias_resolution_fails_closed_on_manifest_drift(tmp_path):
    copies = {}
    profiles = {}
    for account, source in PROFILE_PATHS.items():
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        copies[account] = target
        profiles[account] = {
            "path": target.name,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    manifest = tmp_path / "authority.json"
    manifest.write_text(json.dumps({
        "schema": "gtos.costs.symbol_authority.v1", "profiles": profiles,
    }))
    copies["FTMO"].write_text(copies["FTMO"].read_text() + "\n# drift probe\n")
    authority = ProfileSymbolAuthority(manifest, copies)
    with pytest.raises(SymbolAuthorityError, match="authority drift"):
        profile_broker_symbols(authority)


def test_profile_authority_refuses_duplicate_and_ambiguous_identities(tmp_path):
    unique = """instruments:\n  Solo:\n    market:\n      mt5_symbol: SOLO\n"""
    alias_collision = """instruments:\n  First:\n    market:\n      mt5_symbol: SHARED\n  Second:\n    market:\n      mt5_symbol: SHARED\n"""
    authority = _profile_authority_from_text(
        tmp_path / "alias", ftmo_text=alias_collision, redacted_account_text=unique
    )
    with pytest.raises(SymbolAuthorityError, match="within-account broker alias ambiguity"):
        profile_broker_symbols(authority)

    case_collision = """instruments:\n  Gold:\n    market:\n      mt5_symbol: GOLD\n  gold:\n    market:\n      mt5_symbol: GOLD2\n"""
    authority = _profile_authority_from_text(
        tmp_path / "case", ftmo_text=case_collision, redacted_account_text=unique
    )
    with pytest.raises(SymbolAuthorityError, match="case-normalized canonical ambiguity"):
        profile_broker_symbols(authority)

    exact_duplicate = """instruments:\n  Gold:\n    market:\n      mt5_symbol: GOLD\n  Gold:\n    market:\n      mt5_symbol: GOLD2\n"""
    authority = _profile_authority_from_text(
        tmp_path / "duplicate", ftmo_text=exact_duplicate, redacted_account_text=unique
    )
    with pytest.raises(SymbolAuthorityError, match="duplicate key"):
        profile_broker_symbols(authority)

    # The account is a lawful discriminator. The same spelling on two accounts is
    # accepted, while an account-free lookup refuses to pick one by YAML order.
    authority = _profile_authority_from_text(
        tmp_path / "cross_account",
        ftmo_text="""instruments:\n  Alpha:\n    market:\n      mt5_symbol: SHARED\n""",
        redacted_account_text="""instruments:\n  Beta:\n    market:\n      mt5_symbol: SHARED\n""",
    )
    assert canonical_symbol("SHARED", authority) is None
    assert resolve_account_symbol("FTMO", "SHARED", {"SHARED"}, authority) == "SHARED"
    assert resolve_account_symbol(
        "redacted_account", "SHARED", {"SHARED"}, authority
    ) == "SHARED"


def test_redacted_account_oils_resolve_to_captured_instruments_but_missing_slippage_refuses():
    truth = load_broker_true_costs()
    resolved, uso = truth.resolve_instrument("redacted_account", "USOIL_cash")
    assert resolved == "USOUSD"
    assert uso["commission"]["coverage"] == "MEASURED"
    assert uso["spread_price"]["coverage"] == "MEASURED"
    resolved, uko = truth.resolve_instrument("redacted_account", "UKOIL_cash")
    assert resolved == "UKOUSD"
    assert uko["commission"]["coverage"] == "MEASURED"
    with pytest.raises(CostTruthError, match="no broker truth"):
        truth.resolve_instrument("redacted_account", "USOIL.cash")
    with pytest.raises(CostTruthError, match="slippage.*NOT_EVALUABLE"):
        cost_r(
            "USOIL_cash",
            "redacted_account",
            4.0,
            sl_distance_price=2.0,
            entry_price=75.0,
            entry_utc=dt.datetime(2026, 6, 20, 12, tzinfo=UTC),
        )


def test_schedule_era_cannot_become_decidable_from_zero_dispersion():
    model = load_spread_model()
    doc = model.doc
    account, symbol, quarter = next(
        (a, s, q)
        for a, syms in doc["accounts"].items()
        for s, rec in syms.items()
        if canonical_symbol(s) is not None
        for q, era in (rec.get("eras") or {}).items()
        if era["class"] == "SCHEDULE" and era.get("decidable") is True
    )
    instant = dt.datetime(int(quarter[:4]), (int(quarter[-1]) - 1) * 3 + 2, 15, 12, tzinfo=UTC)
    estimate = model.estimate(symbol, account, instant)
    assert estimate.era_class == "SCHEDULE"
    assert estimate.detail["artifact_decidable"] is True
    assert estimate.decidable is False
    assert estimate.coverage is Coverage.MODELLED
    with pytest.raises(SpreadModelError, match="not decidable"):
        model.estimate(symbol, account, instant, require_decidable=True)


def test_slippage_is_a_price_displacement_and_scales_with_stop_geometry():
    at = dt.datetime(2026, 6, 20, 12, tzinfo=UTC)
    tight = cost_r(
        "XAUUSD", "FTMO", 2.0, sl_distance_price=10.0, entry_price=4300.0, entry_utc=at
    )
    wide = cost_r(
        "XAUUSD", "FTMO", 2.0, sl_distance_price=20.0, entry_price=4300.0, entry_utc=at
    )
    assert tight.detail["slippage"]["expected_adverse_price"] == wide.detail["slippage"][
        "expected_adverse_price"
    ]
    assert tight.slippage_r.value == pytest.approx(2.0 * wide.slippage_r.value)
    assert tight.slippage_r.coverage is Coverage.MEASURED


def test_historical_fx_moves_per_lot_commission_and_propagates_coverage():
    old = cost_r(
        "USDJPY",
        "FTMO",
        2.0,
        sl_distance_price=0.1,
        entry_utc=dt.datetime(2001, 6, 15, 12, tzinfo=UTC),
    )
    recent = cost_r(
        "USDJPY",
        "FTMO",
        2.0,
        sl_distance_price=0.1,
        entry_utc=dt.datetime(2026, 6, 20, 12, tzinfo=UTC),
    )
    assert old.detail["fx_conversion"]["source_broker_date"].startswith("2001-")
    assert old.detail["usd_per_price_unit_per_lot"] != recent.detail[
        "usd_per_price_unit_per_lot"
    ]
    assert old.commission_r.value != recent.commission_r.value
    assert old.commission_r.coverage is Coverage.TRANSFERRED
    assert "completed_utc=" in old.commission_r.provenance
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert old.detail["fx_conversion"]["cost_inputs_manifest_sha256"] == manifest_sha
    assert manifest_sha in old.commission_r.provenance
    assert old.total_r.coverage is Coverage.TRANSFERRED

    transferred_commission = cost_r(
        "CADJPY",
        "FTMO",
        2.0,
        sl_distance_price=0.1,
        entry_utc=dt.datetime(2001, 6, 15, 12, tzinfo=UTC),
        slippage_model=_ZeroSlippage(),
    )
    assert transferred_commission.commission_r.coverage is Coverage.TRANSFERRED
    assert "historical USDJPY D1 close" in (
        transferred_commission.commission_r.transferred_from or ""
    )
    assert "completed_utc=" in transferred_commission.commission_r.provenance


def test_historical_fx_never_falls_back_to_snapshot_without_a_date_or_fresh_rate():
    with pytest.raises(CostTruthError, match="entry_utc.*NOT_EVALUABLE"):
        cost_r("USDJPY", "FTMO", 2.0, sl_distance_price=0.1)
    with pytest.raises(CostTruthError, match="stale.*NOT_EVALUABLE"):
        cost_r(
            "USDJPY",
            "FTMO",
            2.0,
            sl_distance_price=0.1,
            entry_utc=dt.datetime(2026, 8, 8, 12, tzinfo=UTC),
        )


def test_historical_fx_uses_only_a_strictly_completed_d1_bar():
    first_completion = dt.datetime(2020, 1, 2, tzinfo=UTC)
    second_completion = dt.datetime(2020, 1, 3, tzinfo=UTC)
    doc = {
        "schema": "gtos.costs.historical_fx_d1.v2",
        "coverage": "TRANSFERRED",
        "max_staleness_seconds": 7 * 86400,
        "series": {
            "JPY": {
                "source_pair": "USDJPY",
                "source_sha256": "f" * 64,
                "first_broker_date": "2020-01-01",
                "rows": [
                    [int(first_completion.timestamp()), dt.date(2020, 1, 1).toordinal(), 100.0],
                    [int(second_completion.timestamp()), dt.date(2020, 1, 2).toordinal(), 200.0],
                ],
            }
        },
    }
    fx = HistoricalFxRates(doc)
    # At the exact close/completion instant, that close was not available before
    # the entry decision. The prior completed bar is the only lawful input.
    exact = fx.rate_at("JPY", second_completion, server="FTMO")
    assert exact.profit_currency_per_usd == 100.0
    assert exact.source_broker_date == "2020-01-01"
    intraday = fx.rate_at(
        "JPY", first_completion + dt.timedelta(hours=12), server="FTMO"
    )
    assert intraday.profit_currency_per_usd == 100.0
    assert intraday.source_broker_date == "2020-01-01"
    one_second_later = fx.rate_at(
        "JPY", second_completion + dt.timedelta(seconds=1), server="FTMO"
    )
    assert one_second_later.profit_currency_per_usd == 200.0
    assert one_second_later.source_completed_utc == second_completion.isoformat()
    with pytest.raises(FxConversionError, match="begins"):
        fx.rate_at("JPY", first_completion, server="FTMO")


def test_notional_bp_commission_is_invariant_to_fx_date():
    kwargs = dict(
        symbol="USDCAD",
        account="FTMO",
        holding_hours=2.0,
        sl_distance_price=0.01,
        entry_price=1.35,
        slippage_model=_ZeroSlippage(),
    )
    old = cost_r(entry_utc=dt.datetime(2001, 6, 15, 12, tzinfo=UTC), **kwargs)
    recent = cost_r(entry_utc=dt.datetime(2026, 6, 20, 12, tzinfo=UTC), **kwargs)
    assert old.commission_r.value == recent.commission_r.value
    assert "fx_conversion" not in old.detail
    assert old.detail["pnl_conversion"]["historical_fx_required"] is False
    assert old.detail["pnl_conversion"]["component_consumers"] == []
    assert old.commission_r.coverage is Coverage.MEASURED


def test_non_usd_zero_commission_is_decidable_without_unused_fx_conversion():
    old = cost_r(
        "GER40.cash",
        "FTMO",
        2.0,
        sl_distance_price=100.0,
        entry_price=5000.0,
        entry_utc=dt.datetime(2001, 6, 15, 12, tzinfo=UTC),
    )
    recent = cost_r(
        "GER40.cash",
        "FTMO",
        2.0,
        sl_distance_price=100.0,
        entry_price=18000.0,
        entry_utc=dt.datetime(2026, 6, 20, 12, tzinfo=UTC),
    )
    assert old.commission_r.value == recent.commission_r.value == 0.0
    assert old.commission_r.coverage is Coverage.MEASURED
    assert "fx_conversion" not in old.detail
    assert old.detail["pnl_conversion"]["historical_fx_required"] is False
    assert old.detail["pnl_conversion"]["component_consumers"] == []


def test_missing_fx_only_refuses_a_component_that_consumes_it():
    at = dt.datetime(2026, 6, 20, 12, tzinfo=UTC)
    missing = _MissingHistoricalFx()
    zero = cost_r(
        "GER40.cash", "FTMO", 2.0,
        sl_distance_price=100.0,
        entry_price=18000.0,
        entry_utc=at,
        historical_fx=missing,
    )
    notional = cost_r(
        "USDCAD", "FTMO", 2.0,
        sl_distance_price=0.01,
        entry_price=1.35,
        entry_utc=at,
        historical_fx=missing,
        slippage_model=_ZeroSlippage(),
    )
    assert zero.commission_r.value == 0.0
    assert notional.commission_r.value > 0.0
    assert zero.detail["pnl_conversion"]["component_consumers"] == []
    assert notional.detail["pnl_conversion"]["component_consumers"] == []
    with pytest.raises(CostTruthError, match="missing historical FX probe"):
        cost_r(
            "USDJPY", "FTMO", 2.0,
            sl_distance_price=0.1,
            entry_utc=at,
            historical_fx=missing,
        )


def test_runtime_cost_loaders_reverify_current_bytes_before_cache(tmp_path):
    fx_root, fx_manifest, fx_path, _ = _manifest_bound_copy(
        tmp_path, "historical_fx", DEFAULT_FX_ARTIFACT
    )
    accepted_fx = load_historical_fx(
        fx_path, manifest_path=fx_manifest, authority_root=fx_root
    )
    assert accepted_fx.doc["schema"] == "gtos.costs.historical_fx_d1.v2"
    assert accepted_fx.artifact_sha256 == hashlib.sha256(fx_path.read_bytes()).hexdigest()
    assert accepted_fx.manifest_sha256 == hashlib.sha256(
        fx_manifest.read_bytes()
    ).hexdigest()
    # Same pathname after a successful cached parse: current bytes still control.
    fx_path.write_bytes(fx_path.read_bytes() + b"tamper")
    with pytest.raises(FxConversionError, match="hash mismatch"):
        load_historical_fx(fx_path, manifest_path=fx_manifest, authority_root=fx_root)

    slip_root, slip_manifest, slip_path, _ = _manifest_bound_copy(
        tmp_path, "slippage_price", DEFAULT_SLIPPAGE_ARTIFACT
    )
    accepted_slip = load_slippage_model(
        slip_path, manifest_path=slip_manifest, authority_root=slip_root
    )
    assert accepted_slip.doc["schema"] == "gtos.costs.slippage_price.v1"
    assert accepted_slip.artifact_sha256 == hashlib.sha256(
        slip_path.read_bytes()
    ).hexdigest()
    assert accepted_slip.manifest_sha256 == hashlib.sha256(
        slip_manifest.read_bytes()
    ).hexdigest()
    slip_path.write_bytes(slip_path.read_bytes() + b"\n")
    with pytest.raises(SlippageModelError, match="hash mismatch"):
        load_slippage_model(
            slip_path, manifest_path=slip_manifest, authority_root=slip_root
        )

    broker_path = tmp_path / "BROKER_TRUE_COSTS_V1.json"
    broker_path.write_bytes(DEFAULT_BROKER_COST_ARTIFACT.read_bytes())
    broker = load_broker_true_costs(broker_path)
    assert broker.artifact_sha256 == hashlib.sha256(broker_path.read_bytes()).hexdigest()
    broker_path.write_bytes(broker_path.read_bytes() + b"tamper")
    with pytest.raises(CostTruthError, match="not valid JSON"):
        load_broker_true_costs(broker_path)

    spread_path = tmp_path / "SPREAD_MODEL_V1.json"
    spread_path.write_bytes(DEFAULT_SPREAD_MODEL_ARTIFACT.read_bytes())
    spread_model = load_spread_model(spread_path)
    assert spread_model.artifact_sha256 == hashlib.sha256(
        spread_path.read_bytes()
    ).hexdigest()
    spread_path.write_bytes(spread_path.read_bytes() + b"tamper")
    with pytest.raises(SpreadModelError, match="not valid JSON"):
        load_spread_model(spread_path)


def test_cost_input_manifest_schema_containment_and_exact_path_are_enforced(tmp_path):
    root, manifest, target, payload = _manifest_bound_copy(
        tmp_path, "slippage_price", DEFAULT_SLIPPAGE_ARTIFACT
    )
    doc = json.loads(manifest.read_text())
    doc["schema"] = "gtos.phase21.cost_inputs_manifest.future"
    manifest.write_text(json.dumps(doc))
    with pytest.raises(SlippageModelError, match="unsupported cost input manifest schema"):
        load_slippage_model(target, manifest_path=manifest, authority_root=root)

    doc["schema"] = "gtos.phase21.cost_inputs_manifest.v1"
    doc["outputs"]["slippage_price"]["path"] = "../escape.json"
    manifest.write_text(json.dumps(doc))
    with pytest.raises(SlippageModelError, match="not a contained normalized relative path"):
        load_slippage_model(manifest_path=manifest, authority_root=root)

    doc["outputs"]["slippage_price"] = {
        "path": str(target.relative_to(root)),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    manifest.write_text(json.dumps(doc))
    rogue = root / "inputs" / "rogue.json"
    rogue.write_bytes(payload)
    with pytest.raises(SlippageModelError, match="does not equal manifest-bound path"):
        load_slippage_model(rogue, manifest_path=manifest, authority_root=root)

    outside_manifest = tmp_path / "outside_manifest.json"
    outside_manifest.write_text(json.dumps(doc))
    with pytest.raises(SlippageModelError, match="manifest escapes cost authority root"):
        load_slippage_model(
            target, manifest_path=outside_manifest, authority_root=root
        )


def test_fd_component_identity_preserves_exact_float_order_and_rejects_bad_rows():
    got = component_sum_r(0.335891148, 0.02, 0.002783978, 0.0)
    assert got == 0.358675126
    assert got != sum([0.335891148, 0.02, 0.002783978, 0.0])
    for bad in (-0.1, float("nan"), float("inf"), True):
        with pytest.raises(CostTruthError):
            component_sum_r(bad, 0.0, 0.0, 0.0)


def test_quote_geometry_reconciles_physical_spread_and_charges_it_exactly_once(tmp_path):
    base = dict(
        symbol="XAUUSD",
        account="redacted_account",
        holding_hours=2.0,
        sl_distance_price=12.0,
        entry_price=4100.0,
        entry_utc=dt.datetime(2026, 6, 20, 12, tzinfo=UTC),
    )
    explicit = cost_r(**base)
    model_price = explicit.detail["spread"]["spread_price"]
    # A transacted spread legitimately differs from the snapshot/model percentile.
    observed_price = model_price * 1.7
    bid = base["entry_price"] - observed_price
    observed_price = base["entry_price"] - bid
    authority_row = {
        "schema": QUOTE_GEOMETRY_ROW_SCHEMA,
        "trade_id": "trade-123",
        "account": "redacted_account",
        "symbol": "XAUUSD",
        "entry_utc": base["entry_utc"].isoformat(),
        "side": "LONG",
        "gross_basis": "fill_anchored_quote_geometry",
        "gross_includes_spread": True,
        "source_status": "captured",
        "bid_price": bid,
        "ask_price": base["entry_price"],
        "entry_fill_price": base["entry_price"],
        "stop_price": base["entry_price"] - base["sl_distance_price"],
        "spread_price": observed_price,
        "coverage": "MEASURED",
    }
    authority = tmp_path / "quote_fill_rows.jsonl"
    authority.write_text(json.dumps(authority_row, sort_keys=True) + "\n")
    authority_sha = hashlib.sha256(authority.read_bytes()).hexdigest()
    evidence = SpreadGeometryEvidence(
        source_path=authority,
        source_sha256=authority_sha,
        row_index=0,
        trade_id="trade-123",
    )
    geometry = cost_r(
        **base,
        spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
        geometry_spread_evidence=evidence,
    )
    assert geometry.spread_r.value == 0.0
    assert geometry.attributed_spread_r is not None
    assert geometry.attributed_spread_r.value == observed_price / base["sl_distance_price"]
    assert geometry.detail["spread"]["model_spread_price"] == model_price
    assert geometry.detail["spread"]["physical_spread_r"] != explicit.spread_r.value
    assert explicit.detail["spread"]["accounting"] == "explicit_component"
    assert explicit.detail["spread"]["crossings_charged"] == 1
    assert explicit.spread_r.value > 0.0
    assert geometry.detail["spread"]["accounting"] == "quote_geometry"
    assert geometry.detail["spread"]["crossings_charged"] == 0
    assert geometry.spread_r.value == 0.0
    assert explicit.total_r.value == component_sum_r(
        explicit.spread_r.value,
        explicit.slippage_r.value,
        explicit.swap_r.value,
        explicit.commission_r.value,
    )
    assert geometry.total_r.value == component_sum_r(
        0.0,
        geometry.slippage_r.value,
        geometry.swap_r.value,
        geometry.commission_r.value,
    )
    with pytest.raises(CostTruthError, match="requires SpreadGeometryEvidence"):
        cost_r(
            **base,
            spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
            geometry_spread_price=observed_price,
        )
    wrong_trade = SpreadGeometryEvidence(
        source_path=authority,
        source_sha256=authority_sha,
        row_index=0,
        trade_id="different-trade",
    )
    with pytest.raises(CostTruthError, match="trade_id.*does not match"):
        cost_r(
            **base,
            spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
            geometry_spread_evidence=wrong_trade,
        )
    bad_price_row = {**authority_row, "spread_price": observed_price * 2.0}
    bad_price_source = tmp_path / "bad_quote_fill_rows.jsonl"
    bad_price_source.write_text(json.dumps(bad_price_row, sort_keys=True) + "\n")
    bad_price_evidence = SpreadGeometryEvidence(
        source_path=bad_price_source,
        source_sha256=hashlib.sha256(bad_price_source.read_bytes()).hexdigest(),
        row_index=0,
        trade_id="trade-123",
    )
    with pytest.raises(CostTruthError, match="does not reconcile to ask-bid"):
        cost_r(
            **base,
            spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
            geometry_spread_evidence=bad_price_evidence,
        )
    authority.write_text(authority.read_text() + "{}\n")
    with pytest.raises(CostTruthError, match="source hash mismatch"):
        cost_r(
            **base,
            spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
            geometry_spread_evidence=evidence,
        )
    with pytest.raises(CostTruthError, match="only valid"):
        cost_r(**base, geometry_spread_evidence=evidence)


@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_quote_geometry_preserves_approved_r_after_marketable_price_improvement(
    tmp_path, side
):
    entry = dt.datetime(2026, 6, 22, 12, tzinfo=UTC)
    row = _price_improved_geometry_row(side=side, entry_utc=entry)
    evidence = _geometry_evidence(
        tmp_path, f"improved_{side.lower()}.jsonl", row
    )
    fill = row["entry_fill_price"]

    breakdown = cost_r(
        "XAUUSD",
        "redacted_account",
        2.0,
        sl_distance_price=1.0,
        entry_price=fill,
        side=side,
        entry_utc=entry,
        spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
        geometry_spread_evidence=evidence,
    )

    geometry = breakdown.detail["spread"]["geometry_authority"]
    assert abs(fill - row["stop_price"]) == 0.5
    assert geometry["authority_schema"] == (
        QUOTE_GEOMETRY_APPROVED_RISK_ROW_SCHEMA
    )
    assert geometry["risk_denominator_basis"] == (
        APPROVED_PRE_SUBMISSION_RISK_DENOMINATOR_BASIS
    )
    assert geometry["approved_entry_price"] == 100.0
    assert geometry["approved_stop_price"] == row["stop_price"]
    assert geometry["approved_risk_distance"] == 1.0
    assert geometry["actual_fill_stop_distance"] == 0.5
    assert breakdown.detail["sl_distance_price"] == 1.0
    assert breakdown.spread_r.value == 0.0
    assert breakdown.attributed_spread_r is not None
    assert breakdown.attributed_spread_r.value == pytest.approx(0.1)
    assert breakdown.total_r.value == component_sum_r(
        0.0,
        breakdown.slippage_r.value,
        breakdown.swap_r.value,
        breakdown.commission_r.value,
    )

    packet = build_post_lifecycle_component_cost(
        trade_id=row["trade_id"],
        symbol="XAUUSD",
        account="redacted_account",
        entry_utc=entry,
        exit_utc=entry + dt.timedelta(hours=2),
        entry_price=fill,
        exit_price=fill + (2.0 if side == "LONG" else -2.0),
        sl_distance_price=1.0,
        side=side,
        geometry_spread_evidence=evidence,
        lifecycle_provenance=f"price-improved {side} test lifecycle",
        pretrade_expected_cost_ref=f"pretrade-{side.lower()}",
    )
    complete = require_complete_post_lifecycle_component_cost(packet)
    assert packet["lifecycle"]["quote_geometry"] == geometry
    assert packet["components"]["spread_r"]["value"] == 0.0
    assert packet["components"]["spread_r"][
        "attributed_physical_spread_r"
    ] == pytest.approx(0.1)
    assert complete.component_sum_r == packet["total_cost_r"]
    gross_r = 2.0
    assert gross_r - complete.component_sum_r == gross_r - component_sum_r(*(
        packet["components"][field]["value"]
        for field in (
            "spread_r",
            "expected_slippage_r",
            "swap_cost_r",
            "commission_r",
        )
    ))

    # Even an internally re-summed packet may not deduct the physical spread a
    # second time from fill-anchored gross.
    double_spread = json.loads(json.dumps(packet))
    double_spread["components"]["spread_r"]["value"] = double_spread[
        "components"
    ]["spread_r"]["attributed_physical_spread_r"]
    double_spread["total_cost_r"] = component_sum_r(*(
        double_spread["components"][field]["value"]
        for field in (
            "spread_r",
            "expected_slippage_r",
            "swap_cost_r",
            "commission_r",
        )
    ))
    refused = assess_post_lifecycle_component_cost(double_spread)
    assert refused.status == "NOT_EVALUABLE"
    assert refused.component_sum_r is None
    assert "spread_already_in_gross_must_not_be_deducted" in refused.failures

    # Recomputing the packet's self-hash cannot turn a mutated geometry receipt
    # into authority: assessment re-reads the original hash-bound physical row.
    self_rehashed_tamper = json.loads(json.dumps(packet))
    self_rehashed_tamper["lifecycle"]["quote_geometry"][
        "approved_entry_price"
    ] = 100.25
    _rehash_lifecycle_record(self_rehashed_tamper)
    tamper_assessment = assess_post_lifecycle_component_cost(self_rehashed_tamper)
    assert tamper_assessment.status == "NOT_EVALUABLE"
    assert "lifecycle_record_hash_mismatch" not in tamper_assessment.failures
    assert "quote_geometry_authority_receipt_mismatch" in (
        tamper_assessment.failures
    )


def test_quote_geometry_approved_r_basis_is_explicit_and_fail_closed(tmp_path):
    entry = dt.datetime(2026, 6, 22, 12, tzinfo=UTC)
    row = _price_improved_geometry_row(side="LONG", entry_utc=entry)

    # With no discriminator or approved geometry, legacy v1 behavior remains:
    # the caller denominator must equal actual fill-to-stop distance.
    legacy = {
        key: value
        for key, value in row.items()
        if key not in {
            "risk_denominator_basis",
            "approved_entry_price",
            "approved_stop_price",
            "approved_risk_distance",
        }
    }
    legacy["schema"] = QUOTE_GEOMETRY_ROW_SCHEMA
    legacy_evidence = _geometry_evidence(tmp_path, "legacy_improved.jsonl", legacy)
    with pytest.raises(CostTruthError, match="fill/stop distance .* does not match"):
        cost_r(
            "XAUUSD",
            "redacted_account",
            2.0,
            sl_distance_price=1.0,
            entry_price=99.5,
            side="LONG",
            entry_utc=entry,
            spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
            geometry_spread_evidence=legacy_evidence,
        )

    missing_approved_entry = dict(row)
    del missing_approved_entry["approved_entry_price"]
    missing_discriminator = dict(row)
    del missing_discriminator["risk_denominator_basis"]
    adversaries = (
        (
            "missing_discriminator.jsonl",
            missing_discriminator,
            1.0,
            "missing=.*risk_denominator_basis",
        ),
        (
            "unknown_field.jsonl",
            {**row, "caller_r_distance": 1.0},
            1.0,
            "unknown_or_mixed=.*caller_r_distance",
        ),
        (
            "mixed_into_legacy_v1.jsonl",
            {**row, "schema": QUOTE_GEOMETRY_ROW_SCHEMA},
            1.0,
            "unknown_or_mixed=.*approved_entry_price",
        ),
        (
            "missing_approved_entry.jsonl",
            missing_approved_entry,
            1.0,
            "missing=.*approved_entry_price",
        ),
        (
            "unsupported_basis.jsonl",
            {**row, "risk_denominator_basis": "caller_supplied_distance"},
            1.0,
            "unsupported risk_denominator_basis",
        ),
        (
            "bad_approved_geometry.jsonl",
            {**row, "approved_risk_distance": 1.1},
            1.0,
            "approved entry/stop distance .* does not match approved_risk_distance",
        ),
        (
            "wrong_caller_r.jsonl",
            row,
            2.0,
            "approved_risk_distance .* does not match sl_distance_price",
        ),
        (
            "different_stop.jsonl",
            {
                **row,
                "approved_entry_price": 100.1,
                "approved_stop_price": 99.1,
            },
            1.0,
            "approved_stop_price .* does not match actual stop_price",
        ),
        (
            "actual_stop_wrong_side.jsonl",
            {
                **row,
                "stop_price": 99.6,
                "approved_entry_price": 100.6,
                "approved_stop_price": 99.6,
            },
            1.0,
            "stop .* wrong side of entry fill",
        ),
    )
    for name, adversarial_row, sl_distance, error in adversaries:
        evidence = _geometry_evidence(tmp_path, name, adversarial_row)
        with pytest.raises(CostTruthError, match=error):
            cost_r(
                "XAUUSD",
                "redacted_account",
                2.0,
                sl_distance_price=sl_distance,
                entry_price=99.5,
                side="LONG",
                entry_utc=entry,
                spread_accounting=SpreadAccounting.QUOTE_GEOMETRY,
                geometry_spread_evidence=evidence,
            )


def test_post_lifecycle_cost_uses_actual_elapsed_and_never_pretrade_swap(tmp_path):
    entry = dt.datetime(2026, 6, 26, 20, tzinfo=UTC)  # Friday
    exit_ = dt.datetime(2026, 6, 29, 20, tzinfo=UTC)  # Monday, 72 actual hours
    row = {
        "schema": QUOTE_GEOMETRY_ROW_SCHEMA,
        "trade_id": "lifecycle-1",
        "account": "redacted_account",
        "symbol": "XAUUSD",
        "entry_utc": entry.isoformat(),
        "side": "LONG",
        "gross_basis": "fill_anchored_quote_geometry",
        "gross_includes_spread": True,
        "source_status": "captured",
        "bid_price": 4099.5,
        "ask_price": 4100.0,
        "entry_fill_price": 4100.0,
        "stop_price": 4088.0,
        "spread_price": 0.5,
        "coverage": "MEASURED",
    }
    source = tmp_path / "lifecycle_quotes.jsonl"
    source.write_text(json.dumps(row, sort_keys=True) + "\n")
    evidence = SpreadGeometryEvidence(
        source_path=source,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        row_index=0,
        trade_id="lifecycle-1",
    )
    packet = build_post_lifecycle_component_cost(
        trade_id="lifecycle-1",
        symbol="XAUUSD",
        account="redacted_account",
        entry_utc=entry,
        exit_utc=exit_,
        entry_price=4100.0,
        exit_price=4120.0,
        sl_distance_price=12.0,
        side="LONG",
        geometry_spread_evidence=evidence,
        lifecycle_provenance="timewarp terminal simulated exit state row lifecycle-1",
        pretrade_expected_cost_ref="candidate-occurrence-1",
    )
    assessment = require_complete_post_lifecycle_component_cost(packet)
    assert assessment.complete is True
    assert packet["cost_role"] == "post_lifecycle_component_cost"
    assert packet["lifecycle"]["elapsed_holding_hours"] == 72.0
    assert packet["lifecycle"]["holding_source_status"] == (
        "actual_simulated_entry_exit_elapsed"
    )
    assert packet["lifecycle"]["source_status"] == "actual_simulated_lifecycle"
    assert len(packet["lifecycle"]["record_sha256"]) == 64
    assert packet["predecessor"]["cost_role"] == "pretrade_expected_cost"
    assert packet["predecessor"]["components_reused"] == []
    assert packet["broker_realized_status"] == (
        "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS"
    )
    assert packet["components"]["expected_slippage_r"]["source_role"] == (
        "source_bound_expected_slippage_not_broker_realized"
    )
    assert packet["components"]["swap_cost_r"]["source_role"] == (
        "actual_elapsed_broker_rollover_component"
    )
    assert packet["components"]["spread_r"]["value"] == 0.0
    assert packet["components"]["spread_r"]["attributed_physical_spread_r"] > 0
    complete_cost = require_complete_post_lifecycle_component_cost(packet)
    gross_r = 2.0
    expected_net_r = gross_r - component_sum_r(
        packet["components"]["spread_r"]["value"],
        packet["components"]["expected_slippage_r"]["value"],
        packet["components"]["swap_cost_r"]["value"],
        packet["components"]["commission_r"]["value"],
    )
    assert gross_r - complete_cost.component_sum_r == expected_net_r

    # The observed physical spread remains attributed in fill-anchored gross,
    # while its additional deduction is exactly zero.  Reintroducing it into
    # the component slot and re-summing the packet must still fail closed; this
    # adversary cannot be caught by the ordinary component identity check.
    double_spread = json.loads(json.dumps(packet))
    double_spread["components"]["spread_r"]["value"] = double_spread[
        "components"
    ]["spread_r"]["attributed_physical_spread_r"]
    double_spread["total_cost_r"] = component_sum_r(*(
        double_spread["components"][field]["value"]
        for field in (
            "spread_r",
            "expected_slippage_r",
            "swap_cost_r",
            "commission_r",
        )
    ))
    double_spread_assessment = assess_post_lifecycle_component_cost(double_spread)
    assert double_spread_assessment.status == "NOT_EVALUABLE"
    assert double_spread_assessment.component_sum_r is None
    assert "post_lifecycle_component_identity_mismatch" not in (
        double_spread_assessment.failures
    )
    assert "spread_already_in_gross_must_not_be_deducted" in (
        double_spread_assessment.failures
    )
    with pytest.raises(CostPacketIncompleteError):
        require_complete_post_lifecycle_component_cost(double_spread)
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert packet["cost_input_authority"]["manifest_sha256"] == manifest_sha
    assert packet["components"]["expected_slippage_r"][
        "cost_inputs_manifest_sha256"
    ] == manifest_sha
    assert manifest_sha in packet["components"]["expected_slippage_r"]["provenance"]
    assert len(packet["cost_input_authority"][
        "broker_true_costs_artifact_sha256"
    ]) == 64

    # A forecast horizon or a pretrade component cannot be substituted post-exit.
    wrong_elapsed = json.loads(json.dumps(packet))
    wrong_elapsed["lifecycle"]["elapsed_holding_hours"] = 8.0
    assessed = assess_post_lifecycle_component_cost(wrong_elapsed)
    assert assessed.status == "NOT_EVALUABLE"
    assert assessed.component_sum_r is None
    assert "actual_elapsed_holding_mismatch" in assessed.failures

    reused = json.loads(json.dumps(packet))
    reused["predecessor"]["components_reused"] = ["swap_cost_r"]
    assert "pretrade_components_reused" in (
        assess_post_lifecycle_component_cost(reused).failures
    )

    missing = json.loads(json.dumps(packet))
    del missing["components"]["swap_cost_r"]
    assessed = assess_post_lifecycle_component_cost(missing)
    assert assessed.status == "NOT_EVALUABLE"
    assert assessed.component_sum_r is None
    with pytest.raises(CostPacketIncompleteError):
        require_complete_post_lifecycle_component_cost(missing)

    pretrade_disguise = json.loads(json.dumps(packet))
    pretrade_disguise["cost_role"] = "pretrade_expected_cost"
    assert "wrong_cost_role_not_post_lifecycle" in (
        assess_post_lifecycle_component_cost(pretrade_disguise).failures
    )

    source.write_text(source.read_text() + "{}\n")
    refused = build_post_lifecycle_component_cost(
        trade_id="lifecycle-1",
        symbol="XAUUSD",
        account="redacted_account",
        entry_utc=entry,
        exit_utc=exit_,
        entry_price=4100.0,
        exit_price=4120.0,
        sl_distance_price=12.0,
        geometry_spread_evidence=evidence,
        lifecycle_provenance="timewarp terminal simulated exit state row lifecycle-1",
    )
    assert refused["status"] == "NOT_EVALUABLE"
    assert refused["total_cost_r"] is None


def test_truth_mode_cost_packet_is_terminal_non_numeric_when_a_component_is_incomplete():
    values = {
        "spread_r": 0.1,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.003,
        "commission_r": 0.004,
    }
    packet = {
        "total_cost_components": values,
        "total_cost_r": component_sum_r(*(values[k] for k in (
            "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r"
        ))),
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "tick_cost": {"spread_r": 0.1, "source_status": "captured"},
        "quote_authority": {"quote_source": "historical_ftmo_predecision_tick"},
        "expected_slippage_r": 0.02,
        "expected_slippage_source": "SLIPPAGE_PRICE_V1 exact account/profile symbol",
        "swap_cost": {
            "cost_r": 0.003,
            "source_status": "captured",
            "model_version": "broker_clock_rollover_v1",
        },
        "commission_cost": {
            "cost_r": 0.004,
            "source_status": "captured",
            "included_in_total_cost_r": True,
            "comparator_only": False,
            "provenance": "BROKER_TRUE_COSTS_V1 + historical FX",
            "artifact": "BROKER_TRUE_COSTS_V1.json",
        },
    }
    complete = require_complete_cost_packet(packet)
    assert complete.complete is True
    assert complete.component_sum_r == packet["total_cost_r"]

    incomplete = json.loads(json.dumps(packet))
    incomplete["total_cost_components"]["expected_slippage_r"] = None
    incomplete["total_cost_components"]["authority_fallback_total_cost_r"] = 0.12
    incomplete["total_cost_r"] = 0.12
    assessment = assess_cost_packet_completeness(incomplete)
    assert assessment.status == "NOT_EVALUABLE"
    assert assessment.complete is False
    assert assessment.component_sum_r is None
    assert "invalid_component:expected_slippage_r" in assessment.failures
    assert "legacy_authority_fallback_present" in assessment.failures
    with pytest.raises(CostPacketIncompleteError) as excinfo:
        require_complete_cost_packet(incomplete)
    assert excinfo.value.assessment == assessment
    assert excinfo.value.assessment.component_sum_r is None

    mismatch = json.loads(json.dumps(packet))
    mismatch["total_cost_r"] += 1e-6
    mismatch_assessment = assess_cost_packet_completeness(mismatch)
    assert "total_cost_r_component_identity_mismatch" in mismatch_assessment.failures
    assert mismatch_assessment.component_sum_r is None

    plausible_but_unsourced = json.loads(json.dumps(packet))
    del plausible_but_unsourced["commission_cost"]["provenance"]
    unsourced = assess_cost_packet_completeness(plausible_but_unsourced)
    assert unsourced.status == "NOT_EVALUABLE"
    assert unsourced.component_sum_r is None


def test_elapsed_hold_keeps_weekend_wall_time_that_bar_count_deletes(monkeypatch):
    import src.costs as costs_api
    import src.research_infra.regime_spine.sweep as sweep

    entry = dt.datetime(2026, 6, 26, 20, tzinfo=UTC)  # Friday
    exit_ = dt.datetime(2026, 6, 29, 20, tzinfo=UTC)  # Monday
    assert elapsed_holding_hours(entry, exit_) == 72.0

    class Frame:
        symbol = "XAUUSD"
        bars = [SimpleNamespace(c=100.0) for _ in range(4)]
        atr = [1.0] * 4
        times_utc = [
            dt.datetime(2026, 6, 26, 16, tzinfo=UTC),
            dt.datetime(2026, 6, 26, 20, tzinfo=UTC),
            dt.datetime(2026, 6, 29, 12, tzinfo=UTC),
            dt.datetime(2026, 6, 29, 16, tzinfo=UTC),
        ]

        def __len__(self):
            return len(self.bars)

    seen = {}

    def fake_cost(symbol, account, hold, **kwargs):
        seen["hold"] = hold
        return SimpleNamespace(total_r=SimpleNamespace(value=0.0))

    monkeypatch.setattr(sweep, "fires", lambda frame, cond, params: [(0, {
        "stop_dist": 1.0, "target_dist": 1.0, "direction": 1,
    })])
    monkeypatch.setattr(sweep, "simulate_detail", lambda *a, **k: (1.0, 3))
    monkeypatch.setattr(costs_api, "cost_r", fake_cost)
    sweep.evaluate(
        {"canon": Frame()},
        SimpleNamespace(surface=["canon"], sleeve="probe"),
        costs=object(),
    )
    assert seen["hold"] == 72.0
    assert seen["hold"] != (3 - 0) * 4.0


def test_panel_propagates_component_classes_and_not_evaluable_counts():
    at = dt.datetime(2024, 5, 15, 12, tzinfo=UTC)
    trades = [
        TradeRecord("probe", "BTCUSD", at, at + dt.timedelta(hours=6), 1, 900.0, 9000.0, 1.0),
        TradeRecord("probe", "AVAUSD", at, at + dt.timedelta(hours=6), 1, 10.0, 100.0, 1.0),
    ]
    spec = OPTIONS["B_balanced"].with_(spread_band="mid")
    priced, coverage = price_trades(trades, spec)
    assert [row.status for row in priced] == ["priced", "unpriced"]
    assert set(priced[0].component_coverage or {}) == {
        "commission_r", "swap_r", "spread_r", "slippage_r"
    }
    counts = coverage["probe"].as_dict()["coverage_class_counts"]
    assert counts["NOT_EVALUABLE"] == 1
    assert sum(counts.values()) == 2
