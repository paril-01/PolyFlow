# RCIR v8.2 — Context Compiler Report

> Source artifact: `results/context_compiler_evaluation.json`

## Configuration

- Token budget: 4000
- Span deduplication: True
- Target pinning: True

## Macro Averages

| Metric | Value |
|--------|-------|
| Context Precision | 28.07% |
| Context Recall | 31.61% |
| Critical Recall @ Budget | 33.88% |
| Token-Weighted Precision | 19.14% |
| Token-Weighted Recall | 40.68% |

## Per-Task Breakdown

| Task | Tokens / Budget | Context Precision | Context Recall | Critical Recall | Overshoot |
|------|----------------|-------------------|----------------|-----------------|-----------|
| TASK-1 | 3999 / 4000 | 42.9% | 50.0% | 37.5% | NO |
| TASK-2 | 3934 / 4000 | 22.2% | 5.8% | 8.3% | NO |
| TASK-3 | 3961 / 4000 | 23.1% | 33.3% | 54.5% | NO |
| TASK-4 | 3941 / 4000 | 46.2% | 2.2% | 2.3% | NO |
| TASK-5 | 3983 / 4000 | 6.1% | 66.7% | 66.7% | NO |

## Analysis

All tasks compiled within the 4,000-token budget (0 overshoots). CriticalRecall@Budget
of 33.88% falls short of the 60% target, indicating that
the compiler's span selection does not yet prioritize critical dependencies highly enough.
