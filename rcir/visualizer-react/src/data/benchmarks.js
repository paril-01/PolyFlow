/**
 * Benchmark comparisons: Method A (Full-File Naive) vs Method B (RCIR Dependency Graph).
 * Extracted from real benchmark runs on Python codebases.
 */

export const BENCHMARK_DATA = {
  benchmark_timestamp: "2026-09-05T12:11:04Z",
  tasks: [
    {
      task_id: "task_1_validation_rule",
      title: "Debug Guard Violation in Rule Validation Engine",
      query: "guards rule validation execution and AST inspection",
      service: "Recommendation & Rule Validation",
      method_a_conventional: {
        name: "Method A: Full-File Context & Naive Invalidation",
        total_tokens: 7226,
        noise_ratio_percent: 94.2,
        files_ingested: 3,
        invalidation_blast_radius: "9 files (transitive)",
        cache_hit_retention_percent: 14.5
      },
      method_b_rcir: {
        name: "Method B: RCIR Dependency-Graph Context Runtime",
        total_tokens: 1850,
        token_budget: 2000,
        noise_ratio_percent: 5.9,
        nodes_selected: 8,
        invalidation_blast_radius: "2 nodes (local only)",
        cache_hit_retention_percent: 88.2
      },
      metrics: {
        token_savings_percent: 74.4,
        blast_radius_reduction_percent: 77.8,
        signal_to_noise_gain_factor: 16.0
      }
    },
    {
      task_id: "task_2_merkle_audit",
      title: "Verify Merkle Hash Chain Integrity & Audit Entries",
      query: "audit merkle hash chain ledger verify chain record entry",
      service: "Cryptographic Verification & State Ledger",
      method_a_conventional: {
        name: "Method A: Full-File Context & Naive Invalidation",
        total_tokens: 7489,
        noise_ratio_percent: 94.4,
        files_ingested: 3,
        invalidation_blast_radius: "9 files (transitive)",
        cache_hit_retention_percent: 14.5
      },
      method_b_rcir: {
        name: "Method B: RCIR Dependency-Graph Context Runtime",
        total_tokens: 1850,
        token_budget: 2000,
        noise_ratio_percent: 5.9,
        nodes_selected: 8,
        invalidation_blast_radius: "2 nodes (local only)",
        cache_hit_retention_percent: 88.2
      },
      metrics: {
        token_savings_percent: 75.3,
        blast_radius_reduction_percent: 77.8,
        signal_to_noise_gain_factor: 16.0
      }
    },
    {
      task_id: "task_3_body_refactor",
      title: "Refactor Internal AST Node Extraction Logic (Body-only edit)",
      query: "extract import module inspect ast regex guards",
      service: "AST AST-Parser & Microservice Nodes",
      method_a_conventional: {
        name: "Method A: Full-File Context & Naive Invalidation",
        total_tokens: 3813,
        noise_ratio_percent: 76.8,
        files_ingested: 2,
        invalidation_blast_radius: "3 files (transitive)",
        cache_hit_retention_percent: 14.5
      },
      method_b_rcir: {
        name: "Method B: RCIR Dependency-Graph Context Runtime",
        total_tokens: 1120,
        token_budget: 2000,
        noise_ratio_percent: 5.9,
        nodes_selected: 6,
        invalidation_blast_radius: "1 node (body-only edit)",
        cache_hit_retention_percent: 96.4
      },
      metrics: {
        token_savings_percent: 70.6,
        blast_radius_reduction_percent: 66.7,
        signal_to_noise_gain_factor: 13.0
      }
    }
  ],
  aggregate: {
    average_tokens_per_prompt: {
      method_a: 6176,
      method_b: 1606,
      reduction_percent: 74.0
    },
    average_noise_ratio: {
      method_a: "88.5%",
      method_b: "5.9%"
    },
    average_invalidation_blast_radius: {
      method_a: "7.3 files re-indexed",
      method_b: "1.7 nodes updated"
    },
    economic_projection_1000_iterations: {
      token_cost_method_a_usd: 18.53,
      token_cost_method_b_usd: 4.82,
      net_savings_usd: 13.71,
      efficiency_multiplier: 3.8
    },
    latency_ttft_impact: {
      method_a_estimated_ttft_ms: "1,450ms (large prompt)",
      method_b_estimated_ttft_ms: "180ms (budgeted 2k prompt)",
      speedup_factor: "8.1x faster time-to-first-token"
    }
  }
};
