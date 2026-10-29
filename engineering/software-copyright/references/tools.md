# 现有工具与取舍

调研时间：2026-10-29。许可与功能以各项目当前页面为准，使用前重新核实。

| 工具 | 许可 | 形态 | 适合 | 注意 |
|---|---|---|---|---|
| [fanbuz/codesucker](https://github.com/fanbuz/codesucker) | Apache-2.0 | 本地桌面 GUI | 拖入项目，生成 60 页源程序文档；离线抽取、注释清洗、自动排版 | 代码不出本机；与 DOCX/PDF 的最终格式仍需人工核对 |
| [Fokkyp/SoftwareCopyright-Skill](https://github.com/Fokkyp/SoftwareCopyright-Skill) | AGPL-3.0 | Agent Skill | 读本地项目，生成 .docx 申请表信息、操作手册、代码材料 | AGPL 有传染性，本仓库**不内置**，只外链 |
| [na57/chinese-copyright-application-skill](https://github.com/na57/chinese-copyright-application-skill) | 未声明 | Agent Skill | 申请表、源代码、用户手册、设计说明书 | 无明确再分发许可，本仓库**不内置**，只外链 |
| [okooo5km/Skills4U](https://github.com/okooo5km/Skills4U) 的 `chinese-copyright-application` | MIT | Agent Skill | Markdown 申请表 + LaTeX 编译源程序/手册/设计说明书 PDF | 需要 LaTeX 环境；生成后仍需核对页眉页码 |
| [peterfei/ai-agent-team](https://github.com/peterfei/ai-agent-team) 的 SoftCopyright Skill | MIT | Agent Skill | 项目分析、说明书、60 页源代码文档 | 仓库包含多个 agent，按需取用 |
| [软著Pro](https://ruanzhu.pro/) | 商业 | 在线 SaaS | 填信息后生成申请表、说明书、源代码 | 源码需上传，先确认保密与数据留存条款 |
| [爱软著](https://www.aigc.cn/100538.html) | 商业 | 在线 SaaS | 信息校验、材料生成 | 同上；不要把未公开源码直接上传 |

## 本 skill 的定位

- 本地、只读、可审计：源码不上传；先生成清单供人复核，再生成文档。
- 不追求"一键生成假材料"：只整理真实项目代码，不补写、不伪造。
- 生成 HTML 而不是直接 DOCX/PDF：分页稳定、可用浏览器打印；如需 DOCX，转换后必须重新核对页数和行数。
- 自带 `check`：校验页数、每页行数、页眉页码、名称/版本一致性、申请表字段、手册占位内容。

## 选择建议

- 想要图形界面、快速出源程序文档：可先试 CodeSucker。
- 已经在用 Claude/Codex 类 Agent，想要全流程 DOCX：可参考 Fokkyp 或 na57 的 Skill，但先确认许可与数据安全。
- 想要 LaTeX/PDF 流程：看 okooo5km 的 `chinese-copyright-application`。
- 想在本仓库内保持 MIT、本地、可脚本化、可自检：用本 skill。

本仓库不复制上述项目的代码或文档；只登记入口和许可信息。
