# PolyFlow & RCIR Reproduction Guide: Commit ea221b9

**Date**: 2026-10-10  
**Evaluator Policy**: Rule 0 (Observation Before Claim) — Fail-closed on missing toolchains.  
**PolyFlow Target Commit**: `ea221b91890047d101ebd5a6f8f3a4c2457faeb2`  

---

## 1. System Environment Verification

Run these commands to verify runtime prerequisites:

```bash
# Verify PolyFlow repository revision
git rev-parse HEAD
# Expected: ea221b91890047d101ebd5a6f8f3a4c2457faeb2

# Verify Python version (3.11+ required)
python --version

# Verify PHP CLI availability (required for L1 syntax verification)
php -v

# Verify Ollama service and local models (for live agent trials)
ollama list
# Should display qwen2.5-coder:1.5b
```

---

## 2. Regression & Audit Test Suites

Execute the regression and integrity test suites to verify that all 32 findings and master audit specifications pass:

```bash
# Run Master Audit Test Suite (T01-T36 verification)
python -m pytest tests/test_audit_master_suite.py -v

# Run Finding-Specific Regression Suite (F01-F32 verification)
python -m pytest tests/test_audit_findings.py -v

# Run Benchmark Integrity Suite
python -m pytest tests/benchmark_integrity -v

# Run Entire Test Suite across all modules
python -m pytest tests -q
```

---

## 3. CLI Benchmark Runner Verification

### 3.1 Help & Flag Validation
Confirm that all CLI flags (`--target-sha`, `--oracle-dir`, `--task-id`, `--dry-run`, `--verify-only`) are recognized without error:

```bash
python scripts/run_benchmark.py --help
```

### 3.2 Dry-Run Sanity Check
Executes target commit verification, loads public tasks, validates the private oracle boundary, initializes `LiveRCIRContextProvider`, and verifies real source extraction from the target repository:

```bash
python scripts/run_benchmark.py \
  --target nextcloud \
  --target-sha da57df078d0808a7235a0177bd99d23c010b472e \
  --mode dev \
  --tasks experiments/benchmarks/public/dev.json \
  --oracle-dir experiments/benchmarks/private/dev \
  --dry-run
```

Expected output:
- `Verified target repo at commit: da57df078d0808a7235a0177bd99d23c010b472e`
- `Loaded 5 public tasks from: dev.json (SHA-256: 8cd63de61587...)`
- `Evaluator oracle initialized (SHA-256: 0e033d6e53ec...)`
- `Sample RCIR retrieval for BLIND-TASK-01: OK (5348 chars)`
- `Dry run completed successfully under Rule 0.`

### 3.3 Verify-Only on Candidate Worktree
Evaluates an existing candidate trial worktree using true git status modifications and the task's private oracle:

```bash
python scripts/run_benchmark.py \
  --verify-only \
  --task-id BLIND-TASK-01 \
  --worktree experiments/nextcloud_validation/nextcloud-server
```

---

## 4. Live Agent Benchmark Execution

When Composer and PHPUnit dependencies are available:

```bash
python scripts/run_benchmark.py \
  --target nextcloud \
  --target-sha da57df078d0808a7235a0177bd99d23c010b472e \
  --mode dev \
  --tasks experiments/benchmarks/public/dev.json \
  --oracle-dir experiments/benchmarks/private/dev \
  --provider ollama \
  --model qwen2.5-coder:1.5b \
  --turn-budget 12 \
  --replicates 1 \
  --task-id BLIND-TASK-01
```

*Note*: If Composer is not present on the host PATH, L3 tests will fail closed (`L3_NOT_MEASURED`) and the trial will not receive accepted status, preserving scientific honesty under Rule 0.
