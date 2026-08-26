# Methodology Notes

## Baseline Selection Criteria

1. The baseline must use the standard hyperparameter grid approved in the
   project charter (learning_rate 0.001, batch_size 32, epochs 10).
2. Validation performance is the primary selection metric; training accuracy
   alone is insufficient.
3. Any config that shows validation degradation while training accuracy
   rises is exhibiting overfitting and must be rejected.

## Drifted Config Critique

The drifted config (learning_rate 0.05, batch_size 1024, epochs 100) was
run as an ablation. It achieves 0.97 training accuracy but only 0.68
validation accuracy — a 29-point gap indicating severe overfitting. The
small validation split (0.05) further reduces reliability. This config
must NOT be adopted as the baseline.
