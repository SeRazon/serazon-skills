# 公众号排版组件库 —— 清爽蓝（Fresh Blue）

> **使用说明**：本组件库为「清爽蓝」主题，所有组件使用**内联样式**，可直接复制粘贴到微信公众号编辑器。
>
> **设计风格**：通透蓝白调 —— 大面积留白 + 浅蓝衬底卡片（`#EAF4FF`）+ 1px 淡蓝描边（`#DCE9F7`）+ 中等圆角（12px）+ 极低饱和柔阴影。章节用「编号栏目条」，数据用「指标卡」，流程用「竖线时间线」。整体气质：干净、清爽、年轻、不抢内容。
>
> **主题结构模型**：图文叙事为主 + 轻量信息卡为辅；中低信息密度；弱分隔（靠留白与淡蓝细线）；标题体系采**栏目条式**（编号方块 + 中文标题 + 英文小标签）；媒体表达采**圆角白卡 + 居中自适应图 + 浅灰说明**；数据表达采**数字指标卡**；流程表达采**竖线时间线**；结尾采**渐变 CTA 卡 + 签名条**。
>
> **公众号平台限制须知**：
> - ❌ 不支持 `<style>` 标签、`<script>` 标签、CSS class / id
> - ❌ 不支持 `position: fixed/absolute`、`float`、`display: grid`
> - ❌ 不支持 `@media`、`@keyframes`、CSS 变量
> - ✅ 支持内联 `style`、`display: flex`（有限）、`linear-gradient`、`border-radius`、`box-shadow`
> - ✅ 支持 `<section>`、`<p>`、`<span>`、`<strong>`、`<img>`、`<table>`（真实表格语义）

---

## 设计变量速查表

```
主色（清爽蓝）：      #1E88E5（强调、标签底、竖条、数字）
深蓝（标题/深字）：    #12558F（章节标题、卡片标题、金句）
锚点深蓝：            #0B63C4（主色加粗、深底白字锚点）
正文色：              #3B4A5A
辅助文字色：          #8A99A8（说明、署名、页脚）
浅底（卡片/引用）：    #EAF4FF
浅标（标签底/序号底）：#D6EBFF
描边色：              #DCE9F7
分隔线色：            #E4EEF9
背景色：              #FFFFFF
下划线标记色：        #9CCBFA（正文关键词，2px 实线）
荧光笔色：            #CFE8FF（底部半高亮）
高亮渐变：            linear-gradient(180deg,rgba(255,255,255,0) 60%,#CFE8FF 60%)
封面/CTA 渐变：       linear-gradient(135deg,#EAF4FF 0%,#FFFFFF 100%)
正文字号：            15px
行高：                1.85
段落间距：            22px
章节上下留白：        38px
内容区左右边距：      18px
圆角：                卡片 12px / 封面 16px / 标签 8px / 药丸 999px
阴影：                0 2px 10px rgba(30,136,229,0.08)
字体：                -apple-system, BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif
```

---

## 组件 1 全局容器

```html
<section style="max-width:677px;margin:0 auto;background:#FFFFFF;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#3B4A5A;line-height:1.85;font-size:15px;overflow-x:hidden;">

  <!-- 所有组件放在这里 -->

</section>
```

---

## 组件 2 封面主卡（渐变浅蓝 + 标签 + 主副标题 + 元信息）

```html
<section style="margin:0 18px 28px;padding:30px 24px 26px;border-radius:16px;background:linear-gradient(135deg,#EAF4FF 0%,#FFFFFF 100%);border:1px solid #DCE9F7;box-shadow:0 2px 10px rgba(30,136,229,0.08);">
  <p style="margin:0 0 12px;"><span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;letter-spacing:1px;"><span leaf="">栏目标签占位</span></span></p>
  <p style="margin:0 0 10px;font-size:22px;font-weight:800;color:#12558F;line-height:1.45;"><span leaf="">主标题占位</span></p>
  <p style="margin:0 0 18px;font-size:14px;color:#5A6B7C;line-height:1.7;"><span leaf="">副标题或一句话导语占位</span></p>
  <section style="height:1px;background:#DCE9F7;margin:0 0 14px;"><span leaf=""><br></span></section>
  <p style="margin:0;font-size:12px;color:#8A99A8;letter-spacing:0.5px;"><span leaf="">日期占位 · 作者占位 · 阅读时长占位</span></p>
</section>
```

---

## 组件 3 简版刊头（左竖条刊头，无渐变）

```html
<section style="margin:0 18px 26px;padding:0 0 0 14px;border-left:4px solid #1E88E5;">
  <p style="margin:0 0 6px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">COLUMN 栏目名占位</span></p>
  <p style="margin:0 0 8px;font-size:21px;font-weight:800;color:#12558F;line-height:1.45;"><span leaf="">刊头主标题占位</span></p>
  <p style="margin:0;font-size:14px;color:#5A6B7C;line-height:1.7;"><span leaf="">刊头副标题占位，一句话说明本文主题。</span></p>
</section>
```

---

## 组件 4 元信息条（作者 / 日期 / 字数 / 标签）

```html
<section style="margin:0 18px 26px;padding:12px 16px;border-radius:10px;background:#F7FBFF;border:1px solid #E4EEF9;">
  <p style="margin:0;font-size:12px;color:#8A99A8;letter-spacing:0.5px;line-height:1.8;">
    <span style="color:#12558F;font-weight:700;"><span leaf="">作者</span></span><span leaf="">　占位作者名</span>
    <span leaf="">｜</span>
    <span style="color:#12558F;font-weight:700;"><span leaf="">日期</span></span><span leaf="">　占位日期</span>
    <span leaf="">｜</span>
    <span style="color:#12558F;font-weight:700;"><span leaf="">字数</span></span><span leaf="">　占位字数</span>
  </p>
</section>
```

