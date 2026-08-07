# Approved Architecture Patterns

## When to Use Each Pattern

| Pattern | Best For | Avoid When |
|---------|----------|------------|
| **Layered (N-tier)** | Traditional CRUD apps, small teams | Complex domain logic |
| **Clean Architecture** | Complex business logic, long-lived projects | Simple CRUD with no business rules |
| **Hexagonal (Ports & Adapters)** | High testability needs, multiple interfaces | Simple apps, prototypes |
| **Event-Driven** | Loose coupling, async workflows, microservices | Simple request-response apps |
| **CQRS** | Different read/write models needed | Simple CRUD |
| **Microservices** | Large teams, independent deployment needs | Small teams, early-stage products |
| **Monolith** | Small teams, early stage, uncertain requirements | Large independent teams |
| **Modular Monolith** | Growing team, preparing for potential decomposition | Already need independent deployment |

## Architecture Selection Criteria

Choose based on:
1. **Team size** — smaller teams benefit from simpler architectures
2. **Domain complexity** — complex domains need Clean/Hexagonal architecture
3. **Scale requirements** — high scale may need event-driven or microservices
4. **Deployment needs** — independent deployment needs suggest microservices
5. **Team experience** — use patterns the team understands

## Key Principles (All Patterns)
- **Separation of concerns** — each layer/module has a single responsibility
- **Dependency inversion** — depend on abstractions, not concretions
- **Loose coupling** — modules communicate through interfaces
- **High cohesion** — related code lives together
- **Single direction dependency flow** — no circular dependencies
