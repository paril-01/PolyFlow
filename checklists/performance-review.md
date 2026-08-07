# Performance Review Checklist

- [ ] Performance targets are defined (response time, throughput)
- [ ] Database queries use appropriate indexes
- [ ] No N+1 query problems
- [ ] Pagination implemented for list endpoints
- [ ] Caching used where reads >> writes
- [ ] No blocking operations on hot paths
- [ ] Connection pools configured appropriately
- [ ] Resource limits set (memory, connections, threads)
- [ ] Timeouts configured for all external calls
- [ ] No memory leaks (resources cleaned up)
- [ ] Large payloads use streaming/chunking
- [ ] Benchmarks run against performance targets
