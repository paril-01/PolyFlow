"""
Automated Test Suite for PolyFlow (.poly) Engine.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path

from polyflow.parser import PolyParser
from polyflow.schema import PolySchemaValidator, SchemaBlock
from polyflow.linker import PolyLinker
from polyflow.runtime import PolyCellRuntime, LanguageBlock
from polyflow.merge import PolyMergeEngine, CellResult
from polyflow.error_map import PolyErrorTranslator, ErrorMapping
from polyflow.governance import MerkleLedger, PolyGovernanceEngine
from polyflow.guards import PolyGuardEngine

class TestPolyFlowEngine(unittest.TestCase):

    def setUp(self):
        self.parser = PolyParser()

    def test_parser_basic(self):
        poly_code = """
@contract
feature_id: "TEST-101"
owner: "test-team"
@end

@schema UserReq
  email: string
@end

@python[service]
def process(req):
    return {"status": "ok"}
@end
"""
        ast = self.parser.parse_text(poly_code)
        self.assertEqual(ast.contract.get("feature_id"), "TEST-101")
        self.assertIn("UserReq", ast.schemas)
        self.assertEqual(len(ast.language_blocks), 1)
        self.assertEqual(ast.language_blocks[0].language, "python")
        self.assertEqual(ast.language_blocks[0].tag, "service")

    def test_schema_validation(self):
        validator = PolySchemaValidator()
        schema = SchemaBlock(
            name="UserSchema",
            fields={
                "email": "string<format:email>",
                "age": "number<min:18,max:100>",
                "is_active": "boolean"
            }
        )

        valid_payload = {"email": "alice@org.com", "age": 25, "is_active": True}
        is_valid, errs = validator.validate(schema, valid_payload)
        self.assertTrue(is_valid)
        self.assertEqual(errs, {})

        invalid_payload = {"email": "invalid-email", "age": 12, "is_active": "yes"}
        is_valid, errs = validator.validate(schema, invalid_payload)
        self.assertFalse(is_valid)
        self.assertIn("email", errs)
        self.assertIn("age", errs)

    def test_cell_runtime_execution(self):
        runtime = PolyCellRuntime()
        block = LanguageBlock(
            language="python",
            tag="service",
            code="def process(req):\n    return {'result': req.get('val', 0) * 2}"
        )
        res = runtime.execute_cell(block, payload={"val": 21})
        self.assertEqual(res.status, "success")
        self.assertEqual(res.output, {"result": 42})

    def test_fail_partial_resilience(self):
        runtime = PolyCellRuntime()
        py_failing = LanguageBlock(
            language="python",
            tag="service",
            code="def process(req):\n    raise ValueError('Simulated database crash')"
        )
        py_fallback = LanguageBlock(
            language="python",
            tag="fallback",
            code="def process(req):\n    return {'status': 'recovered_from_cache'}"
        )

        res1 = runtime.execute_cell(py_failing, payload={})
        res2 = runtime.execute_cell(py_fallback, payload={})

        self.assertEqual(res1.status, "failed")
        self.assertEqual(res2.status, "success")

        merger = PolyMergeEngine()
        merged = merger.merge([res1, res2], {"strategy": "fallback", "order": ["python"]})
        self.assertEqual(merged["status"], "success")
        self.assertEqual(merged["output"], {"status": "recovered_from_cache"})

    def test_error_map_translation(self):
        em = ErrorMapping(
            language="python",
            rules={"AttributeError:NoneType:strip": "Plain English: You called strip on None."}
        )
        translator = PolyErrorTranslator([em])
        res = translator.translate("AttributeError: 'NoneType' object has no attribute 'strip' on line 12", language="python")
        self.assertTrue(res.mapped)
        self.assertIn("Plain English:", res.translated_text)

    def test_merkle_ledger_audit(self):
        ledger = MerkleLedger()
        n1 = ledger.record_entry("action_1", {"key": "val1"})
        n2 = ledger.record_entry("action_2", {"key": "val2"})

        valid, msg = ledger.verify_chain()
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Intentionally tamper with history
        ledger.entries[0]["data"]["key"] = "tampered_val"
        valid, msg = ledger.verify_chain()
        self.assertFalse(valid)
        self.assertIn("tampering detected", msg)

    def test_ide_guards(self):
        guards = PolyGuardEngine()
        bad_code = """
@standard language="python"
allowed_imports: ["json", "sys"]
@end

@python[service]
import urllib3

def process(req):
    open("debug_ghost.txt", "w").write("ghost file")
    eval("print('dangerous')")
    return {}
@end
"""
        ast = self.parser.parse_text(bad_code)
        violations = guards.inspect_ast(ast)
        self.assertGreaterEqual(len(violations), 3)
        v_ids = [v.guard_id for v in violations]
        self.assertIn("GUARD_A", v_ids)
        self.assertIn("GUARD_C", v_ids)
        self.assertIn("GUARD_D", v_ids)

if __name__ == "__main__":
    unittest.main()
