# Elasticsearch BM25 实现报告

## 1. 本阶段结果

统一岗位主表已经写入本地 Elasticsearch，并建立独立中文岗位索引 `chinese_jobs_v1`。

- 输入：`dataset/cleaned/all_jobs_23714_normalized.jsonl`
- 岗位总数：23714
- 企业岗位：3000
- 公务员岗位：20714
- 写入成功：23714
- 写入失败：0
- 内容重复标记：1628
- 单次查询最多返回：Top200

原项目的英文 `jobs` 索引没有被覆盖，便于后续对比和回退。

## 2. 修改内容

### 2.1 中文 BM25 服务

新增 `backend-src/app/services/chinese_bm25_service.py`，负责：

- 创建和重建 `chinese_jobs_v1`。
- 将统一岗位记录转换成 Elasticsearch 文档。
- 批量导入 JSONL。
- 执行字段加权 BM25 查询。
- 按企业/公务员和地区筛选。
- 默认排除内容重复岗位。
- 返回索引数量、重复数量和查询耗时。

### 2.2 导入和查询脚本

新增：

- `backend-src/scripts/index_chinese_jobs.py`
- `backend-src/scripts/search_chinese_jobs.py`

重建并导入索引：

```powershell
python backend-src/scripts/index_chinese_jobs.py --recreate
```

查询示例：

```powershell
python backend-src/scripts/search_chinese_jobs.py "大模型 人工智能 算法" --source-type enterprise --size 20
python backend-src/scripts/search_chinese_jobs.py "法学 行政管理" --source-type government --size 20
```

### 2.3 FastAPI 接口

新增 `backend-src/app/api/endpoints/bm25.py`，并在 `backend-src/app/main.py` 注册：

- `POST /api/v1/bm25/search`
- `GET /api/v1/bm25/stats`

请求示例：

```json
{
  "query": "Python 后端开发 数据库",
  "size": 200,
  "source_type": "enterprise",
  "location": "北京",
  "exclude_duplicates": true
}
```

当前 Docker 后端仍是作者发布的预构建镜像，新 API 尚未进入该容器。核心索引和检索已经通过本地 Python 脚本实际验证；后续构建本地 backend 镜像后即可由前端调用。

接口代码已使用 FastAPI `TestClient` 验证：`/stats` 返回 23714 条文档，`/search` 能按请求数量正常返回企业岗位，两个请求状态码均为 200。

## 3. 索引设计

BM25 参数采用 Elasticsearch 常用基线：

- `k1 = 1.2`：控制词频增长速度。
- `b = 0.75`：进行文档长度归一化，避免超长 JD 单纯依靠词频占优。

字段权重如下：

| 字段 | 权重 | 设计目的 |
|---|---:|---|
| `job_title` | 6.0 | 岗位名称最能直接说明职业方向 |
| `tags` | 5.0 | 强调技能、业务线和岗位标签 |
| `keyword` | 4.0 | 保留采集时的岗位主题 |
| `job_description` | 2.5 | 匹配职责、要求、专业和技能细节 |
| `company_name` | 1.5 | 支持单位名称检索但避免主导排序 |
| `location` | 1.2 | 地点可参与匹配，也可单独过滤 |
| `all_text` | 1.0 | 作为字段遗漏时的补充召回 |

统一主表中的 `raw` 原始对象没有重复写入 Elasticsearch。它通常体积较大，且不直接参与召回；原始信息仍保留在本地 JSONL/CSV 中，可通过 `job_id` 回溯。

## 4. 实际验证

| 查询 | 数据范围 | 命中数 | ES 耗时 | Top 结果特点 |
|---|---|---:|---:|---|
| Python 后端开发 | 企业 | 1736 | 26ms | 后端开发、研发工程师、客户端研发 |
| 大模型 人工智能 算法 | 企业 | 2282 | 29ms | 大模型、具身智能、算法工程师 |
| 法学 行政管理 公务员 | 公务员 | 19802 | 49ms | 行政执法、综合管理、财务管理 |
| 计算机/软件工程简历式长查询 | 全部 | 11229 | 71ms | 成功稳定返回 Top200 |

这些结果证明当前链路已经满足第一阶段目标：从 23714 个岗位中快速缩小到 200 个候选岗位，为后续 Transformer Embedding 计算降低成本。

## 5. 当前局限

1. 当前中文分析使用 Elasticsearch 内置 `standard` tokenizer，不依赖插件，部署稳定，但中文分词精度只是基线水平。
2. 公务员 JD 中大量岗位共享“行政执法、综合管理”等表述，因此宽泛查询命中数很大，需要进一步利用专业、学历、政治面貌和工作地点做结构化过滤。
3. `tags` 目前来自已有数据字段，并不等于经过统一技能词典抽取后的正式技能标签。
4. BM25 只能判断词项匹配，无法充分识别同义词、隐含技能和跨表达语义。
5. 当前只有运行验证，还没有人工简历-岗位金标，因此暂时不能报告 `Recall@200`。

## 6. 后续工作

下一阶段按以下顺序推进：

1. 对 30 份试标简历批量查询并保存 BM25 Top200。
2. 接入 `BAAI/bge-m3` 或 Qwen Embedding，将简历和候选 JD 向量化。
3. 在 Top200 内计算余弦相似度并完成语义重排。
4. 为每份简历构造约 20 个混合候选，进行人工金标标注。
5. 计算 BM25 的 `Recall@200`，以及重排后的 `NDCG@5/10`、`MRR` 和 `HitRate@K`。
6. 将标准化技能和岗位关系写入 Neo4j，用于推荐解释、技能差距分析和图谱扩展。

本阶段已经完成推荐链路中负责快速召回的第一层，下一步应直接进入“30 份简历批量 Top200 + 中文 Embedding 重排”，暂时不需要继续扩大岗位数据量。
