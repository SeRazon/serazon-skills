# -*- coding: utf-8 -*-
"""人名音译审计（交付前门禁，配合红线 29）。

动机：
  实测教训：曾在五篇稿里编造了 15 个中文人名（把英文名"音译"成汉字）。
  随后改用"英文名（中文名，单位；邮箱）"的写法，加个"邮箱依据"就以为合法——
  但**邮箱推不出汉字**，加了说明也还是猜。

核心规则（最简化）：
  **原文没有汉字 → 稿件里就不许有汉字的人名。零豁免。**

判定逻辑：
  扫稿件里所有 `英文名（中文）` 形式。凡"中文"是 2–6 个纯汉字，且**不属于**下列情形，报嫌疑：
    ① 中文是术语/缩写的中译（原创研究 / 综述 / 定量 / 差异结合基因 …）
    ② 是单位/机构名（大学 / 研究院 / 实验室 …）
    ③ 括号左侧不像人名（缩写 / 技术词 / 章节栏目名）
  **不存在"注明来源即可放行"的后门**（那条后门正是上一版绕过去的路）。

★ 适用范围（2026-09-20 明确）：
  本门禁守的是**本技能今后产出的新稿**。历史存量稿（`outputs/` 下早期那批）
  曾由已移除的身份配置功能自动写入姓名与位次，**按决定保持原样不动**。
  故对存量稿报出的命中是**真实命中**（不是误报），处理方式不是改稿，
  而是**人工确认"这份稿是历史存量、不作为新交付物"**。门禁不会自动放行它们。

退出码：0 = 无嫌疑；1 = 有嫌疑，禁止交付（须删掉中文名，只留英文原名）。

用法：
  python 人名审计.py <稿件.md> [<稿件2.md> ...]
  python 人名审计.py --dir <输出目录>          # 扫该目录全部 文献精读_*.md
"""
import io
import os
import re
import sys
import glob

# ★ 历史教训（保留作为设计依据，不含任何真实姓名）：
#   上一版白名单里放过若干中文人名，理由是"原文邮箱可对应"。
#   这个理由站不住：
#     · 邮箱只能证明"这个人叫某个英文名、邮箱是这个"，
#       **推不出汉字**——拼音对应哪几个汉字是多种可能，仍是猜。
#     · 而且那些汉字根本不是从原文读出来的，是从第三方产出抄来的二手信息。
#   **正确规则：凡原文无汉字，一律不写汉字。**
#   故本门禁不设任何自然人姓名白名单——技能不记录、不比对任何真实姓名。
WHITELIST_CN = set()

# 术语中译白名单：这些不是人名，命中即驳回
TERM_OK = re.compile(
    r'原创研究|综述|定量|定性|必要性|充分性|互作|完全缓解|部分缓解|疾病进展|'
    r'稳定|中国春节|独立一作|共同一作|难点|策略|机制|排除|雌性|雄性|形态|'
    r'皮下|内脏|棕色|全组两两|与对照比|葡萄糖耐量|胰岛素耐量|邻近连接|公共库|'
    r'抗体梯度|荧光素酶互补|依语境推断|原文排版缺陷|作者声称|已验证')

# ★ 机构/单位名白名单：
#   `Li-jun Di（某大学）` 里的单位名是**单位**，不是人名。
#   第一版按"英文名+中文"一刀切，把单位也当成音译人名误报——
#   规避方式是：括号内若是单位/机构名，一律放行。
INSTITUTION_OK = re.compile(
    r'大学|学院|研究院|研究所|科学院|实验室|医院|中心|学校|学系|系|所|'
    r'医院|医学部|医学中心|肿瘤|课题组')

# ★ 统计方法 / 分子标记白名单（2026-09-20 X43 修复）：
#   这些词常写成「英文（中文说明）」形式（如 `Tukey（多重比较）`、`c-Met 蛋白（直接靶向）`），
#   会被 NAME_RE 误判为"音译人名"。但它们是方法名 / 分子名，绝非人名，
#   必须显式放行（放在 looks_like_person 之前，比"长得像人名"优先级更高）。
#   注意：这些 token 均为方法 / 标记术语，不会与真实作者英文名冲突，可安全列入。
METHOD_OK = re.compile(
    r'^(?:Tukey|Dunnett|ANOVA|Shapiro|Levene|Bartlett|Kruskal|'
    r'Mann-Whitney|Wilcoxon|Pearson|Spearman|Benjamini|Bonferroni|'
    r'c-Met|CD|Met|GAPDH|β-actin|Actin|t-test|t\s*检验|PCR|Western|FDR|'
    r'ROC|AUC|HR|CI|SD|SEM|NS|p\s*value)$', re.I)

