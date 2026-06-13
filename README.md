# 中文岗位检索与人岗匹配实验系统

本项目基于开源 JobMatchAI 代码进行中文本地化改造，当前重点是完成比赛所需的中文岗位数据处理、简历预处理、Elasticsearch BM25 候选召回和 BGE-M3 语义重排实验。

> 当前是数据与检索算法原型，不是已经完成的产品。前端尚未适配中文岗位数据和新的预测接口，Neo4j 中文技能图谱、硬条件过滤、人工金标评测及完整线上推荐仍在后续阶段。

## 当前进度

### 已完成

- 采集并整理腾讯、华为公开招聘岗位。
- 导入中央机关及其直属机构 2026 年度公务员招考职位表。
- 合并形成统一岗位主表，共 23,714 条：
  - 企业岗位 3,000 条。
  - 国家公务员岗位 20,714 条。
- 同时输出 JSONL 和 CSV，标记内容重复岗位。
- 对 5,000 条中文简历完成脱敏、字段统一、技能标准化和数据集划分。
- 选择 30 份简历作为第一批实验样本，覆盖 10 个技术岗位族。
- 将统一岗位主表写入 Elasticsearch 索引 `chinese_jobs_v1`。
- 实现字段加权 BM25 检索，每份简历可召回 Top200。
- 接入 `BAAI/bge-m3`，对 BM25 Top200 进行 1024 维向量相似度重排。
- 为 30 份简历生成：
  - 6,000 个 BM25 候选对。
  - 6,000 个 BGE-M3 语义重排结果。
  - 6,000 个可解释自动银标。

### 尚未完成

- `frontend-src` 仍是原项目界面，尚未适配当前中文 BM25/BGE-M3 数据流。
- `docker-compose.yml` 中的 backend/frontend 仍默认使用原作者预构建镜像，不包含本地新增代码。
- BGE-M3 尚未封装为独立 Docker Embedding 服务。
- 尚未把全部岗位向量写入 Elasticsearch HNSW 向量索引；当前只对 BM25 Top200 做向量计算和重排。
- Neo4j 中文岗位、技能、岗位族和技能关系图尚未构建完成。
- 当前银标是自动弱标签，不是人工金标，不能用于宣称真实准确率。
- 尚未完成岗位族门控、学历/专业/经验等硬条件过滤和 Cross-Encoder 精排。
- 尚未完成面向前端的完整简历上传、推荐、差距分析和解释闭环。

## 当前实现的两个数据流

### 数据流一：岗位和简历的离线准备

```text
腾讯/华为公开招聘接口             公务员官方职位表
          |                              |
          +----------> raw 原始数据 <----+
                         |
                         v
                 统一清洗与字段标准化
                         |
                         v
        企业岗位 JSONL/CSV + 公务员岗位 JSONL/CSV
                         |
                         v
              合并为 23,714 条岗位主表
                         |
                         v
             写入 Elasticsearch BM25 索引

中文简历 CSV
    |
    v
脱敏、字段统一、技能标准化、生成 profile_text
    |
    v
5,000 条匿名简历 + 30 份试验简历
```

统一岗位主表位于：

```text
dataset/cleaned/all_jobs_23714_normalized.jsonl
dataset/cleaned/all_jobs_23714_normalized.csv
```

匿名简历位于：

```text
dataset/processed/resumes_anonymized.jsonl
dataset/processed/resumes_anonymized.csv
dataset/annotations/pilot_resumes_30.jsonl
```

### 数据流二：当前简历预测流程

```text
一份中文简历 profile_text
        |
        v
Elasticsearch 字段加权 BM25
        |
        v
从企业岗位中召回 Top200
        |
        v
BGE-M3 编码简历和候选岗位 JD
        |
        v
计算 1024 维向量余弦相似度
        |
        v
对固定 Top200 进行语义重排
        |
        v
结合 BM25、语义、技能覆盖、岗位族生成银标
```

当前 BM25 的主要字段权重为：

```text
岗位标题 6.0
岗位标签 5.0
采集关键词 4.0
岗位描述 2.5
公司名称 1.5
工作地点 1.2
汇总文本 1.0
```

当前语义排序仅按照：

```text
cosine(resume_embedding, job_embedding)
```

从高到低排列。BGE-M3 语义排名并不是最终推荐分数，因为实验中仍出现前端/后端、运维/物流、数据分析/财经等岗位族漂移。

当前银标分数为：

```text
silver_score =
0.45 * BGE-M3 语义排名百分位
+ 0.20 * BM25 排名百分位
+ 0.20 * 简历技能在 JD 中的覆盖率
+ 0.15 * 意向岗位族匹配度
```

银标只用于弱监督训练、候选筛选和人工标注准备。正式评测需要独立人工金标。

