"""
HireWise ML Training Pipeline
Run: python ml/train.py
Trains XGBoost and Random Forest on synthetic resume data,
saves best model + scaler + metrics to model_artifacts/
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


# ─── 1. Synthetic Dataset Generation ─────────────────────────────────────────

def generate_synthetic_dataset(n_samples: int = 1200, random_state: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic resume feature dataset."""
    np.random.seed(random_state)
    records = []

    for _ in range(n_samples):
        # Label-conditional generation for realism
        label_roll = np.random.random()
        if label_roll < 0.33:
            label = "Weak"
        elif label_roll < 0.66:
            label = "Average"
        else:
            label = "Strong"

        if label == "Strong":
            skills_count = np.random.uniform(0.5, 1.0)
            relevant_skills = np.random.uniform(0.4, 1.0)
            experience = np.random.uniform(0.3, 1.0)
            complexity = np.random.uniform(0.5, 1.0)
            education = np.random.choice([0.6, 0.8, 1.0], p=[0.3, 0.4, 0.3])
            has_ml = np.random.choice([0, 1], p=[0.2, 0.8])
            has_cloud = np.random.choice([0, 1], p=[0.3, 0.7])
            has_web = np.random.choice([0, 1], p=[0.2, 0.8])
            certs = np.random.uniform(0.1, 0.8)
            text_len = np.random.uniform(0.5, 1.0)
        elif label == "Average":
            skills_count = np.random.uniform(0.25, 0.65)
            relevant_skills = np.random.uniform(0.2, 0.6)
            experience = np.random.uniform(0.1, 0.5)
            complexity = np.random.uniform(0.2, 0.6)
            education = np.random.choice([0.4, 0.6, 0.8], p=[0.3, 0.5, 0.2])
            has_ml = np.random.choice([0, 1], p=[0.5, 0.5])
            has_cloud = np.random.choice([0, 1], p=[0.6, 0.4])
            has_web = np.random.choice([0, 1], p=[0.4, 0.6])
            certs = np.random.uniform(0.0, 0.4)
            text_len = np.random.uniform(0.3, 0.7)
        else:  # Weak
            skills_count = np.random.uniform(0.0, 0.35)
            relevant_skills = np.random.uniform(0.0, 0.3)
            experience = np.random.uniform(0.0, 0.2)
            complexity = np.random.uniform(0.0, 0.3)
            education = np.random.choice([0.0, 0.2, 0.4], p=[0.4, 0.4, 0.2])
            has_ml = np.random.choice([0, 1], p=[0.85, 0.15])
            has_cloud = np.random.choice([0, 1], p=[0.9, 0.1])
            has_web = np.random.choice([0, 1], p=[0.7, 0.3])
            certs = np.random.uniform(0.0, 0.1)
            text_len = np.random.uniform(0.1, 0.4)

        # Add realistic noise
        noise = lambda x, s=0.05: np.clip(x + np.random.normal(0, s), 0, 1)

        records.append({
            "skills_count": noise(skills_count),
            "relevant_skills_count": noise(relevant_skills),
            "experience_years": noise(experience, 0.08),
            "project_complexity_score": noise(complexity),
            "education_score": education,
            "has_ml_skills": has_ml,
            "has_cloud_skills": has_cloud,
            "has_web_skills": has_web,
            "certifications_count": noise(certs),
            "text_length_score": noise(text_len),
            "label": label,
        })

    return pd.DataFrame(records)


# ─── 2. Training Pipeline ─────────────────────────────────────────────────────

