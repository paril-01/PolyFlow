"""
Synthetic Enterprise Generator - CLI Entry Point.

Usage:
    python -m enterprise_gen.cli generate --scale medium --seed 42
    python -m enterprise_gen.cli generate --scale large --seed 99 --output ./enterprise-platform
"""

import argparse
import random
import time
import sys
import os
from pathlib import Path

# Ensure parent dir is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enterprise_gen.config import SCALE_CONFIGS, FEATURE_DOMAINS, SERVICES, CALL_CHAINS
from enterprise_gen.generators.service_gen import generate_service_scaffolding
from enterprise_gen.generators.feature_gen import generate_features
from enterprise_gen.generators.poly_gen import generate_poly_governance
from enterprise_gen.generators.schema_gen import generate_schemas
from enterprise_gen.generators.infra_gen import generate_infrastructure
from enterprise_gen.generators.extras_gen import (
    generate_docs, generate_cicd, inject_technical_debt,
    seed_bugs, simulate_git_history, generate_benchmark
)


from enterprise_gen.generators.pure_polyflow_gen import generate_pure_polyflow_platform


def safe_print(msg):
    """Print with ASCII-safe encoding for Windows consoles."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())


def _count_files(directory: Path) -> int:
    count = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        count += len(files)
    return count


def _count_poly_files(directory: Path) -> int:
    count = 0
    for root, dirs, files in os.walk(directory):
        count += sum(1 for f in files if f.endswith('.poly'))
    return count


def cmd_generate(args):
    """Execute the full enterprise generation pipeline."""
    scale_name = args.scale
    seed = args.seed
    output = Path(args.output)
    mode = getattr(args, "mode", "pure_polyflow")

    if scale_name not in SCALE_CONFIGS:
        safe_print(f"ERROR: Unknown scale '{scale_name}'. Choose from: {list(SCALE_CONFIGS.keys())}")
        sys.exit(1)

    scale = SCALE_CONFIGS[scale_name]
    rng = random.Random(seed)

    safe_print("=" * 72)
    safe_print("  SYNTHETIC ENTERPRISE GENERATOR -- PolyFlow Benchmark")
    safe_print("=" * 72)
    safe_print(f"  Scale       : {scale.name.upper()}")
    safe_print(f"  Mode        : {mode.upper()}")
    safe_print(f"  Seed        : {seed}")
    safe_print(f"  Output      : {output.absolute()}")
    safe_print(f"  Features    : ~{int(sum(len(d.features) for d in FEATURE_DOMAINS) * scale.feature_multiplier)}")
    safe_print("=" * 72)

    start = time.time()

    if mode in ("pure", "pure_polyflow"):
        safe_print("\n[PURE POLYFLOW NATIVE MODE] Generating .poly modules and Native In-Memory Engine...")
        poly_count = generate_pure_polyflow_platform(output, scale, rng)
        bench_count = generate_benchmark(output, scale, rng)
        elapsed = time.time() - start

        safe_print("\n" + "=" * 72)
        safe_print("  PURE POLYFLOW GENERATION COMPLETE")
        safe_print("=" * 72)
        safe_print(f"  Total .poly Modules Generated : {poly_count}")
        safe_print(f"  Standalone Redundant Files    : 0 (Pure PolyFlow Architecture)")
        safe_print(f"  Benchmark Query Templates     : {bench_count}")
        safe_print(f"  Generation Time               : {elapsed:.2f}s")
        safe_print("=" * 72)
        safe_print(f"\n  Output directory: {output.absolute()}")
        safe_print(f"  Validate .poly modules: python -m polyflow validate {output / 'features'}")
        safe_print(f"  Boot Native Engine:     python {output / 'engine.py'} 9090")
        return

    # Full microservices mode
    safe_print("\n[1/8] Service Scaffolding...")
    generate_service_scaffolding(output)

    safe_print("\n[2/8] Feature Implementations...")
    feat_count = generate_features(output, scale, rng)

    safe_print("\n[3/8] PolyFlow Governance Layer (.poly files)...")
    poly_count = generate_poly_governance(output, scale, rng)

    safe_print("\n[4/8] Schema Generation (SQL, Protobuf, GraphQL)...")
    schema_count = generate_schemas(output, scale, rng)

    safe_print("\n[5/8] Infrastructure (Terraform, Kubernetes, Monitoring)...")
    infra_count = generate_infrastructure(output, scale, rng)

    safe_print("\n[6/8] Documentation & CI/CD Workflows...")
    doc_count = generate_docs(output, scale, rng)
    cicd_count = generate_cicd(output, scale, rng)

    safe_print("\n[7/8] Technical Debt & Bug Injection...")
    debt_count = inject_technical_debt(output, scale, rng)
    bug_count = seed_bugs(output, scale, rng)

    safe_print("\n[8/8] Git History Simulation & Benchmark Harness...")
    git_count = simulate_git_history(output, scale, rng)
    bench_count = generate_benchmark(output, scale, rng)

    elapsed = time.time() - start

    total_files = _count_files(output)
    total_poly = _count_poly_files(output)

    safe_print("\n" + "=" * 72)
    safe_print("  GENERATION COMPLETE")
    safe_print("=" * 72)
    safe_print(f"  Total Files Generated  : {total_files:,}")
    safe_print(f"  Total .poly Files      : {total_poly}")
    safe_print(f"  Features               : {feat_count}")
    safe_print(f"  Generation Time        : {elapsed:.1f}s")
    safe_print("=" * 72)


def main():
    parser = argparse.ArgumentParser(
        prog="enterprise-gen",
        description="Synthetic Enterprise Generator for PolyFlow Benchmarking"
    )
    subparsers = parser.add_subparsers(dest="command")

    gen_parser = subparsers.add_parser("generate", help="Generate the Enterprise Commerce Platform")
    gen_parser.add_argument("--scale", choices=["small", "medium", "large"], default="medium", help="Scale of generation")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    gen_parser.add_argument("--output", type=str, default="./enterprise-platform", help="Output directory")
    gen_parser.add_argument("--mode", choices=["pure_polyflow", "full_microservices"], default="pure_polyflow", help="Architecture mode")

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
