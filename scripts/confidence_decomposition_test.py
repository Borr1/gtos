#!/usr/bin/env python3
"""
Confidence Decomposition Test — Score 5 real MSOs through a 2-dimension rubric.
Each MSO scored TWICE for consistency checking.
"""

import json
import time
from pathlib import Path

import anthropic

BATCH_DIR = Path("knowledge_base_backtest/batch_api")
PRIMARY = "msgbatch_01WUZbzFQniomk49SoLRAsPg"
OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_31/generated/confidence_decomposition")
OUTPUT = OUTPUT_DIR / "decomposition_real_mso_test.md"
RAW_OUTPUT = OUTPUT_DIR / "decomposition_raw_results.json"

SCORING_PROMPT = """You are a setup quality scorer. Rate this trading setup on two independent dimensions.

STRUCTURAL (zone quality): 1-5
  5 = Impulse 1-3 candles, creates FVG, retracement 85-95%, OB from BOS event
  4 = Impulse 4-5 candles OR impulse creates FVG (add +1, cap at 5), retracement 70-90%
  3 = Impulse 6-7 candles, no FVG, adequate retracement (60-85%)
  2 = Impulse 8+ candles, no FVG, shallow (<60%) or excessive (>95%) retracement
  1 = Gradual move, no clear impulse, zone boundaries unclear

CONTEXTUAL (environment): 1-5
  5 = Align score 4/4, with-trend, early in kill zone, no nearby opposing zones
  4 = Align score 3/4, with-trend, good kill zone timing
  3 = Align score 2/4, or late in kill zone, minor concerns
  2 = Align score <2, counter-trend flag active, or at existing OB (reduce by 1 if at_ob)
  1 = Multiple contextual negatives stacked (low align + counter-trend + late KZ + at_ob)

MODIFIERS (apply after initial score):
- If the impulse creates a Fair Value Gap (FVG/three-candle gap): add +1 to STRUCTURAL (cap at 5)
- If price is at or touching a pre-existing OB (at_ob = true): reduce CONTEXTUAL by 1

Your confidence = (STRUCTURAL + CONTEXTUAL) × 10

Respond with ONLY this JSON:
{
  "structural_score": 0,
  "structural_reasoning": "string — cite specific numbers: impulse candle count, FVG yes/no, retracement %, BOS type",
  "contextual_score": 0,
  "contextual_reasoning": "string — cite: align score, trend direction match, KZ timing, at_ob status",
  "confidence": 0,
  "modifiers_applied": "string — list any FVG boost or at_ob penalty applied"
}"""


def load_data():
    with open(BATCH_DIR / f"{PRIMARY}_full_prompts.json") as f:
        prompts = json.load(f)
    with open(BATCH_DIR / f"{PRIMARY}_raw_results.json") as f:
        raw = json.load(f)
    with open(BATCH_DIR / f"{PRIMARY}_results.json") as f:
        results = json.load(f)

    # Build trade outcomes index
    trade_outcomes = {}
    for day in results:
        if not isinstance(day, dict) or not day.get('trade_taken'):
            continue
        for t in day.get('trades', []):
            if isinstance(t, dict):
                trade_outcomes[day['date']] = t

    # Build prompt index
    prompt_idx = {p['custom_id']: p for p in prompts}

    return prompt_idx, raw, trade_outcomes


def find_candidate_key(raw, date, kz):
    """Find the CANDIDATE entry key for a date+kz combo."""
    for k, v in raw.items():
        if not k.startswith(date) or f'_{kz}_' not in k:
            continue
        text = v.get('text', '') if isinstance(v, dict) else str(v)
        try:
            p = json.loads(text)
        except:
            continue
        if p.get('decision') in ('CANDIDATE', 'ENTER_LONG', 'ENTER_SHORT'):
            return k
    return None


def get_mso_text(prompt_idx, key):
    """Extract user_message (MSO) from the prompt."""
    p = prompt_idx.get(key)
    if not p:
        return None
    return p['prompt'].get('user_message', '')


