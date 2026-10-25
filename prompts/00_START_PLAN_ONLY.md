# Phase A0: Baseline Census — PLAN ONLY / READ-ONLY

## Authorization
- **Phase:** `A0_BASELINE`
- **Mode:** `READ_ONLY`
- **Write permission:** NONE — do not create, modify, or delete any repository files.
- **Output:** IDE plan artifact only. Stop after delivery and request review.

## Instructions

1. **Verify repository state:**
   - Run `git rev-parse HEAD` and confirm SHA matches `ea221b91890047d101ebd5a6f8f3a4c2457faeb2`.
   - Run `git status --short` and record any dirty/untracked files.
   - Run `git submodule status --recursive` and record initialization state.
   - Record local Python version, pytest availability, and tool versions.

2. **Inspect CI failures:** For each of the 4 failing GitHub Actions workflows listed in the master spec Section B, identify:
   - Which tests/checks actually fail and why (from source inspection, not guessing).
   - Whether the failure is in test logic, source code, fixture data, or configuration.

3. **Verify the 8 tickets (PF-P0-001 through PF-P0-008):**
   - For each ticket, inspect the actual source files listed.
   - Confirm or amend the failure description against current source.
   - Note any files that don't exist or have changed since the spec was written.

4. **Produce the A0 evidence table** using the mandatory output template from the master spec Section F.

5. **Map file ownership:** For each file in the ownership matrix (spec Section I), verify it exists and note its current state.

6. **Identify unknowns and blockers** — anything that cannot be verified from source inspection alone.

## DO NOT
- Write any code or patches
- Create branches or commits
- Run benchmarks or model-dependent tests
- Generate reports as if they are verified results
- Self-approve or proceed to A1 without human review
