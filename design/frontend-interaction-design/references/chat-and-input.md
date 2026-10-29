# 聊天与输入场景

## Skill 1 · 打中文不误发

- 检测输入法选字状态：`event.isComposing` 或 `keyCode === 229`，候选框开着时回车只用于选字，**不发送**。
- Safari 在选字结束后可能"补"一次回车：选字结束（`compositionend`）后 **500ms 内的回车一并拦截**。
- 发送后清空输入框但保留焦点；`Shift + Enter` 换行，需在界面上可发现（占位符或快捷键提示）。

```js
let composing = false, lastCompositionEnd = 0;
input.addEventListener('compositionstart', () => composing = true);
input.addEventListener('compositionend', () => { composing = false; lastCompositionEnd = Date.now(); });
input.addEventListener('keydown', e => {
  if (e.key !== 'Enter' || e.shiftKey) return;
  if (composing || e.keyCode === 229 || Date.now() - lastCompositionEnd < 500) return;
  e.preventDefault(); send();
});
```

## Skill 2 · 翻记录不被拽走

- 只有距底部 **< 40px**（约一行）才算"正在跟随"，此时才自动滚动到新消息。
- 用户一动滚轮 / 触摸 / 方向键，立即脱离跟随，**不与用户抢滚动**。
- 向上翻超过 **120px**（约三行）显示「跳至最新」按钮，并带未读条数。
- 键盘弹出、窗口 resize 时保持当前锚点，不强制回到底部。
- 消息超过 200 条启用虚拟列表；时间分隔与未读分隔线不参与吸底计算。

## Skill 3 · 边框只套一层

- 从最外层往里看，视线最多穿过**一层**框。
- 框内的按钮不画边，鼠标悬停才变底色。
- 描边用 `inset` 阴影实现，线画在格子内部，不往外撑；选中加粗时相邻元素纹丝不动。

```css
.cell { box-shadow: inset 0 0 0 1px var(--line); }
.cell[aria-selected="true"] { box-shadow: inset 0 0 0 2px var(--accent); }
```

- 高清屏细线：1px 在 2x 屏用 `0.5px` 实际值或 `transform: scale(.5)` 伪元素，避免"糊成 2px"。

## Skill 4 · 圆角内外同心

- 外圆角 = 内圆角 + 内边距，像操场跑道：外圈弯得更大，差值正好是中间那条缝。
- 用变量表达，缩放时仍严丝合缝：

```css
.card { --pad: 8px; --r-inner: 8px; border-radius: calc(var(--r-inner) + var(--pad)); padding: var(--pad); }
.card > .inner { border-radius: var(--r-inner); }
```

- 嵌套超过两层时，最内层用 `border-radius: min(var(--r-inner), 50%)` 防止小尺寸失真。

## Skill 5 · 分屏防翻车

- 拖动分隔条时，给右侧预览盖一层透明玻璃（`pointer-events: none` 的覆盖层），鼠标划过不卡住 iframe。
- `Esc` 弹回拖拽前位置。
- 双击分隔条回到 50 / 50。
- 拖过 **82%** 自动收起右栏，把空间让给主区，并在顶部给"恢复分屏"入口。

## 附加规范

- 输入框高度自适应：随内容增长，最多 8 行后内部滚动。
- 支持粘贴图片与拖拽上传，需有明确的落点提示与取消方式。
- 长按/右键菜单里保留"复制""引用"，不要自造一套无法复制的选择逻辑。
- 所有图标按钮必须有 `aria-label`，并提供 tooltip 说明。
