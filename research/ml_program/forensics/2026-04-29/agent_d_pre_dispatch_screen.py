"""Agent D — Pre-dispatch substrate compatibility screen.

Reusable Python module + CLI for screening literature methods and ML hypotheses
for compatibility with the GTOS MT5 retail broker tick stream.

Background
----------
Two literature transplants (K-4 Stoikov micro-price; B-1 K54 v3 W-unit pooling)
failed because of MT5 retail substrate constraints (`volume=0` and `last=0` on
100% of tick rows across all 7 GTOS instruments). This module formalizes the
substrate compatibility check so future dispatches do not repeat that class
of failure.

Substrate baseline (verified 2026-04-29 across ~3.5M ticks)
-----------------------------------------------------------
- `volume=0` on 100% of tick rows.
- `last=0` on 100% of tick rows.
- Broker BUY/SELL flags absent (0/13,140 in original probe).
- LOB depth not surfaced (FN does not publish BookEvents).
- Available: bid, ask, ts_msc, mid (derived), spread (derived),
  inferred_aggressor (tick test on mid changes — Roll-bounce regime).

Required-input vocabulary
-------------------------
The screening function expects an iterable of input keys per hypothesis. The
vocabulary is fixed (see SUBSTRATE_OK / SUBSTRATE_PARTIAL / SUBSTRATE_FAIL
sets below) so that a hypothesis spec can be classified deterministically.

Usage
-----
::

    >>> from agent_d_pre_dispatch_screen import screen_hypothesis
    >>> spec = {
    ...     'id': 'K-4',
    ...     'name': 'Stoikov micro-price',
    ...     'required_inputs': ['bid_ask_queue_volumes'],
    ... }
    >>> result = screen_hypothesis(spec)
    >>> result['verdict']
    'FAIL'
    >>> result['paid_feed_required']
    'Databento CME L2'
    >>> result['monthly_cost_usd']
    179

CLI:

::

    python agent_d_pre_dispatch_screen.py --backlog research/ml_program/MASTER_BACKLOG.md
    python agent_d_pre_dispatch_screen.py --hypothesis K-4 --inputs bid_ask_queue_volumes
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Substrate compatibility vocabulary
# ---------------------------------------------------------------------------

# Inputs that are FREELY AVAILABLE on MT5 retail or via free public feeds.
# These produce a PASS verdict.
SUBSTRATE_OK: frozenset[str] = frozenset({
    # OHLCV from MT5 (any timeframe)
    'ohlcv_m1', 'ohlcv_m5', 'ohlcv_m15', 'ohlcv_h1', 'ohlcv_h4', 'ohlcv_d1',
    # Trade history (existing trades_unified.csv + _trade_index.json)
    'trade_history', 'trade_outcomes', 'realized_r_per_trade',
    # MT5 quote stream (bid/ask/spread/mid)
    'mt5_bid_ask', 'mt5_spread', 'mt5_mid',
    'inferred_aggressor',  # tick test only; broker-dependent accuracy
    # Calendar / time-of-day
    'calendar', 'kill_zone_clock', 'timezone', 'trading_hours',
    # Free public feeds
    'fred', 'cftc_cot', 'wgc', 'bis_public',
    'cboe_vix_free', 'cboe_gex_free', 'lba_fix_public',
    # Existing GTOS internals
    'regime_label_v1', 'regime_label_v2', 'h4_swing_data',
    'ob_candidate_list', 'fvg_candidate_list', 'breaker_candidate_list',
    'h1_setup_data', 'mso_market_state',
    'ai_outputs', 'model_outputs', 'cpcv_paths',
    'shadow_logs', 'production_logs',
    'round_number_table', 'rolling_RV', 'fix_windows',
    # Methodology
    'statistical_methodology', 'features',
    'cell_groupings', 'side_history', 'production_perf', 'trial_log',
    # Tools / prompts
    'prompts', 'tools', 'market_state',
    # Tracked dependencies
    'TED', 'FRA-OIS', 'DXY', 'VIX', 'GVZ', 'VIX1D-VIX9D',
    'intermediary_capital', 'sentiment_baker_wurgler',
    # Misc
    'broker_audit', 'internal', 'operator', 'research', 'research_only',
    'recovered_template', 'gates', 'executions', 'api_responses',
    'cpcv_path9_composition', 'tick_data',  # tick_data here = bid/ask only
    'broker_history_depth',  # OHLCV depth check, not tick depth
    'monte_carlo_outputs', 'FN_constraint',
    'component3b', 'news',
    'lba_public', 'BoE',
})

# Inputs where a degraded substitute exists. Mechanism preserved at <50%
# fidelity. Pre-register lift haircut ≥40%. Verdict = PARTIAL.
SUBSTRATE_PARTIAL: frozenset[str] = frozenset({
    'tick_count_imbalance',          # substitute for trade-count imbalance
    'rolling_quote_imbalance',       # substitute for OFI
    'inferred_aggressor_aggregated', # substitute for trade direction
    'spread_conditional_volatility', # substitute for V-shape latent liquidity
    'tick_data_quote_only',          # substitute for full tick-and-trade
    'spot_fx_aggregated_lob',        # Hotspot/EBS-aggregated; not full depth
    'free_cboe_gex_dashboard_scrape',  # FlashAlpha/GEX-Metrix HTML
})

# Inputs that REQUIRE A PAID LOB FEED. Verdict = FAIL on MT5 retail.
SUBSTRATE_FAIL: frozenset[str] = frozenset({
    'lob_depth_l2',
    'lob_depth_l3',
    'real_trade_volume',
    'real_trade_volume_dollars',
    'real_trade_aggressor_ground_truth',
    'real_trade_count',
    'tick_direction_authoritative',
    'multi_level_ofi',
    'tick_book_events',
    'mt5_book_events',
    'cme_glbx_mdp3',
    'cme_futures_l2',
    'real_trade_flow',
    'order_book_imbalance_at_level',
    'bid_ask_queue_volumes',  # K-4 Stoikov
    'real_dollar_volume_per_trade',  # K-5 Kyle-Obizhaeva
    'order_book_full_book',
})

# Mapping from FAIL inputs → recommended paid feed
PAID_FEED_MAP: dict[str, dict] = {
    'lob_depth_l2': {'feed': 'Databento CME L2 (MBP-10)', 'monthly_cost_usd': 179},
    'lob_depth_l3': {'feed': 'Databento CME L3 (MBO)', 'monthly_cost_usd': 179},
    'real_trade_volume': {'feed': 'Databento CME L1 trades', 'monthly_cost_usd': 179},
    'real_trade_volume_dollars': {'feed': 'Databento CME L1 trades', 'monthly_cost_usd': 179},
    'real_trade_aggressor_ground_truth': {'feed': 'Databento CME L2 (MBP-10)', 'monthly_cost_usd': 179},
    'real_trade_count': {'feed': 'Databento CME L1 trades', 'monthly_cost_usd': 179},
    'tick_direction_authoritative': {'feed': 'Databento CME L2', 'monthly_cost_usd': 179},
    'multi_level_ofi': {'feed': 'Databento CME L2 (MBP-10)', 'monthly_cost_usd': 179},
    'tick_book_events': {'feed': 'Databento CME L3 (MBO)', 'monthly_cost_usd': 179},
    'mt5_book_events': {'feed': 'FN Level-2 add-on (inquire)', 'monthly_cost_usd': None},
    'cme_glbx_mdp3': {'feed': 'Databento CME GLBX.MDP3', 'monthly_cost_usd': 179},
    'cme_futures_l2': {'feed': 'Databento CME L2', 'monthly_cost_usd': 179},
    'real_trade_flow': {'feed': 'Databento CME L1 trades + L2', 'monthly_cost_usd': 179},
    'order_book_imbalance_at_level': {'feed': 'Databento CME L2', 'monthly_cost_usd': 179},
    'bid_ask_queue_volumes': {'feed': 'Databento CME L2', 'monthly_cost_usd': 179},
    'real_dollar_volume_per_trade': {'feed': 'Databento CME L1 trades', 'monthly_cost_usd': 179},
    'order_book_full_book': {'feed': 'Databento CME L3', 'monthly_cost_usd': 179},
}

# Substitution viability map: degraded substitute description per PARTIAL input
PARTIAL_SUBSTITUTION_MAP: dict[str, str] = {
    'tick_count_imbalance': (
        'Glattfelder-Dupuis-Olsen 2011 tick-count-time bars; substrate-OK '
        'but mechanism-degraded vs published trade-count-time'
    ),
    'rolling_quote_imbalance': (
        'rolling sum of inferred_aggressor over quote stream; collapses to '
        'mid-momentum proxy under Roll-bid-ask-bounce regime'
    ),
    'inferred_aggressor_aggregated': (
        'tick-test on mid changes; broker-dependent accuracy 60-80%'
    ),
    'spread_conditional_volatility': (
        'realized-vol response conditioned on spread bins; substitute for '
        'V-shape latent liquidity (Toth-Bouchaud)'
    ),
    'tick_data_quote_only': (
        'bid/ask quote stream only; useful for L1-derived features but '
        'cannot replicate trade-flow-aware methods'
    ),
    'spot_fx_aggregated_lob': (
        'Databento aggregated LOB (Hotspot/EBS) — narrower than CME futures '
        'spot-FX LOB; not faithful to MT5 broker quotes'
    ),
    'free_cboe_gex_dashboard_scrape': (
        'FlashAlpha or GEX-Metrix HTML scrape; rate-limited; aggregated '
        'dealer-gamma; sufficient for K54 features'
    ),
}


# ---------------------------------------------------------------------------
# Verdict / classification
# ---------------------------------------------------------------------------

@dataclass
class ScreeningResult:
    """Result of a substrate compatibility screen."""

    verdict: str  # 'PASS', 'PARTIAL', 'FAIL'
    inputs_ok: list[str] = field(default_factory=list)
    inputs_partial: list[str] = field(default_factory=list)
    inputs_fail: list[str] = field(default_factory=list)
    inputs_unknown: list[str] = field(default_factory=list)
    reason: str = ''
    alternative_substrate: Optional[str] = None
    paid_feed_required: Optional[str] = None
    monthly_cost_usd: Optional[int] = None

    def to_dict(self) -> dict:
        """Serialize as plain dict (e.g. for JSON output)."""
        return {
            'verdict': self.verdict,
            'inputs_ok': sorted(self.inputs_ok),
            'inputs_partial': sorted(self.inputs_partial),
            'inputs_fail': sorted(self.inputs_fail),
            'inputs_unknown': sorted(self.inputs_unknown),
            'reason': self.reason,
            'alternative_substrate': self.alternative_substrate,
            'paid_feed_required': self.paid_feed_required,
            'monthly_cost_usd': self.monthly_cost_usd,
        }


def classify_input(input_key: str) -> str:
    """Classify a single input key as 'OK', 'PARTIAL', 'FAIL', or 'UNKNOWN'."""
    key = input_key.strip()
    if key in SUBSTRATE_FAIL:
        return 'FAIL'
    if key in SUBSTRATE_PARTIAL:
        return 'PARTIAL'
    if key in SUBSTRATE_OK:
        return 'OK'
    # Defensive fallback: unknown inputs are 'UNKNOWN'. Caller must classify
    # explicitly before dispatch.
    return 'UNKNOWN'


def screen_hypothesis(spec: dict) -> ScreeningResult:
    """Screen a hypothesis spec for MT5 retail substrate compatibility.

    Parameters
    ----------
    spec : dict
        Hypothesis specification. Required keys:
          - 'id': string identifier (e.g. 'K-4', 'H-1')
          - 'name': human-readable name
          - 'required_inputs': iterable of input keys (vocabulary above)

    Returns
    -------
    ScreeningResult

    Verdict logic
    -------------
    - PASS: all inputs in SUBSTRATE_OK.
    - PARTIAL: at least one input in SUBSTRATE_PARTIAL; rest in OK.
    - FAIL: at least one input in SUBSTRATE_FAIL.
    - PARTIAL with caveat: any UNKNOWN inputs flag for manual review.
    """
    required = list(spec.get('required_inputs', []) or [])
    if not required:
        return ScreeningResult(
            verdict='UNKNOWN',
            reason='No required_inputs specified — cannot screen.',
        )

    ok: list[str] = []
    partial: list[str] = []
    fail: list[str] = []
    unknown: list[str] = []

    for inp in required:
        cls = classify_input(inp)
        if cls == 'OK':
            ok.append(inp)
        elif cls == 'PARTIAL':
            partial.append(inp)
        elif cls == 'FAIL':
            fail.append(inp)
        else:
            unknown.append(inp)

    # Verdict precedence: FAIL > PARTIAL > UNKNOWN > PASS.
    if fail:
        verdict = 'FAIL'
        # Take the cheapest paid feed across all FAIL inputs.
        feed_options = [PAID_FEED_MAP[f] for f in fail if f in PAID_FEED_MAP]
        if feed_options:
            costs = [
                opt['monthly_cost_usd'] for opt in feed_options
                if opt['monthly_cost_usd'] is not None
            ]
            cheapest_cost = min(costs) if costs else None
            cheapest_feed = next(
                (opt['feed'] for opt in feed_options
                 if opt.get('monthly_cost_usd') == cheapest_cost),
                feed_options[0]['feed']
            )
        else:
            cheapest_cost = None
            cheapest_feed = 'Paid LOB feed required (vendor TBD)'

        reason = (
            f'Hypothesis requires {len(fail)} FAIL input(s) absent on MT5 '
            f'retail substrate: {fail}. Substrate is L1-quote-only with '
            f'volume=0 and last=0 on 100% of tick rows.'
        )
        return ScreeningResult(
            verdict=verdict,
            inputs_ok=ok,
            inputs_partial=partial,
            inputs_fail=fail,
            inputs_unknown=unknown,
            reason=reason,
            paid_feed_required=cheapest_feed,
            monthly_cost_usd=cheapest_cost,
        )

    if partial:
        # Build alternative-substrate description summary.
        substitutions = [
            f'{inp}: {PARTIAL_SUBSTITUTION_MAP.get(inp, "see audit doc")}'
            for inp in partial
        ]
        alt = '; '.join(substitutions)
        reason = (
            f'Hypothesis requires {len(partial)} PARTIAL input(s); '
            f'degraded substitute exists. Pre-register a lift haircut '
            f'>=40% versus published claim.'
        )
        return ScreeningResult(
            verdict='PARTIAL',
            inputs_ok=ok,
            inputs_partial=partial,
            inputs_fail=fail,
            inputs_unknown=unknown,
            reason=reason,
            alternative_substrate=alt,
        )

    if unknown:
        return ScreeningResult(
            verdict='UNKNOWN',
            inputs_ok=ok,
            inputs_partial=partial,
            inputs_fail=fail,
            inputs_unknown=unknown,
            reason=(
                f'Hypothesis has {len(unknown)} unrecognized input(s): '
                f'{unknown}. Manual review required before dispatch.'
            ),
        )

    return ScreeningResult(
        verdict='PASS',
        inputs_ok=ok,
        inputs_partial=partial,
        inputs_fail=fail,
        inputs_unknown=unknown,
        reason=(
            f'All {len(ok)} input(s) substrate-OK. No paid feed required. '
            f'Hypothesis is dispatchable on existing MT5 retail substrate.'
        ),
    )


# ---------------------------------------------------------------------------
# Batch / CLI
# ---------------------------------------------------------------------------

def screen_batch(specs: Iterable[dict]) -> list[dict]:
    """Screen a batch of hypothesis specs. Returns list of result dicts.

    Each result includes the spec id/name plus the screening verdict.
    """
    results: list[dict] = []
    for spec in specs:
        res = screen_hypothesis(spec).to_dict()
        res['id'] = spec.get('id', '?')
        res['name'] = spec.get('name', '?')
        results.append(res)
    return results


def _load_specs_from_csv(path: str) -> list[dict]:
    """Load hypothesis specs from agent_d_substrate_matrix.csv format.

    The CSV's `required_inputs` column may contain multiple semicolon-
    separated keys; this loader splits them.
    """
    import csv
    specs: list[dict] = []
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_inputs = row.get('required_inputs', '')
            inputs = [
                tok.strip()
                for tok in raw_inputs.replace(',', ';').split(';')
                if tok.strip()
            ]
            specs.append({
                'id': row.get('item_id', '?'),
                'name': row.get('name', '?'),
                'required_inputs': inputs,
            })
    return specs


def _print_summary(results: list[dict]) -> None:
    """Pretty-print a batch screening summary."""
    counts = {'PASS': 0, 'PARTIAL': 0, 'FAIL': 0, 'UNKNOWN': 0}
    for r in results:
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1
    total = len(results)
    print(f'Screened {total} items:')
    for v, c in counts.items():
        pct = (100 * c / total) if total else 0
        print(f'  {v}: {c} ({pct:.1f}%)')
    print()
    fails = [r for r in results if r['verdict'] == 'FAIL']
    if fails:
        print(f'FAIL items ({len(fails)}):')
        for r in fails:
            print(
                f"  {r['id']}: {r['name']}  ->  paid feed: "
                f"{r.get('paid_feed_required', '?')} (${r.get('monthly_cost_usd', '?')}/mo)"
            )
        print()
    partials = [r for r in results if r['verdict'] == 'PARTIAL']
    if partials:
        print(f'PARTIAL items ({len(partials)}) — degraded substitute available; pre-register lift haircut >=40%.')
        for r in partials[:10]:
            print(f"  {r['id']}: {r['name']}")
        if len(partials) > 10:
            print(f'  ... and {len(partials) - 10} more')


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Examples::

        python agent_d_pre_dispatch_screen.py --csv research/ml_program/forensics/2026-04-29/agent_d_substrate_matrix.csv
        python agent_d_pre_dispatch_screen.py --hypothesis K-4 --inputs bid_ask_queue_volumes
    """
    parser = argparse.ArgumentParser(
        description='Substrate-compatibility pre-dispatch screen for GTOS ML hypotheses'
    )
    parser.add_argument('--csv', help='Path to substrate matrix CSV (batch mode)')
    parser.add_argument('--hypothesis', help='Single hypothesis ID (single mode)')
    parser.add_argument(
        '--inputs',
        nargs='+',
        help='Required inputs for single-hypothesis mode',
    )
    parser.add_argument('--name', default='ad-hoc', help='Hypothesis name (single mode)')
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit JSON output instead of pretty summary',
    )
    args = parser.parse_args(argv)

    if args.csv:
        specs = _load_specs_from_csv(args.csv)
        results = screen_batch(specs)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            _print_summary(results)
        return 0

    if args.hypothesis:
        if not args.inputs:
            print('ERROR: --inputs required when --hypothesis is given', file=sys.stderr)
            return 2
        spec = {
            'id': args.hypothesis,
            'name': args.name,
            'required_inputs': args.inputs,
        }
        res = screen_hypothesis(spec).to_dict()
        res['id'] = spec['id']
        res['name'] = spec['name']
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Screening result for {res['id']} ({res['name']}):")
            print(f"  Verdict: {res['verdict']}")
            print(f"  Reason: {res['reason']}")
            if res.get('paid_feed_required'):
                print(f"  Paid feed: {res['paid_feed_required']} (${res.get('monthly_cost_usd')}/mo)")
            if res.get('alternative_substrate'):
                print(f"  Alternative substrate: {res['alternative_substrate']}")
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
