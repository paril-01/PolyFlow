"""
PolyFlow IDE Guards Engine (Guards A through F).

Enforces code standards, blocks alien imports, ghost file writing, dynamic code execution,
rationale contradictions, and secret leakage.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from polyflow.parser import PolyAST, LanguageBlock

@dataclass
class GuardViolation:
    guard_name: str
    guard_id: str
    line_number: int
    message: str
    severity: str = "error"

class PolyGuardEngine:
    DYNAMIC_CODE_PATTERNS = [
        (re.compile(r"\beval\s*\("), "Guard D: Dynamic Code Prevention — Use of 'eval()' is forbidden."),
        (re.compile(r"\bexec\s*\("), "Guard D: Dynamic Code Prevention — Use of 'exec()' is forbidden."),
        (re.compile(r"__import__\s*\(\s*['\"]os['\"]\s*\)\.system"), "Guard D: Dynamic Code Prevention — Dynamic OS system calls forbidden.")
    ]

    GHOST_FILE_PATTERNS = [
        (re.compile(r"open\s*\([^)]*['\"][wa\+]"), "Guard C: Ghost File Prevention — Direct file-writing forbidden. Use structured audit logs via ctx.emit_audit()."),
        (re.compile(r"fs\.writeFileSync\s*\(\s*['\"][^'\"]+\.(txt|log)"), "Guard C: Ghost File Prevention — Direct file-writing forbidden in Node.js.")
    ]

    SECRET_LEAK_PATTERNS = [
        (re.compile(r"print\s*\([^)]*(api_key|password|secret|token)\s*\=\s*"), "Guard F: Secret Leakage Prevention — Secret printing forbidden. Use ctx.secrets.get()."),
        (re.compile(r"console\.log\s*\([^)]*(api_key|password|secret|token)"), "Guard F: Secret Leakage Prevention — Secret logging forbidden.")
    ]

    def inspect_ast(self, ast: PolyAST) -> List[GuardViolation]:
        violations = []

        # Extract allowed imports from @standard
        allowed_imports = set()
        forbidden_patterns = set()

        for std in ast.standards:
            if "allowed_imports" in std.data:
                allowed_imports.update(std.data["allowed_imports"])
            if "forbidden_patterns" in std.data:
                forbidden_patterns.update(std.data["forbidden_patterns"])

        for block in ast.language_blocks:
            lines = block.code.splitlines()
            for idx, line in enumerate(lines, start=block.start_line):
                line_str = line.strip()

                # Guard A: Import Allowlist & Forbidden Patterns
                if allowed_imports and (line_str.startswith("import ") or line_str.startswith("from ")):
                    module_name = self._extract_import_module(line_str)
                    if module_name and module_name not in allowed_imports:
                        violations.append(
                            GuardViolation(
                                guard_name="Guard A: Import Allowlist",
                                guard_id="GUARD_A",
                                line_number=idx,
                                message=f"Import '{module_name}' is not in allowed imports list: {list(allowed_imports)}"
                            )
                        )

                for f_pat in forbidden_patterns:
                    if f_pat in line_str:
                        violations.append(
                            GuardViolation(
                                guard_name="Guard A: Forbidden Pattern",
                                guard_id="GUARD_A",
                                line_number=idx,
                                message=f"Pattern '{f_pat}' violates @standard specification."
                            )
                        )

                # Guard C: Ghost File Prevention
                for pattern, msg in self.GHOST_FILE_PATTERNS:
                    if pattern.search(line_str):
                        violations.append(
                            GuardViolation(
                                guard_name="Guard C: Ghost File Prevention",
                                guard_id="GUARD_C",
                                line_number=idx,
                                message=msg
                            )
                        )

                # Guard D: Dynamic Code Detection
                for pattern, msg in self.DYNAMIC_CODE_PATTERNS:
                    if pattern.search(line_str):
                        violations.append(
                            GuardViolation(
                                guard_name="Guard D: Dynamic Code Prevention",
                                guard_id="GUARD_D",
                                line_number=idx,
                                message=msg
                            )
                        )

                # Guard F: Secret Leakage Prevention
                for pattern, msg in self.SECRET_LEAK_PATTERNS:
                    if pattern.search(line_str):
                        violations.append(
                            GuardViolation(
                                guard_name="Guard F: Secret Leakage",
                                guard_id="GUARD_F",
                                line_number=idx,
                                message=msg
                            )
                        )

        # Guard E: Rationale Contradiction Check
        for rat in ast.rationales:
            target = rat.target
            rationale_text = rat.raw_text.lower()
            if "not" in rationale_text or "rejected" in rationale_text:
                # Check if code contains rejected options
                rejected_items = rat.data.get("rejected_reasons", {})
                if isinstance(rejected_items, dict):
                    for rej_key in rejected_items.keys():
                        for block in ast.language_blocks:
                            if rej_key.lower() in block.code.lower():
                                violations.append(
                                    GuardViolation(
                                        guard_name="Guard E: Rationale Contradiction",
                                        guard_id="GUARD_E",
                                        line_number=block.start_line,
                                        message=f"Code uses '{rej_key}', which contradicts @rationale for '{target}'."
                                    )
                                )

        return violations

    def _extract_import_module(self, line: str) -> str:
        parts = line.split()
        if parts[0] == "import":
            return parts[1].split(".")[0].split(",")[0]
        elif parts[0] == "from":
            return parts[1].split(".")[0]
        return ""