## 项目架构

```text
job-hunt-AI/
├── dataset/       中文岗位和简历数据、采集/清洗/实验脚本及实验输出
├── markdown/      目标、方案、修改记录和实验报告
├── backend-src/   FastAPI 后端源码、Elasticsearch/Neo4j/检索服务
├── frontend-src/  React 前端源码，目前尚未适配新的中文预测流程
├── docker-compose.yml
└── README.md
```

### `dataset/`

项目目前最主要的工作目录。

```text
dataset/
├── raw/           原始企业招聘数据、公务员压缩包和职位表
├── cleaned/       清洗后的岗位 JSONL/CSV 和统一岗位主表
├── resume/        原始中文简历数据
├── processed/     脱敏、标准化后的简历
├── annotations/   30 份试验简历、标注规范和金标模板
├── benchmark/     train/dev/test 简历清单
├── retrieval/     BM25、BGE-M3 和银标实验结果
├── config/        采集关键词、技能别名和岗位族关键词
└── scripts/       采集、导入、清洗、合并、简历处理和实验代码
```

重要脚本：

- `collect_public_jobs.mjs`：采集腾讯、华为公开招聘岗位。
- `import_government_jobs.py`：导入公务员 `.xls/.xlsx/.csv` 职位表。
- `normalize_jobs.mjs`：将 raw 数据统一输出为 JSONL/CSV。
- `merge_job_datasets.py`：合并企业和公务员岗位主表。
- `process_chinese_resumes.py`：简历脱敏、技能标准化和试验样本生成。
- `run_bm25_bge_m3_experiment.py`：30 份简历 BM25 Top200、BGE-M3 重排及银标实验。

### `markdown/`

项目文档和实验审计目录。

- `target.md`：比赛目标和总体技术路线。
- `trace.md`：每次修改、运行问题、结果和下一步建议。
- `resume_fix.md`：中文简历处理、银标/金标和基准测试方案。
- `report.md`：中文简历预处理报告。
- `report_BM25.md`：Elasticsearch BM25 实现报告。
- `test_30.md`：30 份简历 BM25+BGE-M3 实验统计和问题分析。

### `backend-src/`

FastAPI 后端源码目录。

```text
backend-src/
├── app/main.py                 FastAPI 应用入口和路由注册
├── app/api/                    岗位、导入、认证、重排等 HTTP 接口
├── app/api/endpoints/bm25.py   新增中文 BM25 查询和统计接口
├── app/core/                   配置及 Elasticsearch/Neo4j 连接
├── app/models/                 岗位、候选人、图谱和重排数据模型
├── app/services/               检索、NLP、图谱、重排等业务服务
├── app/services/chinese_bm25_service.py
│                                中文岗位索引、批量写入和加权 BM25
└── scripts/
    ├── index_chinese_jobs.py    将统一岗位主表写入 Elasticsearch
    └── search_chinese_jobs.py   命令行查询中文岗位
```

原项目中还有英文 NLP、混合检索、Neo4j 和重排服务。这些代码可以继续复用，但目前尚未全部改造成中文数据模型。

### `frontend-src/`

React + TypeScript 前端源码。当前界面和接口仍主要对应原作者的英文演示系统，尚未连接本项目新增的中文 BM25、BGE-M3 和银标结果。

## 复现环境

### 必需软件

- Git。
- Docker Desktop，建议启用 WSL2。
- Python 3.11 或 3.12，推荐 3.11。
- Node.js 18 及以上版本。
- 至少 16GB 内存和 10GB 可用磁盘空间。

### BGE-M3 GPU 环境

推荐：

- NVIDIA GPU。
- 至少 8GB 显存。
- 支持 CUDA 的 PyTorch。
- RTX 4060 8GB 建议使用 `batch-size=2`。

没有 GPU 也可以使用 CPU，但 BGE-M3 推理会明显变慢。

BGE-M3 权重约 2.27GB，第一次运行需要下载，后续会使用 Hugging Face 本地缓存。不要把模型权重提交到 GitHub。

## 快速复现 30 份简历预测

以下命令默认在仓库根目录执行。

### 1. 创建 Python 环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r dataset\requirements.txt
```

安装 CUDA 版 PyTorch 时，应根据本机 CUDA 环境采用 PyTorch 官方对应安装命令。如果 `torch.cuda.is_available()` 返回 `False`，实验会使用 CPU。

检查 GPU：

```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### 2. 启动 Elasticsearch

```powershell
docker compose up -d elasticsearch
docker ps
```

检查服务：

```powershell
curl.exe --noproxy "*" http://127.0.0.1:9200
```

Neo4j 在当前预测中尚未参与，可以暂不启动。需要查看原系统时可运行：

```powershell
docker compose up -d neo4j
```

### 3. 写入统一岗位主表

