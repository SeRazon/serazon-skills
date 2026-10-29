# -*- coding: utf-8 -*-
"""
图数审计器（文献精读交付前门禁）

核心目的：让"声明的图数 ≠ 实际解析的图数"直接报错，把"少写板块 6 也不显眼"
这个长期漏洞变成机器拦截。

背景：连续三篇对比复盘证实——加文字规则（红线 14 等）无法阻止我漏写补充图，
因为板块 6 是唯一"少写也不会显得不完整"的板块。唯一有效手段是机械校验。

用法：
    python 图数审计.py --原文 <原文txt> --稿 <我的精读.md> [--out 报告.md]

退出码：
    0 = 通过
    1 = 不通过（有图未被解析 / 稿缺固定栏位 / 字数低于下限）
"""
import re
import sys
import os
import io
import argparse

# ---------- 原文侧：数图 ----------

# 注意：原文 txt 由 PDF 转换而来，常带软换行（"Extended \nData Fig. 1"），
# 所有正则必须允许 token 之间出现任意空白（含换行）。
SP = r'[\s\u00a0]+'   # 一个或多个空白/不换行空格
# 编号必须"数字结尾"：S1 / S1A / S12B 都要认，但不能把 S1A 的 A 吞进编号，
# 也不能让 \b 把 "S1A" 判成不匹配（这是上一版的真实 bug）。
SUFFIX = r'(?![0-9])'  # 编号后不能再跟数字

# 复数/缩写形式统一处理（真实 bug：原文写 "Supplementary Figs. S1 and S2"，
# 旧正则只认 Figure/Fig. 单数形式，导致 S1、S2 被整段漏掉，只认出 S3）。
FIGS = r'(?:Figures?|Figs?\.?)'      # Figure / Figures / Fig / Figs. / Fig.
# "和"连接词（用于列表形式：Figure S1 and S2 / Figure S1, S2 / Figure S1–S2）
CONJ = r'(?:' + SP + r'|,|、|和|及|and|to|至|–|—|-|\u2013|\u2014)+'

# 主图：Figure 1. / Figure 1: / Fig. 1 / FIGURE 1 / Figs. 1
RE_MAIN = re.compile(r'\b' + FIGS + SP + r'(\d{1,2})' + SUFFIX, re.I)
# 补充图命名：三种体系都必须覆盖
#   ① Figure S1 / Fig. S1 / Supplementary Figure S1 / Supplementary Figs. S1 → S 编号
#   ② Extended Data Fig. 1 / Extended Data Figure 1  → 纯数字编号（Nature 系用这个）
#   ③ Supplementary Figure 1                         → 纯数字编号
RE_SUPP_S = re.compile(
    r'(?:Supplementary' + SP + FIGS
    + r'|Extended' + SP + r'Data' + SP + FIGS
    + r'|' + FIGS + r')' + SP + r'(S\d{1,2})' + SUFFIX, re.I)
RE_SUPP_XD = re.compile(
    r'Extended' + SP + r'Data' + SP + FIGS + SP + r'(\d{1,2})' + SUFFIX, re.I)
RE_SUPP_PLAIN = re.compile(
    r'Supplementary' + SP + FIGS + SP + r'(\d{1,2})' + SUFFIX, re.I)
# 补充表
RE_SUPP_TAB = re.compile(
    r'(?:Supplementary|Supplemental)' + SP + r'Tables?' + SP + r'(S?\d{1,2})' + SUFFIX, re.I)
# 主表
RE_MAIN_TAB = re.compile(r'\bTables?' + SP + r'(\d{1,2})' + SUFFIX, re.I)


# 列表展开的两个硬上限（防假阳性——真实 bug：'
# 'Figure 1, 2, 3, ... 15 were analyzed' 会被展开成 15 幅图，
# 而原文只有 1 幅，门禁反而把正确稿判成"图号不存在"）
LIST_MAX_TAIL = 6      # 一个前缀最多再跟 6 个后续编号（真实列表极少超过 6 项）
LIST_MAX_SPAN = 48     # 从首个编号到最后一个编号的字符跨度上限


def expand_lists(text, base_re, prefix_letter=False):
    """展开"列表式"引用：Figure S1 and S2 / Figure S1, S2 / Figure S1–S2 → {S1, S2}

    做法：先用 base_re 抓出"前缀 + 首个编号"，再看紧跟其后的若干
    「连接词 + 编号」尾巴，把后续编号也吃进来。

    **两道护栏（缺一即误报）**：
      ① 最多再吃 LIST_MAX_TAIL 个后续编号；
      ② 从首个编号末尾到当前编号末尾的累计跨度不得超过 LIST_MAX_SPAN 字符。
    护栏的代价是"超长真列表"可能漏吃几个编号——那是**漏报**（安全方向），
    而无限展开是**误报**（会把合规稿判死，方向相反、后果更坏）。
    两者相权，宁可漏报。返回 set（编号字符串，已大写）。

    ★ 参数 prefix_letter（真实 bug X35，2026-09-20 第四轮实测）：
      原文写 `Figures S8 and 9`——这是 `Figure S8 and Figure S9` 的省略式，
      后续编号 **省略了 S 前缀**。旧写法把尾巴 `9` 原样收进来，
      于是门禁认定"原文存在一幅编号为 `9` 的补充图"，而任何稿件都不会写出 `Figure 9`
      这种编号 → **这份稿永远无法通过门禁**（实测报"补充图未覆盖 1 幅：9"）。
      修法：当 base_re 属于 **S 编号体系**（RE_SUPP_S）时，尾巴里**没有字母前缀的裸数字**
      一律补上 `S`；已有 `S` 前缀的保持原样。XD / PLAIN 体系不受影响。
    """
    out = set()
    list_tail = re.compile(CONJ + r'(S?\d{1,2})' + SUFFIX, re.I)
    for m in base_re.finditer(text):
        first = m.group(1).upper()
        out.add(first)
        # 该前缀体系是否以字母开头（S 体系）
        base_letter = first[0] if first[:1].isalpha() else ''
        pos = m.end()
        anchor = pos
        n_tail = 0
        while n_tail < LIST_MAX_TAIL:
            t = list_tail.match(text, pos)
            if not t:
                break
            if t.end() - anchor > LIST_MAX_SPAN:
                break
            tok = t.group(1).upper()
            if prefix_letter and base_letter and not tok[:1].isalpha():
                tok = base_letter + tok          # ★ X35：裸数字继承前缀
            out.add(tok)
            pos = t.end()
            n_tail += 1
    return out


