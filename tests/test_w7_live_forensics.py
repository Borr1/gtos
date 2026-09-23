"""Behavioural tests for the Gate G1b forensics generators.

These assert INVARIANTS of the emitted artifact, not the presence of strings in the source. The
load-bearing one is the reconciliation: initial balance + Σ realized_net must reproduce each broker
account's closing balance exactly. If that holds, the row set cannot be silently dropping, duplicating
or misgrouping a deal — which is the whole basis for trusting every attribution number in
`GATE_G1B_RECEIPT.md`.

They skip when the VPS export tree is absent, so a fresh clone does not fail on missing evidence
(the ~177-failure environment delta of B39). A skip is reported, never a silent pass.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
EXPORT = Path("/Users/borr/GTOSActive/vps-export-20260725/extracted")
PACKETS = EXPORT / "05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz"

sys.path.insert(0, str(REPO))

pytestmark = pytest.mark.skipif(
    not (EXPORT / "09_mt5_api/ftmo_history_deals_get.jsonl").is_file(),
    reason="VPS export tree absent; G1b forensics needs the 2026-07-26 broker export",
)

# Broker-reported closing balances, from 09_mt5_api/{ftmo,redacted_account}_account_info.json.
EXPECTED_BALANCE = {"ftmo": 107879.56, "redacted_account": 96229.28}


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> tuple[list[dict], dict]:
    """Run the real generator into a scratch dir and return (rows, manifest)."""
    out = tmp_path_factory.mktemp("w7")
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/w7_live_forensics.py"), "--out-dir", str(out)],
        capture_output=True, text=True, cwd=str(REPO), timeout=600,
    )
    assert r.returncode == 0, f"generator failed:\n{r.stdout}\n{r.stderr}"
    rows = [json.loads(l) for l in (out / "LIVE_TRADE_ROWS.jsonl").read_text().splitlines() if l.strip()]
    manifest = json.loads((out / "LIVE_TRADE_ROWS_MANIFEST.json").read_text())
    return rows, manifest


def test_reconciles_to_broker_balance_exactly(built):
    """THE invariant. Residual must be 0.00 on both accounts, to the cent."""
    _, manifest = built
    for acct, expected in EXPECTED_BALANCE.items():
        recon = manifest["accounts"][acct]["reconciliation"]
        assert recon["broker_reported_balance"] == expected
        assert recon["reconstructed_balance"] == pytest.approx(expected, abs=0.005), (
            f"{acct}: initial + sum(realized_net) = {recon['reconstructed_balance']} "
            f"but the broker says {expected}"
        )
        assert abs(recon["residual"]) < 0.005, f"{acct} residual {recon['residual']}"


def test_eras_partition_every_position_and_every_dollar(built):
    """No position and no dollar may fall outside the era breakdown."""
    _, manifest = built
    for acct in EXPECTED_BALANCE:
        chk = manifest["accounts"][acct]["eras"]["_partition_check"]
        assert chk["n_positions_in_eras"] == chk["n_positions_total"]
        assert chk["sum_realized_net_in_eras"] == pytest.approx(
            chk["sum_realized_net_all_rows"], abs=0.02)
        assert abs(chk["residual"]) < 0.02


def test_no_deal_is_counted_twice_or_dropped(built):
    """Every trade deal appears in exactly one position's deal set."""
    rows, manifest = built
    for acct in EXPECTED_BALANCE:
        sub = [r for r in rows if r["account"] == acct]
        tickets: list[int] = []
        for r in sub:
            tickets.append(r["entry_deal_ticket"])
            tickets.extend(r["exit_deal_tickets"])
        assert len(tickets) == len(set(tickets)), f"{acct}: a deal ticket appears in two positions"
        assert len(tickets) == manifest["accounts"][acct]["reconciliation"]["n_deals_trade"], (
            f"{acct}: position model covers {len(tickets)} trade deals but the file has "
            f"{manifest['accounts'][acct]['reconciliation']['n_deals_trade']}"
        )