def score_trade(client, mso_text, trade_id):
    """Score a single MSO through the decomposition rubric."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SCORING_PROMPT,
        messages=[{"role": "user", "content": f"Score this setup:\n\n{mso_text}"}]
    )
    text = response.content[0].text
    # Extract JSON from possible markdown wrapping or preamble
    text = text.strip()
    if "```" in text:
        # Find content between code fences
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break
    # Find the JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        print(f"    WARNING: Failed to parse JSON. Raw response:\n    {text[:300]}")
        result = {
            "structural_score": 0, "structural_reasoning": "PARSE_ERROR",
            "contextual_score": 0, "contextual_reasoning": "PARSE_ERROR",
            "confidence": 0, "modifiers_applied": "PARSE_ERROR",
        }
    result["trade_id"] = trade_id
    return result


def main():
    print("Loading data...")
    prompt_idx, raw, trade_outcomes = load_data()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Selected trades (from primary batch)
    selected = [
        {"label": "winner1", "date": "2025-01-30", "kz": "london", "outcome": "WIN", "r": 3.77},
        {"label": "winner2", "date": "2025-10-16", "kz": "ny", "outcome": "WIN", "r": 3.45},
        {"label": "loser1", "date": "2024-09-27", "kz": "ny", "outcome": "LOSS", "r": -1.00},
        {"label": "loser2", "date": "2025-02-12", "kz": "london", "outcome": "LOSS", "r": -1.00},
        {"label": "marginal", "date": "2024-04-03", "kz": "ny", "outcome": "WIN", "r": 0.05},
    ]

    # Extract MSOs
    print("\nExtracting MSOs...")
    mso_data = []
    for t in selected:
        cand_key = find_candidate_key(raw, t['date'], t['kz'])
        if not cand_key:
            print(f"  {t['label']} ({t['date']} {t['kz']}): NO CANDIDATE FOUND")
            continue
        mso = get_mso_text(prompt_idx, cand_key)
        if not mso:
            print(f"  {t['label']} ({t['date']} {t['kz']}): NO MSO TEXT")
            continue
        print(f"  {t['label']} ({t['date']} {t['kz']}): {len(mso)} chars")
        mso_data.append({**t, 'cand_key': cand_key, 'mso': mso})

    if not mso_data:
        print("No MSOs found!")
        return

    # Score each MSO TWICE
    print(f"\nScoring {len(mso_data)} trades × 2 runs = {len(mso_data)*2} API calls...")
    client = anthropic.Anthropic()

    results = []
    for t in mso_data:
        print(f"\n  Scoring {t['label']} ({t['date']})...")

        r1 = score_trade(client, t['mso'], f"{t['date']}_run1")
        time.sleep(1)
        r2 = score_trade(client, t['mso'], f"{t['date']}_run2")
        time.sleep(1)

        consistency = abs(r1['confidence'] - r2['confidence'])
        print(f"    Run1: S={r1['structural_score']} C={r1['contextual_score']} conf={r1['confidence']}")
        print(f"    Run2: S={r2['structural_score']} C={r2['contextual_score']} conf={r2['confidence']}")
        print(f"    Gap: {consistency} pts {'CONSISTENT' if consistency <= 10 else 'INCONSISTENT'}")

        results.append({
            'label': t['label'],
            'date': t['date'],
            'kz': t['kz'],
            'outcome': t['outcome'],
            'r': t['r'],
            'mso_len': len(t['mso']),
            'run1': r1,
            'run2': r2,
            'consistency': consistency,
        })

    # Generate report
    print("\nGenerating report...")
    report = format_report(results)
    with open(OUTPUT, 'w') as f:
        f.write(report)
    print(f"Saved to {OUTPUT}")

    # Also save raw results
    with open(RAW_OUTPUT, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def format_report(results):
    lines = []
    lines.append("# Confidence Decomposition Test — Real MSO Results\n")
    lines.append("## Setup\n")
    lines.append("- 5 trades from primary XAUUSD batch (2 winners, 2 losers, 1 marginal)")
    lines.append("- Each MSO scored TWICE through a 2-dimension rubric (Structural × Contextual)")
    lines.append("- Model: claude-sonnet-4-20250514")
    lines.append("- Confidence = (Structural + Contextual) × 10\n")

    # Selected trades table
    lines.append("## Selected Trades\n")
    lines.append("| Label | Date | KZ | Outcome | R-Multiple |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append(f"| {r['label']} | {r['date']} | {r['kz']} | {r['outcome']} | {r['r']:+.2f}R |")

    # Scoring results
    lines.append("\n## Scoring Results\n")
    lines.append("| Trade | Outcome | R | Run1 S | Run1 C | Run1 Conf | Run2 S | Run2 C | Run2 Conf | Gap | Consistent? |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        cons = "YES" if r['consistency'] <= 10 else "**NO**"
        lines.append(
            f"| {r['date']} | {r['outcome']} | {r['r']:+.2f}R | "
            f"{r['run1']['structural_score']} | {r['run1']['contextual_score']} | {r['run1']['confidence']} | "
            f"{r['run2']['structural_score']} | {r['run2']['contextual_score']} | {r['run2']['confidence']} | "
            f"{r['consistency']} | {cons} |"
        )

    # Consistency analysis
    max_gap = max(r['consistency'] for r in results)
    avg_gap = sum(r['consistency'] for r in results) / len(results)
    lines.append(f"\n**Max gap across runs: {max_gap} pts**")
    lines.append(f"**Avg gap: {avg_gap:.1f} pts**")
    if max_gap > 20:
        lines.append("**CONSISTENCY FAIL: Same MSO varies >20 pts. Scores are noise.**\n")
    else:
        lines.append("**Consistency: PASS**\n")

    # Discrimination analysis
    lines.append("## Discrimination Analysis\n")
    # Use average of both runs
    for r in results:
        r['avg_conf'] = (r['run1']['confidence'] + r['run2']['confidence']) / 2
        r['avg_s'] = (r['run1']['structural_score'] + r['run2']['structural_score']) / 2
        r['avg_c'] = (r['run1']['contextual_score'] + r['run2']['contextual_score']) / 2

    winners = [r for r in results if r['outcome'] == 'WIN']
    losers = [r for r in results if r['outcome'] == 'LOSS']

    w_conf = sum(r['avg_conf'] for r in winners) / len(winners) if winners else 0
    l_conf = sum(r['avg_conf'] for r in losers) / len(losers) if losers else 0
    gap = w_conf - l_conf

    lines.append(f"| Group | N | Mean Confidence | Mean Structural | Mean Contextual |")
    lines.append(f"|---|---|---|---|---|")
    lines.append(f"| Winners | {len(winners)} | {w_conf:.0f} | {sum(r['avg_s'] for r in winners)/len(winners):.1f} | {sum(r['avg_c'] for r in winners)/len(winners):.1f} |")
    lines.append(f"| Losers | {len(losers)} | {l_conf:.0f} | {sum(r['avg_s'] for r in losers)/len(losers):.1f} | {sum(r['avg_c'] for r in losers)/len(losers):.1f} |")
    lines.append(f"| **Gap** | — | **{gap:+.0f} pts** | {sum(r['avg_s'] for r in winners)/len(winners) - sum(r['avg_s'] for r in losers)/len(losers):+.1f} | {sum(r['avg_c'] for r in winners)/len(winners) - sum(r['avg_c'] for r in losers)/len(losers):+.1f} |")

    # Per-dimension analysis
    lines.append("\n### Which Dimension Discriminates Better?\n")
    w_s = sum(r['avg_s'] for r in winners) / len(winners) if winners else 0
    l_s = sum(r['avg_s'] for r in losers) / len(losers) if losers else 0
    w_c = sum(r['avg_c'] for r in winners) / len(winners) if winners else 0
    l_c = sum(r['avg_c'] for r in losers) / len(losers) if losers else 0
    lines.append(f"- Structural gap: {w_s - l_s:+.1f} (winners {w_s:.1f} vs losers {l_s:.1f})")
    lines.append(f"- Contextual gap: {w_c - l_c:+.1f} (winners {w_c:.1f} vs losers {l_c:.1f})")

    if abs(w_s - l_s) > abs(w_c - l_c):
        lines.append("- **Structural dimension discriminates better**")
    else:
        lines.append("- **Contextual dimension discriminates better**")

    # Reasoning quality check
    lines.append("\n## Reasoning Quality Check\n")
    lines.append("Does the AI cite specific numbers or use vague language?\n")

    for r in results:
        lines.append(f"### {r['date']} ({r['outcome']}, {r['r']:+.2f}R)\n")
        lines.append(f"**Run 1 Structural:** {r['run1']['structural_reasoning']}")
        lines.append(f"**Run 1 Contextual:** {r['run1']['contextual_reasoning']}")
        lines.append(f"**Run 1 Modifiers:** {r['run1'].get('modifiers_applied', 'none')}\n")

    # Verdict
    lines.append("## Verdict\n")
    if max_gap > 20:
        lines.append("### FAIL — Inconsistent\n")
        lines.append(f"Same MSO varies by up to {max_gap} pts across runs. Scores are noise, not signal.")
        lines.append("The decomposition rubric does not produce stable outputs.")
    elif gap >= 20:
        lines.append("### PASS — Strong Discrimination\n")
        lines.append(f"Winner-loser gap: {gap:+.0f} pts. Scores are consistent (max gap {max_gap} pts).")
        lines.append("**Action:** WF-2 candidate — implement in shadow mode alongside current system.")
    elif gap >= 10:
        lines.append("### PROMISING — Moderate Discrimination\n")
        lines.append(f"Winner-loser gap: {gap:+.0f} pts (threshold: ≥20). Consistent (max gap {max_gap} pts).")
        lines.append("**Action:** Refine rubric, retest on 10 trades. Consider tightening structural criteria.")
    else:
        lines.append("### FAIL — No Discrimination\n")
        lines.append(f"Winner-loser gap: {gap:+.0f} pts (<10 threshold). The rubric doesn't separate winners from losers.")
        lines.append("**Action:** Kill the decomposition idea or redesign from scratch.")

    return "\n".join(lines)


if __name__ == '__main__':
    main()
