#!/usr/bin/env python3
"""
Claim Analysis Script
Purpose: Read all claim files, count by category, and find top 10 untested high-confidence claims
Author: Salma (Operations)
Date: 2026-04-07
"""

import json
import os
import glob
from collections import defaultdict
from typing import Dict, List, Tuple

def calculate_confidence_score(claim: Dict) -> float:
    """
    Calculate confidence score based on source_credibility and relevance
    Higher score = higher confidence
    """
    score = 0.0

    # Source credibility scoring
    if claim.get('source_credibility') == 'DATA':
        score += 3.0
    elif claim.get('source_credibility') == 'EXPERIENCE':
        score += 2.0
    elif claim.get('source_credibility') == 'OPINION':
        score += 1.0

    # Relevance scoring
    if claim.get('relevance') == 'DIRECT':
        score += 2.0
    elif claim.get('relevance') == 'RELATED':
        score += 1.0
    elif claim.get('relevance') == 'TANGENTIAL':
        score += 0.5

    # Specificity bonus
    if claim.get('specificity') == 'SPECIFIC':
        score += 1.0

    # Testable requirement (filter out non-testable)
    if not claim.get('testable', False):
        score = 0.0

    return score

def process_claim_files(claims_dir: str) -> Tuple[Dict, List]:
    """
    Process all claim JSON files in the directory
    Returns: (category_counts, all_claims_list)
    """
    category_counts = defaultdict(int)
    all_claims = []

    # Get all JSON claim files
    json_files = glob.glob(os.path.join(claims_dir, "video_*.json"))
    json_files.sort()

    print(f"Processing {len(json_files)} claim files...")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            video_file = os.path.basename(file_path)
            claims = data.get('claims', [])

            for claim in claims:
                # Normalize category names
                category = claim.get('category', 'UNKNOWN')
                if category == 'STATISTICAL_CLAIMS':
                    category = 'STATISTICAL'
                elif category == 'TRADING_RULES':
                    category = 'RULE'
                elif category == 'MARKET_MECHANICS':
                    category = 'CORRELATION'
                elif category in ['BACKTESTING_METHODOLOGY', 'RISK_MANAGEMENT', 'MARKET_MICROSTRUCTURE']:
                    category = 'OTHER'

                category_counts[category] += 1

                # Add metadata for analysis
                claim_with_meta = claim.copy()
                claim_with_meta['video_file'] = video_file
                claim_with_meta['confidence_score'] = calculate_confidence_score(claim)
                claim_with_meta['normalized_category'] = category

                all_claims.append(claim_with_meta)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    return dict(category_counts), all_claims

def find_untested_claims(all_claims: List[Dict]) -> List[Dict]:
    """
    Filter for untested claims (testable=True, but not yet implemented in our system)
    For this analysis, we assume all claims are untested unless they match known implemented features
    """
    untested_claims = []

    # Known tested patterns (from our existing system)
    tested_keywords = [
        # These would be patterns we've already implemented
        # For now, we'll assume most claims are untested since this is knowledge extraction
    ]

    for claim in all_claims:
        if not claim.get('testable', False):
            continue

        # For this analysis, treat all testable claims as untested
        # (since we're in knowledge extraction phase)
        claim_text = claim.get('claim', '').lower()
        is_tested = any(keyword in claim_text for keyword in tested_keywords)

        if not is_tested:
            untested_claims.append(claim)

    return untested_claims

def generate_report(category_counts: Dict, all_claims: List[Dict], untested_claims: List[Dict]) -> str:
    """
    Generate the priority report
    """
    report = []
    report.append("# Untested Claims Priority Analysis")
    report.append("**Date:** 2026-04-07")
    report.append("**Analyst:** Salma (Operations)")
    report.append("**Purpose:** CEO directive to prioritize untested high-confidence claims")
    report.append("")

    # Category breakdown
    report.append("## Total Claims by Category")
    report.append("")
    total_claims = sum(category_counts.values())
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_claims) * 100 if total_claims > 0 else 0
        report.append(f"- **{category}**: {count} claims ({percentage:.1f}%)")
    report.append(f"\n**Total Claims Analyzed:** {total_claims}")
    report.append("")

    # Testable vs non-testable breakdown
    testable_count = len([c for c in all_claims if c.get('testable', False)])
    report.append(f"**Testable Claims:** {testable_count} ({(testable_count/total_claims)*100:.1f}%)")
    report.append(f"**Untested Testable Claims:** {len(untested_claims)}")
    report.append("")

    # Top 10 highest confidence untested claims
    report.append("## Top 10 Highest-Confidence Untested Claims")
    report.append("")

    # Sort by confidence score (descending)
    top_untested = sorted(untested_claims, key=lambda x: x['confidence_score'], reverse=True)[:10]

    for i, claim in enumerate(top_untested, 1):
        report.append(f"### {i}. {claim['normalized_category']} - Confidence: {claim['confidence_score']:.1f}")
        report.append(f"**Source:** {claim.get('video_file', 'Unknown')} | **Credibility:** {claim.get('source_credibility', 'Unknown')} | **Relevance:** {claim.get('relevance', 'Unknown')}")
        report.append("")
        report.append(f"**Claim:** {claim.get('claim', 'No claim text')}")
        report.append("")
        report.append(f"**Test Method:** {claim.get('testable_reason', 'No test method specified')}")
        report.append("")
        report.append(f"**Context:** {claim.get('context', 'No context provided')}")
        report.append("")
        report.append("---")
        report.append("")

    return "\n".join(report)

def main():
    """Main execution function"""
    claims_dir = "research/kap_outputs/claims"

    if not os.path.exists(claims_dir):
        print(f"Error: Claims directory not found: {claims_dir}")
        return

    print("🔍 Analyzing all claim files...")
    category_counts, all_claims = process_claim_files(claims_dir)

    print("📊 Finding untested claims...")
    untested_claims = find_untested_claims(all_claims)

    print("📝 Generating priority report...")
    report = generate_report(category_counts, all_claims, untested_claims)

    # Save report
    output_file = "research/kap_outputs/untested_claims_priority.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Report saved to {output_file}")
    print(f"📈 Total claims: {len(all_claims)}")
    print(f"🎯 Untested claims: {len(untested_claims)}")
    print(f"🏆 Top 10 identified for priority testing")

if __name__ == "__main__":
    main()