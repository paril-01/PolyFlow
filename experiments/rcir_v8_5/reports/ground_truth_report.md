# RCIR v8.5 — Ground Truth Provenance & Dataset Report

## Overview
The RCIR v8.5 ground truth comprises **16 real Nextcloud tasks** constructed directly from commit `da57df078d0808a7235a0177bd99d23c010b472e` of `nextcloud/server`. All tasks have bitwise-verified file content hashes (SHA-256) and verified AST entity targets.

## Dataset Split Allocation
- **DEV Split**: 6 tasks (`TASK-DEV-01` to `TASK-DEV-06`)
- **VALIDATION Split**: 5 tasks (`TASK-VAL-01` to `TASK-VAL-05`) — Used strictly for ranker profile selection
- **TEST Split**: 5 tasks (`TASK-TEST-01` to `TASK-TEST-05`) — Held out for frozen gate evaluation

## Adjudication Methodology
Every expected file is categorized into:
1. `critical_files`: Primary impact targets and immediate consumers.
2. `must_change`: Files requiring direct modifications.
3. `must_inspect`: Files containing call sites, routes, or contract tests requiring inspection.
4. `supporting_context`: Configuration schemas, sibling services, and fixtures.

All commit SHAs have been validated via `git cat-file -e` on the local Nextcloud git object database. Zero synthetic tasks exist in RCIR v8.5.
