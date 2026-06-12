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

## 2026-06-12 10:28 - 扩大企业范围与赛题岗位采集范围
- 步骤：
  - 扩展 `dataset/config/seed_queries.json`，围绕赛题加入 AI、大模型、算法、数据、Java、Python、云计算、物联网、安全、软件、测试、产品、解决方案、运维、数据库、嵌入式等岗位群。
  - 重写 `dataset/scripts/collect_public_jobs.mjs`，从只支持腾讯招聘改为支持 `tencent`、`huawei`、`all` 三种采集模式。
  - 新增华为招聘公开接口采集逻辑：`https://career.huawei.com/reccampportal/services/portal/portalpub/getJob/newHr/page/{pageSize}/{pageIndex}`。
  - 给采集脚本增加 `--target` 参数，默认目标 3000 条，并在采集过程中按企业岗位 ID 去重。
  - 更新 `dataset/package.json`，默认 `npm run collect` 改为采集腾讯+华为，目标 3000 条，同时保留 `collect:tencent` 和新增 `collect:huawei`。
  - 更新 `dataset/scripts/normalize_jobs.mjs`，在 CSV/JSONL 中增加 `source_name` 和 `publish_time` 字段。
  - 重写 `dataset/README.md`，说明扩大后的企业数据源、3000 条采集命令、字段含义和后续使用建议。
- 目的：
  - 从单一企业小样本扩展到多企业、大范围岗位 JD，为比赛中的岗位能力图谱构建、技能抽取、岗位族分析和动态演化分析提供更充足的中文本地数据。
  - 避开 Boss/猎聘等强反爬平台，把第一阶段数据闭环建立在可复现的企业官网公开 JSON 接口上。
- 效果/当前成果：
  - 腾讯招聘接口当前可返回约 2521 条全量岗位。
  - 华为招聘接口已验证可返回约 3218 条社招岗位，并且列表字段中包含岗位职责 `mainBusiness` 和任职要求 `jobRequire`。
  - 代码已经具备采集 3000 条左右真实 JD 的能力，待运行采集和清洗验证最终落盘数量。
- 运行问题记录：
  - 科大讯飞招聘页初步访问出现超时，且页面疑似使用北森动态门户，暂未接入为稳定数据源。
  - 华为筛选条件接口 `services/rec/baseTalent/pub/callNewHr` 直接 POST 会返回 403，但岗位列表公开 GET 接口可用，因此本次只接入岗位列表接口。
  - Windows PowerShell 终端显示部分中文为乱码，但 Node 读取 UTF-8 配置和接口返回 JSON 不受影响；本次已重写核心配置、README 和采集脚本中的中文常量。
- 下一步建议：
  - 运行 `npm run collect` 和 `npm run normalize`，确认 raw、JSONL、CSV 都生成 3000 条左右真实岗位。
  - 抽查 CSV 中华为和腾讯各 10 条，确认 JD、公司、来源、发布时间字段正确。
  - 若后续需要行业覆盖更广，再继续接入百度、阿里、京东、美团、科大讯飞等企业官网公开源。

## 2026-06-12 10:34 - 增加国内岗位过滤
- 步骤：
  - 在 `dataset/config/seed_queries.json` 的 defaults 中增加 `domesticOnly: true`。
  - 在 `dataset/scripts/collect_public_jobs.mjs` 中增加腾讯和华为的国内岗位判断逻辑。
  - 腾讯岗位优先使用 `CountryName` 判断，若不是 `中国` 则跳过，并过滤东京、日本、新加坡、美国、欧洲等明显海外地点。
  - 华为岗位优先使用 `jobArea` 和 `jobAddress` 判断，保留 `中国/...` 或 `China\\...` 的岗位，并过滤明显海外地点。
  - 在每页 raw 记录中增加 `skipped_by_region`，记录因为地区不符合被跳过的数量。
  - 更新 `dataset/README.md`，说明默认开启国内岗位过滤。
- 目的：
  - 避免中国企业官网中的海外岗位混入本地中文 JD 数据集，让本阶段数据更贴合“本地化中文岗位数据源”的目标。
