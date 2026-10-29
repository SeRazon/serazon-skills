# -*- coding: utf-8 -*-
"""
精读稿 Markdown → 单文件 HTML（带侧栏目录、深色主题、滚动高亮）

用法：
    python 精读转网页.py <输入.md> [--out 输出.html] [--title "文献精读 · XXX"]
                        [--if 6.2] [--journal "Frontiers in Microbiology"]
                        [--quartile Q1]

输出为自包含单文件（内联 CSS + JS，无任何外部资源），可直接双击打开 / 分发。
标题映射：md 的「板块 N」标题（任意级别 #~####）均作为顶级板块（进目录）；
「图表 N / Figure N / 图 N（含 S 前缀）」标题（任意级别）均作为二级目录项（进目录，缩进）；
其余二级标题作小节，三/四级作正文标题。写稿者无需严格用 #/## 也能生成正确两级目录。
影响因子徽标：传入 --if 后，页头右侧显示「IF x.x · Qn · 期刊名」。
未传则完全不显示该徽标（向后兼容，不影响既有调用）。
"""
import os
import re
import sys
import io
import html as _html

CSS = """
:root{
  --bg:#0e1117; --panel:#141b22; --panel2:#18212a; --border:#26313c;
  --txt:#d7e0ea; --txt2:#b9c4d1; --dim:#8b97a6; --faint:#5c6b78;
  --a1:#34d3c4; --a2:#4a9eff; --warn:#ffb454; --radius:14px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth; scroll-padding-top:88px}
body{margin:0;background:linear-gradient(165deg,#0e1117,#111820 55%,#0e1117);color:var(--txt);
  font-family:"Segoe UI","PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;
  line-height:1.78;font-size:16px}
a{color:var(--a2);text-decoration:none}
a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:40;backdrop-filter:blur(10px);
  background:linear-gradient(180deg,rgba(14,17,23,.94),rgba(14,17,23,.8));
  border-bottom:1px solid var(--border)}
header .in{max-width:1280px;margin:0 auto;padding:13px 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.brand{font-weight:700;font-size:17px;background:linear-gradient(90deg,var(--a1),var(--a2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.sub{font-size:12.5px;color:var(--dim)}
.badge{margin-left:auto;font-size:12px;font-weight:700;color:#06222a;
  background:linear-gradient(90deg,var(--a1),var(--a2));padding:5px 12px;border-radius:999px;white-space:nowrap}
/* 影响因子徽标：仅当传入 --if 时渲染 */
.ifbadge{display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:700;
  color:var(--warn);border:1px solid rgba(255,180,84,.42);background:rgba(255,180,84,.09);
  padding:4px 12px;border-radius:999px;white-space:nowrap}
.ifbadge .ifv{font-size:13.5px;letter-spacing:.3px}
.ifbadge .ifq{color:var(--a1);font-weight:700}
.ifbadge .ifj{color:var(--dim);font-weight:400;max-width:22ch;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.wrap{max-width:1280px;margin:0 auto;padding:26px 24px 90px;display:grid;
  grid-template-columns:286px 1fr;gap:34px;align-items:start}
nav{position:sticky;top:88px;background:var(--panel);border:1px solid var(--border);
  border-radius:var(--radius);padding:14px 12px;max-height:calc(100vh - 116px);overflow:auto}
nav h4{margin:0 0 10px;font-size:12px;letter-spacing:1.4px;color:var(--faint);padding:0 8px}
nav ul{list-style:none;margin:0;padding:0}
nav a{display:block;padding:6px 10px;border-radius:8px;color:var(--dim);font-size:13.5px;
  border-left:2px solid transparent}
nav a:hover{background:var(--panel2);color:var(--txt)}
nav a.lv2{padding-left:22px;font-size:12.5px}
nav a.on{color:var(--a1);border-left-color:var(--a1);background:linear-gradient(90deg,rgba(52,211,196,.14),transparent);font-weight:600}
main{min-width:0;font-size:14.5px;color:var(--txt2)}
section{background:var(--panel);border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 24px;margin:0 0 20px}
h1{font-size:21.5px;margin:6px 0 14px;padding-bottom:12px;border-bottom:1px solid var(--border);
  background:linear-gradient(90deg,var(--a1),var(--a2));-webkit-background-clip:text;background-clip:text;color:transparent}
h2{font-size:17.5px;margin:22px 0 10px;padding-left:11px;border-left:3px solid var(--a1)}
h3{font-size:15px;margin:18px 0 8px;color:var(--a1)}
h4{font-size:14px;margin:14px 0 6px;color:var(--txt2)}
p{margin:9px 0}
ul,ol{margin:9px 0;padding-left:24px}
li{margin:4px 0}
blockquote{margin:12px 0;padding:10px 16px;border-left:3px solid var(--warn);
  background:var(--panel2);color:var(--dim);border-radius:0 8px 8px 0}
code{background:var(--panel2);border:1px solid var(--border);border-radius:5px;padding:1px 6px;font-size:12.5px;
  font-family:ui-monospace,Consolas,monospace}
pre{background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:14px 16px;overflow:auto}
pre code{background:none;border:none;padding:0}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;display:block;overflow-x:auto}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--a1);font-weight:600;background:var(--panel2);white-space:nowrap}
hr{border:none;border-top:1px solid var(--border);margin:20px 0}
strong{color:var(--txt)}
.top{position:fixed;right:26px;bottom:26px;width:42px;height:42px;border-radius:50%;
  border:1px solid var(--border);background:var(--panel2);color:var(--txt);cursor:pointer;font-size:17px;display:none}
.top:hover{border-color:var(--a1);color:var(--a1)}
@media(max-width:900px){.wrap{grid-template-columns:1fr}nav{display:none}}
"""