def test_sleeve_attribution_leaves_no_w7_position_unresolved(built):
    """Axis (a) closes: every W7 position resolves to a real sleeve in a real family."""
    rows, _ = built
    w7 = [r for r in rows if r["in_w7_denominator"]]
    assert w7, "no W7 positions found -- the probe is broken, not the window empty"
    families = {"core8", "candidate", "market_expansion"}
    for r in w7:
        assert r["sleeve_resolution"] in ("exact", "prefix_unique"), (
            f"position {r['position_id']} resolution {r['sleeve_resolution']}")
        assert r["sleeve_id"], f"position {r['position_id']} has no sleeve_id"
        assert r["sleeve_family"] in families, f"{r['sleeve_id']} -> {r['sleeve_family']}"
        # Cluster and confidence must resolve for EVERY family, not just core-8. Regression guard:
        # an earlier revision left 43% of the book in cluster "unknown".
        assert r["sleeve_cluster"], f"{r['sleeve_id']} has no cluster"
        assert r["sleeve_confidence"] is not None, f"{r['sleeve_id']} has no confidence"


def test_dial_comparison_uses_base_times_confidence(built):
    """Regression guard on the withdrawn claim.

    The designed unit risk must be base x sleeve_confidence, NOT the bare 2.00% base. A unit whose
    designed risk equals the base while its confidence is below 1.0 means the comparator regressed.
    """
    _, manifest = built
    for acct in EXPECTED_BALANCE:
        u = manifest["accounts"][acct]["unit_risk"]
        assert u["base_risk_per_unit_pct"] == pytest.approx(2.0)
        units = u["designed_vs_observed_units"]
        assert units, "no correlated units measured"
        for d in units:
            assert d["designed_unit_risk_pct"] == pytest.approx(
                u["base_risk_per_unit_pct"] * d["confidence"], abs=1e-6), (
                f"{d['sleeve']} {d['day']}: designed {d['designed_unit_risk_pct']} is not "
                f"2.00% x conf {d['confidence']}")
        # The window's highest-confidence sleeve was 0.40, so the 2.00% ceiling was unreachable.
        assert u["max_confidence_that_traded"] <= 1.0


def test_time_base_is_converted_not_relabelled(built):
    """Broker wall clock and UTC must differ by the resolved offset, and _broker must be naive."""
    rows, _ = built
    from datetime import datetime
    for r in rows[:80]:
        brk = datetime.fromisoformat(r["entry_time_broker"])
        assert brk.tzinfo is None, "the _broker field must be naive so attaching an offset is visible"
        utc = datetime.fromisoformat(r["entry_time_utc"])
        delta = (brk - utc.replace(tzinfo=None)).total_seconds() / 3600.0
        assert delta == pytest.approx(r["broker_clock_offset_hours"], abs=1e-6)
        assert r["broker_clock_rule"] == "new_york_plus_7"


def test_r_fields_are_consistent_and_gross_plus_cost_equals_net(built):
    """gross_r + cost_r == realized_r wherever R exists, so cost can never be read as slippage."""
    rows, _ = built
    checked = 0
    for r in rows:
        if r["realized_r"] is None:
            assert r["r_basis"] == "unavailable"
            continue
        assert r["gross_r"] is not None and r["cost_r"] is not None
        assert r["gross_r"] + r["cost_r"] == pytest.approx(r["realized_r"], abs=2e-4)
        checked += 1
    assert checked > 100, f"only {checked} rows carried R; expected most of 300"


def test_hand_closed_positions_are_flagged(built):
    """A human exit must be visibly separable from the sleeve's own result."""
    rows, manifest = built
    hand = [r for r in rows if r["in_w7_denominator"] and r["hand_closed"]]
    # Known: exactly one W7 position was closed from the phone, and it is worth more than the whole
    # kz_london_crypto_low sleeve. If this count changes, the DEAL_REASON map or the data changed.
    assert len(hand) == 1, [(r["position_id"], r["close_reasons_all"]) for r in hand]
    assert hand[0]["sleeve_id"] == "kz_london_crypto_low"
    assert "mobile" in hand[0]["close_reasons_all"]
    hi = manifest["accounts"]["ftmo"]["attribution"]["hand_intervention"]
    assert hi["n_hand_closed"] == 1
    sleeve = [g for g in manifest["accounts"]["ftmo"]["attribution"]["by_sleeve"]
              if g["key"] == "kz_london_crypto_low"][0]
    assert sleeve["realized_net"] - sleeve["hand_closed_net"] < 0, (
        "the sleeve must be negative once the hand exit is removed")