def count_source_figs(text):
    """从原文统计图/表编号（含正文引用）。返回 dict。"""
    # 先归一化软换行为空格，避免 "Extended \nData Fig. 1" 被拆开
    text = re.sub(r'[ \t]*\n[ \t]*', ' ', text)

    mains = set()
    for m in RE_MAIN.finditer(text):
        # 排除被 "Figure S1" / "Extended Data Fig. 1" 命中后误算成主图的情况
        s = max(0, m.start() - 20)
        if re.search(r'(Supplementary|Extended' + SP + r'Data)' + SP + r'$',
                     text[s:m.start()], re.I):
            continue
        mains.add(int(m.group(1)))

    supps = set()
    # 先按三种命名体系抓，再对 S 编号体系做"列表展开"
    for m in RE_SUPP_S.finditer(text):
        supps.add(m.group(1).upper())
    supps |= expand_lists(text, RE_SUPP_S, prefix_letter=True)  # "Figs. S1 and S2" / "S8 and 9"
    for m in RE_SUPP_XD.finditer(text):
        supps.add('XD' + m.group(1))       # Extended Data Fig. N 单独标记
    supps |= {'XD' + x for x in expand_lists(text, RE_SUPP_XD)}
    for m in RE_SUPP_PLAIN.finditer(text):
        supps.add('S' + m.group(1))
    supps |= {'S' + x for x in expand_lists(text, RE_SUPP_PLAIN)}

    supp_tabs = set()
    for m in RE_SUPP_TAB.finditer(text):
        v = m.group(1).upper()
        if not v.startswith('S'):
            v = 'S' + v
        supp_tabs.add(v)
    supp_tabs |= expand_lists(text, RE_SUPP_TAB)

    main_tabs = set()
    for m in RE_MAIN_TAB.finditer(text):
        s = max(0, m.start() - 20)
        if re.search(r'(Supplementary|Supplemental)' + SP + r'$',
                     text[s:m.start()], re.I):
            continue
        main_tabs.add(int(m.group(1)))
    for x in expand_lists(text, RE_MAIN_TAB):
        main_tabs.add(int(re.sub(r'\D', '', x) or 0))

    def key(x):
        return (x[:2], int(re.sub(r'\D', '', x) or 0))

    return {
        'main': sorted(mains),
        'supp': sorted(supps, key=key),
        'supp_tabs': sorted(supp_tabs),
        'main_tabs': sorted(main_tabs),
    }


# ---------- 稿件侧：数解析条目 + 查固定栏位 ----------

# ★ 真实 bug X21（假阳性，本轮实测，2026-09-20）：
#   旧写法 `^#{2,4}\s*(图表\s*\d+|Figure\s*\d+|图\s*\d+)` 会**无差别命中**
#   诸如 `## 图表 3：全文表格盘点（★ 如实标注）` 这种"声明无表/声明无图"的收尾块。
#   后果（COVID-19 稿实测）：原文确实只有 Figure 1、Figure 2 两图，
#   稿件老老实实写了两图七栏 + 一个"0 表格"声明块，条目数被算成 **3**，
#   随后 6 条七栏齐全度检查全部报"缺"（2 < 3）——**诚实声明反被当成缺陷**。
#   这是最坏的一类信号：它在惩罚诚实、鼓励"少写一个声明块蒙混过去"。
#   修法：条目标题里若含"盘点/声明/无表/合计"这类收尾语义词，则该标题不是图条目。
#   ★ 陷阱（本轮第二次踩）：RE_HEAD_FIG 只捕获到 `## 图表 1`（**不含**后面的标题文字），
#     所以负向过滤**不能对 m.group(0) 做**，必须取"该标题所在整行"来判断，否则永远不命中。
#     这是"过滤写了但没生效"的典型：断言 blocks=3 才暴露出来。
#
# ★★ 真实 bug X34（静默漏报，2026-09-20 第四轮实测，**危害等同 X13/X18**）：
#   旧写法限定 `#{2,4}`（**二级及以下**）。但有稿件的图条目直接写成 **一级标题**
#   `# 图表 1：Figure 1 — …`（实测：8 个主图条目全部是一级标题）。
#   后果链：条目数 = 0 → ① 七栏齐全度检查被 `if n_entries and …` 静默跳过；
#           ② 主图覆盖只进 warnings（不阻断）；③ 最终报"板块 6 没有任何图条目"，
#           但**同时把 7 个栏位全部标成 OK**（见下方 display 口径），报告自相矛盾。
#   更坏的是：`audit()` 的硬判定里"零条目"与"零解析"**只对补充图生效**，
#   主图零解析不阻断 → 若原文没有补充图（COVID-19 型），整篇可 EXIT=0 过关。
#   修法：标题级别放宽到 `#{1,4}`。★ 为什么一级安全：
#     · 板块主标题是 `# 板块 N`，与 `# 图表 N` 前缀不同，不会互相误吃；
#     · 稿件的一级标题只用于板块与图条目两处，放宽不会引入新的误命中。
#   同时补上"主图零解析也要硬拦"的判定（见 audit() 第 5 点）。
# ★ 补丁（2026-09-20 X43 修复）：原正则只认「裸数字」编号，
#   导致 `Figure S1` / `图 S1` / `图表 S1` 这类**补充图标题**完全无法被识别，
#   稿件被迫把补充图条目重命名为「图表 9（S1）」才能过关（写稿者偏离规格）。
#   现把编号段放宽成 [S\d]+，直接认 S 前缀补充图，无需改名。
RE_HEAD_FIG = re.compile(r'^#{1,4}\s*(图表\s*[S\d]+|Figure\s*[S\d]+|图\s*[S\d]+)', re.M)
RE_HEAD_FIG_NEG = re.compile(
    r'盘点|声明|台账|清单|汇总|合计|总计|小计|无表|无图|零表|零图|附表|附注')
RE_LINE_OF = re.compile(r'^.*$', re.M)
# 条目正文里出现的图号引用（用于判断某图号是否被当作条目解析过）
# 三类都要抓：① S 编号 ② Extended Data Fig. N ③ 普通 Figure N / 图 N
# 注意：编号后必须"不能跟数字"（与原文侧 SUFFIX 同理），否则 "Extended Data Fig. 1–7"
# 会把 1 认成编号；同时列表形式由 expand_lists 展开。
RE_REF_S = re.compile(
    r'(?:Supplementary' + SP + FIGS
    + r'|Extended' + SP + r'Data' + SP + FIGS
    + r'|' + FIGS + r'|图)' + SP + r'(S\d{1,2})' + SUFFIX, re.I)
RE_REF_XD = re.compile(
    r'Extended' + SP + r'Data' + SP + FIGS + SP + r'(\d{1,2})' + SUFFIX, re.I)
RE_REF_PLAIN = re.compile(
    r'Supplementary' + SP + FIGS + SP + r'(\d{1,2})' + SUFFIX, re.I)
RE_REF_MAIN = re.compile(r'(?:' + FIGS + r'|图)' + SP + r'(\d{1,2})' + SUFFIX, re.I)

