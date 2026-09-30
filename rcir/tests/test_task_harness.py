"""
Tests for End-to-End Task-Success Harness (v7 §6.2, §7).

Validates:
1. validate_source_syntax catches syntax errors across languages and passes valid code.
2. apply_task_patch cleanly mutates and reverts repo files.
3. TaskSuccessHarness generates Context Contracts, computes coverage, and evaluates overall task success.
"""

import tempfile
from pathlib import Path
import pytest

from rcir.benchmarks.task_harness import (
    validate_source_syntax,
    apply_task_patch,
    CrossServiceTask,
    TaskSuccessHarness,
)


def test_validate_source_syntax():
    """Verify syntax validation catches Python AST errors and unbalanced braces."""
    # Python valid
    valid, msg = validate_source_syntax("def foo():\n    return 42\n", "foo.py")
    assert valid is True

    # Python invalid
    invalid, msg = validate_source_syntax("def foo(:\n    return 42\n", "foo.py")
    assert invalid is False
    assert "SyntaxError" in msg

    # Go / C# / Java balanced braces
    valid, _ = validate_source_syntax("func main() { fmt.Println(1) }", "main.go")
    assert valid is True

    # Unbalanced braces
    invalid, msg = validate_source_syntax("func main() { fmt.Println(1)", "main.go")
    assert invalid is False
    assert "Unbalanced" in msg


@pytest.fixture
def mock_task_repo():
    """Create a temporary microservice repo fixture for task evaluation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Protos
        proto_dir = root / "protos"
        proto_dir.mkdir(parents=True)
        (proto_dir / "demo.proto").write_text(
            '''syntax = "proto3";
package hipstershop;

service CartService {
    rpc AddItem(AddItemRequest) returns (Empty) {}
}
message AddItemRequest { string user_id = 1; }
message Empty {}
''',
            encoding="utf-8",
        )

        # Go frontend caller
        go_dir = root / "src" / "frontend"
        go_dir.mkdir(parents=True)
        (go_dir / "rpc.go").write_text(
            '''package main
import "context"

func insertCart(ctx context.Context) error {
    _, err := pb.NewCartServiceClient(conn).AddItem(ctx, &pb.AddItemRequest{})
    return err
}
''',
            encoding="utf-8",
        )

        # C# cartservice implementation
        cs_dir = root / "src" / "cartservice" / "src" / "services"
        cs_dir.mkdir(parents=True)
        (cs_dir / "CartService.cs").write_text(
            '''namespace CartService {
    public class CartService : Hipstershop.CartService.CartServiceBase {
        public async override Task<Empty> AddItem(AddItemRequest request, ServerCallContext context) {
            return new Empty();
        }
    }
}
''',
            encoding="utf-8",
        )

        yield root


def test_apply_task_patch_reversion(mock_task_repo):
    """Test reversible patch application."""
    proto_p = mock_task_repo / "protos" / "demo.proto"
    orig = proto_p.read_text(encoding="utf-8")

    mutations = {
        "protos/demo.proto": ("rpc AddItem(", "rpc AddCartItem("),
    }

    with apply_task_patch(mock_task_repo, mutations) as modified:
        assert "protos/demo.proto" in modified
        assert "rpc AddCartItem(" in proto_p.read_text(encoding="utf-8")

    assert proto_p.read_text(encoding="utf-8") == orig


def test_task_harness_evaluate_task(mock_task_repo):
    """Test task execution and Context Contract evaluation."""
    task = CrossServiceTask(
        task_id="test_task_add_item",
        title="Rename AddItem",
        description="Rename AddItem to AddCartItem",
        target_symbol="CartService.AddItem",
        expected_files=[
            "protos/demo.proto",
            "src/frontend/rpc.go",
            "src/cartservice/src/services/CartService.cs",
        ],
        prompt="Rename AddItem to AddCartItem",
        sample_mutations={
            "protos/demo.proto": ("rpc AddItem(", "rpc AddCartItem("),
            "src/frontend/rpc.go": (".AddItem(", ".AddCartItem("),
            "src/cartservice/src/services/CartService.cs": ("Task<Empty> AddItem(", "Task<Empty> AddCartItem("),
        },
    )

    harness = TaskSuccessHarness(mock_task_repo)
    result = harness.evaluate_task(task)

    assert result.contract_coverage == 1.0
    assert result.contract_complete is True
    assert result.patch_applied is True
    assert result.syntax_valid is True
    assert result.overall_success is True


def test_dynamic_task_synthesizer(mock_task_repo):
    """Test blind synthesis of tasks without hardcoded file paths."""
    from rcir.benchmarks.task_harness import DynamicTaskSynthesizer
    synthesizer = DynamicTaskSynthesizer(mock_task_repo)
    tasks = synthesizer.synthesize_tasks(max_tasks=5)

    assert len(tasks) >= 1
    t = tasks[0]
    assert t.target_symbol == "CartService.AddItem"
    assert any("demo.proto" in f for f in t.expected_files)
    assert any("rpc.go" in f for f in t.expected_files)
    assert any("CartService.cs" in f for f in t.expected_files)
    assert len(t.sample_mutations) >= 2


def test_task_harness_blind_run_suite(mock_task_repo):
    """Test running harness with tasks=None runs dynamic synthesizer blindly."""
    harness = TaskSuccessHarness(mock_task_repo)
    report = harness.run_suite(tasks=None)

    assert report.total_tasks >= 1
    assert report.contract_coverage_rate == 1.0
    assert report.overall_success_rate == 1.0


def test_generalized_evaluator(mock_task_repo):
    """Test full GeneralizedEvaluator on blind mock repo."""
    from rcir.benchmarks.generalized_evaluator import GeneralizedEvaluator
    evaluator = GeneralizedEvaluator(mock_task_repo)
    report = evaluator.run(mutation_limit=1, task_limit=1)

    assert report.repo_name is not None
    assert report.zero_cloud_verified is True
    assert report.synthetic_mutations["summary"]["total_mutations"] >= 1
    assert report.task_success["summary"]["total_tasks"] >= 1
    md = report.to_markdown()
    assert "# RCIR Generalized Benchmark Report" in md