def test_manual_mobile_trades_are_excluded_from_the_w7_denominator(built):
    """The +13,166.69 pair are hand trades and must not inflate the book's result."""
    rows, _ = built
    mm = [r for r in rows if r["stack_era"] == "manual_mobile"]
    assert len(mm) == 3, [(r["account"], r["position_id"]) for r in mm]
    for r in mm:
        assert r["in_w7_denominator"] is False
        assert r["magic"] == 0
        assert r["open_reason"] == "mobile"
        assert r["comment_raw"] == ""
        assert r["sl_price"] is None, "a hand trade with a stop would break the identification"
    ftmo = [r for r in mm if r["account"] == "ftmo"]
    assert sum(r["realized_net"] for r in ftmo) == pytest.approx(13166.69, abs=0.02)


def test_deal_reason_enum_matches_mt5(built):
    """DEAL_REASON_EXPERT is 3. Getting 1/2/3 wrong relabels every EA close as a browser close."""
    from scripts.w7_live_forensics import DEAL_REASON
    assert DEAL_REASON[0] == "client"
    assert DEAL_REASON[1] == "mobile"
    assert DEAL_REASON[2] == "web"
    assert DEAL_REASON[3] == "expert"
    assert DEAL_REASON[4] == "sl"
    assert DEAL_REASON[5] == "tp"
    rows, _ = built
    w7 = [r for r in rows if r["in_w7_denominator"]]
    assert all(r["open_reason"] == "expert" for r in w7), (
        "every W7 book entry is placed by the EA; a non-expert open means the era split is wrong")


def test_w7_window_is_derived_from_data_not_hardcoded(built):
    """The window bounds must come from the data so a refreshed export cannot age them out."""
    rows, manifest = built
    w = manifest["w7_window_derived"]
    days = sorted({r["day_key_utc"] for r in rows if r["in_w7_denominator"]})
    assert w["first_entry_day_utc"] == days[0]
    assert w["last_entry_day_utc"] == days[-1]


@pytest.mark.skipif(not PACKETS.is_file(), reason="runtime-learning packet export absent")
def test_packet_lane_counts_only_real_skip_events(tmp_path):
    """Regression guard on the ~10x miscount that produced a wrong causal claim.

    `profile_missing_instrument_config` must be attributed ONLY from unit_skipped rows' own
    skip_reason -- never from the broker_unsupported_skips summary that rides on every packet.
    """
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts/w7_packet_forensics.py"), "--out-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=str(REPO), timeout=900,
    )
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    d = json.loads((tmp_path / "W7_PACKET_FORENSICS.json").read_text())

    missing = d["profile_missing_instrument_config"]["by_namespace"]
    total_missing = sum(missing.values())
    n_skipped = d["event_type_totals"]["unit_skipped"]
    assert total_missing <= n_skipped, (
        f"{total_missing} missing-config attributions exceed {n_skipped} unit_skipped rows -- the "
        "summary list is being counted again")

    # It is a redacted_account-only condition: those symbols exist on FTMO.
    assert set(missing) == {"redacted_account_live_bee34003"}, missing

    # The five high-confidence core sleeves placed nothing, and that is the receipt's headline.
    silent = {c["sleeve"] for c in d["core8_composition"] if not c["placed_anything"]}
    assert silent == {"metals_core", "crypto", "energy_agri", "metals_softband", "metals_ob_micro"}
    for c in d["core8_composition"]:
        if c["sleeve"] in silent:
            assert c["n_unit_admitted"] == 0 and c["n_unit_shadow"] == 0, (
                f"{c['sleeve']} generated candidates after all -- the silence claim is wrong")
    assert d["core8_confidence_weight"]["pct_that_placed"] == pytest.approx(11.54, abs=0.01)

    # spread_r is null on every row; if that ever changes, axis (c) gains a source.
    assert d["spread_r_field_presence"].get("value", 0) == 0

    # The governor asymmetry is axis (d)'s mechanism.
    assert d["governor_asymmetry"]["fn_over_ftmo"] > 1.0