# "声明式"句子识别：这类句子只是报总数，不构成"解析"。
# 实测教训：某篇稿写"7 幅扩展数据图（Extended Data Fig. 1–7）"，
# 旧逻辑把 1 和 7 当成"已覆盖"，于是 XD2–XD6 报缺、XD1/XD7 反而不报——
# 实际 7 幅一幅都没解析。**声明不能冒充解析。**
#
# ★ 但"挖声明"本身极易伤及无辜（真实 bug，比上面那个更严重）：
#   旧写法 `全文[^。\n]{0,40}(?:主图|...)[^。\n]{0,40}` 是"从'全文'一路吃 80 字符"，
#   于是 「如图 1 所示，全文共 5 幅主图与 3 幅补充图被逐条解析，
#   Supplementary Fig. S1 显示时间依赖。」整句被挖成「如图 1 所示， 。」，
#   真实解析内容 Supplementary Fig. S1 被一起删除 → 凭空产生"补充图零解析"的
#   **假判决**。这比漏报更坏：它是在没有证据的情况下报缺。
#
# 修正为准入式：只挖**同时满足**下列全部条件的分句——
#   ① 含"声明触发词"（全文/共计/总共/共 N 幅 + 图类词）
#   ② **整句不含任何"具体图号引用"**（Figure N / Fig N / 图 N / Supplementary Fig. S1 /
#      Extended Data Fig. N / Table N）——含具体图号 = 那就是真解析，绝不能挖
#   ③ 分句边界限于 。；! ? \n 与 + 号，不跨越句末标点
RE_DECL_TRIGGER = re.compile(
    r'(?:全文|全部|总计|共计|总共|一共|合计)'
    r'[^。；;！!？?\n+]{0,30}'
    r'(?:主图|主表|扩展数据图|补充图|补充表|扩展图|图|表|'
    r'main\s+figures?|supplementary\s+figures?|figures?|tables?)',
    re.I)
# 「具体图号引用」探测：出现任一命中即认为该分句含真实引用，禁止剥离
RE_ANY_FIGNUM = re.compile(
    r'(?:Supplementary' + SP + FIGS
    + r'|Supplemental' + SP + r'Tables?'
    + r'|Extended' + SP + r'Data' + SP + FIGS
    + r'|' + FIGS
    + r'|Tables?'
    + r'|图|表)' + SP + r'(?:S?\d{1,2}|[A-Z]?\d{1,2})' + SUFFIX,
    re.I)


# ★ CONJ 里含范围符（–—-），这会把 "Fig. 1–7" 这种**范围声明**误判成
#   "逐条列举"，从而被当成真解析保护起来 —— 这正是 某篇稿"7 幅全漏却报缺 5 幅"
#   的原始 bug 复发路径。因此必须把两种形态分开判定：
#   范围声明：前缀 + 编号 + 范围符 + 编号（只有首尾两点，不构成逐条解析）
#   逐条列举：前缀 + 编号 + **非范围**连接词 + 编号（真解析，必须保护）
CONJ_NONRANGE = r'(?:' + SP + r'|,|、|和|及|and|to|至)+'   # 不含 –—- 的范围符

# 「逐条列举」探测：前缀 + 首编号 + 非范围连接词 + 第二编号
# （如 "Supplementary Fig. S1、S2、S3" / "Fig. 1 and 2" / "Fig. 1, 2, 3"）
RE_ENUM_HEAD = re.compile(
    r'(?:Supplementary' + SP + FIGS
    + r'|Extended' + SP + r'Data' + SP + FIGS
    + r'|' + FIGS
    + r'|Tables?|图|表)' + SP + r'(?:S?\d{1,2})' + SUFFIX
    + CONJ_NONRANGE + r'(?:S?\d{1,2})' + SUFFIX,
    re.I)

# 「范围式声明」探测：前缀 + 首编号 + 范围符 + 尾编号
# （如 "Extended Data Fig. 1–7" / "Supplementary Figs. S1–S3"）
# 这类写法只点首尾，**不构成逐条解析**——必须挖掉，否则两端编号会被
# 误当成"已覆盖"。挖的范围仅限该引用本身，不牵连同句其它真解析内容。
RE_RANGE_DECL = re.compile(
    r'(?:Supplementary' + SP + FIGS
    + r'|Extended' + SP + r'Data' + SP + FIGS
    + r'|' + FIGS
    + r'|Figures?|图)'
    + SP + r'(?:S?\d{1,2})' + SUFFIX
    + r'\s*[–—\u2013\u2014-]\s*(?:S?\d{1,2})' + SUFFIX,
    re.I)


def _is_enumeration(sent):
    """该分句是否为"逐条列举"式引用。

    注意：范围式（Fig. 1–7）**不算**逐条列举——它只点首尾，
    若算作列举就会被保护起来，声明句又会冒充解析。
    """
    if not RE_ENUM_HEAD.search(sent):
        return False
    return True


def strip_declaration(sent):
    """对**单个分句**做声明剥离，返回剥离后的文本。

    判定顺序（关键：先看"有没有真解析"，再看"是不是声明"）：
      · 含**列表式真解析**（"Supplementary Fig. S1、S2、S3 分别展示"）→ 原样保留；
      · 含**范围式声明**（"Extended Data Fig. 1–7"，只有首尾编号）→ 挖掉整段引用；
      · 含**单个具体图号 + 其余正文**→ 只挖"总数声明片段"，保留图号引用；
      · 纯声明（无任何图号）→ 整句挖掉。

    ★ 这里的取舍不对称，必须说清：
      挖多了 → 谎报"零解析/缺图"（凭空报缺，方向错误、危害大）；
      挖少了 → 声明冒充解析（漏报，方向安全）。
    因此**只有当声明片段能被精确定位时才挖**，定位不了就保留。
    """
    if not RE_DECL_TRIGGER.search(sent):
        return sent

    # ① 列表式真解析（编号之间有连接词，≥2 个编号）→ 这是真解析，绝不挖
    if _is_enumeration(sent):
        return sent

    # ② 范围式声明 "Fig. 1–7" / "Figs. S1–S3"：只有首尾两个编号 + 连接符
    #    → 该引用是"声明区间"，挖掉整段引用（原 bug 的正解）
    sent2 = RE_RANGE_DECL.sub(' ', sent)

    # ③ 再检查剩余部分是否还有具体图号引用
    if RE_ANY_FIGNUM.search(sent2):
        return sent2        # 保留残余引用（真解析部分）
    return ' '

# 板块 6 的固定七栏（与 SKILL.md 规格一致）
REQUIRED_FIELDS = ['原文标题', '图注中译', '图表类型', '数据模式', '学术意义',
                   '统计方法', '本图数值清单']

