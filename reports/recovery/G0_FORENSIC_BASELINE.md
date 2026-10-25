# Forensic Baseline & Diagnostic Report (Ticket PF-RC-G0)

**Document:** Forensic Baseline Report (`PF-RC-G0`)  
**Audited Date:** 25 October 2026 (Asia/Kolkata)  
**Execution Mode:** READ_ONLY Diagnostic Audit  
**Audited Repository:** `paril-01/PolyFlow`  
**Current HEAD SHA:** `9cf22f34434427cb3471f15b776c53b5144759e7`  
**Current Branch:** `work/pf-b1-ri-spike`  
**Audited Remote `origin/main` SHA:** `57a23c59877bd1775171f135fd9512f1b9eb2eb3` (Merge commit of `work/pf-b1-ri-spike`)  
**Target Pinned Commit:** `da57df078d0808a7235a0177bd99d23c010b472e` (`nextcloud/server`)  

---

## 1. System Census & Environment Snapshot

| Component | Observed Value | Evidence Command |
|---|---|---|
| **Local HEAD SHA** | `9cf22f34434427cb3471f15b776c53b5144759e7` | `git rev-parse HEAD` |
| **Local Active Branch** | `work/pf-b1-ri-spike` | `git branch --show-current` |
| **Remote `origin/main`** | `57a23c59877bd1775171f135fd9512f1b9eb2eb3` | `git log -n 1 origin/main` |
| **Working Tree Status** | Clean (1 untracked recovery execution pack file) | `git status --short` |
| **Operating System** | Windows 11 (AMD64) | `platform.platform()` |
| **Python Environment** | Python 3.12.3 (CPython, win32) | `python -V` |
| **Target Submodule** | `experiments/nextcloud_validation/nextcloud-server` | `git submodule status` |
| **Submodule HEAD** | `da57df078d0808a7235a0177bd99d23c010b472e` | `git -C ... rev-parse HEAD` |
| **Submodule Status** | Clean (working tree clean at pinned commit) | `git -C ... status --short` |

---

## 2. GitHub Actions CI Failure Census

At the audited remote `main` SHA (`57a23c5`), all four GitHub Actions workflows failed:

