# Paired Token Measurement Methodology (Section 12 & 26)

1. **Native Provider Usage Records:**
   All token numbers are recorded directly from the provider response payload (`prompt_eval_count` and `eval_count` from Ollama's native inference engine).
2. **Paired Experimental Design:**
   Each task runs in fresh worktrees across identical turn budgets (turn 5 and turn 8) under two isolated conditions:
   - Condition A: Tool-enabled agent without RCIR
   - Condition B: Tool-enabled agent with RCIR
3. **Three Distinct Token Measurements:**
   - **Semantic Representation Compression:** Ratio of raw source serialization to canonical PolyFlow `.poly` contracts.
   - **RCIR Task-Context Compression:** Ratio of unbounded broad context to contract-bounded delivered context.
   - **Live Model Tokens:** Exact provider-measured prompt and completion tokens.
4. **Credit Attribution:**
   Cloud IDE credits are explicitly flagged as `NOT_MEASURED` to maintain strict empirical truthfulness (Rule 0).
