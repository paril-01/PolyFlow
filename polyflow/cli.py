"""
PolyFlow CLI Engine (`poly`).

Command line interface for parsing, executing, validating, testing, and auditing .poly feature files.
"""

import sys
import json
import argparse
from pathlib import Path
from polyflow.parser import PolyParser
from polyflow.schema import PolySchemaValidator
from polyflow.linker import PolyLinker
from polyflow.runtime import PolyCellRuntime
from polyflow.merge import PolyMergeEngine
from polyflow.error_map import PolyErrorTranslator
from polyflow.governance import PolyGovernanceEngine
from polyflow.guards import PolyGuardEngine

def _safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        cleaned = msg.encode("ascii", "replace").decode("ascii")
        print(cleaned)

def main():
    parser = argparse.ArgumentParser(
        prog="poly",
        description="PolyFlow (.poly) Feature-Centric Polyglot Runtime Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: parse
    parse_parser = subparsers.add_parser("parse", help="Parse a .poly file and print its AST summary")
    parse_parser.add_argument("file", help="Path to .poly file")
    parse_parser.add_argument("--json", action="store_true", help="Output raw JSON AST")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute a .poly file feature through isolated cells")
    run_parser.add_argument("file", help="Path to .poly file")
    run_parser.add_argument("--data", default="{}", help="JSON payload input for feature execution")
    run_parser.add_argument("--timeout", type=int, default=5000, help="Default cell timeout in ms")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate contracts, schemas, and IDE Guards A-F")
    val_parser.add_argument("file", help="Path to .poly file")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Audit & verify Merkle ledger chain")
    audit_parser.add_argument("action", nargs="?", default="verify-chain", help="Audit action (e.g. verify-chain)")

    # Command: test
    test_parser = subparsers.add_parser("test", help="Execute embedded test blocks inside a .poly file")
    test_parser.add_argument("file", help="Path to .poly file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "parse":
        cmd_parse(args.file, print_json=args.json)
    elif args.command == "run":
        cmd_run(args.file, payload_json=args.data, timeout_ms=args.timeout)
    elif args.command == "validate":
        cmd_validate(args.file)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "test":
        cmd_test(args.file)

def cmd_parse(filepath: str, print_json: bool = False):
    p = PolyParser()
    ast = p.parse_file(filepath)
    if print_json:
        out = {
            "filepath": ast.filepath,
            "contract": ast.contract,
            "schemas": list(ast.schemas.keys()),
            "links": [l.target_path for l in ast.links],
            "language_blocks": [{"lang": b.language, "tag": b.tag} for b in ast.language_blocks],
            "merge_strategy": ast.merge_strategy
        }
        _safe_print(json.dumps(out, indent=2))
    else:
        _safe_print(f"📄 PolyFlow File AST Summary: {filepath}")
        _safe_print(f"  • Feature ID: {ast.contract.get('feature_id', 'N/A')}")
        _safe_print(f"  • Owner:      {ast.contract.get('owner', 'N/A')}")
        _safe_print(f"  • Schemas:    {', '.join(ast.schemas.keys()) if ast.schemas else 'None'}")
        _safe_print(f"  • Links:      {len(ast.links)} direct link(s)")
        _safe_print(f"  • Blocks:     {len(ast.language_blocks)} language block(s)")
        for b in ast.language_blocks:
            _safe_print(f"      - @{b.language}[{b.tag}] (lines {b.start_line}-{b.end_line})")
        _safe_print(f"  • Merge:      Strategy='{ast.merge_strategy.get('strategy', 'first-success')}'")

def cmd_run(filepath: str, payload_json: str = "{}", timeout_ms: int = 5000):
    try:
        payload = json.loads(payload_json)
    except Exception as e:
        _safe_print(f"❌ Invalid JSON payload: {e}")
        sys.exit(1)

    p = PolyParser()
    ast = p.parse_file(filepath)

    # Cross-file Link Resolution
    linker = PolyLinker(p)
    base_dir = Path(filepath).parent
    linker_data = linker.resolve_ast(ast, base_dir)

    # Validate Schema if present
    validator = PolySchemaValidator()
    for s_name, schema in ast.schemas.items():
        if "Request" in s_name:
            valid, errs = validator.validate(schema, payload)
            if not valid:
                _safe_print(f"⚠️ Schema Validation Warning for {s_name}: {errs}")

    # Cell Execution
    runtime = PolyCellRuntime(default_timeout_ms=timeout_ms)
    cell_results = []

    for block in ast.language_blocks:
        # Skip test blocks during normal execution
        if block.tag.startswith("test"):
            continue
        res = runtime.execute_cell(block, payload, timeout_ms=timeout_ms)
        cell_results.append(res)

    # Plain-Language Error Translation
    error_translator = PolyErrorTranslator(ast.error_maps)
    for res in cell_results:
        if res.status == "failed" and res.error:
            translated = error_translator.translate(res.error, language=res.language)
            res.error = translated.translated_text

    # Merge Strategy
    merger = PolyMergeEngine()
    final_output = merger.merge(cell_results, ast.merge_strategy)

    # Governance Audit Ledger
    gov = PolyGovernanceEngine()
    ledger_node = gov.audit_execution(filepath, "run_feature", {"status": final_output.get("status")})

    _safe_print("🚀 PolyFlow Execution Result:")
    _safe_print(json.dumps(final_output, indent=2))
    _safe_print(f"\n🔒 Merkle Ledger Node #{ledger_node.index} Created: {ledger_node.merkle_root[:16]}...")

def cmd_validate(filepath: str):
    p = PolyParser()
    ast = p.parse_file(filepath)

    gov = PolyGovernanceEngine()
    is_gov_valid, gov_warnings = gov.verify_contract(ast.contract)

    guards = PolyGuardEngine()
    violations = guards.inspect_ast(ast)

    _safe_print(f"🔍 PolyFlow Governance & Guard Inspection: {filepath}")

    if gov_warnings:
        _safe_print("  ⚠️ Contract Warnings:")
        for w in gov_warnings:
            _safe_print(f"    - {w}")

    if violations:
        _safe_print(f"  ❌ {len(violations)} Guard Violation(s) Found:")
        for v in violations:
            _safe_print(f"    - [Line {v.line_number}] {v.guard_name}: {v.message}")
        sys.exit(1)
    else:
        _safe_print("  ✅ All IDE Guards A-F & Governance checks passed cleanly!")

def cmd_audit(args):
    gov = PolyGovernanceEngine()
    gov.ledger.record_entry("chain_verification_check", {"checker": "cli"})
    valid, msg = gov.ledger.verify_chain()
    if valid:
        _safe_print("✅ Tamper-Evident Merkle Ledger Verification: CHAIN INTEGRITY CONFIRMED (0 anomalies).")
    else:
        _safe_print(f"❌ Merkle Ledger Corruption Detected: {msg}")
        sys.exit(1)

def cmd_test(filepath: str):
    p = PolyParser()
    ast = p.parse_file(filepath)
    runtime = PolyCellRuntime(default_timeout_ms=5000)

    test_blocks = [b for b in ast.language_blocks if b.tag.startswith("test")]
    if not test_blocks:
        _safe_print(f"No test blocks (@python[test:*]) found in {filepath}")
        return

    _safe_print(f"🧪 Executing {len(test_blocks)} Embedded Test Block(s) in {filepath}:")
    passed = 0
    for b in test_blocks:
        res = runtime.execute_cell(b, payload={})
        if res.status == "success":
            _safe_print(f"  ✅ PASS: @{b.language}[{b.tag}] ({res.execution_time_ms:.1f}ms)")
            passed += 1
        else:
            _safe_print(f"  ❌ FAIL: @{b.language}[{b.tag}] -> {res.error}")

    _safe_print(f"\nTest Summary: {passed}/{len(test_blocks)} test blocks passed.")
    if passed < len(test_blocks):
        sys.exit(1)

if __name__ == "__main__":
    main()
