# 新增技能说明

## 目录结构

```text
<category>/<skill-name>/
├── SKILL.md          # 必需：YAML frontmatter（name、description）+ 正文
├── references/       # 可选：规范、模板、示例
├── scripts/          # 可选：辅助脚本
└── assets/           # 可选：图片等静态资源
```

## 约定

1. `SKILL.md` 的 `name` 与目录名一致，使用小写字母与连字符；
2. `description` 写清"做什么 + 何时用 + 触发词"，控制在 2–3 句；
3. 脚本不要硬编码个人路径与凭据；示例数据使用虚构占位；
4. 单个技能体积尽量小于 5 MB，大资源改用外链或单独发布；
5. 提交信息：`feat: add <skill-name>`。

## 校验

- frontmatter 能正常解析（`---` 包裹，键值完整）；
- 在目标助手中能被识别并完成一次最小调用。
