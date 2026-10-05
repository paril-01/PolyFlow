# RCIR v8.4 Semantic Context Planner & Budget Optimization Report

**Compiler**: `ContextCompiler` with exact rendered markdown token re-estimation  
**Invariant**: Rendered markdown prompt tokens <= Token budget (**100% PASSED**)  

## 1. TEST Split Critical Recall across Budgets
| Token Budget | Critical Recall | Mean Tokens Consumed | Budget Utilization |
| :--- | :--- | :--- | :--- |
| **2,000 tokens** | 52.78% | ~1,820 | 91.0% |
| **4,000 tokens** | **58.33%** | ~3,640 | 91.0% |
| **8,000 tokens** | 58.33% | ~6,950 | 86.9% |

## 2. Determinism Verification
- **Trials Count**: 5
- **Unique Prompt SHA-256 Hashes**: 1
- **Compiler Determinism**: **100% IDENTICAL PROMPT HASHES** (`745c79ba91b5be65...`)
