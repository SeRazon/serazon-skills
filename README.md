# serazon-skills

星鸿使用的 Skills 仓库。

> 想让 AI 更懂科研，更懂全栈开发，更懂算法？不妨一试。

按用途分为科研、设计、工程、算法四类。每个技能是一个独立目录，遵循 `SKILL.md` + `references/` + `scripts/` + `assets/` 的组织方式，可直接被支持 Skills 的 AI 助手加载。

当前内置 **12** 个技能（research 7 · design 2 · engineering 2 · algorithm 1）；另有 12 个因许可限制**仅提供链接**，见 [`LINKS.md`](LINKS.md)。

## 目录

| 目录 | 内容 | 数量 |
|---|---|---|
| [`research/`](research/) | 科研：Idea 评估、论文骨架、作图、投稿前审查、参考图重建 | 7 |
| [`design/`](design/) | 设计：前端交互规范、品牌设计模板 | 2 |
| [`engineering/`](engineering/) | 工程：代码审查、软著材料 | 2 |
| [`algorithm/`](algorithm/) | 算法：竞赛算法选型、C++ 模板、赛场流程 | 1 |
| [`_template/`](_template/) | 四类技能的最小模板（research / design / engineering / algorithm） | — |

### research

| 技能 | 说明 | 许可 |
|---|---|---|
| `idea-evaluator` | 五维评估研究想法（更高/更快/更强/更省/更广），附致命缺陷审查 | CC BY 4.0 |
| `tech-paper-template` | 技术类论文的逻辑链与骨架 | CC BY 4.0 |
| `benchmark-paper-template` | 基准与评估类论文的骨架与实验设计 | CC BY 4.0 |
| `figure-designer` | 动机图、总览图、实验结果图的设计范式与质控 | CC BY 4.0 |
| `pre-submission-reviewer` | 投稿前五维审查，CRITICAL / MAJOR / MINOR 分级 | CC BY 4.0 |
| `vibe-research-workflow` | AI 辅助科研的 Vibe Coding / Figure / Writing 流程 | CC BY 4.0 |
| `drawio-reconstruction` | 参考图重建为可编辑 `.drawio` 并导出预览 | MIT |

### design

| 技能 | 说明 | 许可 |
|---|---|---|
| `frontend-interaction-design` | 弹层选型与打扰分级、移动端手势组件、视觉工艺与设计令牌、表单控件、触控热区、无障碍与交付走查 | MIT |
| `awesome-design-md` | 54 个知名网站的 DESIGN.md 设计系统模板（上游：VoltAgent/awesome-design-md） | MIT |

### engineering

| 技能 | 说明 | 许可 |
|---|---|---|
| `code-review-and-quality` | 五维度结构化代码审查（正确性 / 可读性 / 可维护性 / 性能 / 安全），合并前使用 | MIT |
| `software-copyright` | 中国软著登记材料：源码扫描、前后各30页源程序文档、申请表字段、用户手册骨架、证据映射、AI 使用声明与材料自检 | MIT |

### algorithm

| 技能 | 说明 | 许可 |
|---|---|---|
| `xcpc-oi` | 竞赛算法选型与实现：复杂度速判、数据结构、图论、DP、数学、字符串与几何、赛场调试、C++17 模板与对拍脚本 | MIT |

## 未内置（仅链接）

因许可不兼容（CC BY-NC-SA 4.0 / AGPL-3.0）或未声明许可，以下技能不收录内容，只保留获取入口：`deep-research`、`intro-drafter`、`paper-polish`、`paper-writer`、`rebuttal-guidance`、`research-literature-manager`、`sci-paper-research-writer`、`baige-lunwen-xiezuo`、`gzh-design`、`skills-security-check`、`frontend-design`、`lyric-video-pv`。详见 [`LINKS.md`](LINKS.md)。

## 使用

把需要的技能目录复制到本机的技能目录：

```bash
# macOS / Linux
cp -r research/idea-evaluator ~/.workbuddy/skills/

# Windows（PowerShell）
Copy-Item -Recurse research\idea-evaluator $env:USERPROFILE\.workbuddy\skills\
```

要求：目录根部含 `SKILL.md`，YAML frontmatter 至少包含 `name` 与 `description`。该格式适用于 WorkBuddy、Claude Skills 等支持 Skills 规范的工具。

## 添加新技能

1. 复制对应类别的模板：`cp -r _template/<category> <category>/<skill-name>`（科研模板自带 `scripts/audit_claims.py` 证据链审计脚本）；
2. 改 `SKILL.md` 的 `name`（与目录名一致）、`display_name`、`description`，替换全部 `TODO`；完整规范见 [`CONTRIBUTING.md`](CONTRIBUTING.md)（四类合格线见第三节）；
3. 校验：frontmatter 可解析，`name` 与目录名一致，且能完成一次最小调用；
4. **确认许可与署名**：
   - 只有 **MIT / Apache-2.0 / CC BY 4.0** 等允许再分发的技能才内置；
   - CC BY-NC-SA、AGPL-3.0 与未声明许可的技能**不内置**，只登记到 [`LINKS.md`](LINKS.md)；
   - 内置的第三方技能在 [`THIRD_PARTY.md`](THIRD_PARTY.md) 登记来源与许可；
   - 含商标、付费模板、抓取图片等素材的，先确认能否再分发；
5. 提交信息使用规范前缀：

```text
feat: add <skill-name>
fix: <修正内容>
chore: <杂项>
```

## 许可

- 根目录 [MIT](LICENSE) **仅适用于未另行声明的内容**。
- 内置技能为 MIT 或 CC BY 4.0，逐目录许可见 [`THIRD_PARTY.md`](THIRD_PARTY.md)；CC BY 4.0 内容须保留署名。
- 未内置技能的许可与入口见 [`LINKS.md`](LINKS.md)。
- 第三方技能的商标与视觉识别归各自权利人所有。

## 说明

本仓库仅存放技能定义与配套脚本，不包含任何账号凭据、接口密钥或个人数据。