# ★ 假阳性防线（红线 26：误报比漏报危险）：
#   实测本门禁第一版在五篇合规稿上误报 12 处，全是**缩写/术语的中译**而非人名——
#   如 DBG（差异结合基因）、LPL（脂蛋白脂酶）、AMPK（已有激活剂）、
#   CM-supernatant（去外泌体上清）、Western blotting（依据语境推断）。
#   它们的共同特征：**括号左侧是缩写、含连字符的技术词、或含数字/大小写的实验名**，
#   而不是 "Firstname Lastname" 形态的自然人名。
#   故新增第二层判定：只有左侧**长得像人名**才继续查。
#
# 长得像人名 = 1–3 个词、每词首字母大写、词内无数字、非全大写缩写、非已知技术词。
# ★ 修正：连字符后的字母**常常是小写**——
#   `Li-jun Di` 里 `-jun` 是 j 小写，旧写法 `-[A-Z][a-z]+` 匹配不上，
#   于是 `Li-jun Di（某中文名）` 被判"不像人名"而漏过。
#   这正是自测抓出来的：白名单删掉了那个名字，门禁却仍不报它。
LIKE_HUMAN_NAME = re.compile(
    r'^[A-Z][a-z]+(?:-[A-Za-z]+)?'
    r'(?:\s+[A-Z]\.?)?'
    r'(?:\s+[A-Z][a-z]+(?:-[A-Za-z]+)?){0,2}$')
# 明确不是人名的技术词/缩写（全大写、含数字、含已知后缀）
NOT_NAME = re.compile(
    r'^[A-Z0-9\-]+$'                    # 全大写缩写：DBG / LPL / AMPK / ATG / EGFP-PCA
    r'|^\w+-supernatant$'               # 技术名词
    r'|blotting|staining|PCR|seq$'      # 实验方法名
    r'|\d')                             # 含数字


# 进一步排除：单个词但明显是技术词（如 Western / Transmission）
# 也排除"章节标题式翻译"：New Phenomenon（新现象短通讯）、Transmission（六条传播路径）
NOT_NAME_EXTRA = re.compile(
    r'^(?:New|Old|Transmission|Introduction|Discussion|Results|Methods|'
    r'Abstract|Conclusion|Review|Perspective|Commentary|Correspondence|'
    r'Original|Research|Article|Report|Letter|Note|Brief|Communication)'
    r'(?:\s+(?:Phenomenon|Research|Article|Report|Paper|Study|Communication|'
    r'Series|Letter|Note|Review))?$')


def looks_like_person(en):
    """判断括号左侧是否**长得像人名**（而非缩写/术语/章节名）。"""
    en = en.strip()
    if NOT_NAME.search(en):
        return False
    if en.isupper():
        return False
    if NOT_NAME_EXTRA.match(en):
        return False
    # 必须整体符合"首字母大写的 1–3 个词"
    if not LIKE_HUMAN_NAME.match(en):
        return False
    # 进一步排除：单个词但明显是技术词（如 Western / Transmission）
    words = en.split()
    if len(words) == 1 and len(en) > 12:
        return False
    return True


# 人名形态：英文名（可含 - 或空格）+ 括号（2–6 汉字，后可跟任意长度的补充说明）
# ★ 修正：后缀长度上限从 24 放宽到 60——
#   `Li-jun Di（某中文名，某大学；邮箱 xxx@yyy.edu）` 的后缀有 27 字符，
#   旧上限 24 导致该串**整条匹配不上**，加的那句"邮箱依据"反倒让它逃过门禁。
#   这正是"加了说明就放行"的另一种表现形式：**靠把括号写长来躲过匹配**。
NAME_RE = re.compile(
    r'([A-Z][a-zA-Z]+(?:[- ][A-Za-z]+){0,3})\s*（([\u4e00-\u9fff]{2,6})([，,;；][^）]{0,60})?）')
NAME_RE_ASCII = re.compile(
    r'([A-Z][a-zA-Z]+(?:[- ][A-Za-z]+){0,3})\s*\(([\u4e00-\u9fff]{2,6})([,，;；][^)]{0,60})?\)')
# 特殊形态：邮箱（某中文名）—— 括号左侧是邮箱地址，右侧是中文名
EMAIL_NAME_RE = re.compile(r'[\w.\-]+@[\w.\-]+\s*[（(]([\u4e00-\u9fff]{2,6})[）)]')

# 来源说明豁免 —— ★ 已废止
#
# 上一版留了个后门：只要行内出现"邮箱/原文/来源"字样就放行。
# 结果就是靠这个绕过去的：写成
#   "Li-jun Di（某中文名，某大学；邮箱 xxx@yyy.edu）　← 中文名由邮箱得出"
# 加了句"来源说明"就以为合法——**但这不改变"汉字是猜的"这个事实**。
# 现改为：**没有任何豁免，只要原文无汉字就不许写汉字。**
SRC_HINT = None


def scan(path):
    """扫描一份稿件文件。★ 唯一实现：内部调 `_scan_text`，不重复写判定逻辑（红线 27）。"""
    t = io.open(path, encoding='utf-8', errors='replace').read()
    return _scan_text(t)