```powershell
python backend-src\scripts\index_chinese_jobs.py --recreate --batch-size 500
```

预期结果：

```text
index_name: chinese_jobs_v1
succeeded: 23714
failed: 0
document_count: 23714
```

### 4. 运行 BM25 Top200

```powershell
python dataset\scripts\run_bm25_bge_m3_experiment.py --stage bm25
```

该步骤为 30 份简历分别保存 200 个企业岗位候选，共 6,000 对。

### 5. 运行 BGE-M3 语义重排

```powershell
python dataset\scripts\run_bm25_bge_m3_experiment.py `
  --stage rerank `
  --batch-size 2 `
  --max-length 1024
```

国内网络下载较慢时，可先设置镜像：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

模型下载成功后可离线运行：

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
```

也可以一次执行完整流程：

```powershell
cd dataset
npm run experiment:test30
```

### 6. 查看预测结果

```text
dataset/retrieval/test_30/bm25_top200_30.jsonl
dataset/retrieval/test_30/bge_m3_reranked_top200_30.jsonl
dataset/retrieval/test_30/resume_job_silver_30.jsonl
dataset/retrieval/test_30/resume_job_rankings_30.csv
dataset/retrieval/test_30/experiment_summary.json
```

推荐直接用 Excel 或 WPS 打开：

```text
dataset/retrieval/test_30/resume_job_rankings_30.csv
```

它同时包含 BM25 名次、BGE-M3 名次、余弦相似度、银标等级、岗位族匹配和技能覆盖。

## 复现岗位数据采集与处理

公开招聘接口可能调整或限制访问，因此重新采集的数量和当前快照不一定完全相同。仓库已经保留当前实验使用的数据快照，复现实验无需重新抓取。

### 1. 安装 Node.js 和 Python 依赖

```powershell
cd dataset
npm install
pip install -r requirements.txt
```

### 2. 采集腾讯和华为岗位

```powershell
npm run collect
```

也可以单独采集：

```powershell
npm run collect:tencent
npm run collect:huawei
```

采集配置位于：

```text
dataset/config/seed_queries.json
```

原始结果写入：

```text
dataset/raw/chinese_jobs/
```

### 3. 清洗企业岗位

建议显式指定输入和输出，避免误用 `raw/chinese_jobs/` 中最新的其他数据源文件：

```powershell
node scripts\normalize_jobs.mjs `
  --input raw\chinese_jobs\你的企业岗位raw文件.json `
  --jsonl cleaned\enterprise_jobs_normalized.jsonl `
  --csv cleaned\enterprise_jobs_normalized.csv
```

### 4. 导入公务员职位表

将官方 `.xls/.xlsx/.csv` 文件放入 `dataset/raw/government_jobs/`，然后执行：

```powershell
python scripts\import_government_jobs.py `
  --input "raw\government_jobs\职位表.xls" `
  --source-name "2026国家公务员" `
  --output "raw\chinese_jobs\government_jobs.json"
```

再进行清洗：

```powershell
node scripts\normalize_jobs.mjs `
  --input raw\chinese_jobs\government_jobs.json `
  --jsonl cleaned\government_jobs_normalized.jsonl `
  --csv cleaned\government_jobs_normalized.csv
```

### 5. 合并企业和公务员岗位

如果使用仓库默认文件名：

```powershell
npm run merge:jobs
```

自定义输入时：

```powershell
python scripts\merge_job_datasets.py `
  --inputs cleaned\enterprise_jobs_normalized.jsonl cleaned\government_jobs_normalized.jsonl `
  --jsonl-output cleaned\all_jobs_normalized.jsonl `
  --csv-output cleaned\all_jobs_normalized.csv
```

### 6. 处理中文简历

原始简历文件应位于 `dataset/resume/`，默认文件名为：

```text
Chinese_resume_data.csv
revise_Chinese_resume_data.csv
```

执行：

```powershell
npm run process:resumes
```

该步骤会：

- 删除姓名、电话、邮箱等直接身份信息。
- 生成稳定匿名 `resume_id`。
- 标准化技能名称。
- 合并岗位意向、学历、专业、技能、工作和项目经历为 `profile_text`。
- 按内容哈希划分 train/dev/test，避免重复简历跨集合泄漏。
- 生成 30 份试验简历。

## Docker 一键复现当前预测流程

仓库新增了独立的 `docker-compose.reproduce.yml`，用于复现当前已经完成的中文预测流程。它不会占用宿主机的 Elasticsearch 9200 端口，也不会启动尚未适配的旧前端。

需要提前安装：

- Git。
- Docker Desktop（Windows 建议启用 WSL2）。
- GPU 模式需要 NVIDIA 驱动、支持 GPU 的 Docker Desktop；CPU 模式不需要 CUDA。
- 建议至少 16GB 内存、15GB 可用磁盘空间。

