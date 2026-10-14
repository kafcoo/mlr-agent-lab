# SPEC.md — Leaf Species Classification

## 1. Goal
The objective is to train, tune, and evaluate a machine learning classifier that accurately predicts tree species (`maple`, `cherry`, or `walnut`) from physical leaf dimensions (`height` and `width` in cm).

The result must answer:
- Which classification algorithm and hyperparameter configuration best separates the three tree species?
- What is the realistic, unbiased out-of-sample generalization accuracy and macro F1 score on unseen leaf specimens?
- By how much does the chosen model outperform a naive baseline?

## 2. Context
- **Data source**: `leaves2/leaves.csv` (provided dataset).
- **Dimensions**: 518 rows, 3 columns:
  - `Leaf height` (float, range 3.8 cm – 25.5 cm)
  - `Leaf width` (float, range 2.5 cm – 29.7 cm)
  - `Tree type` (categorical target: `maple`, `cherry`, `walnut`)
- **Class distribution (original)**:
  - `maple`: 216 samples (41.7%)
  - `cherry`: 173 samples (33.4%)
  - `walnut`: 129 samples (24.9%)
- **Exploratory findings from Step 1**:
  - **Identical rows**: 26 exact duplicate records exist (492 unique pairs).
  - **Measurement precision**: 316 rows have 1–2 decimal places, while 202 rows have 5–6 decimal places (synthetic jittered copies of prior measurements).
  - **Data anomalies / outliers**: 2 cherry entries (rows 214 and 390) exhibit leaf widths of 17.1 cm and 21.6 cm, placing them far inside the maple distribution (likely mislabeled).
  - **Morphology**: Maple leaves are characteristically wider than tall (width > height for 81% of maples), walnut leaves are tall and narrow, and cherry leaves are small in both dimensions. Maple also shows a bimodal size distribution (< 18 cm and > 18 cm).

## 3. Constraints
- **Data leakage prevention & Test set split**:
  - Exact duplicate rows are dropped before splitting to prevent data leakage between train and test sets (yielding 492 unique records).
  - Outlier policy: The 2 anomalous cherry rows are retained to evaluate real-world label noise robustness.
  - Hold-out test set: Exactly 20% of unique data (99 samples), created via `train_test_split(..., test_size=0.20, stratify=y, random_state=42)`.
  - The remaining 80% (393 samples) forms the training set.
  - The test set must be isolated immediately and evaluated strictly **once** at the very end.
- **Cross-validation**:
  - 5-fold Stratified Cross-Validation (`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`) on the 80% training set for all model selection and hyperparameter tuning.
- **Candidate Models & Search Space**:
  1. *Baseline*: `DummyClassifier(strategy="most_frequent")` (always predicts majority class `maple`).
  2. *Logistic Regression*: `StandardScaler()` + `LogisticRegression(random_state=42, max_iter=1000)` with `C` in `[0.01, 0.1, 1.0, 10.0, 100.0]`.
  3. *K-Nearest Neighbors (k-NN)*: `StandardScaler()` + `KNeighborsClassifier()` with `n_neighbors` in `[1, 3, 5, 7, 11, 15, 21]` and `weights` in `['uniform', 'distance']`.
  4. *Decision Tree*: `DecisionTreeClassifier(random_state=42)` with `max_depth` in `[2, 3, 4, 5, 6, None]` and `min_samples_split` in `[2, 5, 10]`.
  5. *Random Forest*: `RandomForestClassifier(random_state=42)` with `n_estimators` in `[50, 100]`, `max_depth` in `[3, 5, 8, None]`, and `min_samples_split` in `[2, 5]`.
- **Selection Metric**:
  - Primary selection metric: **Macro-averaged F1 score (`macro_f1`)** averaged across the 5 validation folds (ensures balanced performance across all 3 classes).
  - Secondary metrics logged: Overall Accuracy, per-class Precision/Recall/F1, and Confusion Matrix.
- **Tuning budget**:
  - Exhaustive grid search over the specified candidate spaces (fast execution given $N < 500$ and 2 features).
  - Every trial result logged with mean CV score and standard deviation.

## 4. Done when
The project is complete when all of the following artifacts exist and checks pass:
1. **Source code**:
   - `leaves2/explore.py`: Step 1 data analysis and scatter plot generation.
   - `leaves2/train.py`: Full model training, grid search CV, selection, and final test evaluation script.
2. **Saved results (generated directly by code, not hardcoded)**:
   - `leaves2/height_vs_width.png`: Scatter plot of the data.
   - `leaves2/results/baseline_results.json`: Metrics of the baseline model.
   - `leaves2/results/cv_results.csv`: Table of all trained hyperparameter configurations with their CV scores.
   - `leaves2/results/best_model_info.json`: Selected model name, optimal hyperparameters, and validation score.
   - `leaves2/results/test_metrics.json`: Final test set performance (Accuracy, Macro F1, per-class metrics, Confusion Matrix).
   - `leaves2/results/test_predictions.csv`: Test set predictions with columns `[height, width, true_type, predicted_type]`.
3. **Report and Presentation**:
   - `leaves2/slides.qmd` rendered to `leaves2/slides.html` (5 slides via Quarto with revealjs format presenting goal, data findings, model comparisons, final test result, and conclusions).
4. **Verifications**:
   - Baseline accuracy is beaten by at least 40 percentage points (e.g. from ~42% baseline to >85% test accuracy).
   - No data leakage: zero test rows present in train (`len(set(train).intersection(set(test))) == 0`).
   - A single command `uv run python leaves2/train.py` runs cleanly and reproduces all numbers in `results/`.
