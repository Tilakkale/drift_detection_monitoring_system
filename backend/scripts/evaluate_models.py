import argparse
import json
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

WORKDIR = Path(__file__).resolve().parents[2]
DATASET_DIR = WORKDIR / "dataset" / "ServerMachineDataset"
MODELS_DIR = WORKDIR / "backend" / "models"


def load_dataset_files(folder: Path, machine_id: int):
    pattern = f"machine-{machine_id}-*.txt"
    files = sorted(folder.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No files found for machine {machine_id} in {folder}"
        )

    frames = [pd.read_csv(file, header=None) for file in files]
    return pd.concat(frames, ignore_index=True)


def load_labels(dataset_dir: Path, machine_id: int) -> Optional[pd.Series]:

    for label_dir in [
        dataset_dir / "test_label",
        dataset_dir / "train_label",
    ]:

        if not label_dir.exists():
            continue

        files = sorted(label_dir.glob(f"machine-{machine_id}-*.txt"))

        if not files:
            continue

        frames = [pd.read_csv(file, header=None) for file in files]
        labels = pd.concat(frames, ignore_index=True)

        if labels.empty:
            return None

        return labels.iloc[:, 0]

    return None


def check_dataset_readiness(dataset_dir: Path, machine_id: int):
    test_dir = dataset_dir / "test"
    label_dirs = [dataset_dir / "test_label", dataset_dir / "train_label"]

    feature_files = sorted(test_dir.glob(f"machine-{machine_id}-*.txt")) if test_dir.exists() else []
    label_files = []
    for label_dir in label_dirs:
        if label_dir.exists():
            label_files.extend(sorted(label_dir.glob(f"machine-{machine_id}-*.txt")))

    data_present = bool(feature_files)
    labels_present = bool(label_files)

    if not data_present and not labels_present:
        status = "missing_inputs"
    elif not data_present:
        status = "missing_test_data"
    elif not labels_present:
        status = "missing_labels"
    else:
        status = "ready"

    return {
        "machine_id": machine_id,
        "status": status,
        "data_present": data_present,
        "labels_present": labels_present,
        "test_files": [str(path) for path in feature_files],
        "label_files": [str(path) for path in label_files],
    }


def parse_args(argv=None):

    parser = argparse.ArgumentParser(
        description="Evaluate Isolation Forest Model"
    )

    parser.add_argument(
        "--machine",
        dest="machine_ids",
        action="append",
        type=int,
        default=None,
        help="Machine IDs to evaluate",
    )

    return parser.parse_args(argv)


def evaluate_machine(machine_id):

    model_path = MODELS_DIR / f"isolation_forest_machine_{machine_id}.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    readiness = check_dataset_readiness(DATASET_DIR, machine_id)
    if readiness["status"] != "ready":
        print(
            f"Dataset readiness for Machine {machine_id}: {readiness['status']}"
        )
        result = {
            "machine_id": machine_id,
            "status": "skipped",
            "message": readiness["status"],
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "confusion_matrix": [],
            "readiness": readiness,
        }
        output_file = MODELS_DIR / f"evaluation_machine_{machine_id}.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=4)
        return result

    X_test = load_dataset_files(
        DATASET_DIR / "test",
        machine_id,
    ).values

    y_true_series = load_labels(
        DATASET_DIR,
        machine_id,
    )

    if y_true_series is None:

        print(f"No labels found for Machine {machine_id}")

        result = {
            "machine_id": machine_id,
            "status": "skipped",
            "message": "No labels found",
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "confusion_matrix": [],
            "readiness": readiness,
        }

        output_file = (
            MODELS_DIR
            / f"evaluation_machine_{machine_id}.json"
        )

        with open(output_file, "w") as f:
            json.dump(result, f, indent=4)

        return result

    y_true = y_true_series.values

    n = min(len(X_test), len(y_true))

    X_test = X_test[:n]
    y_true = y_true[:n]

    model = joblib.load(model_path)

    raw_predictions = model.predict(X_test)

    y_pred = (raw_predictions == -1).astype(int)

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    cm = confusion_matrix(
        y_true,
        y_pred,
    )

    total_samples = len(y_true)

    true_anomalies = int(sum(y_true))

    predicted_anomalies = int(sum(y_pred))

    print("\n" + "=" * 50)
    print(f"Machine {machine_id} Evaluation")
    print("=" * 50)

    print(f"Accuracy            : {accuracy:.4f}")
    print(f"Precision           : {precision:.4f}")
    print(f"Recall              : {recall:.4f}")
    print(f"F1 Score            : {f1:.4f}")

    print(f"Total Samples       : {total_samples}")
    print(f"True Anomalies      : {true_anomalies}")
    print(f"Predicted Anomalies : {predicted_anomalies}")

    print("\nConfusion Matrix")
    print(cm)

    result = {

        "machine_id": machine_id,

        "accuracy": round(float(accuracy), 4),

        "precision": round(float(precision), 4),

        "recall": round(float(recall), 4),

        "f1_score": round(float(f1), 4),

        "total_samples": total_samples,

        "true_anomalies": true_anomalies,

        "predicted_anomalies": predicted_anomalies,

        "confusion_matrix": cm.tolist(),

        "status": "ok",
    }

    output_file = (
        MODELS_DIR
        / f"evaluation_machine_{machine_id}.json"
    )

    with open(output_file, "w") as f:
        json.dump(result, f, indent=4)

    return result


if __name__ == "__main__":

    args = parse_args()

    machine_ids = args.machine_ids or [1, 2, 3]

    for machine in machine_ids:
        evaluate_machine(machine)