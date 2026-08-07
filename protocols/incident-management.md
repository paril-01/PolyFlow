# Incident Management Protocol

## Trigger
Production system experiencing issues affecting users.

## Process
See [Incident Response Playbook](../playbooks/incident-response.md) for the complete step-by-step process.

## Summary
1. **Detect & Triage** (0-5 min): Confirm incident, assess severity, assign commander
2. **Communicate** (5-10 min): Notify stakeholders, update status
3. **Investigate** (10+ min): Check recent changes, logs, metrics
4. **Mitigate**: Roll back or fix forward
5. **Resolve**: Confirm stability, communicate resolution
6. **Postmortem** (within 48h): Root cause analysis, preventive actions

## Severity Response Times

| Severity | Response | Escalation |
|----------|----------|------------|
| P0 | Immediate | All hands |
| P1 | 15 minutes | Team lead |
| P2 | 1 hour | On-call |
| P3 | Next business day | Normal workflow |