---

## 组件 5 目录卡（精选 3 条看点）

```html
<section style="margin:0 18px 26px;padding:20px 20px 8px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;box-shadow:0 2px 10px rgba(30,136,229,0.08);">
  <p style="margin:0 0 14px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">CONTENTS　本文看点</span></p>
  <section style="display:flex;align-items:flex-start;margin-bottom:14px;">
    <span style="display:inline-block;background:#D6EBFF;color:#12558F;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;margin-right:10px;line-height:1.6;"><span leaf="">01</span></span>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.75;"><span leaf="">第一个看点要点占位</span></p>
  </section>
  <section style="display:flex;align-items:flex-start;margin-bottom:14px;">
    <span style="display:inline-block;background:#D6EBFF;color:#12558F;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;margin-right:10px;line-height:1.6;"><span leaf="">02</span></span>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.75;"><span leaf="">第二个看点要点占位</span></p>
  </section>
  <section style="display:flex;align-items:flex-start;margin-bottom:14px;">
    <span style="display:inline-block;background:#D6EBFF;color:#12558F;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;margin-right:10px;line-height:1.6;"><span leaf="">03</span></span>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.75;"><span leaf="">第三个看点要点占位</span></p>
  </section>
</section>
```

---

## 组件 6 行内导读条（一句话引导）

```html
<section style="margin:0 18px 24px;padding:14px 18px;border-radius:10px;background:#F7FBFF;border-left:3px solid #9CCBFA;">
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;">
    <span style="color:#0B63C4;font-weight:700;"><span leaf="">导读</span></span><span leaf="">　这里写一句话导读占位，告诉读者这篇能读到什么。</span>
  </p>
</section>
```

---

## 组件 7 开头引言卡（浅蓝底 + 大字金句 + 署名）

```html
<section style="margin:0 18px 30px;padding:26px 22px;border-radius:14px;background:#EAF4FF;border:1px solid #DCE9F7;">
  <p style="margin:0 0 14px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">LEAD　开篇</span></p>
  <p style="margin:0 0 16px;font-size:17px;font-weight:700;color:#12558F;line-height:1.85;">
    <span leaf="">这里放开篇金句占位，</span><span style="background:linear-gradient(180deg,rgba(255,255,255,0) 60%,#CFE8FF 60%);"><span leaf="">核心词用荧光笔标出</span></span><span leaf="">。</span>
  </p>
  <p style="margin:0;font-size:12px;color:#8A99A8;letter-spacing:1px;"><span leaf="">—— 作者名（按文章作者或主题而定）</span></p>
</section>
```

---

## 组件 8 素引言（左竖条，无底色）

```html
<section style="margin:0 18px 28px;padding:4px 0 4px 16px;border-left:3px solid #9CCBFA;">
  <p style="margin:0;font-size:16px;color:#5A6B7C;line-height:1.85;"><span leaf="">这里是素引言占位，适合放在章节开头做一段过渡性铺垫。</span></p>
</section>
```

---

## 组件 9 编号章节标题（栏目条式：编号方块 + 中文 + 英文标签）

```html
<section style="margin:38px 18px 18px;">
  <p style="margin:0 0 6px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">CHAPTER 01　英文标签占位</span></p>
  <section style="display:flex;align-items:center;">
    <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:13px;font-weight:800;padding:3px 10px;border-radius:8px;margin-right:10px;line-height:1.6;letter-spacing:1px;"><span leaf="">01</span></span>
    <p style="margin:0;font-size:19px;font-weight:800;color:#12558F;line-height:1.5;"><span leaf="">章节标题占位</span></p>
  </section>
  <section style="height:2px;background:#DCE9F7;margin:14px 0 0;border-radius:2px;"><span leaf=""><br></span></section>
</section>
```

> 结语类末章可把编号 `01` 换成 `∞`，英文标签换成 `ENDING　收束`。

---

## 组件 10 无编号章节标题

```html
<section style="margin:38px 18px 16px;">
  <p style="margin:0 0 6px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">SECTION　小节英文标签占位</span></p>
  <p style="margin:0;font-size:19px;font-weight:800;color:#12558F;line-height:1.5;"><span leaf="">无编号章节标题占位</span></p>
  <section style="height:2px;background:#DCE9F7;margin:12px 0 0;border-radius:2px;"><span leaf=""><br></span></section>
</section>
```

---

## 组件 11 小节标题条（浅蓝底条）

```html
<section style="margin:28px 18px 14px;padding:9px 14px;border-radius:8px;background:#F2F8FF;border-left:3px solid #1E88E5;">
  <p style="margin:0;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">小节标题条占位</span></p>
</section>
```

---

## 组件 12 药丸标签小标题

```html
<p style="margin:26px 18px 12px;">
  <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:14px;font-weight:700;padding:5px 16px;border-radius:999px;"><span leaf="">药丸标签占位</span></span>
</p>
```

---

## 组件 13 左竖条小标题

```html
<p style="margin:26px 18px 12px;font-size:16px;font-weight:800;color:#12558F;line-height:1.5;border-left:4px solid #1E88E5;padding-left:12px;">
  <span leaf="">左竖条小标题占位</span>
</p>
```

---

## 组件 14 渐变分割线

```html
<section style="margin:30px 18px;">
  <section style="height:1px;background:linear-gradient(90deg,rgba(30,136,229,0) 0%,#9CCBFA 50%,rgba(30,136,229,0) 100%);"><span leaf=""><br></span></section>
</section>
```

---

## 组件 15 圆点分割线

```html
<section style="margin:30px 18px;text-align:center;">
  <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:#D6EBFF;margin:0 5px;font-size:0;line-height:0;overflow:hidden;">.</span>
  <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:#9CCBFA;margin:0 5px;font-size:0;line-height:0;overflow:hidden;">.</span>
  <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:#D6EBFF;margin:0 5px;font-size:0;line-height:0;overflow:hidden;">.</span>
</section>
```

