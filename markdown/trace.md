# 修改记录 Trace

## 2026-06-11 16:35 - 创建中文岗位 JD 采集底座

- 步骤：
  - 新建 `dataset` 目录结构。
  - 新增 `package.json`、首批采集配置 `config/seed_queries.json`。
  - 新增 `scripts/collect_mcp_jobs.mjs`，用于通过 `mcp-jobs` MCP 工具采集岗位列表和详情。
  - 新增 `scripts/normalize_jobs.mjs`，用于把原始 JSON 标准化为 JSONL 和 CSV。
  - 新增 `dataset/README.md`，说明采集、清洗、输出文件。
- 目的：
  - 先完成“中文岗位 JD 扒取 + 原始数据落盘 + JSONL/CSV 导出”的最小闭环。
  - 暂时不改动现有 FastAPI 后端、React 前端、Elasticsearch 或 Neo4j。
- 效果/当前成果：
  - 已形成可执行的数据采集与清洗脚本。
  - 首批关键词固定为 `AI Agent 工程师`、`大模型应用开发`、`Java 开发工程师`，城市为北京、上海、合肥。
- 下一步建议：
  - 运行 `npm install` 安装采集脚本依赖。
  - 运行 `npm run collect` 采集小样本。
  - 运行 `npm run normalize` 生成 JSONL 和 CSV。

## 2026-06-11 16:32 - 修复 mcp-jobs 启动方式

- 步骤：
  - 运行 `npm run collect` 发现 `npx -y mcp-jobs` 报错：`could not determine executable to run`。
  - 检查 NPM 包信息，确认当前 `mcp-jobs@1.4.0` 发布包包含 `dist/mcp.js`，但没有暴露 `bin` 字段。
  - 将 `mcp-jobs` 加入 `dataset/package.json` 依赖。
  - 修改采集脚本默认用本地 `node_modules/mcp-jobs/dist/mcp.js` 启动 MCP 服务。
- 目的：
  - 避免依赖 `npx` 自动推断可执行入口，让 MCP 服务启动方式更稳定。
- 效果/当前成果：
  - 首次失败 raw 文件已保存到 `dataset/raw/chinese_jobs/20260611_163031_mcp_jobs.json`，里面记录了配置和空查询结果。
  - 采集脚本已支持本地依赖启动，也保留了自定义 `--server-command`/`--server-arg` 参数。
- 下一步建议：
  - 重新运行 `npm install` 安装新增的 `mcp-jobs` 依赖。
  - 再次运行 `npm run collect` 验证 MCP 工具列表和采集结果。

## 2026-06-11 16:44 - 修正空搜索结果清洗逻辑

- 步骤：
  - 第二次运行 `npm run collect` 成功启动 MCP 服务并生成 `dataset/raw/chinese_jobs/20260611_163831_mcp_jobs.json`。
  - 运行 `npm run normalize` 成功生成 JSONL 和 CSV。
  - 抽查发现 `mcp-jobs` 返回 `{"jobs":[],"metadata":...}`，但通用对象提取逻辑把 `metadata.searchParams` 误识别成岗位，导致 CSV 里出现 6 条空岗位。
  - 修改 `collectObjects`：优先读取顶层 `jobs` 数组，并跳过 `searchParams`。
- 目的：
  - 保证没有真实岗位时输出 0 条记录，不为了凑数量生成假数据。
- 效果/当前成果：
  - 采集链路已能启动并落盘。
  - 当前 `mcp-jobs` 对首批关键词返回空岗位列表。
  - 终端显示拉勾、智联、51job 缺少匹配配置，当前实际可依赖的主要是 Boss 移动站和猎聘规则。
- 下一步建议：
  - 用更泛化关键词，例如 `Java`、`前端`、`算法工程师`，测试 `mcp-jobs` 是否能在当前网络环境下抓到岗位。
  - 如果仍为空，改用企业官网/公开招聘页或直接实现 Python/Playwright 中文采集器作为替代方案。

