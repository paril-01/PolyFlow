# 🔄 Master End-to-End Sequential Pipeline Protocol

## Purpose
This protocol defines the formal specification for executing the 5 specialized AEF agents in a **single, automated, synchronized sequence**.

Instead of manually invoking agents one by one, the End-to-End Pipeline executes the SDLC lifecycle automatically:

```
[Problem Statement]
        │
        ▼
┌─────────────────┐
│ 1. Maker Agent  │ ──► (Requirements Spec + ADRs + Risk Register)
└────────┬────────┘
        │
        ▼
┌─────────────────┐
│ 2. Reviewer     │ ──► (Adversarial Design Review + Severity Matrix)
│    (Design)     │
└────────┬────────┘
        │
        ▼
┌─────────────────┐
│ 3. Implementer  │ ──► (Production Code + Tests + Self-Review Log)
└────────┬────────┘
        │
        ▼
┌─────────────────┐
│ 4. Reviewer     │ ──► (Adversarial Code & Security Review)
│    (Code)       │
└────────┬────────┘
        │
        ▼
┌─────────────────┐
│ 5. Gatekeeper   │ ──► (Release Decision: APPROVE / CONDITIONAL / REJECT)
└────────┬────────┘
        │
        ▼
┌─────────────────┐
│ 6. Historian    │ ──► (Engineering Memory + Decision Log + Tech Debt)
└─────────────────┘
```

---

## Pipeline Execution Rules

1. **Strict Hand-off**: Output from Stage N becomes input context for Stage N+1.
2. **Adversarial Gate**: If Stage 2 (Design Review) or Stage 4 (Code Review) surfaces **P0/P1 issues**, the pipeline loops back to the previous agent (Maker or Implementer) to resolve the findings before proceeding.
3. **Immutable Context**: Every stage inherits the [Engineering Constitution](../constitution/CONSTITUTION.md).
4. **Artifact Persistence**: All intermediate and final artifacts are saved automatically to `.aef_output/` or repository paths.

---

## Stage-by-Stage Contract

### Stage 1: Discovery & Architecture (Maker Agent)
- **Role**: `agents/maker/system-prompt.md`
- **Input**: User Request / Feature Statement
- **Output Artifacts**:
  - `requirements-spec.md`
  - `ADR-001.md`
  - `risk-register.md`

### Stage 2: Design Validation (Reviewer Agent)
- **Role**: `agents/reviewer/system-prompt.md`
- **Input**: Stage 1 Output Artifacts
- **Evaluation**: 12 Engineering Review Dimensions
- **Output Artifacts**:
  - `design-review-report.md` (Verdict: APPROVE / CONDITIONAL / REJECT)

### Stage 3: Production Coding & Testing (Implementer Agent)
- **Role**: `agents/implementer/system-prompt.md`
- **Input**: Approved Design Spec & ADRs
- **Output Artifacts**:
  - Source Code Files
  - Test Suite & Execution Logs
  - `self-review-checklist.md`

### Stage 4: Code & Security Verification (Reviewer Agent)
- **Role**: `agents/reviewer/system-prompt.md`
- **Input**: Source Code, Test Suite, and Self-Review Checklist
- **Output Artifacts**:
  - `code-review-report.md` (P0–P4 Severity Log & Verdict)

### Stage 5: Release Verification (Gatekeeper Agent)
- **Role**: `agents/gatekeeper/system-prompt.md`
- **Input**: Code Review Report, Test Coverage Logs, Rollback Plan
- **Output Artifacts**:
  - `gate-review-report.md` (Final Release Status)

### Stage 6: Institutional Memory (Historian Agent)
- **Role**: `agents/historian/system-prompt.md`
- **Input**: Complete Lifecycle Execution Trail
- **Output Artifacts**:
  - `engineering-memory-log.md`
  - `technical-debt-registry.md`
  - Knowledge Graph Updates

---

## How to Execute the Pipeline

### Option 1: Automated Python CLI Orchestrator
Run the built-in orchestrator engine from your terminal:
```bash
python -m orchestrator "Build a REST API for task management"
```

### Option 2: Single-Prompt LLM Pipeline Execution
Copy the text below into any LLM session (Claude, GPT, Gemini, Cursor) to run the pipeline sequentially:

```text
[SYSTEM INSTRUCTION: AEF PIPELINE RUNNER]
Execute the 5 AEF agents sequentially for the following request:
"<YOUR FEATURE REQUEST>"

Follow the Master Pipeline Protocol:
1. Run Maker Agent (Requirements & ADRs)
2. Run Reviewer Agent (Adversarial Design Review)
3. Run Implementer Agent (Code & Tests)
4. Run Reviewer Agent (Code & Security Review)
5. Run Gatekeeper Agent (Release Decision)
6. Run Historian Agent (Memory & Tech Debt Log)

Produce the outputs for each stage clearly demarcated by headers.
```
