# -*- coding: utf-8 -*-
"""
数字一致性校验（文献精读用）

用途：把"数字前后矛盾"从 LLM 自查变成程序化校验。
输入：原文纯文本（txt / md）
输出：Markdown 报告 —— 数值清单 + 矛盾嫌疑 + 单位可疑项

用法：
    python 数字校验.py <文本文件路径> [--out 报告.md]
"""
import re
import sys
import os
import io
import time
from collections import defaultdict

# 单次跑完 find_integer_conflicts 的墙钟预算（秒）。超预算即停止继续扫描，
# 返回已完成的结果并在报告里标注"未扫完"——宁可少报也不许卡死。
INT_SCAN_BUDGET = 25.0

# 单位类别：把数值按物理含义归类，便于跨章节比对
UNIT_PATTERNS = [
    ("剂量-摩尔", r"nmol|pmol|µmol|μmol|mmol|mol"),
    ("剂量-浓度", r"µM|μM|mM|nM|pM|µg/mL|μg/mL|ng/mL|mg/mL"),
    ("剂量-体重", r"mg/kg|µg/kg|g/kg"),
    ("时间", r"\bh\b|hours?|hr|min|minutes?|days?|weeks?|months?|周|天|小时|分钟"),
    ("百分比", r"%|percent"),
    ("温度", r"°C|℃"),
    ("转速", r"\b[×x]\s?g\b|rpm"),
]

NUM = r"(\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"


def extract_values(text):
    """提取所有 (数值, 单位) 对及其上下文关键词"""
    hits = []
    lines = text.split("\n")
    for ln, line in enumerate(lines, 1):
        for cat, upat in UNIT_PATTERNS:
            for m in re.finditer(NUM + r"\s*(" + upat + r")", line, re.I):
                val, unit = m.group(1), m.group(2)
                # 取左侧 60 字符作上下文，抓参数名
                ctx = line[max(0, m.start() - 60):m.start()].strip()
                hits.append({
                    "cat": cat, "val": val, "unit": unit,
                    "line": ln, "ctx": ctx[-60:],
                })
        # 样本量 n=
        for m in re.finditer(r"\bn\s*=\s*(\d+)", line, re.I):
            hits.append({"cat": "样本量", "val": m.group(1), "unit": "n",
                         "line": ln, "ctx": line[max(0, m.start() - 60):m.start()].strip()[-60:]})
        # p 值
        for m in re.finditer(r"\bp\s*[<>=≤≥]\s*([\d.]+)", line, re.I):
            hits.append({"cat": "p值", "val": m.group(1), "unit": "p",
                         "line": ln, "ctx": line[max(0, m.start() - 60):m.start()].strip()[-60:]})
    return hits


def find_conflicts(hits):
    """
    找矛盾嫌疑：同一类别 + 相同上下文关键词，却出现不同数值。
    用上下文里的英文/中文词做粗略聚类（取末尾若干字符做指纹）。
    """
    groups = defaultdict(set)
    where = defaultdict(list)
    for h in hits:
        if h["cat"] in ("样本量", "p值"):
            continue  # n 和 p 本来就各处不同，不参与矛盾判定
        words = re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fa5]{2,}", h["ctx"])
        if not words:
            continue
        key = (h["cat"], words[-1].lower())
        groups[key].add(h["val"])
        where[key].append((h["val"], h["unit"], h["line"]))
    conflicts = []
    for key, vals in groups.items():
        if len(vals) > 1:
            conflicts.append({
                "cat": key[0], "keyword": key[1],
                "values": sorted(vals),
                "occurrences": sorted(set(where[key]))[:12],
            })
    return conflicts


# 两两比较的安全阈值：超过则降级为"按量词聚合"判定（见 find_integer_conflicts）
PAIRWISE_MAX = 60
# 单个窗口（段落切片）最多处理的 items 数，超出则截断（防病态输入卡死）
ITEMS_CAP = 400


