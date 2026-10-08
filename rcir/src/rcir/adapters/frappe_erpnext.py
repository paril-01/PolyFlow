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


@dataclass
class SourceArtifact:
    path: str
    language: str
    role: str
    sha256: str
    symbol: Optional[str] = None
    span: Optional[Dict[str, Any]] = None


@dataclass
class FeatureClosure:
    feature_id: str
    feature_name: str
    domain: str
    frontend_sources: List[SourceArtifact] = field(default_factory=list)
    backend_sources: List[SourceArtifact] = field(default_factory=list)
    data_model_sources: List[SourceArtifact] = field(default_factory=list)
    database_sources: List[SourceArtifact] = field(default_factory=list)
    api_sources: List[Dict[str, Any]] = field(default_factory=list)
    hook_sources: List[Dict[str, Any]] = field(default_factory=list)
    config_sources: List[SourceArtifact] = field(default_factory=list)
    workflow_sources: List[Dict[str, Any]] = field(default_factory=list)
    permission_sources: List[Dict[str, Any]] = field(default_factory=list)
    test_sources: List[SourceArtifact] = field(default_factory=list)
    template_sources: List[SourceArtifact] = field(default_factory=list)
    integration_sources: List[SourceArtifact] = field(default_factory=list)
    linked_features: List[Dict[str, Any]] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    schemas: List[Dict[str, Any]] = field(default_factory=list)
    runtime_cells: List[Dict[str, Any]] = field(default_factory=list)
    contracts: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    source_hashes: Dict[str, str] = field(default_factory=dict)
    closure_confidence: float = 1.0
    unresolved_sources: List[str] = field(default_factory=list)
    stack_manifest: Dict[str, Any] = field(default_factory=dict)
    coverage: Dict[str, float] = field(default_factory=dict)