JS = """
// 章节锚点必须取「带 id 的元素」：
//   section[id]  = 板块（h1 在 section 内部，**h1 自己没有 id**）
//   h2[id]       = 小节
// 若误写成 'main h1'，h1 的 id 是空字符串，spy 永远对不上任何目录项，
// 高亮就会定格在初始状态（本页实测过这个 bug）。
const secs=[...document.querySelectorAll('main section[id], main h2[id]')];
const links=[...document.querySelectorAll('nav a')];
const nav=document.querySelector('nav');
let curId=null, lockUntil=0;

// 手动点目录后短暂锁定，避免平滑滚动过程中高亮被"半路"的章节抢走
links.forEach(a=>a.addEventListener('click',()=>{
  curId=a.dataset.t; lockUntil=Date.now()+700;
  links.forEach(x=>x.classList.toggle('on',x.dataset.t===curId));
}));

function keepVisible(a){
  // 目录自身是可滚动容器（max-height + overflow:auto），
  // 因此要滚动的是 nav 的 scrollTop，不是 window。
  const aTop=a.offsetTop, aBot=aTop+a.offsetHeight;
  const vTop=nav.scrollTop, vBot=vTop+nav.clientHeight;
  const pad=Math.round(nav.clientHeight*0.28);   // 留出上下余量，不做"贴边跳"
  if(aTop-pad<vTop){ nav.scrollTo({top:Math.max(0,aTop-pad),behavior:'smooth'}); }
  else if(aBot+pad>vBot){ nav.scrollTo({top:aBot+pad-nav.clientHeight,behavior:'smooth'}); }
}

function spy(){
  if(!secs.length) return;
  let cur=secs[0];
  for(const s of secs){ if(s.getBoundingClientRect().top<=150) cur=s; }
  // 锁定窗口内（点了目录、正文还在平滑滚动途中）：高亮固定在点击项，
  // 既不被"半路"的章节抢走，也不去滚动目录。
  if(Date.now()<lockUntil) return;
  if(cur.id===curId) return;                    // 没变就不动，省掉每帧的滚动
  curId=cur.id;
  let act=null;
  links.forEach(a=>{
    const hit=a.dataset.t===curId;
    a.classList.toggle('on',hit);
    if(hit) act=a;
  });
  if(act) keepVisible(act);
}
document.addEventListener('scroll',spy,{passive:true});
window.addEventListener('resize',spy,{passive:true});
spy();

// 注意：变量名不能叫 top —— window.top 是浏览器内置全局量，
// 用 const top = ... 会直接抛 "Identifier 'top' has already been declared"，
// 整个脚本从解析阶段就挂掉，scroll spy 与目录跟随会**全部失效且无任何提示**。
const toTopBtn=document.getElementById('top');
if(toTopBtn){
  window.addEventListener('scroll',()=>{
    toTopBtn.style.display=window.scrollY>500?'block':'none';
  },{passive:true});
  toTopBtn.onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
}
"""