- 效果/当前成果：
  - 代码已支持默认过滤海外岗位，待重新运行采集验证最终 3000 条输出。
- 运行问题记录：
  - 首次 3000 条抽查发现腾讯结果中存在东京岗位，说明仅限制企业来源不等于岗位地点本地化，需要增加地区过滤。
- 下一步建议：
  - 重新运行 `npm run collect` 和 `npm run normalize`，再统计空 JD、来源分布和海外地点残留情况。

## 2026-06-12 10:39 - 3000 条岗位 JD 采集与清洗验证完成
- 步骤：
  - 运行 `node --check scripts/collect_public_jobs.mjs` 和 `node --check scripts/normalize_jobs.mjs`，确认脚本语法正常。
  - 运行 `npm install`，确认当前无额外依赖问题。
  - 运行 `npm run collect`，按腾讯+华为公开企业招聘接口采集岗位 JD。
  - 运行 `npm run normalize`，从最新 raw JSON 导出 JSONL 和 CSV。
  - 使用 Node 脚本抽查清洗结果的总量、来源分布、空标题、空 JD、海外地点残留和关键词分布。
- 目的：
  - 验证扩大企业范围和岗位范围后的代码是否真的能产出目标规模数据，而不是只完成脚本改造。
- 效果/当前成果：
  - 最新 raw 文件：`dataset/raw/chinese_jobs/20260612_103509_all_public_jobs.json`。
  - 最新 JSONL：`dataset/cleaned/chinese_jobs_normalized.jsonl`。
  - 最新 CSV：`dataset/cleaned/chinese_jobs_normalized.csv`。
  - 清洗后记录数：3000 条。
  - 来源分布：腾讯招聘 2219 条，华为招聘 781 条。
  - 采集阶段因地区过滤跳过：633 条。
  - 空标题：0 条。
  - 空 JD：0 条。
  - 按当前海外地点词表检查残留：0 条。
  - 覆盖岗位群数量：15 个，主要包括人工智能与大模型、数据工程与数据治理、算法与机器学习、大模型应用、软件工程、产品与业务分析等。
- 运行问题记录：
  - 首次未过滤地区时也能采满 3000 条，但抽查发现腾讯中存在东京等海外岗位；已通过 `domesticOnly` 过滤修正，并重新生成最终 3000 条数据。
  - 腾讯公开接口虽然传入 `area=cn`，仍可能返回海外岗位，因此后续不能只依赖接口参数，仍需要本地清洗规则兜底。
- 下一步建议：
  - 从 `dataset/cleaned/chinese_jobs_normalized.csv` 抽样 50-100 条做人工技能标注样本。
  - 下一步代码可以做 `skills_extract` 或 `graph_import`：从 JD 中抽取技能短语，再导入 Neo4j 构造岗位-技能-企业-地区图谱。

## 2026-06-12 10:41 - 删除未过滤地区的中间 raw 文件
- 步骤：
  - 删除 `dataset/raw/chinese_jobs/20260612_103136_all_public_jobs.json`。
- 目的：
  - 该文件是首次未开启国内岗位过滤时生成的 3000 条中间结果，抽查发现包含东京等海外岗位；保留它容易后续误用。
- 效果/当前成果：
  - 当前保留的最新可用 raw 文件为 `dataset/raw/chinese_jobs/20260612_103509_all_public_jobs.json`。
  - `dataset/cleaned/chinese_jobs_normalized.jsonl` 和 `dataset/cleaned/chinese_jobs_normalized.csv` 已由过滤后的 raw 文件生成。
- 运行问题记录：
  - 删除的是质量不达标的中间采集文件，不影响最终 3000 条清洗结果。
- 下一步建议：
  - 后续如果再次跑采集，优先检查最新 raw 文件名和清洗脚本输出的 `Input:` 路径，避免使用旧数据。

