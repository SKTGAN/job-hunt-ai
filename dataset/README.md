# 中文岗位 JD 数据采集操作手册

这个目录用于采集、保存和清洗中文岗位 JD 数据。当前阶段已经放弃 Boss/猎聘等强反爬招聘平台，改用更稳定的企业官网公开招聘接口。

## 1. 当前数据源

第一版稳定数据源：

| 数据源 | 类型 | 说明 |
| --- | --- | --- |
| 腾讯招聘公开接口 | 企业官网招聘 | 可直接返回 JSON，包含岗位名称、城市、职责、更新时间、岗位链接等字段 |

后续可以继续增加：

- 科大讯飞招聘官网
- 华为招聘官网
- 阿里/百度/京东/美团等企业招聘官网
- 政府公开职业标准与新职业数据

## 2. 安装依赖

当前脚本只使用 Node.js 内置 `fetch`，没有额外运行依赖。为了同步 `package-lock.json`，仍建议执行：

```powershell
cd C:\Users\A\Desktop\揭榜挂帅\job-hunt-AI\dataset
npm install
```

## 3. 目录结构

```text
dataset/
  config/seed_queries.json          # 第一批岗位关键词和城市
  scripts/collect_public_jobs.mjs   # 企业官网公开接口采集脚本
  scripts/normalize_jobs.mjs        # 清洗 raw JSON，导出 JSONL 和 CSV
  raw/chinese_jobs/                 # 原始采集结果
  cleaned/                          # 清洗结果
```

## 4. 采集岗位 JD

运行：

```powershell
npm run collect
```

等价于：

```powershell
npm run collect:tencent
```

采集结果会保存到：

```text
dataset/raw/chinese_jobs/*_tencent_public_jobs.json
```

## 5. 清洗并导出 JSONL 和 CSV

采集后运行：

```powershell
npm run normalize
```

默认读取最新 raw JSON，输出：

```text
dataset/cleaned/chinese_jobs_normalized.jsonl
dataset/cleaned/chinese_jobs_normalized.csv
```

如果要指定 raw 文件：

```powershell
node scripts/normalize_jobs.mjs --input raw/chinese_jobs/某个文件.json
```

CSV 带 UTF-8 BOM，方便 Excel/WPS 打开。数组字段如 `tags` 会用 `;` 拼接，长文本会做 CSV 转义。

## 6. 当前第一批采集范围

配置文件：

```text
dataset/config/seed_queries.json
```

首批关键词：

- `AI Agent 工程师`：北京、上海
- `大模型应用开发`：北京、上海
- `Java 开发工程师`：合肥、上海

默认每个关键词/城市采集第 1 页，每页 10 条。

注意：腾讯招聘接口不一定每个城市都有结果。合肥可能返回空，但这不是脚本错误。

## 7. 数据字段

清洗后的每条记录包含：

```text
source
keyword
city
crawl_time
job_title
company_name
salary_text
location
tags
job_description
source_url
raw
```

其中：

- `job_description` 来自企业官网岗位职责字段。
- `source_url` 是岗位详情页链接。
- `raw` 保留原始企业接口字段，便于后续追溯证据。

## 8. 为什么删除 Boss/猎聘/MCP 方案

已验证的问题：

- `mcp-jobs@1.4.0` NPM 包没有正确暴露 `bin`。
- Boss 直聘触发安全验证或空白页。
- 猎聘公开页没有稳定返回岗位卡片。
- 登录态采集仍会被平台自动化检测影响。

比赛当前阶段更需要稳定、可复现、可追溯的数据闭环，所以优先使用企业官网公开数据。

## 9. 下一步

1. 执行 `npm run collect`。
2. 执行 `npm run normalize`。
3. 检查 CSV 是否有真实岗位。
4. 从 CSV 中挑选 100 条 JD 做人工标注。
5. 后续再把 JSONL/CSV 写入 Elasticsearch 和 Neo4j。

