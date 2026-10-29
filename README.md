# serazon-skills

星鸿使用的 Skills 仓库。

> 想让 AI 更懂科研，更懂全栈开发，更懂算法？不妨一试。

按用途分为科研、设计、工程、算法四类，持续补充。每个技能是一个独立目录，遵循 `SKILL.md` + `references/` + `scripts/` + `assets/` 的组织方式，可直接被支持 Skills 的 AI 助手加载。

当前收录 **22** 个技能（research 15 · design 5 · engineering 2），更新记录见提交历史。

## 目录

| 目录 | 内容 | 数量 |
|---|---|---|
| [`research/`](research/) | 科研：Idea 评估、综述调研、文献精读与管理、论文写作与润色、作图、投稿前审查、Rebuttal | 15 |
| [`design/`](design/) | 设计：前端交互规范、前端设计、品牌设计模板、公众号排版、歌词视频 | 5 |
| [`engineering/`](engineering/) | 工程：代码审查、技能安全审查 | 2 |
| [`algorithm/`](algorithm/) | 算法（预留，待补充） | — |
| [`_template/`](_template/) | 新增技能的模板与说明 | — |

### research

| 技能 | 说明 |
|---|---|
| `idea-evaluator` | 用"更高、更快、更强、更省、更广"五维评估研究想法，附致命缺陷审查 |
| `deep-research` | 综述级文献调研：多视角检索、逐条核验、MECE 分类与交叉对比 |
| `research-literature-manager` | 论文精读为 11 板块结构化大纲，逐图解析，归档进本地文献库并支持检索 |
| `tech-paper-template` / `benchmark-paper-template` | 技术类 / 基准与评估类论文的骨架与逻辑链 |
| `intro-drafter` | 六段式 Introduction 正文或大纲 |
| `paper-writer` | 证据门控的正文写作，事实性声明可溯源 |
| `paper-polish` | 忠于原意的润色：语法、去 AI 腔、中文稿改投稿级英文 |
| `sci-paper-research-writer` | SCI 论文与真实文献写作：检索、证据矩阵、引用审计 |
| `baige-lunwen-xiezuo` | 中文论文六步写作（含知网/万方检索、GB/T 7714、引用硬审计） |
| `pre-submission-reviewer` | 投稿前五维审查，CRITICAL / MAJOR / MINOR 分级 |
| `figure-designer` | 动机图、总览图、实验结果图的设计范式与质控 |
| `drawio-reconstruction` | 参考图重建为可编辑 `.drawio` 并导出预览 |
| `rebuttal-guidance` | 针对审稿意见的条件说服式回应指导 |
| `vibe-research-workflow` | AI 辅助科研的 Vibe Coding / Figure / Writing 流程 |

### design

| 技能 | 说明 |
|---|---|
| `frontend-interaction-design` | 弹层选型与打扰分级、移动端手势组件、视觉工艺与设计令牌、表单控件、触控热区、无障碍与交付走查 |
| `awesome-design-md` | 54 个知名网站的 DESIGN.md 设计系统模板（上游：VoltAgent/awesome-design-md，MIT） |
| `frontend-design` | 前端界面设计与实现规范 |
| `gzh-design` | 公众号排版引擎：Markdown 转可粘贴 HTML |
| `lyric-video-pv` | 歌词视频生成流程 |

### engineering

| 技能 | 说明 |
|---|---|
| `code-review-and-quality` | 五维度结构化代码审查（正确性 / 可读性 / 可维护性 / 性能 / 安全），合并前使用 |
| `skills-security-check` | 第三方技能安全审计：检查脚本权限、外部请求、凭据与敏感信息（腾讯云鼎实验室出品） |

## 使用

把需要的技能目录复制到本机的技能目录：

```bash
# macOS / Linux
cp -r research/deep-research ~/.workbuddy/skills/

# Windows（PowerShell）
Copy-Item -Recurse research\deep-research $env:USERPROFILE\.workbuddy\skills\
```

要求：目录根部含 `SKILL.md`，YAML frontmatter 至少包含 `name` 与 `description`。该格式适用于 WorkBuddy、Claude Skills 等支持 Skills 规范的工具。

## 添加新技能

1. 在对应类别下新建 `<skill-name>/`，放入 `SKILL.md` 及所需资源；
2. 结构参照 [`_template/`](_template/)；
3. 校验：frontmatter 可解析，`name` 与目录名一致，且能完成一次最小调用；
4. **确认许可与署名**：
   - 第三方技能必须有可核验的许可证（无 LICENSE 时查上游仓库 `homepage`）；
   - 在 [`THIRD_PARTY.md`](THIRD_PARTY.md) 登记来源与许可；
   - 含商标、付费模板、抓取图片等素材的，先确认能否再分发，否则不入库；
5. 提交信息使用规范前缀：

```text
feat: add <skill-name>
fix: <修正内容>
chore: <杂项>
```

## 许可

- 本仓库自有内容采用 [MIT](LICENSE)。
- 目录内含第三方技能，许可与出处见 [THIRD_PARTY.md](THIRD_PARTY.md)，使用时请遵守各自条款；第三方技能的商标与视觉识别归各自权利人所有。

## 说明

本仓库仅存放技能定义与配套脚本，不包含任何账号凭据、接口密钥或个人数据。
