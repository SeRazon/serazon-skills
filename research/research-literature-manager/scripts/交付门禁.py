# -*- coding: utf-8 -*-
"""交付门禁：红线 35 的机器判据。

客户给一篇文章，必须交付两件：
  ① 科研文献分类导航库.html（库仪表盘，须含该条目）
  ② 文献精读_<作者>_<年份>_<关键词>.html（该条目的精读网页）
缺任一 -> 退出码 1，禁止宣告完成。
reading.md 为内部母版，只提示、不计入交付。
"""
import argparse
import glob
import os
import sqlite3
import sys

LIB_ROOT = os.environ.get("LITLIB_ROOT") or os.path.join(os.path.expanduser("~"), "Documents", "科研文献库")
DB = os.path.join(LIB_ROOT, "library.db")
DASH = os.path.join(LIB_ROOT, "科研文献分类导航库.html")


def find_entry_dir(pid):
    for cat in ("保留", "不收藏", "未分类"):
        d = os.path.join(LIB_ROOT, cat, pid)
        if os.path.isdir(d):
            return d, cat
    return None, None


def _dashboard_ids(txt):
    """从仪表盘内嵌 JSON 里取出全部条目 id（精确集合，用于精确判定）。
    解析失败返回空集合 —— 由调用方退化为带引号精确匹配，绝不静默放过。

    ★ 为什么要解析 JSON 而不是子串匹配：见 main() 里 ② 号判据的注释。
    """
    import json as _json
    import re as _re
    m = _re.search(r"const\s+DATA\s*=\s*(\{.*?\});?\s*\n", txt, _re.S)
    if not m:
        # 兜底：从 `"id": "xxx"` 形态直接抠
        ids = set(_re.findall(r'"id"\s*:\s*"([^"]+)"', txt))
        return ids
    try:
        data = _json.loads(m.group(1))
    except Exception:
        return set(_re.findall(r'"id"\s*:\s*"([^"]+)"', txt))
    out = set()
    for e in (data.get("entries") or []):
        if isinstance(e, dict) and e.get("id"):
            out.add(str(e["id"]))
    return out


def _dashboard_html_names(txt):
    """从仪表盘内嵌 JSON 里取出全部条目登记的精读 HTML 文件名。"""
    import json as _json
    import re as _re
    names = set(_re.findall(r'"(?:reading_html_name|html_name|reading_html_path)"\s*:\s*"([^"]+)"', txt))
    return set(os.path.basename(n) for n in names if n)