## 2026-06-12 11:20 - 增加政府/公务员职位表导入能力并继续探测更多大厂源
- 步骤：
  - 重写 `dataset/scripts/collect_public_jobs.mjs`，保留腾讯、华为在线采集逻辑，同时整理源配置、国内过滤、岗位标准化函数，方便后续继续加百度、阿里、美团等企业源。
  - 新增 `dataset/scripts/import_government_jobs.py`，支持把政府/公务员/事业单位官方 `.xlsx`、`.xls`、`.csv` 职位表导入为统一 raw JSON。
  - 新增 `dataset/raw/government_jobs/.gitkeep`，用于放置国家公务员、省考、事业单位等官方职位表。
  - 更新 `dataset/package.json`，增加 `import:government` 命令入口。
  - 更新 `dataset/README.md`，补充政府职位表导入流程、支持字段和后续建议。
  - 探测百度、阿里、美团、京东等大厂招聘站点的公开接口可用性。
- 目的：
  - 继续扩大数据来源类型：一类是互联网/ICT 大厂岗位，另一类是政府、公务员、事业单位公共部门岗位。
  - 政府职位表通常以官方 Excel 附件发布，导入官方表格比爬网页更稳定，也更适合保留专业、学历、招考人数等结构化字段。
- 效果/当前成果：
  - 当前在线稳定企业源仍为腾讯招聘和华为招聘，已能产出 3000 条本地岗位 JD。
  - 新增政府职位表导入脚本，字段会统一为 `source`、`source_name`、`keyword`、`job_title`、`company_name`、`location`、`tags`、`job_description` 等现有清洗格式。
  - 导入器可识别常见列名：`部门名称`、`招录机关`、`职位名称`、`职位代码`、`工作地点`、`学历`、`学位`、`专业`、`基层工作最低年限`、`招考人数`、`职位简介`、`备注`。
  - 验证通过：`node --check scripts/collect_public_jobs.mjs`、`node --check scripts/normalize_jobs.mjs`、`python -m py_compile scripts/import_government_jobs.py`、`python scripts/import_government_jobs.py --help`。
- 运行问题记录：
  - 国家公务员局相关网页在当前网络下直连出现 TLS/连接失败，因此本轮先实现“下载官方职位表后本地导入”的稳妥路径。
  - 百度招聘前端使用懒加载 chunk，已定位到 `list-fetch`/`detail-fetch`，但接口函数仍需继续拆公共模块后再接入。
  - 阿里招聘前端存在岗位相关接口和 `/social/position/*` 路径，但岗位列表接口未稳定复现，暂不写入正式采集器。
  - 美团招聘页面为单页应用，入口 HTML 未直接包含 JD 数据，需要继续拆静态资源接口。
  - 京东招聘页面明显包含登录/验证码相关脚本，短期不适合作为无登录稳定数据源。
- 下一步建议：
  - 先从国家公务员局、各省人事考试网、事业单位招聘网下载官方职位表，放到 `dataset/raw/government_jobs/`，再运行 `python scripts/import_government_jobs.py --input ...`。
  - 企业侧继续优先拆百度、美团、阿里、小米、科大讯飞这类官网公开接口；只有能稳定拿到 JD/职位职责的源再接入正式 CSV。

## 2026-06-12 11:23 - 删除 Python 编译缓存
- 步骤：
  - 删除 `dataset/scripts/__pycache__/`。
- 目的：
  - 该目录是运行 `python -m py_compile` 后生成的本地缓存，不属于项目代码或数据集。
- 效果/当前成果：
  - 工作区不再包含 Python 缓存目录。
- 下一步建议：
  - 后续如再次运行 Python 编译或脚本生成缓存，继续忽略或删除 `__pycache__`。

## 2026-06-12 11:25 - 在线企业采集器小样本验证
- 步骤：
  - 运行 `node scripts/collect_public_jobs.mjs --source tencent --target 3 --output $env:TEMP\\jobhunt_tencent_smoke.json`。
  - 运行 `node scripts/collect_public_jobs.mjs --source huawei --target 3 --output $env:TEMP\\jobhunt_huawei_smoke.json`。
- 目的：
  - 验证重写后的在线采集器仍能真实访问腾讯和华为公开招聘接口。