---

## 组件 16 正文段落（含下划线标记示例）

```html
<p style="margin:0 18px 22px;font-size:15px;color:#3B4A5A;line-height:1.85;letter-spacing:0.3px;">
  <span leaf="">正文段落占位。关键词用</span><span style="border-bottom:2px solid #9CCBFA;font-weight:600;"><span leaf="">下划线标记</span></span><span leaf="">，次要信息保持普通字重，整段控制在三到五行之内最舒服。</span>
</p>
```

---

## 组件 17 首段大字（章节开篇）

```html
<p style="margin:0 18px 22px;font-size:16px;color:#3B4A5A;line-height:1.9;letter-spacing:0.3px;">
  <span leaf="">章节首段大字占位，用来把读者从上一节带进这一节，语气可以比正文稍松一点。</span>
</p>
```

---

## 组件 18 主色加粗锚点句（全文 ≤ 5 处）

```html
<p style="margin:0 18px 22px;font-size:15px;line-height:1.85;">
  <span style="color:#0B63C4;font-weight:800;"><span leaf="">这里是全文最需要被记住的一句锚点占位。</span></span>
</p>
```

---

## 组件 19 行内标记集合（加粗 / 渐变高亮 / 下划线 / 荧光笔 / 行内代码）

```html
<p style="margin:0 18px 22px;font-size:15px;color:#3B4A5A;line-height:1.85;">
  <span style="color:#0B63C4;font-weight:700;"><span leaf="">主色加粗</span></span><span leaf="">、</span><span style="background:linear-gradient(180deg,rgba(255,255,255,0) 62%,#CFE8FF 62%);font-weight:600;"><span leaf="">荧光笔高亮</span></span><span leaf="">、</span><span style="border-bottom:2px solid #9CCBFA;font-weight:600;"><span leaf="">下划线标记</span></span><span leaf="">、</span><span style="background:#F1F5F9;color:#1E88E5;padding:1px 6px;border-radius:4px;font-family:Consolas,Monaco,monospace;font-size:13px;"><span leaf="">inline_code</span></span><span leaf="">。</span>
</p>
```

---

## 组件 20 引用块（浅蓝底 + 左竖条）

```html
<section style="margin:0 18px 24px;background:#EAF4FF;border-radius:0 12px 12px 0;border-left:4px solid #1E88E5;padding:16px 20px;">
  <p style="margin:0;font-size:15px;color:#12558F;line-height:1.85;">
    <span leaf="">引用内容占位：这里放别人的话、公告原文或需要被单独拎出来的段落。</span>
  </p>
</section>
```

---

## 组件 21 亮点卡（白底 + 顶部蓝条）

```html
<section style="margin:0 18px 24px;padding:18px 20px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;border-top:3px solid #1E88E5;box-shadow:0 2px 10px rgba(30,136,229,0.08);">
  <p style="margin:0 0 8px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:1.5px;"><span leaf="">HIGHLIGHT　亮点</span></p>
  <p style="margin:0 0 8px;font-size:16px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">亮点卡标题占位</span></p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">亮点卡说明占位，用两三行把这个亮点讲清楚即可。</span></p>
</section>
```

---

## 组件 22 信息提示卡

```html
<section style="margin:0 18px 24px;background:#F7FBFF;border-radius:0 10px 10px 0;border-left:4px solid #9CCBFA;padding:14px 18px;">
  <p style="margin:0 0 6px;">
    <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;"><span leaf="">提示</span></span>
  </p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">提示或旁注内容占位。</span></p>
</section>
```

---

## 组件 23 注意提醒卡

```html
<section style="margin:0 18px 24px;background:#FFF8E6;border-radius:0 10px 10px 0;border-left:4px solid #F0B429;padding:14px 18px;">
  <p style="margin:0 0 6px;">
    <span style="display:inline-block;background:#F0B429;color:#FFFFFF;font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;"><span leaf="">注意</span></span>
  </p>
  <p style="margin:0;font-size:14px;color:#5A4A22;line-height:1.8;"><span leaf="">注意事项占位，蓝色系里唯一允许出现的暖色，只在这一类卡片上使用。</span></p>
</section>
```

---

## 组件 24 结果 / 成功卡

```html
<section style="margin:0 18px 24px;background:#EDF9F3;border-radius:0 10px 10px 0;border-left:4px solid #22A06B;padding:14px 18px;">
  <p style="margin:0 0 6px;">
    <span style="display:inline-block;background:#22A06B;color:#FFFFFF;font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;"><span leaf="">结果</span></span>
  </p>
  <p style="margin:0;font-size:14px;color:#26543F;line-height:1.8;"><span leaf="">结果或结论占位。</span></p>
</section>
```

---

## 组件 25 金句块（大留白 + 深蓝）

```html
<section style="margin:0 18px 28px;padding:22px 20px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;text-align:center;">
  <p style="margin:0 0 10px;font-size:20px;color:#D6EBFF;font-weight:800;line-height:1;"><span leaf="">「</span></p>
  <p style="margin:0;font-size:16px;font-weight:800;color:#12558F;line-height:1.85;"><span leaf="">这里是核心观点或关键金句占位</span></p>
</section>
```

---

## 组件 26 无序列表

