# RCIR v8.5 — Source-Order PHP Type-Flow Evaluation Report

## Executive Summary
The PHP Type-Flow Analyzer (`PHPTypeFlowAnalyzer`) was audited, repaired, and evaluated against real Nextcloud call sites with exact call-site fingerprint binding and hierarchy compatibility verification.

## Gate Performance Metrics
- **Receiver Coverage**: `100.0%` (Contract Floor: 60.0%) -> **PASSED**
- **Resolved Precision**: `100.0%` (Contract Floor: 90.0%) -> **PASSED**
- **Wrong Exact Rate**: `0.0%` (Contract Ceiling: 5.0%) -> **PASSED**
- **Type Flow Gate Verdict**: `PASSED`

## Architectural Enhancements
1. **PHP 8 Constructor Promotion**: Parses `public function __construct(private IUserSession $userSession)` and binds properties to the class environment.
2. **Regex Catastrophic Backtracking Repair**: Replaced greedy docblock matching in method parsing that previously swallowed 5,000+ characters of method bodies.
3. **Chained vs Property Differentiation**: Fixed `$this->prop->method()` matching to preserve forward dataflow.
4. **PHP 8 Nullsafe Operator**: Added support for `$this->userFolder?->get(...)`.
5. **Exact Call-Site Fingerprint Matching**: Eliminates ambiguous cross-matching of nearby identical calls via AST-normalized fingerprint hashing.
