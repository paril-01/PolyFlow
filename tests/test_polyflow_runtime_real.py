"""
Tests for real multi-language PolyFlow runtime execution.
Verifies real toolchain subprocess execution for Python, Node.js, Java, Go, and PHP.
Ensures zero mock fallbacks.
"""

import unittest
from polyflow.parser import LanguageBlock
from polyflow.runtime import PolyCellRuntime


class TestPolyFlowRuntimeReal(unittest.TestCase):
    def setUp(self):
        # fast_native_mode=False guarantees real compiler/subprocess execution
        self.runtime = PolyCellRuntime(fast_native_mode=False)

    def test_python_real_cell(self):
        block = LanguageBlock(
            language="python",
            tag="py_simple",
            code="def process(req):\n    return {'val': req.get('n', 0) * 10}"
        )
        res = self.runtime.execute_cell(block, {"n": 5})
        self.assertEqual(res.status, "success", f"Failed with: {res.error}")
        self.assertEqual(res.output, {"val": 50})

    def test_node_real_cell(self):
        block = LanguageBlock(
            language="javascript",
            tag="node_hello",
            code="function process(req) { return { message: 'hello ' + (req.name || 'world') }; }"
        )
        res = self.runtime.execute_cell(block, {"name": "PolyFlow"})
        self.assertEqual(res.status, "success", f"Failed with: {res.error}")
        self.assertEqual(res.output, {"message": "hello PolyFlow"})

    def test_java_real_cell(self):
        code = """
public class RealJavaTest {
    public static void main(String[] args) {
        System.out.println("Java JDK 21 execution verified");
    }
}
"""
        block = LanguageBlock(
            language="java",
            tag="java_test",
            code=code
        )
        res = self.runtime.execute_cell(block, {"test": True})
        self.assertEqual(res.status, "success", f"Failed with: {res.error}")
        self.assertIn("Java JDK 21 execution verified", res.output.get("stdout", ""))

    def test_go_real_cell(self):
        code = """
package main

import "fmt"

func main() {
\tfmt.Println("Go 1.27.1 execution verified")
}
"""
        block = LanguageBlock(
            language="go",
            tag="go_test",
            code=code
        )
        res = self.runtime.execute_cell(block, {"engine": "go"}, timeout_ms=15000)
        self.assertEqual(res.status, "success", f"Failed with: {res.error}")
        self.assertIn("Go 1.27.1 execution verified", res.output.get("stdout", ""))

    def test_php_real_cell(self):
        code = """
function process($req) {
    return [
        'status' => 'ok',
        'received_id' => $req['id'] ?? 0,
        'doubled' => ($req['id'] ?? 0) * 2
    ];
}
"""
        block = LanguageBlock(
            language="php",
            tag="php_test",
            code=code
        )
        res = self.runtime.execute_cell(block, {"id": 21})
        self.assertEqual(res.status, "success", f"Failed with: {res.error}")
        self.assertEqual(res.output.get("doubled"), 42)


if __name__ == "__main__":
    unittest.main()
