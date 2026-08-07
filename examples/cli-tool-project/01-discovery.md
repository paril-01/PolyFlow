# CLI Tool Project — Discovery Phase

## User Request
"Build a CLI tool that analyzes code quality metrics for a Git repository."

## Maker Agent Output

### Problem Statement
Build a command-line tool that scans a Git repository and reports code quality metrics including file complexity, code duplication, test coverage gaps, and documentation completeness.

### Functional Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| FR-01 | Scan a directory for source files | Must |
| FR-02 | Calculate cyclomatic complexity per file | Must |
| FR-03 | Detect code duplication | Should |
| FR-04 | Check for missing docstrings/comments | Should |
| FR-05 | Generate summary report (terminal + JSON) | Must |
| FR-06 | Support Python and JavaScript initially | Must |
| FR-07 | Exit code reflects quality threshold | Must |

### Constraints
- Must work on Linux, macOS, and Windows
- No external service dependencies (runs locally)
- Python 3.9+ runtime
