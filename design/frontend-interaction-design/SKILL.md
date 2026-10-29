---
name: frontend-interaction-design
display_name: 前端交互与界面规范
description: 前端交互与界面设计规范：弹层选型与打扰分级、移动端手势组件、视觉工艺与设计令牌、聊天输入、表单控件、触控热区、无障碍与交付走查。用于写交互、选组件、评审界面、改细节。
author: 星鸿SeRazon
license: MIT
---

# 前端交互与界面规范

一套可直接执行的交互决策与视觉工艺规范。核心不是"好看"，而是**减少用户的思考成本与误操作**。

## 何时使用

- 要在 Tooltip / Toast / Alert / Popconfirm / Drawer / Modal / Bottom Sheet 之间做选择
- 移动端手势、安全区、触感反馈
- 视觉细节：描边、圆角、字重、数字对齐、动效参数
- 表单控件选型（Select 还是 Dropdown）与校验
- 组件评审、交互走查、交付前自检

## 五条原则

1. **打扰分级**：能悄悄说就不弹窗；能撤销就不确认；必须拦才用 Modal。
2. **状态先于常态**：默认 / 悬停 / 聚焦 / 禁用 / 加载 / 错误 / 空态 / 极限值，缺一不算完成。
3. **热区优先于视觉**：视觉 16px 可以，热区 ≥ 40×40，底线 28px。
4. **单层视觉**：视线只穿一层框；描边用 inset，选中加粗不撑布局。
5. **动效有性格**：拖拽咬死、点赞回弹、提示即走；时长落在 120 / 200 / 320ms 三档。

## 主题索引

| 主题 | 文件 | 关键内容 |
|---|---|---|
| 弹层选型 | [references/overlays.md](references/overlays.md) | 六档打扰分级、内容量判断、三条防坑铁律、焦点与层级 |
| 移动端组件 | [references/mobile-patterns.md](references/mobile-patterns.md) | Bottom Sheet / ActionSheet / Snackbar / AlertDialog / Tour / Lightbox / Inline Alert |
| 视觉工艺 | [references/visual-craft.md](references/visual-craft.md) | 微对比色阶、暗色字重、流式打字、数字对齐、动效性格、设计令牌 |
| 聊天与输入 | [references/chat-and-input.md](references/chat-and-input.md) | 中文输入法、滚动跟随、单层边框、同心圆角、分屏 |
| 表单控件 | [references/form-controls.md](references/form-controls.md) | Select 与 Dropdown 的边界、四条铁律、校验与错误态 |
| 触控热区 | [references/touch-targets.md](references/touch-targets.md) | 44–48px 热区、死区焊接、手势缓冲、Taptic |
| 无障碍与走查 | [references/accessibility-and-qa.md](references/accessibility-and-qa.md) | 对比度、焦点、键盘、ARIA、降级动效、20 条自检 |

## 弹层快速决策

```text
只需解释图标/术语            → Tooltip（不承载关键信息）
操作成功/失败的轻反馈        → Toast；需要"撤销" → Snackbar
全局提醒但不阻断             → Alert（顶部条）
高频二次确认、不离开现场     → Popconfirm
内容长 / 需对照列表 / 保留焦点 → Drawer（桌面）· Bottom Sheet（移动）
不可逆的关键决策             → Modal / AlertDialog
新功能引导                   → Tour
查看图片/视频                → Lightbox
表单字段校验                 → Inline Alert（不自动消失）
```

## 内容量判断

- **看长短**：内容少用弹窗（宽度 400 / 520 / 720 三档）；表单很长换抽屉或新页面。
- **看要不要对照**：列表里逐条点开用抽屉（焦点不丢）；彻底换流程（下单、付款）才跳新页面。

## 交付物

改动说明 + 组件状态矩阵 + 关键参数（动效、圆角、层级）+ 走查结论（问题 / 等级 / 建议）。参数若无设计稿，先取本技能默认值，再按产品品牌微调。

## 边界

- 平台规范以官方文档为准（Material Design、Apple HIG、Arco Design 等），本技能给决策逻辑与默认参数。
- 不编造品牌色值与字体授权信息；缺设计稿时用中性令牌起步，并标注"待品牌确认"。
- 不替代可用性测试：可访问性与交互假设需真机与真实用户验证。
