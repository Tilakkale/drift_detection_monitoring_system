from pathlib import Path
import joblib
import json
import numpy as np
import pandas as pd

WORKSPACE_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = WORKSPACE_DIR / "backend" / "models"


def _model_path(machine_id: int):
    return MODELS_DIR / f"isolation_forest_machine_{machine_id}.pkl"


def _baseline_path(machine_id: int):
    return MODELS_DIR / f"baseline_machine_{machine_id}.json"


def load_model(machine_id: int):
    path = _model_path(machine_id)
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def load_baseline(machine_id: int):
    path = _baseline_path(machine_id)
    if not path.exists():
        raise FileNotFoundError(f"Baseline not found: {path}")
    with open(path, "r") as fh:
        return json.load(fh)


def infer_batch(machine_id: int, batch_df: pd.DataFrame):
    model = load_model(machine_id)
    baseline = load_baseline(machine_id)

    # Ensure feature counts match
    if batch_df.shape[1] != baseline.get("feature_count"):
        raise ValueError("Batch feature count does not match trained model baseline")

    # Anomaly detection
    preds = model.predict(batch_df.values)
    scores = model.decision_function(batch_df.values)
    anomalies = [int(i) for i, p in enumerate(preds) if p == -1]

    anomaly_summary = {
        "row_count": int(batch_df.shape[0]),
        "anomaly_count": int(len(anomalies)),
        "anomaly_fraction": float(len(anomalies) / max(1, batch_df.shape[0])),
        "anomaly_rows": anomalies,
    }

    # Drift detection (simple baseline mean vs batch mean z-score check)
    baseline_mean = np.array(baseline.get("mean"))
    baseline_std = np.array(baseline.get("std"))
    batch_mean = batch_df.mean(axis=0).to_numpy()

    # Avoid zero std
    baseline_std[baseline_std == 0] = 1e-6

    z_scores = np.abs((batch_mean - baseline_mean) / baseline_std)
    drifted_features = [
        {"feature": f"feature_{i+1}", "z_score": float(z_scores[i])}
        for i in range(len(z_scores)) if z_scores[i] > 3.0
    ]

    drift_summary = {
        "feature_count": int(batch_df.shape[1]),
        "drifted_feature_count": len(drifted_features),
        "drifted_features": drifted_features,
    }

    return {
        "anomaly": anomaly_summary,
        "drift": drift_summary,
    }
