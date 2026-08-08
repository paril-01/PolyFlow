"""ECP Benchmark Runner — Tests PolyFlow against the enterprise platform."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def main():
    with open(os.path.join(os.path.dirname(__file__), "queries.json")) as f:
        queries = json.load(f)

    print("=" * 70)
    print("ECP BENCHMARK — PolyFlow Enterprise Analysis")
    print("=" * 70)

    for q in queries:
        print(f"\n[{q['id']}] ({q['type'].upper()}) {q['query']}")
        print(f"  Status: PENDING — Run PolyFlow analysis to evaluate")

    print(f"\n{'=' * 70}")
    print(f"Total queries: {len(queries)}")
    print(f"Types: {', '.join(set(q['type'] for q in queries))}")

if __name__ == "__main__":
    main()
