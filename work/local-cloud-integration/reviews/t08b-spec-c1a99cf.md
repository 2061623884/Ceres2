# T08-B Spec closure review

Frozen target: c1a99cf27f54647bce32b9d07c4511bdd7a65941. Prior target: eebb326d14c2a6f8b91279c3da8ff82aa883f0e1. Diff: git diff eebb326...c1a99cf; matching commits and diff saved alongside. Reviewed T08-runtime and integration spec/TASK, read-only; no test execution.

Both prior P2 findings are closed by static inspection; no new actionable Spec finding in this delta.

1. pi_product_turn_service.py:48–80 now installs the retrieval observer before _process context construction. Initial projection reads, later Pi reads, and final projection share the same counters. Early events and totals are transferred into Pi without reconstructing them from the bounded tail. Pre-Pi failure rolls back staged work and persists only observed retrieval evidence alongside admission metadata; unobserved provider counters remain absent. The finally reset covers early errors and successful processing. The new public stream regression covers initial success/failure and final projection. This addresses the spec requirement “完整 runtime_summary 独立于裁剪后的详细事件尾部”.
2. export_runs.py:22 preserves method in the diagnostic allowlist, including graph_queries summary and detailed events. Local, Global, and unknown values are explicitly covered by a new test. This addresses “官方 Local/Global 与模型选择结果分别记录”.

The runtime protocol test adjustment correctly accounts for runtime_version/provider observations without removing SDK ordering checks. Tester must establish execution at this exact pin. Static closure is not final integrated, live-provider, browser, or user acceptance.
