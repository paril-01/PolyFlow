# 📦 AEF Adoption Guide

This guide describes strategies for introducing the AI Engineering Framework into individual projects, team workflows, or entire engineering organizations.

---

## Adoption Phases

### Phase 1: Lightweight Adoption (Individual Developer)
- **Step**: Use AEF agent prompts directly in your AI assistant (Cursor, Windsurf, Claude, VS Code).
- **Focus**: Use the **Reviewer Agent** prompt for self-reviewing PRs and the **Maker Agent** prompt when starting complex tasks.
- **Effort**: Low (Immediate value without repository changes).

### Phase 2: Repository-Level Adoption (Single Team)
- **Step**: Add AEF governance assets into the target project repository under `.aef/` or root directory.
- **Focus**: Enforce ADR templates ([`templates/adr-template.md`](../templates/adr-template.md)) and standard pull request checklists ([`checklists/code-review.md`](../checklists/code-review.md)).
- **Effort**: Medium (Team alignment on process).

### Phase 3: Enterprise / Multi-Repo Adoption (Organization-wide)
- **Step**: Standardize AEF across all projects. Use automated CI pipelines to check for ADRs, traceability matrices, and gatekeeper checklists.
- **Focus**: Maintain a central knowledge graph and technical debt registry across services.
- **Effort**: Full organizational alignment.

---

## Anti-Patterns During Adoption

1. **Trying to adopt everything at once**: Start with Maker and Reviewer agents first, then add Gatekeeper and Historian.
2. **Treating checklists as bureaucracy**: Checklists exist to prevent production failures, not to add paperwork. Keep them concise.
3. **Overriding constitutional rules for speed**: Skipping reviews or tests for speed causes long-term instability.
