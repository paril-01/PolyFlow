# RCIR v8.4 Failure Catalog & Silent Miss Analysis

**Split Evaluated**: TEST  
**Total Silent Misses**: 12  

## 1. Root-Cause Categorization
1. **Unregistered Template Files** (e.g. `apps/files/templates/index.php`):
   - Templates are referenced via runtime PHP helper calls rather than static class inheritance or imports.
2. **Cross-Package Sub-Test Suites** (e.g. `tests/lib/ConfigTest.php`):
   - Some unit test suites reference test utility base classes instead of directly importing the subject under test.
3. **Dynamic Service Factory Magic**:
   - Container resolutions using string service identifiers that escape AST type flow.
