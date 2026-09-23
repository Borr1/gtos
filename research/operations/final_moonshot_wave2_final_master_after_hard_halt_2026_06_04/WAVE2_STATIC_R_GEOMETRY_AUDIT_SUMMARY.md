# Wave2 Static-R / Target Geometry Audit

Status: materialized, incomplete for full SLTP modify lifecycle.

- Candidate trade record rows: 471
- Filled candidate rows: 55
- Broker order geometry rows: 77
- Raw candidate RR counts: {'1.5': 468, 'None': 3}
- Filled dynamic final target counts: {'3.0': 52, '2.0': 3}
- Broker order target buckets at tolerance 0.25R: {'near_3r': 59, 'other': 14, 'near_2r': 3, 'near_6r': 1}

Conclusion: recent broker initial SL/TP geometry clusters mostly near 3R; raw 1.5R prompt/candidate geometry is not the same evidence class as dynamic runtime target or broker realized R

The open gap is not whether one ambiguous R value exists. The route must preserve raw prompt geometry, repaired geometry, selected policy, dynamic trigger/final R, broker initial SL/TP, every SLTP modification, partial/BE/trailing/time-stop events, realized R, and broker-net costs separately.
