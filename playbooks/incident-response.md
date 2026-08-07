# Playbook: Incident Response

## When to Use
A production system is experiencing issues affecting users.

## Process

### Step 1: Detect & Triage (0-5 minutes)
1. Confirm the incident — is there a real problem?
2. Assess severity: P0 (system down), P1 (major impact), P2 (minor impact)
3. Assign an incident commander
4. Start an incident log with timestamps

### Step 2: Communicate (5-10 minutes)
1. Notify the on-call team
2. Update the status page
3. Set up a communication channel for the incident
4. Communicate to stakeholders: "We are aware and investigating"

### Step 3: Investigate (10+ minutes)
1. Check recent deployments — did anything change?
2. Check monitoring dashboards — what metrics are abnormal?
3. Check logs — what errors are occurring?
4. Narrow down to the affected component

### Step 4: Mitigate
1. **Decide**: fix forward or roll back?
2. If rolling back: deploy the previous version
3. If fixing forward: apply the minimal fix
4. Verify the mitigation worked
5. Update stakeholders

### Step 5: Resolve
1. Confirm the system is stable
2. Monitor for recurrence
3. Update the status page
4. Communicate resolution to stakeholders

### Step 6: Postmortem (within 48 hours)
1. Conduct a blameless postmortem
2. Document timeline, root cause, and resolution
3. Define preventive actions (specific, assigned, time-bound)
4. **Historian Agent** records the incident
5. Share learnings with the team

## Severity Definitions

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | System completely down | Immediate — all hands |
| P1 | Major feature broken, significant user impact | Within 15 minutes |
| P2 | Minor feature broken, workaround available | Within 1 hour |
| P3 | Cosmetic issue, no user impact | Next business day |
