# Analysis Notes

## Cherry-Picking Warning

Condition A shows a significant positive result (accuracy 0.72).
Condition B shows a significant negative result (accuracy 0.48).
Condition C is not significant (accuracy 0.51).

A claim like "approach X improves accuracy" is UNSUPPORTED because it
ignores condition B. A correct claim must be bounded: "approach X improves
accuracy under condition A but degrades it under condition B, with no
significant effect under condition C."

## Overgeneralization Warning

These results apply ONLY to the tested conditions (A, B, C) and metrics
(accuracy, f1, latency). Do NOT generalize to other datasets, metrics, or
populations not represented in mixed_results.csv.
