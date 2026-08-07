# Coding Standards

See [Implementer Agent — Code Standards](../agents/implementer/code-standards.md) for the complete, detailed coding standards.

## Quick Reference

### Principles
1. **SOLID** — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
2. **DRY** — Don't Repeat Yourself (but prefer duplication over wrong abstraction)
3. **KISS** — Keep It Simple, Stupid
4. **YAGNI** — You Ain't Gonna Need It

### Key Rules
- Functions: single responsibility, <20 lines, <4 parameters
- Naming: descriptive, consistent, searchable
- Error handling: explicit, never swallowed
- Comments: explain WHY, not WHAT
- No magic numbers, no commented-out code, no dead code
