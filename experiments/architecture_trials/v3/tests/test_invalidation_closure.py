from pathlib import Path
from experiments.architecture_trials.v3.r2_versioned_evidence.vest_lite import VestLiteEvidenceStore, FactFreshness


def test_transitive_cycle_and_unrelated_file(tmp_path):
    for name, parent in [("A", "C"), ("B", "A"), ("C", "B"), ("Unrelated", None)]:
        (tmp_path / f"{name}.php").write_text(f"<?php\nclass {name}" + (f" extends {parent}" if parent else "") + " {\n public function method() {}\n}\n")
    store = VestLiteEvidenceStore(tmp_path)
    store.scan_repository()
    store.invalidate_file("A.php")
    assert all(f.freshness == FactFreshness.STALE for f in store.facts.values() if f.file_path != "Unrelated.php")
    assert all(f.freshness == FactFreshness.FRESH for f in store.facts.values() if f.file_path == "Unrelated.php")


def test_reparse_removes_deleted_symbols(tmp_path):
    file = tmp_path / "source.py"
    file.write_text("def previous():\n return 1\n")
    store = VestLiteEvidenceStore(tmp_path)
    store.scan_repository()
    file.write_text("def replacement():\n return 2\n")
    assert store.retrieve("previous")["spans_count"] == 0
    store.index_file("source.py")
    assert not any(f.symbol_name == "previous" for f in store.facts.values())
    assert store.retrieve("replacement")["spans_count"] == 1
    file.unlink()
    store.index_file("source.py")
    assert not store.facts


def test_prefix_sibling_path_rejected(tmp_path):
    root = tmp_path / "repo"
    sibling = tmp_path / "repo-other"
    root.mkdir()
    sibling.mkdir()
    (sibling / "secret.py").write_text("secret = 1")
    store = VestLiteEvidenceStore(root)
    assert store._safe_read_file("../repo-other/secret.py") is None
