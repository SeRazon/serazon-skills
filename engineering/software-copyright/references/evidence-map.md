# 证据映射

证据映射是一张**内部审计表**，不随申请材料提交。它把“申请表里的功能描述”逐项落到真实代码、手册章节和真实截图上，专门对付最常见的驳回原因：**手册写了、代码里没有；申请表写了、手册没有；截图和功能对不上。**

## JSON 模板

```json
{
  "schema": 1,
  "software_name": "示例业务管理系统",
  "version": "V1.0",
  "features": [
    {
      "name": "用户管理",
      "code_paths": ["src/services/user_service.py", "src/api/user_routes.py"],
      "manual_section": "用户管理",
      "screenshots": ["screenshots/users.png"],
      "application_text": "用户管理支持新增、编辑、停用用户，并分配角色",
      "notes": "对应申请表 main_functions 第二段"
    }
  ]
}
```

## 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `schema` | 是 | 固定为 `1` |
| `software_name` | 否 | 填写后必须与申请表一致 |
| `version` | 否 | 填写后必须与申请表一致 |
| `features` | 是 | 至少 1 个功能；每个功能一条 |
| `features[].name` | 是 | 功能/模块名，不能重复 |
| `features[].code_paths` | 是 | 相对项目根目录的真实代码路径，至少 1 个；必须出现在 `scan` 的 `source_manifest.json` / `render` sidecar 的 `source_files` 中 |
| `features[].manual_section` | 是 | 用户手册中的标题文字（可用标题的一部分，如“用户管理”） |
| `features[].screenshots` | 是 | 相对 `evidence-map.json` 所在目录的真实截图路径，至少 1 张 |
| `features[].application_text` | 是 | 申请表 `main_functions` 或 `technical_features` 中的原句，必须逐字出现 |
| `features[].notes` | 否 | 备注，方便人工复核 |

## 怎么填

1. 先从 `application-info.json` 的 `main_functions` 里拆出 3–8 个主要功能；每个功能一条。
2. 在 `source_manifest.json` 的 `files` 里找到该功能对应的真实代码路径；不要填无关文件。
3. 在用户手册里找到对应章节标题，填到 `manual_section`。
4. 准备该功能的真实界面截图，放到 `screenshots/`，并确认手册里引用了它。
5. 从 `main_functions` / `technical_features` 复制一句能代表该功能的原话到 `application_text`。
6. 运行 `check --evidence`，按报错补齐。

## check 会验证

- 使用 `check --evidence` 时必须同时提供 `--info`、`--manual` 和 render 生成的 `.manifest.json`；代码路径校验读取 sidecar 的 `source_files`。
- 每个功能至少 1 个代码路径、1 张截图、1 个手册章节、1 句申请表原文。
- `code_paths` 必须在源程序清单 `source_files` 中；不在提交的 60 页源程序中时给警告。
- `manual_section` 必须出现在用户手册标题中。
- 截图文件必须存在、非空，且为常见图片格式；截图文件名应出现在用户手册中。
- `application_text` 必须逐字出现在 `main_functions` 或 `technical_features` 中。
- 证据映射里的名称/版本若填写，必须与申请表一致。
- 功能描述超过 500 字但只映射 1 个功能时给警告，提示继续拆分。

## 规则

- 截图必须是真实运行界面；不要用示意图、AI 图、模板图或占位图。
- 代码路径必须是本软件的真实代码；不要指向依赖、构建产物、测试或第三方代码。
- 一个功能可以对应多个代码路径和多张截图；不要为了凑数重复填同一个文件。
- 证据映射是内部文件，不要随申请材料提交；但建议保留，补正时能快速定位。
- 如果某个功能是纯后端接口，可以用接口调试界面、管理后台或日志截图作为证据，但必须真实。
