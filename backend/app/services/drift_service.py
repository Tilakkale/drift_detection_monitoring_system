from pathlib import Path
from scipy import stats
import pandas as pd
import numpy as np

WORKSPACE_DIR = Path(__file__).resolve().parents[3]
SERVER_MACHINE_DATASET = WORKSPACE_DIR / "dataset" / "ServerMachineDataset"


# ─── PSI ───────────────────────────────────────────────
def calculate_psi(expected, actual, buckets=10):
    expected_percents = np.histogram(
        expected, bins=buckets
    )[0] / len(expected)

    actual_percents = np.histogram(
        actual, bins=buckets
    )[0] / len(actual)

    psi = np.sum(
        (expected_percents - actual_percents) *
        np.log(
            (expected_percents + 0.0001) /
            (actual_percents + 0.0001)
        )
    )
    return round(float(psi), 4)


# ─── KS TEST ───────────────────────────────────────────
def calculate_ks_test(expected, actual):
    statistic, p_value = stats.ks_2samp(expected, actual)
    return {
        "ks_statistic": round(float(statistic), 4),
        "p_value": round(float(p_value), 6),
        "drift_detected": bool(p_value < 0.05)
    }


# ─── CLASSIFY ──────────────────────────────────────────
def classify_psi(psi: float):
    if psi > 0.25:
        return "significant"
    if psi > 0.1:
        return "moderate"
    return "no_drift"


# ─── LOAD DATA ─────────────────────────────────────────
def load_machine_data(machine_id: int, dataset_type: str = "test"):
    data_dir = SERVER_MACHINE_DATASET / dataset_type
    if not data_dir.exists():
        fallback_dir = SERVER_MACHINE_DATASET / "test"
        if fallback_dir.exists():
            data_dir = fallback_dir
        else:
            raise FileNotFoundError(
                f"Dataset directory not found: {data_dir}"
            )

    pattern = f"machine-{machine_id}-*.txt"
    files = sorted(data_dir.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No files found for machine {machine_id} in {dataset_type}"
        )

    frames = [pd.read_csv(f, header=None) for f in files]
    return pd.concat(frames, ignore_index=True)


# ─── LOAD GROUND TRUTH ─────────────────────────────────
def load_ground_truth(machine_id: int):
    label_dir = SERVER_MACHINE_DATASET / "test_label"
    pattern = f"machine-{machine_id}-*.txt"
    files = sorted(label_dir.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No label files found for machine {machine_id}"
        )

    frames = [pd.read_csv(f, header=None) for f in files]
    return pd.concat(frames, ignore_index=True).iloc[:, 0].values


# ─── DRIFT SCORES ──────────────────────────────────────
def calculate_drift_scores(
    expected_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    buckets: int = 10
):
    if expected_df.shape[1] != actual_df.shape[1]:
        raise ValueError(
            "Expected and actual must have same number of features"
        )

    results = []
    for idx in range(expected_df.shape[1]):
        expected_col = expected_df.iloc[:, idx].to_numpy()
        actual_col = actual_df.iloc[:, idx].to_numpy()

        # PSI
        psi = calculate_psi(expected_col, actual_col, buckets)

        # KS Test
        ks = calculate_ks_test(expected_col, actual_col)

        # Ensemble — both detectors must agree for high confidence
        signals = [
            psi > 0.25,
            ks["drift_detected"]
        ]
        high_confidence = sum(signals) >= 2

        results.append({
            "feature": f"feature_{idx + 1}",
            "psi_score": psi,
            "psi_status": classify_psi(psi),
            "ks_statistic": ks["ks_statistic"],
            "ks_p_value": ks["p_value"],
            "ks_drift": ks["drift_detected"],
            "high_confidence_drift": high_confidence,
            "detectors_agree": sum(signals)
        })

    return results


# ─── MAIN DRIFT ANALYSIS ───────────────────────────────
def analyze_machine_drift(machine_id: int = 1, buckets: int = 10):
    expected_df = load_machine_data(machine_id, "train")
    actual_df = load_machine_data(machine_id, "test")

    drift_results = calculate_drift_scores(
        expected_df, actual_df, buckets=buckets
    )

    average_psi = round(
        float(np.mean([r["psi_score"] for r in drift_results])), 4
    )

    high_confidence_count = sum(
        1 for r in drift_results if r["high_confidence_drift"]
    )

    drifted_count = sum(
        1 for r in drift_results if r["psi_status"] != "no_drift"
    )

    sorted_results = sorted(
        drift_results,
        key=lambda r: r["psi_score"],
        reverse=True
    )

    return {
        "machine_id": machine_id,
        "feature_count": expected_df.shape[1],
        "average_psi": average_psi,
        "drifted_feature_count": drifted_count,
        "high_confidence_drift_count": high_confidence_count,
        "drift_results": sorted_results
    }