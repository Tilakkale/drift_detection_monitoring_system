import tempfile
import unittest
from pathlib import Path

from backend.scripts import evaluate_models, train_models


class TrainingEvaluationScriptTests(unittest.TestCase):
    def test_load_labels_returns_none_for_missing_label_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            self.assertIsNone(train_models.load_labels(dataset_dir, 1))

    def test_check_dataset_readiness_reports_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            status = evaluate_models.check_dataset_readiness(dataset_dir, 1)
            self.assertFalse(status["data_present"])
            self.assertFalse(status["labels_present"])
            self.assertEqual(status["status"], "missing_inputs")

    def test_parse_machine_args_supports_single_machine(self):
        args = evaluate_models.parse_args(["--machine", "2"])
        self.assertEqual(args.machine_ids, [2])


if __name__ == "__main__":
    unittest.main()