## 2026-06-11 16:47 - 为清洗脚本增加空岗位过滤

- 步骤：
  - 重新运行 `npm run normalize`，发现旧 raw 文件中已经保存的误识别空对象仍会进入清洗结果。
  - 在 `normalize_jobs.mjs` 增加 `hasUsableJobContent`，只有存在岗位标题、公司、薪资、链接、描述或标签时才输出。
- 目的：
  - 让历史 raw 文件也能被安全清洗，避免 CSV/JSONL 出现空岗位行。
- 效果/当前成果：
  - 清洗脚本现在会过滤掉没有实际岗位内容的记录。
- 下一步建议：
  - 再次运行 `npm run normalize`，确认当前输出为 0 条真实岗位。
  - 继续用更宽泛关键词验证 MCP 抓取源是否能返回数据。

## 2026-06-11 16:50 - 验证首批采集结果与站点限制

- 步骤：
  - 重新运行 `npm run normalize`，当前 raw 文件清洗后输出 `Records: 0`。
  - 用 Playwright 直接测试猎聘公开搜索页，页面未返回岗位卡片，只返回导航、热门词等内容。
  - 用 Playwright 直接测试 Boss 移动站，页面跳转到安全验证页。
- 目的：
  - 判断当前拿不到真实岗位 JD 是脚本问题、MCP 包问题，还是招聘站点访问限制。
- 效果/当前成果：
  - 已确认脚本链路可以启动 MCP、保存 raw JSON、导出 JSONL 和 CSV。
  - 当前环境下 `mcp-jobs` 对首批查询返回空 `jobs`。
  - Boss 公开移动站触发安全验证，猎聘公开搜索页没有返回岗位卡片。
  - 当前生成的 `dataset/cleaned/chinese_jobs_normalized.jsonl` 为 0 条记录，`dataset/cleaned/chinese_jobs_normalized.csv` 保留标准表头。
- 下一步建议：
  - 优先换用企业官网招聘页、政府公开职业标准、或可公开访问的招聘 API/页面作为第一批稳定数据源。
  - 如果继续使用 Boss/猎聘，需要人工登录态、验证码处理或合规授权，不建议在当前竞赛原型阶段硬绕。
  - 保留 `mcp-jobs` 接入作为后续可选采集器，但不要把它作为唯一数据源。

## 2026-06-11 17:05 - 增加本地手动登录态采集流程

- 步骤：
  - 新增 `scripts/save_browser_state.mjs`：打开可见浏览器，让用户自己登录 Boss/猎聘，登录完成后保存本地 storage state。
  - 新增 `scripts/collect_with_browser_state.mjs`：读取 `dataset/auth/*_state.json`，复用登录态采集岗位列表和详情。
  - 在 `package.json` 增加脚本：
    - `npm run login:zhipin`
    - `npm run login:liepin`
    - `npm run collect:auth:zhipin`
    - `npm run collect:auth:liepin`
  - 在 `.gitignore` 增加 `dataset/auth/`，避免登录态文件被提交。
  - 重写 `dataset/README.md`，补充完整操作步骤和登录态安全提醒。
- 目的：
  - 不让用户提供账号密码，通过本地手动登录解决招聘网站登录/验证码/安全验证问题。
  - 保持采集流程可控，仍然输出 raw JSON，再由清洗脚本导出 JSONL 和 CSV。
- 效果/当前成果：
  - 已具备保存 Boss/猎聘本地登录态的脚本。
  - 已具备复用登录态采集首批关键词岗位的脚本。
  - 登录态文件被明确标记为本地敏感文件，不进入 Git。
- 下一步建议：
  - 运行 `npm install` 更新 Playwright 依赖。
  - 运行 `npm run login:zhipin`，在弹出的浏览器中手动登录 Boss。
  - 登录成功后运行 `npm run collect:auth:zhipin` 采集岗位。
  - 再运行 `npm run normalize` 导出 JSONL 和 CSV。

## 2026-06-11 17:15 - 修改登录脚本为默认保持浏览器打开

