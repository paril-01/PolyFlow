# RCIR v8.5 — Benchmark Integrity & Provenance Report

## Executive Summary
This report establishes the baseline integrity and verification state for the **RCIR v8.5** benchmark evaluation within PolyFlow. In strict accordance with **Rule 0** (Observation before Claim), all evaluations operate exclusively against the verified Nextcloud Server tree with fail-fast sentinels and cryptographic content hashes.

## Target Repository State
- **Target Repository**: `nextcloud/server`
- **Verified Commit**: `da57df078d0808a7235a0177bd99d23c010b472e`
- **Working Tree State**: `CLEAN`
- **PolyFlow Baseline Commit**: `48c6f6170891173e46582466c248e9d882b693a5`
- **PolyFlow Dirty**: `True`
- **Run ID**: `rcir-v8.5.2-3ddfcbf688cd4401`

## Sentinel File Verification
The single source root architecture enforces strict fail-fast verification on the following sentinels:
- `lib/public/IConfig.php`: Verified present
- `apps/files`: Verified present
- `.git`: Verified present
- `version.php`: Verified present
- `lib/private/Server.php`: Verified present
- `core/Command/Base.php`: Verified present

## Integrity Gate Results
- **Provenance Status**: `PASSED`
- **Total Audited Tasks**: `16`
- **Total Errors**: `0`
- **Token Budget Invariant**: Satisfied (0 budget violations)
- **Source Availability**: 100% verified real source files; zero synthetic stubs.