# 全文级必查栏位（红线 22 / 板块 10 / 板块 11）——"少写也不显眼"的板块
# 注意：计数用 input_count 而不是"关键词出现次数"——否则
# "## 可引用金句" 这个小标题只会被数 1 次，3 条金句本身不含"金句"二字。
WHOLE_DOC_CHECKS = [
    # (栏位名, 小节标题正则, 条目计数正则, 最低条数, 说明)
    # ★ 条目计数正则须容忍 markdown 引用前缀与加粗（真实 bug X17）：
    #   稿件常写成 `1. > "**原文**"`（引用块嵌套在编号列表里），
    #   旧正则 `^\s*\d+\.\s*["“]` 要求引号紧跟 `N. `，
    #   于是 3 条合规金句全被数成 0 条 → 判"不通过"（假阴性，冤枉合规稿）。
    #   现允许 `> `、`**`、`- ` 等修饰符出现在引号之前。
    ('可引用金句', r'可引用金句',
     r'^\s*(?:\d+\.|[-*])\s*(?:>\s*)?(?:\*\*|__)?\s*["“]', 3,
     '板块 10「可引用金句」须 ≥3 条（红线 22）：格式 `"<英文原文>"（<中译>）—— <位置/页码>`'),
    ('关键节点穷举', r'关键节点', None, 1,
     '板块 5「关键节点」穷举式盘点必写（红线 22）：凡出现具体日期/时间刻度的事件一律列出'),
    ('创新星级', r'创新', r'[⭐★]', 4,
     '板块 8 四类创新各给星级（红线 22 扩展）：理论/方法/命名/应用四类都要 ⭐ 评级'),
]

# 需要"限定在某个板块内计数"的检查项：栏位名 → 板块号。
# ★ 真实 bug X19：创新星级的 old 口径是"全篇找第一个 ⭐/★，从那里数到下一个标题"。
#   但板块 6（图表解析）里常用 ★ 做"关键对照/要点"标记，
#   于是扫描起点落在板块 6，scope 只覆盖到板块 6 内下一个 `##` 标题（约 900 字符），
#   板块 8 里那 16 颗真正的评级星**一颗都没数到** → 合规稿被判"创新星级 0 次"。
#   这是假阴性（冤枉合规稿），且误导性极强：报告说"缺"，
#   作者会去板块 8 反复加星，但星本来就在那儿。
SECTION_SCOPE_CHECKS = {'创新星级': 8}


def _section_span(md, n):
    """返回板块 n 的 (start, end) 字符区间；找不到返回 None。"""
    m = re.search(r'^#+\s*板块\s*%d\b' % n, md, re.M)
    if not m:
        return None
    m2 = re.search(r'^#+\s*板块\s*\d+', md[m.end():], re.M)
    end = m.end() + m2.start() if m2 else len(md)
    return (m.start(), end)

# 板块切片
# ★ `\b` 词边界同样必要（bug X36）：否则 `板块 1` 会命中 `板块 10/11/12` 的前缀，
#   把板块 10 的正文并进板块 1，导致 10 的"找不到"→ 该板块字数闸静默跳过。
SECTION_PAT = r'^#+\s*板块\s*(\d+)\b'

# 分句切分（用于声明剥离）：只在句末标点/换行处切，不跨句。
# ★ 不能按 "+" 切（真实 bug）：稿件的图数声明常写成
#   「全文 7 幅主图（Fig. 1–7）+ 7 幅扩展数据图（Extended Data Fig. 1–7）+ 5 个补充表」，
#   若按 "+" 切成多段，只有第一段带"全文"触发词能被剥离，
#   后面几段（含 Extended Data Fig. 1–7）会整段残留 → 首尾编号被误判为"已解析"，
#   于是报"缺 XD2–XD6"而不是"7 幅全没解析"——**凭空替稿件认了 2 幅**。
#   一分句 = 一完整声明，是这里唯一正确的粒度。
SENT_SPLIT = re.compile(r'(?<=[。；;！!？?\n])')


def strip_declarations(text):
    """按分句剥离"声明句"，保留含具体图号的真实解析分句。

    比旧的整段 sub 安全：以"分句"为最小单位，逐句判断，
    因此同一行里"声明 + 真解析"混排时不会误删真解析。
    """
    parts = SENT_SPLIT.split(text)
    return ' '.join(strip_declaration(p) for p in parts)


# 板块主标题：要求 "板块 N" 出现在 **一级标题（# ）** 里。
# ★ 真实 bug X20（假阴性，本轮实测）：
#   SECTION_PAT 允许任意级标题命中，于是稿件里的小节
#   `## 板块 6 补充说明：本篇图表结构的特征` 会被**当成第二个"板块 6"**，
#   把板块 6 的统计一刀切成 8020 + 322 两段。
#   后果：板块 6 字数地板（≥1200）被判为"322 < 1200 偏薄"——
#   实际稿件有 8342 字、24 个完整图条目，是**合规稿被冤枉**。
#   若某篇合规稿板块 6 真在 1200 上下，这一刀足以让它被判"不通过"（EXIT=1），
#   属于"凭空报缺"，方向错误。正解：主标题必须是一级标题。
MAIN_SECTION_PAT = r'^#\s*板块\s*(\d+)\b'


def slice_sections(md):
    """把稿件按"板块 N"切成 {N: 文本}。

    边界只认**一级标题**（`# 板块 N`）；`## 板块 N …` 这类小节**不参与切分**，
    否则正文里的说明小节会把所属板块截成两段，导致字数地板误判（bug X20）。
    """
    hits = list(re.finditer(MAIN_SECTION_PAT, md, re.M))
    if not hits:                     # 兜底：稿件若用了非一级标题，退回宽松口径
        hits = list(re.finditer(SECTION_PAT, md, re.M))
    out = {}
    for i, m in enumerate(hits):
        n = int(m.group(1))
        end = hits[i + 1].start() if i + 1 < len(hits) else len(md)
        out[n] = md[m.start():end]
    return out


def slice_section6(md):
    """切出板块 6 的正文（从"板块 6"标题到"板块 7"标题之间）。

    ★ 必须带 `\b` 词边界（本轮实测 bug X36）：
      旧写法 `^#+\\s*板块\\s*7` 在稿件里出现 `# 板块 70 …` 时会**提前截断**——
      "板块 7" 命中了 "板块 70" 的前缀，于是板块 6 被切在 70 之前，
      后面的图条目被静默丢弃（条目数变少，七栏核验随之漏检）。
      这类"章节号前缀吞并"是真实的静默漏报路径，必须有词边界挡住。

    ★ 与 slice_sections 保持**同一口径**（一级标题优先，退回任意级）：
      两处对"板块边界"的定义若不一致，字数目检与图条目检会各切各的，
      同一份稿在两处判出不同结果（X20 的同类根因）。
    """
    m = re.search(r'^#\s*板块\s*6\b', md, re.M) or \
        re.search(r'^#+\s*板块\s*6\b', md, re.M)
    if not m:
        return None, 'NO_SECTION6'
    tail = md[m.start():]
    m2 = re.search(r'^#\s*板块\s*7\b', tail, re.M) or \
        re.search(r'^#+\s*板块\s*7\b', tail, re.M)
    seg = tail[: m2.start()] if m2 else tail
    return seg, None


