# Botanical Classification ML Pipeline

End-to-end Machine Learning classification pipeline for identifying tree species (`maple`, `walnut`, `cherry`) from leaf dimensions (`height`, `width`) in `leaves.csv`.

## Overview

- **Dataset:** 518 raw samples (492 unique botanical records after removing 26 exact duplicate artifacts; two physiological cherry leaf extremes preserved).
- **Validation Strategy:** Stratified 80/20 train/test holdout split; 5-fold Stratified Cross-Validation on the 393 training samples.
- **Primary Optimization Metric:** Macro F1-score (mitigating class imbalance).
- **Hyperparameter Search:** Evaluated 53 model configurations across 4 model families:
  - Logistic Regression (scaling + regularisation penalty C)
  - k-Nearest Neighbors ($k \in [3, 15]$, uniform vs. distance weighting)
  - Decision Tree (`max_depth`, `min_samples_leaf`)
  - Random Forest (`n_estimators`, `max_depth`, `min_samples_split`)

## Key Results

| Metric | Dummy Baseline | Champion Model (k-NN, $k=7$, distance) | Improvement |
| :--- | :--- | :--- | :--- |
| **CV Macro F1** | 0.1980 | **0.9556** | **+0.7576** |
| **CV Accuracy** | 42.24% | **95.67%** | **+53.43%** |
| **Holdout Test F1** | 0.1980 | **0.8983** | **+0.7003** |
| **Holdout Test Acc** | 42.24% | **90.91%** | **+48.67%** |

## Deliverables

1. **`report.html` (Interactive Technical Report):**
   - 5 KPI summary metric cards.
   - Interactive Canvas simulation showcasing 9 chronological stages of decision boundary evolution.
   - Comprehensive model leaderboard comparing all 53 hyperparameter trials.
   - Autopsy and confusion breakdown of the 9 holdout test classification errors.
2. **`slides.html` (Quarto Reveal.js Presentation):**
   - 5 linear, content-dense slides tailored for stakeholders and engineering teams.
   - Speaker notes, responsive typography, and embedded experimental visualizations.
3. **`SPEC.md`:** Complete architectural specification, constraints, data governance, and checklist.

## Usage

```bash
# Run exploratory data analysis and generate scatter plot
uv run python explore.py

# Execute 5-fold CV hyperparameter search and holdout test evaluation
uv run python train.py

# Render Quarto slides to standalone HTML
uv run quarto render slides.qmd

# Render Quarto technical report to standalone HTML
uv run quarto render report.qmd
```
