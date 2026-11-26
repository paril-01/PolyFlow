# RCIR development package

Source evidence SDK, CLI and read-only MCP server. Development version
`0.2.0.dev0`; benchmark and release acceptance are pending. No measured coding
improvement, token savings or native IDE credit savings is claimed.

## Install and use

Python 3.10+ and Git are required. The verified local environment used Python
3.12.2, tiktoken 0.14.0 and MCP SDK 2.3.0. Install the stdio extra for MCP:

```sh
python -m pip install './rcir[mcp]'
rcir index --repo /absolute/repository --ref EXACT_COMMIT
rcir query --repo /absolute/repository --query 'calculate' --budget 4000
rcir impact --repo /absolute/repository --path module.py
rcir serve --repo /absolute/repository --transport stdio
rcir verify-run --run /absolute/sealed-run
```

Commands refuse dirty source unless `--allow-overlay` is explicit. A requested
ref must match the checked-out commit. Snapshot identity includes actual source
bytes and policy; refresh is an atomic full rebuild, not a claimed incremental
speedup. Saved index output is a source manifest; startup rebuilds the index.
Default manifests live outside the target in the user's cache directory.

For an MCP client with executable/argument configuration, use its documented
stdio entrypoint with command `rcir` and arguments
`["serve", "--repo", "/absolute/repository", "--transport", "stdio"]`.
The captured real Python SDK client initialization/list/call test is
[test_rcir_service_mcp.py](../tests/test_rcir_service_mcp.py). A native IDE session
has not been measured. Server stdout contains protocol traffic only.

```python
from rcir.service import RepositoryService

service = RepositoryService('/absolute/repository', ref='EXACT_COMMIT')
bundle = service.retrieve('calculate', 4000, required_symbols=['Calculator.calculate'])
expanded = service.expand(bundle['evidence_items'][0]['evidence_id'], 4000)
service.refresh()  # rebuild after intentional edits; old handles become stale
```

## Guarantees and limits

- Source paths remain inside the declared root. Symlinks, evaluator directory
  names, credentials, vendored/generated paths and unsupported binary files are
  excluded. This policy is not secret detection: configure a repository without
  secrets and keep evaluator material outside it. No shell or write MCP tools.
- Python definitions use AST qualified names and actual UTF-8 byte offsets.
  Other languages use lexical candidates labeled `INFERRED`. Python import
  impact is a cycle-safe static module closure, with explicit partial coverage;
  dynamic dispatch and a complete call graph are unsupported.
- Bytes and hashes are verified before and after delivery. A source change
  returns `STALE`; missing or evicted expansion returns `UNRESOLVED`. Required
  duplicate symbols return `AMBIGUOUS`. A pinned span that cannot fit returns
  `BUDGET_INSUFFICIENT`.
- SDK/CLI token counts cover compact sorted UTF-8 JSON. MCP counts cover the
  compact serialized tool result, including escaping and content metadata.
  JSON-RPC framing, request IDs, transport, provider wrappers, schemas and client
  prompts are outside these delivery budgets and must be counted separately in
  whole-request studies. Encoding is cl100k_base, not a claim about another
  model's native billing tokenizer. Error messages can exceed a tiny requested
  budget and explicitly report failure instead of successful delivery.
- The supplementary router is **off by default**. Its optional adjacent-line
  presentation is lossy and scoped by tenant/snapshot/policy, with bounded TTL,
  LRU and byte storage. Protected content passes through. Originals become
  unavailable after expiry/eviction. Upstream Headroom integration and comparison
  remain unimplemented; no Headroom code is bundled.
- Canonical graph and hybrid candidates are experimental DEV arms. They are
  not selected architectures. Supplied graphs must bind to the exact commit.

## Studies and reproducibility

Product and benchmark commands are separate:

```sh
python scripts/run_retrieval_study.py --help
python scripts/run_product_study.py --help
```

The retrieval command requires separate public queries and source-hashed private
critical spans, exact source identity, an unused output directory, and explicit
arms. It retains every delivered span, measures each budget and query latency,
and seals receipts with SHA-256. It does not pick a winner or grant release.
The old bakeoff entrypoint now requires these same explicit arguments.

The product study commands validate protocol structure, export base-only source
without future Git objects, qualify base/reference/irrelevant-edit controls,
run explicitly bounded local Ollama DEV agents, evaluate captured changes in a
separate sandbox, check Linux bubblewrap and recompute metrics. A
directory is not a security boundary: Windows host execution is refused and no
fallback runs agent commands on the host. The independent controller is in
[agent_trial.py](../experiments/benchmark_core/agent_trial.py); it records raw
requests, responses, native usage and tool actions. Complete file changes include
untracked/binary content, hashes and executable modes; capture never runs host
Git against an agent-modified config. Missing usage remains null.
Trial retrieval ignores Git metadata entirely; the separate controller receipt
binds the exported upstream base SHA, while the source-only context reports a
null commit and actual byte-derived snapshot identity.
Arbitrary test
commands must have qualified exit-code semantics: 0 pass, 1 assertion failure,
other exits setup/execution errors. Control execution alone does not establish
task validity. A curator-reviewed dataset, frozen candidate and real model runs
are still needed. Protocol validation
checks structure, not authenticity of an external curator's signature.

Use `run-dev`, `qualify` and `evaluate` subcommand help for their explicit
inputs. These execute only on Linux with working bubblewrap; source export
refuses symlinks/submodules requiring separate materialization. The controller
caps source capture at 256 MB / 16 MB per file, sandbox address space at 2 GB,
and output files at 8 MB. Dependency-heavy repositories need an explicitly
prepared toolchain/image adapter. A/B only is supported; unqualified C/D arms
fail rather than silently substituting another treatment. The synthetic sandbox
integration fixture is software validation, not a historical task or LLM result.

Intention-to-treat counts retain failed trials. Secondary efficiency uses only
both-successful pairs with actual native usage and task-cluster bootstrap
intervals. Missing native usage or IDE credits remain null. Integrity manifests
are hashes, not signatures, correctness proof or independent acceptance.

See [implementation progress](../plans/rcir_proof/PROGRESS.md) for exact observed
commands, failures, source identities and outstanding master-plan requirements.