def _visible_text_len(html_path):
    """去掉标签/样式/脚本后，估可见正文字符数（用于识别"壳够大但里面是空的"）。

    ★ 为什么需要：实测 2026-09-21，reading.md 只有 `# 标题`（10 字节）时，
      模板仍产出 7370 字节 HTML，纯字节判据放过。去标签后仅几百字。
    """
    import re as _re
    try:
        t = open(html_path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return -1
    t = _re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", t)
    t = _re.sub(r"(?s)<[^>]+>", " ", t)
    t = _re.sub(r"&[a-zA-Z#0-9]+;", " ", t)
    t = _re.sub(r"\s+", "", t)
    return len(t)


# 精读网页去标签后的正文中文字数下限。
# 依据：红线 17 的"11 板块正文 ≥6,000 中文字"是**成稿**要求；
#       此处的下限只用于识别**空壳**（远低于正常成稿），故取一个宽松值，
#       宁可漏报空壳也不误杀正常短稿。
BODY_MIN_CHARS = 800


def main():
    ap = argparse.ArgumentParser(description="交付门禁：两个交付物缺一即失败")
    ap.add_argument("--id", required=True, help="条目标识")
    args = ap.parse_args()
    pid = args.id

    errs, warns = [], []
    hbody = -1          # 精读网页去标签后的正文长度（-1 = 未测）

    # ① 客户精读 HTML
    edir, cat = find_entry_dir(pid)
    if edir is None:
        print("交付门禁 | 条目：%s" % pid)
        print("  [FAIL] 条目目录不存在（三条分类下都找不到）")
        print("\n结论：不通过（退出码 1）")
        return 1

    htmls = glob.glob(os.path.join(edir, "文献精读_*.html"))
    if not htmls:
        errs.append("客户交付物① 文献精读_*.html 不存在于 %s —— 只入库不算交付" % edir)
        hpath, hsize = None, 0
    elif len(htmls) > 1:
        # 红线 35 说"不增不减不改名"：一个条目目录里出现多个精读 HTML = 命名漂移的残留
        hpath = sorted(htmls)[0]
        hsize = os.path.getsize(hpath)
        errs.append("客户交付物① 出现 %d 个 文献精读_*.html（应恰好 1 个）：%s"
                    % (len(htmls), "、".join(os.path.basename(x) for x in sorted(htmls))))
    else:
        hpath = htmls[0]
        hsize = os.path.getsize(hpath)
        if hsize < 1024:
            errs.append("客户交付物① 存在但过小（%d 字节），疑似空壳" % hsize)
        else:
            # ★ 字节数够了不等于有内容。实测教训（2026-09-21）：
            #   reading.md 只有 10 字节（`# 标题`）时，模板仍会渲染出一个 7370 字节的
            #   "看起来正常"的 HTML —— 壳够大、里面是空的，纯字节判据会放过它。
            #   改为**去标签后的可见正文长度**判据。
            body = _visible_text_len(hpath)
            if body < BODY_MIN_CHARS:
                errs.append("客户交付物① 存在且 %d 字节，但去标签后正文仅 %d 字"
                            "（下限 %d）—— 疑似空壳页面，不算有效交付"
                            % (hsize, body, BODY_MIN_CHARS))
            else:
                hbody = body

    # ② 库仪表盘（须含该条目）
    if not os.path.isfile(DASH):
        errs.append("客户交付物② 科研文献分类导航库.html 不存在于 %s" % LIB_ROOT)
        dsize, has_entry = 0, False
    else:
        dsize = os.path.getsize(DASH)
        txt = open(DASH, encoding="utf-8", errors="ignore").read()
        # ★ 必须做**结构化判定**，不许用 `pid in txt` 子串匹配。
        #   实测教训（2026-09-21）：条目 A100 未收录进仪表盘，但库里另有 A1000，
        #   `"A100" in txt` 因 A1000 含子串 A100 而恒为 True → 假 OK，门禁放过未重建的仪表盘。
        #   还须防止基线上曾被修掉的 `basename(hpath or "")` 假 OK（空串 in 文本 恒 True）。
        ids = _dashboard_ids(txt)
        names = _dashboard_html_names(txt)
        has_entry = False
        if ids:
            # 仪表盘内嵌 JSON 可解析 → 以**精确相等**为唯一判据
            has_entry = (pid in ids) or (hpath and os.path.basename(hpath) in names)
        else:
            # 回退（老版仪表盘无内嵌 JSON）：用带引号的精确形态匹配，仍不用裸子串
            def _exact(s):
                if not s:
                    return False
                return ('"%s"' % s) in txt or ("'%s'" % s) in txt
            has_entry = _exact(pid) or (hpath and _exact(os.path.basename(hpath)))
            if has_entry:
                warns.append("仪表盘未含内嵌 JSON，本次判定退化为「带引号精确匹配」，"
                             "可能仍有极小误判空间（建议重建仪表盘）")
        if not has_entry:
            errs.append("客户交付物② 仪表盘存在，但其中不含该条目（未重建/未收录）")

    # 内部母版（仅提示）
    md = os.path.join(edir, "reading.md")
    if not os.path.isfile(md):
        warns.append("内部母版 reading.md 不存在（不阻断交付，但应留底）")
    mdsize = os.path.getsize(md) if os.path.isfile(md) else 0

    print("=" * 68)
    print("交付门禁  |  红线 35：两个交付物缺一即失败")
    print("=" * 68)
    print("条目：%s  （分类：%s）" % (pid, cat))
    print("-" * 68)
    print("① 客户精读网页 ：%s" % ("OK" if (hpath and hsize >= 1024
                                          and hbody >= BODY_MIN_CHARS) else "FAIL"))
    if hpath:
        print("     %s" % os.path.basename(hpath))
        print("     %d 字节   去标签正文 %s 字（下限 %d）"
              % (hsize, hbody if hbody >= 0 else "?", BODY_MIN_CHARS))
    print("② 库仪表盘     ：%s" % ("OK" if (dsize and has_entry) else "FAIL"))
    print("     科研文献分类导航库.html  %d 字节  含本条目=%s" % (dsize, has_entry))
    print("-" * 68)
    print("（内部留底，不计交付）reading.md：%s  %d 字节" % ("有" if mdsize else "无", mdsize))
    print("-" * 68)

    if warns:
        for w in warns:
            print("[WARN] %s" % w)
    if errs:
        for e in errs:
            print("[FAIL] %s" % e)
        print("\n结论：不通过（退出码 1）——禁止宣告完成")
        return 1

    print("\n结论：通过（退出码 0）——两个交付物齐全，可交付")
    return 0


if __name__ == "__main__":
    sys.exit(main())