def selftest():
    """双向自测（红线 24）。

    没有这一节，"门禁通过"只能证明"没报错"，不能证明"能拦住违规"。
    实测教训：本门禁第一版在五篇合规稿上误报 12 处（全是缩写中译），
    如果只跑真实稿、只看"有没有报错"，这个假阳性根本发现不了。
    """
    cases = [
        # (描述, 文本, 期望是否报嫌疑)
        # ★ 用例中的英文名与汉字均为占位构造，不对应任何真实人物。
        ('编造人名：甲', '作者：Sample Zhang（张甲），某大学', True),
        ('编造人名：乙', 'Samplea Zhang（张乙）为通讯作者', True),
        ('编造人名：丙', '第一作者 Sampleb Li（张丙）', True),
        # ★ 这几条是曾被否决的写法，必须一律拦下
        ('【否决】连字符小写 + 中文名', 'Sample-jun Di（张丁，某大学）', True),
        ('【否决】加"邮箱依据"也不许',
         'Sample-jun Di（张丁，某大学；邮箱 di@example.edu）', True),
        ('【否决】邮箱可推也不许',
         '共同通讯作者：gx@example.edu.cn（张戊）', True),
        ('术语中译：DBG（差异结合基因）', 'DBG（差异结合基因）∩ DEG', False),
        ('术语中译：LPL（脂蛋白脂酶）', 'LPL（脂蛋白脂酶）mRNA 升高', False),
        ('缩写中译：AMPK（已有激活剂）', 'AMPK（已有激活剂）节点', False),
        ('技术词：CM-supernatant（去外泌体上清）', '用 CM-supernatant（去外泌体上清）证明', False),
        ('章节名：Transmission（六条传播路径）', 'Transmission（六条传播路径）', False),
        ('栏目名：New Phenomenon（新现象短通讯）', '栏目：New Phenomenon（新现象短通讯）', False),
        ('单位名：某大学不是人名', 'Sample-jun Di（某大学）团队', False),
        # ★ X43 回归用例：统计方法 / 分子标记写成「英文（中文说明）」不得误判为音译人名
        ('统计方法：Tukey（多重比较）', '采用 Tukey（多重比较）事后检验', False),
        ('分子标记：c-Met（直接靶向）', 'c-Met（直接靶向）信号通路激活', False),
    ]
    bad = 0
    for desc, text, expect in cases:
        # 直接调用扫描内核（写临时文件属于实现细节，这里复用同一逻辑）
        hits = _scan_text(text)
        got = bool(hits)
        mark = '✓' if got == expect else '✗'
        if got != expect:
            bad += 1
        print('  %s %-34s 期望=%s 实际=%s' % (mark, desc[:34], expect, got))
    print()
    return bad


def _scan_text(t):
    """扫描一段文本，返回嫌疑列表（供 selftest 复用，保证与主流程同源）。"""
    hits = []
    for m in EMAIL_NAME_RE.finditer(t):
        cn = m.group(1)
        if cn in WHITELIST_CN or TERM_OK.search(cn):
            continue
        ls = t.rfind('\n', 0, m.start()) + 1
        le = t.find('\n', m.end())
        line = t[ls:le if le > 0 else len(t)]
        hits.append(('(邮箱)', cn, line.strip()[:110]))
    for rx in (NAME_RE, NAME_RE_ASCII):
        for m in rx.finditer(t):
            en, cn, tail = m.group(1), m.group(2), (m.group(3) or '')
            ls = t.rfind('\n', 0, m.start()) + 1
            le = t.find('\n', m.end())
            line = t[ls:le if le > 0 else len(t)]
            if cn in WHITELIST_CN:
                continue
            if TERM_OK.search(cn):
                continue
            if INSTITUTION_OK.search(cn):     # ★ 单位名，非人名
                continue
            if METHOD_OK.search(en):          # ★ 统计方法 / 分子标记，非人名（X43）
                continue
            if not looks_like_person(en):
                continue
            if SRC_HINT is not None and (SRC_HINT.search(line) or SRC_HINT.search(tail)):
                continue
            hits.append((en, cn, line.strip()[:110]))
    return hits


def main():
    args = sys.argv[1:]
    if not args:
        print('用法: python 人名审计.py <稿件.md> [...] | --dir <目录> | --selftest')
        return 2
    if args[0] == '--selftest':
        print('=== 人名审计·双向自测（红线 24）===')
        bad = selftest()
        if bad:
            print('自测不通过：%d 条与期望不符 —— 门禁自身有问题，禁止用于判定。' % bad)
            return 1
        print('自测通过：能拦编造、不误伤术语。')
        return 0
    if args[0] == '--dir':
        files = sorted(glob.glob(os.path.join(args[1], '文献精读_*.md')))
    else:
        files = args

    total = 0
    for f in files:
        if not os.path.exists(f):
            print('[缺文件]', f)
            total += 1
            continue
        hits = scan(f)
        base = os.path.basename(f)
        if hits:
            print('✗ %s —— %d 处疑似音译编造' % (base, len(hits)))
            for en, cn, line in hits:
                print('    %s（%s）' % (en, cn))
                print('        | %s' % line)
            total += len(hits)
        else:
            print('✓ %s —— 无嫌疑' % base)

    print()
    if total:
        print('结论：不通过（%d 处）。逐条核实来源，无据者删中文名或注明出处。' % total)
        return 1
    print('结论：通过。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
