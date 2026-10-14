"""Training, hyperparameter tuning, model selection, and test evaluation.

Implements all specifications from leaves2/SPEC.md:
- Deduplicates exact repeats
- Stratified 80/20 train/test holdout (random_state=42)
- Baseline DummyClassifier evaluation
- 5-fold Stratified CV across 4 model families
- Saves cv_results.csv, best_model_info.json, test_predictions.csv, test_metrics.json
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

HERE = Path(__file__).parent
DATA_PATH = HERE / "leaves.csv"
RESULTS_DIR = HERE / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_and_split_data():
    raw_df = pd.read_csv(DATA_PATH)
    raw_df.columns = ["height", "width", "type"]
    
    # Drop exact duplicate rows to prevent leakage
    df = raw_df.drop_duplicates().copy().reset_index(drop=True)
    print(f"Original samples: {len(raw_df)}, Unique samples after deduplication: {len(df)}")
    
    X = df[["height", "width"]]
    y = df["type"]
    
    # 80/20 Stratified Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    
    # Verify no overlap between train and test
    train_idx = set(zip(X_train["height"], X_train["width"], y_train))
    test_idx = set(zip(X_test["height"], X_test["width"], y_test))
    overlap = train_idx.intersection(test_idx)
    assert len(overlap) == 0, f"Data leakage detected! {len(overlap)} rows overlap!"
    
    print(f"Training samples: {len(X_train)} (80%), Test holdout samples: {len(X_test)} (20%)")
    print("Class distribution in Train:\n", y_train.value_counts().to_dict())
    print("Class distribution in Test:\n", y_test.value_counts().to_dict())
    
    return X_train, X_test, y_train, y_test


def evaluate_baseline(X_train, y_train, cv):
    print("\n--- STEP 3: Baseline Dummy Classifier ---")
    baseline = DummyClassifier(strategy="most_frequent")
    
    scoring = {
        "macro_f1": "f1_macro",
        "accuracy": "accuracy"
    }
    cv_res = cross_validate(baseline, X_train, y_train, cv=cv, scoring=scoring)
    
    baseline_stats = {
        "model": "DummyClassifier(strategy='most_frequent')",
        "predicted_class": "maple",
        "cv_mean_macro_f1": float(np.mean(cv_res["test_macro_f1"])),
        "cv_std_macro_f1": float(np.std(cv_res["test_macro_f1"])),
        "cv_mean_accuracy": float(np.mean(cv_res["test_accuracy"])),
        "cv_std_accuracy": float(np.std(cv_res["test_accuracy"])),
    }
    
    out_path = RESULTS_DIR / "baseline_results.json"
    out_path.write_text(json.dumps(baseline_stats, indent=2))
    print(f"Baseline CV Macro F1: {baseline_stats['cv_mean_macro_f1']:.4f} (+/- {baseline_stats['cv_std_macro_f1']:.4f})")
    print(f"Baseline CV Accuracy: {baseline_stats['cv_mean_accuracy']:.4f} (+/- {baseline_stats['cv_std_accuracy']:.4f})")
    print(f"Saved baseline metrics to {out_path}")
    return baseline_stats


def run_hyperparameter_search(X_train, y_train, cv):
    print("\n--- STEP 4: Model Exploration & Hyperparameter Tuning ---")
    
    model_definitions = {
        "Logistic Regression": {
            "estimator": Pipeline([
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(random_state=42, max_iter=1000))
            ]),
            "param_grid": {
                "clf__C": [0.01, 0.1, 1.0, 10.0, 100.0]
            }
        },
        "K-Nearest Neighbors": {
            "estimator": Pipeline([
                ("scaler", StandardScaler()),
                ("clf", KNeighborsClassifier())
            ]),
            "param_grid": {
                "clf__n_neighbors": [1, 3, 5, 7, 11, 15, 21],
                "clf__weights": ["uniform", "distance"]
            }
        },
        "Decision Tree": {
            "estimator": DecisionTreeClassifier(random_state=42),
            "param_grid": {
                "max_depth": [2, 3, 4, 5, 6, None],
                "min_samples_split": [2, 5, 10]
            }
        },
        "Random Forest": {
            "estimator": RandomForestClassifier(random_state=42),
            "param_grid": {
                "n_estimators": [50, 100],
                "max_depth": [3, 5, 8, None],
                "min_samples_split": [2, 5]
            }
        }
    }
    
    all_trials = []
    best_overall_score = -1.0
    best_overall_model_name = None
    best_overall_grid_search = None
    
    scoring = {
        "macro_f1": "f1_macro",
        "accuracy": "accuracy"
    }
    
    for name, config in model_definitions.items():
        print(f"\nRunning GridSearch for: {name}...")
        grid = GridSearchCV(
            estimator=config["estimator"],
            param_grid=config["param_grid"],
            scoring=scoring,
            refit="macro_f1",
            cv=cv,
            n_jobs=-1,
            return_train_score=False
        )
        grid.fit(X_train, y_train)
        
        cv_results = grid.cv_results_
        n_candidates = len(cv_results["params"])
        
        for i in range(n_candidates):
            trial = {
                "model_family": name,
                "params": str(cv_results["params"][i]),
                "mean_cv_macro_f1": round(float(cv_results["mean_test_macro_f1"][i]), 4),
                "std_cv_macro_f1": round(float(cv_results["std_test_macro_f1"][i]), 4),
                "mean_cv_accuracy": round(float(cv_results["mean_test_accuracy"][i]), 4),
                "std_cv_accuracy": round(float(cv_results["std_test_accuracy"][i]), 4),
                "rank_macro_f1": int(cv_results["rank_test_macro_f1"][i])
            }
            all_trials.append(trial)
            
        print(f"  Best params: {grid.best_params_}")
        print(f"  Best CV Macro F1: {grid.best_score_:.4f}")
        
        if grid.best_score_ > best_overall_score:
            best_overall_score = grid.best_score_
            best_overall_model_name = name
            best_overall_grid_search = grid

    # Save all trials
    trials_df = pd.DataFrame(all_trials).sort_values("mean_cv_macro_f1", ascending=False)
    trials_csv = RESULTS_DIR / "cv_results.csv"
    trials_df.to_csv(trials_csv, index=False)
    print(f"\nSaved all {len(trials_df)} trial results to {trials_csv}")
    
    best_model_info = {
        "best_model_family": best_overall_model_name,
        "best_params": best_overall_grid_search.best_params_,
        "best_cv_macro_f1": float(best_overall_score),
        "total_configurations_tested": len(trials_df)
    }
    info_path = RESULTS_DIR / "best_model_info.json"
    info_path.write_text(json.dumps(best_model_info, indent=2))
    print(f"Saved best model info to {info_path}")
    print(f"Winner: {best_overall_model_name} with CV Macro F1 = {best_overall_score:.4f}")
    
    return best_overall_grid_search.best_estimator_, best_model_info


def evaluate_final_test_set(best_model, X_train, y_train, X_test, y_test, best_info):
    print("\n--- STEP 5: Final Evaluation on Untouched Test Holdout ---")
    
    # Fit the best model on full training set
    best_model.fit(X_train, y_train)
    
    # Predict strictly ONCE on held-out test data
    y_pred = best_model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, output_dict=True)
    labels = sorted(list(y_test.unique()))
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    
    print(f"Holdout Test Accuracy: {acc:.4f} ({acc*100:.2f}%)")
    print(f"Holdout Test Macro F1: {macro_f1:.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))
    print("Confusion Matrix:\n", pd.DataFrame(cm, index=labels, columns=labels))
    
    # Save predictions
    preds_df = X_test.copy()
    preds_df["true_type"] = y_test
    preds_df["predicted_type"] = y_pred
    preds_df["correct"] = (preds_df["true_type"] == preds_df["predicted_type"])
    preds_csv = RESULTS_DIR / "test_predictions.csv"
    preds_df.to_csv(preds_csv, index=False)
    print(f"\nSaved test predictions to {preds_csv}")
    
    # Save final metrics
    test_metrics = {
        "model_family": best_info["best_model_family"],
        "hyperparameters": best_info["best_params"],
        "test_samples": len(y_test),
        "test_accuracy": float(acc),
        "test_macro_f1": float(macro_f1),
        "test_weighted_f1": float(weighted_f1),
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "classification_report": report
    }
    metrics_json = RESULTS_DIR / "test_metrics.json"
    metrics_json.write_text(json.dumps(test_metrics, indent=2))
    print(f"Saved test metrics to {metrics_json}")
    
    # Plot Decision Boundary & Test Points
    plot_decision_boundaries(best_model, X_train, y_train, X_test, y_test, preds_df)


def plot_decision_boundaries(model, X_train, y_train, X_test, y_test, preds_df):
    plt.figure(figsize=(9, 7), dpi=150)
    
    all_X = pd.concat([X_train, X_test])
    h_min, h_max = all_X["height"].min() - 1, all_X["height"].max() + 1
    w_min, w_max = all_X["width"].min() - 1, all_X["width"].max() + 1
    
    xx, yy = np.meshgrid(np.linspace(h_min, h_max, 300), np.linspace(w_min, w_max, 300))
    grid_points = pd.DataFrame(np.c_[xx.ravel(), yy.ravel()], columns=["height", "width"])
    
    type_map = {"cherry": 0, "maple": 1, "walnut": 2}
    inv_type_map = {0: "cherry", 1: "maple", 2: "walnut"}
    
    preds_grid = model.predict(grid_points)
    Z = np.array([type_map[p] for p in preds_grid]).reshape(xx.shape)
    
    cmap_bg = matplotlib.colors.ListedColormap(["#d8b365", "#f5c5b8", "#a6dba0"])
    plt.contourf(xx, yy, Z, alpha=0.3, cmap=cmap_bg)
    
    # Colors for points
    palette = {"cherry": "#8c510a", "maple": "#c51b7d", "walnut": "#01665e"}
    markers = {"cherry": "^", "maple": "o", "walnut": "s"}
    
    # Plot test points
    for tree_type in ["cherry", "maple", "walnut"]:
        sub = preds_df[preds_df["true_type"] == tree_type]
        correct = sub[sub["correct"]]
        incorrect = sub[~sub["correct"]]
        
        plt.scatter(
            correct["height"], correct["width"],
            color=palette[tree_type], marker=markers[tree_type],
            s=45, label=f"Test {tree_type} (correct n={len(correct)})", edgecolors="black", linewidth=0.5
        )
        if len(incorrect) > 0:
            plt.scatter(
                incorrect["height"], incorrect["width"],
                color="red", marker="x", s=70, linewidth=2,
                label=f"Test {tree_type} (mislabeled n={len(incorrect)})"
            )

    plt.title("Winning Model Decision Boundaries & Holdout Test Predictions", fontsize=12, fontweight="bold")
    plt.xlabel("Leaf Height (cm)", fontsize=11)
    plt.ylabel("Leaf Width (cm)", fontsize=11)
    plt.legend(loc="upper left", fontsize=9, framealpha=0.9)
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    
    boundary_path = RESULTS_DIR / "decision_boundaries.png"
    plt.savefig(boundary_path)
    plt.close()
    print(f"Saved decision boundaries plot to {boundary_path}")


def main():
    X_train, X_test, y_train, y_test = load_and_split_data()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Step 3: Baseline
    evaluate_baseline(X_train, y_train, cv)
    
    # Step 4: Models & Hyperparameter search
    best_model, best_info = run_hyperparameter_search(X_train, y_train, cv)
    
    # Step 5: Final Evaluation on held-out test set
    evaluate_final_test_set(best_model, X_train, y_train, X_test, y_test, best_info)
    
    print("\n--- Pipeline Completed Successfully ---")


if __name__ == "__main__":
    main()
