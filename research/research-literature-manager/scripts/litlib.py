# -*- coding: utf-8 -*-
"""科研文献分类导航库（Research Literature Classification Library） —— 本地文献知识库命令行工具。

存储：默认 ~/Documents/科研文献库/（可用环境变量 LITLIB_ROOT 覆盖；单一数据源，按判定结果分子目录 + 多维标签 + SQLite FTS5 全文索引）
（库根目录见 LIB_ROOT 常量）
每篇文献一个 entry 目录，按「保留 / 不收藏 / 未分类」归入对应子文件夹：
    保留/<id>/source.pdf      原文（复制进库，保留原始扩展名）
    保留/<id>/reading.md      11 板块精读
    保留/<id>/meta.json       结构化元数据
    （不收藏/未分类 结构相同）

命令（全部为中文）：
    收文 <源PDF/Word路径> [--id 标识]                复制进库，默认归入 未分类
    归档 --id 标识 [--pdf 原文] [--reading 解读]      归档一篇（meta.json 须已在该 entry 目录）
    判定 --id 标识 --类别 保留|不收藏|未分类           整文件夹搬移到对应分类子目录
    检索 <关键词>                                   全文+标签检索，返回 原文+解读 双路径
    作者 | 期刊 | 年份 [年] | 影响因子 [下限] | 方向 [词] | 第一作者 <名> | 通讯 <名> | 机构 [词]
    统计                                         对话内文本统计
    未匹配                                       列出未匹配到期刊影响因子的期刊
    迁移                                         把旧 papers/ 扁平结构迁移进 未分类/ 子目录
    构建                                         重新生成 科研文献分类导航库.html
"""
import argparse
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
import html
import http.server
from collections import Counter
from datetime import datetime, date

LIB_ROOT = os.environ.get("LITLIB_ROOT") or os.path.join(os.path.expanduser("~"), "Documents", "科研文献库")
DB_PATH = os.path.join(LIB_ROOT, "library.db")
PAPERS_DIR = os.path.join(LIB_ROOT, "papers")
UNMATCHED_PATH = os.path.join(LIB_ROOT, "unmatched.json")
DASHBOARD_PATH = os.path.join(LIB_ROOT, "科研文献分类导航库.html")
CATS = ["保留", "不收藏", "未分类"]


def paper_dir_by_id(pid):
    conn = get_conn(); init_db(conn)
    r = conn.execute("SELECT folder FROM entries WHERE id=?", (pid,)).fetchone()
    conn.close()
    if r and r[0] in CATS:
        return os.path.join(LIB_ROOT, r[0], pid)
    if os.path.isdir(os.path.join(PAPERS_DIR, pid)):
        return os.path.join(PAPERS_DIR, pid)
    for c in CATS:
        if os.path.isdir(os.path.join(LIB_ROOT, c, pid)):
            return os.path.join(LIB_ROOT, c, pid)
    return os.path.join(LIB_ROOT, "未分类", pid)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import jcr_helper
except ImportError as e:
    print(f"【警告】jcr_helper 模块缺失，影响因子相关功能将不可用：{e}")
    jcr_helper = None


