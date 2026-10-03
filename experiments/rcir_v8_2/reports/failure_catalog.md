# RCIR v8.2 — Failure Catalog

> Source artifacts: `results/silent_miss_catalog.json`, `results/gate_evaluation.json`

## Failed Gates (6/7)

- **impact_recall**: Global & Macro Pool Recall
- **silent_miss_limit**: Silent Miss Limit
- **context_precision**: Context Precision (P@20 and P@50)
- **context_ndcg**: Ranking Quality Graded nDCG@50
- **critical_budget_recall**: Critical Recall @ 4k Budget
- **real_agent_e2e**: Live Verified Agent E2E Execution

## Passed Gates (1/7)

- **context_mrr**: Mean Reciprocal Rank (MRR)

## Silent Miss Catalog (Top 20)

| Task | File | Root Cause |
|------|------|------------|
| TASK-1 | `tests/lib/Preview/PreviewPixelsTrait.php` | PHP trait usage in test hierarchy was not linked via direct class inheritance edges in the static graph. |
| TASK-2 | `apps/comments/lib/Activity/Listener.php` | Event listener accesses Node::getId() from untyped event payload; receiver type was not propagated interprocedurally. |
| TASK-2 | `apps/dav/lib/BulkUpload/BulkUploadPlugin.php` | Node instance stored in Sabre DAV plugin property without explicit property type hint; receiver resolved as ambiguous. |
| TASK-2 | `apps/dav/lib/Connector/Sabre/TagsPlugin.php` | Untyped node parameter passed through Sabre tree navigation methods. |
| TASK-2 | `apps/dav/lib/DAV/ViewOnlyPlugin.php` | Distant property access getId() on untyped receiver. |
| TASK-2 | `apps/files/lib/Service/TagService.php` | TagService receives NodeInterface; implementation implements NodeInterface but resolution was ambiguous. |
| TASK-2 | `apps/files/tests/Service/TagServiceTest.php` | Test file was 2 hops away through TagService, which was pruned when TagService was dropped from pool. |
| TASK-2 | `apps/files_sharing/lib/Listener/RestrictInteractionListener.` | Listener unwraps Node entity from event object without explicit variable type hint. |
| TASK-2 | `apps/files_versions/lib/Sabre/VersionCollection.php` | Sabre version collection iterates child nodes using untyped foreach loop. |
| TASK-2 | `core/BackgroundJobs/GenerateMetadataJob.php` | Background job receives fileId scalar integer from cron/job queue and loads Node dynamically. |
| TASK-2 | `lib/private/Encryption/Update.php` | Traversal policy under HIGH fanout mode pruned 2-hop storage updater path. |
| TASK-2 | `lib/private/Files/Template/TemplateManager.php` | Dynamic template node instantiation via factory method without return type annotation. |
| TASK-2 | `lib/private/Preview/Generator.php` | Generator was 2 hops away via FileView and was pruned due to degree thresholding. |
| TASK-2 | `lib/private/Preview/MP3.php` | MP3 preview provider depended on Generator.php; dropped cascadingly. |
| TASK-2 | `lib/public/Files/Template/Template.php` | Public template class wraps internal Node instance without typed property hint. |
| TASK-2 | `tests/lib/FilesMetadata/FilesMetadataManagerTest.php` | Test class 2 hops away was truncated under HIGH fanout mode. |
| TASK-3 | `lib/composer/composer/autoload_classmap.php` | Composer generated autoload mapping contains class name strings. Build artifact, not hand-edited source. |
| TASK-3 | `lib/composer/composer/autoload_static.php` | Composer static loader table contains class name map. Build artifact. |
| TASK-4 | `lib/public/ServerVersion.php` | Static facade calls \OC::$server->getConfig() via global static container accessor. |
| TASK-4 | `lib/public/Util.php` | Static facade \OCP\Util::getVersion() delegates to static container service. |

## Root Cause Distribution

The primary causes of silent misses are:
1. **Missing graph edges** — dependency relationships not captured in the static graph
2. **Threshold pruning** — candidates pruned by traversal policy limits
3. **Unresolvable entities** — files referenced in ground truth but absent from the graph