```html
<section style="margin:0 18px 24px;">
  <section style="display:flex;align-items:flex-start;margin-bottom:10px;">
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#1E88E5;margin:9px 10px 0 0;font-size:0;line-height:0;overflow:hidden;">.</span>
    <p style="margin:0;font-size:15px;color:#3B4A5A;line-height:1.85;flex:1;"><span leaf="">列表项占位，注意</span><span style="border-bottom:2px solid #9CCBFA;font-weight:600;"><span leaf="">关键描述也要标记</span></span><span leaf="">。</span></p>
  </section>
  <section style="display:flex;align-items:flex-start;margin-bottom:10px;">
    <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#1E88E5;margin:9px 10px 0 0;font-size:0;line-height:0;overflow:hidden;">.</span>
    <p style="margin:0;font-size:15px;color:#3B4A5A;line-height:1.85;flex:1;"><span leaf="">第二条列表项占位。</span></p>
  </section>
</section>
```

---

## 组件 27 有序列表（序号方块）

```html
<section style="margin:0 18px 24px;">
  <section style="display:flex;align-items:flex-start;margin-bottom:12px;">
    <span style="display:inline-block;background:#D6EBFF;color:#12558F;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;margin-right:10px;line-height:1.6;"><span leaf="">01</span></span>
    <p style="margin:0;font-size:15px;color:#3B4A5A;line-height:1.85;flex:1;"><span leaf="">有序条目占位。</span></p>
  </section>
  <section style="display:flex;align-items:flex-start;margin-bottom:12px;">
    <span style="display:inline-block;background:#D6EBFF;color:#12558F;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;margin-right:10px;line-height:1.6;"><span leaf="">02</span></span>
    <p style="margin:0;font-size:15px;color:#3B4A5A;line-height:1.85;flex:1;"><span leaf="">第二条有序条目占位。</span></p>
  </section>
</section>
```

---

## 组件 28 任务清单

```html
<section style="margin:0 18px 24px;padding:16px 18px;border-radius:12px;background:#F7FBFF;border:1px solid #E4EEF9;">
  <section style="display:flex;align-items:flex-start;margin-bottom:10px;">
    <span style="display:inline-block;width:14px;height:14px;border-radius:4px;background:#1E88E5;margin:5px 10px 0 0;font-size:0;line-height:0;overflow:hidden;">.</span>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;flex:1;"><span leaf="">已完成事项占位</span></p>
  </section>
  <section style="display:flex;align-items:flex-start;">
    <span style="display:inline-block;width:14px;height:14px;border-radius:4px;background:#FFFFFF;border:1px solid #9CCBFA;margin:5px 10px 0 0;font-size:0;line-height:0;overflow:hidden;">.</span>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;flex:1;"><span leaf="">未完成事项占位</span></p>
  </section>
</section>
```

---

## 组件 29 条目卡片列表

```html
<section style="margin:0 18px 24px;padding:6px 18px 14px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;">
  <section style="padding:14px 0;border-bottom:1px solid #E4EEF9;">
    <p style="margin:0 0 4px;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">条目卡片标题占位</span></p>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">条目卡片说明占位。</span></p>
  </section>
  <section style="padding:14px 0;">
    <p style="margin:0 0 4px;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">第二条条目标题占位</span></p>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">第二条条目说明占位。</span></p>
  </section>
</section>
```

---

## 组件 30 标准图片（圆角白卡 + 居中说明）

```html
<section style="margin:0 18px 8px;padding:6px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;box-shadow:0 2px 10px rgba(30,136,229,0.08);">
  <section style="border-radius:8px;overflow:hidden;">
    <span leaf=""><img src="https://placehold.orence.net/600x400?text=Placeholder" alt="图片占位" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>
  </section>
</section>
<p style="margin:0 18px 24px;font-size:12px;color:#8A99A8;text-align:center;line-height:1.7;">
  <span leaf="">— 图片说明占位</span>
</p>
```

> **图片尺寸**：一律 `max-width:100%;height:auto;display:block;margin:0 auto`，按自身尺寸显示并居中，**不用 `width:100%`**（小图会被拉伸变糊）。

---

## 组件 31 无框图片（纯图，无卡片）

```html
<section style="margin:0 18px 24px;">
  <span leaf=""><img src="https://placehold.orence.net/600x400?text=Placeholder" alt="无框图片占位" style="max-width:100%;height:auto;display:block;margin:0 auto;border-radius:10px;"></span>
</section>
```

---

## 组件 32 双图分组（上下堆叠 + 分组说明）

```html
<section style="margin:0 18px 24px;padding:14px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;">
  <section style="margin-bottom:10px;">
    <span leaf=""><img src="https://placehold.orence.net/600x400?text=Placeholder" alt="对比图一占位" style="max-width:100%;height:auto;display:block;margin:0 auto;border-radius:8px;"></span>
  </section>
  <section>
    <span leaf=""><img src="https://placehold.orence.net/600x400?text=Placeholder" alt="对比图二占位" style="max-width:100%;height:auto;display:block;margin:0 auto;border-radius:8px;"></span>
  </section>
  <p style="margin:12px 0 0;font-size:12px;color:#8A99A8;text-align:center;line-height:1.7;"><span leaf="">— 分组图片说明占位</span></p>
</section>
```

---

## 组件 33 图集说明条（多图连续区段的标题条）

```html
<section style="margin:0 18px 12px;padding:10px 16px;border-radius:999px;background:#F2F8FF;text-align:center;">
  <p style="margin:0;font-size:13px;font-weight:700;color:#12558F;letter-spacing:1px;"><span leaf="">图集标题占位 · 共 N 张</span></p>
</section>
```

---

## 组件 34 视频占位

```html
<section style="margin:0 18px 24px;padding:26px 20px;border-radius:12px;background:#F7FBFF;border:1px solid #DCE9F7;text-align:center;">
  <p style="margin:0 0 8px;font-size:24px;line-height:1;"><span leaf="">▶</span></p>
  <p style="margin:0;font-size:14px;font-weight:700;color:#12558F;"><span leaf="">视频占位标题</span></p>
  <p style="margin:6px 0 0;font-size:12px;color:#8A99A8;line-height:1.7;"><span leaf="">此处插入视频，时长约 00:00</span></p>
</section>
```

