# Inherited direct Pi stdio fixture adaptation

Source: integration4eb8b7497ef8a04581fd68e84c1cd7202849a7bc, safely fast-forwarded into the05 worktree. Frozen seven-slice full suite recorded378 passes and1 failure in486.23s. The failing node is backend/tests/test_runtime_pi_product_query.py::test_actual_pi_stdio_contract_emits_sdk_events_and_scoped_tool_requests.

## Contract finding

The direct test start frame omitted context and promptModules after05 made both mandatory. The production Python sender already supplies context including the existing Kev capability, plus keke_modules(); the current TypeScript Start interface requires both. The fixture's omission caused a terminal PI_RUNTIME_ERROR/TypeError before the expected result. No production sender/receiver mismatch was found in this path.

The correction changes only that fixture: include factual_qa with its minimal ordinary context and obtain the real host promptModules from keke_modules(). All existing tool-scope, arguments, rounds, result reference, run ID, sequence, SDK event, provider call count and secret-nondisclosure assertions remain untouched. No fallback, production prompt or active TASK06 worker code was changed.

## Sole Tester evidence

Evidence root: integration work/next-experience/10/.

- runs/seven-baseline-full/{record.json,output.log}: historical frozen378/1, retained unchanged.
- checks/inherited-stdio-runtime/{record.json,output.log}: fresh runtime build/typecheck before reproduction.
- runs/inherited-stdio-red/{record.json,output.log}: targeted inherited failure reproduced on unchanged4eb8b749 before editing.
- runs/inherited-stdio-green/{record.json,output.log}: corrected direct stdio fixture plus entire runtime/context batch30/30 passed in88.85s; candidate source unchanged.

The targeted30/30 result does not relabel the frozen full-suite result as passing. A future full-suite run must record its own source and result. No real-provider/browser/person acceptance is claimed.