def inline(s):
    s = _html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def convert(md, title, if_val=None, journal=None, quartile=None):
    lines = md.split("\n")
    body, toc = [], []
    sec_n = sub_n = 0
    open_sec = False
    i = 0
    buf = []
    empty_lines = 0      # 统计"未产出任何内容"的输入行，用于结尾自检

    def flush_para():
        if buf:
            body.append("<p>%s</p>" % inline(" ".join(buf)))
            buf.clear()

    def close_sec():
        nonlocal open_sec
        if open_sec:
            body.append("</section>")
            open_sec = False

    while i < len(lines):
        ln = lines[i]

        if ln.strip().startswith("```"):
            flush_para()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(_html.escape(lines[i]))
                i += 1
            body.append("<pre><code>%s</code></pre>" % "\n".join(code))
            i += 1
            continue

        if re.match(r"^\s*\|.*\|\s*$", ln):
            flush_para()
            rows = []
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            cells = [r for r in rows if not re.match(r"^[\s:\-|]+$", "|".join(r))]
            if cells:
                t = ["<table><thead><tr>"]
                t += ["<th>%s</th>" % inline(c) for c in cells[0]]
                t.append("</tr></thead><tbody>")
                for r in cells[1:]:
                    t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
                t.append("</tbody></table>")
                body.append("".join(t))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            flush_para()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            i += 1
            # ★ 容错补丁（2026-09-20 X43 修复）：板块 / 图条目在「任意标题级别」都被识别，
            #   不再强制要求 # 板块 / ## 图表。这样即使写稿者用了 ## 板块 或 #### 图表，
            #   目录（TOC）仍能生成正确的两级结构，不会退化成 11 条平铺。
            #   · 板块主标题：以「板块 N」开头；拒绝「板块 N 补充说明 / 备注」等同前缀小标题，
            #     以免复现 X20 把板块切成两段的 bug；
            #   · 图条目：以「图表 N / Figure N / 图 N（含 S 前缀）」开头。
            sec = bool(re.match(r'板块\s*\d+', txt)) and not re.match(
                r'板块\s*\d+\s*(?:补充|说明|备注|续|之[一二三四五六七八九十])', txt)
            fig = bool(re.match(r'(图表|Figure|图)\s*[S\d]+', txt))
            if sec:
                close_sec()
                sec_n += 1
                sid = "sec-%d" % sec_n
                toc.append((sid, txt, 1))
                body.append('<section id="%s"><h1>%s</h1>' % (sid, inline(txt)))
                open_sec = True
            elif fig:
                sub_n += 1
                sid = "sub-%d" % sub_n
                toc.append((sid, txt, 2))
                body.append('<h2 id="%s">%s</h2>' % (sid, inline(txt)))
            elif lvl == 1:
                if ("文献精读" in txt) or ("大纲" in txt):   # 文档大标题不进正文
                    continue
                close_sec()
                sec_n += 1
                sid = "sec-%d" % sec_n
                toc.append((sid, txt, 1))
                body.append('<section id="%s"><h1>%s</h1>' % (sid, inline(txt)))
                open_sec = True
            elif lvl == 2:
                sub_n += 1
                sid = "sub-%d" % sub_n
                toc.append((sid, txt, 2))
                body.append('<h2 id="%s">%s</h2>' % (sid, inline(txt)))
            elif lvl == 3:
                body.append("<h3>%s</h3>" % inline(txt))
            else:
                body.append("<h4>%s</h4>" % inline(txt))
            continue

        if re.match(r"^\s*>\s?", ln):
            flush_para()
            q = []
            while i < len(lines) and re.match(r"^\s*>\s?", lines[i]):
                q.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            body.append("<blockquote>%s</blockquote>" % inline(" ".join(q)))
            continue

        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            flush_para()
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i])):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            body.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue

        if re.match(r"^\s*---+\s*$", ln):
            flush_para()
            close_sec()
            i += 1
            continue

        if not ln.strip():
            flush_para()
            i += 1
            continue

        buf.append(ln.strip())
        i += 1

    flush_para()
    close_sec()

    # ---------- 自检：不给"看起来成功的空页面" ----------
    # 不诚实的失败方式有两种：报错、以及**静默产出空壳**。
    # 后者更坏——用户双击打开才发现什么都没有，却以为转换成功了。
    if not toc:
        raise ValueError(
            '输入未包含任何一级标题（"# 板块 N"），转换结果会是空页面。'
            '请检查：稿件是否用了 Markdown 一级标题、是否误传了空文件。')
    if not any(t.strip() for t in body):
        raise ValueError('输入解析后正文为空，已中止（不产出空壳页面）。')

    toc_html = "".join(
        '<li><a href="#%s" data-t="%s" class="lv%d">%s</a></li>' % (sid, sid, lv, _html.escape(t))
        for sid, t, lv in toc
    )

    # —— 影响因子徽标（仅在拿到 IF 时渲染；拿不到就完全不出现在页面上）——
    ifbadge_html = ""
    if if_val is not None:
        try:
            _v = float(if_val)
            # 显示规则（2026-09-21 修）：JCR 影响因子惯例保留一位小数。
            # 不能用 "%g"——它会把 18.0 压成 "18"、把 5.80 压成 "5.8"（尾随零被吃），
            # 与 JCR 表里的写法不一致，用户对着表核不上。
            _shown = ("%.1f" % _v) if abs(_v - round(_v, 1)) < 1e-9 else ("%g" % _v)
        except (TypeError, ValueError):
            _shown = str(if_val)
        _parts = ['<span class="ifv">IF %s</span>' % _html.escape(_shown)]
        if quartile:
            _parts.append('<span class="ifq">%s</span>' % _html.escape(str(quartile)))
        if journal:
            _parts.append('<span class="ifj">%s</span>' % _html.escape(str(journal)))
        ifbadge_html = '<div class="ifbadge">%s</div>' % "".join(_parts)

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>%s</style>
</head>
<body>
<header><div class="in">
  <div><div class="brand">%s</div><div class="sub">结构化精读 · 逐图解析 · 缺陷审计</div></div>
  %s<div class="badge">科研文献精读剖析助手</div>