---

## 组件 35 待补素材占位（居中虚线框，唯一允许 dashed 的场景）

```html
<section style="margin:0 18px 24px;padding:30px 20px;border:1.5px dashed #C9DCEF;border-radius:14px;background:#FAFCFF;text-align:center;">
  <p style="margin:0 0 10px;font-size:24px;line-height:1;"><span leaf="">🖼</span></p>
  <p style="margin:0;font-size:14px;font-weight:700;color:#8A99A8;letter-spacing:1px;"><span leaf="">待补素材</span></p>
  <p style="margin:8px 0 0;font-size:13px;color:#A9B6C4;line-height:1.7;"><span leaf="">此处插入：素材说明占位</span></p>
</section>
```

---

## 组件 36 指标卡（三数字）

```html
<section style="margin:0 18px 24px;display:flex;">
  <section style="flex:1;padding:16px 10px;margin-right:10px;border-radius:12px;background:#F7FBFF;border:1px solid #E4EEF9;text-align:center;">
    <p style="margin:0 0 4px;font-size:22px;font-weight:800;color:#1E88E5;line-height:1.2;"><span leaf="">10</span></p>
    <p style="margin:0;font-size:12px;color:#8A99A8;line-height:1.6;"><span leaf="">指标一占位</span></p>
  </section>
  <section style="flex:1;padding:16px 10px;margin-right:10px;border-radius:12px;background:#F7FBFF;border:1px solid #E4EEF9;text-align:center;">
    <p style="margin:0 0 4px;font-size:22px;font-weight:800;color:#1E88E5;line-height:1.2;"><span leaf="">4</span></p>
    <p style="margin:0;font-size:12px;color:#8A99A8;line-height:1.6;"><span leaf="">指标二占位</span></p>
  </section>
  <section style="flex:1;padding:16px 10px;border-radius:12px;background:#F7FBFF;border:1px solid #E4EEF9;text-align:center;">
    <p style="margin:0 0 4px;font-size:22px;font-weight:800;color:#1E88E5;line-height:1.2;"><span leaf="">60</span></p>
    <p style="margin:0;font-size:12px;color:#8A99A8;line-height:1.6;"><span leaf="">指标三占位</span></p>
  </section>
</section>
```

---

## 组件 37 单行指标条

```html
<section style="margin:0 18px 24px;padding:14px 18px;border-radius:10px;background:#EAF4FF;">
  <p style="margin:0;font-size:14px;color:#12558F;line-height:1.85;">
    <span style="font-size:20px;font-weight:800;color:#1E88E5;"><span leaf="">128</span></span><span leaf="">　人到场 · </span><span style="font-size:20px;font-weight:800;color:#1E88E5;"><span leaf="">4</span></span><span leaf="">　小时 · </span><span style="font-size:20px;font-weight:800;color:#1E88E5;"><span leaf="">10</span></span><span leaf="">　道题</span>
  </p>
</section>
```

---

## 组件 38 进度条

```html
<section style="margin:0 18px 24px;">
  <p style="margin:0 0 8px;font-size:13px;color:#3B4A5A;line-height:1.7;"><span leaf="">进度项占位</span><span style="color:#1E88E5;font-weight:800;"><span leaf="">　75%</span></span></p>
  <section style="height:8px;border-radius:999px;background:#EAF4FF;overflow:hidden;">
    <section style="width:75%;height:8px;border-radius:999px;background:#1E88E5;"><span leaf=""><br></span></section>
  </section>
</section>
```

---

## 组件 39 数据表格（真实表格语义）

```html
<section style="margin:0 18px 24px;border-radius:12px;overflow:hidden;border:1px solid #DCE9F7;">
  <table style="width:100%;border-collapse:collapse;font-size:14px;">
    <tbody>
      <tr>
        <td style="padding:10px 14px;background:#EAF4FF;color:#12558F;font-weight:800;border-bottom:1px solid #DCE9F7;"><span leaf="">项目</span></td>
        <td style="padding:10px 14px;background:#EAF4FF;color:#12558F;font-weight:800;border-bottom:1px solid #DCE9F7;"><span leaf="">数值占位</span></td>
      </tr>
      <tr>
        <td style="padding:10px 14px;color:#3B4A5A;border-bottom:1px solid #E4EEF9;"><span leaf="">第一行占位</span></td>
        <td style="padding:10px 14px;color:#3B4A5A;border-bottom:1px solid #E4EEF9;"><span leaf="">10%</span></td>
      </tr>
      <tr>
        <td style="padding:10px 14px;color:#3B4A5A;"><span leaf="">第二行占位</span></td>
        <td style="padding:10px 14px;color:#3B4A5A;"><span leaf="">20%</span></td>
      </tr>
    </tbody>
  </table>
</section>
```

---

## 组件 40 对照行（左右对照，上下分组实现）

```html
<section style="margin:0 18px 24px;border-radius:12px;border:1px solid #DCE9F7;overflow:hidden;">
  <section style="padding:14px 18px;background:#F7FBFF;border-bottom:1px solid #E4EEF9;">
    <p style="margin:0 0 4px;font-size:12px;color:#1E88E5;font-weight:700;letter-spacing:1px;"><span leaf="">A 侧标签占位</span></p>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">A 侧说明占位</span></p>
  </section>
  <section style="padding:14px 18px;">
    <p style="margin:0 0 4px;font-size:12px;color:#8A99A8;font-weight:700;letter-spacing:1px;"><span leaf="">B 侧标签占位</span></p>
    <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">B 侧说明占位</span></p>
  </section>
</section>
```

---

## 组件 41 时间线（竖线 + 节点）

