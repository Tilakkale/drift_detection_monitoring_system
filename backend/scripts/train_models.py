"""
Train three anomaly-detection models per machine and save models + evaluation.
Models: IsolationForest, OneClassSVM, LocalOutlierFactor (novelty)
Saves:
 - backend/models/<model>_machine_<id>.pkl
 - backend/models/eval_machine_<id>.json
 - backend/models/comparison_all_machines.json
"""

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

WORKDIR = Path(__file__).resolve().parents[2]
DATASET = WORKDIR / "dataset" / "ServerMachineDataset"
MODELS_DIR = WORKDIR / "backend" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_CONSTRUCTORS = {
    "isolation_forest": lambda: IsolationForest(n_estimators=100, contamination=0.05, random_state=42),
    "oneclass_svm": lambda: OneClassSVM(gamma='scale', nu=0.05),
    "local_outlier_factor": lambda: LocalOutlierFactor(novelty=True, contamination=0.05)
}


def load_concat(folder: Path, pattern: str):
    if not folder.exists():
        return None
    files = sorted(folder.glob(pattern))
    if not files:
        return None
    frames = [pd.read_csv(f, header=None) for f in files]
    return pd.concat(frames, ignore_index=True)


def load_labels(dataset_dir: Path, machine_id: int) -> Optional[pd.Series]:
    for label_dir in [dataset_dir / "test_label", dataset_dir / "train_label"]:
        if not label_dir.exists():
            continue
        files = sorted(label_dir.glob(f"machine-{machine_id}-*.txt"))
        if not files:
            continue
        frames = [pd.read_csv(f, header=None) for f in files]
        if not frames:
            return None
        labels_df = pd.concat(frames, ignore_index=True)
        if labels_df.empty or labels_df.shape[1] == 0:
            return None
        return labels_df.iloc[:, 0]
    return None


def train_and_evaluate():
    summary_all = {}
    for machine_id in [1, 2, 3]:
        print(f"\n=== Machine {machine_id} ===")
        X_train_df = load_concat(DATASET / "train", f"machine-{machine_id}-*.txt")
        X_test_df = load_concat(DATASET / "test", f"machine-{machine_id}-*.txt")
        y_test_series = load_labels(DATASET, machine_id)

        if X_train_df is None:
            print(f"No training data for machine {machine_id}, skipping")
            continue

        X_train = X_train_df.values
        X_test = X_test_df.values if X_test_df is not None else None
        y_test = y_test_series.values if y_test_series is not None else None

        machine_summary = {}
        for name, ctor in MODEL_CONSTRUCTORS.items():
            model = ctor()
            print(f"Training {name}...")
            # LocalOutlierFactor with novelty=True supports fit
            # For OneClassSVM, subsample large training sets to speed up training
            if name == "oneclass_svm":
                max_samples = 2000
                if X_train.shape[0] > max_samples:
                    idx = np.random.choice(X_train.shape[0], max_samples, replace=False)
                    X_fit = X_train[idx]
                else:
                    X_fit = X_train
                model.fit(X_fit)
            elif name == "local_outlier_factor":
                # LOF can be expensive for large datasets (neighbor computations).
                max_samples_lof = 3000
                if X_train.shape[0] > max_samples_lof:
                    idx = np.random.choice(X_train.shape[0], max_samples_lof, replace=False)
                    X_fit = X_train[idx]
                else:
                    X_fit = X_train
                model.fit(X_fit)
            else:
                model.fit(X_train)

            model_path = MODELS_DIR / f"{name}_machine_{machine_id}.pkl"
            joblib.dump(model, model_path)
            print(f"Saved {model_path}")

            metrics = None
            if X_test is not None and y_test is not None:
                try:
                    pred = model.predict(X_test)
                except Exception as exc:
                    print(f"Prediction failed for {name} on machine {machine_id}: {exc}")
                    metrics = None
                else:
                    y_pred = (pred == -1).astype(int)
                    p = precision_score(y_test, y_pred, zero_division=0)
                    r = recall_score(y_test, y_pred, zero_division=0)
                    f1 = f1_score(y_test, y_pred, zero_division=0)
                    cm = confusion_matrix(y_test, y_pred).tolist()

                    metrics = {
                        "precision": round(float(p), 4),
                        "recall": round(float(r), 4),
                        "f1_score": round(float(f1), 4),
                        "confusion_matrix": cm,
                        "predicted_anomalies": int(y_pred.sum()),
                        "true_anomalies": int(y_test.sum()),
                        "total_samples": int(len(y_test))
                    }
                    print(f"Metrics for {name}: P={p:.4f} R={r:.4f} F1={f1:.4f}")
            else:
                print(f"No test labels for machine {machine_id}; skipping metric computation for {name}")

            machine_summary[name] = {
                "model_path": str(model_path),
                "metrics": metrics
            }

        # Save machine summary
        out_path = MODELS_DIR / f"evaluation_machine_{machine_id}.json"
        with open(out_path, "w") as fh:
            json.dump(machine_summary, fh, indent=2)
        summary_all[machine_id] = machine_summary

    # Save overall comparison
    overall_path = MODELS_DIR / "comparison_all_machines.json"
    with open(overall_path, "w") as fh:
        json.dump(summary_all, fh, indent=2)
    print(f"Saved comparison -> {overall_path}")


if __name__ == "__main__":
    train_and_evaluate()