- 效果/当前成果：
  - 腾讯小样本采集成功，返回 3 条岗位。
  - 华为小样本采集成功，返回 3 条岗位。
  - 输出写入系统临时目录，没有新增项目 raw 数据文件。
- 下一步建议：
  - 继续拆百度、美团、阿里等企业源时，也先用临时输出做 smoke test，确认有 JD 后再写入正式数据集。

## 2026-06-12 11:40 - 删除早期腾讯小样本 raw
- 步骤：
  - 删除 `dataset/raw/chinese_jobs/20260611_174055_tencent_public_jobs.json`。
  - 运行 `python -m py_compile dataset/scripts/import_government_jobs.py`，确认政府职位表导入脚本语法正常。
- 目的：
  - 该文件是早期只含 43 条腾讯岗位的小样本，已经被正式的 3000 条腾讯+华为数据替代，继续保留容易误用。
  - 在抓取/导入公务员职位表前，确认导入脚本可执行。
- 效果/当前成果：
  - `dataset/raw/chinese_jobs/` 中只保留当前正式 raw：`20260612_103509_all_public_jobs.json`。
  - 政府职位表导入脚本语法检查通过。
- 下一步建议：
  - 继续抓取国家公务员或地方公务员官方职位表，导入为 `*_government_jobs.json` 后再统一 normalize。

## 2026-06-12 11:58 - 抓取并导入 2026 国家公务员职位表
- 步骤：
  - 通过 `http://bm.scs.gov.cn/kl2026` 进入中央机关及其直属机构 2026 年度考试录用公务员专题。
  - 读取下载页 `http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/download/gkdownloads.html`。
  - 分析 `gkdownloads.js`，定位附件列表接口：`http://dl.scs.gov.cn/api/res/8a81f6d9980207bb0198ab5683670008/1110`。
  - 从附件列表中定位“中央机关及其直属机构2026年度考试录用公务员招考简章.zip”，资源 ID 为 `8a81f6d19780e4080199e13f881f0153`。
  - 下载到 `dataset/raw/government_jobs/2026_guokao_zhaokaojianzhang.zip`。
  - 解压得到 `dataset/raw/government_jobs/2026_guokao_zhaokaojianzhang/中央机关及其直属机构2026年度考试录用公务员招考简章.xls`。
  - 首次导入只得到 125 条，检查发现 Excel 有 4 个 sheet 且第 1 行是说明、第 2 行才是真表头。
  - 修改 `dataset/scripts/import_government_jobs.py`，增加自动识别表头行和默认导入所有 sheet 的逻辑。
  - 新增 `dataset/requirements.txt`，记录 Python 依赖：`pandas`、`openpyxl`、`xlrd>=2.0.1`。
  - 运行 `python -m pip install -r dataset/requirements.txt` 安装 `xlrd`，用于读取官方 `.xls` 文件。
  - 重新导入，生成 `dataset/raw/chinese_jobs/20260612_115252_government_jobs.json`。
  - 删除半成品 `dataset/raw/chinese_jobs/20260612_115134_government_jobs.json`。
  - 导出公务员专名清洗文件：
    - `dataset/cleaned/government_jobs_2026_normalized.jsonl`
    - `dataset/cleaned/government_jobs_2026_normalized.csv`
  - 重新导出企业专名清洗文件：
    - `dataset/cleaned/enterprise_jobs_3000_normalized.jsonl`
    - `dataset/cleaned/enterprise_jobs_3000_normalized.csv`
  - 删除 Python 编译缓存 `dataset/scripts/__pycache__/`。
- 目的：
  - 把公务员官方职位表纳入本地中文岗位数据源，形成“企业岗位 + 公共部门岗位”两类数据，对应赛题中多源异构岗位和能力图谱的建设目标。
  - 清理早期半成品和缓存文件，避免后续误用。
- 效果/当前成果：
  - 成功导入 2026 国家公务员职位 20714 条。
  - 公务员清洗结果空标题：0 条。
  - 公务员清洗结果空描述：0 条。
  - 样例字段已经包含职位名称、招录机关、工作地点、学历、学位、专业、政治面貌、基层工作年限、考试类别等。
  - 当前企业岗位和公务员岗位均已有专名 JSONL/CSV 文件，后续不会只依赖通用的 `chinese_jobs_normalized.*`。
