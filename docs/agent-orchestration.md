# 🔄 Agent Orchestration Guide

This document explains how the 5 specialized AEF agents interact and hand off state throughout the development process.

---

## The Hand-Off Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant M as 🔍 Maker Agent
    participant R as 🔬 Reviewer Agent
    participant I as ⚙️ Implementer Agent
    participant G as 🚪 Gatekeeper Agent
    participant H as 📚 Historian Agent

    Developer->>M: Feature Request / Problem Statement
    M->>M: Requirement Discovery & ADR Generation
    M->>R: Hand off Design Artifacts & ADRs
    
    R->>R: Review across 12 Dimensions
    alt Findings Present (P0-P1)
        R-->>M: Return for Design Revision
    else Design Approved
        R->>I: Validated Design Spec
    end

    I->>I: Minimal Safe Implementation + Self-Review + Tests
    I->>R: Submit Code Diff & Test Execution Log

    R->>R: Adversarial Code & Security Review
    alt Code Deficiencies Found
        R-->>I: Request Code Fixes
    else Code Approved
        R->>G: Code Review Report & Test Proof
    end

    G->>G: Check Release Criteria & Production Readiness
    alt Gate Criteria Passed
        G->>Developer: APPROVE (Ready for Deploy)
        G->>H: Update Engineering Memory & Technical Debt
    else Gate Criteria Failed
        G-->>Developer: REJECT / CONDITIONAL APPROVAL
    end
```

---

## Inter-Agent Contracts

### Contract 1: Maker → Reviewer
- **Artifacts Handed Off**:
  - Requirements Specification (Functional + NFR)
  - Architecture Decision Records (ADRs)
  - Assumption & Risk Register
- **Gate Criteria**:
  - All non-functional metrics must have explicit targets (e.g. latency < 200ms p95).
  - Alternatives considered must be documented.

### Contract 2: Reviewer → Implementer
- **Artifacts Handed Off**:
  - Approved Design Specification
  - List of design trade-offs to preserve
  - Specific edge cases highlighted for testing

### Contract 3: Implementer → Reviewer
- **Artifacts Handed Off**:
  - Git Diff / Code Changes
  - Unit & Integration Test Results
  - Completed Self-Review Checklist

### Contract 4: Reviewer → Gatekeeper
- **Artifacts Handed Off**:
  - Code Review Report (P0–P4 severity log)
  - Verdict (APPROVE / CONDITIONAL / REJECT)

### Contract 5: Gatekeeper → Historian
- **Artifacts Handed Off**:
  - Final Release Summary
  - Registered Technical Debt (if any)
  - Traceability Matrix Update
