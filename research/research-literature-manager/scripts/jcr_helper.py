# -*- coding: utf-8 -*-
"""JCR 影响因子匹配助手（只读引用 pubmed skill 的映射表，不复制、不修改原表）。

提供 journal -> {if, jcr_quartile, jcr_category, cas_big_class, cas_top} 的自动匹配。
匹配策略：
  1) 期刊名归一化（大写、去标点空格）后精确匹配表键；
  2) 缩写展开后再次精确匹配（处理 Adv. Sci. / Nat. Commun. 等缩写）；
  3) 仍无命中返回 None，由调用方记入未匹配清单。
"""
import json
import os
import re

def _find_map():
    """按优先级定位 JCR 映射表：环境变量 > 本技能自带（与脚本同目录）。"""
    cands = []
    env = os.environ.get("JCR_IF_MAP")
    if env:
        cands.append(env)
    cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "journal_if_map.json"))
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return cands[-1]


JCR_PATH = _find_map()

# 常见缩写 -> 完整词，用于展开期刊名做二次匹配
_ABBR = {
    "ADV": "ADVANCED", "SCI": "SCIENCE", "CHEM": "CHEMISTRY", "BIOL": "BIOLOGY",
    "MED": "MEDICINE", "PHYS": "PHYSICS", "INT": "INTERNATIONAL", "J": "JOURNAL",
    "AM": "AMERICAN", "NATL": "NATIONAL", "RES": "RESEARCH", "REV": "REVIEWS",
    "LET": "LETTERS", "COMMUN": "COMMUNICATIONS", "EXP": "EXPERIMENTAL",
    "MOL": "MOLECULAR", "BIOTECHNOL": "BIOTECHNOLOGY", "PHARMACOL": "PHARMACOLOGY",
    "IMMUNOL": "IMMUNOLOGY", "PATHOL": "PATHOLOGY", "GENET": "GENETICS",
    "DEV": "DEVELOPMENTAL", "CELL": "CELL", "CANCER": "CANCER", "CLIN": "CLINICAL",
    "TRANSL": "TRANSLATIONAL", "STRUCT": "STRUCTURAL", "FUNCT": "FUNCTIONAL",
    "ENVIRON": "ENVIRONMENTAL", "TOXICOL": "TOXICOLOGY", "NEURO": "NEURO",
    "NEUROSCI": "NEUROSCIENCE", "ONCOL": "ONCOLOGY", "RADIO": "RADIOLOGY",
    "SURG": "SURGERY", "PEDIATR": "PEDIATRIC", "CARDIOVASC": "CARDIOVASCULAR",
    "INFECT": "INFECTIOUS", "MICROBIOL": "MICROBIOLOGY", "PARASITOL": "PARASITOLOGY",
    "BIOCHEM": "BIOCHEMISTRY", "BIOPHYS": "BIOPHYSICS", "COMPUT": "COMPUTATIONAL",
    "MATER": "MATERIALS", "ENG": "ENGINEERING", "ELECTRON": "ELECTRONIC",
    "OPT": "OPTICS", "METAB": "METABOLISM", "NUTR": "NUTRITION", "FOOD": "FOOD",
    "AGR": "AGRICULTURAL", "PLANT": "PLANT", "ANIM": "ANIMAL", "VET": "VETERINARY",
    "REPROD": "REPRODUCTIVE", "ENDOCR": "ENDOCRINOLOGY", "METAB": "METABOLIC",
    "PHYSIO": "PHYSIOLOGY", "PHARMACY": "PHARMACY", "ALLERGY": "ALLERGY",
    "RHEUMATOL": "RHEUMATOLOGY", "HEMATOL": "HEMATOLOGY", "GASTRO": "GASTROENTEROLOGY",
    "HEPATOL": "HEPATOLOGY", "NEPHROL": "NEPHROLOGY", "UROL": "UROLOGY",
    "DERMATOL": "DERMATOLOGY", "PSYCHIATRY": "PSYCHIATRY", "NEUROLOGY": "NEUROLOGY",
    "PATH": "PATHOLOGY", "RADIAT": "RADIATION", "ATOM": "ATOMIC", "SOLID": "SOLID",
    "APPL": "APPLIED", "THEOR": "THEORETICAL", "MATH": "MATHEMATICAL",
    "STAT": "STATISTICAL", "COMP": "COMPUTER", "SCI": "SCIENCE",
    "NAT": "NATURE", "PROC": "PROCEEDINGS", "ANN": "ANNALS", "ARCH": "ARCHIVES",
    "BULL": "BULLETIN", "REP": "REPORTS", "OPEN": "OPEN", "FRONT": "FRONTIERS",
    "PLOS": "PLOS", "BMC": "BMC", "ELIFE": "ELIFE", "SCI": "SCIENCE",
}

