import joblib
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from pathlib import Path

router = APIRouter()

# Load all 3 models at startup
MODEL_DIR = Path(__file__).resolve().parents[3] / "models"

def load_models():
    models = {}
    for machine_id in [1, 2, 3]:
        path = MODEL_DIR / f"isolation_forest_machine_{machine_id}.pkl"
        if path.exists():
            models[machine_id] = joblib.load(path)
    return models

MODELS = load_models()


class TelemetryBatch(BaseModel):
    machine_id: int
    data: List[List[float]]


@router.post("/monitor")
def monitor_telemetry(batch: TelemetryBatch):
    machine_id = batch.machine_id

    if machine_id not in MODELS:
        raise HTTPException(
            status_code=404,
            detail=f"No model found for machine {machine_id}"
        )

    model = MODELS[machine_id]
    X = np.array(batch.data)

    if X.shape[1] != 38:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 38 features, got {X.shape[1]}"
        )

    # Predictions
    predictions = model.predict(X)
    scores = model.decision_function(X)

    anomalies = []
    for idx, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:
            anomalies.append({
                "row_index": idx,
                "anomaly_score": round(float(score), 4),
                "severity": (
                    "high" if score < -0.1
                    else "medium"
                )
            })

    return {
        "machine_id": machine_id,
        "total_rows": len(X),
        "anomaly_count": len(anomalies),
        "anomaly_fraction": round(len(anomalies) / len(X), 4),
        "anomalies": anomalies
    }


@router.get("/monitor/status")
def monitor_status():
    return {
        "loaded_machines": list(MODELS.keys()),
        "total_models": len(MODELS)
    }