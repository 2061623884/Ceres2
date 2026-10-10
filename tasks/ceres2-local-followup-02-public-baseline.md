# 02 公共 HTTP/SSE 评测执行

- 状态：待验收；原runner七条/真实FastAPI-Pi受控smoke、本次真实100采集与缺plan诊断第八条runner验证完成，cbca最终两轴完成；等待用户审阅，完整driver仍开放。
- 负责人：followup_experience；Tester 独占运行验证。
- 所属：[总 TASK](ceres2-local-followup.md)；[规格](../docs/plans/ceres2-local-followup-spec.md)。
- 前置：01 的 batch/capture 合同已释放；完整场景与评分依赖 01。

## 范围与文件

`backend/app/evaluation/run_baseline.py` 与 `backend/tests/test_local_followup_baseline.py`。
只调用选定评测 API 的公共 bootstrap/navigation/run/SSE/receipt/messages/业务接口。
每次执行独立合成 owner 与 canonical Guide session；不启服务、不读旧状态，不添加测试专用产品接口。
后续回复/角色选择/业务确认必须在场景动作中预先授权。角色等待保留 capture=null；一题故障继续其他题。

## 验收与证据

- [ ] 公共 CLI 逐题隔离身份、采集实际运行，保留不可取得字段为 null；首轮 [RED](../work/local-followup/02/baseline-red.md)。
- [ ] 角色等待/准备失败/脚本失败单列，保留计划分母并继续后续题。
- [ ] 必要多轮任务及重复执行沿同一任务会话，授权与状态可观察。
- [ ] 实际 SSE 到达计时、固定输入/source/index/model 及重复 trial 有来源；不混同缓冲 TestClient。

原工具阶段证据：[runner全7项](../work/local-followup/02/baseline-runner-file-final.md)、[真实API受控smoke](../work/local-followup/01/app-controlled-http-smoke.md)、[最终补修后共同29项](../work/local-followup/01/tool-combined-final-delta.md)，对应`739f13ead0c53ce9d82519efc30f51263e29ab45`。原[26项](../work/local-followup/01/tool-combined-final.md)保留e855候选版本。采集包含逐题/每步状态、client SSE计时、全run capture按request消息隔离、confirm/replay、小型多轮与resume；unsupported在HTTP前明确记录。完整订单/售后/Memory setup未实现。

后续真实DeepSeek100已采集，实际结果见[正式报告](../work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)。公开dev-01 trial3缺plan导致旧确认组装TypeError，原失败轨迹保留。现在driver给明确ValueError且保留capture/状态；新增第八条runner测试并纳入4008阶段[35项受控组合](../work/local-followup/01/tool-combined-after-real-harness-casefold-fix.md)，最终cbca只清理harness两处签名，没有重跑原模型批次。

下一步：用户审阅；完整driver和后续业务修复按[04](ceres2-local-followup-04-real-evaluation-feedback.md)处理，不复用原owner或覆盖失败。