- 步骤：
  - 修改 `scripts/save_browser_state.mjs`，将登录脚本默认行为改为保存登录态后继续保持浏览器打开。
  - 增加 `--close-after-save` 参数，用于需要保存后自动关闭浏览器的场景。
  - 增加浏览器关闭等待逻辑：手动关闭浏览器或终端按 `Ctrl+C` 后脚本才结束。
  - 更新 `dataset/README.md`，说明保存后浏览器会保持打开以及如何结束。
- 目的：
  - 解决登录窗口保存后立刻退出、用户无法继续停留确认登录状态的问题。
- 效果/当前成果：
  - 执行 `npm run login:zhipin` 或 `npm run login:liepin` 时，浏览器会默认保持打开。
  - 登录完成按 Enter 保存登录态后，窗口不会自动关闭。
- 下一步建议：
  - 重新运行 `npm run login:zhipin`，完成登录后按 Enter 保存，并确认浏览器窗口保持。
  - 确认登录态可用后，再运行 `npm run collect:auth:zhipin`。

## 2026-06-11 17:25 - 修复登录窗口停在 about:blank 的体验

- 步骤：
  - 根据登录时浏览器停在 `about:blank` 的现象，调整 `save_browser_state.mjs`。
  - 在自动跳转前先渲染一个本地登录说明页，页面里包含目标登录地址和可点击链接。
  - 将自动跳转改为短超时 `commit` 等待；如果跳转失败或超时，回退到本地说明页。
  - 更新 `dataset/README.md`，说明空白页时可手动输入地址或点击说明页链接。
- 目的：
  - 避免目标网站加载卡住时用户只能看到空白页，不知道下一步怎么做。
- 效果/当前成果：
  - 执行登录脚本后会先看到可操作的说明页。
  - 自动跳转失败时也能继续手动打开登录页，不影响后续保存登录态。
- 下一步建议：
  - 重新运行 `npm run login:zhipin`。
  - 如果仍停在空白页，直接在地址栏输入 `https://www.zhipin.com/`，登录完成后回终端按 Enter。

## 2026-06-11 17:40 - 换用公开企业招聘数据源并删除无效采集代码

- 步骤：
  - 根据 Boss/猎聘持续空白页、防爬和安全验证问题，停止继续维护招聘平台登录态采集方案。
  - 删除 `dataset` 中不再使用的脚本：
    - `scripts/collect_mcp_jobs.mjs`
    - `scripts/save_browser_state.mjs`
    - `scripts/collect_with_browser_state.mjs`
  - 删除本地登录态文件 `dataset/auth/zhipin_state.json` 和失败 raw 文件：
    - `20260611_163031_mcp_jobs.json`
    - `20260611_163831_mcp_jobs.json`
    - `20260611_171445_zhipin_browser_state_jobs.json`
    - `20260611_171715_zhipin_browser_state_jobs.json`
    - `20260611_173241_zhipin_browser_state_jobs.json`
  - 新增 `scripts/collect_public_jobs.mjs`，优先采集腾讯招聘公开 JSON 接口。
  - 修改 `package.json`，移除 MCP/登录态采集命令，新增 `collect:tencent`。
  - 重写 `dataset/README.md`，改为公开企业招聘数据源操作手册。
- 目的：
  - 放弃不可稳定复现的强反爬平台路径，优先完成比赛需要的“可采集、可追溯、可清洗”的中文 JD 数据集。
  - 清理 `dataset` 内部没用的代码和失败数据，避免后续混淆。
- 效果/当前成果：
  - `dataset` 采集主线已切换为企业官网公开接口。
  - 当前第一版数据源为腾讯招聘公开接口，能返回岗位列表 JSON。
  - 后续仍输出 raw JSON、JSONL 和 CSV。
- 运行问题记录：
  - Boss/猎聘不是简单脚本问题，而是平台风控导致 Playwright 页面空白、安全验证或无岗位卡片。
  - `mcp-jobs` 包也存在发布包入口和抓取规则不完整问题，因此不再作为主路径。
