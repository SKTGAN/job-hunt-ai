# 中文简历数据处理执行报告

## 1. 本次目标

按照 `markdown/resume_fix.md`，完成中文简历基准建设的第一阶段：

- 对 5000 条中文简历进行脱敏。
- 将原始 34 列转换为适合 BM25、Embedding 和 Neo4j 使用的统一结构。
- 对技能及熟练度进行配对和标准化。
- 保留原版、修订版筛选标签的差异用于审计。
- 建立无重复泄漏的 train/dev/test 基础划分。
- 准备 30 份试标简历和人工金标模板。

## 2. 已实现内容

### 2.1 简历脱敏

处理结果不包含以下字段：

- 姓名。
- 性别。
- 年龄。
- 电话。
- 邮箱。

每条简历使用不可逆哈希生成 `resume_id`。验证结果中手机号和邮箱模式命中数为 0。

### 2.2 统一结构

每条简历包含：

- `resume_id` 和 `profile_hash`。
- 意向岗位族、学历、院校类别、专业和英语水平。
- 企业规模维度的工作经验。
- 小型、中型和大型项目数量。
- 原始技能分组、标准化技能和技能熟练度。
- 用于 BM25 和 Embedding 的 `profile_text`。
- 原版标签、修订版标签和标签冲突标记。

`profile_text` 不包含筛选结果和个人敏感信息，避免标签泄漏到检索模型中。

### 2.3 技能标准化

第一版已拆分常见组合技能，例如：

- `HTML/CSS` 转换为 `HTML`、`CSS`。
- `React/Vue` 转换为 `React`、`Vue`。
- `Docker/Kubernetes` 转换为 `Docker`、`Kubernetes`。
- `TensorFlow/PyTorch` 转换为 `TensorFlow`、`PyTorch`。
- `Tableau/Power BI/FineBI` 转换为三个独立技能。

技能与熟练度列在 5000 条数据中均能正确对齐，没有发现数量错位。

## 3. 运行结果

| 检查项 | 结果 |
| --- | ---: |
| 输入简历 | 5000 |
| 输出简历 | 5000 |
| 唯一匿名 ID | 5000 |
| 唯一简历文本 | 4998 |
| 重复简历行 | 2 |
| PII 模式命中 | 0 |
| 空 `profile_text` | 0 |
| 空技能列表 | 0 |
| 原版与修订版标签冲突 | 2033（40.66%） |

基础数据划分：

| 集合 | 数量 |
| --- | ---: |
| Train | 2951 |
| Dev | 995 |
| Test | 1054 |

划分按照 `profile_hash` 完成，因此相同简历内容不会跨集合，重复泄漏数为 0。该划分目前是工程基线，后续获得金标后还需增加 skill-disjoint 测试集。

## 4. 数据集特点

### 4.1 结构化程度高

每份简历平均包含 10.14 个标准化技能，最少 3 个、最多 24 个。生成的检索文本平均约 201 个字符，适合先建立 BM25 与中文 Embedding 基线。

### 4.2 分布较规则，可能含较强合成特征

- 修订版筛选结果正好为通过 2500、不通过 2500。
- 学历中本科 2883、专科 2084、硕士及以上仅 33。
- 计算机类专业 3536、非计算机类 1464。
- 5000 条数据仅覆盖 10 个预设技术岗位族。
- Java、Python、SQL、JavaScript、Go 出现频率很高，技能组合模式较集中。

这些特征适合流程联调和模型开发，但可能不能完整反映真实中文求职者分布。

### 4.3 筛选标签不能直接作为岗位匹配金标

原版和修订版有 2033 条标签不同，且缺少标签修改依据。当前处理结果保留两版标签，但默认修订版只用于辅助分类实验，不能用于报告正式的人岗检索指标。

## 5. 已生成文件

### 处理数据

- `dataset/processed/resumes_anonymized.jsonl`
- `dataset/processed/resumes_anonymized.csv`
- `dataset/processed/resume_quality_report.json`

### 基础划分

- `dataset/benchmark/resume_train_manifest.jsonl`
- `dataset/benchmark/resume_dev_manifest.jsonl`
- `dataset/benchmark/resume_test_manifest.jsonl`

### 标注准备

- `dataset/annotations/pilot_resumes_30.jsonl`
- `dataset/annotations/annotation_guideline.md`
- `dataset/annotations/resume_job_gold_template.csv`

30 份试标简历覆盖全部 10 个岗位族，每类 3 份，并保证 30 份简历文本互不重复。

## 6. 当前尚未完成

- 尚未建立 Elasticsearch BM25 岗位索引。
- 30 份试标简历尚未生成每份约 20 个岗位候选。
- 尚未产生简历-岗位银标和人工金标。
- 尚未计算 `Recall@200`、`NDCG@10`、MRR 等指标。
- 当前划分不是最终 skill-disjoint 基准划分。

这些工作依赖下一阶段的 BM25 候选召回和岗位技能抽取，不能通过现有“通过/不通过”标签替代。

## 7. 下一步建议

1. 将统一岗位主表写入 Elasticsearch，建立字段加权 BM25 索引。
2. 用 30 份试标简历分别召回 Top200 岗位。
3. 从 BM25、Embedding、图谱候选和随机负样本中，每份抽取约 20 个岗位。
4. 按 `annotation_guideline.md` 完成双人独立标注和第三人仲裁。
5. 建立约 600 对第一批金标，开始评测 BM25 `Recall@200`。
6. 再比较 `bge-m3`、Qwen Embedding 与原英文模型的重排效果。

## 8. 结论

中文简历已经从包含个人信息的原始表格，转换为可复现、可审计、适合本地检索和向量化的统一数据。当前数据可以直接用于 BM25 和 Embedding 工程联调，但正式模型结论必须等待独立的简历-JD 人工金标。
