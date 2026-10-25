---
name: polyflow-phase-execution
description: Skill for executing a specific phase of the PolyFlow/RCIR/AEF project. Read this before beginning any phase work. Covers the phase gate process, ticket format, output template, and behavioral guardrails.
---

# PolyFlow Phase Execution Skill

## Before Starting Any Phase

1. Read `AGENTS.md` for permanent workspace rules.
2. Read the relevant section of `plans/MASTER_IDE_EXECUTION_SPEC.md`.
3. Check `templates/PHASE_STATE.json` for current phase status.
4. Verify `git rev-parse HEAD` and `git status --short`.

## Phase Gate Protocol

Phases must execute in order. You cannot skip a phase or self-approve past a gate:

- **A0–A2**: Read-only research phases → require HUMAN REVIEW A
- **B0**: CI recovery (scoped code) → only approved tickets PF-P0-001 to 007
- **B1**: Retrieval spike (disposable branch) → experimental only
- **B2**: Deterministic bakeoff (evaluation) → require HUMAN REVIEW B
- **C0–C4**: Implementation and evaluation phases
- **D**: Product hardening

## Ticket Contract

Every code task must have an approved ticket with:
- `id`, `phase`, `repo`, `repo_sha`, `branch`, `mode`
- `objective`, `observable_behavior`
- `owned_paths` (only these files may be modified)
- `forbidden_paths` (never touch these)
- `acceptance_tests` (commands to run and verify)
- `negative_controls` (failure cases that must fail correctly)
- `approval: EXPLICIT_USER_SCOPED_APPROVAL_REQUIRED`

## Mandatory Output Template

Every phase must output:
```
PHASE: <phase_name>
REPO / SHA / BRANCH / DIRTY STATUS: ...
USER AUTHORIZATION FOR CURRENT ACTION: READ_ONLY / EXACT_APPROVAL_REF / ABSENT
FILES & DOCS ACTUALLY READ: path + SHA or line range
REQUIREMENT-TO-FILE MAPPING: R# => file/symbol => proposed edit or NO_EDIT
EVIDENCE TABLE: claim | source/command/log | OBSERVED/INFERRED/NOT_RUN | limitation
PLAN + ALTERNATIVE: chosen hypothesis / strongest simpler comparator / rejection test
WHAT CHANGED: exact paths, or NONE
COMMANDS EXECUTED: exact command, environment, exit code, captured log, or NOT_RUN
TESTS: passing, failing, skipped, not run; no invented counts
RISKS, BLOCKERS, UNKNOWNS: explicit
PROHIBITED ACTIONS RESPECTED: yes/no with evidence
GATE: PASS_FOR_SCOPE / BLOCKED / INCOMPLETE / NOT_EVALUATED
NEXT LEGAL ACTION: only the following permitted phase and required owner approval
```

## Evidence Classification

Every claim must be tagged:
- `OBSERVED_SOURCE` — directly read from source code
- `OBSERVED_EXECUTION` — from running a command with captured output
- `PROPOSED` — suggested but not verified
- `UNVERIFIED` — stated but not independently confirmed
- `NOT_RUN` — test/command was not executed
- `BLOCKED` — cannot proceed due to dependency/permission
- `RETRACTED` — previously stated, now withdrawn

## Guardrails

- Never fabricate test results, hashes, or model identity
- Never self-approve past a gate
- Never modify files not in `owned_paths`
- Never touch `polyflow/` without a separate approved ticket
- Stop on repeated failure, permission issues, or uncertain destructive ops
- Propose minimum reversible change
