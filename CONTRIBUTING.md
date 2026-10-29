# 贡献指南

本仓库收集星鸿在科研、设计、工程与算法场景中使用的 Skills。提交前请对照本指南。

## 目录约定

```text
<category>/<skill-name>/
├── SKILL.md          # 必需
├── references/       # 可选：规范、清单、示例
├── scripts/          # 可选：可执行脚本
└── assets/           # 可选：图片等静态资源
```

- 类别目录：`research/` `design/` `engineering/` `algorithm/`；新增类别需在 README 目录表中登记。
- 技能目录名使用**小写字母与连字符**，与 `SKILL.md` 的 `name` 完全一致。
- 单个技能体积尽量 < 5 MB；大资源用外链或单独发布。

## SKILL.md 规范

```markdown
---
name: skill-name
display_name: 中文名
description: 一句话说明做什么、何时使用（含触发词）。
author: 你的署名
license: MIT
---

# 标题

## 何时使用
## 核心规则 / 流程
## 交付物
## 边界（不做什么、不确定时怎么办）
```

- `name`：必填，与目录名一致。
- `description`：2–3 句，写清"做什么 + 何时用 + 触发词"；不要写成宣传语。
- 正文用**可执行**的规则与参数，少讲概念；能用表格就不用长段落。
- 不确定的内容标注「待核实」，不得编造数据、链接与结论。

## 许可与署名（必查）

1. **先找许可证**：目录内 `LICENSE` → `SKILL.md` 的 `license` 字段 → 上游仓库 `homepage` 的 LICENSE。
2. **无许可证不得入库**：仅有"仅供学习交流"或无 LICENSE 文件的，不收录内容，只登记到 [`LINKS.md`](LINKS.md)。
3. **署名**：内置的第三方技能必须在 [`THIRD_PARTY.md`](THIRD_PARTY.md) 登记来源、许可证与备注。
4. **传染性许可不入库**：CC BY-SA / CC BY-NC-SA / AGPL 一律不内置（会带来 SA / AGPL 义务），只在 [`LINKS.md`](LINKS.md) 保留获取入口，不得改标 MIT。
5. **素材**：商标、Logo、付费模板、抓取的图片，先确认能否再分发，否则不入库。
6. **敏感信息**：不得包含 token、Cookie、接口密钥、手机号、邮箱等个人数据。

## 提交规范

```text
feat: add <skill-name>       新增技能
fix: <修正内容>              修复错误
chore: <杂项>                文档、脚本、配置
```

- 一次提交只做一件事；提交信息简短，不写冗长说明。
- 中文与英文均可，保持同一提交内语言一致。

## 提交前自检

- [ ] `SKILL.md` frontmatter 可解析，`name` 与目录名一致
- [ ] 描述里写清了触发场景
- [ ] 参考文件能被正文正确链接（相对路径）
- [ ] 脚本无硬编码绝对路径与个人凭据
- [ ] 已在 `THIRD_PARTY.md` 登记（若为第三方）
- [ ] README 的数量与目录表已同步

## 发布流程

```bash
git add <改动>
git commit -m "feat: add <skill-name>"
git push origin main
```

推送需能访问 `github.com:443`；若直连失败，可用本地代理：

```bash
git -c http.proxy=http://127.0.0.1:7897 push origin main
```
