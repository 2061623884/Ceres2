# Ceres2

保留现有 React 页面，Python 作为业务权威，售前采用实际 Node/Pi，售后采用 Python/LangGraph。01–15 受控技术范围已释放；16 同版受控集成已通过（294 场景两次、45 项匹配源码检查、两轴审查关闭）。真实模型、真实浏览器和用户本人验收仍分别待完成。禁止从相邻 reference/archive 运行时导入或借用依赖。

- [项目目标](PROJECT.md) · [产品定义](prd.md)
- [16 票与当前状态](tasks/ceres2-upgrade.md)
- [最终集成范围、未验证项与体验步骤](work/clean-rebuild/16/DELIVERY.md)
- [迁移来源、边界及新验收](work/clean-rebuild/README.md)
- [选择性迁移与静态数据来源](work/clean-rebuild/migration-ledger.md)

## 本地准备与启动

以下为新环境操作步骤；当前协作中安装、测试和构建命令只由专职 Tester 执行。不要复制归档 .env 或运行数据库。

1. 在工程根目录创建 Python 虚拟环境，安装固定依赖：
   `python -m venv .venv`，然后 `.venv/bin/python -m pip install -r backend/requirements.lock`。
2. 复制 `.env.example` 为根目录 `.env`，手动填写自己的 OpenAI-compatible endpoint、API key 和模型。空配置不能作为真实模型可用证明。
3. 在 `backend/` 运行 `../.venv/bin/python -m app.services.seed_service`。它建立全新业务 schema，并仅插入缺失的静态商品、门店和 Offer；重复执行不会重置现有价格／库存。静态来源共 65 SKU、65 模拟 Offer、33 个已校验原图，其他商品正常显示缺图。
4. 在 `runtime/pi/` 按 package-lock 安装依赖并运行 `npm run build`，生成真实 Pi worker。
5. 在 `backend/` 运行 `../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012`。
6. 在 `frontend/` 按 package-lock 安装依赖，运行 `npm run dev`。保留的 Vite 配置使用 8443 端口，将 `/api` 和 `/media` 代理到后端 8012。

`/health` 检查数据库连接；`/api/v1/bootstrap` 建立可信匿名用户 cookie，未导入门店时明确返回 503。导购与墨墨共用该用户身份。LangGraph checkpoint 文件单独保存流程状态，订单／case／责任仍在同一业务数据库；不迁入旧订单或会话。

模拟价格、库存、配送和售后不能表述为真实交易或履约。自动技术证据、真实模型、真实页面与本人验收分别记录于各票；基础接口通过不代表完整购物生命周期已经可用。

## Controlled test configuration

`backend/tests/conftest.py` installs dummy loopback provider settings and disables root dotenv loading before pytest collection. Normal application settings are unchanged. This protects direct pytest and pytest launched through the capture wrapper; it does not authorize or isolate arbitrary live scripts. See [the isolation follow-up](work/live-validation/TEST-ISOLATION-REVIEW.md) for its independently verified scope.