_CACHE = None
_IDX = None      # 归一化索引（精确/展开/键列表），随 _CACHE 一起构建


def _norm(s):
    if not s:
        return ""
    s = str(s).upper().strip()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _expand(tokens):
    out = []
    for t in tokens:
        out.append(_ABBR.get(t, t))
    return out


def _decode(raw):
    """把映射表原文解成 {期刊名: {if, jcr_quartile, ...}} 的普通字典。

    ★ 为什么需要（2026-09-21）：WorkBuddy 上架规定"**解压后**总大小 ≤3MB"，
      而原表（对象化 JSON，每条都重复写 8 个键名）解压后 4.06MB，单它就超限。
      改存"列定义 + 行数组 + 低基数字段字典"后降到 1.96MB，**22,643 条一条不丢**。
      本函数同时吃两种格式（旧对象格式 / 新列式格式），旧库、旧环境不受影响。
    """
    d = json.loads(raw.lstrip("\ufeff"))
    # —— 新格式：{"cols": [...], "dict": {...}, "rows": [[...], ...]}
    if isinstance(d, dict) and "rows" in d and "cols" in d:
        cols = d["cols"]
        dic = d.get("dict") or {}
        qrt, yr, cls, top = dic.get("q", []), dic.get("y", []), dic.get("c", []), dic.get("t", [])
        # 哨兵值：区分"键缺失"与"键在但值为 null"两种语义
        ABSENT, NULL = -1, -2

        def _undef(v, table):
            """字典编码值还原。

            ★ 三态必须分开（2026-09-21 由匹配行为比对抓出，12/414 条差异）：
              - `ABSENT(-1)` → 键**整个不存在**（原始表里就没这个字段）；
              - `NULL(-2)`   → 键存在但值为 `null`（如无影响因子的 668 条艺术/人文期刊）；
              - 非负整数      → 查字典还原成字符串。
            曾把空值一并剔除，导致调用方 `info["if"]` 从"取到 None"变成 **KeyError**。
            """
            if v == ABSENT:
                return ABSENT
            if v is None or v == NULL:
                return None
            if isinstance(v, int) and table:
                return table[v] if 0 <= v < len(table) else None
            return v

        out = {}
        for r in d["rows"]:
            rec = dict(zip(cols, r))
            name = rec.pop("name", None)
            if not name:
                continue
            # `if` 列：可能是数值、NULL（键在值为 null）、ABSENT（键缺失）
            if_val = _undef(rec.get("if"), None)
            clean = {}
            if if_val != ABSENT:
                clean["if"] = if_val
            for f, tb in (("jcr_quartile", qrt), ("year", yr),
                          ("cas_big_class", cls), ("cas_top", top),
                          # ★ 这两个字段也要走三态判定：我曾无条件写入，
                          #   结果给"本来就没这键"的条目凭空造出键（1971 处不符，
                          #   由 --write 前的无损校验抓出）。凡"可缺失"的字段都必须判哨兵。
                          ("jcr_category", None), ("cas_big_partition", None)):
                val = _undef(rec.get(f), tb) if tb is not None else rec.get(f)
                if val != ABSENT:          # 只有"键缺失"才不放进结果
                    clean[f] = val
            out[name] = clean
        return out
    # —— 旧格式：{期刊名: {...}}
    return d


