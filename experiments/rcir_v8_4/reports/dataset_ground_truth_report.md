# RCIR v8.4 Benchmark Dataset & Ground Truth Report

**Total Tasks**: 20 stratified tasks across 3 splits  
**Adjudication Source**: Upstream Nextcloud pull requests and commits  
**Inheritance Status**: ZERO inheritance from compromised v8.2/v8.3 ground truth  

## 1. Split Allocation
- **DEV Split**: 8 tasks (`TASK-DEV-01` to `TASK-DEV-08`) — for candidate expansion tuning.
- **VALIDATION Split**: 6 tasks (`TASK-VAL-01` to `TASK-VAL-06`) — for ranker parameter tuning.
- **TEST Split**: 6 tasks (`TASK-TEST-01` to `TASK-TEST-06`) — **SEALED**, evaluated strictly once for gates.

## 2. Task Category Diversity
- Route changes (`apps/files`, `apps/dav`, `apps/activity`)
- Configuration mutations (`OCP\IConfig`, `OCP\SystemTag`)
- Event listeners & dispatchers (`NodeDeletedEvent`, `NodeCreatedEvent`)
- Security & Authentication contracts (`ISecureRandom`, `IUserSession`)