首次运行会拉取或构建以下镜像：

| 镜像 | 用途 | 是否必需 |
| --- | --- | --- |
| `mvyas7/job-hunt-ai-backend:v1.2.0` | Python、PyTorch、Transformers 基础环境 | 必需 |
| `job-hunt-ai-toolkit:2026-06-13` | 从本仓库 Dockerfile 构建，运行索引和预测脚本 | 自动构建 |
| `docker.elastic.co/elasticsearch/elasticsearch:8.11.0` | 中文字段加权 BM25 | 必需 |
| `node:20-bookworm-slim` | 重新采集岗位数据 | 仅采集时需要 |
| `neo4j:5.14-community` | 后续岗位技能图谱 | 当前预测不需要 |

BGE-M3 权重约 2.27GB，不提交到 GitHub。第一次重排会下载到 Docker 卷 `jobhunt-repro_reproduce_huggingface_cache`，后续运行直接复用。

Windows PowerShell，NVIDIA GPU：

```powershell
.\scripts\reproduce.ps1 -Mode gpu -Stage all -HfEndpoint https://hf-mirror.com
```

运行前可检查 Docker 是否能识别 GPU：

```powershell
docker run --rm --gpus all job-hunt-ai-toolkit:2026-06-13 `
  python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

如果 CUDA 返回 `False`，或 Docker Desktop 报显存充足但仍无法分配显存，先重启 Docker Desktop；仍未恢复时使用下面的 CPU 模式完成复现。

Windows CPU：

```powershell
.\scripts\reproduce.ps1 -Mode cpu -Stage all -HfEndpoint https://hf-mirror.com
```

Linux/macOS（macOS 只能使用 CPU 模式）：

```bash
chmod +x scripts/reproduce.sh
HF_ENDPOINT=https://hf-mirror.com ./scripts/reproduce.sh gpu all
```

也可以分阶段执行：

```powershell
.\scripts\reproduce.ps1 -Mode gpu -Stage index
.\scripts\reproduce.ps1 -Mode gpu -Stage bm25
.\scripts\reproduce.ps1 -Mode gpu -Stage rerank -HfEndpoint https://hf-mirror.com
```

运行结果位于 `dataset/retrieval/test_30/`。停止容器但保留索引和模型缓存：

```powershell
docker compose -p jobhunt-repro -f docker-compose.reproduce.yml down
```

只有需要完全删除索引、Neo4j 数据和 BGE-M3 缓存时才使用 `down -v`。

## 当前 Docker 状态

`docker-compose.yml` 可以直接启动：

- Elasticsearch 8.11。
- Neo4j 5.14。
- 原作者预构建 FastAPI backend。
- 原作者预构建 React frontend。

```powershell
docker compose up -d
```

但需要注意：预构建 backend/frontend 不包含本仓库新增的中文代码。当前最可靠的复现方式是：

```text
Docker 运行 Elasticsearch
+ 本地 Python 运行索引和 BGE-M3 实验脚本
```

新增的复现 Compose 已将当前中文索引和预测代码封装到 toolkit 容器。完整 FastAPI 在线预测服务、中文前端和 Neo4j 图谱仍属于后续工作，当前复现的是离线 30 份简历实验流水线。

## 实验结果摘要

30 份简历实验结果：

- BM25 生成 6,000 个候选，Elasticsearch 查询延迟 P50 为 49ms，P95 为 95.2ms。
- 30 份候选合并后包含 587 个唯一岗位。
- BGE-M3 编码 617 段唯一文本，RTX 4060 上耗时约 21.65 秒。
- 语义排序与 BM25 排序的平均绝对名次变化为 60.34。
- 两种排序 Top10 平均重合率为 2.67%。
- 银标 0/1/2/3 级数量为 3159/2445/378/18。

详细分析见：

- `markdown/report_BM25.md`
- `markdown/test_30.md`

## 下一阶段

1. 为约 600 个简历-岗位对进行双人独立人工金标。
2. 加入岗位族门控和学历、专业、经验等硬条件。
3. 对 Top50 接入 Cross-Encoder 精排。
4. 将岗位、技能、技能别名和岗位族写入 Neo4j。
5. 比较 BM25、BM25+BGE-M3、加入 Neo4j 和完整学习排序的消融结果。
6. 将中文预测接口接入新的 Docker backend，并改造前端。

## 安全与合规

- 只采集公开岗位信息并遵守数据源访问限制。
- 不将登录账号、密码、Cookie 或浏览器登录状态提交到仓库。
- 简历进入实验前必须脱敏。
- 推荐分数只表示简历与特定岗位的相关程度，不能代表候选人的整体价值，也不能替代人工招聘决策。