def _load():
    global _CACHE, _IDX
    if _CACHE is None:
        if not os.path.isfile(JCR_PATH):
            _CACHE = {}
            _IDX = {"exact": {}, "expand": {}, "keys": []}
            return _CACHE
        with open(JCR_PATH, "r", encoding="utf-8-sig") as f:
            _CACHE = _decode(f.read())
        # ★ 预算归一化索引（性能修复 2026-09-21）：
        #   原实现对每次 match() 都实时对 22,643 个键做 _norm()（两次 re.sub），
        #   实测单次 12.7ms；建索引后降到微秒级。
        _IDX = _build_index(_CACHE)
    return _CACHE


def _build_index(table):
    """建立三张索引：精确 / 缩写展开 / (短键->原键) 用于受控的包含兜底。"""
    exact, expand, keys = {}, {}, []
    for k, v in table.items():
        nk = _norm(k)
        if not nk:
            continue
        keys.append((nk, v))
        exact.setdefault(nk, v)
        ke = _norm(" ".join(_expand(nk.split())))
        if ke:
            expand.setdefault(ke, v)
    return {"exact": exact, "expand": expand, "keys": keys}


# 包含兜底的严格门槛（2026-09-21 修复"假匹配"）
#   原实现 `if n in nk or nk in n` 无任何长度约束，导致
#   "JOURNAL THAT DOES NOT EXIST IN JCR AT ALL XYZ" 因含子串 "RNA" 而命中 RNA 刊（if=4.3）。
#   现要求：被包含的一侧必须足够长（>= MIN_SUBSTR_LEN 字符）且占另一侧足够比例。
MIN_SUBSTR_LEN = 12          # 子串至少 12 个字符才允许兜底
MIN_SUBSTR_RATIO = 0.75      # 且子串须覆盖较长一侧的 75% 以上


def _contain_ok(short, long_):
    """判断 short 作为 long_ 的子串是否足够"可信"（不是偶然撞上的短刊名）。"""
    if len(short) < MIN_SUBSTR_LEN:
        return False
    if not long_:
        return False
    return len(short) / len(long_) >= MIN_SUBSTR_RATIO


def match(journal):
    """返回匹配到的 JCR 字典或 None。

    ★ 三级匹配（2026-09-21 重写）：
      1) 归一化精确匹配（走索引，O(1)）；
      2) 缩写展开后精确匹配（走索引，O(1)）；
      3) 包含兜底 —— **带长度与比例门槛**，只接受"一方几乎完整包含另一方"的情形。
    门槛的由来：原第 3 级无条件接受任意子串，实测把一个根本不存在的刊名
    匹配到了 `RNA`（因假名里含字母 R-N-A），返回 if=4.3 的**错误**影响因子。
    """
    if not journal:
        return None
    table = _load()
    if not table:
        return None
    n = _norm(journal)
    if not n:
        return None
    idx = _IDX or _build_index(table)

    # 1) 精确匹配
    hit = idx["exact"].get(n)
    if hit is not None:
        return hit

    qt = n.split()
    qe = _norm(" ".join(_expand(qt)))
    # 2) 缩写展开后精确匹配
    hit = idx["expand"].get(qe)
    if hit is not None:
        return hit

    # 3) 包含兜底：仅接受"一端几乎完整包含另一端"
    if len(qt) >= 2:
        for nk, v in idx["keys"]:
            if n == nk:
                return v
            if n in nk:                      # 查询是表键的子串
                if _contain_ok(n, nk):
                    return v
            elif nk in n:                    # 表键是查询的子串
                if _contain_ok(nk, n):
                    return v
    return None


def resolve(journal):
    """返回 (matched_bool, dict_or_none)。"""
    return match(journal) is not None, match(journal)


if __name__ == "__main__":
    import sys
    for j in sys.argv[1:]:
        ok, r = resolve(j)
        print(j, "->", r if ok else "未匹配")