RE_ANY_HEAD = re.compile(r'^(#{2,4})\s*\S', re.M)


def _entry_head_hits(s6):
    """板块 6 里"真图条目"的标题匹配列表（**全脚本唯一入口**）。

    ★ 为什么必须收成唯一入口（本轮真实教训）：
      X21 修好后回归断言过了，但审计报告仍显示"图条目数 3"——
      因为 `audit()` 里另有一处**独立的内联计数**（直接对 s6 做 findall），
      与 `_split_entry_blocks()` 各算各的。**同一件事两条实现路径，改了一条必然留下另一条。**
      故此处收敛为唯一函数，`audit()` 与 `_split_entry_blocks()` 都只许调它。
      （回归测试里有一条"不许再出现内联 findall 计数"的源码级断言钉住这一点。）
    """
    hits = []
    for m in RE_HEAD_FIG.finditer(s6):
        line_end = s6.find('\n', m.start())
        line = s6[m.start():line_end if line_end >= 0 else len(s6)]
        if RE_HEAD_FIG_NEG.search(line):
            continue          # ★ X21：收尾声明块（"全文表格盘点"等）不是图条目
        hits.append(m)
    return hits


def _split_entry_blocks(s6):
    """把板块 6 切成"图条目块"列表，块内 = 该条目标题到**下一个同级/更高级标题**之间。

    用途：判定"某幅图是否真被解析"时，**只能看条目块内部**。
    若拿整个板块 6 去搜图号，一句"（S1–S3 见补充图）"就能让 3 幅图凭空过关
    —— 这是真实发生过的静默漏报（X18）。

    ★ 边界必须停在"下一个任意标题"，不能停在"下一个图条目标题"：
      否则最后一个条目会把后面的说明段（如 `## 板块 6 补充说明`）整段吞进来，
      说明段里的图号又被算成"已解析"，漏洞原样复现。
      （这条是被单元断言抓出来的：E 组"说明段里的 S1 不算条目解析"。）

    ★ X21（假阳性，2026-09-20 实测）：标题命中了不等于"这是个图条目"。
      `## 图表 3：全文表格盘点（★ 如实标注）` 是**声明"无表格"的收尾块**，
      把它算成第 3 个图条目，会让后续 6 条七栏齐全度检查全部误报"缺"
      ——诚实声明被当成缺陷。故此处**跳过含收尾语义词（盘点/声明/无表/合计…）的标题**。
    """
    hits = _entry_head_hits(s6)          # ★ 唯一入口，勿再用 inline findall（X21）
    blocks = []
    for i, m in enumerate(hits):
        start = m.start()
        # 找该条目之后的下一个任意标题作为终点
        nxt = RE_ANY_HEAD.search(s6, m.end())
        end = nxt.start() if nxt else len(s6)
        # 若下一个标题本身就是图条目标题，用它的位置（等价，但更直观）
        if i + 1 < len(hits) and hits[i + 1].start() <= end:
            end = hits[i + 1].start()
        blocks.append(s6[start:end])
    return blocks


def check_whole_doc(md, problems, warnings):
    """跑"全文级"栏位硬检查（红线 18/22）。这些栏位"少写也不显眼"，必须机器拦。

    计数口径：
      有 item_re 的 → 数"条目"（如金句是编号列表 1. "..."，不是数"金句"二字）；
      没有 item_re 的 → 先定位小节标题，再在该小节正文里数（或全篇数一次）。
    """
    stat = {}
    for tup in WHOLE_DOC_CHECKS:
        name, head_re, item_re, floor, note = tup
        # ① 首选：本项被显式指定了"只在某板块内计数"（如创新星级 → 板块 8）。
        #    这是最可靠的口径，不依赖"第一个关键词出现处"这种脆弱启发式。
        sec_no = SECTION_SCOPE_CHECKS.get(name)
        span = _section_span(md, sec_no) if sec_no else None
        if span:
            body = md[span[0]:span[1]]
            c = len(re.findall(item_re, body, re.M)) if item_re \
                else len(re.findall(head_re, body))
            stat[name] = {'count': c, 'floor': floor, 'note': note,
                          'scope': '板块 %d' % sec_no}
            if c < floor:
                problems.append(
                    '【必填栏位缺失】「%s」在**板块 %d 内**出现 %d 次 < 最低 %d 次。%s'
                    % (name, sec_no, c, floor, note))
            continue
        if item_re:
            # 若给了小节标题，就在该小节范围内数条目；否则全篇数
            scope = md
            hm = re.search(head_re, md)
            if hm:
                rest = md[hm.end():]
                nm = re.search(r'^#+\s*板块\s*\d+|^#+\s*(?!.*' + head_re + r')#{1,3}\s', rest, re.M)
                scope = rest[:nm.start()] if nm else rest
            c = len(re.findall(item_re, scope, re.M))
        else:
            c = len(re.findall(head_re, md))
        stat[name] = {'count': c, 'floor': floor, 'note': note, 'scope': '全文/小节'}
        if c < floor:
            problems.append(
                '【必填栏位缺失】「%s」出现 %d 次 < 最低 %d 次。%s'
                % (name, c, floor, note))
    return stat


# 板块级"参考上限"（提示用，不拦截）。键=板块号，值=中文字上限。
# 只给高度模板化的板块设；目的是把"板块切分错位"这种静默故障暴露出来。
UPPER = {6: 12000}


