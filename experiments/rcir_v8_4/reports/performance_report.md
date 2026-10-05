# RCIR v8.4 Benchmark Performance & Scalability Report

**Graph Scale**: 48,611 nodes, 143,225 edges (`nextcloud-server`)  

## 1. Latency & Memory Profile
- **Graph Parsing & Ingestion**: **3.74s**
- **Peak Ingestion Memory**: Low (<120MB) after O(1) canonical alias optimization.
- **Candidate Expansion Latency**: <12ms per task
- **Cascaded Ranker Latency**: <18ms per task
- **Context Package Compilation**: <8ms per task