- 下一步建议：
  - 运行 `npm install` 更新 lockfile，移除不再需要的包。
  - 运行 `npm run collect` 获取腾讯招聘 JD。
  - 运行 `npm run normalize` 导出 JSONL 和 CSV。
  - 如果腾讯数据量不足，再继续加科大讯飞、华为等企业官网公开数据源。

## 2026-06-11 17:43 - 修复清洗脚本仍查找旧 MCP 文件名的问题

- 步骤：
  - 运行 `npm install`，已移除 MCP/Playwright 相关依赖。
  - 运行 `npm run collect`，成功生成 `dataset/raw/chinese_jobs/20260611_174055_tencent_public_jobs.json`。
  - 运行 `npm run normalize` 失败，错误为：`No raw MCP JSON files found`。
  - 修改 `normalize_jobs.mjs`，从只查找 `*_mcp_jobs.json` 改为查找最新的任意 `.json` raw 文件。
- 目的：
  - 适配新的公开企业招聘数据源文件命名。
- 效果/当前成果：
  - 清洗脚本不再绑定 MCP 文件名，后续腾讯、科大讯飞、华为等 raw JSON 都可复用同一清洗入口。
- 下一步建议：
  - 重新运行 `npm run normalize`。
  - 抽查 JSONL/CSV 是否有真实岗位标题、职责和岗位链接。

## 2026-06-11 17:46 - 修复 tags 清洗只保留第一个标签的问题

- 步骤：
  - 运行 `npm run normalize` 成功从腾讯 raw 文件导出 43 条记录。
  - 抽查发现 `raw.list_item.tags` 中包含 BG、产品线、技术类别、经验要求等多个标签，但清洗结果只保留第一个标签。
  - 修改 `normalizeTags`，优先直接读取数组字段，不再通过 `getFirst` 把数组压成第一个元素。
- 目的：
  - 保留岗位的产品线、类别、经验要求等标签，为后续技能图谱和岗位筛选提供更多上下文。
- 效果/当前成果：
  - 标签清洗逻辑已修复。
- 下一步建议：
  - 重新运行 `npm run normalize`，确认 CSV 中 `tags` 字段使用 `;` 保留多个标签。

## 2026-06-11 17:48 - 腾讯公开数据源采集成功

- 步骤：
  - 重新运行 `npm run normalize`。
  - 抽查 `dataset/cleaned/chinese_jobs_normalized.jsonl` 和 `dataset/cleaned/chinese_jobs_normalized.csv`。
- 目的：
  - 验证换数据源后是否真正产生可用中文 JD 数据集。
- 效果/当前成果：
  - 成功生成 43 条真实中文岗位 JD。
  - raw 文件：`dataset/raw/chinese_jobs/20260611_174055_tencent_public_jobs.json`。
  - JSONL 文件：`dataset/cleaned/chinese_jobs_normalized.jsonl`。
  - CSV 文件：`dataset/cleaned/chinese_jobs_normalized.csv`。
  - 样例岗位包括：
    - `腾讯云-AI Agent测试工程师`
    - `AI量化投研工程师-Agent方向`
    - `AI应用开发工程师-Agent方向`
  - 标签字段已保留多个标签，例如 `CSIG;腾讯云;技术;五年以上工作经验`。
- 运行问题记录：
  - 腾讯招聘接口按关键词返回结果，但城市筛选不一定严格。例如查询北京时，岗位实际地点可能是深圳；后续需要区分“查询城市”和“岗位实际地点”。
  - 合肥在腾讯招聘接口里可能没有稳定 cityId，目前配置为空时相当于更宽泛查询。
- 下一步建议：
  - 增加更多企业官网公开接口，优先科大讯飞、华为、百度、阿里。
  - 将字段拆得更细：`query_city`、`actual_location`、`publish_time`、`experience_required`。
  - 从当前 43 条中先抽 20 条做 JD 技能标注样例。