def check_section_floors(secs, problems, warnings, n_figs=None):
    """板块级最低字数闸（红线 17 的板块化）：这些板块"少写也不显眼"，最易被砍。"""
    # (板块号, 名称, 字数下限, 理由)
    FLOORS = [
        (2, '主要研究内容', 260, 'M15：须写研究对象本身的分量（流行学/临床重要性），只写"没人做过"不合格'),
        (4, '样本量', 190, 'M16：四栏固定模板（样本类型/来源/纳入排除/每组 n），只填 n 不合格'),
        (5, '研究时间', 110, 'M19：须写成实验时序，不是参数罗列'),
        (6, '图表解析', 1200, '板块 6 是重头戏，逐图七栏；低于此值多半漏了补充图或栏位'),
        (8, '创新点', 190, 'M17：四类（理论/方法/命名/应用）各给星级，缺类须写明理由'),
        (10, '研究可复刻性', 500, 'M14：须含总体判断+分维度评分表+缺失清单+可引用金句+主线衔接'),
        (11, '核心要点总结', 400, 'M22：须含 100 字概括+三要点+引用建议+可迁移要素'),
    ]
    # 参考上限：只对"结构高度模板化"的板块设，用于提示"切分错位"。
    # 板块 6 每图 7 栏，单图条目约 600–900 中文字；给 2 倍余量。
    # 总数 = 图条目数 × 1200；图条目数取自原文盘点（缺信息时按 10 图兜底），
    # 不硬编码某个篇目，避免换一篇就失真。
    stat = {}
    for n, name, floor, why in FLOORS:
        seg = secs.get(n, '')
        cn = len(re.findall(r'[\u4e00-\u9fff]', seg))
        upper = (n_figs * 1200) if (n == 6 and n_figs) else UPPER.get(n)
        stat[name] = {'cn': cn, 'floor': floor, 'upper': upper}
        if not seg:
            warnings.append('未找到板块 %d（%s）标题。' % (n, name))
            continue
        if cn < floor:
            warnings.append('板块 %d（%s）中文字 %d < 建议下限 %d。%s'
                            % (n, name, cn, floor, why))
        if upper and cn > upper:
            # ★ 上限同样是"信号"：超上限多半意味着该板块被注入其它板块的内容
            #   （真实 bug：板块 6 切分点被本区块内的 `## 图表 N` 之类
            #     同前缀标题抢先命中，导致后续板块全文被算进本板块 → 字数虚高）。
            #   只提示不拦截——按取舍原则，宁可提示也不误判合规稿。
            warnings.append('板块 %d（%s）中文字 %d > 参考上限 %d（按 %s 图 × 1200 估）。'
                            '超上限不必然是缺陷，但**常见的真因是板块切分错位**：'
                            '请人工确认本板块边界是否被本区块内的同前缀小标题抢先命中。'
                            % (n, name, cn, upper, n_figs if n_figs else '默认'))
    return stat


