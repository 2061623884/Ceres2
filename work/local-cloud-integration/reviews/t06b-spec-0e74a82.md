# T06-B independent Spec review

Fixed HEAD: `0e74a8210371bc00960a2c06b5046ea94b18689f`; baseline: `8186897ee58d7bf0702b17cfe86509c32c27ccfa`. Owner-confirmed clean worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-runtime`. Commands: `git diff 8186897ee58d7bf0702b17cfe86509c32c27ccfa...0e74a8210371bc00960a2c06b5046ea94b18689f` and matching `git log --format=fuller`; outputs saved alongside.

## Result

Zero new missing, incorrect, or out-of-scope behavior findings in the inspected B-stage delta.

- Spec “GraphRAG 是显式可选关系查询路径，确定性 recipe_facts 保留”: `runtime/pi/src/worker.ts` adds only search_recipe_relations with local/global choices. Python dispatch calls the existing official-backend DishService.graph_search. Ordinary search_dishes, product and policy paths do not invoke graph. Prompt distinguishes explicit relation exploration from known-recipe facts and corrects its obsolete budget wording to 15 seconds.
- Spec “模型选择与规范事实来源分别呈现和计量”: `_graph_lookup` records attempts, official calls, provider completions, embeddings, model-selected IDs and canonical scope separately. `_graph_message` explains host community expansion versus model selection, reports graph provenance, and disclaims safety/nutrition/substitution/purchase authority. Unknown observed counts propagate as null rather than invented zero; the complete summary survives the bounded event tail.
- Existing native dish_refs are issued only from backend-returned canonical recipes, remain per-run Python references, and still pass the T03 primary-field/membership checks. recipe_facts renders required/optional/unknown quantities from canonical records; optional facts do not authorize procurement. Ingredient product output rereads current catalog/Offer through the existing host path. Graph text itself cannot inject quantities or product facts into final recipe rendering.
- Spec “缺索引/失败不能伪称已执行图查询”: handled graph failures yield outcome:error, no dish refs and explicit unknown wording; successful zero matches yield empty with different wording. The side message composes with valid policy references and role boundaries in the same final publication, without a new primary-answer schema.
- Original catalog.deadline/should_stop reach the graph service; the Pi loop rechecks after return before another model turn, and existing final stop/stale/deadline/transaction fences remain unchanged. No budget reset, automatic purchase, frontend or shared-schema expansion was introduced.

## Limits

Static review only; no tests, installs, builds, APIs or models executed. New public regression source covers Local/Global mixed results, errors/empty, forged refs, normal graph-free facts, current Offer/interim coexistence, summary truncation, stop and deadline. In-progress deeper coexistence results are not inherited as passed. Controlled graph transport evidence does not establish real-LLM graph quality, UI acceptance or final whole-branch same-pin verification.
