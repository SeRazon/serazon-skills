# 技能模板

四类技能各一份最小可用的起点，复制对应目录、改名即可。

```text
_template/
├── research/      # 科研：证据表 + 提纲 + 证据链审计
│   ├── SKILL.md
│   ├── references/evidence-table.md
│   └── scripts/audit_claims.py
├── design/        # 设计：状态矩阵 + 令牌 + 动效参数
│   ├── SKILL.md
│   └── references/state-matrix.md
├── engineering/   # 工程：审查维度 + 分级 + 复现
│   ├── SKILL.md
│   └── references/review-report.md
└── algorithm/     # 算法：适用条件 + 复杂度 + 边界 + 代码骨架
    ├── SKILL.md
    └── references/algorithm-entry.md
```

## 用法

```bash
# 1) 复制对应类别的模板
cp -r _template/design ../design/<your-skill-name>

# 2) 改 SKILL.md 的 name / display_name / description
#    name 必须与目录名一致

# 3) 按「TODO」提示逐项替换，删掉用不到的章节

# 4) 自检：见 CONTRIBUTING.md 第五节
```

## 选哪个

| 技能主要… | 用 |
|---|---|
| 处理文献、写作、审稿、投稿 | `research/` |
| 产出界面规范、交互决策、视觉参数 | `design/` |
| 审查代码、扫描风险、检查配置 | `engineering/` |
| 讲解算法、给模板、赛场流程 | `algorithm/` |

新增类别时，复制任一模板改写，并在 README 目录表中登记。

## 注意

- 模板中的 `TODO` 与示例数据必须全部替换；提交前搜一遍 `TODO`。
- research 模板自带 `scripts/audit_claims.py`，复制后即可对 `claims.csv` / `sources.json` / 正文做证据链审计。
- 第三方内容先过许可判定（`CONTRIBUTING.md` 第二节）：不能内置的只登记 `LINKS.md`。
- 模板本身不属于任何技能，不要在其中直接写具体业务内容。
