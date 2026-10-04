# RCIR v8.3 — Failure Mode & Silent Miss Catalog

**Run ID**: `rcir-v8.3-5537bf1bbca8`  
**Total Documented Silent Misses**: 98  

## 1. Catalog Breakdown by Root Cause
1. **Unresolved Indirect Callers**: Callers connected via dynamic container lookup (`OCP\Server::get(...)`).
2. **Beyond Traversal Horizon**: Tests located in peripheral sub-apps more than 2 hops away from the canonical target entity.
3. **Implicit Event Listeners**: Listeners registered via configuration array files without explicit method dispatch calls.

## 2. Catalog Excerpt (First 10 Misses)
| Task | Omitted Ground Truth File | Tier | Root Cause |
| :--- | :--- | :--- | :--- |
| `TASK-1` | `lib/private/Preview/Bitmap.php` | Tier 2 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/CDR.php` | Tier 1 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/Generator.php` | Tier 3 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/GeneratorHelper.php` | Tier 3 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/Heif.php` | Tier 1 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/Image.php` | Tier 2 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/Imaginary.php` | Tier 1 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/Krita.php` | Tier 1 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/MP3.php` | Tier 2 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
| `TASK-1` | `lib/private/Preview/MarkDown.php` | Tier 2 | `GRAPH_HORIZON_OR_UNRESOLVED_DISPATCH` |
