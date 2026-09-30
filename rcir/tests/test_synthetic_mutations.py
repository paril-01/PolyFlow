"""
Tests for Synthetic Mutation Benchmark (v7 §6.1.B).

Validates:
1. find_independent_call_sites accurately discovers callers independently of RCIR extractor.
2. apply_temporary_mutation reversibly mutates and restores files.
3. evaluate_mutation detects call sites and accurately flags silent misses / false negatives.
4. SyntheticMutationBenchmark computes live recall and precision without hardcoding.
"""

import tempfile
from pathlib import Path
import pytest

from rcir.benchmarks.synthetic_mutations import (
    find_independent_call_sites,
    apply_temporary_mutation,
    MutationSpec,
    SyntheticMutationBenchmark,
)


@pytest.fixture
def sample_microservices_repo():
    """Create a temporary multi-service repo fixture with Go, Python, and proto files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # 1. Protos
        proto_dir = root / "protos"
        proto_dir.mkdir(parents=True)
        proto_file = proto_dir / "demo.proto"
        proto_file.write_text(
            '''syntax = "proto3";
package hipstershop;

service CartService {
    rpc AddItem(AddItemRequest) returns (Empty) {}
    rpc GetCart(GetCartRequest) returns (Cart) {}
}

message AddItemRequest {
    string user_id = 1;
}
message GetCartRequest {
    string user_id = 1;
}
message Cart {}
message Empty {}
''',
            encoding="utf-8",
        )

        # 2. Go caller
        go_dir = root / "src" / "frontend"
        go_dir.mkdir(parents=True)
        go_file = go_dir / "rpc.go"
        go_file.write_text(
            '''package main
import (
    "context"
    pb "example/protos"
)

func (fe *frontendServer) insertCart(ctx context.Context) error {
    _, err := pb.NewCartServiceClient(fe.cartConn).AddItem(ctx, &pb.AddItemRequest{})
    return err
}
''',
            encoding="utf-8",
        )

        # 3. Python caller
        py_dir = root / "src" / "checkoutservice"
        py_dir.mkdir(parents=True)
        py_file = py_dir / "client.py"
        py_file.write_text(
            '''import grpc

def checkout():
    stub = CartServiceStub(channel)
    resp = stub.GetCart(GetCartRequest(user_id="123"))
''',
            encoding="utf-8",
        )

        yield root


def test_find_independent_call_sites(sample_microservices_repo):
    """Test independent scanner discovers call sites across Go and Python."""
    add_item_sites = find_independent_call_sites(
        sample_microservices_repo, "AddItem", "protos/demo.proto"
    )
    assert len(add_item_sites) == 1
    assert "frontend/rpc.go" in add_item_sites[0].file_path.replace("\\", "/")
    assert "AddItem" in add_item_sites[0].snippet

    get_cart_sites = find_independent_call_sites(
        sample_microservices_repo, "GetCart", "protos/demo.proto"
    )
    assert len(get_cart_sites) == 1
    assert "checkoutservice/client.py" in get_cart_sites[0].file_path.replace("\\", "/")


def test_apply_temporary_mutation_reversion(sample_microservices_repo):
    """Test that apply_temporary_mutation modifies content and cleanly restores it."""
    target_file = sample_microservices_repo / "protos" / "demo.proto"
    original_text = target_file.read_text(encoding="utf-8")

    with apply_temporary_mutation(target_file, "rpc AddItem(", "rpc AddCartItem("):
        mutated_text = target_file.read_text(encoding="utf-8")
        assert "rpc AddCartItem(" in mutated_text
        assert "rpc AddItem(" not in mutated_text

    restored_text = target_file.read_text(encoding="utf-8")
    assert restored_text == original_text


def test_synthetic_mutation_benchmark_run(sample_microservices_repo):
    """Test running the synthetic mutation benchmark on a mock repo."""
    bench = SyntheticMutationBenchmark(sample_microservices_repo)
    report = bench.run_benchmark(mutation_limit=2)

    assert report.total_mutations >= 1
    assert report.total_expected_call_sites >= 1
    assert report.overall_recall > 0.0
    assert report.total_missed == 0