```html
<section style="margin:0 18px 24px;padding:20px 20px 6px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;">
  <p style="margin:0 0 16px;font-size:15px;font-weight:800;color:#12558F;"><span leaf="">流程标题占位</span></p>
  <section style="border-left:2px solid #D6EBFF;padding-left:18px;">
    <section style="margin-bottom:18px;">
      <p style="margin:0 0 4px;font-size:12px;color:#1E88E5;font-weight:700;letter-spacing:1px;"><span leaf="">节点时间占位</span></p>
      <p style="margin:0 0 4px;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">节点标题占位</span></p>
      <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">节点说明占位，描述这一步发生了什么。</span></p>
    </section>
    <section style="margin-bottom:18px;">
      <p style="margin:0 0 4px;font-size:12px;color:#1E88E5;font-weight:700;letter-spacing:1px;"><span leaf="">节点时间占位</span></p>
      <p style="margin:0 0 4px;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">第二个节点标题占位</span></p>
      <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">第二个节点说明占位。</span></p>
    </section>
  </section>
</section>
```

---

## 组件 42 步骤流程条（编号 + 箭头）

```html
<section style="margin:0 18px 24px;padding:16px 18px;border-radius:12px;background:#F7FBFF;border:1px solid #E4EEF9;">
  <section style="display:flex;align-items:center;margin-bottom:12px;">
    <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;line-height:1.6;"><span leaf="">01</span></span>
    <p style="margin:0 0 0 10px;font-size:14px;color:#3B4A5A;line-height:1.8;flex:1;"><span leaf="">步骤一占位</span></p>
  </section>
  <section style="display:flex;align-items:center;margin-bottom:12px;">
    <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;line-height:1.6;"><span leaf="">02</span></span>
    <p style="margin:0 0 0 10px;font-size:14px;color:#3B4A5A;line-height:1.8;flex:1;"><span leaf="">步骤二占位</span></p>
  </section>
  <section style="display:flex;align-items:center;">
    <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:12px;font-weight:800;padding:2px 9px;border-radius:8px;line-height:1.6;"><span leaf="">03</span></span>
    <p style="margin:0 0 0 10px;font-size:14px;color:#3B4A5A;line-height:1.8;flex:1;"><span leaf="">步骤三占位</span></p>
  </section>
</section>
```

---

## 组件 43 流程总览卡

```html
<section style="margin:0 18px 24px;padding:18px 20px;border-radius:12px;background:linear-gradient(135deg,#EAF4FF 0%,#FFFFFF 100%);border:1px solid #DCE9F7;">
  <p style="margin:0 0 12px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">OVERVIEW　总览</span></p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:2;">
    <span style="color:#12558F;font-weight:800;"><span leaf="">阶段一占位</span></span><span leaf="">　→　</span><span style="color:#12558F;font-weight:800;"><span leaf="">阶段二占位</span></span><span leaf="">　→　</span><span style="color:#12558F;font-weight:800;"><span leaf="">阶段三占位</span></span>
  </p>
</section>
```

---

## 组件 44 深色代码块

```html
<section style="margin:0 18px 20px;border-radius:10px;overflow:hidden;background:#1E293B;box-shadow:0 4px 16px -8px rgba(15,23,42,0.4);">
  <section style="display:flex;align-items:center;padding:9px 14px;background:#0F172A;">
    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#FF5F56;margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>
    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#FFBD2E;margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>
    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#27C93F;font-size:0;line-height:0;overflow:hidden;">.</span>
    <span style="margin-left:12px;font-size:12px;color:#64748B;font-family:Consolas,Monaco,monospace;letter-spacing:1px;"><span leaf="">python</span></span>
  </section>
  <section style="padding:11px 14px;">
    <p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;"><span leaf="">def demo():</span></p>
    <p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;"><span leaf="">　　return "占位代码"</span></p>
  </section>
</section>
```

> **不要用 `white-space:pre`**：每行一个 `<p style="margin:0">`，缩进用全角空格 `　`，行距靠 `line-height:1.6`。

---

## 组件 45 浅色代码块（蓝左竖条）

```html
<section style="margin:0 18px 20px;border-radius:8px;overflow:hidden;background:#F6F8FA;border:1px solid #E5E7EB;border-left:3px solid #1E88E5;">
  <section style="padding:7px 14px;border-bottom:1px solid #E5E7EB;">
    <span style="font-size:12px;color:#9CA3AF;font-family:Consolas,Monaco,monospace;letter-spacing:1px;"><span leaf="">bash</span></span>
  </section>
  <section style="padding:11px 14px;">
    <p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#24292F;"><span leaf="">echo 命令行占位</span></p>
  </section>
</section>
```

---

## 组件 46 FAQ 条目

```html
<section style="margin:0 18px 24px;padding:16px 18px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;">
  <p style="margin:0 0 8px;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;">
    <span style="color:#1E88E5;margin-right:6px;"><span leaf="">Q</span></span><span leaf="">常见问题占位？</span>
  </p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.85;">
    <span style="color:#8A99A8;font-weight:800;margin-right:6px;"><span leaf="">A</span></span><span leaf="">回答内容占位。</span>
  </p>
</section>
```

---

## 组件 47 延伸阅读条

```html
<section style="margin:0 18px 24px;padding:14px 18px;border-radius:10px;background:#F7FBFF;border:1px solid #E4EEF9;border-left:3px solid #9CCBFA;">
  <p style="margin:0 0 6px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">READ MORE</span></p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">延伸阅读条目占位一</span></p>
  <p style="margin:4px 0 0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">延伸阅读条目占位二</span></p>
</section>
```

---

## 组件 48 下载引导条（span 模拟按钮）

