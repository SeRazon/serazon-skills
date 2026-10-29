# 申请表信息

申请表字段以中国版权保护中心最新在线表单为准。下面是一份可直接落成 `application-info.json` 的字段清单，`check` 会按它做一致性校验。

## JSON 模板

```json
{
  "software_name": "示例业务管理系统",
  "short_name": "示例系统",
  "version": "V1.0",
  "classification_code": "",
  "completion_date": "2026-08-01",
  "publication_status": "未发表",
  "first_publication_date": "",
  "first_publication_place": "",
  "copyright_owner": "示例科技有限公司",
  "development_method": "独立开发",
  "rights_scope": "全部权利",
  "hardware_env": "x86_64 服务器，8GB 内存，100GB 磁盘",
  "software_env": "Ubuntu 24.04，Python 3.11，Node.js 20，MySQL 8",
  "languages": "Python、JavaScript、CSS",
  "source_lines": 3703,
  "purpose": "用于企业内部数据管理与查询统计",
  "domain": "企业内部管理",
  "main_functions": "按真实功能填写，建议 500–1300 字，覆盖主要模块、业务流程和用户角色。",
  "technical_features": "按真实架构填写，例如前后端分离、权限模型、审计日志、数据校验等。",
  "ai_usage": "未使用 AI 生成代码或文档；代码与文档由开发团队编写。"
}
```

## 字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| `software_name` | 是 | 软件全称，与申请表、源程序页眉、用户手册一致 |
| `short_name` | 否 | 简称；申请表有则填，没有留空 |
| `version` | 是 | 如 `V1.0` 或 `1.0`；有无 `V` 以申请表为准 |
| `classification_code` | 否 | 申请表要求时填写 |
| `completion_date` | 是 | 开发完成日期，`YYYY-MM-DD`，不得晚于今天 |
| `publication_status` | 是 | `已发表` / `未发表` |
| `first_publication_date` | 条件 | 已发表必填，`YYYY-MM-DD`，不得早于完成日期、不得晚于今天 |
| `first_publication_place` | 条件 | 已发表必填 |
| `copyright_owner` | 是 | 著作权人，与身份证明文件一致 |
| `development_method` | 是 | `独立开发` / `合作开发` / `委托开发` / `下达任务开发` |
| `rights_scope` | 是 | `全部权利` / `部分权利` |
| `hardware_env` | 是 | 开发与运行的硬件环境 |
| `software_env` | 是 | 操作系统、支持软件及版本 |
| `languages` | 是 | 全部编程语言 |
| `source_lines` | 是 | 源程序总量，建议与 `scan` 的 `totals.raw_lines` 对齐 |
| `purpose` | 是 | 开发目的 |
| `domain` | 是 | 面向领域 |
| `main_functions` | 是 | 主要功能；2026 年新规常见要求 500–1300 字，以最新表单为准 |
| `technical_features` | 是 | 技术特点 |
| `ai_usage` | 建议 | AI 使用情况；如使用过 AI 辅助，必须如实说明场景与人工贡献 |

## 一致性规则

- 软件名称、版本号在申请表、源程序页眉、用户手册页眉中必须完全一致。
- `source_lines` 与源程序清单的总行数差异超过 10% 时，`check` 会警告；请统一口径（含空行或不含空行）。
- 已发表软件的首次发表日期不得早于开发完成日期。
- 著作权人、开发方式、权利范围必须与身份证明、合同或任务书一致。
- 使用 AI 辅助写代码或文档时，按最新申请表要求如实声明；不要填写与事实不符的"未使用 AI"。

## 与证据映射、AI 声明的关系

- `main_functions` 应按功能拆成 [`evidence-map.md`](evidence-map.md) 里的 `features`；每个功能都要能落到真实代码路径、手册章节、真实截图和 `main_functions` / `technical_features` 原句。
- `ai_usage` 必须与 [`ai-usage.md`](ai-usage.md) 的 `declaration` 一致；`check` 会做关键词级冲突检查，但最终真实性由申请人负责。
- `source_lines` 建议与 `scan` 的 `totals.raw_lines` 对齐；如果按非空行统计，确保与提交材料口径一致。

## 官方依据

- 中国版权保护中心“所需文件”：<https://www.ccopyright.com.cn/index.php?optionid=1080>
- 中国版权保护中心“填表说明”：<https://www.ccopyright.com.cn/index.php?optionid=1081>
- 2026-03-15《共同维护计算机软件版权登记良好生态》：<https://www.ccopyright.com.cn/index.php?auto_id=1524&method=view&optionid=999>
- 《计算机软件著作权登记办法》第十条：鉴别材料由源程序和任何一种文档前、后各连续 30 页组成；不足 60 页全部提交；程序每页不少于 50 行，文档每页不少于 30 行。
