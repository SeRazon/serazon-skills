# -*- coding: utf-8 -*-
"""
全量同源比对：以未被我改动过的原始表副本为基准，
对压缩后的表做全量、全字段、双向严格比对。

判据（任一不符即 EXIT=1）：
  ① 期刊名集合完全一致（无增无减）
  ② 每条记录的「键集合」完全一致（区分 键缺失 / 键在值为 null）
  ③ 每条记录的「全部字段值」逐一相等
  ④ jcr_helper 行为级：match() 对全量键 + 真实查询形态，返回结果与键集合一致

用法：
  python 全量同源比对.py
  python 全量同源比对.py --orig <原始表> --new <压缩表>
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

ABSENT = object()   # 键缺失


def _load_raw(path):
    with io.open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _decode_to_plain(raw):
    """
    把任意形态（对象化 / 列式字典编码）解成「纯对象化 dict」，
    且严格保留三态：键缺失 = 不写该键；键在值为 None = 写 None。
    """
    if not (isinstance(raw, dict) and "rows" in raw and "cols" in raw):
        # 已是对象化：原样返回（但深拷贝一层，避免污染）
        return {k: dict(v) if isinstance(v, dict) else v for k, v in raw.items()}

    cols = raw["cols"]
    dic = raw.get("dict") or {}
    qrt, yr, cls, top = dic.get("q", []), dic.get("y", []), dic.get("c", []), dic.get("t", [])
    ABSENT_V, NULL_V = -1, -2

    def _undef(v, table):
        if v == ABSENT_V:
            return ABSENT
        if v is None or v == NULL_V:
            return None
        if isinstance(v, int) and table:
            return table[v] if 0 <= v < len(table) else None
        return v

    enum_map = {"jcr_quartile": qrt, "year": yr, "cas_big_class": cls, "cas_top": top}
    out = {}
    for r in raw["rows"]:
        rec = dict(zip(cols, r))
        name = rec.pop("name", None)
        if not name:
            continue
        clean = {}
        for f in cols:
            if f == "name":
                continue
            val = _undef(rec.get(f, ABSENT_V), enum_map.get(f))
            if val is ABSENT:
                continue          # 键缺失 -> 不写
            clean[f] = val        # 键在（值可为 None/字符串/数字）
        out[name] = clean
    return out


def compare(orig_path, new_path):
    print("=" * 72)
    print("全量同源比对（基准 = 未改动过的原始表副本）")
    print("=" * 72)
    print("基准 : %s" % orig_path)
    print("待验 : %s" % new_path)
    print("-" * 72)

    A = _decode_to_plain(_load_raw(orig_path))
    B = _decode_to_plain(_load_raw(new_path))

    ka, kb = set(A), set(B)
    print("基准条目数 : %d" % len(ka))
    print("待验条目数 : %d" % len(kb))

    ok = True

    # ① 名称集合
    only_a = ka - kb
    only_b = kb - ka
    print("\n[①] 期刊名集合")
    print("    仅基准有 : %d" % len(only_a))
    print("    仅待验有 : %d" % len(only_b))
    if only_a or only_b:
        ok = False
        for n in sorted(only_a)[:10]:
            print("      缺 -", n)
        for n in sorted(only_b)[:10]:
            print("      多 +", n)

    # ②③ 逐条键集合 + 值
    key_diff = []
    val_diff = []
    tri_absent_vs_null = []   # 专项：键缺失 vs 键在值为 null 的混淆
    for name in sorted(ka & kb):
        ra, rb = A[name], B[name]
        sa, sb = set(ra), set(rb)
        if sa != sb:
            key_diff.append((name, sorted(sa - sb), sorted(sb - sa)))
            continue
        for f in ra:
            va, vb = ra[f], rb[f]
            if va != vb:
                val_diff.append((name, f, repr(va), repr(vb)))
        # 三态专项
        for f in ("if", "jcr_quartile", "cas_big_class", "cas_top"):
            ina, inb = f in ra, f in rb
            if ina != inb:
                tri_absent_vs_null.append((name, f, ina, inb))

    print("\n[②] 键集合逐条比对")
    print("    键集合不符条目数 : %d" % len(key_diff))
    for name, miss, extra in key_diff[:10]:
        print("      %s  基准独有键=%s  待验独有键=%s" % (name, miss, extra))
    if key_diff:
        ok = False

    print("\n[③] 字段值逐条比对")
    print("    字段值不符数 : %d" % len(val_diff))
    for name, f, va, vb in val_diff[:10]:
        print("      %s.%s  基准=%s  待验=%s" % (name, f, va, vb))
    if val_diff:
        ok = False

    print("\n[③b] 三态专项（键缺失 vs 键在值为 null）")
    print("    混淆数 : %d" % len(tri_absent_vs_null))
    for name, f, ina, inb in tri_absent_vs_null[:10]:
        print("      %s.%s  基准有键=%s 待验有键=%s" % (name, f, ina, inb))
    if tri_absent_vs_null:
        ok = False

    # 键分布统计（用于证明结构完整）
    from collections import Counter
    ca = Counter(len(v) for v in A.values())
    cb = Counter(len(v) for v in B.values())
    print("\n[结构] 每条记录键数量分布（键数: 条目数）")
    print("    基准 : %s" % dict(sorted(ca.items())))
    print("    待验 : %s" % dict(sorted(cb.items())))
    if ca != cb:
        ok = False

    return ok, A, B


def behavior_check(A, B, orig_path, new_path):
    """④ 行为级：两边各自喂进同一份 jcr_helper，逐条比对 match() 的返回。

    ★ 方法论修正（2026-09-21）：初版拿"表里的字面记录"当基准去比 match()，
      结果 SCIEEE&EDUCATION 这类会被模糊匹配命中近似条目的查询被误报为差异
      （'SCIENCE & EDUCATION' 字面 if=2.5，但 match 会命中 'SCIENCE EDUCATION' if=4）。
      match() 是模糊匹配，其返回 ≠ 字面记录，所以**基准必须同样是 match() 的输出**。
    """
    print("\n" + "=" * 72)
    print("[④] 行为级比对：同一 jcr_helper 分别加载两张表，比对 match() 返回")
    print("=" * 72)
    sys.path.insert(0, HERE)
    import jcr_helper

    orig_raw = io.open(orig_path, "r", encoding="utf-8-sig").read()
    new_raw = io.open(new_path, "r", encoding="utf-8-sig").read()

    names = sorted(A)
    print("查询条目数 : %d" % len(names))

    # 基准：原始表
    jcr_helper._CACHE = jcr_helper._decode(orig_raw)
    base = {n: jcr_helper.match(n) for n in names}
    # 待验：压缩表
    jcr_helper._CACHE = jcr_helper._decode(new_raw)
    test = {n: jcr_helper.match(n) for n in names}

    diff = 0
    samples = []
    for n in names:
        if base[n] != test[n]:
            diff += 1
            if len(samples) < 5:
                samples.append((n, base[n], test[n]))

    print("    match() 返回不一致数 : %d" % diff)
    for n, rb, rt in samples:
        print("      %s" % n)
        print("        原始表 : %s" % rb)
        print("        压缩表 : %s" % rt)

    ok = (diff == 0)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", default=r"E:/Work buddy/工作存储/学术人才背调团/pubmed-position-links/scripts/journal_if_map.json")
    ap.add_argument("--new", default=os.path.join(HERE, "journal_if_map.json"))
    ap.add_argument("--report", default=os.path.join(HERE, "全量同源比对报告.txt"))
    a = ap.parse_args()

    # 全部输出同时写文件（不走管道，避免被不存在的命令吞掉）
    buf = io.StringIO()
    _stdout = sys.stdout

    class _Tee(object):
        def write(self, s):
            buf.write(s)
            try:
                _stdout.write(s)
            except Exception:
                pass
            return len(s)

        def flush(self):
            try:
                _stdout.flush()
            except Exception:
                pass

    sys.stdout = _Tee()
    try:
        ok1, A, B = compare(a.orig, a.new)
        ok2 = behavior_check(A, B, a.orig, a.new)
        print("\n" + "=" * 72)
        verdict = "完全一致（全量、全字段、双向）" if (ok1 and ok2) else "存在不符"
        print("结论 : %s" % verdict)
        print("退出码 : %d" % (0 if (ok1 and ok2) else 1))
        print("=" * 72)
        code = 0 if (ok1 and ok2) else 1
    finally:
        sys.stdout = _stdout
        with io.open(a.report, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print("报告已写入 : %s" % a.report)

    sys.exit(code)


if __name__ == "__main__":
    main()