def audit(orig_text, md_text, char_floor=6000):
    src = count_source_figs(orig_text)
    s6, err = slice_section6(md_text)
    secs = slice_sections(md_text)
    problems = []
    warnings = []

    # 1) 板块 6 是否存在
    if err:
        problems.append('未找到"板块 6"标题——按规格必须有。')
        s6 = ''

    # 2) 图条目数（★ 必须走 _entry_head_hits，否则会与 _split_entry_blocks 口径不一致 → 真实 bug X21）
    heads = _entry_head_hits(s6)
    n_entries = len(heads)

    # 3) 引用到的图号集合（从板块 6 全文抽；三类命名都要认）
    s6n = re.sub(r'[ \t]*\n[ \t]*', ' ', s6)
    # 先把"声明式"分句挖掉——声明不能冒充解析（真实 bug：某篇稿的
    # "Extended Data Fig. 1–7" 声明句让 XD1/XD7 被误判为已覆盖）。
    # ★ 用 strip_declarations 按分句处理，且含具体图号的分句一律保留——
    #   否则会把真实解析内容一起挖掉，凭空产生"零解析"假判决。
    s6_body = strip_declarations(s6n)
    refd = set()          # 归一化后的补充图标记（S3 / XD1）
    for m in RE_REF_S.finditer(s6_body):
        refd.add(m.group(1).upper())
    for m in RE_REF_XD.finditer(s6_body):
        refd.add('XD' + m.group(1))
    for m in RE_REF_PLAIN.finditer(s6_body):
        refd.add('S' + m.group(1))
    refd |= expand_lists(s6_body, RE_REF_S, prefix_letter=True)
    refd |= {'XD' + x for x in expand_lists(s6_body, RE_REF_XD)}
    refd |= {'S' + x for x in expand_lists(s6_body, RE_REF_PLAIN)}
    refd_num = set()
    for m in RE_REF_MAIN.finditer(s6_body):
        s = max(0, m.start() - 24)
        if re.search(r'(Supplementary|Extended' + SP + r'Data)' + SP + r'$',
                     s6_body[s:m.start()], re.I):
            continue
        refd_num.add(int(m.group(1)))

    # 4) 补充图覆盖：**逐条目判定**，不是"某处提到过就算解析"
    #
    # ★★ 这里修的是一个严重漏报（真实 bug X18）：
    #    旧逻辑在"整个板块 6 文本"里搜 S 编号，只要出现过一次就认为该图被覆盖。
    #    于是下面这份稿能**通过门禁**：
    #      · 板块 6 只写了 2 个图条目（Fig. 1、Fig. 2），S1/S2/S3 一条条目都没有；
    #      · 但某处一句"（S1/S2/S3 已在补充图解析）"就把 3 幅补充图"认账"了。
    #    实测：`_tmp_旧版模式.md` 图条目=2、补充图引用={S1,S2,S3} → EXIT=0。
    #    这是"静默给假成品"，比报错更坏：门禁说通过，稿件实际缺 3 幅。
    #
    #    正确口径：**一个图号必须出现在某个图条目的条目体内，才算被解析**。
    #    因此这里把板块 6 切成"条目块 + 非条目杂质"，只认条目块里的图号。
    entry_blocks = _split_entry_blocks(s6)
    entry_body = '\n'.join(entry_blocks)
    entry_body = strip_declarations(re.sub(r'[ \t]*\n[ \t]*', ' ', entry_body))

    refd = set()          # 仅在"条目体内"出现过的补充图标记（S3 / XD1）
    for m in RE_REF_S.finditer(entry_body):
        refd.add(m.group(1).upper())
    for m in RE_REF_XD.finditer(entry_body):
        refd.add('XD' + m.group(1))
    for m in RE_REF_PLAIN.finditer(entry_body):
        refd.add('S' + m.group(1))
    refd |= expand_lists(entry_body, RE_REF_S, prefix_letter=True)
    refd |= {'XD' + x for x in expand_lists(entry_body, RE_REF_XD)}
    refd |= {'S' + x for x in expand_lists(entry_body, RE_REF_PLAIN)}

    # 另算一份"全板块引用集"，只用于在提示里说明"残留提及"（不参与通过判定）
    all_body = strip_declarations(re.sub(r'[ \t]*\n[ \t]*', ' ', s6))
    mentioned_only = set()
    for m in RE_REF_S.finditer(all_body):
        mentioned_only.add(m.group(1).upper())
    for m in RE_REF_XD.finditer(all_body):
        mentioned_only.add('XD' + m.group(1))
    for m in RE_REF_PLAIN.finditer(all_body):
        mentioned_only.add('S' + m.group(1))
    mentioned_only |= expand_lists(all_body, RE_REF_S, prefix_letter=True)
    mentioned_only |= {'XD' + x for x in expand_lists(all_body, RE_REF_XD)}
    mentioned_only |= {'S' + x for x in expand_lists(all_body, RE_REF_PLAIN)}

    refd_num = set()
    for m in RE_REF_MAIN.finditer(entry_body):
        s = max(0, m.start() - 24)
        if re.search(r'(Supplementary|Extended' + SP + r'Data)' + SP + r'$',
                     entry_body[s:m.start()], re.I):
            continue
        refd_num.add(int(m.group(1)))

    src_supp = set(src['supp'])
    missing_supp = sorted(src_supp - refd,
                          key=lambda x: int(re.sub(r'\D', '', x) or 0))
    # "只在正文提过、但没有任何条目解析它"的图号——单列出来，措辞要说准
    mention_only_supp = sorted(mentioned_only - refd,
                               key=lambda x: int(re.sub(r'\D', '', x) or 0))

    # 5) 主图覆盖
    src_main = set(str(x) for x in src['main'])
    missing_main = sorted(src_main - set(str(x) for x in refd_num), key=int)

    # 6) 固定栏位齐全度
    field_stat = {}
    for f in REQUIRED_FIELDS:
        field_stat[f] = len(re.findall(f, s6))

    # 7) 字数
    cn = len(re.findall(r'[\u4e00-\u9fff]', md_text))
    s6_cn = len(re.findall(r'[\u4e00-\u9fff]', s6))

    # 8) 全文级必填栏位（红线 18/22）——硬拦
    whole_stat = check_whole_doc(md_text, problems, warnings)

    # 9) 板块级字数闸（红线 17 板块化）
    sec_stat = check_section_floors(secs, problems, warnings,
                                    n_figs=len(src['main']) + len(src['supp']))

    # ---------- 判定 ----------
    if src['supp'] and not refd.intersection(src_supp):
        # 区分两种"零解析"：真的一句没提 vs 提过但没写条目
        if mentioned_only & src_supp:
            problems.append(
                '原文含补充图 %d 幅（%s），板块 6 **没有任何图条目解析它们**，'
                '仅在正文中被顺带提及（提到过：%s）——判定为「补充图零解析」。'
                '★ 注意：顺带提及不等于解析，不计入覆盖。'
                % (len(src_supp), ','.join(sorted(src_supp)),
                   ','.join(sorted(mentioned_only & src_supp))))
        else:
            problems.append(
                '原文含补充图 %d 幅（%s），但板块 6 全文未引用任何补充图号'
                '——判定为「补充图零解析」。' % (len(src_supp), ','.join(sorted(src_supp))))
    elif missing_supp:
        problems.append(
            '补充图未覆盖 %d 幅：%s（原文存在，稿件未提及）。'
            % (len(missing_supp), ','.join(missing_supp)))

    if src['main'] and len(refd_num) < len(src_main):
        miss = missing_main
        if miss:
            warnings.append('主图未在板块 6 引用：%s' % ','.join(miss))

    # ★ X34 修复：主图"零解析"必须硬拦。
    #   旧逻辑里"零解析"只对补充图生效（下面那一段），主图零解析**最多只进 warnings**。
    #   若某篇原文恰好没有补充图（如 COVID-19 综述篇只有 2 主图 0 补图），
    #   稿件一个主图条目都不写，仍可 EXIT=0 过关——这是**静默给假成品**。
    #   与补充图同口径处理：主图引用数 = 0 视为"零解析"，属不通过。 
    if src['main'] and not refd_num:
        problems.append(
            '原文含主图 %d 幅（%s），板块 6 **没有引用任何主图编号**'
            '——判定为「主图零解析」。' % (len(src_main), ','.join(sorted(src_main, key=int))))

    # 只在正文提过、却没写条目的补充图 → 提示（避免"看起来覆盖了"）
    if mention_only_supp and (mentioned_only & src_supp):
        warnings.append(
            '以下补充图号**只被顺带提及、没有独立图条目**：%s。'
            '若判定为"已覆盖"会在交付后被发现漏图，建议补条目或明确写明省略理由。'
            % ','.join(mention_only_supp))

    if n_entries == 0:
        problems.append('板块 6 没有任何图条目（## 图表 N / ## Figure N）。')

    # 栏位齐全度：每图应有七栏，总出现次数应 ≈ 条目数
    #
    # ★ X34-b（静默放行，本轮实测）：旧写法 `if n_entries and c < n_entries`——
    #   条目数一旦为 0，**整段检查被静默跳过**，报告却在"栏位齐全度"表里
    #   对每一栏打印 "OK"（因为 `res['n_entries'] and c >= res['n_entries']` 为假走 else 分支
    #   时用的是 '缺'，但条目数同为 0 的其它栏位口径不一致，实测输出里出现过全 OK）。
    #   后果：一份板块 6 有 5,796 中文字、8 幅真图条目但标题级别没被认出的稿，
    #   报告显示"栏目全 OK / 判定通过"——**报告自相矛盾且鼓励误信**。
    #   修法：条目数为 0 时不再静默跳过，而是显式把"无法核验"写进 warnings，
    #   并把该情形记为**不通过**（problems 里已由上一行兜底）。
    if n_entries == 0:
        warnings.append(
            '条目数为 0，**七栏齐全度无法核验**（不是"通过"）。'
            '若板块 6 确实有图条目，请检查条目标题是否用了本脚本未识别的写法'
            '（当前识别 `#`~`####` 级 + `图表 N` / `Figure N` / `图 N`）。')
    else:
        for f, c in field_stat.items():
            if c < n_entries:
                warnings.append(
                    '栏位「%s」出现 %d 次 < 图条目 %d 条——存在图缺此栏。'
                    % (f, c, n_entries))

    # 注意分母：声明"N 幅主图"要跟"主图类条目数"比，不能跟全部条目比
    # （真实 bug：合规稿声明"2 幅主图 + 3 幅补充图"，条目共 5 条，
    #   旧逻辑拿 2 != 5 报错——把正确的稿判成不通过，是假阳性。）
    m_decl = re.search(r'(\d+)\s*幅?\s*(?:主图|main figures?)', s6, re.I)
    if m_decl:
        decl = int(m_decl.group(1))
        # ★ X34 同步：主图条目判据同样放宽到 1~4 级标题
        #   （某篇的一级标题写法若不放宽，n_main_entries 恒为 0，
        #    会静默退回"总数比较 + 降级提示"，主图条目与声明数的硬核对就失效了）
        n_main_entries = len(re.findall(
            r'^#{1,4}\s*图表\s*\d+\s*[：:]\s*(?:Figure|Fig\.?)\s*\d', s6, re.M))
        # 若无法区分主图/补充图条目（旧格式），退回总数比较并降级为提示
        if n_main_entries:
            if decl != n_main_entries:
                problems.append(
                    '「声明主图数 ≠ 主图解析条目数」：稿件声明 %d 幅主图，'
                    '实际主图条目 %d 条。' % (decl, n_main_entries))
        elif decl != n_entries:
            warnings.append(
                '「声明图数 ≠ 解析条目数」：稿件声明 %d 幅，实际解析条目 %d 条'
                '（未能区分主图/补充图条目，请人工确认）。' % (decl, n_entries))

    # 栏位齐全度已在上面（n_entries == 0 分支）统一处理，此处不再重复——
    # ★ X34-c：这里原有一份**重复的**栏位齐全度循环，与上面那份口径相同但分散两处。
    #   同一事实两处实现 = 红线 27 违反项（改一处必留另一处，X21-b 同型）。
    #   已删除，保留上方唯一实现。

    if char_floor and cn < char_floor:
        warnings.append('全篇中文字 %d < 下限 %d（红线 17：视为太浅）。' % (cn, char_floor))

    return {
        'src': src, 'n_entries': n_entries, 'refd': sorted(refd),
        'missing_supp': missing_supp, 'missing_main': missing_main,
        'field_stat': field_stat, 'cn': cn, 's6_cn': s6_cn,
        'whole_stat': whole_stat, 'sec_stat': sec_stat,
        'problems': problems, 'warnings': warnings,
    }


