# T04 final test-only pin binding

Final HEAD: `4cf49a72f1a6e07c94204a02f1220ad054d03b24`; unchanged product pin: `39adf78abcfbc49f4efb6b25cb066fbd6fbedb4b`; previous reviewed final pin: `0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1`. Clean worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T04-interim`. Commands: `git diff 0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1...4cf49a72f1a6e07c94204a02f1220ad054d03b24` and matching `git log --format=fuller`; outputs saved alongside.

## Result

Final Spec clearance: zero new findings. This delta changes only `backend/tests/test_official_deepseek_thinking.py`; production remains exactly the previously reviewed 39adf78 source.

The primary Pi requests now assert tool_choice=auto and absence of response_format for both official and nonofficial providers, matching the approved T03 native finish protocol. The former official-primary forced-JSON expectation contradicted that protocol. The change does not weaken the independent validator: its 256-token allowance, no-tools wire shape, existing response_format expectation, structured verdict processing and approval assertion are retained. Primary 1536-token limits, configured model identity, streaming, official-host thinking-disabled profile and nonofficial-host exclusion checks remain intact.

This is a correction to a stale test expectation, not a product change or retroactive pass. The prior run with 90 passes/two old wire failures remains historical evidence. The subsequent 92-test GREEN is a separate Tester result on the final candidate and must retain its original source/build attribution.

Prior 3064fe1 full T04 static review and 0c77e59 diagnostics-delta review remain applicable to unchanged production. This final binding introduces no UI acceptance claim and does not replace final whole-branch same-pin verification.

No tests, builds, installs, model/API calls or product modifications were performed by this reviewer.
