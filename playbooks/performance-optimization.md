# Playbook: Performance Optimization

## When to Use
System performance doesn't meet requirements or has degraded over time.

## Process

### Step 1: Measure First
1. **Define the performance target** — what is "fast enough"? (specific numbers)
2. **Benchmark current performance** — measure before changing anything
3. **Identify the bottleneck** — use profiling tools, not intuition
4. **Document baseline** — record current metrics

### Step 2: Analyze
1. Profile the application (CPU, memory, I/O, network)
2. Analyze database queries (slow query log, explain plans)
3. Check for common issues: N+1 queries, missing indexes, memory leaks
4. Review caching strategy

### Step 3: Optimize
1. Fix the **biggest bottleneck first** — Pareto principle (80/20)
2. Make **one change at a time** — measure after each change
3. Prefer **algorithmic improvements** over hardware scaling
4. Add **caching** where reads far exceed writes
5. Add **indexes** for frequently queried columns

### Step 4: Verify
1. Re-benchmark after each change
2. Compare against the target
3. Run the full test suite — optimizations must not break correctness
4. Load test under realistic conditions

### Step 5: Document
1. Document what was optimized and why
2. Document the trade-offs (e.g., more memory for less CPU)
3. Record performance budgets for future monitoring

## Key Rules
- ✅ Measure before optimizing
- ✅ Optimize the bottleneck, not what you think is slow
- ✅ Correctness ALWAYS takes priority over performance
- ❌ Never optimize without a benchmark
- ❌ Never sacrifice readability for micro-optimizations
