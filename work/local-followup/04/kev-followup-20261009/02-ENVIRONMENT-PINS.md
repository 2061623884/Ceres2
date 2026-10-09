# 02 B0 non-secret environment pins

Date: 2026-10-09. This is a bounded, read-only handoff of safe launch and index metadata for the active B0. It does not inspect the 02 raw batch, private cases, the original `.env`, application database, checkpoint contents, or model request bodies; it makes no HTTP or model calls and does not change the API, Kev service, source, fixtures, or indexes.

## Launch selection and runtime identity

- Worktree HEAD is `f9d7b44870e447c1f592a12163ad443b17782980`, tree `f6dd1554335b9da351a89ec825b3c6034d47c2e5`. The B0 freeze records that the API in exec session `78420` was started from `9e9be1da8ef7dd7ba630a2025e63835612e4795e`; the later HEAD change is docs/state-only. This report does not inspect the process or claim that its loaded modules equal current disk files. Runtime `source_revision`, `build_revision`, and `prompt_revision` remain unknown until the B0 capture records them.
- The approved, non-secret model selection already recorded for the 01 launcher and B0 freeze is `deepseek-flash` for primary response, Memory extraction, and Dream, using `api.deepseek.com`. The fixed Kev endpoint is `http://127.0.0.1:8009`, model label `kev-latest`, with a 3-second route/judgment timeout. The Guide stream budget is 15 seconds. No `.env` value or key hash was read or recorded.
- The 01 safe launch metadata does not record the selected `LLM_MODE`; this field remains unknown rather than inferred from the source default. The current TypeScript and Python official-DeepSeek helpers set `thinking: {type: "disabled"}` when the configured host is exactly `api.deepseek.com`; this is a disk-source behavior pin, not independent evidence of the active process's wire body.
- The existing launcher `serve_baseline.py` pins the isolated state directory to `data/runtime/kev-followup-20261009/baseline/`, with `ceres2.sqlite3`, `mercury-checkpoints.sqlite3`, and a private `tmp/` child. It binds the Ceres API to `127.0.0.1:8017` and points Kev to `127.0.0.1:8009`. The launcher reads the approved model and Memory fields only when starting a process; this metadata-only check did not relaunch it.

## Current BGE and index identity

- Current source and Graph manifest both pin `BAAI/bge-small-zh-v1.5`, revision `7999e1d3359715c523056ef9478215996d62a620`, 512 dimensions. The on-disk Hugging Face tree metadata SHA-256 is `70ab3a152b39753ca0815774a822d5ca35d7716aafa40b6d0b8e23e6598fed71`. The previously completed component verification recorded primary weight blob SHA-256 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026`; the large weight blob was not re-read for this handoff.
- The current hybrid artifact SHA-256 is `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`. The current GraphRAG manifest SHA-256 is `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`; its safe identity fields report graph revision `ceres-recipe-byog-v4`, GraphRAG `3.2.0`, completion model `deepseek-flash` at `api.deepseek.com`, and the same BGE revision/dimensions. The 01 report's knowledge index revision is `fb981e66e2cd272a9a32a6da9db49512dd7a55142e3ccf59afbdc43ee1bb2c01`. No index was opened for content or rewritten.

## Current disk source/build hashes

These hashes identify current files on disk only. B0 captures remain authoritative for the actual loaded source/build/prompt revisions.

| Scope | File | SHA-256 |
| --- | --- | --- |
| API launcher | `work/local-followup/04/kev-followup-20261009/serve_baseline.py` | `af65cd78c7045da48d186fdedf27e9306b1a41194e71b9e351a7d6a89f7dc3d8` |
| Safe config loader | `work/local-followup/04/real-model-20261008/harness_config.py` | `9a5caa0ba6adbe62aa04b36b14eee5db09a678cb4074d9bc0e192704b21139c3` |
| Runtime worker source | `runtime/pi/src/worker.ts` | `6d3c8661fb6ff84087352c96bbed22032e636d7b283735551c87926fd80197d3` |
| Runtime worker build | `runtime/pi/dist/worker.js` | `b3de5c2655878e88fbc9f5d8614aa33dba27e179413e4b8f3076ccf6dd1c7e97` |
| Prompt module source | `runtime/pi/src/prompt-modules.ts` | `d58e0adddc7adba7a07573dc6453910b9d2810a62dbaa76ca90f241bbcc9b1d2` |
| Prompt module build | `runtime/pi/dist/prompt-modules.js` | `3223f61a244db77262e30da2980d97584507b0244f5230f7e61078c7999e5d1d` |
| Interim claim source | `runtime/pi/src/general-claim.ts` | `b533be86d49da2009a54cca16929dd30df0227b98331cb8fa644c4a24bb78b4d` |
| Interim claim build | `runtime/pi/dist/general-claim.js` | `95b8d7fbcafd4ee179bab17efb446ca73544f4d4fdb8d85a283baa38ffc0eb68` |
| DeepSeek request source/build | `runtime/pi/src/official-deepseek.ts` | `62613e886f354907be25384f437017a04258e5f7065f285b8ea9bced6937e367` |
| DeepSeek request build | `runtime/pi/dist/official-deepseek.js` | `ff9313e72e592167c91527df900931a9b266dd275ffa2885f531326d57c9b62c` |
| Python experience prompt | `backend/app/prompts/experience.json` | `29fb0d1491ba130d6fbab2b3309a81155cac76867ab300121cddb19ab5e060d7` |
| Python prompt projection | `backend/app/prompts/experience.py` | `d66693ea9c11b7d5ff50df83c133389f0d7104d013f10f6194dc7666a26502a3` |
| Memory background worker | `backend/app/services/memory_background.py` | `2faffdf6f725acdf2b01f444eefd6345c5c2dabc895fadb7e853026e0f839f36` |
| Memory model adapter | `backend/app/services/memory_model.py` | `6a1e059e8c78c52e8dfdcb6e7ce8b7417db8fba48fbc097eb431866044ae90d2` |
| Guide run service | `backend/app/services/guide_run_service.py` | `db281d7198f7f99cdd2e411ed1ef8444012560987bc0f405374cdceabd6ec571` |
| BGE source | `backend/app/knowledge/bge.py` | `08dbcbd1206f600fcda8674807381203caaab74f19e329e110dbc989232b3e16` |
| Hybrid index implementation | `backend/app/knowledge/hybrid.py` | `2fcf437313526cb564939adca2c6198edbdcb073293ec1079797b64467a6d8ca` |
| Graph manifest validator | `backend/app/knowledge/graph_manifest.py` | `9791a2ae45817928b5d531149e8e2ab8c342179898234619f5e2498f7084b740` |

The tracked `backend/`, `frontend/`, `runtime/`, and fixture paths have no staged or unstaged changes at this B0 pin. Hybrid and Graph artifact hashes above were checked without altering them. No private batch/raw data or original configuration was read.
