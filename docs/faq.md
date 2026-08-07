# ❓ Frequently Asked Questions (FAQ)

### Q1: Is AEF tied to a specific programming language or framework?
**No.** AEF is completely language-agnostic, architecture-agnostic, and framework-agnostic. It governs *engineering discipline*, not language syntax.

### Q2: Do I need a specific LLM or AI coding tool to use AEF?
**No.** AEF system prompts and workflows work with Claude, GPT-4o, Gemini, Llama, Cursor, Windsurf, VS Code Copilot, or any other LLM interface.

### Q3: Isn't this process too heavy for small projects or MVPs?
**No.** AEF is scalable. For small projects, you can combine Maker + Implementer steps in one session, but keeping the *Reviewer* and *Gatekeeper* verification steps ensures you don't build buggy, unmaintainable software.

### Q4: How does AEF handle technical debt?
Technical debt is explicitly tracked by the **Historian Agent** in the Technical Debt Tracker schema. Shortcuts taken during MVP stages are logged with severity, impact, and remediation plans rather than forgotten.

### Q5: Can I customize the Engineering Constitution?
Yes. While the base constitution provides universal software engineering principles, teams can append project-specific safety rules or governance policies in `constitution/`.