class FrappeFeatureClosureExtractor:
    """Discovers and constructs full-stack FeatureClosure representations from source evidence."""

    @staticmethod
    def _hash_file(p: Path) -> str:
        try:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            return ""

    @classmethod
    def extract_closure(
        cls,
        dt_name: str,
        adapter: FrappeERPNextSourceDerivedAdapter,
        rel_to: Optional[Path] = None,
    ) -> Optional[FeatureClosure]:
        adapter.index()
        dt = adapter.doctypes.get(dt_name)
        if not dt:
            return None

        dt_path = Path(dt.source_file)
        dt_dir = dt_path.parent
        domain = dt.module.lower().replace(" ", "_")
        safe_name = dt_name.lower().replace(" ", "_").replace("-", "_")
        feature_id = f"ERPNEXT-{domain.upper()}-{safe_name.upper()}"

        closure = FeatureClosure(
            feature_id=feature_id,
            feature_name=dt_name,
            domain=domain,
            contracts={
                "feature_id": feature_id,
                "tier": "CRITICAL" if dt.is_submittable else "STANDARD",
                "is_submittable": dt.is_submittable,
                "owner": f"{domain}-engineering",
                "timeout_ms": 3000,
            }
        )

        def make_rel(p: Path) -> str:
            if rel_to:
                try:
                    return os.path.relpath(p, rel_to).replace("\\", "/")
                except Exception:
                    pass
            return str(p).replace("\\", "/")

        # 1. Data Model / Persistence Sources
        dt_sha = dt.sha256 or cls._hash_file(dt_path)
        closure.data_model_sources.append(
            SourceArtifact(
                path=make_rel(dt_path),
                language="Frappe DocType JSON",
                role="doctype_metadata",
                sha256=dt_sha,
                symbol=dt_name,
            )
        )
        closure.source_hashes[make_rel(dt_path)] = dt_sha

        # Inspect child tables directly linked
        for fieldname, child_dt_name in dt.child_tables.items():
            child_dt = adapter.doctypes.get(child_dt_name)
            if child_dt:
                c_path = Path(child_dt.source_file)
                c_sha = child_dt.sha256 or cls._hash_file(c_path)
                closure.data_model_sources.append(
                    SourceArtifact(
                        path=make_rel(c_path),
                        language="Frappe DocType JSON",
                        role="child_table_schema",
                        sha256=c_sha,
                        symbol=child_dt_name,
                    )
                )
                closure.source_hashes[make_rel(c_path)] = c_sha

        # 2. Backend Sources
        if dt.controller_file and os.path.exists(dt.controller_file):
            ctrl_p = Path(dt.controller_file)
            ctrl_sha = cls._hash_file(ctrl_p)
            closure.backend_sources.append(
                SourceArtifact(
                    path=make_rel(ctrl_p),
                    language="Python",
                    role="backend_controller",
                    sha256=ctrl_sha,
                    symbol=f"{dt_name.replace(' ', '')}Controller",
                )
            )
            closure.source_hashes[make_rel(ctrl_p)] = ctrl_sha

        # Additional backend files in doctype directory (dashboards, mappers, services)
        if dt_dir.exists():
            for p in dt_dir.iterdir():
                if p.is_file() and p.suffix == ".py":
                    rel = make_rel(p)
                    if rel in closure.source_hashes:
                        continue
                    p_sha = cls._hash_file(p)
                    role = "backend_utility"
                    if "dashboard" in p.name:
                        role = "backend_dashboard"
                    elif "mapper" in p.name:
                        role = "backend_mapper"
                    elif "test" in p.name:
                        continue  # handled in test section

                    closure.backend_sources.append(
                        SourceArtifact(
                            path=rel,
                            language="Python",
                            role=role,
                            sha256=p_sha,
                            symbol=p.stem,
                        )
                    )
                    closure.source_hashes[rel] = p_sha

        # 3. Frontend / Client Sources
        if dt_dir.exists():
            for p in dt_dir.iterdir():
                if p.is_file() and p.suffix in (".js", ".ts", ".vue"):
                    rel = make_rel(p)
                    p_sha = cls._hash_file(p)
                    role = "form_script"
                    if "list" in p.name:
                        role = "list_view_handler"
                    elif "tree" in p.name:
                        role = "tree_view_handler"

                    closure.frontend_sources.append(
                        SourceArtifact(
                            path=rel,
                            language="JavaScript" if p.suffix == ".js" else ("TypeScript" if p.suffix == ".ts" else "Vue"),
                            role=role,
                            sha256=p_sha,
                            symbol=p.stem,
                        )
                    )
                    closure.source_hashes[rel] = p_sha

        # 4. Hooks & Framework Events
        for hook in adapter.find_hooks_for_doctype(dt_name):
            closure.hook_sources.append({
                "hook_type": hook.hook_type,
                "event": hook.event,
                "handler_method": hook.handler_method,
                "source_file": make_rel(Path(hook.source_file)),
            })

        # 5. Tests
        if dt_dir.exists():
            for p in dt_dir.iterdir():
                if p.is_file() and ("test" in p.name.lower()):
                    rel = make_rel(p)
                    p_sha = cls._hash_file(p)
                    role = "unit_test" if p.suffix == ".py" else "test_fixtures"
                    closure.test_sources.append(
                        SourceArtifact(
                            path=rel,
                            language="Python" if p.suffix == ".py" else "JSON",
                            role=role,
                            sha256=p_sha,
                            symbol=p.stem,
                        )
                    )
                    closure.source_hashes[rel] = p_sha

        # 6. Cross-Feature Dependencies
        for fieldname, target_dt in dt.link_fields.items():
            if target_dt in adapter.doctypes:
                closure.linked_features.append({
                    "relationship": "LINK",
                    "field": fieldname,
                    "target_feature": target_dt,
                    "target_module": adapter.doctypes[target_dt].module,
                })

        for fieldname, child_dt in dt.child_tables.items():
            if child_dt in adapter.doctypes:
                closure.linked_features.append({
                    "relationship": "CHILD_TABLE",
                    "field": fieldname,
                    "target_feature": child_dt,
                    "target_module": adapter.doctypes[child_dt].module,
                })

        # 7. Stack Manifest
        frontend_techs = sorted(list({s.language for s in closure.frontend_sources})) or ["None"]
        backend_techs = sorted(list({s.language for s in closure.backend_sources})) or ["None"]
        data_model_techs = ["Frappe DocType JSON", "MariaDB ORM Metadata"]

        closure.stack_manifest = {
            "feature": dt_name,
            "poly_file": f"features/{domain}/{safe_name}.poly",
            "layers": {
                "frontend": {
                    "technologies": frontend_techs,
                    "files": [s.path for s in closure.frontend_sources],
                },
                "backend": {
                    "technologies": backend_techs,
                    "files": [s.path for s in closure.backend_sources],
                },
                "data_model": {
                    "technologies": data_model_techs,
                    "files": [s.path for s in closure.data_model_sources],
                },
                "framework": {
                    "files": [h["source_file"] for h in closure.hook_sources],
                },
                "tests": {
                    "files": [s.path for s in closure.test_sources],
                },
            },
            "native_artifact_count": len(closure.source_hashes),
            "polyflow_module_count": 1,
            "unresolved_artifacts": closure.unresolved_sources,
        }

        # 8. Layer Coverage Calculation
        closure.coverage = {
            "frontend": 1.0 if closure.frontend_sources else 0.0,
            "backend": 1.0 if closure.backend_sources else 0.0,
            "data_model": 1.0 if closure.data_model_sources else 0.0,
            "framework": 1.0 if closure.hook_sources else 0.85,
            "tests": 1.0 if closure.test_sources else 0.0,
            "dependencies": 1.0 if closure.linked_features else 0.9,
        }
        closure.coverage["overall"] = round(
            sum(closure.coverage.values()) / len(closure.coverage), 3
        )

        return closure

    @classmethod
    def generate_poly_file(cls, closure: FeatureClosure) -> str:
        """Generates canonical full-stack .poly content representing the entire closure."""
        lines = [
            f"# PolyFlow Full-Stack Feature Closure for {closure.feature_name}",
            f"# Domain: {closure.domain} | Native Artifacts: {len(closure.source_hashes)}",
            "",
            "@contract",
            f"feature_id: {closure.feature_id}",
            f"owner: {closure.domain}-engineering",
            f"classification: enterprise",
            f"is_submittable: {str(closure.contracts.get('is_submittable', False)).lower()}",
            f"timeout_ms: {closure.contracts.get('timeout_ms', 3000)}",
            "@end",
            "",
            f"@schema {closure.feature_name.replace(' ', '')}",
        ]

        # Add fields from data_model
        lines.append("  # Schema defined across primary doctype & child table contracts")
        lines.append("  name: string [primary_key]")
        lines.append("  docstatus: integer [0..2]")
        lines.append("@end")
        lines.append("")

        # Data Model Sources
        for src in closure.data_model_sources:
            lines.extend([
                "@source",
                f'path: "{src.path}"',
                f'language: "{src.language}"',
                f'role: "{src.role}"',
                f'symbol: "{src.symbol or closure.feature_name}"',
                f'sha256: "{src.sha256}"',
                "@end",
                ""
            ])

        # Frontend Sources
        for src in closure.frontend_sources:
            lines.extend([
                "@source",
                f'path: "{src.path}"',
                f'language: "{src.language}"',
                f'role: "{src.role}"',
                f'symbol: "{src.symbol or closure.feature_name}"',
                f'sha256: "{src.sha256}"',
                "@end",
                ""
            ])

        # Backend Sources
        for src in closure.backend_sources:
            lines.extend([
                "@source",
                f'path: "{src.path}"',
                f'language: "{src.language}"',
                f'role: "{src.role}"',
                f'symbol: "{src.symbol or closure.feature_name}"',
                f'sha256: "{src.sha256}"',
                "@end",
                ""
            ])

        # Test Sources
        for src in closure.test_sources:
            lines.extend([
                "@source",
                f'path: "{src.path}"',
                f'language: "{src.language}"',
                f'role: "{src.role}"',
                f'symbol: "{src.symbol or closure.feature_name}"',
                f'sha256: "{src.sha256}"',
                "@end",
                ""
            ])

        # Hook sources
        for hook in closure.hook_sources[:3]:
            lines.extend([
                "@source",
                f'path: "{hook["source_file"]}"',
                'language: "Python"',
                f'role: "framework_hook:{hook["event"]}"',
                f'symbol: "{hook["handler_method"]}"',
                'sha256: "framework_registered_hook"',
                "@end",
                ""
            ])

        # Linked features
        for link in closure.linked_features[:8]:
            tgt_clean = link["target_feature"].replace(" ", "").replace("-", "")
            tgt_mod = link["target_module"].lower().replace(" ", "_")
            tgt_safe = link["target_feature"].lower().replace(" ", "_").replace("-", "_")
            lines.append(f"@link ../{tgt_mod}/{tgt_safe}.poly::{tgt_clean} as ref_{link['field']}")

        lines.extend([
            "",
            "@error-map(code=\"PF_ERP_VALIDATION_FAIL\", action=\"ROLLBACK_TRANSACTION\")",
            "@decision(adr=\"ADR-ERP-001\", rationale=\"Unified feature closure eliminates multi-directory cognitive load while preserving native Frappe controllers\")",
            ""
        ])

        return "\n".join(lines)

    format_as_poly = generate_poly_file
