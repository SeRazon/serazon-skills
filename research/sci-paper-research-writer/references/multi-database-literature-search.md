# 多数据库学术检索与文献核验模块

## 目的

把 Google Scholar、Crossref、OpenAlex、Semantic Scholar、PubMed/Europe PMC、arXiv、Web of Science、Scopus、ScienceDirect、IEEE Xplore、CNKI 等来源组织成“发现—交叉核验—全文/证据—引用管理”的流程。检索入口可以很多，但正式引用必须回到可追溯的元数据来源和论文正文。

## 平台路由

### 第一层：开放元数据与交叉核验

优先使用 Crossref、OpenAlex、Semantic Scholar、PubMed/Europe PMC、arXiv 等可结构化查询的来源。用于获取题名、作者、年份、期刊、DOI、PMID、摘要、引用关系和开放获取线索。不同平台结果要去重，并以 DOI、PMID、数据库唯一 ID 或规范化题名+作者+年份为匹配键。

### 第二层：学科平台

- 生物医学与临床：PubMed/Europe PMC，必要时补充 Embase、Web of Science、Scopus。
- 计算机与人工智能：Semantic Scholar、arXiv、DBLP、ACM Digital Library、IEEE Xplore、Papers with Code。
- 综合自然科学：Web of Science、Scopus、Crossref、OpenAlex、出版社页面。
- 化学与材料：Web of Science、Scopus、ACS、ScienceDirect、Springer、Wiley。
- 中文研究：CNKI（中国知网）及学校图书馆可访问的中文数据库。

Web of Science、Scopus、CNKI、ScienceDirect 等需要登录或机构订阅时，只使用用户已有的合法访问权限；不能绕过验证码、付费墙、访问控制或反爬机制。

### 第三层：发现入口

Google Scholar 和用户提供的导航页（例如老师发送的学术平台导航页）可以用于发现关键词、相关文章、被引文献和开放版本。导航页是入口，不是文献真实性证明；Google Scholar 的结果也必须回到 DOI、出版社、PubMed、Crossref 等来源核验。

## 两遍搜索策略

### 第一遍：宽搜与候选表

1. 明确主题、研究对象、暴露/干预、结局、研究设计和时间范围。
2. 为每个核心概念生成同义词、缩写、旧称和受控词表词项。
3. 形成 2–4 个互补检索式，覆盖不同命名习惯。
4. 跨至少两个独立来源搜索，记录数据库、检索式、日期和结果数量。
5. 输出候选表，先不把搜索摘要当作结论。

### 第二遍：深搜与证据表

1. 对核心候选文献回查 DOI/PMID、出版社页面、期刊官网或数据库记录。
2. 检查摘要、正文、表格、补充材料和研究设计；关键数字必须能定位到原文位置。
3. 沿参考文献和被引文献追踪，主动寻找不一致结果和反方证据。
4. 仅对合法开放获取全文生成下载清单；非开放全文标记为“需要机构访问”而不是继续尝试绕过。
5. 将每篇文献放入证据矩阵，并区分“论文存在”与“支持指定论断”。

## 来源优先级与状态

建议优先级：出版社/期刊官网和正式 DOI 记录 > PubMed、Crossref、Web of Science、Scopus、CNKI 等权威数据库 > OpenAlex、Semantic Scholar 等聚合元数据 > Google Scholar、网页摘要和第三方导航页。

每条记录使用以下状态之一：

- `candidate`：仅发现候选，尚未核验。
- `metadata-verified`：核心元数据与可靠来源匹配。
- `claim-verified`：已读取正文、表格或补充材料，确认可支持指定论断。
- `open-pdf-available`：存在合法开放全文入口。
- `institution-access-required`：可能存在，但全文需要学校/机构权限。
- `needs-check`：来源冲突、字段不完整或无法访问。
- `excluded`：重复、无关、撤稿/更正未处理或无法确认。

## 统一文献记录字段

| 字段 | 说明 |
|---|---|
| `record_id` | 本地唯一编号 |
| `title` | 规范化题名 |
| `authors` | 作者及作者顺序 |
| `year` | 区分 online-first 与卷期年份 |
| `venue` | 期刊、会议、学位论文或预印本 |
| `doi` / `pmid` / `other_id` | 唯一标识 |
| `source_records` | 核验过的数据库或出版社来源 |
| `document_type` | 原始研究、综述、指南、预印本等 |
| `oa_status` | 开放全文、机构访问或未知 |
| `claim_ids` | 支持的论断编号 |
| `evidence_location` | 页码、章节、表格、图或补充材料位置 |
| `limitations` | 样本、设计、外推和偏倚限制 |
| `verification_status` | 上述状态 |
| `checked_at` | 核验日期 |

## 去重与冲突处理

- DOI 去掉 `https://doi.org/`、大小写和尾部标点后比较。
- DOI 缺失时使用 PMID、数据库 ID，或题名规范化后与第一作者和年份联合匹配。
- 同一研究的预印本、会议版、正式期刊版分别保留版本关系，正式发表版优先进入参考文献表。
- 在线发表年份与卷期年份冲突时并列记录并说明，不强行选择一个“看起来正确”的年份。
- 题名相同但作者、期刊或 DOI 不同的记录必须人工确认，不能自动合并。
- 发现撤稿、勘误或表达关注时，标记并检查正文是否仍适合引用。

## Google Scholar、CNKI 和 ScienceDirect 的边界

- Google Scholar：适合发现线索、查看引用网络和查找作者上传的开放版本；不作为唯一元数据来源。
- CNKI：可用于中文题名、作者、机构、关键词、引文和学位论文检索；正式引用前核对题名、刊名、年份、卷期、页码和 DOI/数据库记录。
- ScienceDirect：可用于出版社正文和开放获取状态确认；需要订阅的内容由用户通过学校或机构登录访问。
- 老师提供的导航页：只作为手动导航入口，不批量抓取不明镜像，不绕过验证码或访问限制。

## 最低交付物

完成检索任务时至少产出：

1. `search_log.md`：数据库、检索式、日期、结果数量和调整记录；
2. `candidate_references.csv` 或 Markdown 表：候选文献和核验状态；
3. `evidence_matrix.md`：论断—文献—证据位置—局限；
4. `citation_audit.md`：真实性、元数据、支持性和反方证据审计；
5. 合法开放全文清单（如用户需要），对需机构权限的项目明确标注。

## 输出限制

不要承诺“全部文献绝对真实”或“AI率降到某个百分比”。应明确哪些记录已经核验、哪些只发现未核验、哪些论断仍缺少正文证据。对 CNKI、Web of Science、Scopus、ScienceDirect 或 Google Scholar 的访问受登录、地区、验证码和订阅状态影响时，直接报告限制。