</div></header>
<div class="wrap">
  <nav><h4>目录</h4><ul>%s</ul></nav>
  <main>%s</main>
</div>
<button class="top" id="top" title="回到顶部">↑</button>
<script>%s</script>
</body>
</html>""" % (_html.escape(title), CSS, _html.escape(title), ifbadge_html,
           toc_html, "".join(body), JS)


def main():
    if len(sys.argv) < 2:
        print("用法: python 精读转网页.py <输入.md> [--out 输出.html] [--title 标题] "
              "[--if 6.2] [--journal 期刊名] [--quartile Q1]")
        return 1
    src = sys.argv[1]
    out = None
    title = None
    if_val = None
    journal = None
    quartile = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    if "--if" in sys.argv:
        if_val = sys.argv[sys.argv.index("--if") + 1]
    if "--journal" in sys.argv:
        journal = sys.argv[sys.argv.index("--journal") + 1]
    if "--quartile" in sys.argv:
        quartile = sys.argv[sys.argv.index("--quartile") + 1]
    if not os.path.isfile(src):
        print("[错误] 找不到文件:", src)
        return 1
    md = io.open(src, encoding="utf-8").read()
    if not title:
        first = md.split("\n")[0].lstrip("# ").strip()
        title = first if first else os.path.splitext(os.path.basename(src))[0]
    if not out:
        out = os.path.splitext(src)[0] + ".html"
    try:
        page = convert(md, title, if_val=if_val, journal=journal, quartile=quartile)
    except ValueError as e:
        # 宁可报错退出，也不产出"能打开但没内容"的假成品
        print("[错误] 转换失败：%s" % e)
        return 1
    io.open(out, "w", encoding="utf-8").write(page)
    n_sec = page.count("<section ")
    tag = ""
    if if_val is not None:
        tag = "，IF 徽标已渲染(IF %s)" % if_val
    print("[完成] 已生成网页:", out,
          "(%.1f KB, %d 个板块%s)" % (os.path.getsize(out) / 1024, n_sec, tag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