- 运行问题记录：
  - `https://bm.scs.gov.cn` 在当前网络环境下 443 连接失败，但 `http://bm.scs.gov.cn` 和 `http://dl.scs.gov.cn` 可用。
  - 官方文件是 `.xls` 老格式，pandas 读取需要 `xlrd`；首次运行缺少 `xlrd`，已通过 `dataset/requirements.txt` 补充并安装。
  - 首次导入 125 条是因为只读第一个 sheet 且没有识别第二行表头；已修复为自动识别表头和默认导入所有 sheet。
  - 清洗时曾在 `dataset/` 目录下误传 `dataset\\raw\\...`，导致路径变成 `dataset\\dataset\\raw\\...`；已改用 `raw\\chinese_jobs\\...` 成功运行。
- 下一步建议：
  - 公务员数据可直接用于公共部门岗位能力图谱分析，尤其适合抽取专业要求、学历要求、政治面貌、基层经验、工作地点等结构化能力条件。
  - 后续继续抓省考、事业单位、国企招聘职位表，放入 `dataset/raw/government_jobs/` 后用同一导入器处理。

## 2026-06-12 12:05 - 更新下一阶段 target 目标
- 步骤：
  - 在 `markdown/target.md` 末尾追加“下一阶段目标：从数据拿到进入图谱与分析原型”。
  - 基于当前已有数据重新规划下一阶段：企业岗位 3000 条、国家公务员岗位 20714 条。
  - 明确下一阶段 6 个目标：中文技能与能力词表、岗位能力抽取脚本、Neo4j 本地岗位能力图谱、企业岗位与公务员岗位对比分析、人工标注与评测样本、人岗匹配雏形。
  - 列出最近 7 个优先任务和“可演示原型”的完成标志。
- 目的：
  - 将项目重点从继续采集数据转向能力抽取、图谱构建、差异分析和比赛可演示闭环。
- 效果/当前成果：
  - `markdown/target.md` 已新增第 13 节，作为当前最新阶段目标。
  - 下一步开发可直接围绕 `dataset/taxonomy/`、`dataset/processed/`、Neo4j 导入、企业/公务员对比报告展开。
- 运行问题记录：
  - PowerShell 终端仍会把部分中文显示成乱码，但 `target.md` 中新增章节已成功写入，`Select-String` 可定位到“下一阶段目标”等标题。
- 下一步建议：
  - 优先创建中文技能词表和公务员条件词表，然后实现第一版岗位能力抽取脚本。
## 2026-06-12 16:20 - 重写阶段目标并核查中文简历数据
- 步骤：
  - 检查 `dataset/resume/` 中 3 个 CSV、1 个 JSONL 和数据说明文件。
  - 统计数据规模、字段、缺失率、重复情况、岗位类别和筛选标签分布。
  - 对比 `Chinese_resume_data.csv` 与 `revise_Chinese_resume_data.csv` 的字段差异。
  - 重写 `markdown/target.md`，将主线调整为 BM25 + Transformer 混合检索、Top150 召回、最终推荐、Neo4j 图谱增强和能力差距分析。
- 目的：
  - 让阶段目标与当前已有数据和赛题技术路线一致，减少旧文档中过长、重复和已过时的采集目标。
  - 明确区分“存在筛选结果”和“具备可靠人岗匹配标注”，避免高估现有简历数据的可用程度。
- 效果/当前成果：
  - 企业岗位数据明确为腾讯、华为 3000 条，国家公务员岗位明确为 20714 条，现阶段暂不继续追求采集规模。
  - 中文简历共 5000 条、34 个字段、10 类技术岗位；具有通过/不通过粗粒度标签，但缺少简历-JD 相关性、技能实体和能力差距等细粒度人工标注，状态设为待定。
  - `master_resumes.jsonl` 共 4817 条，为英文真实/合成混合数据且无外部标注，仅保留为参考。
  - 新版目标文档已给出从岗位建索引、岗位向量化、简历向量化、Top150 混合召回到最终推荐的执行顺序。
