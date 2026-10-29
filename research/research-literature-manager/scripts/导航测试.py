# -*- coding: utf-8 -*-
"""
导航（左侧目录跟随右侧滚动）真实浏览器回归测试。

为什么必须用真实浏览器：
  2026-09-20 我用 Node + mock DOM 跑出 14/14 全绿，但页面在浏览器里
  **整个脚本从头就没执行**（`const top` 与浏览器内置 `window.top` 冲突，
  解析阶段直接抛错）。mock 里没有 window.top，所以测不出来。
  → 教训：**导航/布局类逻辑，mock 通过不算通过，必须真实渲染 + 真实滚动。**

用法：
  python 导航测试.py [单个 html 路径 | 输出目录]
  不传参数时，默认扫当前工作区 outputs/ 下全部 文献精读_*.html

依赖：playwright（用本机已装 Edge，不需要额外下载浏览器内核）
"""
import glob
import io
import os
import re
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("【需要依赖】本脚本用于真实浏览器渲染校验，需先安装 playwright：pip install playwright")
    print("（这是开发期自测脚本，不属于精读/归档交付流程，缺失不影响正常使用。）")
    sys.exit(0)

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser():
    for c in EDGE_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def collect(arg=None):
    if arg and os.path.isfile(arg):
        return [arg]
    base = arg or os.environ.get("READING_OUT_DIR") or os.getcwd()
    return sorted(glob.glob(os.path.join(base, "文献精读_*.html")))


def check(pg, path):
    """返回 (是否通过, 说明行列表)"""
    lines = []
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file:///" + path.replace("\\", "/").replace(" ", "%20"))
    pg.wait_for_timeout(300)

    if errs:
        lines.append("  JS 报错: " + "; ".join(errs))
        return False, lines

    nav = pg.evaluate(
        "()=>{const n=document.querySelector('nav');"
        "return {sh:n.scrollHeight, ch:n.clientHeight};}")
    scrollable = nav["sh"] > nav["ch"]

    # 断言 1：锚点必须都能对上目录项（h1 无 id 这类结构错误会在这里暴露）
    mapping = pg.evaluate("""()=>{
      const secs=[...document.querySelectorAll('main section[id], main h2[id]')];
      const links=[...document.querySelectorAll('nav a')].map(a=>a.dataset.t);
      const ids=secs.map(s=>s.id);
      return {nSec:ids.length, nLink:links.length,
              emptyIds:ids.filter(x=>!x).length,
              orphan:links.filter(t=>!ids.includes(t)).length};
    }""")
    ok_map = mapping["emptyIds"] == 0 and mapping["orphan"] == 0 and mapping["nSec"] > 0
    lines.append(f"  锚点: {mapping['nSec']} 个 / 目录 {mapping['nLink']} 项 / "
                 f"空id {mapping['emptyIds']} / 对不上 {mapping['orphan']}")

    # 断言 2：滚动时高亮确实在变、目录确实在滚
    tops, ons = [], []
    for frac in (0.15, 0.45, 0.8):
        pg.evaluate(f"window.scrollTo(0, document.body.scrollHeight*{frac})")
        pg.wait_for_timeout(500)
        s = pg.evaluate("""()=>{
          const n=document.querySelector('nav');
          const on=document.querySelector('nav a.on');
          return {t:Math.round(n.scrollTop), on:on?on.dataset.t:null};
        }""")
        tops.append(s["t"])
        ons.append(s["on"])
    tracked = all(o is not None for o in ons) and len(set(ons)) > 1
    nav_moved = len(set(tops)) > 1
    lines.append(f"  滚动: navTop={tops} 高亮={ons}")
    ok_scroll = tracked and (nav_moved or not scrollable)

    # 断言 3：点目录能跳到并高亮
    clicked = pg.evaluate("""()=>{
      const ls=[...document.querySelectorAll('nav a')];
      const a=ls[Math.floor(ls.length*0.75)];
      a.dataset.probe=a.dataset.t; a.click(); return a.dataset.t;
    }""")
    pg.wait_for_timeout(800)
    after = pg.evaluate("""()=>{
      const on=document.querySelector('nav a.on');
      return {on:on?on.dataset.t:null, y:Math.round(window.scrollY)};
    }""")
    ok_click = after["on"] is not None and after["y"] > 0
    lines.append(f"  点击 {clicked} -> 高亮 {after['on']}  winY={after['y']}")

    return (ok_map and ok_scroll and ok_click and not errs), lines


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    files = collect(arg)
    if not files:
        print("没找到待测 HTML")
        return 1
    exe = find_browser()
    if not exe:
        print("找不到 Edge/Chrome，无法做真实浏览器测试")
        return 1
    print("浏览器:", exe)
    print("待测:", len(files), "份")
    print()

    fails = 0
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        for f in files:
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            ok, lines = check(pg, f)
            pg.close()
            if not ok:
                fails += 1
            print(("OK  " if ok else "FAIL"), os.path.basename(f))
            for l in lines:
                print(l)
            print()
        b.close()

    print("=" * 50)
    print(f"结果：{len(files) - fails} 通过 / {fails} 失败")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
