# Jev / TypeSafe lab SUMMARY

Date: 2026-09-16 ICT. Probes only — never place/remint/flatten.

Successful named probes: 7; failed: 0
Ping latencies_ms: [205.87979699485004, 140.7651170156896, 186.39405793510377, 147.84065599087626, 195.57208800688386]

## Takeaways for GTOS
- Primitives Choice / Score / Noul work for admit, close-label, HOLD-draft shapes.
- Compose policy in code from atomic answers + confidence gates; do not ask one mega-question.
- Keep Jev off the place path; use as intelligence/info sidecar with escalate-on-low-confidence.

## Per-probe
### models_list
- elapsed_ms: 283.5 error: None

### smoke_support_ticket
- elapsed_ms: 230.9 error: None
- usage: {'input_tokens': 424, 'output_tokens': 73}
- answers: `{"department": {"type": null, "choice": "billing", "confidence": 0.45, "probabilities": {"sales": 0.0, "technical": 0.36, "billing": 0.64}}, "frustration": {"type": null, "score": 1.0, "confidence": 1.0, "probabilities": {"0": 0.0, "1": 1.0, "2": 0.0}, "legend": {"0": "Calm, just stating facts", "1": "Frustrated but civil", "2": "Very angry, strong language"}}, "is_urgent": {"type": null, "noul": 0.99}}`

### gtos_admit_candidate
- elapsed_ms: 206.9 error: None
- usage: {'input_tokens': 781, 'output_tokens': 109}
- answers: `{"admit": {"type": null, "choice": "admit", "confidence": 0.33, "probabilities": {"admit": 0.56, "abstain": 0.13, "hard_refuse": 0.31}}, "surface_ok": {"type": null, "noul": 0.75}, "toxic_family": {"type": null, "noul": 0.61}, "geometry_quality": {"type": null, "score": 1.01, "confidence": 0.95, "probabilities": {"0": 0.01, "1": 0.97, "2": 0.02}, "legend": {"0": "Poor \u2014 stop too tight or TP unreachable vs tape", "1": "Acceptable \u2014 house default ~1R/6R with known fast-stop risk", "2": "Good \u2014 stop width and TP fit current volatility"}}, "confidence_gate": {"type": null, "score": 0.89, "confidence": 0.0, "probabilities": {"0": 0.41000000000000003, "1": 0.3, "2": 0.29}, "legend": {"0": "Escalate to chair \u2014 ambiguity or low reliability", "1": "Sidecar only \u2014 record sco`

### gtos_close_label
- elapsed_ms: 171.4 error: None
- usage: {'input_tokens': 577, 'output_tokens': 105}
- answers: `{"exit_class": {"type": null, "choice": "orig_stop", "confidence": 1.0, "probabilities": {"tp": 0.0, "orig_stop": 1.0, "time_stop": 0.0, "manual_other": 0.0}}, "remint_toxic": {"type": null, "noul": 0.63}, "prefill_hold_would_help": {"type": null, "noul": 0.45}, "lesson": {"type": null, "score": 1.68, "confidence": 0.51, "probabilities": {"0": 0.02, "1": 0.29, "2": 0.69}, "legend": {"0": "Noise \u2014 ignore for policy", "1": "Useful single sample \u2014 study only", "2": "Strong signal \u2014 consider sleeve pressure or HOLD timing repair"}}}`

### gtos_corr_hold_draft
- elapsed_ms: 145.6 error: None
- usage: {'input_tokens': 483, 'output_tokens': 78}
- answers: `{"speak_hold": {"type": null, "noul": 0.64}, "hold_strength": {"type": null, "score": 1.92, "confidence": 0.88, "probabilities": {"0": 0.03, "1": 0.01, "2": 0.96}, "legend": {"0": "Weak \u2014 n low or mixed directions", "1": "Moderate \u2014 cluster forming", "2": "Strong \u2014 multi-symbol same-dir cluster >=3"}}, "action_scope": {"type": null, "choice": "audit_only", "confidence": 1.0, "probabilities": {"block_sibling_prefills": 0.0, "flatten": 0.0, "audit_only": 1.0}}}`

### fanout_12_nouls
- elapsed_ms: 168.8 error: None
- usage: {'input_tokens': 695, 'output_tokens': 210}
- answers: `{"q0": {"type": null, "noul": 0.61}, "q1": {"type": null, "noul": 0.62}, "q2": {"type": null, "noul": 0.56}, "q3": {"type": null, "noul": 0.57}, "q4": {"type": null, "noul": 0.6}, "q5": {"type": null, "noul": 0.58}, "q6": {"type": null, "noul": 0.56}, "q7": {"type": null, "noul": 0.57}, "q8": {"type": null, "noul": 0.58}, "q9": {"type": null, "noul": 0.59}, "q10": {"type": null, "noul": 0.57}, "q11": {"type": null, "noul": 0.58}}`

### adversarial_emptyish
- elapsed_ms: 141.4 error: None
- usage: {'input_tokens': 322, 'output_tokens': 49}
- answers: `{"admit": {"type": null, "choice": "no", "confidence": 0.93, "probabilities": {"yes": 0.03, "no": 0.97}}, "sure": {"type": null, "noul": 0.13}}`
