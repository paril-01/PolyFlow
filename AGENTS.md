# PolyFlow Workspace Rules

## Active Specification
- Master spec: `plans/MASTER_IDE_EXECUTION_SPEC.md` — read before any phase work.
- Phase state: `templates/PHASE_STATE.json` — check at session start.

## Behavioral Contract (Always Active)
1. **Default mode is READ-ONLY.** No code changes without an explicitly approved ticket.
2. **Distinguish evidence types:** `OBSERVED_SOURCE`, `OBSERVED_EXECUTION`, `PROPOSED`, `UNVERIFIED`, `NOT_RUN`, `BLOCKED`, `RETRACTED`.
3. **Never fabricate:** Do not invent test results, hashes, benchmark values, model identity, or credit savings. Report `NOT_RUN` if not actually executed.
4. **Stop on blocked gates.** Do not self-promote past a phase gate. Request human review.
5. **Minimum reversible change.** Propose the smallest scoped patch. No bulk rewrites without evidence they're needed.
6. **Preserve interpreter.** `polyflow/`, SDK, `.poly` runtime are frozen unless a separate regression-backed ticket is approved.
7. **Respect file ownership.** Only modify files listed in the current approved ticket's `owned_paths`.
8. **Label every test claim** with command, exit code, log path. If not run, say `NOT_RUN`.
9. **No direct changes to `main`.** Use `work/<ticket-slug>` branches off verified SHA.
10. **Record tool/model identity.** Capture actual model ID, IDE version, and tool versions used.

## Project Boundaries
- **PolyFlow interpreter** → independent of Agent Pool internals
- **RCIR** → independent of AEF gatekeeper/approvals; read-only `ContextEvidenceBundle` API
- **Agent Pool / AEF 3.2** → standalone in `paril-01/agents`; independent of PolyFlow
- **Do not merge repositories.** The `agents/` folder in PolyFlow is legacy role docs, not AEF 3.2.

## Phase Output Template (Mandatory)
Every phase output must include: PHASE, REPO/SHA/BRANCH/DIRTY, AUTHORIZATION, FILES READ, EVIDENCE TABLE, PLAN, CHANGES, COMMANDS, TESTS, RISKS/BLOCKERS, PROHIBITED ACTIONS, GATE STATUS, NEXT ACTION.

## Source-of-Truth Priority
1. User's explicit authorization and security approvals
2. Current SHA, live raw test/log outputs, native tool receipts
3. Reviewed plan v3 and approved tickets
4. AEF 3.2 / architecture references (labeled PROPOSED)
5. Old Markdown reports (NOT proof)