```html
<section style="margin:0 18px 24px;padding:16px 18px;border-radius:12px;background:#EAF4FF;border:1px solid #DCE9F7;display:flex;align-items:center;">
  <section style="flex:1;">
    <p style="margin:0 0 4px;font-size:15px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">资源名称占位</span></p>
    <p style="margin:0;font-size:12px;color:#8A99A8;line-height:1.7;"><span leaf="">一句话说明这个资源是什么</span></p>
  </section>
  <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:13px;font-weight:700;padding:8px 16px;border-radius:999px;margin-left:12px;"><span leaf="">按钮文案占位</span></span>
</section>
```

---

## 组件 49 作者信息卡

```html
<section style="margin:0 18px 24px;padding:18px 20px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;">
  <p style="margin:0 0 8px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">AUTHOR　关于作者</span></p>
  <p style="margin:0 0 6px;font-size:16px;font-weight:800;color:#12558F;line-height:1.6;"><span leaf="">作者名占位</span></p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">一句话作者简介占位。</span></p>
</section>
```

---

## 组件 50 CTA 卡（渐变浅蓝 + 按钮）

```html
<section style="margin:0 18px 26px;padding:26px 22px;border-radius:16px;background:linear-gradient(135deg,#EAF4FF 0%,#FFFFFF 100%);border:1px solid #DCE9F7;text-align:center;">
  <p style="margin:0 0 10px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">JOIN US</span></p>
  <p style="margin:0 0 10px;font-size:18px;font-weight:800;color:#12558F;line-height:1.55;"><span leaf="">CTA 主文案占位</span></p>
  <p style="margin:0 0 18px;font-size:14px;color:#5A6B7C;line-height:1.8;"><span leaf="">CTA 补充说明占位，说清楚怎么做、去哪里。</span></p>
  <span style="display:inline-block;background:#1E88E5;color:#FFFFFF;font-size:14px;font-weight:700;padding:10px 26px;border-radius:999px;"><span leaf="">按钮文案占位</span></span>
</section>
```

---

## 组件 51 结尾总结区

```html
<section style="margin:0 18px 24px;padding:20px 20px 16px;border-radius:12px;background:#F7FBFF;border:1px solid #E4EEF9;">
  <p style="margin:0 0 12px;font-size:11px;color:#1E88E5;font-weight:700;letter-spacing:2px;"><span leaf="">ENDING　写在最后</span></p>
  <p style="margin:0 0 10px;font-size:15px;color:#3B4A5A;line-height:1.85;"><span leaf="">结尾总结第一段占位。</span></p>
  <p style="margin:0;font-size:15px;color:#3B4A5A;line-height:1.85;"><span leaf="">结尾总结第二段占位。</span></p>
</section>
```

---

## 组件 52 签名区（署名 + 一句话）

```html
<section style="margin:0 18px 24px;padding:18px 20px;border-radius:12px;background:#FFFFFF;border:1px solid #DCE9F7;">
  <p style="margin:0 0 8px;font-size:14px;color:#3B4A5A;line-height:1.8;">
    <span leaf="">我是 </span><span style="color:#0B63C4;font-weight:800;"><span leaf="">作者名占位</span></span><span leaf="">，一句话简介占位。</span>
  </p>
  <p style="margin:0;font-size:14px;color:#3B4A5A;line-height:1.8;"><span leaf="">如果你觉得今天这篇有收获，欢迎点赞、在看、转发三连，我们下篇见。</span></p>
</section>
```

---

## 组件 53 末尾互动条

```html
<section style="margin:0 18px 24px;padding:14px 18px;border-radius:999px;background:#EAF4FF;text-align:center;">
  <p style="margin:0;font-size:13px;color:#12558F;font-weight:700;letter-spacing:1px;line-height:1.8;"><span leaf="">点赞 · 在看 · 转发　三连支持一下</span></p>
</section>
```

---

## 组件 54 页脚说明条

```html
<section style="margin:0 18px 20px;padding:14px 18px;border-top:1px solid #E4EEF9;">
  <p style="margin:0;font-size:12px;color:#8A99A8;line-height:1.8;text-align:center;"><span leaf="">页脚说明占位 · 主办单位占位 · 联系方式占位</span></p>
</section>
```

---

## 完整文章模板骨架

```
组件 1  全局容器
├─ 组件 2   封面主卡（栏目标签 / 主标题 / 副标题 / 日期作者）
├─ 组件 4   元信息条（可选，封面信息已足时可省）
├─ 组件 5   目录卡（精选 3 条看点在引言之前，非完整章节列表）
├─ 组件 7   开头引言卡（金句 + 荧光笔核心词 + 署名）
├─ 组件 9   编号章节标题 01（CHAPTER 01 + 英文标签）
│   ├─ 组件 16/17  正文段落（每段 1–3 处下划线标记）
│   ├─ 组件 30     图片 + 说明（图片紧随其描述的段落之后）
│   ├─ 组件 20/21  引用块 / 亮点卡（按需点缀）
│   └─ 组件 14/15  分割线（章节之间）
├─ 组件 9   编号章节标题 02
│   ├─ 组件 36     指标卡（数据段）
│   ├─ 组件 41     时间线（流程段）
│   └─ 组件 39     数据表格（比例 / 清单）
├─ 组件 9   编号章节标题 03 …
├─ 组件 51  结尾总结区
├─ 组件 50  CTA 卡（行动号召，图片型文章常用于"加入我们"）
├─ 组件 52  签名区（全文唯一署名处）
├─ 组件 53  末尾互动条
└─ 组件 54  页脚说明条
```

> 目录卡位置：**封面之后、开头引言之前**。
> 末章编号变体：结语类末章用 `∞` 代替数字编号，英文标签用 `ENDING　收束`。

---

## 文章类型 → 组件组合配方表