def _pairwise_conflict(items, sep_re):
    """O(n²) 精判：仅当两处相距 <400 字符且中间无分组标记时才算矛盾。

    **复杂度护栏**：items 超过 PAIRWISE_MAX 时不再两两比较。
    真实教训：某段落在窗口切分后可含数百个计数，两两比较是 O(n²)，
    ×N 窗口 → 分钟到小时级卡死（实测 200 items 需 0.9 秒，纯 Python 下
    更密集时非线性放大）。降级策略见 find_integer_conflicts。
    返回 (是否发现真矛盾, 真矛盾对数)。
    """
    if len(items) > PAIRWISE_MAX:
        return None      # 交给调用方走聚合降级路径
    n_pairs = 0
    for i in range(len(items)):
        vi, si = items[i]
        for j in range(i + 1, len(items)):
            vj, _sj = items[j]
            if vi == vj:
                continue
            if j - i > 12:
                break    # 位置差太远，后面的只会更远，直接剪枝（等价 ≤400 字符窗）
            between = " ".join(x[1] for x in items[i:j + 1])
            if not sep_re.search(between):
                n_pairs += 1
    return n_pairs > 0, n_pairs


def find_integer_conflicts(text):
    """
    纯整数矛盾检测（补盲区）。

    背景：extract_values() 只抓"数值+单位"，因此 433/443 这类
    不带单位的纯计数（基因数、peak 数、细胞数、例数）会被整体漏掉。
    实测教训：某文中同一段先写 "Four hundred thirty-three genes" 再写
    "these 443 genes"，脚本未报，双方人工复核也都漏了。

    策略：把数字词（含英文拼写）归一化为整数，按"同段落内 + 同一量词"
    聚类，同一量词出现不同整数即为嫌疑。
    """
    WORDS = {
        "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
        "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    }
    # 量词：这些词前面的整数视为同一可比的"计数"
    MEASURE = (r"genes?|peaks?|cells?|samples?|patients?|cases?|proteins?|"
               r"sites?|clusters?|groups?|tumors?|tumours?|organoids?|"
               r"基因|峰|细胞|样本|患者|病例|蛋白|位点|聚类|分组|肿瘤|类器官")
    # 匹配"一段英文数词短语"：可含 hundred / thousand / and / 连字符
    EN_NUM = (r"(?:[a-zA-Z]+(?:[-\s]+[a-zA-Z]+){0,5})")

    def parse_english_number(s):
        """'four hundred thirty-three' / 'four hundred and thirty-three' -> 433；纯数字 -> int"""
        s = s.strip()
        if s.isdigit():
            return int(s)
        s = s.lower().replace("-", " ")
        words = re.findall(r"[a-z]+", s)
        if not any(w in WORDS or w in ("hundred", "thousand") for w in words):
            return None
        total, cur = 0, 0
        for w in words:
            if w in WORDS:
                cur += WORDS[w]
            elif w == "hundred":
                cur = (cur or 1) * 100
            elif w == "thousand":
                total += (cur or 1) * 1000
                cur = 0
            # and / 其它词忽略
        n = total + cur
        return n if n else None

    suspects = []
    truncated = False
    t_start = time.time()
    # 按段落切分；PDF 抽出的 txt 常常没有空行，
    # 因此若按空行切出的"段落"过大（>1200 字符），改用固定滑窗，
    # 保证 433/443 这类同段矛盾仍能被捕捉。
    raw_paras = re.split(r"\n\s*\n", text)
    paras = []
    for p in raw_paras:
        if len(p) <= 1200:
            paras.append(p)
        else:
            flat_p = re.sub(r"\s+", " ", p)
            for i in range(0, len(flat_p), 900):
                paras.append(flat_p[i:i + 1200])
    for pi, para in enumerate(paras, 1):
        if time.time() - t_start > INT_SCAN_BUDGET:
            truncated = True
            break
        flat = re.sub(r"\s+", " ", para)
        found = defaultdict(list)  # measure -> [(int, snippet)]

        # 统一扫描：阿拉伯数字 或 英文数词短语，紧后跟量词
        pattern = r"(\d{2,6}|" + EN_NUM + r")\s+(" + MEASURE + r")\b"
        for m in re.finditer(pattern, flat, re.I):
            # 排除"细胞系/试剂/仪器名里的数字"（如 MDA-MB-231 cells、HEK293 cells、
            # A549 cells、XF24 cell culture）——这些不是计数，是名称的一部分。
            lead = flat[max(0, m.start() - 24):m.start()]
            if re.search(r"[A-Za-z]{2,}[-A-Za-z0-9]*[-\s]?$", lead) and \
               re.search(r"(MDA|MB|HEK|A549|HCT|MCF|SKOV|OVCAR|ES-|T293|XF|U2|"
                         r"PC-|HeLa|K562|NIH|ATCC|CoraLite|Phalloidin)", lead, re.I):
                continue
            n = parse_english_number(m.group(1))
            if n is None or n < 10:
                continue
            snippet = flat[max(0, m.start() - 50):m.end() + 30]
            found[m.group(2).lower()].append((n, snippet))
            if len(found[m.group(2).lower()]) > ITEMS_CAP:
                found[m.group(2).lower()] = found[m.group(2).lower()][:ITEMS_CAP]
        # 判定：同一段落内，同一量词出现 ≥2 个不同整数
        # 降噪：只保留上下文里没有明显"分组/不同实验"标记的簇。
        # 复杂度：先走 O(n²) 精判（小规模），超阈值则降级为聚合判定（O(n)），
        #         保证任何输入都不会卡死。
        for measure, items in found.items():
            vals = sorted({n for n, _ in items})
            if len(vals) < 2:
                continue
            SEP = re.compile(
                r"upregulated|downregulated|上调|下调|normal|grades?|组|group|"
                r"respectively|vs\.?|versus|对照|control|versus", re.I)
            verdict = _pairwise_conflict(items, SEP)
            if verdict is None:
                # 聚合降级：窗口内已出现 ≥2 个不同计数，且未全部被分组标记隔开
                joined = " ".join(s for _, s in items)
                if SEP.search(joined):
                    # 有分组标记：保守起见只在"相同分组标记之间"仍冲突时报
                    segs = SEP.split(joined)
                    hit = any(len({int(x) for x in re.findall(r'\b(\d{2,6})\b', seg)})
                              > 1 for seg in segs if seg)
                    if not hit:
                        continue
                suspects_note_agg = True
            else:
                found_flag, _np = verdict
                if not found_flag:
                    continue
                suspects_note_agg = False
            suspects.append({
                "para": pi, "measure": measure, "values": vals,
                "context": [sn for _, sn in items][:4],
                "mode": "agg" if suspects_note_agg else "pair",
            })
    if truncated:
        print('[警告] 整数矛盾扫描超出 %.0f 秒预算，已提前停止；'
              '结果为**不完整**，请分段重跑。' % INT_SCAN_BUDGET)
    return suspects


def find_unit_suspects(text):
    """单位可疑：小写 µm 与 µM 混用、浓度单位写成长度单位等"""
    suspects = []
    lines = text.split("\n")
    for ln, line in enumerate(lines, 1):
        if re.search(r"\d+\s*µm\b", line) or re.search(r"\d+\s*μm\b", line):
            # 浓度语境里出现 µm（微米）多半是 µM（微摩尔）的排版错误
            if re.search(r"浓度|concentration|处理|treated|incubat", line, re.I):
                suspects.append((ln, "µm/μm 出现在浓度语境，疑为 µM 排版错误", line.strip()[:120]))
        if re.search(r"\d+\s*µM", line) and re.search(r"\d+\s*µm\b", line):
            suspects.append((ln, "同一行混用 µM 与 µm", line.strip()[:120]))
    return suspects


def render_report(path, hits, conflicts, suspects, int_confs=None):
    out = []
    out.append("# 数字一致性校验报告\n")
    out.append(f"源文件：`{path}`\n")
    out.append(f"共提取数值条目 **{len(hits)}** 处\n")

    out.append("\n## 一、矛盾嫌疑（同一参数出现不同数值）\n")
    if conflicts:
        out.append("| 类别 | 关键词 | 出现的不同数值 | 位置（行号） |")
        out.append("|---|---|---|---|")
        for c in conflicts:
            locs = "；".join(f"{v}{u}@L{ln}" for v, u, ln in c["occurrences"])
            out.append(f"| {c['cat']} | `{c['keyword']}` | {' / '.join(c['values'])} | {locs} |")
        out.append("\n> 以上需逐条回原文核对：是同一参数的口径不一致，还是不同实验/不同图的正常差异。")
    else:
        out.append("未检出同参数不同数值的情况。")

    int_confs = int_confs or []
    out.append("\n## 一·补、纯整数矛盾嫌疑（同段落内同一量词出现不同计数）\n")
    if int_confs:
        n_agg = sum(1 for c in int_confs if c.get("mode") == "agg")
        out.append("| 段落 | 量词 | 出现的不同整数 | 判定方式 | 上下文片段 |")
        out.append("|---|---|---|---|---|")
        for c in int_confs:
            ctx = " ⟪⟫ ".join(x.replace("|", "/") for x in c["context"])
            mode = "聚合（大段落降级）" if c.get("mode") == "agg" else "逐对（精判）"
            out.append(f"| 第{c['para']}段 | `{c['measure']}` | "
                       f"{' / '.join(str(v) for v in c['values'])} | {mode} | {ctx} |")
        if n_agg:
            out.append(f"\n> 其中 **{n_agg} 组为「聚合降级」判定**：该段落计数项过多，"
                       "为避免 O(n²) 卡死，脚本未做逐对精判，改用组内聚合。"
                       "**这类结果确定性较低，必须人工回原文核对。**")
        out.append("\n> 这类矛盾不带单位，最容易被漏。**必须逐条回原文核对**，"
                   "并检查是否同时存在英文数词写法（如 Four hundred thirty-three）"
                   "与阿拉伯数字写法（443）混用。")
    else:
        out.append("未检出同段整数计数不一致。"
                   "（注意：本项只覆盖正文中'数字 + 量词'形式的计数，"
                   "表格内数据、图中标注不在覆盖范围。）")

    out.append("\n## 二、单位可疑项\n")
    if suspects:
        for ln, why, snippet in suspects:
            out.append(f"- **L{ln}** {why}： `{snippet}`")
    else:
        out.append("未检出单位可疑写法。")

    out.append("\n## 三、数值清单（按类别）\n")
    by_cat = defaultdict(list)
    for h in hits:
        by_cat[h["cat"]].append(h)
    for cat in sorted(by_cat):
        items = by_cat[cat]
        vals = sorted({h["val"] + h["unit"] for h in items})
        out.append(f"- **{cat}**（{len(items)} 处）：{', '.join(vals[:40])}")

    out.append("\n## 四、样本量与统计\n")
    ns = sorted({h["val"] for h in by_cat.get("样本量", [])})
    ps = sorted({h["val"] for h in by_cat.get("p值", [])})
    out.append(f"- 样本量 n 取值：{', '.join(ns) if ns else '未检出'}")
    out.append(f"- p 值取值：{', '.join(ps[:30]) if ps else '未检出'}")
    if ns:
        out.append("- 提醒：若全文未见 power analysis / 样本量估算依据，需在局限性中点出。")

    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("用法: python 数字校验.py <文本文件路径> [--out 报告.md]")
        return 1
    src = sys.argv[1]
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    if not os.path.isfile(src):
        print(f"[错误] 文件不存在: {src}")
        return 1
    text = io.open(src, encoding="utf-8", errors="ignore").read()
    hits = extract_values(text)
    conflicts = find_conflicts(hits)
    suspects = find_unit_suspects(text)
    int_confs = find_integer_conflicts(text)
    report = render_report(src, hits, conflicts, suspects, int_confs)
    if out_path:
        io.open(out_path, "w", encoding="utf-8").write(report)
        print(f"[完成] 报告已写入: {out_path}")
    else:
        print(report)
    print(f"[统计] 数值 {len(hits)} 处 / 矛盾嫌疑 {len(conflicts)} 组 / "
          f"整数矛盾 {len(int_confs)} 组 / 单位可疑 {len(suspects)} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
