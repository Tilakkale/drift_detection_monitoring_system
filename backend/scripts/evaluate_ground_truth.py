import joblib
import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay
)

DATASET_PATH = Path("dataset/ServerMachineDataset")


def load_test_data(machine_id):
    files = sorted(
        (DATASET_PATH / "test").glob(f"machine-{machine_id}-*.txt")
    )
    frames = [pd.read_csv(f, header=None) for f in files]
    return pd.concat(frames, ignore_index=True).values


def load_labels(machine_id):
    files = sorted(
        (DATASET_PATH / "test_label").glob(f"machine-{machine_id}-*.txt")
    )
    frames = [pd.read_csv(f, header=None) for f in files]
    return pd.concat(frames, ignore_index=True).iloc[:, 0].values


def evaluate_machine(machine_id):
    print(f"\n{'='*50}")
    print(f"Evaluating Machine {machine_id}")
    print(f"{'='*50}")

    X_test = load_test_data(machine_id)
    y_true = load_labels(machine_id)

    # Trim to same length
    min_len = min(len(X_test), len(y_true))
    X_test = X_test[:min_len]
    y_true = y_true[:min_len]

    # Load Isolation Forest
    model = joblib.load(
        f"isolation_forest_machine_{machine_id}.pkl"
    )

    # Predict — convert -1/1 to 1/0
    raw_pred = model.predict(X_test)
    y_pred = (raw_pred == -1).astype(int)

    # Metrics
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)

    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"Confusion Matrix:\n{cm}")

    # Save confusion matrix chart
    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Normal", "Anomaly"]
    )
    disp.plot(ax=ax, cmap="Blues")
    ax.set_title(f"Machine {machine_id} — Isolation Forest")
    plt.tight_layout()
    plt.savefig(f"confusion_matrix_machine_{machine_id}.png")
    plt.close()
    print(f"Saved: confusion_matrix_machine_{machine_id}.png")

    return {
        "machine_id": machine_id,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "total_samples": min_len,
        "true_anomalies": int(y_true.sum()),
        "predicted_anomalies": int(y_pred.sum())
    }


# Run all machines
all_results = []
for machine_id in [1, 2, 3]:
    try:
        result = evaluate_machine(machine_id)
        all_results.append(result)
    except Exception as e:
        print(f"Machine {machine_id} failed: {e}")

# Save results
with open("ground_truth_evaluation.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("\n✅ Saved: ground_truth_evaluation.json")

# F1 comparison chart
machine_ids = [r["machine_id"] for r in all_results]
f1_scores = [r["f1_score"] for r in all_results]
precisions = [r["precision"] for r in all_results]
recalls = [r["recall"] for r in all_results]

x = np.arange(len(machine_ids))
width = 0.25

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x - width, precisions, width, label="Precision", color="steelblue")
ax.bar(x, recalls, width, label="Recall", color="orange")
ax.bar(x + width, f1_scores, width, label="F1 Score", color="green")

ax.set_xlabel("Machine")
ax.set_ylabel("Score")
ax.set_title("Isolation Forest — Precision / Recall / F1 per Machine")
ax.set_xticks(x)
ax.set_xticklabels([f"Machine {m}" for m in machine_ids])
ax.legend()
ax.set_ylim(0, 1)
plt.tight_layout()
plt.savefig("model_evaluation_chart.png")
plt.close()
print("✅ Saved: model_evaluation_chart.png")