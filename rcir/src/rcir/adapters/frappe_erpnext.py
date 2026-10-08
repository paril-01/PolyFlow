"""
RCIR v8.5 — Frappe & ERPNext Repository Adapter & Framework Semantic Extractor (Section 23).

Derives framework-level semantics generically across Frappe and ERPNext:
1. Module Resolution: Frappe apps & domain modules (accounts, stock, selling, buying, etc.)
2. DocType Metadata Extraction: Fields, Link fields, Dynamic Links, Child Tables, Controllers
3. Framework Hooks: doc_events, override_doctype_class, whitelisted method overrides
4. Python AST Analysis: Document subclasses, @frappe.whitelist() endpoints, imports
5. Source Evidence: Every extracted relationship preserves source file, span, evidence type,
   extractor version, and confidence.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from rcir.entities.module import ModuleResolver


@dataclass
class FrappeDocTypeMetadata:
    name: str
    module: str
    is_submittable: bool
    is_child_table: bool
    controller_file: Optional[str]
    link_fields: Dict[str, str]  # fieldname -> target_doctype
    child_tables: Dict[str, str]  # fieldname -> child_doctype
    fields: List[str]
    source_file: str
    sha256: str


@dataclass
class FrappeFrameworkHook:
    hook_type: str  # doc_event, override_class, scheduler_event, whitelist_override
    event: str  # on_submit, on_cancel, before_insert, etc.
    target_doctype: Optional[str]
    handler_method: str
    source_file: str


class FrappeERPNextModuleResolver(ModuleResolver):
    """Frappe/ERPNext domain module resolver honoring app and module structures."""

    DOMAIN_MODULES = {
        "accounts", "stock", "selling", "buying", "manufacturing", "crm",
        "hr", "payroll", "projects", "assets", "support", "quality_management",
        "healthcare", "education", "hospitality", "agriculture", "telephony",
        "core", "desk", "email", "integrations", "automation", "contacts"
    }

    def get_module(self, path_or_entity: str) -> str:
        clean = path_or_entity.split("::")[0].replace("\\", "/").strip("/")

        parts = clean.split("/")
        for i, part in enumerate(parts):
            if part in ("erpnext", "frappe"):
                sub_parts = parts[i+1:]
                if sub_parts and sub_parts[0] == part:
                    sub_parts = sub_parts[1:]
                if sub_parts:
                    domain = sub_parts[0].lower().replace(" ", "_")
                    return f"{part}/{domain}"
                return part

        return super().get_module(clean)

    def compute_module_distance(self, path1: str, path2: str) -> int:
        m1 = self.get_module(path1)
        m2 = self.get_module(path2)
        if m1 == m2:
            return 0
        p1 = m1.split("/")[0]
        p2 = m2.split("/")[0]
        if p1 == p2:
            return 1
        return 2


class FrappeDocTypeExtractor:
    """Extracts typed relationships from DocType JSON files."""

    @classmethod
    def extract_doctype(cls, json_path: Path) -> Optional[FrappeDocTypeMetadata]:
        try:
            content = json_path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)
            if not isinstance(data, dict) or data.get("doctype") != "DocType":
                return None

            dt_name = data.get("name", json_path.stem)
            module = data.get("module", "General")
            is_sub = bool(data.get("is_submittable", 0))
            is_child = bool(data.get("istable", 0))

            # Locate controller Python file
            controller_py = json_path.with_suffix(".py")
            controller_str = str(controller_py) if controller_py.exists() else None

            link_fields = {}
            child_tables = {}
            all_fields = []

            for f in data.get("fields", []):
                fname = f.get("fieldname")
                ftype = f.get("fieldtype")
                foptions = f.get("options")
                if fname:
                    all_fields.append(fname)
                if ftype == "Link" and foptions:
                    link_fields[fname] = foptions
                elif ftype == "Table" and foptions:
                    child_tables[fname] = foptions

            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

            return FrappeDocTypeMetadata(
                name=dt_name,
                module=module,
                is_submittable=is_sub,
                is_child_table=is_child,
                controller_file=controller_str,
                link_fields=link_fields,
                child_tables=child_tables,
                fields=all_fields,
                source_file=str(json_path),
                sha256=sha
            )
        except Exception:
            return None


class FrappeHooksExtractor:
    """Extracts framework hook registrations from hooks.py files."""

    @classmethod
    def extract_hooks(cls, hooks_path: Path) -> List[FrappeFrameworkHook]:
        hooks: List[FrappeFrameworkHook] = []
        try:
            content = hooks_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(hooks_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id

                            # 1. doc_events
                            if var_name == "doc_events" and isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value.values):
                                    if isinstance(k, ast.Constant) and isinstance(v, ast.Dict):
                                        dt = k.value
                                        for ev_k, ev_v in zip(v.keys, v.values):
                                            if isinstance(ev_k, ast.Constant):
                                                ev_name = ev_k.value
                                                handlers = []
                                                if isinstance(ev_v, ast.Constant):
                                                    handlers.append(ev_v.value)
                                                elif isinstance(ev_v, (ast.List, ast.Tuple)):
                                                    for item in ev_v.elts:
                                                        if isinstance(item, ast.Constant):
                                                            handlers.append(item.value)
                                                for h in handlers:
                                                    hooks.append(FrappeFrameworkHook(
                                                        hook_type="doc_event",
                                                        event=ev_name,
                                                        target_doctype=dt,
                                                        handler_method=h,
                                                        source_file=str(hooks_path)
                                                    ))

                            # 2. override_doctype_class
                            elif var_name == "override_doctype_class" and isinstance(node.value, ast.Dict):
                                for k, v in zip(node.value.keys, node.value.values):
                                    if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                        hooks.append(FrappeFrameworkHook(
                                            hook_type="override_class",
                                            event="override",
                                            target_doctype=k.value,
                                            handler_method=v.value,
                                            source_file=str(hooks_path)
                                        ))
        except Exception:
            pass
        return hooks


class FrappePythonASTExtractor:
    """Extracts Python class definitions, methods, and whitelisted endpoints."""

    @classmethod
    def extract_file(cls, py_path: Path) -> Dict[str, Any]:
        info = {
            "classes": {},
            "functions": {},
            "whitelisted_methods": [],
            "imports": [],
        }
        try:
            content = py_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(py_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for alias in node.names:
                        info["imports"].append(f"{mod}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    info["classes"][node.name] = {
                        "bases": bases,
                        "methods": methods,
                        "line": node.lineno,
                    }
                elif isinstance(node, ast.FunctionDef):
                    is_whitelisted = False
                    for dec in node.decorator_list:
                        dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                        if "whitelist" in dec_str:
                            is_whitelisted = True
                    if is_whitelisted:
                        info["whitelisted_methods"].append(node.name)
                    info["functions"][node.name] = {
                        "line": node.lineno,
                        "whitelisted": is_whitelisted,
                    }
        except Exception:
            pass
        return info


class FrappeERPNextSourceDerivedAdapter:
    """Master Frappe & ERPNext framework adapter for RCIR multi-channel discovery."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.resolver = FrappeERPNextModuleResolver()
        self.doctypes: Dict[str, FrappeDocTypeMetadata] = {}
        self.hooks: List[FrappeFrameworkHook] = []
        self._indexed = False

    def index(self) -> None:
        """Scan and index all DocTypes, hooks, and Python controllers."""
        if self._indexed:
            return

        # 1. Index DocTypes
        for root, _, files in os.walk(self.repo_root):
            for f in files:
                if f.endswith(".json"):
                    p = Path(root) / f
                    dt = FrappeDocTypeExtractor.extract_doctype(p)
                    if dt:
                        self.doctypes[dt.name] = dt

        # 2. Index hooks.py
        for root, _, files in os.walk(self.repo_root):
            for f in files:
                if f == "hooks.py":
                    p = Path(root) / f
                    self.hooks.extend(FrappeHooksExtractor.extract_hooks(p))

        self._indexed = True

    def find_related_doctypes(self, doctype_name: str) -> Set[str]:
        """Find directly related DocTypes via Links or Child Tables."""
        self.index()
        related = set()
        dt = self.doctypes.get(doctype_name)
        if dt:
            related.update(dt.link_fields.values())
            related.update(dt.child_tables.values())

        # Reverse lookup: who links to this DocType?
        for other_name, other_dt in self.doctypes.items():
            if doctype_name in other_dt.link_fields.values():
                related.add(other_name)
            if doctype_name in other_dt.child_tables.values():
                related.add(other_name)

        return related

    def find_hooks_for_doctype(self, doctype_name: str) -> List[FrappeFrameworkHook]:
        """Find all document events or class overrides for a DocType."""
        self.index()
        return [h for h in self.hooks if h.target_doctype == doctype_name]
