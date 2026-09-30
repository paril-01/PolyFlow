"""
PolyFlow Standalone Language Interpreter.

Parses, validates, and interprets .poly files containing multi-language contracts,
schemas, standards, architectural decisions, and executable language cells.
"""

import os
import re
import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from polyflow.parser import LanguageBlock
from polyflow.runtime import PolyCellRuntime, CellResult


@dataclass
class PolyContract:
    feature_id: str = ""
    owner: str = ""
    classification: str = "internal"
    approvers: List[str] = field(default_factory=list)
    timeout_ms: int = 5000
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchemaField:
    name: str
    type_str: str
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolySchema:
    name: str
    fields: Dict[str, SchemaField] = field(default_factory=dict)


@dataclass
class PolyDecision:
    for_feature: str
    variable: str
    choice: str


@dataclass
class PolyStandard:
    language: str
    allowed_imports: List[str] = field(default_factory=list)


@dataclass
class PolyFile:
    path: str
    contracts: List[PolyContract] = field(default_factory=list)
    schemas: Dict[str, PolySchema] = field(default_factory=dict)
    decisions: List[PolyDecision] = field(default_factory=list)
    standards: List[PolyStandard] = field(default_factory=list)
    blocks: List[LanguageBlock] = field(default_factory=list)


class PolyInterpreter:
    """Standalone interpreter for PolyFlow (.poly) files."""

    def __init__(self, runtime: Optional[PolyCellRuntime] = None):
        self.runtime = runtime or PolyCellRuntime(fast_native_mode=False)

    def parse_source(self, content: str, filepath: str = "<memory>") -> PolyFile:
        """Parse raw .poly source text into a structured PolyFile AST."""
        poly_file = PolyFile(path=filepath)
        lines = content.splitlines()
        idx = 0
        n = len(lines)

        while idx < n:
            line = lines[idx].strip()

            # Ignore empty lines and comments
            if not line or line.startswith("#"):
                idx += 1
                continue

            # 1. @contract block
            if line.startswith("@contract"):
                block_lines = []
                idx += 1
                while idx < n and not lines[idx].strip().startswith("@end"):
                    block_lines.append(lines[idx])
                    idx += 1
                idx += 1  # Skip @end
                contract_yaml = "\n".join(block_lines)
                try:
                    data = yaml.safe_load(contract_yaml) or {}
                except Exception:
                    # Fallback key-value parser
                    data = {}
                    for cl in block_lines:
                        if ":" in cl:
                            k, v = cl.split(":", 1)
                            data[k.strip()] = v.strip().strip('"').strip("'")
                poly_file.contracts.append(PolyContract(
                    feature_id=data.get("feature_id", "UNKNOWN"),
                    owner=data.get("owner", "engineering"),
                    classification=data.get("classification", "internal"),
                    approvers=data.get("approvers", []),
                    timeout_ms=int(data.get("timeout_ms", 5000)),
                    raw_data=data
                ))
                continue

            # 2. @schema <Name> block
            if line.startswith("@schema"):
                parts = line.split()
                schema_name = parts[1] if len(parts) > 1 else "AnonymousSchema"
                schema = PolySchema(name=schema_name)
                idx += 1
                while idx < n and not lines[idx].strip().startswith("@end"):
                    sline = lines[idx].strip()
                    if sline and not sline.startswith("#") and ":" in sline:
                        fname, fdef = [x.strip() for x in sline.split(":", 1)]
                        # Parse constraints like string<format:email> or string<min:8,max:128>
                        constraints = {}
                        m = re.search(r'<([^>]+)>', fdef)
                        if m:
                            c_str = m.group(1)
                            base_type = fdef[:m.start()].strip()
                            for c_item in c_str.split(","):
                                if ":" in c_item:
                                    ck, cv = c_item.split(":", 1)
                                    constraints[ck.strip()] = cv.strip()
                        else:
                            base_type = fdef
                        schema.fields[fname] = SchemaField(name=fname, type_str=base_type, constraints=constraints)
                    idx += 1
                idx += 1  # Skip @end
                poly_file.schemas[schema_name] = schema
                continue

            # 3. @decision for="<target>"
            if line.startswith("@decision"):
                m = re.search(r'for=["\']([^"\']+)["\']', line)
                target = m.group(1) if m else "general"
                block_lines = []
                idx += 1
                while idx < n and not lines[idx].strip().startswith("@end"):
                    block_lines.append(lines[idx])
                    idx += 1
                idx += 1
                dec_yaml = "\n".join(block_lines)
                try:
                    data = yaml.safe_load(dec_yaml) or {}
                except Exception:
                    data = {}
                poly_file.decisions.append(PolyDecision(
                    for_feature=target,
                    variable=str(data.get("variable", "")),
                    choice=str(data.get("choice", ""))
                ))
                continue

            # 4. @standard language="<lang>"
            if line.startswith("@standard"):
                m = re.search(r'language=["\']([^"\']+)["\']', line)
                lang = m.group(1) if m else "unknown"
                block_lines = []
                idx += 1
                while idx < n and not lines[idx].strip().startswith("@end"):
                    block_lines.append(lines[idx])
                    idx += 1
                idx += 1
                std_yaml = "\n".join(block_lines)
                try:
                    data = yaml.safe_load(std_yaml) or {}
                except Exception:
                    data = {}
                poly_file.standards.append(PolyStandard(
                    language=lang,
                    allowed_imports=data.get("allowed_imports", [])
                ))
                continue

            # 5. Language code cells: @<language>[<tag>]
            m_lang = re.match(r'@([a-zA-Z0-9_-]+)\[([a-zA-Z0-9_.-]+)\]', line)
            if m_lang:
                lang = m_lang.group(1)
                tag = m_lang.group(2)
                code_lines = []
                idx += 1
                while idx < n and not lines[idx].strip().startswith("@end"):
                    code_lines.append(lines[idx])
                    idx += 1
                idx += 1  # Skip @end
                poly_file.blocks.append(LanguageBlock(
                    language=lang,
                    tag=tag,
                    code="\n".join(code_lines)
                ))
                continue

            idx += 1

        return poly_file

    def parse_file(self, file_path: str | Path) -> PolyFile:
        """Parse a .poly file from disk."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"PolyFlow file not found: {path}")
        content = path.read_text(encoding="utf-8")
        return self.parse_source(content, filepath=str(path))

    def execute_file(
        self,
        file_path: str | Path,
        payload: Optional[Dict[str, Any]] = None,
        context_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute all code cells in a .poly file."""
        poly_file = self.parse_file(file_path)
        payload = payload or {}
        context_vars = context_vars or {}

        timeout_ms = 5000
        if poly_file.contracts:
            timeout_ms = poly_file.contracts[0].timeout_ms

        results = []
        all_success = True

        for block in poly_file.blocks:
            res = self.runtime.execute_cell(
                block=block,
                payload=payload,
                timeout_ms=timeout_ms,
                context_vars=context_vars
            )
            results.append({
                "language": res.language,
                "tag": res.tag,
                "status": res.status,
                "output": res.output,
                "error": res.error,
                "execution_time_ms": res.execution_time_ms
            })
            if res.status != "success":
                all_success = False

        return {
            "file": poly_file.path,
            "contracts_count": len(poly_file.contracts),
            "schemas_count": len(poly_file.schemas),
            "cells_executed": len(results),
            "status": "success" if all_success else "failed",
            "results": results
        }
