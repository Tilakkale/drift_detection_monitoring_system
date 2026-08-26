from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import subprocess
import sys

router = APIRouter()

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
DATASET_DIR = WORKSPACE_ROOT / "dataset" / "ServerMachineDataset"
MODELS_DIR = WORKSPACE_ROOT / "backend" / "models"


def _evaluation_path(machine_id: int) -> Path:
    for candidate in [
        MODELS_DIR / f"evaluation_machine_{machine_id}.json",
        MODELS_DIR / f"eval_machine_{machine_id}.json",
    ]:
        if candidate.exists():
            return candidate
    return MODELS_DIR / f"evaluation_machine_{machine_id}.json"


@router.get("/evaluation/{machine_id}")
def get_evaluation(machine_id: int):
    path = _evaluation_path(machine_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    with open(path, "r") as fh:
        return json.load(fh)


@router.get("/evaluation/{machine_id}/status")
def get_evaluation_status(machine_id: int):
    from backend.scripts.evaluate_models import check_dataset_readiness

    readiness = check_dataset_readiness(DATASET_DIR, machine_id)
    return {
        "machine_id": machine_id,
        "status": readiness["status"],
        "data_present": readiness["data_present"],
        "labels_present": readiness["labels_present"],
        "test_files": readiness["test_files"],
        "label_files": readiness["label_files"],
    }


@router.post("/evaluation/{machine_id}/run")
def run_evaluation(machine_id: int):
    repo_root = Path(__file__).resolve().parents[4]
    cmd = [sys.executable, str(repo_root / "backend" / "scripts" / "evaluate_models.py"), "--machine", str(machine_id)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=repo_root)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc.stderr}")

    path = _evaluation_path(machine_id)
    if not path.exists():
        raise HTTPException(status_code=500, detail="Evaluation finished but result file missing")
    with open(path, "r") as fh:
        result = json.load(fh)

    result["readiness"] = {
        "machine_id": machine_id,
        "status": "ready" if result.get("status") == "ok" else "skipped",
        "data_present": True,
        "labels_present": True,
    }
    return result