# ---------------- DB ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        title TEXT, doi TEXT, year INTEGER, journal TEXT,
        if REAL, jcr_quartile TEXT, jcr_category TEXT, cas_big_class TEXT, cas_top TEXT,
        article_type TEXT, status TEXT,
        first_author TEXT, corresponding_authors TEXT, affiliations TEXT, authors TEXT,
        research_topics TEXT, methods TEXT, models TEXT, pathways TEXT,
        paper_id TEXT, pdf_path TEXT, reading_path TEXT, created TEXT, keep TEXT, folder TEXT, reading_html_path TEXT
    )""")
    conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(id UNINDEXED, text)")
    conn.commit()
    _ensure_columns(conn)


def _ensure_columns(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(entries)").fetchall()]
    if "keep" not in cols:
        conn.execute("ALTER TABLE entries ADD COLUMN keep TEXT DEFAULT '未分类'")
    if "folder" not in cols:
        conn.execute("ALTER TABLE entries ADD COLUMN folder TEXT DEFAULT '未分类'")
    if "reading_html_path" not in cols:
        conn.execute("ALTER TABLE entries ADD COLUMN reading_html_path TEXT")
    # 旧词汇迁移：收藏→保留 / 未定→未分类 / 不保留→不收藏
    conn.execute("UPDATE entries SET keep='保留' WHERE keep='收藏'")
    conn.execute("UPDATE entries SET keep='未分类' WHERE keep='未定'")
    conn.execute("UPDATE entries SET keep='不收藏' WHERE keep='不保留'")
    conn.execute("UPDATE entries SET folder=keep WHERE folder IS NULL OR folder=''")
    conn.commit()


def _j(x):
    return json.dumps(x, ensure_ascii=False) if x is not None else "[]"


def _load_json_field(s):
    try:
        v = json.loads(s) if isinstance(s, str) else s
        return v if isinstance(v, list) else []
    except Exception:
        return []


def _surname(name):
    """从 first_author 字段提取姓氏（英文取最后一个词，中文取全名），去掉括号注释。"""
    name = str(name or '').strip()
    if not name:
        return 'Unknown'
    name = re.sub(r'[（(].*?[）)]', '', name)
    name = name.split('，')[0].split(',')[0].strip()
    en = re.findall(r'[A-Za-z]+', name)
    if en:
        return en[-1]
    return name


def _clean_kw(s, maxlen=25):
    """把关键词/文件名清理成可安全用于文件名的字符串。"""
    s = re.sub(r'[\\/:*?"<>| ]', '', str(s))
    s = re.sub(r'[(（].*?[)）]', '', s)
    return s[:maxlen]


def _reading_html_name(pid, meta):
    """生成面向客户的精读 HTML 文件名：文献精读_<第一作者姓氏>_<年份>_<关键词>.html。

    ★ 命名口径（2026-09-21 定稿，pid 后缀方案已**回退**）：
      每个条目在库里都是**独立目录**（保留/<id>/、未分类/<id>/……），精读网页
      各自躺在自己的 entry 目录内，**不在同一目录下**，因此跨条目"同名覆盖"在
      本库的真实结构里**不会发生**。曾一度在文件名尾部追加条目标识 pid 以求"唯一"，
      实测代价大于收益：① 全库 8 个既有条目命名 100% 与代码不一致（新老两套并存）；
      ② 文件名被 pid 拉到 60+ 字符、中英混杂，可读性明显下降；③ 结构上本无此风险。
      故**回退为纯文章信息命名**，与库内既有 8 篇保持完全一致。
      同一目录内的重复，改由门禁侧兜底（见 交付门禁.py 的"多文件 = FAIL"判定）。
    """
    sur = _surname(meta.get('first_author'))
    year = meta.get('year') or 'YYYY'
    topics = meta.get('research_topics', [])
    if topics:
        kw = _clean_kw(''.join(topics[:2]))
    else:
        m = re.match(r'^[A-Za-z]+\d{4}_(.+)$', pid)
        kw = _clean_kw(m.group(1) if m else pid)
    return f'文献精读_{sur}_{year}_{kw}.html'


def _generate_reading_html(reading_md_path, html_path, meta):
    """调用精读技能的精读转网页模板，生成客户可见的 HTML。"""
    here = os.path.dirname(os.path.abspath(__file__))            # <root>/scripts
    root = os.path.dirname(here)                                 # <root>
    parent = os.path.dirname(root)
    candidates = []
    env = os.environ.get("LIT_READING_TPL")
    if env:
        candidates.append(env)
    # ① 本技能自带模板（合并技能布局）
    candidates.append(os.path.join(root, "templates", "精读转网页.py"))
    # ② 兼容「专家包 / 多技能并列」布局：同级或父级下的精读技能
    for sib in ("research-literature-analyzer", "科研文献精读剖析助手"):
        candidates.append(os.path.join(root, sib, "templates", "精读转网页.py"))
        candidates.append(os.path.join(parent, sib, "templates", "精读转网页.py"))
    # ③ 兜底：扫描同级与父级目录
    for base in (root, parent):
        try:
            for d in sorted(os.listdir(base)):
                candidates.append(os.path.join(base, d, "templates", "精读转网页.py"))
        except OSError:
            pass
    tpl = None
    for c in candidates:
        if os.path.isfile(c):
            tpl = c
            break
    if not tpl:
        print(f"【警告】找不到精读转网页模板，跳过 HTML 生成：{reading_md_path}")
        return False
    title = f"文献精读 · {_surname(meta.get('first_author'))} {meta.get('year') or ''} · {'/'.join(meta.get('research_topics', [])[:2])}"
    cmd = [sys.executable, tpl, reading_md_path, '--out', html_path, '--title', title]

    # —— 把已解析出的影响因子带进精读网页（2026-09-21 补）——
    # 此前 IF 只写进 meta.json / DB，网页上看不到；这里补上页头 IF 徽标。
    # 拿不到 IF 就不传该参数，模板会自动不渲染徽标（向后兼容）。
    _if = meta.get("if")
    if _if is not None:
        cmd += ['--if', str(_if)]
        if meta.get("jcr_quartile"):
            cmd += ['--quartile', str(meta.get("jcr_quartile"))]
        if meta.get("journal"):
            cmd += ['--journal', str(meta.get("journal"))]

    try:
        import subprocess
        r = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if not os.path.isfile(html_path):
            print(f"【警告】模板执行成功但未产出文件：{html_path}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        # ★ 不再静默吞（2026-09-21 自查）：原实现只打一句泛化警告，
        #   模板的真实报错（如"未包含任何一级标题"）全被丢掉，
        #   表现为"归档成功但精读网页缺失"，排查困难。
        err = (e.stderr or e.stdout or "").strip()
        print(f"【警告】精读网页生成失败（退出码 {e.returncode}）：{err[:500]}")
        return False
    except Exception as e:
        print(f"【警告】精读网页生成异常：{type(e).__name__}: {e}")
        return False


# ---------------- save ----------------
def cmd_save(args):
    paper_dir = paper_dir_by_id(args.id)
    cat = None
    for c in CATS:
        if paper_dir == os.path.join(LIB_ROOT, c, args.id):
            cat = c; break
    if cat is None:
        cat = "未分类"
    meta_path = os.path.join(paper_dir, "meta.json")
    if not os.path.isfile(meta_path):
        print(f"【错误】meta.json 不存在：{meta_path}\n请先在该 entry 目录写入 meta.json（含分类字段）")
        return 1
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    os.makedirs(paper_dir, exist_ok=True)
    # 复制原文
    if args.pdf:
        ext = os.path.splitext(args.pdf)[1].lower() or ".pdf"
        dst = os.path.join(paper_dir, "source" + ext)
        # 幂等：若 `--pdf` 指向的正是 entry 内已有的 source.*（重跑归档的常见情形），
        # 直接跳过复制。否则 shutil.copyfile 抛 SameFileError 中断整个归档，
        # 连后面的"生成精读 HTML / 重建仪表盘"都跑不到（2026-09-21 实测）。
        if os.path.abspath(args.pdf) != os.path.abspath(dst):
            shutil.copyfile(args.pdf, dst)
        meta["pdf_path"] = f"{cat}/{args.id}/source{ext}"
    # 自动匹配 IF
    # ★ 顺序铁律（2026-09-21）：必须在「生成精读 HTML」**之前**解析 IF，
    #   否则精读网页拿不到 meta["if"]，页头 IF 徽标永远不渲染。
    #   此前该段位于生成 HTML 之后，导致"归档成功但网页无 IF"。
    journal = meta.get("journal", "")
    ok, info = jcr_helper.resolve(journal)
    if ok and info:
        meta["if"] = info.get("if")
        meta["jcr_quartile"] = info.get("jcr_quartile")
        meta["jcr_category"] = info.get("jcr_category")
        meta["cas_big_class"] = info.get("cas_big_class")
        meta["cas_top"] = info.get("cas_top")
        # 从未匹配清单移除
        _remove_unmatched(journal)
    else:
        meta.setdefault("if", None)
        _add_unmatched(journal)

    # 复制/采用精读（reading.md 为内部母版，不直接呈现给客户）
    reading_rel = f"{cat}/{args.id}/reading.md"
    if args.reading:
        dst = os.path.join(paper_dir, "reading.md")
        # 幂等：若来源已是目标文件（如重跑归档重新生成 HTML），跳过复制，避免 SameFileError
        if os.path.abspath(args.reading) != os.path.abspath(dst):
            shutil.copyfile(args.reading, dst)
        meta["reading_path"] = reading_rel
        # 生成面向客户的精读 HTML，文件名按「文献精读_<第一作者姓氏>_<年份>_<关键词>.html」
        # ★ 先清掉同目录既有 文献精读_*.html（2026-09-21）：文件名由 meta 推导，
        #   meta 改了就会产出新名，不清理则新旧并存 → 交付门禁 FAIL。
        for _old in glob.glob(os.path.join(paper_dir, "文献精读_*.html")):
            try:
                os.remove(_old)
            except OSError:
                pass
        html_name = _reading_html_name(args.id, meta)
        html_path = os.path.join(paper_dir, html_name)
        if _generate_reading_html(dst, html_path, meta):
            meta["reading_html_path"] = f"{cat}/{args.id}/{html_name}"
            meta["reading_html_name"] = html_name
        else:
            meta["reading_html_path"] = None
            meta["reading_html_name"] = None
    elif meta.get("reading_html_path"):
        # 未传 --reading 但库内已有精读网页：按最新 meta 重新渲染一次，
        # 使 IF 徽标等新增字段对既有条目也能生效（不改动 reading.md 本身）。
        # ★ 先清掉同目录既有 文献精读_*.html（2026-09-21 修复）：
        #   文件名由 meta 的 姓氏/年份/关键词 推导，一旦这些字段被改动，
        #   重渲染会生成**新名**文件而导致旧的残留 → 同目录出现 2 个精读网页
        #   → 触发 交付门禁 的"应恰好 1 个"判据（实测 EXIT=1）。
        #   此处按"该条目只有一份精读产物"的契约，先清后写。
        for _old in glob.glob(os.path.join(paper_dir, "文献精读_*.html")):
            try:
                os.remove(_old)
            except OSError:
                pass
        html_name = _reading_html_name(args.id, meta)
        html_path = os.path.join(paper_dir, html_name)
        src_md = os.path.join(paper_dir, "reading.md")
        if os.path.isfile(src_md):
            _generate_reading_html(src_md, html_path, meta)
            if os.path.isfile(html_path):
                meta["reading_html_path"] = f"{cat}/{args.id}/{html_name}"
                meta["reading_html_name"] = html_name

    # 写回 meta.json（含解析后的 IF 字段、keep 状态与相对路径）
    meta.setdefault("keep", cat)
    meta["folder"] = cat
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 入库
    conn = get_conn()
    init_db(conn)
    conn.execute("DELETE FROM entries WHERE id=?", (args.id,))
    conn.execute("DELETE FROM fts WHERE id=?", (args.id,))
    conn.execute("""INSERT INTO entries (
        id,title,doi,year,journal,if,jcr_quartile,jcr_category,cas_big_class,cas_top,
        article_type,status,first_author,corresponding_authors,affiliations,authors,
        research_topics,methods,models,pathways,paper_id,pdf_path,reading_path,created,keep,folder,reading_html_path)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        args.id, meta.get("title"), meta.get("doi"), meta.get("year"), journal,
        meta.get("if"), meta.get("jcr_quartile"), meta.get("jcr_category"),
        meta.get("cas_big_class"), meta.get("cas_top"),
        meta.get("article_type"), meta.get("status"),
        meta.get("first_author"), _j(meta.get("corresponding_authors")),
        _j(meta.get("affiliations")), _j(meta.get("authors")),
        _j(meta.get("research_topics")), _j(meta.get("methods")),
        _j(meta.get("models")), _j(meta.get("pathways")),
        meta.get("paper_id"), meta.get("pdf_path"), meta.get("reading_path"),
        meta.get("created") or date.today().isoformat(),
        meta.get("keep", cat), cat,
        meta.get("reading_html_path")
    ))
    # FTS 全文
    reading_body = ""
    rp = os.path.join(LIB_ROOT, meta.get("reading_path", "")) if meta.get("reading_path") else ""
    if rp and os.path.isfile(rp):
        reading_body = open(rp, "r", encoding="utf-8", errors="ignore").read()
    fts_text = " ".join([
        str(meta.get("title", "")), journal or "",
        " ".join(_load_json_field(meta.get("authors"))),
        " ".join(_load_json_field(meta.get("affiliations"))),
        " ".join(_load_json_field(meta.get("research_topics"))),
        " ".join(_load_json_field(meta.get("methods"))),
        " ".join(_load_json_field(meta.get("models"))),
        " ".join(_load_json_field(meta.get("pathways"))),
        reading_body,
    ])
    conn.execute("INSERT INTO fts(id,text) VALUES (?,?)", (args.id, fts_text))
    conn.commit()
    conn.close()
    print(f"【完成】归档成功：{args.id}")
    print(f"     期刊={journal}  影响因子={meta.get('if')}  {meta.get('jcr_quartile')}  {meta.get('cas_big_class')}  顶刊={meta.get('cas_top')}")
    print(f"     原文：{meta.get('pdf_path')}")
    print(f"     精读母版（内部）：{meta.get('reading_path')}")
    print(f"     精读产物（客户）：{meta.get('reading_html_path')}")
    build_dashboard()
    # 流程内强制（红线 35）：交付门禁。缺任一交付物 -> 归档不视为完成，退出码 1。
    import subprocess
    _gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "交付门禁.py")
    _r = subprocess.run([sys.executable, _gate, "--id", args.id])
    if _r.returncode != 0:
        print("【门禁未过】两个交付物不全，归档不视为完成（退出码 1）。")
        return 1
    return 0


# ---------------- search ----------------
def search_ids(conn, q):
    ids = set()
    like = f"%{q}%"
    rows = conn.execute("""SELECT id FROM entries WHERE
        title LIKE ? OR journal LIKE ? OR authors LIKE ? OR affiliations LIKE ?
        OR research_topics LIKE ? OR methods LIKE ? OR models LIKE ? OR pathways LIKE ?
        OR first_author LIKE ? OR corresponding_authors LIKE ? OR jcr_category LIKE ?
        OR cas_big_class LIKE ?""", (like,)*12).fetchall()
    for r in rows:
        ids.add(r[0])
    # FTS5 兜底（英文多词有效）
    try:
        safe = q.replace('"', '""')
        fts_rows = conn.execute("SELECT id FROM fts WHERE fts MATCH ?", (f'"{safe}"',)).fetchall()
        for r in fts_rows:
            ids.add(r[0])
    except Exception:
        pass
    return ids


def _entry_rows(conn, ids):
    out = []
    for i in ids:
        r = conn.execute("SELECT * FROM entries WHERE id=?", (i,)).fetchone()
        if r:
            out.append(r)
    return out


def cmd_search(args):
    conn = get_conn()
    init_db(conn)
    ids = search_ids(conn, args.query)
    rows = _entry_rows(conn, ids)
    _print_entries(rows)
    conn.close()
    return 0


