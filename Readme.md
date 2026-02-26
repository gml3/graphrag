# GraphRAG 3.0 极简版架构设计大纲

**核心思想：**
将系统完全解耦为**“图谱构建 (Indexing)”**与**“检索查询 (Search)”**两个完全独立的模块。中间通过标准化存储（Parquet + LanceDB）解耦。这意味着可以在离线机器上建图，在另一台机器上直接搜索，互不干涉。

## 模块一：索引构建流程 (Indexing Pipeline)
负责将原始文档转化为结构化的知识图谱并写入存储。

**1. 数据读取 (Loader)**
- `load_input.py`: 从本地 `.txt`/`.csv` 读取原始文本。

**2. 文本切分 (Chunking)**
- `chunk_text.py`: 按 Token 或固定长度切分文本，带 Overlap 保证上下文连贯。

**3. 信息抽取 (Extraction)**
- `extract_entities.py`: 调用 LLM 抽取实体 (Node) 和关系 (Edge)。
- *输出：`entities.parquet`, `relationships.parquet`*

**4. 社区聚合 (Community Detection)**
- `extract_communities.py`: 基于实体关系图运用 Leiden 算法划分社区。
- `build_community_reports.py`: 对于各个层级的社区生成总结报告 (Community Reports)。
- *输出：`community_reports.parquet`*

**5. 向量化 (Embedding)**
- `embed_data.py`: 调用 Embedding API 将实体的描述文本向量化，存入 LanceDB 向量库。
- *输出：LanceDB 存储目录*

---

## 模块二：检索查询流程 (Search Pipeline)
通过纯净的接口提供大模型问答能力，不依赖 Indexing 环境的任何内部状态。

**1. 数据加载器 (State Loader)**
- 启动时加载已准备好的 Parquet 表（Entities, Relationships, Reports）。
- 连接 LanceDB 向量库。

**2. 本地检索 (Local Search) — 针对具体实体的问题**
- **步骤 1：向量召回。** 用问题文本去 LanceDB 匹配最相关的 K 个实体。
- **步骤 2：图谱扩充。** 抓取这 K 个实体相连的所有关联实体和关系。
- **步骤 3：文本扩充。** 抓取它们最初对应的原始切片 (`text_units`)。
- **步骤 4：生成 Prompt 汇总。** 把前面所有信息打包成 Context 发给 LLM 生成解答。

**3. 全局检索 (Global Search) — 针对整体数据的宏观问题**
- **步骤 1：Map 环节。** 将问题抛给图谱顶层（Root 层）的数百个社区报告，让并行的 LLM 给各个社区打分并写评价。
- **步骤 2：Reduce 环节。** 挑选得分最高的 Top-N 个评价，扔给最终的 LLM 进行全局融合成文。

---

## 目录结构规划
```text
graphrag3.0/
├── input/               # 存放生文本
├── output/              # 存放生成的 parquet 和 lancedb
├── index/               # 模块一：纯粹的流水线脚本
│   ├── run_pipeline.py  # 启动建库！
│   ├── extractors/
│   └── ...
└── query/               # 模块二：没有任何图谱构建代码，只有检索
    ├── local_search.py  # 局部问答
    ├── global_search.py # 宏观总结
    └── context_builder/ # 专门用来把图谱数据拼成字符串
```