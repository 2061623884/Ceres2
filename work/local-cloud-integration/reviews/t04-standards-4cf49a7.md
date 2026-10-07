# T04 final test-only binding: Standards

Final pin: `4cf49a72f1a6e07c94204a02f1220ad054d03b24`.

Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T04-interim`, clean and at the final pin when inspected.

Exact delta: `git diff 0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1...4cf49a72f1a6e07c94204a02f1220ad054d03b24`.

Commit list: `git log 0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1..4cf49a72f1a6e07c94204a02f1220ad054d03b24 --format='%H %s'`; single commit 4cf49a7. Diff/list saved alongside this report.

Zero new hard or judgment findings. Only `backend/tests/test_official_deepseek_thinking.py` changes: the primary Pi wire expectation now requires tool_choice=auto and no response_format, matching accepted T03 native completion. The independent 256-token validator branch, thinking behavior, model/token limits and official/spoofed/nonofficial hostname assertions remain intact.

Production source diff from previously reviewed `39adf78abcfbc49f4efb6b25cb066fbd6fbedb4b` is empty across backend/app, runtime/pi/src, frontend and data. This is a final test-only pin binding, not a repeated production review.

The parent reports the final 92-test group GREEN at this pin with stable source/harness. No tests, builds, services, installations, APIs or product edits were performed by this reviewer.

T04 Standards is clear at `4cf49a72f1a6e07c94204a02f1220ad054d03b24`, with the earlier cause-preservation finding closed. Independent Spec, merge verification, frontend integration and final whole-branch acceptance remain separate gates.