| Workflow | Run ID | Failing Step | Exact Error Message | Classification |
|---|---|---|---|---|
| **RCIR Artifact Integrity & Report Consistency** | [40180868419](https://github.com/paril-01/PolyFlow/actions/runs/40180868419) | `Validate Ground Truth Provenance` | `BenchmarkIntegrityError: Ground truth provenance failed with 107 errors.` | `OBSERVED_CI_FAILURE` |
| **RCIR Unit Tests & Static Verification** | [40180868389](https://github.com/paril-01/PolyFlow/actions/runs/40180868389) | `Run Ground Truth Provenance Validation` | `BenchmarkIntegrityError: Ground truth provenance failed with 107 errors.` (downstream stages not run) | `OBSERVED_CI_FAILURE` |
| **RCIR Benchmark Smoke Test** | [40180868427](https://github.com/paril-01/PolyFlow/actions/runs/40180868427) | `Validate Ground Truth Provenance` | `BenchmarkIntegrityError: Ground truth provenance failed with 107 errors.` | `OBSERVED_CI_FAILURE` |
| **PolyFlow Continuous Integration** | [40180868436](https://github.com/paril-01/PolyFlow/actions/runs/40180868436) | `Run Backend Proof Server Tests` | `assert p_res.status_code == 200 ... Advertised proof proof_001_agent_trials returned HTTP 404` | `OBSERVED_CI_FAILURE` |

---

## 3. Local Offline Reproduction Results

| Diagnostic Check | Local Windows Command | Exit Code | Observed Outcome |
|---|---|---|---|
| **Ground Truth Provenance** | `python experiments/rcir_v8_5/scripts/validate_ground_truth_provenance.py` | `0` | `SUCCESS: All 16 tasks, commits, files, and hashes 100% verified!` |
| **Backend Proof Server Tests** | `python -m pytest tests/test_backend_proof_server.py -q` | `0` | `9 passed, 1 warning in 3.86s` |
| **Benchmark Integrity Suite** | `python -m pytest tests/benchmark_integrity/ -q` | `0` | `21 passed, 1 warning in 8.45s` |
| **Audit Findings Suite** | `python -m pytest tests/test_audit_findings.py -q` | `0` | `21 passed in 1.95s` |

**Divergence Analysis:**
All four checks **pass locally on Windows** (exit code 0), but **fail remotely on Ubuntu Linux in GitHub Actions**. This definitively narrows the root causes to cross-platform environment divergence and validator assumptions rather than missing benchmark files.

---

## 4. Forensic Deep-Dive & Root-Cause Mechanisms

### Finding 1: The 107 Ground-Truth Errors on Linux CI
- **Sample File Examined:** `apps/files/lib/Controller/ApiController.php`
- **Expected Hash in `ground_truth.json`:** `4a05ac7b8bfa5b6da59d459e94dca9c68cf7c0fb909ab824495402bd1dd9f407`
- **Windows Local Disk Hash:** `4a05ac7b8bfa5b6da59d459e94dca9c68cf7c0fb909ab824495402bd1dd9f407` (Byte length: 15,701; CRLF: 499; LF: 499)
- **Git Blob Object Hash at `da57df07`:**
  `git -C experiments/nextcloud_validation/nextcloud-server show da57df078d0808a7235a0177bd99d23c010b472e:apps/files/lib/Controller/ApiController.php`
  -> Raw byte SHA-256: `4a05ac7b8bfa5b6da59d459e94dca9c68cf7c0fb909ab824495402bd1dd9f407` (The git object was committed with CRLF line endings).
- **Normalized LF Hash (as checked out on Ubuntu Linux):**
  `hashlib.sha256(content.replace(b'\r\n', b'\n')).hexdigest()` -> `4aadcd241689f234d0989e5d6472c4f81c7b1885998e85da6079f95a87b4fd13`
- **Root Cause Mechanism:**
  `validate_ground_truth_provenance.py` does `hashlib.sha256(tf_path.read_bytes()).hexdigest()` directly against the working tree files. On Linux GitHub runners, Git checks out files with native LF (`\n`), altering the byte digest for all 107 files. The validator neither uses `git show <upstream_commit>:<path>` nor normalizes line endings, nor asserts `HEAD == upstream_commit` before raw byte hashing.

### Finding 2: Proof Server HTTP 404 for `proof_001_agent_trials`
- **Sample File Examined:** `experiments/runs/run_20261009_blind_verified/exports/agent_trials.csv`
- **Expected Hash in `proof_index.json`:** `90045c8d145f8fd99d6180b7eb7106cdfff643934bfd63a99af9289a31f419f1`
- **Windows Local Disk Hash:** `90045c8d145f8fd99d6180b7eb7106cdfff643934bfd63a99af9289a31f419f1` (1648 bytes, 11 CRLF)
- **Linux Checked Out Hash:** `76e9394e937726da4651def7a516d3995d72577841466ab8ddd1b736e816c948` (1637 bytes, 11 LF)
- **EvidenceRegistry Mechanism:**
  In `showcase_app/backend/services/evidence_registry.py` (lines 70-74):
  `current_hash = hashlib.sha256(content).hexdigest()`
  `if expected_hash and current_hash != expected_hash: return None`
  When `client.get("/api/proofs/proof_001_agent_trials")` runs on Linux, the hash check fails because Git checked out LF line endings. `resolve_proof_file()` returns `None`, which causes the FastAPI router to return HTTP 404.
  Furthermore, `EvidenceRegistry.get_all_proofs()` advertises every proof from JSON without verifying that `resolve_proof_file()` will succeed.

### Finding 3: CI Checkout Submodule Configuration
- In `.github/workflows/ci.yml` (line 16):
  `uses: actions/checkout@v4` is invoked **without** `submodules: true`. Any step in `ci.yml` touching submodule files would fail due to missing directories.

---

## 5. Summary of Forensic Findings

1. **Failure 1 (107 Provenance Errors):** Diagnosed with cryptographic certainty. Caused by raw filesystem byte hashing in `validate_ground_truth_provenance.py` without line-ending normalization / git blob reading across Linux and Windows.
2. **Failure 2 (Proof 404):** Diagnosed with cryptographic certainty. Caused by `EvidenceRegistry.resolve_proof_file()` rejecting LF-checked-out CSV artifacts as tampered, returning `None`.
3. **Failure 3 (CI Submodule Omission):** `ci.yml` does not checkout submodules.

---

## 6. Prohibited Actions Enforced
- **Zero repository code edits made.**
- **No hashes regenerated or rewritten.**
- **No CI workflows dispatched.**
- **No changes to `main` branch.**

---

## 7. Status & Next Action

- **Current State:** `G0_REPORT_READY`
- **Active Ticket:** `PF-RC-G0` (Completed Forensic Reproduction)
- **Proposed Next Ticket:** `PF-RC-CI-001` (Commit-bound ground-truth provenance & cross-platform line-ending hash normalization)
- **Execution State:** `WAITING_FOR_OWNER_TICKET_APPROVAL`
