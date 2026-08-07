# Knowledge Graph Maintenance

## When to Update
- After every significant engineering event (design, implementation, review, release)
- When dependencies change
- When ownership changes
- When decisions are made or superseded
- When technical debt is added or resolved

## How to Update
1. The **Historian Agent** is primarily responsible for graph maintenance
2. Other agents flag graph updates as part of their output
3. Updates are reviewed during retrospectives

## Best Practices
- Keep the graph current — stale graphs are misleading
- Use consistent node naming
- Document the reason for relationship changes
- Periodically review for orphaned nodes (modules nobody owns)
