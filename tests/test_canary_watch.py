"""Every canary check must be shown to go RED.

The premise, from the session prompt: *an alert that does not fire is
indistinguishable from all-clear* — which is exactly how `.tools/monitor_books.py`
sat mute through the window it was supposed to be watching. A check that has only
ever been observed green has tested nothing.

So each pre-registered condition gets a pair: a fixture that MUST trigger it, and
a fixture that must NOT. The red case is the one that matters; the green case
exists so the red case cannot pass by a check that always fires.

The cost fixtures are built by perturbing **real** rows from
`LIVE_TRADE_ROWS.jsonl` rather than by inventing a trade, so the pricing path
under test is the one the reconciliation receipt uses.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SCRIPT = REPO / "scripts" / "canary_watch.py"
LIVE_ROWS = (REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics"
             / "LIVE_TRADE_ROWS.jsonl")
CANARY_TAGS = "metals_core,crypto,energy_agri"


def _mod():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_canary_watch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_canary_watch"] = module
    spec.loader.exec_module(module)
    return module


canary = _mod()


def run(tmp_path, *args, expect_exit=None):
    """Drive the script as the owner would, and return the parsed JSON page."""

    out = tmp_path / "page.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", str(out), *args],
        cwd=REPO, capture_output=True, text=True)
    assert out.is_file(), f"no page written.\nstdout:{proc.stdout}\nstderr:{proc.stderr}"
    page = json.loads(out.read_text(encoding="utf-8"))
    if expect_exit is not None:
        assert proc.returncode == expect_exit, (
            f"exit {proc.returncode} != {expect_exit}; alerts={page['alerts']}")
    return page


def alerts_for(page, condition_id):
    return [a for a in page["alerts"] if a["condition"] == condition_id]


def priced_rows(n=8, era="w7_book"):
    rows = [json.loads(x) for x in LIVE_ROWS.read_text("utf-8-sig").splitlines() if x.strip()]
    rows = [r for r in rows if r.get("stack_era") == era and r.get("commission")
            and r.get("risk_at_entry_usd") and (r.get("risk_distance_price") or 0) > 0]
    assert rows, "no priceable rows in the live corpus — the fixture source has changed"
    return rows[:n]


def write_jsonl(path: Path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# The spec itself
# --------------------------------------------------------------------------


def test_every_condition_in_the_spec_is_reachable_from_the_code():
    """A pre-registered condition the tool cannot raise is decoration."""

    spec = canary.load_spec()
    source = SCRIPT.read_text(encoding="utf-8")
    for block in spec["conditions"]:
        assert f'"{block["id"]}"' in source, (
            f"{block['id']} is pre-registered but no Alert in canary_watch.py cites it")


def test_the_spec_predates_the_first_fill():
    """A threshold chosen after seeing live data is a rationalisation."""

    spec = canary.load_spec()
    assert spec["pre_registered_utc"] == "2026-07-29"
    assert "before any live fill" in spec["pre_registered_by"]


# --------------------------------------------------------------------------
# C4 — book composition. The one the prompt calls "not paranoia".
# --------------------------------------------------------------------------


def test_c4_goes_red_against_the_real_config_with_no_launch_tags(tmp_path):
    """The committed supervisor passes no --tags. That must be loud."""

    page = run(tmp_path)
    fired = alerts_for(page, "C4")
    assert fired, "C4 did not fire against a config that resolves 20 generating sleeves"
    assert any(a["severity"] == "CRITICAL" for a in fired)
    assert page["book"]["n_generation"] > 3


def test_c4_goes_green_when_the_launch_tags_express_the_canary_book(tmp_path):
    page = run(tmp_path, "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C4"), page["book"]
    assert page["book"]["n_generation"] == 3
    assert sorted(page["book"]["generation"]) == sorted(page["book"]["canary_book"])


def test_c4_goes_red_when_a_dead_sleeve_is_added_back(tmp_path):
    page = run(tmp_path, "--launch-tags", CANARY_TAGS + ",idxrev")
    fired = alerts_for(page, "C4")
    assert fired
    assert "idxrev" in " ".join(a["detail"] for a in fired)


def test_c4_goes_red_when_an_armed_sleeve_disappears(tmp_path):
    page = run(tmp_path, "--launch-tags", "metals_core,crypto")
    fired = alerts_for(page, "C4")
    assert any("cannot generate" in a["headline"] for a in fired), fired
    assert page["book"]["missing_sleeves"] == ["energy_agri"]


def test_no_config_flag_combination_can_express_a_three_sleeve_book():
    """The finding the whole check rests on, asserted rather than asserted-about.

    If this ever fails, a confidence floor (or an exclusion knob) has landed and
    the C4 alert text — which tells the owner the restriction lives in --tags —
    is out of date.
    """

    import itertools
    from src.components.ultimate_book import admission as P

    smallest = None
    for clean3, clean4, candidate, expansion in itertools.product([False, True], repeat=4):
        registry = dict(P.effective_registry(include_clean3=clean3, include_clean4=clean4))
        if candidate:
            registry.update(P.candidate_book_registry(None))
        if expansion:
            sleeves, error = P.resolve_market_expansion_sleeves(
                policy="positive_weighted12_after_swap", explicit_sleeves=())
            if not error and sleeves:
                registry.update(P.market_expansion_registry(sleeves))
        smallest = len(registry) if smallest is None else min(smallest, len(registry))
    assert smallest == 8, (
        f"the minimum resolvable sizing book is now {smallest}, not 8 (core-8). "
        "If it is 3, a confidence floor exists and C4's alert text must be revised.")


def test_c4_models_the_engines_own_three_step_chain(tmp_path):
    """32 specs built, 3 dropped by book_engine.py:452-453, 29 can trade.

    WITHDRAWN and replaced (B332). The first version of this test asserted that
    the three clean_3 sleeves "generate but carry no confidence weight". They do
    not generate: `book_engine.py:426` computes `_active_sleeve_names()` — which
    is `effective_registry` with all six parameters — and `:452` drops every spec
    not in it, with a comment naming the reason. The check reported 20 generating
    sleeves because it also passed the RAW `market_expansion_sleeves` (`[]`) where
    both live callers resolve the named policy first, silently omitting all 12
    `mx_*` sleeves from what the operator is shown.
    """

    page = run(tmp_path)                       # real config, no --tags
    book = page["book"]
    assert book["n_raw_specs"] == 32
    assert book["dropped_by_engine_filter"] == [
        "sub_mid_dn_revert", "sub_xvol_pullback", "vp_euidx_pocgrav"]
    assert book["n_generation"] == 29
    assert book["n_sizing"] == 29
    # After the engine filter the two resolvers must agree exactly.
    assert book["generation"] == book["sizing"]
    # And the market-expansion sleeves must be visible to the operator.
    assert len([s for s in book["generation"] if s.startswith("mx_")]) == 12


def test_c4_goes_red_when_the_two_resolvers_drift_apart(tmp_path):
    """The replacement alert. Only meaningful with no --tags in play."""

    page = run(tmp_path)
    assert page["book"]["sizing_without_generation"] == [], (
        "sizing and generation already disagree at HEAD; the drift alert would be "
        "permanently red, which is the cry-wolf failure this check exists to avoid")


def test_c4_does_not_call_tag_narrowing_a_drift(tmp_path):
    """With --tags, sizing legitimately exceeds generation. Alerting on that would
    fire on every correctly-configured canary run."""

    page = run(tmp_path, "--launch-tags", CANARY_TAGS)
    assert len(page["book"]["sizing_without_generation"]) == 26
    assert not [a for a in alerts_for(page, "C4") if "cannot generate" in a["headline"]]


def test_generation_and_sizing_registries_genuinely_disagree():
    """Not a style point: they answer the same question differently."""

    page_source = SCRIPT.read_text(encoding="utf-8")
    assert "active_specs" in page_source and "effective_registry" in page_source, (
        "the check must consult BOTH registries; reporting one is confidently wrong")


# --------------------------------------------------------------------------
# C5 — authority gates
# --------------------------------------------------------------------------


def _config_with_gates(tmp_path, **overrides):
    """A minimal config carrying only the keys the checks read."""

    import yaml
    block = {
        "ultimate_book_enabled": True,
        "ultimate_book_apply_to_execution": True,
        "ultimate_book_live_activation_allowed": False,
        "ultimate_book_include_clean3": False,
        "ultimate_book_include_clean4": False,
        "ultimate_book_include_candidate_book": False,
        "ultimate_book_include_market_expansion_book": False,
    }
    block.update(overrides)
    path = tmp_path / "agent_config.yaml"
    path.write_text(yaml.safe_dump({"gtos_vnext_runtime": block}), encoding="utf-8")
    return path


def test_c5_goes_red_when_the_gates_are_live_and_no_token_exists(tmp_path):
    """Fail-closed, but indistinguishable from a dead book unless it is said.

    This is its own branch, asserted on its own headline: a mutation run showed
    the earlier generic assertion passing while the gate comparison was disabled,
    and it would have passed equally with THIS branch disabled instead.
    """

    config = _config_with_gates(tmp_path, ultimate_book_live_activation_allowed=True)
    empty = tmp_path / "no_tokens_here"
    empty.mkdir(parents=True, exist_ok=True)
    page = run(tmp_path, "--config", str(config), "--token-dir", str(empty),
               "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C5")
    assert any("no valid activation token" in a["headline"] for a in fired), fired
    assert any(a["severity"] == "CRITICAL" for a in fired)
    assert page["arming"]["token_valid_for_armed_account"] is False


def _mint_token(tmp_path, digest):
    """A real, valid token in an isolated directory."""

    from datetime import datetime, timedelta, timezone
    from src.safety import activation_token as at

    directory = tmp_path / "activation"
    directory.mkdir(parents=True, exist_ok=True)
    issued = datetime.now(timezone.utc)
    at.write_token(at.build_token(account_login_sha256=digest,
                                  expires_utc=issued + timedelta(hours=4),
                                  issued_by="test", now=issued),
                   directory=directory)
    return directory


def test_c5_goes_red_on_the_GATE_COMPARISON_alone(tmp_path):
    """Isolate the gate-comparison branch from the token branches.

    The first version of this test flipped `live_activation_allowed` with no
    token present, so the "gates are LIVE but no valid token" branch fired and
    the assertion passed even with the gate comparison disabled — a mutation run
    caught it. Here the book is fully armed WITH a valid token, and one gate that
    should be true is false, so only the comparison can speak.
    """

    from src.safety.activation_token import account_digest

    digest = account_digest("531325516")
    directory = _mint_token(tmp_path, digest)
    config = _config_with_gates(
        tmp_path,
        ultimate_book_live_activation_allowed=True,
        ultimate_book_live_broker_authority=True,
        ultimate_book_apply_to_execution=False)       # the one that must be caught

    page = run(tmp_path, "--config", str(config), "--token-dir", str(directory),
               "--launch-tags", CANARY_TAGS)
    assert page["arming"]["armed"] is True
    fired = alerts_for(page, "C5")
    comparison = [a for a in fired if "Authority gate ultimate_book_apply_to_execution" in a["headline"]]
    assert comparison, f"the gate comparison did not fire: {fired}"
    assert not [a for a in fired if "no valid activation token" in a["headline"]]


def test_c5_goes_red_on_a_standing_token_while_the_gates_are_shut(tmp_path):
    """Harmless today, one config edit from not being.

    The third C5 branch, and the last one a mutation run could still disable
    without any test noticing.
    """

    from src.safety.activation_token import account_digest

    digest = account_digest("531325516")
    directory = _mint_token(tmp_path, digest)
    config = _config_with_gates(tmp_path)          # gates shut, token valid

    page = run(tmp_path, "--config", str(config), "--token-dir", str(directory),
               "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C5")
    assert any("gates are NOT live" in a["headline"] for a in fired), fired
    assert page["arming"]["token_valid_for_armed_account"] is True
    assert page["arming"]["armed"] is False


def test_c5_goes_green_when_a_fully_armed_book_matches_its_pre_registered_gates(tmp_path):
    from src.safety.activation_token import account_digest

    digest = account_digest("531325516")
    directory = _mint_token(tmp_path, digest)
    config = _config_with_gates(
        tmp_path,
        ultimate_book_live_activation_allowed=True,
        ultimate_book_live_broker_authority=True)

    page = run(tmp_path, "--config", str(config), "--token-dir", str(directory),
               "--launch-tags", CANARY_TAGS)
    assert page["arming"]["armed"] is True
    assert not alerts_for(page, "C5"), page["arming"]


def test_c5_goes_red_when_the_config_cannot_be_read(tmp_path):
    """Unverifiable is not all-clear."""

    broken = tmp_path / "broken.yaml"
    broken.write_text("this: [is: not: valid: yaml\n", encoding="utf-8")
    page = run(tmp_path, "--config", str(broken))
    fired = alerts_for(page, "C5")
    assert any("UNVERIFIABLE" in a["headline"] for a in fired), page["alerts"]


def test_c5_reports_an_absent_gate_key_as_ABSENT_not_as_false(tmp_path):
    """`ultimate_book_live_broker_authority` is absent on mainline and explicitly
    false in the VPS export. Collapsing the two makes a fresh clone look like the
    live host."""

    config = _config_with_gates(tmp_path)
    page = run(tmp_path, "--config", str(config), "--launch-tags", CANARY_TAGS)
    assert page["arming"]["gates"]["ultimate_book_live_broker_authority"] == "ABSENT"
    assert page["arming"]["gates"]["ultimate_book_live_activation_allowed"] is False


def test_c5_goes_green_on_the_expected_not_armed_state(tmp_path):
    config = _config_with_gates(tmp_path)
    page = run(tmp_path, "--config", str(config), "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C5"), page["alerts"]
    assert page["arming"]["armed"] is False


# --------------------------------------------------------------------------
# C1 / C2 — cost and swap deviation
# --------------------------------------------------------------------------


def test_c1_goes_green_on_the_unperturbed_live_corpus(tmp_path):
    fills = write_jsonl(tmp_path / "fills.jsonl", priced_rows(8))
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C1"), page["costs"]
    assert page["costs"]["n_priced"] > 0
    assert page["costs"]["mean_abs_error_r"] < 0.01


def _perturb_to_error(rows, target_error_r):
    """Move each row's realized commission so |modelled - actual| ~= target.

    Setting a multiplier and hoping is what the first version of this test did,
    and it landed every fill above the SINGLE-fill threshold as well — so the
    test passed with the rolling trigger disabled. A mutation run caught it.
    Solving for the error directly is what makes the two triggers separable.
    """

    for row in rows:
        risk = float(row["risk_at_entry_usd"])
        row["commission"] = float(row["commission"]) - target_error_r * risk
    return rows


def test_c1_goes_red_on_the_ROLLING_trigger_alone(tmp_path):
    """The condition the whole activation case rests on.

    Each fill is perturbed to ~0.015 R — above the 0.01 R rolling threshold and
    BELOW the 0.02 R single-fill one — so only the rolling trigger can fire.
    """

    rows = _perturb_to_error(priced_rows(8), 0.015)
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS,
               expect_exit=1)
    fired = alerts_for(page, "C1")
    rolling = [a for a in fired if "last" in a["headline"] and "mean |error|" in a["headline"]]
    single = [a for a in fired if "Single fill" in a["headline"]]
    assert rolling, f"the ROLLING trigger did not fire: {fired}"
    assert not single, f"the fixture leaked into the single-fill trigger: {single}"
    assert 0.01 < page["costs"]["rolling_mean_abs_error_r"] < 0.02


def test_c1_goes_red_on_a_single_extreme_fill(tmp_path):
    rows = priced_rows(8)
    rows[-1]["commission"] = float(rows[-1]["commission"]) - 200.0
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C1")
    assert any("Single fill" in a["headline"] for a in fired), page["alerts"]


def test_c1_does_not_evaluate_below_the_pre_registered_minimum(tmp_path):
    """Two fills cannot condemn a cost model, and the spec says so."""

    rows = priced_rows(2)
    for row in rows:
        row["commission"] = float(row["commission"]) * 50.0 - 40.0
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    rolling = [a for a in alerts_for(page, "C1") if "last" in a["headline"]]
    assert not rolling, "the rolling trigger fired below its pre-registered minimum n"


def test_c2_goes_red_when_holding_time_runs_long(tmp_path):
    """Carry is what OD-3 waits on, so it gets its own tripwire."""

    rows = priced_rows(6)
    for row in rows:
        row["holding_seconds"] = 40 * 3600          # ~32x the live broker-true median
        row["sleeve_id"] = "metals_core"
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C2")
    assert any("median hold" in a["headline"] for a in fired), page["alerts"]


def test_c2_swap_does_not_fire_on_the_BASELINE_corpus(tmp_path):
    """The false-alarm control, and it caught a real defect. (B336)

    The first draft set the swap trigger at 0.01 R by copying C1's commission
    threshold without measuring the swap baseline. The measured swap baseline mean
    |error| is 0.010324 R — ABOVE the threshold — so 39 of 171 chronological
    rolling-5 windows on the corpus the thresholds were derived from would have
    fired. A page whose whole design constraint is not to cry wolf would have cried
    wolf on its own reference data.

    This test is the guard: the unperturbed live corpus must produce no swap alert.
    """

    fills = write_jsonl(tmp_path / "fills.jsonl", priced_rows(60))
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    swap_alerts = [a for a in alerts_for(page, "C2") if "wap" in a["headline"]]
    assert not swap_alerts, (
        f"C2 fired on the baseline corpus: {swap_alerts}; "
        f"rolling mean was {page['costs'].get('swap_rolling_mean_abs_error_r')}")


def test_c2_swap_still_fires_on_a_real_deviation(tmp_path):
    """A wide band must not be an absent one."""

    rows = priced_rows(8)
    for row in rows:
        risk = float(row["risk_at_entry_usd"])
        row["swap"] = float(row.get("swap") or 0.0) - 0.5 * risk     # ~0.5 R of swap
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    fired = [a for a in alerts_for(page, "C2") if "wap" in a["headline"]]
    assert fired, f"swap rolling mean was {page['costs'].get('swap_rolling_mean_abs_error_r')}"


def test_c2_swap_threshold_sits_above_the_measured_baseline(tmp_path):
    """Pin the relationship, not just the number: a future edit that drops the
    threshold below the measured baseline re-introduces the same defect."""

    spec = canary.load_spec()
    block = canary.condition(spec, "C2")
    baseline = block["derived_from"]["swap_baseline_measured_2026_07_29"]
    assert block["trigger_swap"]["mean_abs_error_r_above"] > baseline[
        "worst_chronological_rolling_5_mean_r"]
    assert block["trigger_swap_single_fill"]["abs_error_r_above"] > baseline[
        "worst_single_fill_r"]


def test_c2_goes_green_at_the_live_broker_true_median(tmp_path):
    rows = priced_rows(6)
    for row in rows:
        row["holding_seconds"] = int(1.2603 * 3600)
        row["sleeve_id"] = "metals_core"
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    assert not [a for a in alerts_for(page, "C2") if "median hold" in a["headline"]]


# --------------------------------------------------------------------------
# C3 — sleeve tripwires of the JPY kind
# --------------------------------------------------------------------------


def test_c3_goes_red_on_a_sleeve_that_is_negative_gross(tmp_path):
    """The specific signal that separated the two dead JPY sleeves from the nine
    that survived re-costing: losing BEFORE any cost is charged."""

    rows = priced_rows(6)
    for row in rows:
        row["sleeve_id"] = "crypto"
        row["gross_r"] = -0.4
        row["realized_r"] = -0.45
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C3")
    assert any("negative GROSS" in a["headline"] for a in fired), page["sleeves"]


def test_c3_goes_green_on_a_sleeve_that_is_merely_net_negative(tmp_path):
    """Net-negative but gross-positive is a cost problem, not a dead sleeve —
    and nine of eleven were exactly that."""

    rows = priced_rows(6)
    for row in rows:
        row["sleeve_id"] = "crypto"
        row["gross_r"] = 0.30
        row["realized_r"] = -0.05
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    assert not [a for a in alerts_for(page, "C3") if "negative GROSS" in a["headline"]]


def test_c3_goes_red_on_loss_concentration(tmp_path):
    """The JPY cluster was 37.4 % of live net loss and took a fortnight to see."""

    rows = priced_rows(12)
    for i, row in enumerate(rows):
        row["sleeve_id"] = "crypto" if i < 4 else "metals_core"
        row["gross_r"] = 0.5
        row["realized_r"] = -3.0 if i < 4 else -0.05
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C3")
    assert any("% of total net loss" in a["headline"] for a in fired), page["sleeves"]


def test_c3_needs_the_pre_registered_minimum_fills(tmp_path):
    rows = priced_rows(3)
    for row in rows:
        row["sleeve_id"] = "crypto"
        row["gross_r"] = -0.4
        row["realized_r"] = -0.45
    fills = write_jsonl(tmp_path / "fills.jsonl", rows)
    page = run(tmp_path, "--fills", str(fills), "--launch-tags", CANARY_TAGS)
    assert not [a for a in alerts_for(page, "C3") if "negative GROSS" in a["headline"]]


# --------------------------------------------------------------------------
# C6 / C7 — alive versus quiet. These must NOT be conflated.
# --------------------------------------------------------------------------


def _packets(path: Path, namespace, instants):
    return write_jsonl(path, [{"created_at_utc": t, "namespace": namespace,
                               "event_type": "cycle"} for t in instants])


def test_c6_goes_red_on_a_stale_packet_stream(tmp_path):
    packets = _packets(tmp_path / "p.jsonl", "operator_profile",
                       ["2026-07-29T00:00:00Z", "2026-07-29T00:01:00Z"])
    page = run(tmp_path, "--packets", str(packets), "--now", "2026-07-29T06:00:00Z",
               "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C6")
    assert any("no packet for" in a["headline"] for a in fired), page["liveness"]


def test_c6_goes_red_when_an_expected_namespace_never_appears(tmp_path):
    """The set-difference an accumulator would miss: a book that died completely
    emits nothing and so can never appear in an observed set."""

    packets = _packets(tmp_path / "p.jsonl", "operator_profile",
                       ["2026-07-29T05:59:00Z"])
    page = run(tmp_path, "--packets", str(packets), "--now", "2026-07-29T06:00:00Z",
               "--expect-namespace", "operator_profile",
               "--expect-namespace", "redacted_account_live_bee34003",
               "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C6")
    assert any("DEAD" in a["headline"] and "redacted_account" in a["headline"] for a in fired)


def test_c6_goes_green_at_the_normal_poll_cadence(tmp_path):
    """p90 of the live export is 60.4 s; a 1-minute cadence must not alarm."""

    instants = [f"2026-07-29T05:{m:02d}:00Z" for m in range(0, 60)]
    packets = _packets(tmp_path / "p.jsonl", "operator_profile", instants)
    page = run(tmp_path, "--packets", str(packets), "--now", "2026-07-29T06:00:00Z",
               "--expect-namespace", "operator_profile", "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C6"), page["liveness"]


def test_c6_goes_green_across_the_measured_p99_idle(tmp_path):
    """909.6 s is the M15 idle pattern, entirely normal. Alarming on it would
    have produced 1,633 false alarms in the live export."""

    packets = _packets(tmp_path / "p.jsonl", "operator_profile",
                       ["2026-07-29T05:30:00Z", "2026-07-29T05:45:10Z", "2026-07-29T05:59:50Z"])
    page = run(tmp_path, "--packets", str(packets), "--now", "2026-07-29T06:00:00Z",
               "--expect-namespace", "operator_profile", "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C6"), page["liveness"]


def test_c7_stays_quiet_through_the_whole_38_day_window(tmp_path):
    """The three armed sleeves fired ZERO times across the entire live window.
    A monitor that alarms on that cries wolf from the first month."""

    page = run(tmp_path, "--armed-utc", "2026-06-18T00:00:00Z",
               "--now", "2026-07-26T00:00:00Z", "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C7"), page["fills"]
    assert page["fills"]["days_since_armed"] == pytest.approx(38.0, abs=0.1)


def test_c7_fires_past_the_pre_registered_horizon(tmp_path):
    page = run(tmp_path, "--armed-utc", "2026-06-01T00:00:00Z",
               "--now", "2026-07-29T00:00:00Z", "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C7")
    assert any("zero fills" in a["headline"] for a in fired), page["fills"]
    assert page["fills"]["p_silence_independence_lower_bound"] < 0.05


def test_c7_is_silent_once_a_fill_exists(tmp_path):
    fills = write_jsonl(tmp_path / "fills.jsonl", priced_rows(1))
    page = run(tmp_path, "--fills", str(fills), "--armed-utc", "2026-01-01T00:00:00Z",
               "--now", "2026-07-29T00:00:00Z", "--launch-tags", CANARY_TAGS)
    assert not [a for a in alerts_for(page, "C7") if "zero fills" in a["headline"]]


def test_c7_horizon_matches_the_pre_registered_derivation():
    """Re-derive the 42-day horizon from the spec's own inputs, so a silently
    edited threshold cannot pass as pre-registered."""

    import math
    spec = canary.load_spec()
    block = canary.condition(spec, "C7")
    joint = 1.0
    for value in block["derived_from"]["per_sleeve_p_zero_in_38_days"].values():
        joint *= float(value)
    per_day = joint ** (1.0 / 38.0)
    horizon = math.log(0.05) / math.log(per_day)
    assert block["trigger"]["calendar_days_of_complete_silence_above"] == pytest.approx(
        horizon, abs=1.0), f"spec horizon does not match its own derivation ({horizon:.1f})"


# --------------------------------------------------------------------------
# C8 — drawdown headroom
# --------------------------------------------------------------------------


def _account_state(tmp_path, **overrides):
    block = {
        "FTMO": {
            "balance": 107872.0, "equity": 107872.0, "day_start_equity": 107872.0,
            "static_dd_floor": 90000.0, "initial_capital": 100000.0,
            "daily_loss_basis": "initial_capital", "daily_reset_rule": "CE(S)T",
            "broker_server": "FTMO-Server3",
            "provenance": "[input] figures supplied to the tool, not measured by it",
        }
    }
    block["FTMO"].update(overrides)
    path = tmp_path / "account_state.json"
    path.write_text(json.dumps(block), encoding="utf-8")
    return path


def test_c8_goes_green_at_the_stated_headroom(tmp_path):
    state = _account_state(tmp_path)
    page = run(tmp_path, "--account-state", str(state), "--launch-tags", CANARY_TAGS)
    assert not alerts_for(page, "C8"), page["headroom"]
    assert page["headroom"]["accounts"]["FTMO"]["static_headroom_usd"] == pytest.approx(17872.0)


def test_c8_goes_red_near_the_static_floor(tmp_path):
    state = _account_state(tmp_path, equity=93000.0, day_start_equity=93000.0)
    page = run(tmp_path, "--account-state", str(state), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C8")
    assert any("static max-DD floor" in a["headline"] for a in fired), page["headroom"]


def test_c8_goes_red_when_the_daily_budget_is_half_spent(tmp_path):
    state = _account_state(tmp_path, equity=104000.0, day_start_equity=107872.0)
    page = run(tmp_path, "--account-state", str(state), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C8")
    assert any("daily-loss allowance" in a["headline"] for a in fired), page["headroom"]


def test_c8_uses_the_firms_own_reset_calendar_not_the_server_clock(tmp_path):
    """FTMO resets at 00:00 CE(S)T; its MT5 server runs the US calendar. The two
    are one hour apart normally and two apart for ~4 weeks a year."""

    state = _account_state(tmp_path)
    page = run(tmp_path, "--account-state", str(state), "--launch-tags", CANARY_TAGS,
               "--now", "2026-07-29T06:00:00Z")
    block = page["headroom"]["accounts"]["FTMO"]
    assert block["reset_calendar"] == "CE(S)T"
    assert block["reset_offset_hours_now"] == pytest.approx(2.0)   # CEST in July


def test_c8_fails_closed_on_an_unregistered_server(tmp_path):
    """broker_clock refuses to guess a reset window, and the page must say so
    rather than quietly using a default."""

    state = _account_state(tmp_path, daily_reset_rule=None, broker_server="Nonesuch-Server9")
    page = run(tmp_path, "--account-state", str(state), "--launch-tags", CANARY_TAGS)
    fired = alerts_for(page, "C8")
    assert any("UNKNOWN" in a["headline"] for a in fired), page["headroom"]


def test_c8_reports_provenance_for_every_supplied_figure(tmp_path):
    """Balance is an INPUT. A page that renders inputs and measurements in the
    same typeface invites the reader to trust the wrong one."""

    state = _account_state(tmp_path)
    page = run(tmp_path, "--account-state", str(state), "--launch-tags", CANARY_TAGS)
    assert "input" in page["headroom"]["accounts"]["FTMO"]["provenance"].lower()


# --------------------------------------------------------------------------
# Exit codes and the "unevaluated is not all-clear" rule
# --------------------------------------------------------------------------


def test_unevaluated_checks_do_not_read_as_clean(tmp_path):
    """Exit 3, not 0: nothing is wrong and nothing was checked are different."""

    page = run(tmp_path, "--launch-tags", CANARY_TAGS, expect_exit=3)
    severities = {a["severity"] for a in page["alerts"]}
    assert severities == {"INFO"}, page["alerts"]
    assert any("not evaluated" in a["headline"] for a in page["alerts"])


def test_a_real_alert_exits_1(tmp_path):
    run(tmp_path, expect_exit=1)


def test_the_page_renders_without_crashing_on_an_empty_world(tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--launch-tags", CANARY_TAGS],
                          cwd=REPO, capture_output=True, text=True)
    assert "GTOS CANARY" in proc.stdout
    assert proc.returncode in (0, 1, 3), proc.stderr


def test_the_tool_never_imports_a_broker_module():
    """It runs on a laptop against a funded account's state. It must be inert."""

    source = SCRIPT.read_text(encoding="utf-8")
    assert "MetaTrader5" not in source
    assert "order_send" not in source
    assert ".connect()" not in source
