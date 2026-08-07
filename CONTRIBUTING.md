# Contributing to AEF

Thank you for your interest in contributing to the **AI Engineering Framework (AEF)**! This document provides guidelines for contributing.

---

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include a clear title and description
- Provide steps to reproduce (if applicable)
- Label appropriately: `bug`, `enhancement`, `documentation`, `agent`, `playbook`, etc.

### Suggesting Enhancements

- Open a GitHub Issue with the `enhancement` label
- Describe the problem the enhancement would solve
- Propose a solution with rationale
- Reference any relevant engineering literature or industry standards

### Submitting Changes

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the guidelines below
4. **Test your changes** — ensure all markdown renders correctly
5. **Commit** with clear, descriptive messages
6. **Push** to your fork
7. **Open a Pull Request** against `main`

---

## Contribution Guidelines

### Content Standards

- **Be specific and actionable** — avoid vague generalities
- **Use evidence-based reasoning** — cite sources where applicable
- **Follow existing formatting** — match the style of surrounding documents
- **Think production-first** — every recommendation should work in real production environments

### Agent Contributions

When modifying or creating agents:

- System prompts must be **self-contained** — an agent should work with only its system prompt
- Workflows must be **step-by-step** — no ambiguity in process
- Examples must be **realistic** — not toy problems
- All agents must inherit from the [Engineering Constitution](constitution/)

### Playbook Contributions

When adding playbooks:

- Include **when to use** the playbook
- Provide a **step-by-step** process
- Include **decision points** with clear criteria
- Add **anti-patterns** — what NOT to do
- Include **examples** where possible

### Template Contributions

When adding templates:

- Include **instructions** for how to fill out each section
- Provide a **completed example**
- Keep fields **minimal but sufficient** — avoid bureaucratic overhead

### Documentation

- Use **clear, concise language**
- Include **code examples** where relevant
- Use **mermaid diagrams** for complex workflows
- Cross-reference related documents

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for everyone.

### Our Standards

- **Be respectful** — disagreement is welcome; disrespect is not
- **Be constructive** — feedback should help, not harm
- **Be evidence-based** — support claims with reasoning
- **Be collaborative** — we're building something together

### Enforcement

Unacceptable behavior may result in removal from the project. Contact the maintainers for concerns.

---

## Questions?

Open a GitHub Issue or reach out to the maintainers. We're happy to help!
