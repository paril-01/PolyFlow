"""
'polyflow inspect' and 'polyflow ast' Commands.

Inspects .poly files and renders grammar version, contracts, schemas,
sources, language cells, links, merge strategies, error maps, decisions,
and machine-readable AST output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from polyflow_sdk.core.parser import PolyParser, PolyAST


def execute_inspect(file_path: str, as_json: bool = False) -> int:
    path = Path(file_path).resolve()
    if not path.is_file():
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        parser = PolyParser()
        ast = parser.parse_file(path)
    except Exception as ex:
        print(f"Parse error in '{file_path}': {ex}", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(ast.to_dict(), indent=2))
        return 0

    print("=" * 80)
    print(f"PolyFlow Contract Inspection: {path.name}")
    print("=" * 80)
    print(f"File Path:          {ast.filepath}")
    print(f"Grammar Version:    {ast.grammar_version}")
    print(f"AST Schema Version: {ast.ast_schema_version}")

    # Contracts
    print(f"\n[Contracts] ({1 if ast.contract else 0} declared)")
    if ast.contract:
        for k, v in ast.contract.items():
            print(f"  • {k}: {v}")
    else:
        print("  (None)")

    # Schemas
    print(f"\n[Schemas] ({len(ast.schemas)} declared)")
    if ast.schemas:
        for sname, sblock in ast.schemas.items():
            print(f"  • @schema {sname}")
            for fname, ftype in sblock.fields.items():
                print(f"      - {fname}: {ftype}")
    else:
        print("  (None)")

    # Source References (@source)
    print(f"\n[Source References] ({len(ast.sources)} mapped)")
    if ast.sources:
        for src in ast.sources:
            sym_str = f" :: {src.symbol}" if src.symbol else ""
            print(f"  • [{src.language.upper()}] {src.path}{sym_str} (role: {src.role or 'generic'})")
            if src.sha256:
                print(f"      sha256: {src.sha256}")
    else:
        print("  (None)")

    # Language Cells
    print(f"\n[Language Cells] ({len(ast.language_blocks)} executable blocks)")
    if ast.language_blocks:
        for block in ast.language_blocks:
            loc = f"lines {block.start_line}-{block.end_line}"
            print(f"  • @{block.language}[{block.tag}] ({loc}, {len(block.code.splitlines())} lines)")
    else:
        print("  (None)")

    # Links (@link)
    print(f"\n[Links] ({len(ast.links)} linked modules)")
    if ast.links:
        for link in ast.links:
            alias_str = f" as {link.alias}" if link.alias else ""
            sel_str = f"::{link.selector}" if link.selector else ""
            print(f"  • @link {link.target_path}{sel_str}{alias_str}")
    else:
        print("  (None)")

    # Merge Strategy
    print(f"\n[Merge Strategy]")
    if ast.merge_strategy:
        for k, v in ast.merge_strategy.items():
            print(f"  • {k}: {v}")
    else:
        print("  (default)")

    # Error Maps
    print(f"\n[Error Maps] ({len(ast.error_maps)} registered)")
    if ast.error_maps:
        for em in ast.error_maps:
            print(f"  • @error-map language={em.language} ({len(em.rules)} rules)")
            for pat, repl in list(em.rules.items())[:3]:
                print(f"      - '{pat}' -> '{repl}'")
    else:
        print("  (None)")

    # Decisions & Standards
    gov_count = len(ast.decisions) + len(ast.standards) + len(ast.rationales) + len(ast.audits)
    print(f"\n[Governance & Standards] ({gov_count} entries)")
    for d in ast.decisions:
        print(f"  • @decision for={d.target}: {d.data}")
    for st in ast.standards:
        print(f"  • @standard lang={st.target}: {st.data}")
    for r in ast.rationales:
        print(f"  • @rationale for={r.target}: {r.data}")
    for a in ast.audits:
        print(f"  • @{a.block_type}: {a.data}")

    print("\n" + "=" * 80)
    return 0


def execute_ast(file_path: str, as_json: bool = True) -> int:
    return execute_inspect(file_path, as_json=True)
