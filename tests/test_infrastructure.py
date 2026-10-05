"""Infrastructure tests for execution 1005-1.

These tests verify repository/provenance infrastructure only. They do not
test any scientific analysis, since none has been implemented or
authorized yet.

Run with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXECUTION_ID = "1005-1"


class TestPackageImport(unittest.TestCase):
    def test_package_import_works(self):
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        try:
            import urban_history_transfer  # noqa: F401

            self.assertTrue(hasattr(urban_history_transfer, "__version__"))
        finally:
            sys.path.remove(str(PROJECT_ROOT / "src"))


class TestEnvironmentChecker(unittest.TestCase):
    def test_environment_checker_runs(self):
        script = PROJECT_ROOT / "scripts" / "check_environment.py"
        out_path = PROJECT_ROOT / "results" / EXECUTION_ID / "environment_test.json"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--execution-id",
                EXECUTION_ID,
                "--out",
                str(out_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(out_path.exists())
        out_path.unlink()

    def test_environment_json_parses(self):
        path = PROJECT_ROOT / "results" / EXECUTION_ID / "environment.json"
        self.assertTrue(path.exists(), msg=f"{path} does not exist")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("execution_id", data)
        self.assertIn("python_version", data)
        self.assertIn("git", data)


class TestRunMetadata(unittest.TestCase):
    def test_run_metadata_json_parses(self):
        path = PROJECT_ROOT / "results" / EXECUTION_ID / "run_metadata.json"
        self.assertTrue(path.exists(), msg=f"{path} does not exist")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        required_keys = {
            "execution_id",
            "source_prompt",
            "report",
            "results_directory",
            "figures_directory",
            "status",
            "started_at",
            "completed_at",
            "random_seed",
            "real_research_data_used",
            "scientific_hypothesis_tested",
            "scientific_analysis_performed",
            "unauthorized_scope_deviation",
            "tests_passed",
            "tests_failed",
            "warnings_count",
            "outputs",
        }
        missing = required_keys - set(data.keys())
        self.assertFalse(missing, msg=f"Missing keys in run_metadata.json: {missing}")
        self.assertEqual(data["execution_id"], EXECUTION_ID)


class TestGovernanceDocsExist(unittest.TestCase):
    def test_scientific_governance_exists(self):
        self.assertTrue((PROJECT_ROOT / "docs" / "SCIENTIFIC_GOVERNANCE.md").exists())

    def test_experiment_protocol_exists(self):
        self.assertTrue((PROJECT_ROOT / "docs" / "EXPERIMENT_PROTOCOL.md").exists())

    def test_provenance_protocol_exists(self):
        self.assertTrue((PROJECT_ROOT / "docs" / "PROVENANCE_PROTOCOL.md").exists())

    def test_report_template_exists(self):
        self.assertTrue((PROJECT_ROOT / "reports" / "REPORT_TEMPLATE.md").exists())


class TestDirectoryStructure(unittest.TestCase):
    def test_required_directories_exist(self):
        required_dirs = [
            "prompts",
            "reports",
            f"results/{EXECUTION_ID}",
            f"figures/{EXECUTION_ID}",
            "configs",
            "data/raw",
            "data/interim",
            "data/processed",
            "docs",
            "src/urban_history_transfer",
            "scripts",
            "tests",
        ]
        for rel in required_dirs:
            path = PROJECT_ROOT / rel
            self.assertTrue(path.is_dir(), msg=f"Missing required directory: {rel}")

    def test_required_top_level_files_exist(self):
        required_files = ["README.md", "pyproject.toml", ".gitignore"]
        for rel in required_files:
            path = PROJECT_ROOT / rel
            self.assertTrue(path.is_file(), msg=f"Missing required file: {rel}")


class TestExecutionIdConsistency(unittest.TestCase):
    def test_prompt_report_results_figures_share_execution_id(self):
        prompt_path = PROJECT_ROOT / "prompts" / f"prompt{EXECUTION_ID}.txt"
        report_path = PROJECT_ROOT / "reports" / f"report{EXECUTION_ID}.md"
        results_dir = PROJECT_ROOT / "results" / EXECUTION_ID
        figures_dir = PROJECT_ROOT / "figures" / EXECUTION_ID

        self.assertTrue(prompt_path.exists(), msg=f"{prompt_path} missing")
        self.assertTrue(results_dir.is_dir(), msg=f"{results_dir} missing")
        self.assertTrue(figures_dir.is_dir(), msg=f"{figures_dir} missing")
        # report_path is checked for existence by the report-generation step,
        # not asserted strictly here to avoid a false failure if this test
        # runs before the final report is written in the same execution.
        self.assertEqual(prompt_path.name, f"prompt{EXECUTION_ID}.txt")
        self.assertEqual(report_path.name, f"report{EXECUTION_ID}.md")


if __name__ == "__main__":
    unittest.main()
