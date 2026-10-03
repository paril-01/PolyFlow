# RCIR v8 — Agent Execution & Edit Loop Report (PHASE 15, 16, 17 & 20)

**Status:** APPROVED  
**Date:** 2026-10-04  
**Implementation Modules:** `orchestrator/tools.py`, `orchestrator/agent_loop.py`, `orchestrator/router.py`  
**Specification Reference:** `enhancemts - 01.md` (PHASE 15, 16, 17, 20)

---

## 1. The Edit Loop Challenge in LLM Coding Agents

Prior to RCIR v8, agent coding evaluations suffered from a severe structural flaw:
- Agents attempted edits using `edit_file(path, old_str, new_str)` requiring exact bitwise string equality.
- Even when models identified the exact correct bug fix, a single differing space, indentation tab, or trailing newline caused the tool to fail with `ERROR: Target string to replace was not found`.
- In the frozen Nextcloud baseline, the local model produced 0 successful edits, triggering an automatic Gatekeeper `REJECT`.

---

## 2. Phase 15 Implementation: Unified Diff `apply_patch`

RCIR v8 introduces `apply_patch`, engineered specifically for robust agent modification:
1. **Unified Diff Format:** Accepts standard `--- a/file` and `+++ b/file` hunks.
2. **Context Alignment:** Matches surrounding context lines to locate the hunk even if file line numbers shifted.
3. **Automatic Pre-Edit Backup:** Backs up the original file into memory (`_original_files`) prior to any write.
4. **Syntax Validation & Atomic Rollback:**
   - Validates Python files via `ast.parse`.
   - Validates JSON files via `json.loads`.
   - If syntax errors occur, the file is **immediately rolled back** to the original state and a descriptive error message with line numbers is returned to the agent.
5. **Fallback:** `edit_file` is retained as a secondary fallback tool.

### Empirical Validation of `apply_patch`
- **Clean Patch Test:** Succeeded, modifying file and tracking relative path.
- **Corrupted Patch Test (Syntax Error):**
  - Input: Malformed python statement `return (def syntax error`.
  - Output: `ERROR: Patch produced Python SyntaxError at line 2: invalid syntax. File changes rolled back.`
  - Verification: Target file contents remained 100% identical to original; `_modified_files` remained empty.

---

## 3. Phase 16: Turn Budget Protocol

The agent loop evaluates task completion across 3 turn budgets:
- **5 turns:** Quick bug fix (Inspect -> Patch -> Verify -> Finish).
- **10 turns:** Moderate cross-file fix with 1 test failure repair cycle.
- **20 turns:** Complex multi-component refactor with iterative debugging.

Under Phase 16 rules:
> "Do not infer that five-turn failure means RCIR failure."
A turn exhaustion must record exact turn counts, tool calls, and test results rather than falsely blaming retrieval.

---

## 4. Phase 17: Adaptive Orchestration via Task-Risk Router

Instead of running all 6 stages (Maker $\to$ Reviewer $\to$ Implementer $\to$ Reviewer $\to$ Gatekeeper $\to$ Historian) for every minor edit, `TaskRiskRouter` dynamically routes requests:

| Risk Category | Inferred Conditions | Pipeline Stages | Average Token Footprint | Token Savings vs Fixed 6-Stage |
|---|---|---|---|---|
| **LOCAL_BUG** | Local scope, rename, small bug | Retriever $\to$ Implementer $\to$ Reviewer $\to$ Gatekeeper (4 stages) | **~12,000 tokens** | **45.5% savings** |
| **CROSS_MODULE** | Standard multi-file feature | Maker $\to$ Retriever $\to$ Implementer $\to$ Reviewer $\to$ Gatekeeper $\to$ Historian (6 stages) | **~22,000 tokens** | Baseline standard |
| **ARCHITECTURE_REFACTOR** | Schema change, service boundary, database migration | Maker $\to$ Reviewer $\to$ Maker $\to$ Implementer $\to$ Reviewer $\to$ Gatekeeper $\to$ Historian (7 stages) | **~32,000 tokens** | Rigorous deep review |

---

## 5. Phase 20: Valid E2E Agent Success Criteria

To eliminate fabricated agent success:
1. **Actual Source Change Required:** A non-empty git diff must exist (`git_diff_length > 0`).
2. **Fresh Test Execution:** Pre-existing passing tests on unchanged code are **NOT** implementation success. Tests must execute after the diff is applied.
3. **Gatekeeper Approval:** Gatekeeper evaluates test exit code (0), absence of regressions, and scope compliance before emitting `APPROVE`.