COLS = ["id","title","doi","year","journal","if","jcr_quartile","jcr_category","cas_big_class","cas_top",
         "article_type","status","first_author","corresponding_authors","affiliations","authors",
         "research_topics","methods","models","pathways","paper_id","pdf_path","reading_path","created","keep","folder","reading_html_path"]


def _print_entries(rows):
    if not rows:
        print("(无匹配文献)")
        return
    for r in rows:
        d = dict(zip(COLS, r))
        print(f"● {d['id']}")
        print(f"    标题: {d['title']}")
        print(f"    期刊: {d['journal']} ({d['year']})  IF={d['if']} {d['jcr_quartile']} {d['cas_big_class']}")
        print(f"    状态: {d['status']}  第一作者: {d['first_author']}")
        print(f"    原文: {d['pdf_path']}")
        print(f"    精读母版: {d['reading_path']}")
        print(f"    精读产物: {d['reading_html_path']}")


# ---------------- 维度列表 ----------------
def _col(conn, name):
    return [r[0] for r in conn.execute(f"SELECT {name} FROM entries").fetchall()]


def cmd_authors(args):
    conn = get_conn(); init_db(conn)
    c = Counter()
    for s in _col(conn, "authors"):
        for a in _load_json_field(s):
            c[a] += 1
    for a, n in c.most_common():
        print(f"{n:3}  {a}")
    conn.close(); return 0


def cmd_journal(args):
    conn = get_conn(); init_db(conn)
    c = Counter(_col(conn, "journal"))
    for j, n in c.most_common():
        print(f"{n:3}  {j}")
    conn.close(); return 0


def cmd_year(args):
    conn = get_conn(); init_db(conn)
    c = Counter(_col(conn, "year"))
    if getattr(args, "year", None) is not None:
        print(f"{args.year}: {c.get(args.year, 0)}")
    else:
        for y in sorted(c):
            print(f"{y}: {c[y]}")
    conn.close(); return 0


def cmd_if(args):
    conn = get_conn(); init_db(conn)
    rows = conn.execute("SELECT id,title,journal,if FROM entries").fetchall()
    rows = [r for r in rows if r[3] is not None and (args.min is None or r[3] >= args.min)]
    rows.sort(key=lambda x: -(x[3] or 0))
    for r in rows:
        print(f"IF={r[3]:<5}  {r[1]}  ({r[2]})")
    conn.close(); return 0


def cmd_topics(args):
    conn = get_conn(); init_db(conn)
    c = Counter()
    for s in _col(conn, "research_topics"):
        for t in _load_json_field(s):
            c[t] += 1
    for t, n in c.most_common():
        print(f"{n:3}  {t}")
    conn.close(); return 0


def cmd_firstauthor(args):
    conn = get_conn(); init_db(conn)
    rows = conn.execute("SELECT id,title,first_author FROM entries WHERE first_author LIKE ?",
                        (f"%{args.name}%",)).fetchall()
    for r in rows:
        print(f"{r[0]}  | 第一作者: {r[2]} | {r[1]}")
    conn.close(); return 0


def cmd_corr(args):
    conn = get_conn(); init_db(conn)
    rows = conn.execute("SELECT id,title,corresponding_authors FROM entries WHERE corresponding_authors LIKE ?",
                        (f"%{args.name}%",)).fetchall()
    for r in rows:
        print(f"{r[0]}  | 通讯: {_load_json_field(r[2])} | {r[1]}")
    conn.close(); return 0


def cmd_affiliations(args):
    conn = get_conn(); init_db(conn)
    c = Counter()
    for s in _col(conn, "affiliations"):
        for a in _load_json_field(s):
            c[a] += 1
    for a, n in c.most_common():
        if args.term.lower() in a.lower():
            print(f"{n:3}  {a}")
    conn.close(); return 0


def cmd_unmatched(args):
    data = _read_unmatched()
    if not data:
        print("(无未匹配期刊)")
        return 0
    for j in data:
        print("未匹配:", j)
    return 0


# ---------------- 分类（保留 / 不收藏 / 未分类） ----------------
def _slug(s):
    s = re.sub(r'\s+', '_', (s or '').strip())
    s = re.sub(r'[\\/:*?"<>|]', '_', s)
    return s[:80] or "doc"

def find_paper_cat(pid):
    # 文件系统优先：以真实位置为准，避免 DB 记录陈旧导致定位错
    for c in CATS:
        if os.path.isdir(os.path.join(LIB_ROOT, c, pid)):
            return c
    if os.path.isdir(os.path.join(PAPERS_DIR, pid)):
        return "papers"
    conn = get_conn(); init_db(conn)
    r = conn.execute("SELECT folder FROM entries WHERE id=?", (pid,)).fetchone()
    conn.close()
    if r and r[0] in CATS:
        return r[0]
    return None

def _reconcile_entry(pid, cat, conn):
    """把单条记录按文件系统真实位置对齐：folder/keep/pdf_path/reading_path/reading_html_path + meta.json。"""
    d = os.path.join(LIB_ROOT, cat, pid) if cat != "papers" else os.path.join(PAPERS_DIR, pid)
    pdf = None; read = None; rhtml = None
    try:
        names = os.listdir(d)
    except Exception:
        names = []
    for fn in names:
        low = fn.lower()
        if low == "meta.json":
            continue
        if low == "reading.md":
            read = f"{cat}/{pid}/{fn}"
        elif low.startswith("文献精读_") and low.endswith(".html"):
            rhtml = f"{cat}/{pid}/{fn}"
        elif pdf is None and (low.startswith("source") or low.endswith((".pdf", ".doc", ".docx", ".txt"))):
            pdf = f"{cat}/{pid}/{fn}"
    # 若目录里只有 reading.md 但没有 HTML，尝试按 meta 自动生成一个（修复旧数据）
    if rhtml is None and read is not None:
        try:
            mp = os.path.join(d, "meta.json")
            if os.path.isfile(mp):
                m = json.load(open(mp, encoding="utf-8"))
                html_name = _reading_html_name(pid, m)
                html_path = os.path.join(d, html_name)
                if os.path.isfile(html_path):
                    rhtml = f"{cat}/{pid}/{html_name}"
                else:
                    if _generate_reading_html(os.path.join(LIB_ROOT, read), html_path, m):
                        rhtml = f"{cat}/{pid}/{html_name}"
        except Exception as e:
            # ★ 不再静默吞（2026-09-21 自查）：本段会在 DB 里写 reading_html_path，
            #   静默失败会让"DB 说有为 None、磁盘却有文件"这类不一致无从察觉。
            print(f"【警告】条目 {pid} 对齐时读取 meta.json / 补生成精读网页失败："
                  f"{type(e).__name__}: {e}")
    conn.execute("UPDATE entries SET folder=?,keep=?,pdf_path=?,reading_path=?,reading_html_path=? WHERE id=?",
                 (cat, cat, pdf, read, rhtml, pid))
    mp = os.path.join(d, "meta.json")
    if os.path.isfile(mp):
        try:
            m = json.load(open(mp, encoding="utf-8"))
            m["folder"] = cat; m["keep"] = cat
            m["pdf_path"] = pdf; m["reading_path"] = read
            if rhtml:
                m["reading_html_path"] = rhtml
                m["reading_html_name"] = os.path.basename(rhtml)
            json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        except Exception as e:
            # ★ 不再静默吞（2026-09-21 自查）：meta.json 写失败 = 磁盘与 DB 脱节。
            print(f"【警告】条目 {pid} 的 meta.json 写回失败：{type(e).__name__}: {e}")

def move_paper(pid, target):
    """把 <id> 整文件夹在 保留/不收藏/未分类（或旧 papers/）之间搬移，并同步 DB + meta.json + 仪表盘。
    以文件系统真实位置为准，先回写 DB，避免历史/中断造成的不一致。"""
    if target not in CATS:
        return False, "非法分类：" + str(target)
    conn = get_conn(); init_db(conn)
    cols = ["id","title","doi","year","journal","if","jcr_quartile","jcr_category","cas_big_class","cas_top",
            "article_type","status","first_author","corresponding_authors","affiliations","authors",
            "research_topics","methods","models","pathways","paper_id","pdf_path","reading_path","created","keep","folder","reading_html_path"]
    r = conn.execute("SELECT " + ",".join(cols) + " FROM entries WHERE id=?", (pid,)).fetchone()
    if not r:
        conn.close(); return False, "文献不存在：" + pid
    d = dict(zip(cols, r))
    # 文件系统真实位置优先
    cur = find_paper_cat(pid) or d.get("folder") or "未分类"
    # 先把 DB 对齐到文件系统真实位置（修复历史/中断造成的错位）
    if cur != d.get("folder"):
        conn.execute("UPDATE entries SET folder=?,keep=? WHERE id=?", (cur, cur, pid))
        conn.commit()
    if cur == target:
        conn.close()
        # 仍以文件系统为准刷新 pdf_path/reading_path/meta
        conn2 = get_conn(); init_db(conn2)
        _reconcile_entry(pid, target, conn2)
        conn2.commit(); conn2.close()
        return True, "已在 " + target
    src = os.path.join(LIB_ROOT, cur, pid) if cur != "papers" else os.path.join(PAPERS_DIR, pid)
    dst = os.path.join(LIB_ROOT, target, pid)
    if not os.path.isdir(src):
        conn.close(); return False, "找不到源文件夹：" + src
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    new_pdf = (f"{target}/{pid}/" + os.path.basename(d["pdf_path"])) if d.get("pdf_path") else None
    new_read = (f"{target}/{pid}/" + os.path.basename(d["reading_path"])) if d.get("reading_path") else None
    new_html = (f"{target}/{pid}/" + os.path.basename(d["reading_html_path"])) if d.get("reading_html_path") else None
    conn.execute("UPDATE entries SET folder=?, pdf_path=?, reading_path=?, reading_html_path=?, keep=? WHERE id=?",
                 (target, new_pdf, new_read, new_html, target, pid))
    conn.commit(); conn.close()
    mp = os.path.join(dst, "meta.json")
    if os.path.isfile(mp):
        try:
            m = json.load(open(mp, encoding="utf-8"))
            m["keep"] = target; m["folder"] = target
            m["pdf_path"] = new_pdf; m["reading_path"] = new_read
            if new_html:
                m["reading_html_path"] = new_html
                m["reading_html_name"] = os.path.basename(new_html)
            json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        except Exception as e:
            # ★ 不再静默吞（2026-09-21 自查）：搬移后 meta 未更新 = 与真实位置脱节。
            print(f"【警告】条目 {pid} 搬移后 meta.json 更新失败：{type(e).__name__}: {e}")
    build_dashboard()
    return True, "已归类到 " + target

