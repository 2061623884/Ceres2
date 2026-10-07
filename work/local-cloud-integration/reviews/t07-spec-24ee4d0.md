# T07 Mercury hookup: independent Spec review

Frozen HEAD: `24ee4d03268cfd16b9a171acc7fe6dced465768c`; product: `79a7efffadaeac3706dc54db2066f6ababcb6848`. Clean worktree at inspection: `/workspace/scratch/0c1b4cfa2ef3/ceres2_t07_aftersales`.

Commands: `git diff ccf272b752f096ce0d80f7d0a4f29b19c05b0a77...24ee4d03268cfd16b9a171acc7fe6dced465768c`; `git log --format=fuller ccf272b752f096ce0d80f7d0a4f29b19c05b0a77..24ee4d03268cfd16b9a171acc7fe6dced465768c`. Overall baseline diff also saved: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...24ee4d03268cfd16b9a171acc7fe6dced465768c`. This review covers the hookup delta, not final whole-branch acceptance.

## Result

Zero missing, incorrect, or unrequested behavior findings in this delta.

- Spec “按真实知识快照更新所有调用方”: `backend/app/mercury/tools.py::schemas/execute` both use the same ten `policy.CATEGORIES`. The public regression covers all ten through Mercury HTTP and confirms no application receipt is produced.
- Spec “知识 worker 排锁、启动、写入、等待与读取必须消耗同一个剩余 deadline”: `graph.py::_run_query` retains `accepted_at + 15`; `build_graph.read_tools` passes that exact absolute deadline into `tools.execute`, then `policy.search_policies`, then `KnowledgeService.search/_query`. No renewed 30-second budget enters this route. Five-round behavior is unchanged.
- Spec “error 不伪装成 empty”: source/index errors still propagate from `policy.search_policies` and become query failure, while actual zero hits retain the explicit unknown-policy summary. Neither fallback evidence nor invented success was added.
- Spec “LangGraph 负责售后” and “文字不触发 Kev”: existing persistent LangGraph and navigation authorization remain unchanged. Owner/order/selection/generation fences, explicit confirmation, immutable proposal flow, and previously corrected exact-ticket evidence scope are untouched.

Cancellation scope: existing model-timeout cancellation and late read-result discard remain intact; the knowledge worker now expires against the same deadline. Mercury has no existing explicit stop callback to forward, and this delta does not claim or add one. This is not a certification of whole-branch cancellation/publication behavior.

Tester evidence independently records 63 affected tests passing on product `79a7eff`; interrupted pre-build output is invalid. No tests, installs, services, real API, or repository edits were performed by this reviewer. Final same-pin integrated verification and overall two-axis review remain required.
