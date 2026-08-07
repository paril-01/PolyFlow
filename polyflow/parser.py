"""
PolyFlow (.poly) File Parser and AST Generator.

Parses .poly files containing multi-language code blocks, contracts, schemas,
links, merge strategies, error maps, rationales, decisions, and audit entries.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class LanguageBlock:
    language: str
    tag: str = "default"
    code: str = ""
    start_line: int = 0
    end_line: int = 0

@dataclass
class SchemaBlock:
    name: str
    fields: Dict[str, str] = field(default_factory=dict)

@dataclass
class LinkDirective:
    target_path: str
    selector: Optional[str] = None
    alias: Optional[str] = None

@dataclass
class ErrorMapping:
    language: str
    rules: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GovernanceBlock:
    block_type: str  # contract, rationale, decision, audit, ledger, standard, config, secret, env
    target: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""

@dataclass
class PolyAST:
    filepath: str = ""
    contract: Dict[str, Any] = field(default_factory=dict)
    schemas: Dict[str, SchemaBlock] = field(default_factory=dict)
    links: List[LinkDirective] = field(default_factory=list)
    language_blocks: List[LanguageBlock] = field(default_factory=list)
    merge_strategy: Dict[str, Any] = field(default_factory=dict)
    error_maps: List[ErrorMapping] = field(default_factory=list)
    rationales: List[GovernanceBlock] = field(default_factory=list)
    decisions: List[GovernanceBlock] = field(default_factory=list)
    audits: List[GovernanceBlock] = field(default_factory=list)
    standards: List[GovernanceBlock] = field(default_factory=list)
    raw_content: str = ""

class PolyParser:
    LANG_BLOCK_REGEX = re.compile(r"^@([a-zA-Z0-9_\-]+)(?:\[([a-zA-Z0-9_\-:]+)\])?\s*$")
    SCHEMA_REGEX = re.compile(r"^@schema\s+([a-zA-Z0-9_]+)\s*$")
    LINK_REGEX = re.compile(r"^@link\s+([^\s:]+)(?:::(.+?))?(?:\s+as\s+([a-zA-Z0-9_]+))?\s*$")
    MERGE_REGEX = re.compile(r"^@merge\s*(.*)$")
    ERROR_MAP_REGEX = re.compile(r"^@error-map(?:\s+language=[\"']?([a-zA-Z0-9_\-]+)[\"']?)?\s*$")
    RATIONALE_REGEX = re.compile(r"^@rationale(?:\s+for=[\"']?([^\s\"']+)[\"']?)?\s*$")
    DECISION_REGEX = re.compile(r"^@decision(?:\s+for=[\"']?([^\s\"']+)[\"']?)?\s*$")
    STANDARD_REGEX = re.compile(r"^@standard(?:\s+language=[\"']?([a-zA-Z0-9_\-]+)[\"']?)?\s*$")

    RESERVED_DIRECTIVES = {
        "contract", "schema", "link", "merge", "error-map", "rationale",
        "decision", "audit", "ledger", "standard", "config", "secret", "env", "end"
    }

    KNOWN_LANGUAGES = {
        "python", "py", "typescript", "ts", "javascript", "js", "node",
        "java", "go", "golang", "ruby", "rust", "cpp", "c", "csharp", "cs"
    }

    def parse_text(self, content: str, filepath: str = "inline.poly") -> PolyAST:
        ast = PolyAST(filepath=filepath, raw_content=content)
        lines = content.splitlines()

        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                i += 1
                continue

            if line.startswith("@"):
                # Handle Directives
                if line.startswith("@contract"):
                    i, data = self._parse_key_value_block(lines, i + 1)
                    ast.contract.update(data)
                    continue

                elif line.startswith("@schema"):
                    match = self.SCHEMA_REGEX.match(line)
                    schema_name = match.group(1) if match else "UnnamedSchema"
                    i, fields = self._parse_schema_block(lines, i + 1)
                    ast.schemas[schema_name] = SchemaBlock(name=schema_name, fields=fields)
                    continue

                elif line.startswith("@link"):
                    match = self.LINK_REGEX.match(line)
                    if match:
                        target = match.group(1)
                        selector = match.group(2)
                        alias = match.group(3)
                        ast.links.append(LinkDirective(target_path=target, selector=selector, alias=alias))
                    i += 1
                    continue

                elif line.startswith("@merge"):
                    match = self.MERGE_REGEX.match(line)
                    attr_str = match.group(1) if match else ""
                    attrs = self._parse_attributes(attr_str)
                    i, sub_data = self._parse_key_value_block(lines, i + 1)
                    attrs.update(sub_data)
                    ast.merge_strategy = attrs
                    continue

                elif line.startswith("@error-map"):
                    match = self.ERROR_MAP_REGEX.match(line)
                    lang = match.group(1) if match else "generic"
                    i, rules, metadata = self._parse_error_map_block(lines, i + 1)
                    ast.error_maps.append(ErrorMapping(language=lang, rules=rules, metadata=metadata))
                    continue

                elif line.startswith("@rationale"):
                    match = self.RATIONALE_REGEX.match(line)
                    target = match.group(1)
                    i, data, raw_text = self._parse_governance_block(lines, i + 1)
                    ast.rationales.append(GovernanceBlock(block_type="rationale", target=target, data=data, raw_text=raw_text))
                    continue

                elif line.startswith("@decision"):
                    match = self.DECISION_REGEX.match(line)
                    target = match.group(1)
                    i, data, raw_text = self._parse_governance_block(lines, i + 1)
                    ast.decisions.append(GovernanceBlock(block_type="decision", target=target, data=data, raw_text=raw_text))
                    continue

                elif line.startswith("@audit") or line.startswith("@ledger"):
                    btype = "audit" if line.startswith("@audit") else "ledger"
                    i, data, raw_text = self._parse_governance_block(lines, i + 1)
                    ast.audits.append(GovernanceBlock(block_type=btype, data=data, raw_text=raw_text))
                    continue

                elif line.startswith("@standard"):
                    match = self.STANDARD_REGEX.match(line)
                    lang = match.group(1) if match else "universal"
                    i, data, raw_text = self._parse_governance_block(lines, i + 1)
                    ast.standards.append(GovernanceBlock(block_type="standard", target=lang, data=data, raw_text=raw_text))
                    continue

                # Check if it's a language block (e.g. @python[service])
                match = self.LANG_BLOCK_REGEX.match(line)
                if match:
                    lang_name = match.group(1).lower()
                    tag_name = match.group(2) if match.group(2) else "default"

                    if lang_name in self.KNOWN_LANGUAGES or lang_name not in self.RESERVED_DIRECTIVES:
                        start_l = i + 1
                        i, code_lines = self._parse_code_until_end(lines, i + 1)
                        end_l = i
                        code_content = "\n".join(code_lines)
                        ast.language_blocks.append(
                            LanguageBlock(
                                language=lang_name,
                                tag=tag_name,
                                code=code_content,
                                start_line=start_l,
                                end_line=end_l
                            )
                        )
                        continue

            i += 1

        return ast

    def parse_file(self, filepath: str) -> PolyAST:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return self.parse_text(content, filepath=filepath)

    def _parse_code_until_end(self, lines: List[str], start_index: int):
        i = start_index
        code_lines = []
        n = len(lines)
        while i < n:
            raw_line = lines[i]
            if raw_line.strip() == "@end":
                return i + 1, code_lines
            code_lines.append(raw_line)
            i += 1
        return i, code_lines

    def _parse_key_value_block(self, lines: List[str], start_index: int):
        i = start_index
        data = {}
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            if line == "@end":
                return i + 1, data
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                # Parse strings, numbers, booleans, lists
                if v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
                    data[k] = items
                elif v.lower() == "true":
                    data[k] = True
                elif v.lower() == "false":
                    data[k] = False
                elif v.isdigit():
                    data[k] = int(v)
                else:
                    data[k] = v.strip("\"'")
            i += 1
        return i, data

    def _parse_schema_block(self, lines: List[str], start_index: int):
        i = start_index
        fields = {}
        n = len(lines)
        while i < n:
            line = lines[i].strip()
            if line == "@end":
                return i + 1, fields
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
            i += 1
        return i, fields

    def _parse_error_map_block(self, lines: List[str], start_index: int):
        i = start_index
        rules = {}
        metadata = {}
        n = len(lines)
        current_pattern = None
        current_text_lines = []

        while i < n:
            line = lines[i].strip()
            if line == "@end":
                if current_pattern:
                    rules[current_pattern] = "\n".join(current_text_lines).strip()
                return i + 1, rules, metadata

            if "→" in line or "->" in line:
                if current_pattern:
                    rules[current_pattern] = "\n".join(current_text_lines).strip()
                    current_text_lines = []

                sep = "→" if "→" in line else "->"
                parts = line.split(sep, 1)
                current_pattern = parts[0].strip()
                val = parts[1].strip()
                if val:
                    current_text_lines.append(val)
            elif ":" in line and not current_pattern:
                k, v = line.split(":", 1)
                metadata[k.strip()] = v.strip().strip("\"'")
            elif current_pattern:
                current_text_lines.append(line)
            i += 1

        if current_pattern:
            rules[current_pattern] = "\n".join(current_text_lines).strip()

        return i, rules, metadata

    def _parse_governance_block(self, lines: List[str], start_index: int):
        i = start_index
        data = {}
        raw_lines = []
        n = len(lines)

        while i < n:
            line = lines[i].strip()
            if line == "@end":
                return i + 1, data, "\n".join(raw_lines)

            raw_lines.append(lines[i])

            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                if v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
                    data[k] = items
                else:
                    data[k] = v.strip("\"'")
            i += 1

        return i, data, "\n".join(raw_lines)

    def _parse_attributes(self, attr_str: str) -> Dict[str, Any]:
        result = {}
        matches = re.findall(r'([a-zA-Z0-9_\-]+)=(?:["\']([^"\']+)["\']|([^\s]+))', attr_str)
        for k, v1, v2 in matches:
            val = v1 if v1 else v2
            result[k] = val
        return result
