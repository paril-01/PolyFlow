# RCIR Nextcloud Validation: Failure & Limitation Catalog

**Target Repository**: Nextcloud Server (`https://github.com/nextcloud/server`)  
**Validation Date**: 2026-10-01  
**Environment**: Windows 11, Python 3.12.3, Intel Core i7-1360P, 16GB RAM  
**Scope**: 11,793 files, 926,080 LOC, 49,720 extracted graph nodes, 109,089 edges  

---

## 1. Executive Summary

During the extreme real-world validation of PolyFlow and RCIR against Nextcloud Server, empirical testing identified **7 primary failure modes and architectural limitations**. Each failure was categorized by root cause, measured against ground truth, and traced to specific architectural mechanisms.

| ID | Title | Root Cause Category | Impact on Analysis | Severity |
|---|---|---|---|---|
| **FC-001** | Missing Native PHP AST Parser | Parsing / Architecture | Regex scanner extracts top-level structures but lacks statement-level AST | **High** |
| **FC-002** | Declarative Framework Routing Indirection | Framework Indirection | URL endpoints mapped via nested PHP arrays rather than direct method calls | **Medium** |
| **FC-003** | Cross-Language Frontend-to-Backend Disconnection | Polyglot Boundary | TypeScript frontend API client calls not resolved to PHP controller actions | **High** |
| **FC-004** | Dynamic Variable Type Ambiguity | Dynamic Behavior | Common method names (e.g. `getId()`) cannot disambiguate receiver class without type flow | **High** |
| **FC-005** | Event-Driven Architectural Decoupling | Design Pattern Indirection | Dynamic event dispatchers decouple publishers from listeners at static analysis time | **Medium** |
| **FC-006** | Host Runtime Toolchain Absence | System Environment | Host lacks PHP runtime, blocking live dynamic test suite execution | **Medium** |
| **FC-007** | PolyFlow Runtime Synthetic Execution Paths | Codebase Implementation | `polyflow/runtime.py` contains hardcoded fake success paths for non-Python cells | **Critical** |

---

## 2. Exhaustive Failure Mode Analysis

### FC-001: Missing Native PHP AST Parser
- **Root Cause**: RCIR was originally designed around Python's built-in `ast` module. Nextcloud is 61.6% PHP (570,205 LOC). Prior to Phase B-hardening, RCIR had **0% PHP capability**.
- **Hardening Action**: We engineered `rcir/src/rcir/graph/php_scanner.py`, an optimized regex scanner capturing namespaces, imports, class/interface/trait declarations, inheritance, method signatures, static calls, DI lookups, and event dispatch.
- **Remaining Limitation**: Because regex cannot build a full Concrete Syntax Tree (CST) or track block-level lexical scope:
  - Local variable reassignments (e.g., `$obj = $this->getService(); $obj->run();`) lose their static type target.
  - Complex anonymous closures and nested arrow functions can obscure parameter types.
- **Evidence**: On MUT-006 (`getId`), regex-based scanning achieved 76.8% precision but only 13.3% recall on un-annotated variable method calls.

---

### FC-002: Declarative Framework Routing Indirection
- **Root Cause**: Nextcloud routes are not registered via standard Python decorators or Java annotations. Instead, Nextcloud uses:
  1. `apps/<app>/appinfo/routes.php`: Returning an associative array defining URL patterns, verb, and controller method.
  2. Docblock annotations: `@NoAdminRequired`, `@PublicPage`, `@UseSession`.
- **Measurement**: Ground truth edge `GT-006` (`apps/files/appinfo/routes.php -> ApiController::getThumbnail`) was classified as `partial_match`.
- **Root Cause Analysis**: The target method `ApiController::getThumbnail` was present in the graph, but the connection from `routes.php` to the method was absent because `routes.php` returns an array config literal rather than invoking the method directly.

---

### FC-003: Cross-Language Frontend-to-Backend Disconnection
- **Root Cause**: Nextcloud's frontend is Vue.js and TypeScript (`apps/files/src/services/Files.ts`), communicating over HTTP REST/OCS endpoints to PHP controllers.
- **Measurement**: Ground truth edge `GT-010` (`Files.ts -> /apps/files/api/v1/recent`) was a **silent miss** (0% recall).
- **Impact**: When an agent renames or modifies a backend API route, frontend callers in TypeScript/Vue remain undetected unless an explicit cross-language contract layer links URL string literals to backend route definitions.
- **Architectural Gap**: RCIR's `polyglot_scanner.py` supported gRPC and Python HTTP decorators (Flask, FastAPI, Django), but lacked a route-compiler bridge connecting frontend REST URLs to PHP OCS routes.

---

### FC-004: Dynamic Variable Type Ambiguity
- **Root Cause**: In PHP, variables are untyped unless explicitly declared in parameter signatures or docblocks. In `MUT-006` (`getId()`), 399 files in Nextcloud call a method named `getId()`.
- **Measurement**:
  - Ground truth referencing files: 399
  - RCIR affected files identified: 69
  - True Positives: 53
  - Recall: 13.3%
  - Precision: 76.8%
- **Analysis**: RCIR correctly refused to blindly match all 399 occurrences of `->getId()` across unrelated domain objects (User, Group, Session, File, Storage), prioritizing precision over false-positive explosion. However, without inter-procedural type inference, it silently missed valid calls where the receiver variable was typed in an upstream caller.

---

### FC-005: Event-Driven Architectural Decoupling
- **Root Cause**: Nextcloud uses PSR-14 event dispatching via `OCP\EventDispatcher\IEventDispatcher::dispatch($event)`.
- **Measurement**:
  - Ground truth edge `GT-009` (`Node.php -> NodeDeletedEvent`) was a `partial_match`.
  - In `MUT-004` (`NodeDeletedEvent`), RCIR achieved 88.9% recall and 100.0% precision (16/18 files identified).
- **Gap**: The two missed files registered listeners dynamically inside XML descriptors (`appinfo/info.xml`) or runtime service registration hooks, which static code scanning does not execute.

---

### FC-006: Host Runtime Toolchain Absence
- **Observation**: The host operating system environment lacks native `php` and `go` CLI runtimes:
  - `php --version` -> CommandNotFoundException
  - `go version` -> CommandNotFoundException
- **Impact on Validation**:
  - Dynamic PHP unit test execution (`phpunit`) could not be run locally.
  - All correctness and impact verifications had to rely on AST/static extraction, independent ripgrep ground-truth verification, and structural contract evaluation.

---

### FC-007: PolyFlow Runtime Synthetic Execution Paths
- **Observation**: During code audit of `polyflow/runtime.py`:
  - `_execute_java_cell` (L395-416) and `_execute_go_cell` (L418-438) return hardcoded mock execution dictionaries when called.
  - `fast_native_mode` (L184-199) returns fabricated success results for all non-Python languages.
- **Validation Assessment**:
  - PolyFlow's runtime cannot be claimed to natively execute polyglot workflows without containerized execution or real host compilers.
  - Any benchmark claiming true end-to-end execution of multi-language polyflow cells must explicitly run in `fast_native_mode=False` with real compilers, or declare non-Python runtime execution as **SIMULATED**.