def cmd_panding(args):
    ok, msg = move_paper(args.id, args.cat)
    print(("【完成】" if ok else "【错误】") + msg)
    return 0 if ok else 1

def cmd_intake(args):
    src = args.path
    if not os.path.isfile(src):
        print("【错误】源文件不存在：", src); return 1
    base = os.path.splitext(os.path.basename(src))[0]
    pid = args.id or _slug(base)
    cat = "未分类"
    dst = os.path.join(LIB_ROOT, cat, pid)
    if os.path.isdir(dst):
        print("【错误】该 id 已存在：", dst); return 1
    os.makedirs(dst, exist_ok=True)
    ext = os.path.splitext(src)[1].lower()
    sname = "source" + (ext or ".pdf")
    shutil.copyfile(src, os.path.join(dst, sname))
    meta = {"id": pid, "title": base, "keep": cat, "folder": cat,
            "pdf_path": f"{cat}/{pid}/{sname}", "reading_path": None,
            "reading_html_path": None, "created": date.today().isoformat()}
    json.dump(meta, open(os.path.join(dst, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    conn = get_conn(); init_db(conn)
    conn.execute("DELETE FROM entries WHERE id=?", (pid,))
    conn.execute("INSERT INTO entries(id,title,pdf_path,reading_path,created,folder,keep,reading_html_path) VALUES(?,?,?,?,?,?,?,?)",
                 (pid, base, meta["pdf_path"], None, meta["created"], cat, cat, None))
    conn.commit(); conn.close()
    print(f"【完成】收文成功，已归入 未分类：{pid}")
    print(f"     原文：{meta['pdf_path']}")
    print(f"     下一步：生成 reading.md 后运行  归档 --id {pid} --reading <reading.md>")
    build_dashboard()
    return 0

def cmd_migrate(args):
    """一次性迁移：把旧 papers/<id>/ 扁平结构搬进 未分类/<id>/，并修正 DB 路径。"""
    for c in CATS:
        os.makedirs(os.path.join(LIB_ROOT, c), exist_ok=True)
    conn = get_conn(); init_db(conn)
    rows = conn.execute("SELECT id,pdf_path,reading_path,reading_html_path,keep FROM entries").fetchall()
    moved = 0
    for pid, pp, rp, rhp, keep in rows:
        if pp and str(pp).startswith("papers/"):
            src = os.path.join(PAPERS_DIR, pid)
        else:
            cur = find_paper_cat(pid)
            src = os.path.join(LIB_ROOT, cur, pid) if cur in CATS else None
        if not src or not os.path.isdir(src):
            continue
        target = "未分类"
        dst = os.path.join(LIB_ROOT, target, pid)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        new_pdf = (f"{target}/{pid}/" + os.path.basename(pp)) if pp else None
        new_read = (f"{target}/{pid}/" + os.path.basename(rp)) if rp else None
        new_html = (f"{target}/{pid}/" + os.path.basename(rhp)) if rhp else None
        conn.execute("UPDATE entries SET folder=?,pdf_path=?,reading_path=?,reading_html_path=? WHERE id=?",
                     (target, new_pdf, new_read, new_html, pid))
        mp = os.path.join(dst, "meta.json")
        if os.path.isfile(mp):
            try:
                m = json.load(open(mp, encoding="utf-8"))
                m["keep"] = target; m["folder"] = target
                m["pdf_path"] = new_pdf; m["reading_path"] = new_read
                if new_html:
                    m["reading_html_path"] = new_html
                json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception as e:
                # ★ 不再静默吞（2026-09-21 自查）
                print(f"【警告】迁移条目 {pid} 的 meta.json 更新失败：{type(e).__name__}: {e}")
        moved += 1
        print("迁移:", pid, "→", target)
    conn.commit(); conn.close()
    try:
        if os.path.isdir(PAPERS_DIR) and not os.listdir(PAPERS_DIR):
            os.rmdir(PAPERS_DIR); print("已移除空 papers/ 目录")
    except OSError as e:
        # 删不掉空目录不影响迁移结果，但要说出来（原为静默 pass）
        print(f"【提示】空 papers/ 目录未能移除：{e}")
    build_dashboard()
    print(f"【完成】迁移 {moved} 篇至 未分类/")
    return 0


def cmd_fix(args):
    """修复 DB 与文件系统不一致：以真实文件夹位置为准，重算 folder/pdf_path/reading_path/reading_html_path/keep。"""
    conn = get_conn(); init_db(conn)
    fixed = 0
    found = {}
    for c in CATS + (["papers"] if os.path.isdir(PAPERS_DIR) else []):
        base = os.path.join(LIB_ROOT, c) if c != "papers" else PAPERS_DIR
        if not os.path.isdir(base):
            continue
        for pid in os.listdir(base):
            p = os.path.join(base, pid)
            if os.path.isdir(p):
                found[pid] = c
    for pid, cat in found.items():
        _reconcile_entry(pid, cat, conn)
        fixed += 1
        print("修复:", pid, "→", cat)
    conn.commit(); conn.close()
    build_dashboard()
    print(f"【完成】已按文件系统对齐 {fixed} 条记录")
    return 0


def cmd_apply_decisions(args):
    """应用分类决策 JSON（离线写回磁盘）：读取 {id: 类别} 后逐篇搬文件夹 + 重建仪表盘。
    无需常驻服务，纯一次性落盘，最稳。"""
    fpath = args.file or os.path.join(LIB_ROOT, "litlib_decisions.json")
    if not os.path.isfile(fpath):
        print(f"【错误】找不到决策文件：{fpath}")
        return 1
    try:
        obj = json.load(open(fpath, encoding="utf-8"))
    except Exception as e:
        print(f"【错误】JSON 解析失败：{e}")
        return 1
    dec = obj.get("decisions", obj) if isinstance(obj, dict) else {}
    ok = 0; skip = 0; bad = 0
    for pid, cat in dec.items():
        if cat not in CATS:
            print(f"  跳过（非法类别）: {pid} -> {cat}"); bad += 1; continue
        res, msg = move_paper(pid, cat)
        if res:
            ok += 1; print(f"  已归类: {pid} -> {cat}")
        else:
            skip += 1; print(f"  跳过: {pid} ({msg})")
    build_dashboard()
    print(f"【完成】应用决策：成功 {ok} / 跳过 {skip} / 非法 {bad}")
    return 0


# ---------------- 本地服务（仪表盘持久化接口，可选） ----------------
class _DashHandler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, payload, ctype="application/json; charset=utf-8"):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/科研文献分类导航库.html"):
            try:
                data = open(DASHBOARD_PATH, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/keep":
            try:
                n = int(self.headers.get("Content-Length", 0) or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                pid = body.get("id"); state = body.get("state")
                if pid and state in CATS:
                    conn = get_conn(); init_db(conn)
                    ok = conn.execute("SELECT id FROM entries WHERE id=?", (pid,)).fetchone()
                    if not ok:
                        conn.close(); self._send(404, {"ok": False, "msg": "not found"}); return
                    conn.close()
                    ok2, msg = move_paper(pid, state)
                    self._send(200, {"ok": ok2, "state": state, "msg": msg})
                else:
                    self._send(400, {"ok": False, "msg": "bad request"})
            except Exception as e:
                self._send(500, {"ok": False, "msg": str(e)})
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


def cmd_serve(args):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), _DashHandler)
    print(f"【文献库服务】已启动：http://127.0.0.1:{args.port}/科研文献分类导航库.html")
    print("（该地址下仪表盘的 保留/不收藏/未分类 按钮会直接搬移文件并写入文献库；按 Ctrl+C 停止）")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


# ---------------- stats ----------------
def cmd_stats(args):
    conn = get_conn(); init_db(conn)
    rows = conn.execute("SELECT * FROM entries").fetchall()
    cols = ["id","title","doi","year","journal","if","jcr_quartile","jcr_category","cas_big_class","cas_top",
            "article_type","status","first_author","corresponding_authors","affiliations","authors",
            "research_topics","methods","models","pathways","paper_id","pdf_path","reading_path","created","keep","folder","reading_html_path"]
    n = len(rows)
    print(f"总文献数: {n}")
    status_c = Counter(r[cols.index("status")] for r in rows)
    print("状态: " + "  ".join(f"{k}={v}" for k, v in status_c.items()))
    ifs = [r[cols.index("if")] for r in rows if r[cols.index("if")] is not None]
    if ifs:
        print(f"影响因子: 均={sum(ifs)/len(ifs):.2f}  最高={max(ifs)}  最低={min(ifs)}")
    print("\n--- 年份分布 ---")
    for y, c in sorted(Counter(r[cols.index("year")] for r in rows).items()):
        print(f"  {y}: {c}")
    print("\n--- 作者频次 Top ---")
    ac = Counter()
    for r in rows:
        for a in _load_json_field(r[cols.index("authors")]):
            ac[a] += 1
    for a, c in ac.most_common(10):
        print(f"  {c:3}  {a}")
    print("\n--- 机构分布 ---")
    afc = Counter()
    for r in rows:
        for a in _load_json_field(r[cols.index("affiliations")]):
            afc[a] += 1
    for a, c in afc.most_common():
        print(f"  {c:3}  {a}")
    print("\n--- 研究方向 Top ---")
    tc = Counter()
    for r in rows:
        for t in _load_json_field(r[cols.index("research_topics")]):
            tc[t] += 1
    for t, c in tc.most_common(15):
        print(f"  {c:3}  {t}")
    print("\n--- 期刊分布 ---")
    for j, c in Counter(r[cols.index("journal")] for r in rows).most_common():
        print(f"  {c:3}  {j}")
    conn.close(); return 0


# ---------------- unmatched io ----------------
def _read_unmatched():
    if os.path.isfile(UNMATCHED_PATH):
        try:
            return json.load(open(UNMATCHED_PATH, encoding="utf-8"))
        except Exception:
            return []
    return []


def _add_unmatched(journal):
    if not journal:
        return
    data = _read_unmatched()
    if journal not in data:
        data.append(journal)
        json.dump(data, open(UNMATCHED_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _remove_unmatched(journal):
    data = _read_unmatched()
    if journal in data:
        data.remove(journal)
        json.dump(data, open(UNMATCHED_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


# ---------------- dashboard ----------------
def build_dashboard():
    conn = get_conn(); init_db(conn)
    rows = conn.execute("SELECT * FROM entries").fetchall()
    cols = ["id","title","doi","year","journal","if","jcr_quartile","jcr_category","cas_big_class","cas_top",
            "article_type","status","first_author","corresponding_authors","affiliations","authors",
            "research_topics","methods","models","pathways","paper_id","pdf_path","reading_path","created","keep","folder","reading_html_path"]
    entries = []
    for r in rows:
        d = dict(zip(cols, r))
        for k in ["authors","affiliations","research_topics","methods","models","pathways","corresponding_authors"]:
            d[k] = _load_json_field(d.get(k))
        rd = d.get("reading_path")
        if rd and os.path.isfile(os.path.join(LIB_ROOT, rd)):
            try:
                d["reading_md"] = open(os.path.join(LIB_ROOT, rd), encoding="utf-8").read()
            except Exception:
                d["reading_md"] = ""
        else:
            d["reading_md"] = ""
        pdf = d.get("pdf_path")
        if pdf:
            d["pdf_url"] = "file:///" + os.path.abspath(os.path.join(LIB_ROOT, pdf)).replace("\\", "/")
        else:
            d["pdf_url"] = ""
        rhtml = d.get("reading_html_path")
        if rhtml and os.path.isfile(os.path.join(LIB_ROOT, rhtml)):
            d["reading_html_url"] = "file:///" + os.path.abspath(os.path.join(LIB_ROOT, rhtml)).replace("\\", "/")
        else:
            d["reading_html_url"] = ""
        entries.append(d)
    conn.close()

    ac = Counter()
    afc = Counter()
    tc = Counter()
    mc = Counter()
    mlc = Counter()
    pc = Counter()
    jc = Counter()
    yc = Counter()
    for e in entries:
        for a in e["authors"]: ac[a] += 1
        for a in e["affiliations"]: afc[a] += 1
        for t in e["research_topics"]: tc[t] += 1
        for m in e["methods"]: mc[m] += 1
        for m in e["models"]: mlc[m] += 1
        for p in e["pathways"]: pc[p] += 1
        jc[e["journal"]] += 1
        yc[e["year"]] += 1

    ifs = [e["if"] for e in entries if e["if"] is not None]
    data = {
        "entries": entries,
        "total": len(entries),
        "status": dict(Counter(e["status"] for e in entries)),
        "authors": ac.most_common(),
        "affiliations": afc.most_common(),
        "topics": tc.most_common(),
        "methods": mc.most_common(),
        "models": mlc.most_common(),
        "pathways": pc.most_common(),
        "journals": jc.most_common(),
        "years": sorted(((y, c) for y, c in yc.items() if y is not None), key=lambda x: x[0]),
        "if_avg": (sum(ifs)/len(ifs)) if ifs else 0,
        "if_max": max(ifs) if ifs else 0,
        "if_min": min(ifs) if ifs else 0,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    tpl = DASHBOARD_TPL
    out = tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"【完成】仪表盘已生成：{DASHBOARD_PATH}（文献 {len(entries)} 篇）")


def cmd_build(args):
    build_dashboard()
    return 0


# ---------------- CLI ----------------
def main():
    p = argparse.ArgumentParser(prog="科研文献分类导航库（Research Literature Classification Library）", description="本地文献知识库 · 中文命令行")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("归档"); sp.add_argument("--id", required=True); sp.add_argument("--pdf"); sp.add_argument("--reading"); sp.set_defaults(func=cmd_save)
    sp = sub.add_parser("检索"); sp.add_argument("query"); sp.set_defaults(func=cmd_search)
    sp = sub.add_parser("作者"); sp.set_defaults(func=cmd_authors)
    sp = sub.add_parser("期刊"); sp.set_defaults(func=cmd_journal)
    sp = sub.add_parser("年份"); sp.add_argument("year", type=int, nargs="?"); sp.set_defaults(func=cmd_year)
    sp = sub.add_parser("影响因子"); sp.add_argument("min", type=float, nargs="?"); sp.set_defaults(func=cmd_if)
    sp = sub.add_parser("方向"); sp.add_argument("term", nargs="?", default=""); sp.set_defaults(func=cmd_topics)
    sp = sub.add_parser("第一作者"); sp.add_argument("name"); sp.set_defaults(func=cmd_firstauthor)
    sp = sub.add_parser("通讯"); sp.add_argument("name"); sp.set_defaults(func=cmd_corr)
    sp = sub.add_parser("机构"); sp.add_argument("term", nargs="?", default=""); sp.set_defaults(func=cmd_affiliations)
    sp = sub.add_parser("统计"); sp.set_defaults(func=cmd_stats)
    sp = sub.add_parser("未匹配"); sp.set_defaults(func=cmd_unmatched)
    sp = sub.add_parser("构建"); sp.set_defaults(func=cmd_build)
    sp = sub.add_parser("收文"); sp.add_argument("path"); sp.add_argument("--id"); sp.set_defaults(func=cmd_intake)
    sp = sub.add_parser("判定"); sp.add_argument("--id", required=True); sp.add_argument("--类别", dest="cat", required=True, choices=CATS); sp.set_defaults(func=cmd_panding)
    sp = sub.add_parser("保留"); sp.add_argument("--id", required=True); sp.set_defaults(func=cmd_panding, cat="保留")
    sp = sub.add_parser("不收藏"); sp.add_argument("--id", required=True); sp.set_defaults(func=cmd_panding, cat="不收藏")
    sp = sub.add_parser("未分类"); sp.add_argument("--id", required=True); sp.set_defaults(func=cmd_panding, cat="未分类")
    sp = sub.add_parser("迁移"); sp.set_defaults(func=cmd_migrate)
    sp = sub.add_parser("修复"); sp.set_defaults(func=cmd_fix)
    sp = sub.add_parser("应用决策", aliases=["apply"]); sp.add_argument("--file", default=None); sp.set_defaults(func=cmd_apply_decisions)
    sp = sub.add_parser("服务", aliases=["serve"]); sp.add_argument("--port", type=int, default=8788); sp.set_defaults(func=cmd_serve)

    args = p.parse_args()
    if not args.cmd:
        p.print_help(); return 1
    return args.func(args)


DASHBOARD_TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>科研文献分类导航库（Research Literature Classification Library） · 总览</title>
<style>
:root{
  --bg:#0e1116; --panel:#161b22; --panel2:#1c232c; --border:#2a323d;
  --txt:#d7e0ea; --dim:#8b97a6; --accent:#34d3c4; --accent2:#4a9eff; --accent3:#7c9cff;
  --warn:#ffb454;
}
*{box-sizing:border-box}
body{margin:0;display:flex;height:100vh;overflow:hidden;
  background:linear-gradient(160deg,#0e1116,#10161d 60%,#0e1116);color:var(--txt);
  font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.5}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
.btn{background:linear-gradient(90deg,var(--accent),var(--accent2));color:#06222a;border:none;
  border-radius:8px;padding:7px 12px;font-size:12.5px;font-weight:600;cursor:pointer;white-space:nowrap}
.btn:hover{filter:brightness(1.08)}
.btn.ghost{background:var(--panel2);color:var(--txt);border:1px solid var(--border)}
.kbd{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);
  border-radius:4px;padding:0 5px;font-size:10.5px;font-weight:600;margin-left:4px;font-family:ui-monospace,monospace}
.muted{color:var(--dim);font-size:12px}
.tag{display:inline-block;background:var(--panel2);border:1px solid var(--border);border-radius:20px;
  padding:1px 9px;margin:1px 3px 1px 0;font-size:11px;color:var(--dim)}

/* 左栏 */
#sidebar{width:340px;flex:0 0 340px;display:flex;flex-direction:column;
  background:var(--panel);border-right:1px solid var(--border);height:100vh}
.sb-head{padding:16px 16px 12px;border-bottom:1px solid var(--border);
  background:radial-gradient(600px 140px at 10% -30%,rgba(52,211,196,.18),transparent)}
.t1{font-size:17px;font-weight:700;background:linear-gradient(90deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.t2{color:var(--dim);font-size:11.5px;margin-top:4px}
#sb-search{padding:12px 14px;border-bottom:1px solid var(--border);display:flex;gap:8px}
#sb-search input{flex:1;background:var(--panel2);border:1px solid var(--border);color:var(--txt);
  border-radius:8px;padding:8px 10px;font-size:13px;min-width:0}
#nav{flex:1;overflow-y:auto;padding:10px 8px}
.nav-group{margin:7px 4px;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--panel2)}
.ng-title{font-size:12.5px;color:var(--txt);font-weight:600;padding:8px 10px;border-left:3px solid var(--accent);
  display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none}
.ng-title:hover{background:rgba(52,211,196,.08)}
.ng-title .en{color:var(--dim);font-weight:400;font-size:11px}
.ng-arrow{color:var(--accent);font-size:11px;margin-right:6px;display:inline-block;width:10px}
.ng-cnt{color:var(--dim);font-size:11px}
.nav-items{padding:3px 4px 7px}
.nav-item{display:flex;justify-content:space-between;align-items:center;cursor:pointer;
  padding:3px 10px;border-radius:6px;font-size:12.5px;color:var(--dim)}
.nav-item:hover{background:var(--panel);color:var(--txt)}
.nav-item.active{background:linear-gradient(90deg,rgba(52,211,196,.22),transparent);color:var(--accent);font-weight:600}
.nav-item .cnt{color:var(--dim);font-size:11px}

/* 分隔条（可左右拖动） */
#resizer{width:6px;flex:0 0 6px;cursor:col-resize;background:var(--border);position:relative;transition:background .15s}
#resizer:hover,#resizer.drag{background:linear-gradient(180deg,var(--accent),var(--accent2))}

/* 右栏 */
#main{flex:1;overflow-y:auto;padding:20px 26px;height:100vh}
.cards{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:14px 18px;min-width:118px;flex:1}
.card .n{font-size:24px;font-weight:700;background:linear-gradient(90deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.card .l{color:var(--dim);font-size:12px;margin-top:2px}
.section{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:16px 20px;margin:16px 0}
.section h2{margin:0 0 12px;font-size:15px;border-left:3px solid var(--accent);padding-left:10px}
.bar{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}
.bar .name{width:240px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .track{flex:1;background:var(--panel2);border-radius:6px;height:18px;overflow:hidden}
.bar .fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px}
.bar .v{width:40px;text-align:right;color:var(--txt)}
.cloud{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:baseline}
.cloud span{cursor:pointer;transition:.15s}
.cloud span:hover{color:var(--accent)}

/* 右栏结果列表 */
#resultView{display:none}
.result-head{font-size:14px;color:var(--dim);margin:2px 0 14px;line-height:1.6}
.result-head b{color:var(--accent)}
.paper{padding:10px 12px;border:1px solid var(--border);border-radius:10px;margin:8px 0;cursor:pointer;
  background:var(--panel2);transition:.12s}
.paper:hover{border-color:var(--accent)}
.p-title{font-size:13.5px;color:var(--txt);font-weight:600;line-height:1.35}
.p-meta{font-size:11px;color:var(--dim);margin:4px 0}
.p-tags{margin-top:3px}
.empty{color:var(--dim);padding:18px;text-align:center;font-size:13px}

/* 收藏状态按钮 */
.keep-row{display:flex;gap:5px;margin:6px 0 2px;flex-wrap:wrap}
.keep-btn{background:none;border:1px solid #3a4654;border-radius:6px;color:#8b97a6;cursor:pointer;
  font-size:11.5px;padding:2px 10px;line-height:1.4;transition:.12s}
.keep-btn:hover{border-color:var(--accent);color:var(--accent)}
.keep-btn.active{color:#06222a;border-color:transparent;font-weight:600}
.keep-btn[data-state="保留"].active{background:linear-gradient(90deg,var(--accent),var(--accent2))}
.keep-btn[data-state="未分类"].active{background:#2a323d;color:var(--txt)}
.keep-btn[data-state="不收藏"].active{background:#5a2b2b;color:#ff9b9b;border-color:#ff9b9b}
.paper.sel{outline:2px solid #34d3c4;outline-offset:2px}

/* 精读详情 */
.d-head{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:16px}
.d-head h2{margin:0 0 8px;font-size:19px;line-height:1.35}
.d-meta{color:var(--dim);font-size:13px;margin-bottom:8px}
.d-row{font-size:13px;margin:3px 0}
.d-tags{margin:8px 0 10px}
.d-links{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.reading{font-size:14px;line-height:1.7}
.reading h1{font-size:22px;margin:18px 0 10px;background:linear-gradient(90deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.reading h2{font-size:18px;margin:18px 0 8px;padding-left:10px;border-left:3px solid var(--accent)}
.reading h3{font-size:15.5px;margin:14px 0 6px;color:var(--accent)}
.reading h4{font-size:14px;margin:12px 0 5px;color:var(--txt)}
.reading p{margin:8px 0}
.reading ul,.reading ol{margin:8px 0;padding-left:24px}
.reading li{margin:3px 0}
.reading blockquote{margin:10px 0;padding:8px 14px;border-left:3px solid var(--warn);
  background:var(--panel2);color:var(--dim);border-radius:0 8px 8px 0}
.reading code{background:var(--panel2);border:1px solid var(--border);border-radius:5px;padding:1px 5px;font-size:12.5px}
.reading table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}
.reading th,.reading td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}
.reading th{color:var(--dim);background:var(--panel2)}
.reading hr{border:none;border-top:1px solid var(--border);margin:16px 0}
@media(max-width:900px){#sidebar{width:260px;flex-basis:260px}.bar .name{width:150px}}
</style>
</head>
<body>
<div id="sidebar">
  <div class="sb-head">
    <div class="t1">科研文献分类导航库（Research Literature Classification Library）</div>
    <div class="t2" id="gen"></div>
  </div>
  <div id="sb-search">
    <input id="q" placeholder="搜索分类 / 文献（标题·作者·机构·方向·方法…）">
    <button id="reset" class="btn ghost">统计总览</button>
  </div>
  <div id="nav"></div>
</div>
<div id="resizer"></div>
<div id="main">
  <div id="statsView">
    <div id="cards" class="cards"></div>
    <div id="decisionBar" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0 4px">
      <button id="toggleDiscarded" class="btn ghost" style="white-space:nowrap"></button>
      <button id="exportDecisions" class="btn ghost" style="white-space:nowrap">导出分类决策</button>
      <button id="importDecisions" class="btn ghost" style="white-space:nowrap">导入分类决策</button>
      <input id="importFile" type="file" accept="application/json,.json" style="display:none">
      <span id="decisionHint" style="font-size:12px;opacity:.7"></span>
    </div>
    <div class="section"><h2>作者频次 Top (authors)</h2><div id="authors" class="bars"></div></div>
    <div class="section"><h2>机构分布 (affiliations)</h2><div id="affs" class="bars"></div></div>
    <div class="section"><h2>研究方向 (research_topics)</h2><div id="topics" class="bars"></div></div>
    <div class="section"><h2>技术方法 (methods)</h2><div id="methods" class="bars"></div></div>
    <div class="section"><h2>模型 / 物种 (models)</h2><div id="models" class="bars"></div></div>
    <div class="section"><h2>信号通路 (pathways)</h2><div id="pathways" class="bars"></div></div>
    <div class="section"><h2>期刊分布 (journals)</h2><div id="journals" class="bars"></div></div>
    <div class="section"><h2>发表年份 (years)</h2><div id="years" class="bars"></div></div>
    <div class="section"><h2>影响因子分布 (if)</h2><div id="ifbars" class="bars"></div></div>
    <div class="section"><h2>标签云（全部维度合并）</h2><div id="cloud" class="cloud"></div></div>
  </div>
  <div id="resultView">
    <button id="backStats" class="btn">← 返回统计总览 <span class="kbd">Backspace</span></button>
    <div class="result-head" id="resultHead"></div>
    <div id="resultList"></div>
  </div>
  <div id="detailView" style="display:none">
    <button id="back" class="btn">← 返回结果列表 <span class="kbd">Backspace</span></button>
    <div id="detail" style="margin-top:14px"></div>
  </div>
</div>
<script>
const DATA = /*__DATA__*/;
document.getElementById('gen').textContent = '生成于 '+DATA.generated+' · 共 '+DATA.total+' 篇';

const DIMS = [
  {dim:'research_topics', label:'研究方向', en:'research_topics'},
  {dim:'methods', label:'技术方法', en:'methods'},
  {dim:'authors', label:'作者', en:'authors'},
  {dim:'affiliations', label:'机构', en:'affiliations'},
  {dim:'models', label:'模型 / 物种', en:'models'},
  {dim:'pathways', label:'信号通路', en:'pathways'},
  {dim:'journal', label:'期刊', en:'journal'},
  {dim:'year', label:'年份', en:'year'},
  {dim:'ifbucket', label:'影响因子', en:'if'},
  {dim:'status', label:'状态', en:'status'},
];
// 默认折叠：仅展开最常用的三个（研究方向/技术方法/作者），其余可点开
const COLLAPSED_DEFAULT = new Set(['affiliations','models','pathways','journal','year','ifbucket','status']);
let collapsed = new Set(COLLAPSED_DEFAULT);

function ifBucket(v){ if(v==null) return 'IF 未知'; if(v>=10) return 'IF ≥ 10'; if(v>=5) return '5 ≤ IF < 10'; return 'IF < 5'; }
function entryVals(e, dim){
  if(dim==='journal') return e.journal?[String(e.journal)]:[];
  if(dim==='year') return (e.year==null)?[]:[String(e.year)];
  if(dim==='status') return e.status?[e.status]:[];
  if(dim==='ifbucket') return [ifBucket(e.if)];
  return e[dim]||[];
}
function dimCounts(dim){
  const c={};
  DATA.entries.forEach(e=>{ entryVals(e,dim).forEach(v=>{c[v]=(c[v]||0)+1;}); });
  return Object.entries(c).sort((a,b)=>b[1]-a[1]);
}
let activeFilter=null;
let query='';
let currentView='stats';
let currentList=[];
let selIdx=-1;
let showDiscarded=false;
let currentDetailId=null;
// 收藏状态：DB 为真源；file:// 下用 localStorage 兜底
let keepOverride = loadKeepOverride();
function loadKeepOverride(){ try{ return JSON.parse(localStorage.getItem('litlib_keep')||'{}'); }catch(e){ return {}; } }
function saveKeepOverride(){ try{ localStorage.setItem('litlib_keep', JSON.stringify(keepOverride)); }catch(e){} }
function getKeep(e){ return keepOverride[e.id] || e.keep || '未分类'; }
function keepCountsNow(){ const c={保留:0,不收藏:0,未分类:0}; DATA.entries.forEach(e=>{ const k=getKeep(e); c[k]=(c[k]||0)+1; }); return c; }
async function setKeep(id, state){
  keepOverride[id]=state; saveKeepOverride();
  const e=DATA.entries.find(x=>x.id===id); if(e) e.keep=state;
  if(location.protocol==='http:' || location.protocol==='https:'){
    try{ await fetch('/api/keep',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,state})}); }
    catch(err){ /* 离线：仅保留 localStorage */ }
  }
  renderNav(); renderCards();
  if(currentView==='detail' && currentDetailId===id){ showDetail(id); }
  else { updateRight(); }
}
// 导出分类决策：把当前选择导出为 JSON（"复制"），供离线脚本写回磁盘
function exportDecisions(){
  const obj = { _note: '科研文献分类导航库（Research Literature Classification Library）·分类决策；把本文件丢进 WorkBuddy 对话框，让 AI 运行「应用决策」命令即可写回磁盘（无需任何 bat）', decisions: keepOverride };
  const blob = new Blob([JSON.stringify(obj, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'litlib_decisions.json';
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(a.href);
  const hint=document.getElementById('decisionHint');
  if(hint) hint.textContent = '已导出 litlib_decisions.json（' + Object.keys(keepOverride).length + ' 条）';
}
// 导入分类决策：从 JSON 读回选择（"粘贴"回网页）
function importDecisions(file){
  const reader = new FileReader();
  reader.onload = function(){
    try{
      const obj = JSON.parse(reader.result);
      const dec = obj.decisions || obj;
      Object.assign(keepOverride, dec);
      saveKeepOverride();
      renderNav(); renderCards(); updateRight();
      const hint=document.getElementById('decisionHint');
      if(hint) hint.textContent = '已导入 ' + Object.keys(dec).length + ' 条决策';
    }catch(err){ alert('导入失败：' + err.message); }
  };
  reader.readAsText(file);
}
function matchEntry(e){
  const keep=getKeep(e);
  if(activeFilter && activeFilter.special==='keep'){
    if(keep!==activeFilter.value) return false;
  } else if(!showDiscarded && keep==='不收藏'){
    return false;
  }
  if(activeFilter && activeFilter.special!=='keep'){
    if(!entryVals(e,activeFilter.dim).includes(activeFilter.value)) return false;
  }
  if(query){
    const hay=[e.title,e.journal,e.first_author,...(e.authors||[]),...(e.affiliations||[]),
      ...(e.research_topics||[]),...(e.methods||[]),...(e.models||[]),...(e.pathways||[])].join(' ').toLowerCase();
    if(!hay.includes(query.toLowerCase())) return false;
  }
  return true;
}
function renderNav(){
  const nav=document.getElementById('nav');
  const kc=keepCountsNow();
  const keepGroup = `<div class="nav-group">
      <div class="ng-title"><span><span class="ng-arrow">▾</span>分类 (分类)</span><span class="ng-cnt">${DATA.total}</span></div>
      <div class="nav-items">${['保留','未分类','不收藏'].map(s=>{
        const act=(activeFilter && activeFilter.special==='keep' && activeFilter.value===s)?' active':'';
        return `<div class="nav-item${act}" data-keep="${s}"><span>${s}</span><span class="cnt">${kc[s]||0}</span></div>`;
      }).join('')}</div>
    </div>`;
  nav.innerHTML = keepGroup + DIMS.map(g=>{
    const items=dimCounts(g.dim);
    const vis = query ? items.filter(([k])=>k.toLowerCase().includes(query.toLowerCase())) : items;
    if(vis.length===0) return '';
    const isCol = collapsed.has(g.dim);
    const html = vis.map(([k,v])=>{
      const act = activeFilter && activeFilter.dim===g.dim && activeFilter.value===k ? ' active':'';
      return `<div class="nav-item${act}" data-dim="${g.dim}" data-val="${k}"><span>${k}</span><span class="cnt">${v}</span></div>`;
    }).join('');
    const arrow = isCol ? '▸' : '▾';
    return `<div class="nav-group">
      <div class="ng-title" data-dim="${g.dim}"><span><span class="ng-arrow">${arrow}</span>${g.label} <span class="en">(${g.en})</span></span><span class="ng-cnt">${items.length}</span></div>
      <div class="nav-items" style="${isCol?'display:none':''}">${html}</div>
    </div>`;
  }).join('');
  nav.querySelectorAll('.ng-title').forEach(el=>{
    el.addEventListener('click',()=>{
      const dim=el.dataset.dim;
      if(collapsed.has(dim)) collapsed.delete(dim); else collapsed.add(dim);
      renderNav();
    });
  });
  nav.querySelectorAll('.nav-item[data-dim]').forEach(el=>{
    el.addEventListener('click',ev=>{
      ev.stopPropagation();
      const dim=el.dataset.dim, val=el.dataset.val;
      if(activeFilter && activeFilter.dim===dim && activeFilter.value===val) activeFilter=null;
      else activeFilter={dim,value:val};
      renderNav(); updateRight();
    });
  });
  nav.querySelectorAll('.nav-item[data-keep]').forEach(el=>{
    el.addEventListener('click',ev=>{
      ev.stopPropagation();
      const s=el.dataset.keep;
      if(activeFilter && activeFilter.special==='keep' && activeFilter.value===s) activeFilter=null;
      else activeFilter={special:'keep',value:s};
      renderNav(); updateRight();
    });
  });
}
function keepButtons(id){
  const ent=DATA.entries.find(x=>x.id===id)||{id,keep:'未分类'};
  const cur=getKeep(ent);
  return `<div class="keep-row">${['保留','不收藏','未分类'].map(s=>
    `<button class="keep-btn${(cur===s)?' active':''}" data-keep-btn="${id}" data-state="${s}">${s}</button>`).join('')}</div>`;
}
function bindKeepButtons(root){
  root.querySelectorAll('.keep-btn').forEach(b=>{
    b.addEventListener('click',ev=>{ ev.stopPropagation(); setKeep(b.dataset.keepBtn, b.dataset.state); });
  });
}
function paperCard(e, idx){
  const sel = (idx===selIdx)?' sel':'';
  return `<div class="paper${sel}" data-id="${e.id}" data-idx="${idx}">
    ${keepButtons(e.id)}
    <div class="p-title">${e.title}</div>
    <div class="p-meta">${e.journal} · ${e.year} · IF ${e.if!=null?e.if:'—'} · ${e.jcr_quartile||''}</div>
    <div class="p-tags">${(e.research_topics||[]).slice(0,6).map(t=>`<span class="tag">${t}</span>`).join('')}</div>
  </div>`;
}
function updateRight(){
  const filtering = activeFilter || query;
  if(!filtering){ currentView='stats'; showView('stats'); return; }
  currentView='result'; showView('result');
  const rows=DATA.entries.filter(matchEntry);
  currentList = rows;
  const head=[];
  if(activeFilter){ head.push(activeFilter.special==='keep' ? '<b>分类：'+activeFilter.value+'</b>' : '<b>'+activeFilter.value+'</b>'); }
  if(query) head.push('搜索：'+query);
  document.getElementById('resultHead').innerHTML='匹配文献 <b>'+rows.length+'</b> 篇'+(head.length?'　·　'+head.join('　·　'):'');
  document.getElementById('resultList').innerHTML = rows.map((e,i)=>paperCard(e,i)).join('') || '<div class="empty">无匹配文献</div>';
  if(selIdx<0 || selIdx>=rows.length) selIdx=0;
  document.getElementById('resultList').querySelectorAll('.paper').forEach(el=>{
    el.addEventListener('click',ev=>{ if(ev.target.closest('.keep-btn')) return; showDetail(el.dataset.id); });
  });
  bindKeepButtons(document.getElementById('resultList'));
}
function showView(v){
  document.getElementById('statsView').style.display = v==='stats'?'block':'none';
  document.getElementById('resultView').style.display = v==='result'?'block':'none';
  if(v!=='detail') document.getElementById('detailView').style.display='none';
}
function showDetail(id){
  const e=DATA.entries.find(x=>x.id===id);
  if(!e) return;
  currentDetailId=id;
  selIdx = currentList.findIndex(x=>x.id===id);
  currentView='detail';
  document.getElementById('statsView').style.display='none';
  document.getElementById('resultView').style.display='none';
  document.getElementById('detailView').style.display='block';
  const tags=[...(e.research_topics||[]),...(e.methods||[]),...(e.models||[]),...(e.pathways||[])].map(t=>`<span class="tag">${t}</span>`).join('');
  const d=document.getElementById('detail');
  d.innerHTML=`
    <div class="d-head">
      <h2>${e.title}</h2>
      <div class="d-meta">${[e.journal, e.year, 'IF '+(e.if!=null?e.if:'—'), e.jcr_quartile, e.cas_big_class].filter(Boolean).join(' · ')}</div>
      <div class="d-row"><b>作者：</b>${(e.authors||[]).join('、')}</div>
      <div class="d-row"><b>第一作者：</b>${e.first_author||'—'}　<b>通讯：</b>${(e.corresponding_authors||[]).join('、')}</div>
      <div class="d-row"><b>机构：</b>${(e.affiliations||[]).join('、')}</div>
      <div class="d-tags">${tags}</div>
      <div class="d-links">
        ${e.pdf_url?`<a class="btn" href="${e.pdf_url}" target="_blank">打开原文 PDF</a>`:''}
        ${e.reading_html_url?`<a class="btn" href="${e.reading_html_url}" target="_blank">打开精读 HTML</a>`:''}
        ${e.pdf_path?`<span class="muted">${e.pdf_path}</span>`:''}
        ${keepButtons(e.id)}
        <span class="muted" style="margin-left:6px">← / → 切换上一条·下一条</span>
      </div>
    </div>
    <div class="reading">${mdToHtml(e.reading_md||'（无解读内容）')}</div>`;
  bindKeepButtons(d);
  document.getElementById('main').scrollTop=0;
}
function navDetail(d){
  if(currentList.length===0) return;
  let i=selIdx+d; i=Math.max(0,Math.min(currentList.length-1,i));
  if(i!==selIdx){ selIdx=i; showDetail(currentList[i].id); }
}
function moveSel(d){
  if(currentList.length===0) return;
  let i = selIdx<0 ? 0 : selIdx+d;
  i=Math.max(0,Math.min(currentList.length-1,i));
  selIdx=i;
  const list=document.getElementById('resultList');
  list.querySelectorAll('.paper').forEach((el,idx)=>{ el.classList.toggle('sel', idx===i); });
  const els=list.querySelectorAll('.paper'); if(els[i]) els[i].scrollIntoView({block:'nearest'});
}
function mdToHtml(md){
  if(!md) return '';
  const lines=md.replace(/\r/g,'').split('\n');
  let html='', i=0;
  const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const inline=s=>{
    s=esc(s);
    s=s.replace(/`([^`]+)`/g,'<code>$1</code>');
    s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
    s=s.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2">$1</a>');
    return s;
  };
  while(i<lines.length){
    const line=lines[i];
    let m=line.match(/^(#{1,4})\s+(.*)$/);
    if(m){ const lv=m[1].length; html+=`<h${lv}>${inline(m[2].trim())}</h${lv}>`; i++; continue; }
    if(/^\s*[-*]\s+/.test(line) || /^\s*\d+\.\s+/.test(line)){
      const ordered=/^\s*\d+\.\s+/.test(line); const items=[];
      while(i<lines.length && (/^\s*[-*]\s+/.test(lines[i]) || /^\s*\d+\.\s+/.test(lines[i]))){
        items.push('<li>'+inline(lines[i].replace(/^\s*([-*]|\d+\.)\s+/,''))+'</li>'); i++;
      }
      html+=(ordered?'<ol>':'<ul>')+items.join('')+(ordered?'</ol>':'</ul>'); continue;
    }
    if(/^\s*>\s?/.test(line)){
      const buf=[];
      while(i<lines.length && /^\s*>\s?/.test(lines[i])){ buf.push(inline(lines[i].replace(/^\s*>\s?/,''))); i++; }
      html+='<blockquote>'+buf.join('<br>')+'</blockquote>'; continue;
    }
    if(/^\s*\|.*\|\s*$/.test(line)){
      const rowsT=[];
      while(i<lines.length && /^\s*\|.*\|\s*$/.test(lines[i])){ rowsT.push(lines[i]); i++; }
      const pr=r=>r.trim().replace(/^\|/,'').replace(/\|$/,'').split('|').map(c=>c.trim());
      const head=pr(rowsT[0]); const body=rowsT.slice(2);
      html+='<table><thead><tr>'+head.map(h=>`<th>${inline(h)}</th>`).join('')+'</tr></thead><tbody>';
      body.forEach(r=>{ const cells=pr(r); html+='<tr>'+cells.map(c=>`<td>${inline(c)}</td>`).join('')+'</tr>'; });
      html+='</tbody></table>'; continue;
    }
    if(/^\s*---\s*$/.test(line)){ html+='<hr>'; i++; continue; }
    if(line.trim()===''){ i++; continue; }
    html+='<p>'+inline(line)+'</p>'; i++;
  }
  return html;
}
function bars(el, items, n){
  const m=Math.max(1,...items.map(x=>x[1]));
  el.innerHTML=items.slice(0,(n||99)).map(([k,v])=>{
    const w=(v/m*100).toFixed(1);
    return `<div class="bar"><div class="name" title="${k}">${k}</div><div class="track"><div class="fill" style="width:${w}%"></div></div><div class="v">${v}</div></div>`;
  }).join('');
}
function renderCards(){
  const st=DATA.status, tot=DATA.total, k=keepCountsNow();
  document.getElementById('cards').innerHTML=[
    ['文献总数',tot],['已精读',st['已精读']||0],['待精读',st['待精读']||0],
    ['保留',k['保留']||0],['不收藏',k['不收藏']||0],['未分类',k['未分类']||0]
  ].map(([l,n])=>`<div class="card"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');
}
renderCards();
bars(document.getElementById('authors'), DATA.authors, 12);
bars(document.getElementById('affs'), DATA.affiliations, 20);
bars(document.getElementById('topics'), DATA.topics, 20);
bars(document.getElementById('methods'), DATA.methods, 20);
bars(document.getElementById('models'), DATA.models, 25);
bars(document.getElementById('pathways'), DATA.pathways);
bars(document.getElementById('journals'), DATA.journals);
bars(document.getElementById('years'), DATA.years);
const ifb={}; DATA.entries.forEach(e=>{const b=ifBucket(e.if); ifb[b]=(ifb[b]||0)+1;});
bars(document.getElementById('ifbars'), Object.entries(ifb));
const cloud={};
[...DATA.topics, ...DATA.methods, ...DATA.models, ...DATA.pathways, ...DATA.affiliations].forEach(([k,v])=>{cloud[k]=(cloud[k]||0)+v;});
const ck=Object.entries(cloud).sort((a,b)=>b[1]-a[1]).slice(0,60);
const cmax=Math.max(1,...ck.map(x=>x[1]));
document.getElementById('cloud').innerHTML=ck.map(([k,v])=>{
  const sz=(12+v/cmax*22).toFixed(1);
  return `<span style="font-size:${sz}px;color:${v/cmax>.6?'#34d3c4':v/cmax>.3?'#4a9eff':'#8b97a6'}" data-t="${k}">${k}</span>`;
}).join('');
const toggleBtn=document.getElementById('toggleDiscarded');
function renderToggle(){
  const k=keepCountsNow();
  toggleBtn.textContent = showDiscarded ? '隐藏不收藏 ('+ (k['不收藏']||0) +')' : '显示不收藏 ('+ (k['不收藏']||0) +')';
}
toggleBtn.addEventListener('click',()=>{ showDiscarded=!showDiscarded; renderToggle(); updateRight(); });
document.getElementById('exportDecisions').addEventListener('click', exportDecisions);
document.getElementById('importDecisions').addEventListener('click', ()=> document.getElementById('importFile').click());
document.getElementById('importFile').addEventListener('change', ev=>{ if(ev.target.files[0]) importDecisions(ev.target.files[0]); ev.target.value=''; });
renderToggle();
document.getElementById('back').addEventListener('click',()=>{ updateRight(); });
document.getElementById('backStats').addEventListener('click',()=>{ activeFilter=null; query=''; document.getElementById('q').value=''; renderNav(); showView('stats'); });
document.getElementById('reset').addEventListener('click',()=>{ activeFilter=null; query=''; document.getElementById('q').value=''; renderNav(); showView('stats'); });
document.getElementById('q').addEventListener('input',ev=>{ query=ev.target.value.trim(); renderNav(); updateRight(); });
// 返回上一层（Backspace 键）：detail→result→stats；搜索框内有字时仅删字，空时返回
function goBack(){
  if(currentView==='detail'){ currentView='result'; showView('result'); }
  else if(currentView==='result'){ currentView='stats'; showView('stats'); }
}
document.addEventListener('keydown',function(e){
  const ae=document.activeElement;
  const inInput = ae && ae.tagName==='INPUT';
  if(e.key==='Backspace'){
    if(inInput && ae.value!=='') return;
    e.preventDefault(); goBack(); return;
  }
  if(inInput) return; // 搜索框聚焦时方向键/回车不触发切换
  if(currentView==='detail'){
    if(e.key==='ArrowRight'){ e.preventDefault(); navDetail(1); }
    else if(e.key==='ArrowLeft'){ e.preventDefault(); navDetail(-1); }
  } else if(currentView==='result'){
    if(e.key==='ArrowDown'||e.key==='ArrowRight'){ e.preventDefault(); moveSel(1); }
    else if(e.key==='ArrowUp'||e.key==='ArrowLeft'){ e.preventDefault(); moveSel(-1); }
    else if(e.key==='Enter'){ if(selIdx>=0 && currentList[selIdx]) showDetail(currentList[selIdx].id); }
  }
});
// 分隔条拖动
const resizer=document.getElementById('resizer');
const sidebar=document.getElementById('sidebar');
let dragging=false;
resizer.addEventListener('mousedown',e=>{dragging=true;resizer.classList.add('drag');document.body.style.cursor='col-resize';e.preventDefault();});
window.addEventListener('mousemove',e=>{ if(!dragging) return; let w=e.clientX; w=Math.max(240,Math.min(640,w)); sidebar.style.width=w+'px'; sidebar.style.flexBasis=w+'px'; });
window.addEventListener('mouseup',()=>{ if(dragging){dragging=false;resizer.classList.remove('drag');document.body.style.cursor='';} });
renderNav(); showView('stats');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main())
