# Playbook: Bug Investigation

## When to Use
A bug has been reported and needs investigation and resolution.

## Process

### Step 1: Triage
1. **Reproduce the bug** — can you make it happen consistently?
2. **Assess severity** — using the [severity matrix](../agents/reviewer/severity-matrix.md)
3. **Assess impact** — how many users are affected?
4. **Check history** — has this been reported before? (consult **Historian Agent**)

### Step 2: Investigate
1. **Gather evidence** — logs, metrics, traces, user reports
2. **Isolate the problem** — narrow down to the smallest reproducible case
3. **Identify the root cause** — use [Root Cause Analysis](../constitution/root-cause-analysis.md)
4. **Document findings** — what you found and how

### Step 3: Plan the Fix
1. **Design the fix** — what is the minimal safe change?
2. **Assess risk** — could the fix break anything else?
3. **Plan testing** — how will you verify the fix works?
4. **Plan regression testing** — ensure the bug doesn't reoccur

### Step 4: Implement the Fix
1. **Implementer Agent** applies the minimal safe change
2. Write a test that fails without the fix and passes with it
3. Run the full test suite
4. Self-review the change

### Step 5: Review
1. **Reviewer Agent** reviews the fix
2. Verify the root cause is addressed, not just the symptom

### Step 6: Deploy
1. Follow normal deployment process
2. Verify the bug is fixed in production
3. Monitor for related issues

### Step 7: Postmortem (for P0/P1 bugs)
1. Document the bug, root cause, and fix
2. Identify preventive actions
3. **Historian Agent** records the incident

## Anti-Patterns
- 🚫 Fixing the symptom instead of the root cause
- 🚫 Not writing a regression test
- 🚫 Rushing to fix without understanding the problem
- 🚫 Making large, sweeping changes to fix a small bug
