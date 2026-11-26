"""Compatibility entrypoint for the explicit, non-overwriting study CLI.

Historical baked-in task hints and automatic architecture selection are removed.
Run with --help; an exact repository, commit, public tasks, gold and output are
required. Old receipts remain immutable historical records.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.run_retrieval_study import main

if __name__ == "__main__":
    raise SystemExit(main())
