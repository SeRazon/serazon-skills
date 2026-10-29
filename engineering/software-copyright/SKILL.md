---
name: software-copyright
display_name: 软著申请材料
description: 从真实项目准备中国软件著作权登记材料：扫描并筛选源码、生成前后各30页/每页50行的源程序文档、整理申请表字段、起草用户手册骨架、建立功能证据映射、记录 AI 使用声明并做材料自检。用于软著、软件著作权、著作权登记、源代码文档、用户手册、申请表、证据映射。只整理真实代码与真实信息，不编造材料、不承诺过审。
author: 星鸿SeRazon
license: MIT
---

# 软著申请材料

面向中国计算机软件著作权登记（CPCC）的材料准备。把分页、筛选、格式和一致性检查交给脚本，把真实性判断留给人。

## 真实性门禁

动手前先确认，答不上来就停下来补事实，不要生成材料：

1. 代码是否由申请人/团队真实开发？是否使用 AI 生成或改写？用了哪些工具、人工改了多少？
2. 用户手册里的功能、截图是否来自真实运行的软件？
3. 开发完成日期、发表状态、著作权归属、开发方式是否有证据？
4. 每个主要功能能否同时找到代码路径、手册章节、真实截图和申请表原句？

四项都能对上，才进入下面的工作流。AI 可以用来排版、检查和起草初稿，但初稿必须由人核对/改写，不能替代真实代码、真实界面和真实声明。

## 何时使用

- 已有真实项目，要准备软著申请材料。
- 需要把源码整理成前后各 30 页、每页 50 行的源程序文档。
- 需要整理申请表字段、用户手册结构，或做提交前自检。
- 需要判断现有材料是否会出现名称/版本不一致、页眉页码缺失、行数不足等常见问题。

## 何时不使用

- 没有真实项目或真实代码，想生成"看起来像"的代码、文档或截图。
- 想伪造开发完成日期、发表状态、著作权归属、开发方式或 AI 使用情况。
- 想规避查重、绕过审查、批量代写虚假软件或买卖材料。

遇到以上情况直接拒绝，并说明：软著登记实行诚信制度，虚假材料可能导致不予登记、失信惩戒等后果。

## 输入

开始前逐项确认，缺项直接问，不猜：

- 项目路径（真实源码目录）。
- 软件全称、简称（如有）、版本号（如 `V1.0`）。
- 著作权人、开发方式、权利范围。
- 开发完成日期、是否已发表、首次发表日期与地点。
- 硬件环境、软件环境、编程语言、源程序量。
- 主要功能、技术特点、面向领域、开发目的。
- 每个主要功能对应的真实代码路径、手册章节和真实界面截图（用于证据映射）。
- 是否使用过 AI 辅助：用于代码还是文档、工具、人工修改范围（按最新申请表如实声明）。

字段说明见 [`references/application-info.md`](references/application-info.md)，证据映射见 [`references/evidence-map.md`](references/evidence-map.md)，AI 声明见 [`references/ai-usage.md`](references/ai-usage.md)。

## 工作流

1. **事实确认**：按上面的输入清单逐项确认；不要从代码猜著作权人、日期或发表状态。
2. **扫描源码**：运行 `scan`，得到 `source_manifest.json` 和 `source_stats.md`。
3. **人工复核清单**：确认纳入/排除的文件；剔除第三方代码、构建产物、测试、密钥和与本软件无关的模块。清单是后续所有材料的唯一代码范围。
4. **生成源程序文档**：运行 `render` 生成 HTML；用 Chrome/Edge 打印为 PDF（A4、边距 None、缩放 100%）。
5. **填写申请表信息**：按 `references/application-info.md` 生成 `application-info.json`，所有字段来自用户确认和项目事实。
6. **写用户手册**：按 `references/manual-outline.md` 组织；只用真实功能和真实截图，没有截图就列入待补清单，不生成假图。
7. **建立证据映射**：按 `references/evidence-map.md` 生成 `evidence-map.json`，每个功能至少对应 1 个代码路径、1 个手册章节、1 张真实截图、1 句申请表原文；缺一项就补，补不了就删掉该功能描述。
8. **记录 AI 使用**：按 `references/ai-usage.md` 生成 `ai-usage.json`，如实填写代码/文档是否使用 AI、工具和人工修改范围；不写与事实不符的“未使用”。
9. **自检**：运行 `check --evidence --ai-usage`；先修 error，再复核 warning；再按 `references/compliance.md` 核对官方最新要求。
10. **交付**：材料清单 + 证据映射 + AI 声明 + 待补清单 + 官方提交入口；提醒用户提交前再次核对最新申请表和页眉版本号。

## 脚本

脚本只读取项目，不修改项目；只写 `--out` 指定的文件。Python 3.8+，仅标准库。先解析 `SKILL_DIR` 为 `SKILL.md` 所在目录，再在项目目录运行：

