# 🚀 Getting Started with AEF

Welcome to the **AI Engineering Framework (AEF)**. This guide will help you get up and running with AEF in your software development workflow.

---

## 1. Quick Concept Overview

AEF is an **Engineering Operating System** for AI-assisted software development. Instead of using generic LLM prompts, AEF structures your AI interactions around five specialized engineering agents, supported by a formal constitution, playbooks, checklists, and templates.

```
                  ┌────────────────────────┐
                  │ 🏛️ Engineering        │
                  │    Constitution        │
                  └───────────┬────────────┘
                              │
  ┌─────────────┬─────────────┼─────────────┬─────────────┐
  ▼             ▼             ▼             ▼             ▼
🔍 Maker    🔬 Reviewer  ⚙️ Implementer 🚪 Gatekeeper 📚 Historian
(Design)    (Review)     (Code)        (Release)    (Memory)
```

---

## 2. Setting Up AEF for Your Project

### Option A: Integrate into Existing Repository
Copy the `agents/`, `constitution/`, `templates/`, and `checklists/` directories into your repository root or a `.aef/` directory.

### Option B: Use as a Global Reference
Keep AEF in a central location or repository, and paste relevant agent prompts into your AI coding assistant (VS Code, Cursor, Windsurf, Claude, ChatGPT, Custom IDE).

---

## 3. Your First Workflow: Building a Feature

Follow these steps for any new feature:

### Step 1: Discovery & Design (Maker Agent)
1. Load [`agents/maker/system-prompt.md`](../agents/maker/system-prompt.md) into your AI assistant.
2. Prompt: *"We need to build [feature description]. Please run requirement discovery and generate an initial architecture design."*
3. Answer the Maker's discovery questions.
4. Output: Requirements specification and ADRs.

### Step 2: Independent Review (Reviewer Agent)
1. Load [`agents/reviewer/system-prompt.md`](../agents/reviewer/system-prompt.md).
2. Prompt: *"Please perform an adversarial review of this design across all 12 dimensions."*
3. Output: Review report with severity findings (P0–P4) and verdict.
4. Resolve any P0/P1 findings with the Maker.

### Step 3: Production Implementation (Implementer Agent)
1. Load [`agents/implementer/system-prompt.md`](../agents/implementer/system-prompt.md).
2. Prompt: *"Implement the approved design following minimal safe change principles and SOLID design standards."*
3. Output: Source code, unit/integration tests, inline docs, and self-review checklist.

### Step 4: Verification & Code Review (Reviewer Agent)
1. Load [`agents/reviewer/system-prompt.md`](../agents/reviewer/system-prompt.md).
2. Review the code diff, test cases, and error handling logic.

### Step 5: Release Decision (Gatekeeper Agent)
1. Load [`agents/gatekeeper/system-prompt.md`](../agents/gatekeeper/system-prompt.md).
2. Verify all production readiness criteria.
3. Output: **Approve**, **Conditional Approval**, or **Reject**.

### Step 6: Engineering Memory Record (Historian Agent)
1. Load [`agents/historian/system-prompt.md`](../agents/historian/system-prompt.md).
2. Record the final ADRs, implementation notes, and technical debt.

---

## 4. Supporting Resources

- 📖 **Playbooks**: Step-by-step guides for bug triage, database migrations, security audits, etc. ([`playbooks/`](../playbooks/))
- ✅ **Checklists**: Verification lists for code review, deployment, security ([`checklists/`](../checklists/))
- 📄 **Templates**: Standard markdown templates for ADRs, design docs, postmortems ([`templates/`](../templates/))
