# ML Project Health Report

Generated on: 2026-08-22 14:18

## Overview
- Total files analyzed: 4
- Total code chunks (functions/classes): 8
- Overall Project Score: **80/100**
- Total issues found: 2

## Findings

### Data Leakage (1 issue(s))
- **bad_model.py** (line 6): Possible data leakage: fit_transform() called before train_test_split()
  - *Suggestion:* Split data first, then fit_transform only on training data.

### Overfitting Risk (1 issue(s))
- **bad_model.py**: Model is trained but never evaluated on a validation/test set
  - *Suggestion:* Add a train/validation split and evaluate performance (e.g. accuracy, loss) on held-out data to check for overfitting.