```bash
# 1) 扫描：生成源码清单和统计
python "<SKILL_DIR>/scripts/software_copyright.py" scan \
  --project /path/to/project \
  --out materials

# 2) 生成源程序 HTML：名称/版本必须与申请表一致
python "<SKILL_DIR>/scripts/software_copyright.py" render \
  --manifest materials/source_manifest.json \
  --name "软件全称" --version "V1.0" \
  --out materials/源程序文档.html

# 3) 自检：源程序 + 申请表 + 用户手册 + 证据映射 + AI 声明
python "<SKILL_DIR>/scripts/software_copyright.py" check \
  --source-html materials/源程序文档.html \
  --info materials/application-info.json \
  --manual materials/用户手册.md \
  --evidence materials/evidence-map.json \
  --ai-usage materials/ai-usage.json \
  --report materials/自检报告.md
```

- `scan` 默认排除 `node_modules`、`dist`、`build`、`vendor`、测试、锁文件、密钥文件和压缩/生成文件；可用 `--include-tests`、`--include-ext` 调整。
- `render` 默认去掉空行、按半角 90 列硬换行，取前 30 页 + 后 30 页；源码不足 60 页时全部输出。长行换行只影响排版，不改代码内容。
- `render` 会生成同名 `.manifest.json`，记录页数、源码总量、全部源文件、前后页选择和每页文件，供 `check` 使用。
- `check --evidence` 逐项校验“功能 → 代码路径 → 手册章节 → 真实截图 → 申请表原句”；`check --ai-usage` 校验声明字段完整性和明显矛盾。
- `--manual` 支持 Markdown/HTML；DOCX/PDF 请先导出为文本，或保留 Markdown 源文件供校验。
- `--report` 生成 Markdown 自检报告，便于交付和补正时留档。
- `check` 退出码：`0` 通过，`1` 有材料错误，`2` 输入或参数错误；`--strict` 把警告也视为失败，`--json` 输出机器可读报告。

## 硬规则

- **真实代码**：只使用项目里实际存在的代码；不生成、不补写、不"优化"代码来凑页数。
- **真实文档**：用户手册只写真实功能，截图必须来自真实界面；不得用示意图、AI 图或占位图冒充。
- **真实信息**：名称、版本、日期、权属、发表状态、开发方式、AI 使用情况必须如实填写；不替用户编造。
- **证据闭环**：每个主要功能至少对应 1 个真实代码路径、1 个手册章节、1 张真实截图、1 句申请表原文；缺一项不算完备。
- **AI 声明**：`ai-usage.json` 如实记录代码/文档是否使用 AI、工具和人工修改范围；使用过就不写“未使用”。脚本只查完整性和明显矛盾，不判断声明真假。
- **不规避审查**：不提供查重规避、AI 痕迹清洗、虚假承诺或批量代写服务。
- **同名校验**：申请表、源程序页眉、用户手册页眉的名称与版本号必须一致；有无 `V` 以申请表为准。
- **源程序**：前 30 页 + 后 30 页；不足 60 页全部提交；每页不少于 50 行（结束页可少于 50 行）；页眉写软件名称与版本号，右上角连续页码。
- **文档**：前 30 页 + 后 30 页；不足 60 页全部提交；每页不少于 30 行（有图可少于 30 行）；页眉和页码要求同上。
- **不夹带**：不包含第三方源码、依赖、构建产物、密钥、个人信息或与本软件无关的模块。
- **官方优先**：本 skill 的规则是编写时的快照；提交前以中国版权保护中心最新的“所需文件 / 填表说明 / 申请表”为准。

## 输出

建议的材料目录：

```text
materials/
├── source_manifest.json      # scan 生成
├── source_stats.md           # scan 生成
├── 源程序文档.html           # render 生成
├── 源程序文档.manifest.json  # render 生成
├── 源程序文档.pdf            # 浏览器打印
├── application-info.json     # 申请表字段
├── evidence-map.json         # 功能→代码→手册→截图→申请表原句
├── ai-usage.json             # AI 使用声明（内部记录）
├── 用户手册.md / .docx / .pdf
├── screenshots/              # 真实界面截图
└── 自检报告.md               # check 输出摘要
```

交付时说明：哪些材料已生成、哪些字段待用户确认、哪些内容仍是占位/待补。

`source_manifest.json`、`source_stats.md`、`evidence-map.json`、`ai-usage.json` 是内部工作文件，含本地路径、哈希或内部说明，不要随申请材料提交。

## 参考文件

- [`references/application-info.md`](references/application-info.md)：申请表字段、JSON 模板与一致性规则。
- [`references/evidence-map.md`](references/evidence-map.md)：功能→代码→手册→截图→申请表原句的证据映射。
- [`references/ai-usage.md`](references/ai-usage.md)：AI 使用声明模板、真实写法与检查规则。
- [`references/source-document.md`](references/source-document.md)：源程序页数/行数、打印、选码与常见驳回点。
- [`references/manual-outline.md`](references/manual-outline.md)：用户手册结构、截图清单与排版建议。
- [`references/compliance.md`](references/compliance.md)：官方依据、2026 年政策变化、红线与提交前核对。
- [`references/tools.md`](references/tools.md)：现有软著工具、许可与取舍。

## 边界

- 不提供法律意见，不保证受理或过审，不代用户提交。
- 不生成虚假代码、虚假文档、虚假截图，不伪造日期、权属、发表状态或 AI 使用情况。
- 官方要求、申请表字段和审查口径可能变化；本 skill 不替代中国版权保护中心的正式说明。