- 运行问题记录：
  - PowerShell 默认显示编码会造成旧 Markdown 中文乱码，但文件本身可按 UTF-8 正常读取和重写。
  - 中文 CSV 含姓名、电话和邮箱，正式实验前必须脱敏；大量专项技能列缺失率较高，不能直接视为负样本。
- 下一步建议：
  - 先生成统一岗位主表和匿名化简历主表，再实现 BM25 基线，以 `Recall@150` 作为第一项可量化结果。
## 2026-06-12 16:45 - 补充 BM25、Embedding 与 Neo4j 完整推荐数据流
- 步骤：
  - 修改 `markdown/target.md` 的总体架构，将岗位离线处理和简历在线查询拆分为两条数据流。
  - 将候选岗位召回数量由 Top150 调整为 Top200。
  - 明确 BM25 负责快速候选召回，Transformer Embedding 负责 Top200 语义相似度计算与重排。
  - 增加中文 Embedding 模型路线，区分直接使用 `BAAI/bge-m3`、Qwen Embedding 与后续领域微调。
  - 补充 Neo4j 在推荐解释、知识扩展、能力差距分析、岗位动态更新和新岗位发现中的作用。
- 目的：
  - 形成可实现、可解释且适合答辩展示的人岗推荐技术链路。
  - 使用 BM25 缩小候选范围，降低全量向量计算成本，同时利用图谱弥补关键词检索和黑盒语义模型的局限。
- 效果/当前成果：
  - 岗位侧流程明确为：清洗 JD、建立 BM25 索引、生成岗位向量、抽取岗位技能关系并写入 Neo4j。
  - 查询侧流程明确为：解析简历、BM25 召回 Top200、计算候选向量相似度、图谱扩展与规则重排、输出最终 TopN。
  - Transformer 训练策略改为先建立现有中文模型基线，在获得简历-岗位正负样本和相关性标注后再进行领域微调。
  - 评测主指标同步调整为 `Recall@200`、`HitRate@K` 和 `NDCG@K`。
- 运行问题记录：
  - 当前仍缺少可靠的简历-岗位相关性标注，因此暂时不能直接开展有监督微调，也不能仅凭“通过/不通过”标签判断检索排序质量。
  - 图谱邻居扩展可能引入无关岗位，扩展结果必须再次经过技能、语义和岗位条件过滤。
- 下一步建议：
  - 先完成统一岗位主表和 Elasticsearch BM25 索引，验证每份简历能稳定召回 Top200，再接入 `bge-m3` 生成向量重排基线。
## 2026-06-12 19:45 - 合并岗位主表并制定中文简历标注基准
- 步骤：
  - 阅读论文 `2603.14558v2.pdf` 中混合检索、知识图谱、白盒重排、JobSearch-XS 标注和评测部分。
  - 新增 `dataset/scripts/merge_job_datasets.py`，合并企业岗位和国家公务员岗位 JSONL。
  - 在 `dataset/package.json` 中增加 `npm run merge:jobs`。
  - 更新 `dataset/README.md`，说明合并命令、输入输出和重复标记字段。
  - 生成统一岗位数据 `all_jobs_23714_normalized.jsonl` 和 `all_jobs_23714_normalized.csv`。
  - 新增 `markdown/resume_fix.md`，给出中文简历脱敏、结构化、银标、金标、数据划分、评测和消融实验方案。
- 目的：
  - 为 BM25 建索引、岗位向量化和 Neo4j 图谱构建准备统一岗位入口。
  - 将现有中文简历从“有筛选标签的数据”改造成能够独立评测召回、排序、图谱扩展和解释质量的基准数据。