def train():
    print("=" * 60)
    print("  HireWise ML Training Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Imports
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
    from sklearn.metrics import (
        accuracy_score, f1_score, precision_score,
        recall_score, confusion_matrix, classification_report
    )
    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except ImportError:
        has_xgb = False
        print("[Warning] XGBoost not installed. Using Random Forest only.")

    # 1. Generate data
    print("\n[1/5] Generating synthetic dataset (1200 samples)...")
    df = generate_synthetic_dataset(n_samples=1200)
    print(f"      Label distribution:\n{df['label'].value_counts().to_string()}")

    # Also save dataset for inspection
    df.to_csv(os.path.join(ARTIFACTS_DIR, "training_data.csv"), index=False)
    print("      Saved training_data.csv")

    # 2. Prepare features
    FEATURE_COLS = [
        "skills_count", "relevant_skills_count", "experience_years",
        "project_complexity_score", "education_score", "has_ml_skills",
        "has_cloud_skills", "has_web_skills", "certifications_count", "text_length_score"
    ]
    X = df[FEATURE_COLS].values
    y = df["label"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)  # Weak=0/1/2 based on alphabetical

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print(f"\n[2/5] Train/Test split: {len(X_train)} / {len(X_test)}")

    # 3. Train models
    print("\n[3/5] Training models...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results = {}

    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=10, min_samples_leaf=3,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    rf.fit(X_train_s, y_train)
    rf_cv = cross_val_score(rf, X_train_s, y_train, cv=cv, scoring="f1_weighted")
    rf_pred = rf.predict(X_test_s)
    results["RandomForest"] = {
        "model": rf,
        "cv_mean": rf_cv.mean(),
        "cv_scores": rf_cv.tolist(),
        "preds": rf_pred,
        "accuracy": accuracy_score(y_test, rf_pred),
        "f1": f1_score(y_test, rf_pred, average="weighted"),
        "precision": precision_score(y_test, rf_pred, average="weighted", zero_division=0),
        "recall": recall_score(y_test, rf_pred, average="weighted", zero_division=0),
        "cm": confusion_matrix(y_test, rf_pred).tolist(),
        "feature_importances": dict(zip(FEATURE_COLS, rf.feature_importances_.tolist())),
    }
    print(f"      RandomForest  — CV F1: {rf_cv.mean():.4f} ± {rf_cv.std():.4f} | Test Acc: {results['RandomForest']['accuracy']:.4f}")

    if has_xgb:
        xgb = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="mlogloss",
            random_state=42, n_jobs=-1
        )
        xgb.fit(X_train_s, y_train, eval_set=[(X_test_s, y_test)], verbose=False)
        xgb_cv = cross_val_score(xgb, X_train_s, y_train, cv=cv, scoring="f1_weighted")
        xgb_pred = xgb.predict(X_test_s)
        results["XGBoost"] = {
            "model": xgb,
            "cv_mean": xgb_cv.mean(),
            "cv_scores": xgb_cv.tolist(),
            "preds": xgb_pred,
            "accuracy": accuracy_score(y_test, xgb_pred),
            "f1": f1_score(y_test, xgb_pred, average="weighted"),
            "precision": precision_score(y_test, xgb_pred, average="weighted", zero_division=0),
            "recall": recall_score(y_test, xgb_pred, average="weighted", zero_division=0),
            "cm": confusion_matrix(y_test, xgb_pred).tolist(),
            "feature_importances": dict(zip(FEATURE_COLS, xgb.feature_importances_.tolist())),
        }
        print(f"      XGBoost       — CV F1: {xgb_cv.mean():.4f} ± {xgb_cv.std():.4f} | Test Acc: {results['XGBoost']['accuracy']:.4f}")

    # 4. Select best model
    best_name = max(results, key=lambda k: results[k]["cv_mean"])
    best = results[best_name]
    print(f"\n[4/5] Best model: {best_name} (CV F1={best['cv_mean']:.4f})")

    print("\n      Classification Report:")
    print(classification_report(y_test, best["preds"], target_names=le.classes_))

    # 5. Save artifacts
    print("\n[5/5] Saving artifacts...")
    with open(os.path.join(ARTIFACTS_DIR, "best_model.pkl"), "wb") as f:
        pickle.dump(best["model"], f)
    with open(os.path.join(ARTIFACTS_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(ARTIFACTS_DIR, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)

    metrics = {
        "model_name": best_name,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(best["accuracy"], 4),
        "f1_score": round(best["f1"], 4),
        "precision": round(best["precision"], 4),
        "recall": round(best["recall"], 4),
        "cv_scores": [round(s, 4) for s in best["cv_scores"]],
        "cv_mean": round(best["cv_mean"], 4),
        "confusion_matrix": best["cm"],
        "feature_importances": {k: round(v, 4) for k, v in best["feature_importances"].items()},
        "classes": le.classes_.tolist(),
        "trained_at": datetime.now().isoformat(),
        "all_models": {
            name: {
                "accuracy": round(r["accuracy"], 4),
                "f1_score": round(r["f1"], 4),
                "cv_mean": round(r["cv_mean"], 4),
            }
            for name, r in results.items()
        }
    }
    with open(os.path.join(ARTIFACTS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Model : {best_name}")
    print(f"  Accuracy : {best['accuracy']*100:.2f}%")
    print(f"  F1 Score : {best['f1']*100:.2f}%")
    print(f"  Precision: {best['precision']*100:.2f}%")
    print(f"  Recall   : {best['recall']*100:.2f}%")
    print(f"  Artifacts saved to: {ARTIFACTS_DIR}")
    print(f"{'='*60}")
    return metrics


if __name__ == "__main__":
    train()
