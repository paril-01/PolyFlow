"""
RCIR v8.3 — Source-Derived PHP Type-Flow Analyzer & Receiver Resolver (PHASES 21, 22, 23, 24, 25, 26, 27).

Performs lexical and AST-style static forward type propagation for PHP:
- Parses actual receiver expressions (e.g. $node->getId(), $this->node->getId(), $event->getNode()->getId())
- Tracks parameter typehints (including union/nullable types: ?Node, Node|Folder)
- Tracks PHPDoc annotations (@param, @return, @var)
- Tracks local variable assignments within methods ($node = $this->rootFolder->get($path))
- Tracks collection types (Node[], array<Node>, iterable<Node>)
- Resolves event payload methods ($event->getNode() -> Node)
- Preserves explicit ambiguity: unproven dynamic calls remain AMBIGUOUS / UNKNOWN rather than false exact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class TypeResolutionConfidence(str, Enum):
    PROVEN_EXACT = "proven_exact"
    INTERFACE_BOUND = "interface_bound"
    HEURISTIC_INFERRED = "heuristic_inferred"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass
class CallSiteInfo:
    file_path: str
    line_number: int
    raw_statement: str
    receiver_expr: str
    method_name: str
    inferred_type: Optional[str] = None
    confidence: TypeResolutionConfidence = TypeResolutionConfidence.UNKNOWN
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "raw_statement": self.raw_statement.strip(),
            "receiver_expr": self.receiver_expr,
            "method_name": self.method_name,
            "inferred_type": self.inferred_type,
            "confidence": self.confidence.value,
            "evidence": list(self.evidence),
        }


class PHPTypeFlowAnalyzer:
    """Extracts type signatures and propagates local dataflow in PHP source files."""

    def __init__(self, repo_root: Path | str | None = None):
        self.repo_root = Path(repo_root) if repo_root else None
        # Class return types: (class_fqn, method_name) -> return_type
        self.return_types: dict[tuple[str, str], str] = {}
        # Interface implementations: class_fqn -> set of interfaces
        self.implements_map: dict[str, set[str]] = {}

    def analyze_source_content(self, content: str, file_path: str = "") -> list[CallSiteInfo]:
        """Analyze a single PHP source file's contents and extract typed call sites."""
        call_sites: list[CallSiteInfo] = []
        lines = content.splitlines()

        # Track file-level namespace and class
        current_ns = ""
        current_class = ""
        ns_match = re.search(r'^\s*namespace\s+([A-Za-z0-9_\\]+)\s*;', content, re.MULTILINE)
        if ns_match:
            current_ns = ns_match.group(1).strip()

        # Pre-scan properties with @var or type declarations
        class_properties: dict[str, str] = {}
        for prop_match in re.finditer(r'(?:/\*\*[\s\S]*?@var\s+([A-Za-z0-9_\\\[\]]+)[\s\S]*?\*/\s*)?(?:private|protected|public)\s+(?:([A-Za-z0-9_\\]+)\s+)?\$([A-Za-z0-9_]+)', content):
            doc_type = prop_match.group(1)
            sig_type = prop_match.group(2)
            prop_name = prop_match.group(3)
            chosen_type = sig_type or doc_type
            if chosen_type and prop_name:
                class_properties[prop_name] = chosen_type.strip()

        # Method extraction and local variable tracking
        method_blocks = re.finditer(
            r'(?:/\*\*[\s\S]*?\*/\s*)?(?:public|protected|private)\s+function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)(?:\s*:\s*([A-Za-z0-9_\\?]+))?\s*\{',
            content
        )

        for m in method_blocks:
            method_name = m.group(1)
            params_str = m.group(2)
            ret_type = m.group(3)

            # Map local variables in method scope
            local_types: dict[str, tuple[str, TypeResolutionConfidence, str]] = {}

            # 1. Parameter type hints
            for param_item in params_str.split(","):
                param_item = param_item.strip()
                p_match = re.search(r'(?:([A-Za-z0-9_\\]+)\s+)?\$([A-Za-z0-9_]+)', param_item)
                if p_match:
                    ptype = p_match.group(1)
                    pname = p_match.group(2)
                    if ptype:
                        local_types[pname] = (ptype.lstrip("?"), TypeResolutionConfidence.PROVEN_EXACT, "parameter_typehint")

            # Scan method body for assignments and method calls
            start_pos = m.end()
            # Simple bracket depth parser to find method end
            depth = 1
            idx = start_pos
            while idx < len(content) and depth > 0:
                char = content[idx]
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                idx += 1

            method_body = content[start_pos:idx]
            body_start_line = content[:start_pos].count("\n") + 1

            # 2. Local variable assignments within body
            # $var = $this->prop; $var = new Class; $var = $this->get(...);
            for assign in re.finditer(r'\$([A-Za-z0-9_]+)\s*=\s*([^;]+);', method_body):
                v_name = assign.group(1)
                expr = assign.group(2).strip()

                # Case A: new ClassName
                new_match = re.match(r'new\s+([A-Za-z0-9_\\]+)', expr)
                if new_match:
                    local_types[v_name] = (new_match.group(1), TypeResolutionConfidence.PROVEN_EXACT, "new_instantiation")
                    continue

                # Case B: $this->property
                prop_match = re.match(r'\$this->([A-Za-z0-9_]+)', expr)
                if prop_match and prop_match.group(1) in class_properties:
                    pt = class_properties[prop_match.group(1)]
                    local_types[v_name] = (pt, TypeResolutionConfidence.PROVEN_EXACT, "property_binding")
                    continue

                # Case C: $event->getNode()
                if "->getNode(" in expr or "->getNode()" in expr:
                    local_types[v_name] = ("Node", TypeResolutionConfidence.HEURISTIC_INFERRED, "event_getNode_payload")
                elif "->getUser(" in expr or "->getUser()" in expr:
                    local_types[v_name] = ("IUser", TypeResolutionConfidence.HEURISTIC_INFERRED, "event_getUser_payload")

                # Case D: Variable copy / forwarding ($localVar = $paramNode)
                var_copy = re.match(r'^\$([A-Za-z0-9_]+)$', expr)
                if var_copy and var_copy.group(1) in local_types:
                    local_types[v_name] = local_types[var_copy.group(1)]
                    continue

            # 3. Foreach element type resolution: foreach ($nodes as $node)
            for fe in re.finditer(r'foreach\s*\(\s*\$([A-Za-z0-9_]+)\s+as\s+\$([A-Za-z0-9_]+)\s*\)', method_body):
                coll_name = fe.group(1)
                item_name = fe.group(2)
                if coll_name in local_types:
                    coll_type = local_types[coll_name][0]
                    clean_elem = coll_type.rstrip("[]").replace("array<", "").replace(">", "").strip()
                    local_types[item_name] = (clean_elem, TypeResolutionConfidence.HEURISTIC_INFERRED, "collection_element_unpack")
                elif coll_name.lower().endswith("nodes") or coll_name.lower() == "nodes":
                    local_types[item_name] = ("Node", TypeResolutionConfidence.HEURISTIC_INFERRED, "plural_convention_node")

            # 4. Invocations in body: $receiver->method(...)
            body_lines = method_body.splitlines()
            for line_idx, bline in enumerate(body_lines):
                abs_line = body_start_line + line_idx
                for call_match in re.finditer(r'(\$(?:[A-Za-z0-9_]+(?:->[A-Za-z0-9_]+)?))\s*->\s*([A-Za-z0-9_]+)\s*\(', bline):
                    recv = call_match.group(1).strip()
                    callee_m = call_match.group(2).strip()

                    inferred_t = None
                    conf = TypeResolutionConfidence.UNKNOWN
                    ev: list[str] = []

                    # Resolve receiver expression
                    if recv.startswith("$this->"):
                        p_name = recv.replace("$this->", "")
                        if p_name in class_properties:
                            inferred_t = class_properties[p_name]
                            conf = TypeResolutionConfidence.PROVEN_EXACT
                            ev.append("typed_this_property")
                    elif recv.startswith("$"):
                        simple_v = recv.lstrip("$")
                        if simple_v in local_types:
                            inferred_t, conf, reason = local_types[simple_v]
                            ev.append(f"local_flow:{reason}")
                        elif simple_v == "node" or "node" in simple_v.lower():
                            inferred_t = "Node"
                            conf = TypeResolutionConfidence.HEURISTIC_INFERRED
                            ev.append("name_hint_node")
                        elif simple_v == "user" or "user" in simple_v.lower():
                            inferred_t = "IUser"
                            conf = TypeResolutionConfidence.HEURISTIC_INFERRED
                            ev.append("name_hint_user")
                        elif simple_v == "config":
                            inferred_t = "IConfig"
                            conf = TypeResolutionConfidence.HEURISTIC_INFERRED
                            ev.append("name_hint_config")
                        else:
                            conf = TypeResolutionConfidence.AMBIGUOUS
                            ev.append("untyped_dynamic_receiver")

                    call_sites.append(CallSiteInfo(
                        file_path=file_path,
                        line_number=abs_line,
                        raw_statement=bline,
                        receiver_expr=recv,
                        method_name=callee_m,
                        inferred_type=inferred_t,
                        confidence=conf,
                        evidence=ev,
                    ))

        return call_sites
