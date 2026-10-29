# -*- coding: utf-8 -*-
"""把 journal_if_map.json 从「对象化」转成「列式 + 字典编码」，并做**无损校验**。

背景：WorkBuddy 技能上架规定"**解压后**总大小 ≤ 3MB（3145728 字节）"。
原表解压后 4.06MB，单它就把整包顶到 4.78MB，被平台以
  "压缩包解压后超出大小限制（最大 3MB）"驳回。
对象化 JSON 每条都要重复写 8 个键名（"jcr_quartile"、"cas_big_partition"…），
22,643 条 × 8 = 18 万个键名，纯属冗余。
改列式后键名只写一次；再把低基数字段（分区/年份/大类/顶栏）做字典编码。

用法：
    python scripts/压缩影响因子表.py --in  scripts/journal_if_map.json
    python scripts/压缩影响因子表.py --in  scripts/journal_if_map.json --write
    python scripts/压缩影响因子表.py --verify-only      # 只校验现有表可解码且无损

退出码：0 = 通过；1 = 解不回原值（禁止替换）。
"""
import json
import os
import sys
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "journal_if_map.json")

COLS = ["name", "if", "jcr_quartile", "jcr_category", "year",
        "cas_big_class", "cas_big_partition", "cas_top"]


def _enc(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def load_any(path):
    """读入既有的表（兼容旧对象格式与新列式格式），统一返回 {name: {...}}。"""
    with open(path, "rb") as f:
        raw = f.read()
    d = json.loads(raw.decode("utf-8-sig"))
    if isinstance(d, dict) and "rows" in d and "cols" in d:
        # 已经是新格式：复用 jcr_helper 的解码，避免两套逻辑漂移
        sys.path.insert(0, HERE)
        import jcr_helper
        return jcr_helper._decode(raw.decode("utf-8")), True
    return d, False


ABSENT, NULL = -1, -2   # 哨兵：-1 = 键缺失；-2 = 键在但值为 null


def pack(table):
    """对象字典 → 列式 + 字典编码的紧凑结构。

    ★ 三态保留（2026-09-21）：原始表里字段有三种状态，压缩后必须原样还原：
        ① 有值            → 数值 / 字典下标
        ② 键在、值为 null  → NULL(-2)   （如 668 条无影响因子的艺术/人文期刊）
        ③ 键整个缺失       → ABSENT(-1) （如 1,303 条缺 cas_* 的期刊）
      混同 ② 与 ③ 会让调用方 `info["if"]` 从"取到 None"变成 KeyError。
    """
    enum_cols = {2: "q", 4: "y", 5: "c", 7: "t"}   # 下标 → 字典键
    rows = []
    for k, v in table.items():
        row = []
        for i, f in enumerate(COLS):
            if f == "name":
                row.append(k)
            elif f in v:
                row.append(v[f])        # 键在：值可能是 None
            else:
                row.append(ABSENT)      # 键缺失
        rows.append(row)

    # 低基数枚举列 → 字典编码（仅对"有值"的项编码，哨兵保持原样）
    def _enum(idx):
        vals = sorted({r[idx] for r in rows if isinstance(r[idx], str)})
        m = {v: i for i, v in enumerate(vals)}
        for r in rows:
            cell = r[idx]
            if isinstance(cell, str):
                r[idx] = m[cell]
            elif cell is None:
                r[idx] = NULL
            # ABSENT 保持 -1
        return vals

    dic = {}
    for idx, key in enum_cols.items():
        dic[key] = _enum(idx)

    # "if" 列可能是 None（不可枚举），保持 NULL 哨兵
    for r in rows:
        if r[1] is None:
            r[1] = NULL
    return {"v": 2, "cols": COLS, "dict": dic, "rows": rows}


def unpack(packed, decoder):
    """用 jcr_helper 的解码器把列式结构还原成对象字典（校验用）。"""
    return decoder(json.dumps(packed, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=DEFAULT, help="源表路径")
    ap.add_argument("--out", dest="dst", default=None, help="输出路径（默认覆盖 --in）")
    ap.add_argument("--write", action="store_true", help="真正写盘（不加则只演练）")
    ap.add_argument("--verify-only", action="store_true", help="只校验现有表可解码且行数正常")
    a = ap.parse_args()

    src = a.src
    dst = a.dst or src
    if not os.path.isfile(src):
        print("★ 找不到源表：%s" % src)
        return 1

    sys.path.insert(0, HERE)
    import jcr_helper

    old_bytes = os.path.getsize(src)
    table, already = load_any(src)
    print("=" * 70)
    print("影响因子表压缩")
    print("=" * 70)
    print("  源表      ：%s" % src)
    print("  源体积    ：%d 字节 = %.2f MB" % (old_bytes, old_bytes / 1048576))
    print("  条目数    ：%d" % len(table))
    print("  源格式    ：%s" % ("已是列式（无需再压）" if already else "对象化（可压缩）"))
    print()

    if a.verify_only:
        if not already:
            print("  [verify-only] 源表仍是对象格式，解码路径正常（%d 条）" % len(table))
            return 0
        return _verify(table, table, decoder=jcr_helper._decode)

    if already:
        print("  已是列式格式，跳过压缩。")
        return 0

    packed = pack(table)
    new_bytes = _enc(packed)
    print("  压缩后    ：%d 字节 = %.2f MB （省 %.1f%%）"
          % (len(new_bytes), len(new_bytes) / 1048576,
             (1 - len(new_bytes) / old_bytes) * 100))
    print()

    # ============ 无损校验（替换前必须全过）============
    print("=" * 70)
    print("无损校验")
    print("=" * 70)
    rc = _verify(table, None, packed=packed, decoder=jcr_helper._decode)
    if rc != 0:
        print("\n★ 校验未通过，**不写盘**。")
        return 1

    if not a.write:
        print("\n[演练模式] 未写盘。加 --write 才真正替换。")
        return 0

    with open(dst, "wb") as f:
        f.write(new_bytes)
    print("\n已写入：%s（%d 字节）" % (dst, len(new_bytes)))
    return 0


def _verify(orig, _unused, packed=None, decoder=None):
    """逐条核对：解码后的值必须与原始表完全一致。"""
    if packed is None:
        print("  （无需校验：已是目标格式）")
        return 0
    back = decoder(json.dumps(packed, ensure_ascii=False))
    if len(back) != len(orig):
        print("  ✗ 条目数不符：原 %d → 还原 %d" % (len(orig), len(back)))
        return 1
    bad = 0
    fields = ["if", "jcr_quartile", "jcr_category", "year",
              "cas_big_class", "cas_big_partition", "cas_top"]
    miss = [k for k in orig if k not in back]
    if miss:
        print("  ✗ 有 %d 个期刊名丢失，例：%s" % (len(miss), miss[:3]))
        return 1
    for k in orig:
        o, n = orig[k], back[k]
        # ① 逐键核对"键在不在"（区分 键缺失 vs 键在值为 null）
        for f in fields:
            if (f in o) != (f in n):
                if bad < 5:
                    print("  ✗ %s 的键 %s 存在性不符：原在=%s → 还原在=%s"
                          % (k[:40], f, f in o, f in n))
                bad += 1
                continue
            if f not in o:
                continue
            if o[f] != n[f]:
                if bad < 5:
                    print("  ✗ %s 的 %s 值不符：原 %r → 还原 %r" % (k[:40], f, o[f], n[f]))
                bad += 1
    extra = [k for k in back if k not in orig]
    if extra:
        print("  ✗ 多出 %d 条：%s" % (len(extra), extra[:3]))
        return 1
    if bad:
        print("  ✗ 共 %d 处字段不符" % bad)
        return 1
    print("  ✓ 条目数一致（%d）且全部 7 个字段逐条相符，零丢失" % len(orig))
    return 0


if __name__ == "__main__":
    sys.exit(main())
