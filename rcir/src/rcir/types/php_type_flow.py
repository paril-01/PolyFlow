"""
RCIR v8.4 — Structured Lexical PHP Type-Flow Analyzer & Receiver Resolver (PHASES 26-35).

Features:
- Source-order forward data flow with Env(line) state tracking
- PHP import / `use` statement FQN resolution with alias support
- `$this` resolution against enclosing class hierarchy
- Scope stack (method, closure, foreach, catch, block)
- Control-flow branch join with union candidate sets
- Method return-type propagation and chained call decomposition ($event->getNode()->getId())
- Union, nullable, and intersection types (?Node, Node|Folder)
- PHPDoc type extraction (@param, @return, @var, array<Type>, Type[])
- Strict evidence provenance: NO guesswork based on variable names.
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
class TypeBinding:
    candidate_types: set[str]
    confidence: TypeResolutionConfidence
    evidence: list[str] = field(default_factory=list)

    @property
    def primary_type(self) -> Optional[str]:
        if not self.candidate_types:
            return None
        return sorted(list(self.candidate_types))[0]


@dataclass
class CallSiteInfo:
    file_path: str
    line_number: int
    raw_statement: str
    receiver_expr: str
    method_name: str
    inferred_type: Optional[str] = None
    candidate_types: list[str] = field(default_factory=list)
    confidence: TypeResolutionConfidence = TypeResolutionConfidence.UNKNOWN
    evidence: list[str] = field(default_factory=list)
    enclosing_class: str = ""
    enclosing_method: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "raw_statement": self.raw_statement.strip(),
            "receiver_expr": self.receiver_expr,
            "method_name": self.method_name,
            "inferred_type": self.inferred_type,
            "candidate_types": self.candidate_types,
            "confidence": self.confidence.value,
            "evidence": list(self.evidence),
            "enclosing_class": self.enclosing_class,
            "enclosing_method": self.enclosing_method,
        }


@dataclass
class ClassContext:
    namespace: str = ""
    class_name: str = ""
    parent_class: str = ""
    interfaces: list[str] = field(default_factory=list)
    properties: dict[str, TypeBinding] = field(default_factory=dict)
    use_map: dict[str, str] = field(default_factory=dict)

    @property
    def fqn(self) -> str:
        if not self.class_name:
            return ""
        if self.namespace:
            return f"{self.namespace}\\{self.class_name}".strip("\\")
        return self.class_name


class PHPTypeFlowAnalyzer:
    """Structured lexical type-flow analyzer with source-order forward propagation."""

    def __init__(self, repo_root: Path | str | None = None):
        self.repo_root = Path(repo_root) if repo_root else None
        # (class_fqn, method_name) -> return type binding
        self.method_summaries: dict[tuple[str, str], TypeBinding] = {}
        # Pre-seed standard Nextcloud contracts
        self._seed_standard_summaries()

    def _seed_standard_summaries(self) -> None:
        """Derive standard method return types dynamically from source when repo_root is available (Issue 31)."""
        # When running without repository, fallback to empty dictionary (no hardcoded contracts)
        self.method_summaries.clear()

    def _find_class_file(self, class_fqn: str) -> Optional[Path]:
        """Locate the PHP source file declaring class_fqn under repo_root."""
        if not self.repo_root:
            return None
        clean = class_fqn.strip().lstrip("\\")
        simple_name = clean.rsplit("\\", 1)[-1]

        # PSR-4 Nextcloud mappings
        candidates: list[Path] = []
        if clean.startswith("OCP\\"):
            rel_part = clean[4:].replace("\\", "/") + ".php"
            candidates.append(self.repo_root / "lib" / "public" / rel_part)
        elif clean.startswith("OC\\"):
            rel_part = clean[3:].replace("\\", "/") + ".php"
            candidates.append(self.repo_root / "lib" / "private" / rel_part)
        elif clean.startswith("OCA\\"):
            parts = clean[4:].split("\\")
            if len(parts) > 1:
                app_name = parts[0].lower()
                rel_part = "/".join(parts[1:]) + ".php"
                candidates.append(self.repo_root / "apps" / app_name / "lib" / rel_part)

        for c in candidates:
            if c.exists():
                return c

        # Fallback shallow/targeted search for simple_name.php
        try:
            for p in self.repo_root.glob(f"**/{simple_name}.php"):
                p_str = str(p).replace("\\", "/")
                if "/tests/" not in p_str and "/vendor/" not in p_str:
                    return p
        except Exception:
            pass
        return None

    def _derive_method_summary_from_source(self, class_fqn: str, method_name: str) -> Optional[TypeBinding]:
        """Derive method summary dynamically from source declarations and PHPDoc (Issue 31)."""
        if not self.repo_root:
            return None
        summary_key = (class_fqn, method_name)
        if summary_key in self.method_summaries:
            return self.method_summaries[summary_key]

        class_file = self._find_class_file(class_fqn)
        if not class_file or not class_file.exists():
            return None

        try:
            content = class_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        # Build class context for FQN resolution
        ctx = ClassContext()
        ctx.use_map = self.parse_use_statements(content)
        ns_m = re.search(r'^\s*namespace\s+([A-Za-z0-9_\\]+)\s*;', content, re.MULTILINE)
        if ns_m:
            ctx.namespace = ns_m.group(1).strip().lstrip("\\")

        # Search for method signature return type hint: function method(...) : ?Type
        pattern = re.compile(
            r'function\s+' + re.escape(method_name) + r'\s*\([^)]*\)\s*:\s*([A-Za-z0-9_\\?|&\[\]]+)',
            re.MULTILINE,
        )
        m = pattern.search(content)
        if m:
            ret_type_str = m.group(1).strip()
            parsed_types = self.parse_type_expression(ret_type_str, ctx)
            if parsed_types:
                binding = TypeBinding(parsed_types, TypeResolutionConfidence.PROVEN_EXACT, [f"source_return_type:{class_file.name}"])
                self.method_summaries[summary_key] = binding
                return binding

        # Search for PHPDoc @return preceding method
        doc_pattern = re.compile(
            r'/\*\*[\s\S]*?@return\s+([A-Za-z0-9_\\?|&\[\]]+)[\s\S]*?\*/\s*(?:(?:public|protected|private|static)\s+)*function\s+' + re.escape(method_name) + r'\b',
            re.MULTILINE,
        )
        doc_m = doc_pattern.search(content)
        if doc_m:
            ret_type_str = doc_m.group(1).strip()
            parsed_types = self.parse_type_expression(ret_type_str, ctx)
            if parsed_types:
                binding = TypeBinding(parsed_types, TypeResolutionConfidence.PROVEN_EXACT, [f"phpdoc_return_type:{class_file.name}"])
                self.method_summaries[summary_key] = binding
                return binding

        return None


    def parse_use_statements(self, content: str) -> dict[str, str]:
        """Resolve PHP `use` declarations into an alias -> FQN mapping (Phase 31)."""
        use_map: dict[str, str] = {}
        # Matches: use OCP\Files\Node; or use OCP\Files\Node as FileNode;
        pattern = re.compile(r'^\s*use\s+([A-Za-z0-9_\\]+)(?:\s+as\s+([A-Za-z0-9_]+))?\s*;', re.MULTILINE)
        for match in pattern.finditer(content):
            fqn = match.group(1).strip().lstrip("\\")
            alias = match.group(2).strip() if match.group(2) else fqn.rsplit("\\", 1)[-1]
            use_map[alias] = fqn
        return use_map

    def resolve_type_fqn(self, type_str: str, ctx: ClassContext) -> str:
        """Resolve a type identifier to its FQN using use_map, namespace, or native types."""
        if not type_str:
            return ""
        clean = type_str.strip().lstrip("?\\")
        # Handle arrays or collections
        if clean.endswith("[]"):
            base = self.resolve_type_fqn(clean[:-2], ctx)
            return f"{base}[]"
        if clean.startswith("array<") and clean.endswith(">"):
            base = self.resolve_type_fqn(clean[6:-1], ctx)
            return f"array<{base}>"
        # Check use map
        if clean in ctx.use_map:
            return ctx.use_map[clean]
        # Qualified with leading subnamespace
        first_part = clean.split("\\")[0]
        if first_part in ctx.use_map:
            rest = clean[len(first_part):]
            return f"{ctx.use_map[first_part]}{rest}"
        # Native PHP types
        if clean.lower() in ("string", "int", "integer", "bool", "boolean", "float", "array", "void", "object", "callable", "iterable", "mixed"):
            return clean.lower()
        # Default to current namespace if relative
        if ctx.namespace and "\\" not in clean:
            return f"{ctx.namespace}\\{clean}"
        return clean

    def parse_type_expression(self, raw_type: str, ctx: ClassContext) -> set[str]:
        """Parse union, nullable, or intersection types (Phase 32)."""
        if not raw_type:
            return set()
        types: set[str] = set()
        # Split on union '|' or intersection '&'
        parts = re.split(r'[|&]', raw_type)
        for p in parts:
            p = p.strip().lstrip("?")
            if p and p.lower() != "null":
                resolved = self.resolve_type_fqn(p, ctx)
                if resolved:
                    types.add(resolved)
        return types

    def analyze_source_content(self, content: str, file_path: str = "") -> list[CallSiteInfo]:
        """Analyze PHP source with source-order forward flow and environment tracking."""
        call_sites: list[CallSiteInfo] = []
        ctx = ClassContext()
        ctx.use_map = self.parse_use_statements(content)

        # Namespace
        ns_m = re.search(r'^\s*namespace\s+([A-Za-z0-9_\\]+)\s*;', content, re.MULTILINE)
        if ns_m:
            ctx.namespace = ns_m.group(1).strip().lstrip("\\")

        # Class declaration
        class_m = re.search(
            r'^\s*(?:abstract\s+|final\s+)?class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_\\]+))?(?:\s+implements\s+([^{]+))?',
            content,
            re.MULTILINE,
        )
        if class_m:
            ctx.class_name = class_m.group(1).strip()
            if class_m.group(2):
                ctx.parent_class = self.resolve_type_fqn(class_m.group(2).strip(), ctx)
            if class_m.group(3):
                for iface in class_m.group(3).split(","):
                    iface_clean = iface.strip()
                    if iface_clean:
                        ctx.interfaces.append(self.resolve_type_fqn(iface_clean, ctx))

        # Extract typed properties and PHPDoc @var
        for prop_m in re.finditer(
            r'(?:/\*\*[\s\S]*?@var\s+([A-Za-z0-9_\\|&?\[\]<>]+)[\s\S]*?\*/\s*)?(?:private|protected|public)\s+(?:([A-Za-z0-9_\\|&?]+)\s+)?\$([A-Za-z0-9_]+)',
            content,
        ):
            doc_type = prop_m.group(1)
            sig_type = prop_m.group(2)
            prop_name = prop_m.group(3)
            raw = sig_type or doc_type
            if raw and prop_name:
                cand = self.parse_type_expression(raw, ctx)
                conf = TypeResolutionConfidence.PROVEN_EXACT if sig_type else TypeResolutionConfidence.HEURISTIC_INFERRED
                ev = ["property_type_declaration" if sig_type else "property_phpdoc_var"]
                ctx.properties[prop_name] = TypeBinding(cand, conf, ev)

        # Parse methods with line spans (PHASE 35)
        method_pattern = re.compile(
            r'(?:public|protected|private)\s+(?:static\s+)?function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)(?:\s*:\s*([A-Za-z0-9_\\|&?]+))?\s*\{'
        )

        for m in method_pattern.finditer(content):
            enclosing_method_name = m.group(1)
            method_name = enclosing_method_name
            params_str = m.group(2)
            ret_type_str = m.group(3) or ""

            # Extract docblock immediately preceding method without backtracking
            docblock = ""
            pre_text = content[:m.start()].rstrip()
            if pre_text.endswith("*/"):
                doc_start = pre_text.rfind("/**")
                if doc_start != -1:
                    candidate_doc = pre_text[doc_start:]
                    if "class " not in candidate_doc and "function " not in candidate_doc:
                        docblock = candidate_doc

            # Register method summary
            if ret_type_str and ctx.fqn:
                ret_cand = self.parse_type_expression(ret_type_str, ctx)
                self.method_summaries[(ctx.fqn, method_name)] = TypeBinding(
                    ret_cand, TypeResolutionConfidence.PROVEN_EXACT, ["return_type_declaration"]
                )

            # Find matching closing brace for method body
            start_pos = m.end()
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

            # Build initial Environment for method: parameters + $this
            env: dict[str, TypeBinding] = {}
            if ctx.fqn:
                env["this"] = TypeBinding({ctx.fqn}, TypeResolutionConfidence.PROVEN_EXACT, ["this_receiver"])

            # Parse PHPDoc @param annotations
            doc_params: dict[str, str] = {}
            if docblock:
                for dp in re.finditer(r'@param\s+([A-Za-z0-9_\\|&?\[\]<>]+)\s+\$([A-Za-z0-9_]+)', docblock):
                    doc_params[dp.group(2)] = dp.group(1)

            # Parameters & Constructor Promotion (PHP 8, Phase 35)
            for p_item in params_str.split(","):
                p_item = p_item.strip()
                if not p_item:
                    continue
                promoted = bool(re.search(r'\b(private|protected|public)\b', p_item))
                p_m = re.search(r'(?:(?:private|protected|public)\s+)?(?:readonly\s+)?(?:([A-Za-z0-9_\\|&?]+)\s+)?\$([A-Za-z0-9_]+)', p_item)
                if p_m:
                    sig_t = p_m.group(1)
                    p_name = p_m.group(2)
                    raw_t = sig_t or doc_params.get(p_name)
                    if raw_t:
                        cand = self.parse_type_expression(raw_t, ctx)
                        conf = TypeResolutionConfidence.PROVEN_EXACT if sig_t else TypeResolutionConfidence.HEURISTIC_INFERRED
                        ev = [f"parameter_typehint:{p_name}" if sig_t else f"param_phpdoc:{p_name}"]
                        binding = TypeBinding(cand, conf, ev)
                        env[p_name] = binding
                        if promoted and method_name == "__construct":
                            ctx.properties[p_name] = binding

            # Line-by-line forward simulation (Phase 27, 28, 29, F07)
            # Forward simulation with normalized statements (Phase 27, 28, 29, F07, v8.5.1 CFG)
            body_lines = method_body.splitlines()
            current_env = dict(env)
            branch_stack: list[dict[str, Any]] = []
            closure_stack: list[dict[str, Any]] = []
            current_brace_depth = 0

            # Decompose lines into sequential statement units
            statement_units: list[tuple[int, str]] = []
            for line_idx, raw_line in enumerate(body_lines):
                l_no = body_start_line + line_idx
                stripped_line = raw_line.strip()
                if not stripped_line:
                    continue

                # Strip inline comments for statement normalization
                clean = re.sub(r'//.*$', '', stripped_line)
                clean = re.sub(r'/\*.*?\*/', '', clean).strip()
                if not clean:
                    continue

                # 1. Normalize } else { and } elseif (...) {
                norm = re.sub(r'}\s*(else\s*if\b|elseif\b|else\b)', r'}\n\1', clean)

                # 2. Normalize one-line branch with braces: if (...) { ... }
                ol_brace = re.match(r'^(if\s*\([^)]+\)\s*\{)(.+)(\})$', norm)
                if ol_brace:
                    norm = f"{ol_brace.group(1)}\n{ol_brace.group(2).strip()}\n{ol_brace.group(3)}"

                # 3. Normalize one-line guard without braces: if (...) return/throw;
                ol_guard = re.match(r'^(if\s*\([^)]+\))\s*(return\b[^;]*;|throw\b[^;]*;)$', norm)
                if ol_guard:
                    norm = f"{ol_guard.group(1)} {{\n{ol_guard.group(2)}\n}}"

                for part in norm.splitlines():
                    p = part.strip()
                    if p:
                        statement_units.append((l_no, p))

            for u_idx, (line_no, stripped) in enumerate(statement_units):
                clean_braces = re.sub(r'//.*$', '', stripped)
                clean_braces = re.sub(r'/\*.*?\*/', '', clean_braces)
                clean_braces = re.sub(r"'(?:\\.|[^'])*'", "''", clean_braces)
                clean_braces = re.sub(r'"(?:\\.|[^"])*"', '""', clean_braces)

                closes_count = clean_braces.count("}")
                opens_count = clean_braces.count("{")

                # Lookahead to see if next statement is else or elseif (i.e. branch transition)
                next_is_else_or_elseif = False
                if u_idx + 1 < len(statement_units):
                    next_stmt = statement_units[u_idx + 1][1]
                    if re.match(r'^(?:else\s*if|elseif|else)\b', next_stmt):
                        next_is_else_or_elseif = True

                # Process closing braces
                if closes_count > 0:
                    # Pop closures if closing a closure scope
                    while closure_stack and (current_brace_depth - closes_count) < closure_stack[-1]["open_depth"]:
                        top_closure = closure_stack.pop()
                        current_env = top_closure["saved_env"]

                    # Process branch stack
                    while branch_stack and (current_brace_depth - closes_count) <= branch_stack[-1]["open_depth"]:
                        # If this closing brace is immediately followed by else/elseif, transition without popping!
                        if next_is_else_or_elseif:
                            br = branch_stack[-1]
                            if not br.get("has_early_return", False):
                                br["branch_exits"].append(dict(current_env))
                            break

                        br = branch_stack.pop()
                        if not br.get("has_early_return", False):
                            br["branch_exits"].append(dict(current_env))

                        if br.get("has_early_return", False) and not br.get("in_else", False) and not br["branch_exits"]:
                            # Guard clause: early return occurred in the 'if' body with no surviving exits.
                            # Surviving path is when condition was FALSE!
                            surviving_env = dict(br["pre_branch_env"])
                            if br["is_negated"] and br["narrowed_var"] and br["narrowed_type"]:
                                surviving_env[br["narrowed_var"]] = TypeBinding(
                                    {br["narrowed_type"]},
                                    TypeResolutionConfidence.PROVEN_EXACT,
                                    ["guard_clause_narrowing"],
                                )
                            elif not br["is_negated"] and br["narrowed_var"]:
                                surviving_env.pop(br["narrowed_var"], None)
                            current_env = surviving_env
                        else:
                            # Join all surviving paths + pre_branch_env if if-only branch
                            all_paths = list(br["branch_exits"])
                            if not br.get("in_else", False) and br["pre_branch_env"] not in all_paths:
                                all_paths.append(dict(br["pre_branch_env"]))

                            if all_paths:
                                joined: dict[str, TypeBinding] = {}
                                all_keys = set().union(*(p.keys() for p in all_paths))
                                for k in all_keys:
                                    types: set[str] = set()
                                    evs = []
                                    confs = []
                                    present_in_all = True
                                    for p in all_paths:
                                        if k in p:
                                            types.update(p[k].candidate_types)
                                            evs.extend(p[k].evidence)
                                            confs.append(p[k].confidence)
                                        else:
                                            present_in_all = False

                                    if len(types) == 1 and present_in_all and all(c == TypeResolutionConfidence.PROVEN_EXACT for c in confs):
                                        conf = TypeResolutionConfidence.PROVEN_EXACT
                                    elif types:
                                        conf = TypeResolutionConfidence.AMBIGUOUS if len(types) > 1 else TypeResolutionConfidence.HEURISTIC_INFERRED
                                    else:
                                        conf = TypeResolutionConfidence.UNKNOWN
                                    joined[k] = TypeBinding(types, conf, list(set(evs)))
                                current_env = joined

                    current_brace_depth += (opens_count - closes_count)
                else:
                    current_brace_depth += opens_count

                # Inline PHPDoc @var
                var_doc_m = re.search(r'@var\s+([A-Za-z0-9_\\|&?\[\]<>]+)\s+\$([A-Za-z0-9_]+)', stripped)
                if var_doc_m:
                    v_type = self.resolve_type_fqn(var_doc_m.group(1), ctx)
                    v_name = var_doc_m.group(2)
                    current_env[v_name] = TypeBinding({v_type}, TypeResolutionConfidence.HEURISTIC_INFERRED, ["inline_phpdoc_var"])

                # Closure parameter handling with lexical isolation
                closure_m = re.search(r'function\s*\(([^)]*)\)', stripped)
                if closure_m:
                    saved_outer_env = dict(current_env)
                    params_raw = closure_m.group(1).strip()
                    if params_raw:
                        for cp in params_raw.split(","):
                            c_match = re.search(r'(?:([A-Za-z0-9_\\]+)\s+)?\$([A-Za-z0-9_]+)', cp.strip())
                            if c_match and c_match.group(2):
                                c_name = c_match.group(2)
                                if c_match.group(1):
                                    c_type = self.resolve_type_fqn(c_match.group(1), ctx)
                                    current_env[c_name] = TypeBinding({c_type}, TypeResolutionConfidence.PROVEN_EXACT, ["closure_parameter"])
                                else:
                                    current_env[c_name] = TypeBinding(set(), TypeResolutionConfidence.UNKNOWN, ["closure_parameter"])
                    closure_stack.append({
                        "open_depth": current_brace_depth,
                        "saved_env": saved_outer_env,
                    })

                # Arrow functions: fn(...) => ...
                arrow_saved_env = None
                arrow_m = re.search(r'fn\s*\(([^)]*)\)\s*(?:use\s*\([^)]*\))?\s*=>', stripped)
                if arrow_m:
                    arrow_saved_env = dict(current_env)
                    params_raw = arrow_m.group(1).strip()
                    if params_raw:
                        for ap in params_raw.split(","):
                            a_match = re.search(r'(?:([A-Za-z0-9_\\]+)\s+)?\$([A-Za-z0-9_]+)', ap.strip())
                            if a_match and a_match.group(2):
                                a_name = a_match.group(2)
                                if a_match.group(1):
                                    a_type = self.resolve_type_fqn(a_match.group(1), ctx)
                                    current_env[a_name] = TypeBinding({a_type}, TypeResolutionConfidence.PROVEN_EXACT, ["arrow_param"])
                                else:
                                    current_env[a_name] = TypeBinding(set(), TypeResolutionConfidence.UNKNOWN, ["arrow_param"])

                # Branch points: if / elseif / else
                if re.match(r'^if\s*\(', stripped):
                    pre_branch = dict(current_env)
                    neg_inst_m = re.search(r'!\s*\(?\s*\$([A-Za-z0-9_]+)\s+instanceof\s+([A-Za-z0-9_\\]+)', stripped)
                    pos_inst_m = re.search(r'(?<![!])\s*\$([A-Za-z0-9_]+)\s+instanceof\s+([A-Za-z0-9_\\]+)', stripped)

                    br_record: dict[str, Any] = {
                        "open_depth": current_brace_depth - opens_count,
                        "pre_branch_env": pre_branch,
                        "is_negated": False,
                        "narrowed_var": None,
                        "narrowed_type": None,
                        "branch_exits": [],
                        "has_early_return": False,
                        "in_else": False,
                    }

                    if neg_inst_m:
                        v_name = neg_inst_m.group(1)
                        t_name = self.resolve_type_fqn(neg_inst_m.group(2), ctx)
                        br_record["is_negated"] = True
                        br_record["narrowed_var"] = v_name
                        br_record["narrowed_type"] = t_name
                    elif pos_inst_m:
                        v_name = pos_inst_m.group(1)
                        t_name = self.resolve_type_fqn(pos_inst_m.group(2), ctx)
                        br_record["is_negated"] = False
                        br_record["narrowed_var"] = v_name
                        br_record["narrowed_type"] = t_name
                        current_env[v_name] = TypeBinding({t_name}, TypeResolutionConfidence.PROVEN_EXACT, ["instanceof_narrowing"])

                    branch_stack.append(br_record)

                elif re.match(r'^(?:else\s*if|elseif)\s*\(', stripped):
                    if branch_stack:
                        br = branch_stack[-1]
                        current_env = dict(br["pre_branch_env"])
                        br["has_early_return"] = False
                        pos_inst_m = re.search(r'(?<![!])\s*\$([A-Za-z0-9_]+)\s+instanceof\s+([A-Za-z0-9_\\]+)', stripped)
                        if pos_inst_m:
                            v_name = pos_inst_m.group(1)
                            t_name = self.resolve_type_fqn(pos_inst_m.group(2), ctx)
                            current_env[v_name] = TypeBinding({t_name}, TypeResolutionConfidence.PROVEN_EXACT, ["instanceof_narrowing"])

                elif re.match(r'^else\b', stripped):
                    if branch_stack:
                        br = branch_stack[-1]
                        current_env = dict(br["pre_branch_env"])
                        br["has_early_return"] = False
                        br["in_else"] = True
                        if br["is_negated"] and br["narrowed_var"] and br["narrowed_type"]:
                            current_env[br["narrowed_var"]] = TypeBinding(
                                {br["narrowed_type"]},
                                TypeResolutionConfidence.PROVEN_EXACT,
                                ["instanceof_else_narrowing"],
                            )

                if re.search(r'\b(return|throw)\b', stripped):
                    if branch_stack:
                        branch_stack[-1]["has_early_return"] = True

                # 1. Check for assignments: $var = expr;
                assign_m = re.match(r'^\$([A-Za-z0-9_]+)\s*=\s*([^;]+);', stripped)
                if assign_m:
                    var_name = assign_m.group(1)
                    expr = assign_m.group(2).strip()

                    # Instantiation: new Foo()
                    new_m = re.match(r'^new\s+([A-Za-z0-9_\\]+)', expr)
                    if new_m:
                        cls_name = self.resolve_type_fqn(new_m.group(1), ctx)
                        current_env[var_name] = TypeBinding(
                            {cls_name}, TypeResolutionConfidence.PROVEN_EXACT, ["new_instantiation"]
                        )
                    # Simple property read: $this->prop
                    elif re.match(r'^\$this->([A-Za-z0-9_]+)$', expr):
                        prop_name = re.match(r'^\$this->([A-Za-z0-9_]+)$', expr).group(1)
                        if prop_name in ctx.properties:
                            p_bind = ctx.properties[prop_name]
                            current_env[var_name] = TypeBinding(
                                set(p_bind.candidate_types), p_bind.confidence, ["this_property_read"]
                            )
                    # Variable copy: $var = $otherVar
                    elif re.match(r'^\$([A-Za-z0-9_]+)$', expr):
                        src_var = expr.lstrip("$")
                        if src_var in current_env:
                            current_env[var_name] = current_env[src_var]
                    # Chained call or method call: $receiver->method(...) or $this->prop?->method(...) (Phase 35)
                    elif "->" in expr or "?->" in expr:
                        clean_expr = expr.replace("?->", "->")
                        resolved_t = self._evaluate_expression_type(clean_expr, current_env, ctx)
                        if resolved_t:
                            current_env[var_name] = resolved_t

                # 2. Foreach element unpacking: foreach ($items as $item)
                fe_m = re.search(r'foreach\s*\(\s*\$([A-Za-z0-9_]+)\s+as\s+\$([A-Za-z0-9_]+)\s*\)', stripped)
                if fe_m:
                    coll_var = fe_m.group(1)
                    elem_var = fe_m.group(2)
                    if coll_var in current_env:
                        elem_cands: set[str] = set()
                        for ct in current_env[coll_var].candidate_types:
                            clean_elem = ct.rstrip("[]").replace("array<", "").replace(">", "").strip()
                            elem_cands.add(clean_elem)
                        current_env[elem_var] = TypeBinding(
                            elem_cands, TypeResolutionConfidence.HEURISTIC_INFERRED, ["foreach_unpack"]
                        )

                # 3. Detect method invocations: $receiver->method(...)
                for call_match in re.finditer(r'(\$(?:[A-Za-z0-9_]+(?:->[A-Za-z0-9_]+(?:\([^)]*\))?)*))\s*->\s*([A-Za-z0-9_]+)\s*\(', stripped):
                    raw_recv = call_match.group(1).strip()
                    called_m = call_match.group(2).strip()

                    # Resolve receiver type
                    recv_binding = self._resolve_receiver_chain(raw_recv, current_env, ctx)
                    if recv_binding and recv_binding.candidate_types:
                        cand_list = sorted(list(recv_binding.candidate_types))
                        primary = cand_list[0]
                        conf = recv_binding.confidence if len(cand_list) == 1 else TypeResolutionConfidence.AMBIGUOUS
                        ev = recv_binding.evidence
                    else:
                        cand_list = []
                        primary = None
                        conf = TypeResolutionConfidence.AMBIGUOUS if raw_recv != "$this" else TypeResolutionConfidence.UNKNOWN
                        ev = ["unresolved_receiver_expression"]

                    call_sites.append(CallSiteInfo(
                        file_path=file_path,
                        line_number=line_no,
                        raw_statement=stripped,
                        receiver_expr=raw_recv,
                        method_name=called_m,
                        inferred_type=primary,
                        candidate_types=cand_list,
                        confidence=conf,
                        evidence=ev,
                        enclosing_class=ctx.class_name,
                        enclosing_method=enclosing_method_name,
                    ))

                # If an arrow function was evaluated, restore outer environment
                if arrow_saved_env is not None:
                    current_env = arrow_saved_env

        return call_sites

    def _resolve_receiver_chain(
        self, recv_expr: str, env: dict[str, TypeBinding], ctx: ClassContext
    ) -> Optional[TypeBinding]:
        """Resolve simple and chained receivers: $node, $this, $this->node, $event->getNode()."""
        # Exact $this
        if recv_expr == "$this":
            if ctx.fqn:
                return TypeBinding({ctx.fqn}, TypeResolutionConfidence.PROVEN_EXACT, ["this_receiver"])
            return None

        # Simple variable $node
        if re.match(r'^\$([A-Za-z0-9_]+)$', recv_expr):
            var_name = recv_expr.lstrip("$")
            if var_name in env:
                return env[var_name]
            return None

        # Property on this: $this->property
        if re.match(r'^\$this->([A-Za-z0-9_]+)$', recv_expr):
            p_name = recv_expr.replace("$this->", "").strip()
            if p_name in ctx.properties:
                return ctx.properties[p_name]
            return None

        # Chained expression: $event->getNode()
        return self._evaluate_expression_type(recv_expr, env, ctx)

    def _evaluate_expression_type(
        self, expr: str, env: dict[str, TypeBinding], ctx: ClassContext
    ) -> Optional[TypeBinding]:
        """Evaluate type of an expression chain like $event->getNode(), $this->userSession->getUser(), or $file->getStorage()."""
        chain_m = re.match(r'^(\$(?:[A-Za-z0-9_]+(?:->[A-Za-z0-9_]+)?))\s*->\s*([A-Za-z0-9_]+)\s*\([^)]*\)$', expr)
        if chain_m:
            head_expr = chain_m.group(1).strip()
            called_m = chain_m.group(2).strip()

            head_binding = None
            if head_expr.startswith("$this->"):
                p_name = head_expr.replace("$this->", "").strip()
                head_binding = ctx.properties.get(p_name)
            elif head_expr == "$this":
                if ctx.fqn:
                    head_binding = TypeBinding({ctx.fqn}, TypeResolutionConfidence.PROVEN_EXACT, ["this_receiver"])
            else:
                var_name = head_expr.lstrip("$")
                head_binding = env.get(var_name)

            if head_binding:
                for head_t in head_binding.candidate_types:
                    summary_key = (head_t, called_m)
                    if summary_key in self.method_summaries:
                        return self.method_summaries[summary_key]
                    derived = self._derive_method_summary_from_source(head_t, called_m)
                    if derived:
                        return derived
        return None

    def analyze_file(self, rel_path: str) -> list[CallSiteInfo]:
        """Analyze a file located under repo_root (PHASE 27)."""
        if not self.repo_root:
            raise ValueError("repo_root must be configured to call analyze_file")
        clean = rel_path.replace("\\", "/").lstrip("/")
        full_path = self.repo_root / clean
        if not full_path.exists():
            return []
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        return self.analyze_source_content(content, file_path=clean)
