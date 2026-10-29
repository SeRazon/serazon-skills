---
name: skill-name
display_name: 研究类技能名
description: 解决哪个研究环节的什么问题；触发词：选题、文献、写作、投稿。
author: 星鸿SeRazon
license: MIT
---

# 标题

## 何时使用

- 选题阶段：TODO
- 写作阶段：TODO
- 投稿 / 审稿回应：TODO

## 输入

- 研究问题（一句话）
- 已有材料：数据、笔记、初稿、文献清单
- 目标：期刊档次 / 学校要求 / 篇幅

## 工作流

1. 确认输入是否齐全，缺项直接问，不猜。
2. TODO：第一步做什么。
3. TODO：产出中间物（提纲 / `claims.csv` / `sources.json` / 对照表）。
4. 交付前运行 `scripts/audit_claims.py`：先修 error，再复核 warning。

## 证据规则

- 每条事实性断言绑定一个来源编号，登记在 `references/evidence-table.md`。
- 文献须可核验（DOI / 数据库链接 / 完整出版信息）；三无文献不得引用。
- 查不到就写"未查到"，不得用"看起来像真的"凑数。
- 区分事实、他人观点与作者判断；相关性不得写成因果。
- 多个来源用 `;` 分隔（如 `S001;S002`）；`观点` 类断言的 `status` 用 `作者观点`。

## 脚本

`scripts/audit_claims.py` 对证据表与正文做只读硬审计，不修改文件（Python 3.8+，仅标准库）。先解析 `SKILL_DIR` 为 `SKILL.md` 所在目录，再在项目目录运行：

```bash
# SKILL_DIR = 本 SKILL.md 所在目录
python "<SKILL_DIR>/scripts/audit_claims.py" \
  --claims claims.csv \
  --sources sources.json \
  manuscript.md
```

- 正文里的每个 `C###` 必须在 `claims.csv` 中，每个 `S###` 必须在 `sources.json` 中。
- `未查到` / `待核实` 的断言出现在事实段即报错；默认把除「待核实 / 待核验 / 未核实 / 未核验 / 待办 / 附录 / 参考文献 / 致谢」之外的章节都视为事实段。
- `--allow-unverified-in REGEX` 可追加允许章节（如 `讨论|局限`）；`--strict` 把警告也视为失败；`--json` 输出机器可读报告。
- 退出码：`0` 通过，`1` 有审计错误，`2` 输入或参数错误。

## 输出

- 形态：TODO（提纲 / 逐段对照 / 审查报告）
- 结构：TODO
- 必备：来源标注、待核实清单

## 边界

- 不代写、不编造数据与文献、不承诺发表。
- 不替代作者的判断：结论与研究设计由用户拍板。
