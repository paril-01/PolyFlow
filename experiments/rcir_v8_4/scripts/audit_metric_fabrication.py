#!/usr/bin/env python3
"""
RCIR v8.4 — Metric Fabrication Auditor (RULE 0 & RULE 0.1).

Statically inspects all benchmark runners and evaluators:
- Prohibits hardcoded empirical metric outcomes (completion_rate = ..., avg_turns = ..., exact_rec = ..., etc.)
- Enforces that empirical metrics are derived from raw observation counts or distributions
- Allows threshold constants, configuration weights, and test fixtures explicitly marked FIXTURE_ONLY
"""

import ast
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Forbidden patterns in evaluation scripts representing fabricated results
SUSPICIOUS_PATTERNS = [
    r'completion_rate\s*=\s*0\.\d+',
    r'turn_reduction\s*=\s*0\.\d+',
    r'avg_turns\s*=\s*\d+',
    r'exact_rec\s*=\s*0\.\d+',
    r'relaxed_rec\s*=\s*0\.\d+',
    r'precision_among_resolved\s*=\s*0\.\d+',
    r'wrong_exact_rate\s*=\s*0\.\d+',
    r'ambiguity_rate\s*=\s*0\.\d+',
]


class MetricFabricationAuditor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: list[str] = []

    def visit_Assign(self, node: ast.Assign):
        # Inspect target variables
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                # Check if assigning a literal float/int to a metric result name outside test fixtures
                if name in ("completion_rate", "avg_turns", "turn_reduction_pct", "token_reduction_pct", "wrong_exact"):
                    if isinstance(node.value, (ast.Constant, ast.Num)):
                        # If inside test file or explicitly marked fixture, allow
                        if "test" not in self.filename.lower() and "fixture" not in self.filename.lower():
                            self.violations.append(
                                f"{self.filename}:{node.lineno}: Suspicious hardcoded empirical assignment to '{name}' = {ast.dump(node.value)}"
                            )
        self.generic_visit(node)


def audit_directory(dir_path: Path) -> list[str]:
    violations = []
    if not dir_path.exists():
        return violations

    for py_file in dir_path.rglob("*.py"):
        # Ignore audit script itself
        if py_file.name == "audit_metric_fabrication.py":
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        # AST Inspection
        try:
            tree = ast.parse(content, filename=str(py_file))
            auditor = MetricFabricationAuditor(str(py_file.relative_to(REPO_ROOT)))
            auditor.visit(tree)
            violations.extend(auditor.violations)
        except Exception as e:
            violations.append(f"{py_file}: Parse error: {e}")

        # Regex Inspection for forbidden hardcoded metric assignments
        for pat in SUSPICIOUS_PATTERNS:
            for m in re.finditer(pat, content):
                # Check if commented
                line_start = content.rfind("\n", 0, m.start()) + 1
                line = content[line_start:content.find("\n", m.start())].strip()
                if not line.startswith("#") and "FIXTURE" not in line and "threshold" not in line.lower() and "test" not in str(py_file).lower():
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}: Hardcoded metric pattern '{m.group(0)}' in line: {line}")

    return violations


def main():
    print("=" * 70)
    print("RCIR v8.4 — Metric Fabrication Audit (RULE 0 & RULE 0.1)")
    print("=" * 70)

    target_dirs = [
        REPO_ROOT / "experiments" / "rcir_v8_4" / "scripts",
        REPO_ROOT / "rcir" / "src",
    ]

    all_violations = []
    for td in target_dirs:
        print(f"Auditing directory: {td.relative_to(REPO_ROOT)}...")
        all_violations.extend(audit_directory(td))

    if all_violations:
        print(f"\n[FAILED] Detected {len(all_violations)} metric fabrication violations:")
        for v in all_violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print(f"\n[PASSED] 0 metric fabrication violations detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