- 效果/当前成果：
  - 统一岗位主表共 23714 条，其中企业岗位 3000 条、公务员岗位 20714 条。
  - JSONL 与 CSV 均为 23714 条、19 个字段，`job_id` 全部唯一，岗位标题和岗位描述均无空值。
  - 发现并标记 1628 条内容重复记录，但未直接删除，后续建索引时可按实验需要折叠。
  - 简历基准方案明确区分自动银标与独立人工金标，建议先试标 30 份简历约 600 对，再扩展到 100 份简历约 2000 对。
  - 正式指标包括 `Recall@200`、`NDCG@5/10`、`MRR`、延迟、图谱新增候选相关率和解释忠实度。
- 运行问题记录：
  - 公务员数据的 `source_url` 并非全局唯一，不能仅以 URL 去重；企业数据也存在不同职位 ID 共享相同文本的情况，因此合并阶段只标记内容重复。
  - 论文的银标来自技能图谱重合，论文也明确使用独立人工金标报告正式指标；本项目不能用图谱规则生成标签后再用同一标签证明图谱有效。
  - Python 编译检查产生的 `__pycache__` 和论文临时文本已在验证后删除，未作为项目文件保留。
- 下一步建议：
  - 新增简历处理脚本，输出脱敏且结构统一的 `resumes_anonymized.jsonl/csv`，随后选择 30 份简历生成第一批人工标注候选池。
## 2026-06-12 20:25 - 完成中文简历脱敏、标准化和基准准备
- 步骤：
  - 新增 `dataset/config/skill_aliases.json`，拆分并标准化常见组合技能。
  - 新增 `dataset/scripts/process_chinese_resumes.py`，同时读取原版和修订版 5000 条中文简历。
  - 删除姓名、性别、年龄、电话和邮箱等字段，生成稳定匿名 `resume_id`。
  - 将意向岗位、学历、专业、英语、技能、经验和项目组合为不含标签的 `profile_text`。
  - 保留原版筛选标签、修订版筛选标签和标签冲突标记，当前辅助标签使用修订版。
  - 按 `profile_hash` 分组划分 train/dev/test，避免重复简历跨集合泄漏。
  - 新增 `dataset/annotations/annotation_guideline.md` 和 `resume_job_gold_template.csv`。
  - 从 10 个岗位族各选 3 份不同简历，生成 `pilot_resumes_30.jsonl`。
  - 在 `dataset/package.json` 增加 `npm run process:resumes`，并更新 `dataset/README.md`。
  - 运行处理脚本和质量断言，生成 `markdown/report.md`。
- 目的：
  - 把原始中文简历转换为可以安全用于 BM25、中文 Embedding、Neo4j 和人工标注的标准输入。
  - 为后续 30 份简历、约 600 个简历-岗位对的试标建立数据和规范基础。
- 效果/当前成果：
  - 成功输出 5000 条脱敏简历，匿名 ID 全部唯一，PII 模式命中为 0。
  - 5000 条简历均有非空 `profile_text` 和技能列表，技能与熟练度没有数量错位。
  - 得到 4998 个唯一简历文本，发现 2 条重复内容；按文本哈希划分后跨集合泄漏为 0。
  - Train/Dev/Test 数量分别为 2951、995、1054。
  - 原版与修订版筛选标签有 2033 条冲突，占 40.66%，因此两版标签均保留审计，不能作为正式检索金标。
  - 生成 30 份试标简历，覆盖 10 个岗位族且无重复文本。
- 运行问题记录：
  - 首次隐私扫描在哈希 ID 中误识别出 3 个手机号样式数字；调整为只扫描用户内容字段后确认实际敏感信息命中为 0。
  - 改用 `profile_hash` 划分集合后，哈希字段又产生 2 个同类正则误报；已将技术标识字段排除在 PII 内容扫描之外。
  - 最初按 `resume_id` 划分可能让重复简历跨集合；已改为按 `profile_text` 哈希分组，最终泄漏检查为 0。
  - 一次临时验证断言对岗位族计数的写法不正确，但数据实际为 10 类各 3 份；修正验证逻辑后不影响生成文件。
- 下一步建议：
  - 建立统一岗位主表的 Elasticsearch BM25 索引，为 `pilot_resumes_30.jsonl` 中每份简历生成 Top200，再构造每份约 20 个岗位的人工标注池。