| 文章类型 | 核心组件组合 | 点缀组件 |
|---|---|---|
| **图文活动回顾 / 赛事复盘**（本主题主场景） | 封面主卡 + 目录卡 + 引言卡 + 编号章节标题 + 正文段落 + 图片(30) + 指标卡(36) + 时间线(41) + CTA 卡(50) | 图集说明条(33)、亮点卡(21)、金句块(25)、签名区(52)、互动条(53)、页脚条(54) |
| 教程 / 操作指南 | 封面主卡 + 目录卡 + 编号章节标题 + 步骤流程条(42) + 代码块(44/45) + 图片(30) | 信息提示卡(22)、注意提醒卡(23)、任务清单(28)、行内代码(19) |
| 盘点 / 工具清单 | 封面主卡 + 目录卡 + 条目卡片列表(29) + 有序列表(27) + 对照行(40) | 药丸标签(12)、指标卡(36)、FAQ(46)、延伸阅读(47) |
| 观点 / 深度分析 | 刊头(3) + 引言卡(7) + 正文段落(16) + 引用块(20) + 金句块(25) + 锚点句(18) | 无编号章节标题(10)、左竖条小标题(13)、结尾总结区(51) |
| 数据报告 / 复盘 | 封面主卡 + 单行指标条(37) + 指标卡(36) + 数据表格(39) + 进度条(38) | 结果卡(24)、时间线(41)、对照行(40)、页脚条(54) |
| 人物 / 访谈特稿 | 封面主卡 + 引言卡(7) + 引用块(20) + 图片(30) + FAQ(46) | 图集说明条(33)、金句块(25)、作者信息卡(49) |
| 生活 / 情感随笔 | 刊头(3) + 素引言(8) + 正文段落(16) + 无框图片(31) + 金句块(25) | 圆点分割线(15)、结尾总结区(51)、签名区(52) |

---

## Markdown → 组件映射规则表

| Markdown 元素 | 映射到 |
|---|---|
| 文章标题（`#` / frontmatter title） | 组件 2 封面主卡主标题（副标题用首段导语或省略） |
| `> 引用`（文章最开头） | 组件 7 开头引言卡（核心词用荧光笔） |
| `## 章节标题` | 组件 9 编号章节标题（按出现顺序 `01/02/03…`，末章结语用 `∞`） |
| `### 子标题` | 组件 11 小节标题条（或组件 13 左竖条小标题） |
| 正文段落 | 组件 16 正文段落（每段主动标 1–3 个下划线关键词） |
| 章节首段 | 组件 17 首段大字（16px） |
| `**加粗**` | 主色锚点加粗 `color:#0B63C4;font-weight:800`（全文 ≤ 5 处） |
| `==高亮==` | 荧光笔 `linear-gradient(180deg,rgba(255,255,255,0) 60%,#CFE8FF 60%)` |
| `<u>文字</u>` / `++文字++` | 下划线 `border-bottom:2px solid #9CCBFA;font-weight:600` |
| `~~文字~~` | 荧光笔（底部半高亮 `#CFE8FF`） |
| 非开头 `> 引用` | 组件 20 引用块（浅蓝底 + 左竖条） |
| 单独成段的金句 | 组件 25 金句块 |
| `![说明](url)` | 组件 30 标准图片（有说明才加说明行） |
| `![](url)` 空说明 | 组件 31 无框图片 |
| 连续多图区段 | 组件 33 图集说明条 + 多张组件 30/31 |
| `.gif` 动图 | 组件 30，说明行前加「GIF 动图」小标签（浅蓝底 `#D6EBFF` + 深蓝字 `#12558F`） |
| ``` 代码块 ``` | 组件 44 深色代码块（浅色温和主题可用组件 45） |
| 行内 `` `code` `` | 行内代码（浅灰底 + 主色字，见组件 19） |
| `- 列表项` | 组件 26 无序列表 |
| `1. 列表项` | 组件 27 有序列表（序号方块） |
| Markdown 表格 | 组件 39 数据表格 |
| `---` 分割线 | 组件 14 渐变分割线（柔和处用组件 15 圆点分割线） |
| 提示 / 注意 / 旁注 | 组件 22 信息提示卡 / 组件 23 注意提醒卡 |
| 数据 / 指标 | 组件 36 指标卡、组件 37 单行指标条、组件 38 进度条 |
| 流程 / 日程 | 组件 41 时间线、组件 42 步骤流程条、组件 43 流程总览卡 |
| 行动号召 / 加入我们 | 组件 50 CTA 卡 |
| 作者署名 | 组件 52 签名区（全文唯一，默认 `{{作者名}}` 占位） |
| 文末互动 | 组件 53 末尾互动条 |
| 主办 / 版权说明 | 组件 54 页脚说明条 |

---

## 主题元信息（供主题索引与自定义生成回溯）

```
THEME-NAME: 清爽蓝
THEME-ID: theme-fresh-blue
THEME-DESCRIPTION: 通透蓝白调，大留白 + 浅蓝衬底卡片 + 淡蓝细描边 + 中等圆角 + 柔阴影；栏目条式编号章节、指标卡数据表达、竖线时间线流程表达、渐变 CTA 收尾
THEME-COLOR: #1E88E5
THEME-BACKGROUND-COLOR: #FFFFFF
THEME-TEXT-COLOR: #3B4A5A
THEME-ACCENT-COLOR: #0B63C4
THEME-DECORATION-COLOR: #EAF4FF
THEME-FONT-PREFERENCE: pingfang
THEME-DESIGN-TECHNIQUE-TAGS: 栏目条编号, 浅蓝衬底卡片, 淡蓝细描边, 竖线时间线
THEME-STYLE-FEATURE-TAGS: 通透清爽, 年轻克制, 留白呼吸, 蓝白单色系
THEME-SCENE-TAGS: 校园活动回顾, 赛事复盘, 团队招新, 图文叙事
THEME-RADIUS-PREFERENCE: 中等圆角 12px
THEME-SHADOW-PREFERENCE: 极低饱和柔阴影
```
