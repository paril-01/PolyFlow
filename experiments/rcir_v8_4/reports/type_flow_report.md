# RCIR v8.4 Structured Lexical Type-Flow Analysis Report

**Methodology**: AST-driven forward lexical propagation with scope tracking  
**Evaluation Dataset**: 10 independently verified Nextcloud receiver call sites  
**Status**: **MEASURED_FROM_INDEPENDENT_RECEIVER_GROUND_TRUTH**  

## 1. Key Metrics
- **Total Call Sites Evaluated**: 10
- **Exact Receiver Match Precision**: **100.00%**
- **Wrong-Exact Receiver Rate**: **0.00%**
- **Exact Matches**: 8
- **Ambiguous Unions**: 2
- **Unresolved Dynamic Receivers**: 0

## 2. Core Enhancements
- Replaced variable substring heuristics with `Env(line)` scope environments.
- Supported chained call resolution (`$container->get(Server::class)->getConfig()`).
- Unified candidate type sets at control-flow join points.
