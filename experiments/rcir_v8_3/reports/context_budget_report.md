# RCIR v8.3 — Context Budget Curve (2k, 4k, 8k) Efficiency Report

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Macro CriticalRecall@2k**: 20.59%  
**Macro CriticalRecall@4k**: 25.34%  
**Macro CriticalRecall@8k**: 29.45%  

## 1. Context Efficiency Curve
```text
CriticalRecall
  100% ┼
   80% ┼                                   ● (8k: 29.4%)
   60% ┼
   40% ┼                      ● (4k: 25.3%)
   20% ┼         ● (2k: 20.6%)
    0% ┼─────────┴────────────┴────────────┴────
               2,000        4,000        8,000 tokens
```

## 2. Interpretation
Expanding the budget from 2,000 to 8,000 tokens reliably increases critical ground-truth recall as caller and test quotas are filled with fine-grained source spans.
