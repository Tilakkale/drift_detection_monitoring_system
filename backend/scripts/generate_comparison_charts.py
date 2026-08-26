"""Generate comparison charts for model evaluation results."""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

WORKDIR = Path(__file__).resolve().parents[2]
MODELS_DIR = WORKDIR / "backend" / "models"
COMPARISON_FILE = MODELS_DIR / "comparison_all_machines.json"


def generate_charts():
    if not COMPARISON_FILE.exists():
        print(f"Comparison file not found: {COMPARISON_FILE}")
        return

    with open(COMPARISON_FILE) as f:
        data = json.load(f)

    models_data = {}
    for machine_id, machine_data in data.items():
        if isinstance(machine_data, dict):
            if "accuracy" in machine_data:
                model_name = "isolation_forest"
                if model_name not in models_data:
                    models_data[model_name] = []
                models_data[model_name].append({
                    "machine": f"Machine {machine_id}",
                    "accuracy": machine_data.get("accuracy", 0),
                    "precision": machine_data.get("precision", 0),
                    "recall": machine_data.get("recall", 0),
                    "f1_score": machine_data.get("f1_score", 0),
                })
            else:
                for model_name, model_info in machine_data.items():
                    if isinstance(model_info, dict) and "metrics" in model_info:
                        metrics = model_info.get("metrics", {})
                        if metrics and metrics.get("accuracy") is not None:
                            if model_name not in models_data:
                                models_data[model_name] = []
                            models_data[model_name].append({
                                "machine": f"Machine {machine_id}",
                                "accuracy": metrics.get("accuracy", 0),
                                "precision": metrics.get("precision", 0),
                                "recall": metrics.get("recall", 0),
                                "f1_score": metrics.get("f1_score", 0),
                            })

    if not models_data:
        print("No model data found")
        return

    model_names = list(models_data.keys())
    machines = [f"Machine {i}" for i in [1, 2, 3]]

    # Chart 1: Model Accuracy Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(model_names))
    width = 0.25

    for i, machine in enumerate(machines):
        accuracies = []
        for model_name in model_names:
            acc = next(
                (m["accuracy"] for m in models_data[model_name] if m["machine"] == machine),
                0
            )
            accuracies.append(acc)
        ax.bar(x + (i * width), accuracies, width, label=machine)

    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Model Accuracy Comparison Across Machines", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels([name.replace("_", " ").title() for name in model_names])
    ax.legend()
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(MODELS_DIR / "model_accuracy_comparison.png", dpi=100, bbox_inches="tight")
    print("✅ Saved: model_accuracy_comparison.png")
    plt.close()

    # Chart 2: F1 Score Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, machine in enumerate(machines):
        f1_scores = []
        for model_name in model_names:
            f1 = next(
                (m["f1_score"] for m in models_data[model_name] if m["machine"] == machine),
                0
            )
            f1_scores.append(f1)
        ax.bar(x + (i * width), f1_scores, width, label=machine)

    ax.set_ylabel("F1 Score", fontsize=12)
    ax.set_title("Model F1 Score Comparison Across Machines", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width)
    ax.set_xticklabels([name.replace("_", " ").title() for name in model_names])
    ax.legend()
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(MODELS_DIR / "model_f1_comparison.png", dpi=100, bbox_inches="tight")
    print("✅ Saved: model_f1_comparison.png")
    plt.close()

    # Chart 3: All Metrics for Best Model (Isolation Forest)
    if "isolation_forest" in models_data:
        fig, ax = plt.subplots(figsize=(12, 6))
        metrics_names = ["Accuracy", "Precision", "Recall", "F1 Score"]
        x = np.arange(len(metrics_names))
        width = 0.25

        for i, machine in enumerate(machines):
            iso_forest = next(
                (m for m in models_data["isolation_forest"] if m["machine"] == machine),
                None
            )
            if iso_forest:
                values = [
                    iso_forest["accuracy"],
                    iso_forest["precision"],
                    iso_forest["recall"],
                    iso_forest["f1_score"],
                ]
                ax.bar(x + (i * width), values, width, label=machine)

        ax.set_ylabel("Score", fontsize=12)
        ax.set_title("🏆 Isolation Forest - All Metrics Across Machines", fontsize=14, fontweight="bold")
        ax.set_xticks(x + width)
        ax.set_xticklabels(metrics_names)
        ax.legend()
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(MODELS_DIR / "isolation_forest_all_metrics.png", dpi=100, bbox_inches="tight")
        print("✅ Saved: isolation_forest_all_metrics.png")
        plt.close()

    # Chart 4: Average Performance by Model
    fig, ax = plt.subplots(figsize=(12, 6))
    metrics_names = ["Accuracy", "Precision", "Recall", "F1 Score"]
    x = np.arange(len(model_names))
    width = 0.2

    for i, metric_key in enumerate(["accuracy", "precision", "recall", "f1_score"]):
        avg_values = []
        for model_name in model_names:
            avg = np.mean([m[metric_key] for m in models_data[model_name]])
            avg_values.append(avg)
        ax.bar(x + (i * width), avg_values, width, label=metrics_names[i])

    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Average Model Performance (All Metrics & Machines)", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels([name.replace("_", " ").title() for name in model_names])
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(MODELS_DIR / "model_average_performance.png", dpi=100, bbox_inches="tight")
    print("✅ Saved: model_average_performance.png")
    plt.close()

    print("\n📊 All comparison charts generated successfully!")


if __name__ == "__main__":
    generate_charts()
