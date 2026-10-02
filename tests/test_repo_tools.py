"""
Unit tests for RepoToolEnvironment in orchestrator/tools.py.
"""

import os
import shutil
import tempfile
import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orchestrator.tools import RepoToolEnvironment


class TestRepoTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="repo_tool_test_")
        self.repo_path = Path(self.test_dir)

        # Create sample files
        (self.repo_path / "src").mkdir()
        (self.repo_path / "src" / "main.py").write_text(
            "def calculate_total(items):\n    tax = 0.05\n    return sum(items) * (1 + tax)\n",
            encoding="utf-8"
        )
        (self.repo_path / "src" / "config.json").write_text(
            '{"version": "1.0.0", "name": "demo"}',
            encoding="utf-8"
        )
        self.env = RepoToolEnvironment(str(self.repo_path))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_inspect_file(self):
        content = self.env.inspect_file("src/main.py", start_line=1, end_line=2)
        self.assertIn("1: def calculate_total", content)
        self.assertIn("2:     tax = 0.05", content)
        self.assertNotIn("3: ", content)

    def test_inspect_file_bounds_and_errors(self):
        err = self.env.inspect_file("nonexistent.py")
        self.assertIn("ERROR: File not found", err)

        err_dir = self.env.inspect_file("src")
        self.assertIn("ERROR: Path is a directory", err_dir)

    def test_search_code(self):
        matches = self.env.search_code("tax")
        self.assertIn("src/main.py:2:", matches)
        self.assertIn("tax = 0.05", matches)

        no_matches = self.env.search_code("nonexistent_symbol")
        self.assertIn("No matches found", no_matches)

    def test_list_dir(self):
        listing = self.env.list_dir("src")
        self.assertIn("[FILE] main.py", listing)
        self.assertIn("[FILE] config.json", listing)

    def test_edit_file_and_diff_and_revert(self):
        # Apply edit
        res = self.env.edit_file("src/main.py", "tax = 0.05", "tax = 0.08")
        self.assertIn("SUCCESS: Modified src/main.py", res)

        # Check modified file
        content = self.env.inspect_file("src/main.py")
        self.assertIn("tax = 0.08", content)
        self.assertNotIn("tax = 0.05", content)

        # Check diff
        diff = self.env.get_git_diff()
        self.assertIn("-    tax = 0.05", diff)
        self.assertIn("+    tax = 0.08", diff)

        # Revert
        reverted = self.env.revert_changes()
        self.assertEqual(reverted, 1)

        # Check reverted file
        reverted_content = self.env.inspect_file("src/main.py")
        self.assertIn("tax = 0.05", reverted_content)
        self.assertNotIn("tax = 0.08", reverted_content)

        # Diff should now be empty
        self.assertEqual(self.env.get_git_diff(), "")

    def test_edit_file_validation(self):
        # Target string not found
        res = self.env.edit_file("src/main.py", "tax = 0.99", "tax = 0.10")
        self.assertIn("ERROR: Target string to replace was not found", res)

        # Add duplicate lines
        (self.repo_path / "dup.txt").write_text("hello\nhello\n", encoding="utf-8")
        res2 = self.env.edit_file("dup.txt", "hello", "world")
        self.assertIn("ERROR: Target string occurs 2 times", res2)

    def test_path_traversal_protection(self):
        with self.assertRaises(PermissionError):
            self.env.inspect_file("../../../outside.txt")

    def test_run_command(self):
        res = self.env.run_command("python -c \"print('Hello from Sandbox')\"")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("Hello from Sandbox", res["stdout"])


if __name__ == "__main__":
    unittest.main()
