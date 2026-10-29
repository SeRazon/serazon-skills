# AI 使用声明

2026-03-15 中国版权保护中心公告建立软件版权登记申请诚信制度并启用新版申请表；行业报道还提到 AI 使用声明、手写承诺等要求。**以最新官方申请表为准。** 这份 JSON 是内部记录和起草辅助，不能替代官方表单、手写承诺或真实说明。

## JSON 模板

```json
{
  "schema": 1,
  "used_ai_for_code": "no",
  "used_ai_for_docs": "partial",
  "tools": ["ChatGPT"],
  "human_review": "手册由作者根据真实界面逐段改写并核对，截图来自实际运行系统。",
  "code_declaration": "代码由开发团队编写，未使用 AI 生成或改写。",
  "docs_declaration": "用户手册在 AI 辅助下起草，经作者逐段改写并与真实界面核对。",
  "declaration": "代码由开发团队编写；用户手册在 AI 辅助下起草，经作者逐段改写并与真实界面核对。",
  "date": "2026-10-29"
}
```

## 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `schema` | 是 | 固定为 `1` |
| `used_ai_for_code` | 是 | `no` / `partial` / `yes`，指是否用 AI 生成或改写代码 |
| `used_ai_for_docs` | 是 | `no` / `partial` / `yes`，指是否用 AI 生成或改写文档 |
| `tools` | 条件 | 使用过 AI 时至少填 1 个工具名；未使用可为空数组 |
| `human_review` | 条件 | 使用过 AI 时说明人工设计、修改、测试、核对的范围 |
| `code_declaration` | 是 | 只描述代码的 AI 使用情况，避免和文档混在一句里 |
| `docs_declaration` | 是 | 只描述文档的 AI 使用情况 |
| `declaration` | 是 | 准备填入申请表的合并说明，应与上面两段一致 |
| `date` | 否 | 声明日期，`YYYY-MM-DD`，不得晚于今天 |

分开写 `code_declaration` 和 `docs_declaration`，是为了避免“代码未使用 AI，文档用了 AI”这类句子被误判，也方便 `check` 分别核对。

## 三种写法

**完全未使用 AI**

```json
{
  "schema": 1,
  "used_ai_for_code": "no",
  "used_ai_for_docs": "no",
  "tools": [],
  "human_review": "",
  "code_declaration": "代码由开发团队人工编写，未使用 AI 生成或改写。",
  "docs_declaration": "用户手册由作者根据真实界面人工编写，未使用 AI 生成或改写。",
  "declaration": "本软件代码与用户手册均由作者人工编写，未使用 AI 生成或改写。",
  "date": "2026-10-29"
}
```

**只辅助文档**

```json
{
  "schema": 1,
  "used_ai_for_code": "no",
  "used_ai_for_docs": "partial",
  "tools": ["ChatGPT"],
  "human_review": "手册由作者根据真实界面逐段改写并核对；截图来自实际运行系统。",
  "code_declaration": "代码由开发团队人工编写，未使用 AI 生成或改写。",
  "docs_declaration": "用户手册在 AI 辅助下起草，经作者逐段改写并与真实界面核对。",
  "declaration": "代码由开发团队编写；用户手册在 AI 辅助下起草，经作者逐段改写并与真实界面核对。",
  "date": "2026-10-29"
}
```

**辅助代码**

```json
{
  "schema": 1,
  "used_ai_for_code": "partial",
  "used_ai_for_docs": "no",
  "tools": ["GitHub Copilot"],
  "human_review": "AI 仅用于局部函数草稿；架构设计、关键逻辑、修改、测试和集成由作者完成。",
  "code_declaration": "代码部分模块使用 AI 辅助生成草稿，作者完成设计、修改、测试与集成。",
  "docs_declaration": "用户手册由作者人工编写，未使用 AI 生成或改写。",
  "declaration": "代码部分模块使用 AI 辅助生成草稿，作者完成设计、修改、测试与集成；用户手册由作者编写。",
  "date": "2026-10-29"
}
```

## check 会验证

- `used_ai_for_code` / `used_ai_for_docs` 只能是 `no` / `partial` / `yes`。
- `code_declaration`、`docs_declaration`、`declaration` 都不能为空；合并说明过短会警告。
- 使用过代码 AI 时：`code_declaration` 必须提到 AI；`yes` 时不能声称“未使用 AI 编写代码”，`partial` 时出现否定表述会给警告，请确认是否特指“生成/改写”；文档同理。
- 使用过 AI 时：`tools` 非空、`human_review` 非空。
- 未使用某项 AI 时：对应 declaration 应明确写“未使用 / 人工 / 自行”。
- 声明日期合法且不晚于今天。
- 与 `application-info.json` 的 `ai_usage` 做文本一致性检查；表述不一致会警告。
- 只检查字段完整性和明显矛盾，**不能判断声明是否真实**。

## 规则

- 不要为了“好过审”写“未使用 AI”。使用过就如实写清场景、工具和人工贡献。
- 不要用本模板替代官方申请表或手写承诺；最终文本以官方页面为准。
- 如果代码或文档主要由 AI 生成，先回到真实开发与人工改写；格式化工具不能把这类材料变成合规材料。
- `ai-usage.json` 是内部文件，不要随申请材料提交；保留它便于补正和内部审计。
