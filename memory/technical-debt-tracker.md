# Technical Debt Tracker

```yaml
debt_items:
  - id: TD-001
    date_identified: 2026-08-07
    title: "Missing rate limiting on API endpoints"
    description: "No rate limiting is configured on any endpoint, making the API vulnerable to abuse"
    cause: "Deferred during MVP to meet timeline"
    impact: high  # low | medium | high | critical
    affected_components: ["task-api", "auth-api"]
    remediation_plan: "Implement rate limiting middleware with Redis-backed counter"
    estimated_effort: "2 days"
    priority: high
    status: open  # open | in_progress | resolved | accepted
    resolved_date: null
    resolution_notes: null
```

## Tracking Process
1. When debt is identified, create an entry with full context
2. Assess impact and priority
3. Include in sprint planning (allocate 10-20% capacity)
4. Track resolution and document what changed
5. Review debt trends quarterly
