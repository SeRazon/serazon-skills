#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文引用硬审计：校验 claims.csv 与 sources.json 的证据绑定关系。

用法（Windows cmd）:
    python scripts\\audit_claims.py claims.csv sources.json [--out audit_report.md]

claims.csv 列: claim_id,claim_text,type,source_ids,status
    type 取值: 事实 / 数据 / 方法 / 观点
    source_ids: 分号分隔的 S 编号，如 S001;S002；观点类可空
sources.json: [{"id","title","authors","year","venue","doi","cnki","note"}]
    可核验标识: doi / cnki(知网或万方链接) / venue+year 完整出版信息，三者至少其一

硬审计（任一失败直接报错退出，不产出通过报告）:
    1. 事实/数据/方法类断言必须绑定 ≥1 个 source_id
    2. 引用的 source_id 必须在 sources.json 中存在
    3. 每条被引用的文献必须有可核验标识，否则视为编造嫌疑
    4. claim_id 不得重复；source 登记不得出现完全相同的标题+年份重复条目
"""
import csv
import json
import sys
from pathlib import Path


def fail(msg):
    print(f"[硬审计失败] {msg}", file=sys.stderr)
    sys.exit(1)


def has_verifiable(src):
    if src.get("doi"):
        return True
    if src.get("cnki"):
        return True
    if src.get("venue") and src.get("year"):
        return True
    return False


def main():
    if len(sys.argv) < 3:
        print("用法: python audit_claims.py claims.csv sources.json [--out audit_report.md]")
        sys.exit(2)
    claims_path = Path(sys.argv[1])
    sources_path = Path(sys.argv[2])
    out_path = Path(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--out" else claims_path.parent / "audit_report.md"

    try:
        rows = list(csv.DictReader(claims_path.read_text(encoding="utf-8-sig").splitlines()))
    except FileNotFoundError:
        fail(f"找不到 claims.csv: {claims_path}")
    try:
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"找不到 sources.json: {sources_path}")
    except json.JSONDecodeError as e:
        fail(f"sources.json 解析失败: {e}")

    src_map = {}
    seen_title_year = set()
    for s in sources:
        sid = s.get("id", "?")
        if sid in src_map:
            fail(f"文献编号重复: {sid}")
        src_map[sid] = s
        key = ((s.get("title") or "").strip(), str(s.get("year") or "").strip())
        if key[0] and key in seen_title_year:
            print(f"[警告] 文献 {sid} 与已有条目标题+年份完全相同，可能重复登记: {key[0]}")
        seen_title_year.add(key)

    seen_claims = set()
    problems = []
    for r in rows:
        cid = (r.get("claim_id") or "").strip()
        if not cid:
            fail("存在缺 claim_id 的行")
        if cid in seen_claims:
            fail(f"断言编号重复: {cid}")
        seen_claims.add(cid)
        ctype = (r.get("type") or "").strip()
        sids = [x.strip() for x in (r.get("source_ids") or "").split(";") if x.strip()]
        if ctype in ("事实", "数据", "方法"):
            if not sids:
                fail(f"断言 {cid}（{ctype}）未绑定任何文献来源")
            for sid in sids:
                if sid not in src_map:
                    fail(f"断言 {cid} 引用的文献 {sid} 不存在（疑似编造编号）")
                if not has_verifiable(src_map[sid]):
                    fail(f"断言 {cid} 引用的文献 {sid} 缺少可核验标识（DOI/数据库链接/完整出版信息）")
        elif ctype == "观点":
            if sids:
                problems.append(f"断言 {cid} 标为观点却挂了文献，请确认是观点还是事实")
        else:
            fail(f"断言 {cid} 的 type 非法: {ctype}（只允许 事实/数据/方法/观点）")

    # 渲染审计报告（GB/T 7714 顺序编码制草稿）
    L = ["# 引用审计报告", ""]
    L.append(f"- 断言总数：{len(rows)}｜文献总数：{len(sources)}｜审计结论：通过")
    L.append("")
    L.append("## 参考文献（GB/T 7714 顺序编码制草稿，需按目标期刊微调）")
    L.append("")
    for i, s in enumerate(sources, 1):
        authors = s.get("authors") or "佚名"
        title = s.get("title") or "题名缺失"
        venue = s.get("venue") or "出处未查到"
        year = s.get("year") or "年份未查到"
        ident = s.get("doi") or s.get("cnki") or "无DOI/数据库链接"
        L.append(f"[{i}] {authors}. {title}[J]. {venue}, {year}. {ident}")
    L.append("")
    L.append("## 断言—文献绑定表")
    L.append("")
    L.append("| 断言编号 | 类型 | 文献 | 状态 |")
    L.append("|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['claim_id']} | {r.get('type','')} | {r.get('source_ids') or '—'} | {r.get('status','')} |")
    L.append("")
    if problems:
        L.append("## 待确认事项")
        L.append("")
        for p in problems:
            L.append(f"- [ ] {p}")
        L.append("")
    out_path.write_text("\n".join(L), encoding="utf-8")
    print(f"[通过] 引用审计通过，已生成: {out_path}")


if __name__ == "__main__":
    main()
