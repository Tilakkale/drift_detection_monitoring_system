"""Update comparison file with evaluation results."""

import json
from pathlib import Path

WORKDIR = Path(__file__).resolve().parents[2]
MODELS_DIR = WORKDIR / "backend" / "models"

# Load evaluation results for each machine
comparison = {}
for machine_id in [1, 2, 3]:
    eval_file = MODELS_DIR / f"evaluation_machine_{machine_id}.json"
    if eval_file.exists():
        with open(eval_file) as f:
            eval_data = json.load(f)
        comparison[str(machine_id)] = eval_data
    else:
        print(f"Warning: {eval_file} not found")

if comparison:
    comparison_path = MODELS_DIR / "comparison_all_machines.json"
    with open(comparison_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"✅ Updated: {comparison_path}")
    print(f"Machines: {list(comparison.keys())}")
else:
    print("No evaluation files found")