def render(res, orig_path, md_path):
    L = []
    A = L.append
    A('# 图数审计报告（交付前门禁）\n')
    A('- 原文：`%s`' % orig_path)
    A('- 稿件：`%s`\n' % md_path)
    s = res['src']
    A('## 一、原文图/表盘点（脚本自动抽取）\n')
    A('| 类别 | 数量 | 编号 |')
    A('|---|---|---|')
    A('| 主图 | %d | %s |' % (len(s['main']), ', '.join('F%d' % x for x in s['main']) or '—'))
    A('| 补充图 | %d | %s |' % (len(s['supp']), ', '.join(s['supp']) or '—'))
    A('| 补充表 | %d | %s |' % (len(s['supp_tabs']), ', '.join(s['supp_tabs']) or '—'))
    A('| 主表 | %d | %s |' % (len(s['main_tabs']), ', '.join('T%d' % x for x in s['main_tabs']) or '—'))
    A('')
    A('## 二、稿件板块 6 盘点\n')
    A('- 图条目数：**%d**' % res['n_entries'])
    A('- 板块 6 中文字：**%d**' % res['s6_cn'])
    A('- 全篇中文字：**%d**' % res['cn'])
    A('- 板块 6 引用到的图号：%s' % (', '.join(res['refd']) or '—'))
    A('')
    A('## 三、板块 6 固定栏位齐全度（规格要求每图 7 栏）\n')
    if not res['n_entries']:
        # ★ X34-b：条目数为 0 时**不许**打印"OK"——那是自相矛盾的报告
        #   （板块 6 明明有内容，却因为有 0 个被识别的条目而显示全部栏位 OK）。
        A('**条目数为 0，本表无法核验（不等于通过）**——'
          '若板块 6 确有图条目，请检查条目标题写法是否被识别'
          '（`#`~`####` + `图表 N` / `Figure N` / `图 N`）。\n')
    else:
        A('| 栏位 | 出现次数 | 图条目数 | 状态 |')
        A('|---|---|---|---|')
        for f, c in res['field_stat'].items():
            st = 'OK' if c >= res['n_entries'] else '缺'
            A('| %s | %d | %d | %s |' % (f, c, res['n_entries'], st))
        A('')
    A('## 四、全文级必填栏位（红线 18 / 22，硬拦）\n')
    A('| 栏位 | 出现次数 | 最低要求 | 状态 |')
    A('|---|---|---|---|')
    for k, v in res.get('whole_stat', {}).items():
        st = 'OK' if v['count'] >= v['floor'] else '**缺（不通过）**'
        A('| %s | %d | %d | %s |' % (k, v['count'], v['floor'], st))
    A('')
    A('## 五、板块字数闸（红线 17 板块化）\n')
    A('| 板块 | 中文字 | 建议下限 | 状态 |')
    A('|---|---|---|---|')
    for k, v in res.get('sec_stat', {}).items():
        st = 'OK' if v['cn'] >= v['floor'] else '偏薄'
        A('| %s | %d | %d | %s |' % (k, v['cn'], v['floor'], st))
    A('')
    A('## 六、判定\n')
    if res['problems']:
        A('### 不通过（%d 条）\n' % len(res['problems']))
        for i, p in enumerate(res['problems'], 1):
            A('%d. %s' % (i, p))
        A('')
    else:
        A('**通过**：未发现图数/栏位硬缺陷。\n')
    if res['warnings']:
        A('### 提示（%d 条，不阻断但需看）\n' % len(res['warnings']))
        for i, w in enumerate(res['warnings'], 1):
            A('%d. %s' % (i, w))
        A('')
    A('---')
    A('*本报告由 `图数审计.py` 自动生成。它的**实际能力边界**：*')
    A('')
    A('**能查**：原文图/表编号 vs 稿件板块 6 引用的编号差集（含 S / Extended Data / 纯数字三套命名）；')
    A('板块 6 七栏关键词出现次数；三条全文级必填栏位（金句≥3 / 关键节点 / 创新星级≥4）；')
    A('板块 2/4/5/6/8/10/11 中文字下限。')
    A('')
    A('**查不了**（这些必须人工读，不要因为本报告显示"通过"就放过）：')
    A('① 图注中译的**翻译质量**；② 「本图数值清单」里的数字**是否真在原文中**（有栏位 ≠ 数字对）；')
    A('③ 图与结论的对应是否成立；④ 排查板块 7–9、11 的论证质量；')
    A('⑤ 表格内部数据、图中标注上的数字（不在文本正则覆盖范围）；')
    A('⑥ 同一栏位写满 7 次但内容重复/模板化的情形（关键词计数无法识别）；')
    A('⑦ **七栏是否"每图各一份"只按总次数粗判**——2 图各 3.5 栏与 1 图 7 栏是同一计数，'
      '程序分不出，须人工逐图点一遍。')
    A('')
    A('**条目识别口径（写出来便于自查，不匹配即漏认）**：'
      '`#`~`####` 级标题 + `图表 N`/`图表 S*`（含 S 前缀补充图）/ `Figure N`/`Figure S*` / `图 N`/`图 S*` 前缀；'
      '含"盘点/声明/无表/合计"等收尾语义词的标题**不算**图条目（红线 28）。')
    A('')
    A('**结论措辞说明**：本报告的"通过"仅指「未触发上述可机检项」，')
    A('**不等于稿件合格**，也**不构成对内容正确性的担保**。出现"不通过"时，')
    A('报告只声明机器发现了什么，不断言真实缺陷的全部范围。')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--原文', required=True)
    ap.add_argument('--稿', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--floor', type=int, default=6000)
    a = ap.parse_args()

    orig = io.open(a.原文, encoding='utf-8', errors='ignore').read()
    md = io.open(a.稿, encoding='utf-8', errors='ignore').read()

    res = audit(orig, md, char_floor=a.floor)
    rep = render(res, a.原文, a.稿)

    if a.out:
        io.open(a.out, 'w', encoding='utf-8').write(rep)
        print('报告已写入：' + a.out)
    else:
        print(rep)

    print('\n结论：' + ('不通过' if res['problems'] else '通过'))
    return 1 if res['problems'] else 0


if __name__ == '__main__':
    sys.exit(main())
