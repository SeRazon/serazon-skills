# -*- coding: utf-8 -*-
"""
门禁回归测试器（双向验证）

用途：每次修改 `图数审计.py` 后，必须跑这个脚本，做两个方向的验证：

  方向一（假阴性）：对全部历史稿件重跑，确认旧缺陷仍被抓住、没有漏报。
  方向二（假阳性）：构造一份合规稿，确认它能通过——门禁过严会把好稿判死。

用法：
    python 回归测试.py --原文 <原文目录> --稿 <稿件目录> [--pairs pairs.txt]

--pairs 格式（每行一篇）：<原文文件名>\t<稿件文件名>\t<篇名>
不给 pairs 就自动配对（原文 txt 与稿件 md 按关键词模糊匹配）。

退出码：
    0 = 两个方向都符合预期
    1 = 有不符合预期的项（漏报 / 误杀 / 配对失败）
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, '图数审计.py')
sys.path.insert(0, HERE)


def _load_audit_module():
    """导入 图数审计.py，复用它的 count_source_figs（避免两处正则不一致）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location('_audit_mod', AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_compliant_fixture(orig_text, name='测试'):
    """**根据原文实际的图/表清单**生成一份合规稿。

    关键：fixture 不能写死图数——必须覆盖该原文真实存在的每一幅图，
    否则门禁会正确地判它"漏图"，测试就会假失败。
    """
    mod = _load_audit_module()
    src = mod.count_source_figs(orig_text)

    def fig_block(i, srcno, is_supp):
        tag = '（依正文）' if is_supp else ''
        return (
            '## 图表 %d：%s — 第 %d 幅\n'
            '- **原文标题**：Fixture Figure %d%s\n'
            '- **图注中译**：MOI 2:1，60 min，浓度 5 µM，n=5\n'
            '- **图表类型**：柱状图\n'
            '- **数据模式**：组间差异 P<0.05，n=5\n'
            '- **学术意义**：在论证链中提供一类证据\n'
            '- **统计方法**：one-way ANOVA + Tukey，n=5\n'
            '- **本图数值清单**：n=5，P<0.05，60 min，5 µM\n\n'
            % (i, srcno, i, i, tag))

    blocks = []
    i = 0
    for n in src['main']:
        i += 1
        blocks.append(fig_block(i, 'Figure %d' % n, False))
    for s in src['supp']:
        i += 1
        if s.startswith('XD'):
            blocks.append(fig_block(i, 'Extended Data Fig. %s' % s[2:], True))
        else:
            blocks.append(fig_block(i, 'Supplementary Figure %s' % s[1:], True))
    for s in src['supp_tabs']:
        i += 1
        blocks.append('## 图表 %d：Supplementary Table %s — 补充表\n'
                      '- **原文标题**：Supplementary Table %s\n'
                      '- **图注中译**：补充表内容说明\n'
                      '- **图表类型**：表格\n'
                      '- **数据模式**：列表数据\n'
                      '- **学术意义**：提供原始数据\n'
                      '- **统计方法**：不适用\n'
                      '- **本图数值清单**：不适用\n\n' % (i, s[1:], s[1:]))
    for n in src['main_tabs']:
        i += 1
        blocks.append('## 图表 %d：Table %d — 主表\n'
                      '- **原文标题**：Table %d\n'
                      '- **图注中译**：主表内容说明\n'
                      '- **图表类型**：表格\n'
                      '- **数据模式**：列表数据\n'
                      '- **学术意义**：提供原始数据\n'
                      '- **统计方法**：不适用\n'
                      '- **本图数值清单**：不适用\n\n' % (i, n, n))

    decl = '全文 **%d 幅主图 + %d 幅补充图 + %d 个补充表 + %d 个主表**。' % (
        len(src['main']), len(src['supp']), len(src['supp_tabs']), len(src['main_tabs']))

    head = (
        '# 文献精读\n'
        '# 板块 1：文献基本资料\n标题、期刊、DOI、作者、基金、伦理。\n'
        '# 板块 2：主要研究内容\n研究对象分量：该对象的流行学与临床重要性、'
        '为什么这个细胞或模型值得研究，构成有分量的空白。科学问题、假说、逻辑链、核心发现。\n'
        '# 板块 3：研究方法\n虫株或细胞、动物、分离、刺激体系、检测、抑制、对照、统计逐项列出。\n'
        '# 板块 4：样本量\n样本类型：外周血来源细胞。样本来源：实验动物中心。'
        '纳入与排除标准：无剔除。每组样本量：n=5，误差线 mean±SD。\n'
        '# 板块 5：研究时间\n关键节点：刺激 0/30/60/90/120 min，抑制剂预处理 2 h，'
        '培养 24–36 h，检测紧随刺激结束。按实验时序交代先后关系。\n'
        '# 板块 6：图表解析\n' + decl + '\n')
    mid = (
        '# 板块 7：主要结论\n形态证据（Figure 1）；量效证据（补充图）；通路证据。'
        '每条标注证据强度与来源图号。\n'
        '# 板块 8：创新点\n'
        '- 理论创新 ⭐⭐⭐☆☆：首次报道该现象\n'
        '- 方法创新 ⭐⭐☆☆☆：多模态验证链\n'
        '- 命名创新 ⭐☆☆☆☆：本文未新造术语，无命名类贡献\n'
        '- 应用创新 ⭐⭐☆☆☆：为体内研究提供起点\n'
        '# 板块 9：局限性\n作者自述、我识别出的若干条、对结论的影响判断。\n'
        '# 板块 10：研究可复刻性\n总体判断：有条件可复刻。\n'
        '| 维度 | 评分 | 依据 |\n|---|---|---|\n'
        '| 模型可获取性 | 5 | 材料易得 |\n'
        '| 试剂与序列公开度 | 4 | 给出货号 |\n'
        '| 仪器与方法记载完整度 | 3 | 部分参数缺失 |\n'
        '| 原始数据可得性 | 2 | 无公共库编号 |\n'
        '| 统计方法清晰度 | 4 | 检验明确 |\n'
        '缺失清单：株系编号、独立重复次数、完整制样参数。\n'
        '与使用者主线衔接：可接到使用者相关研究方向。\n'
        '## 可引用金句\n'
        '1. "Our data lay a foundation for exploring this in vivo."（为体内探索奠定基础）—— PAGE 3 L208。\n'
        '2. "Whether this phenomenon occurs remains undetermined."（此前尚未确定）—— PAGE 1 L43。\n'
        '3. "In this study we demonstrated the core finding."（本研究表明核心发现）—— PAGE 3 L204。\n'
        '# 板块 11：核心要点总结\n100 字概括、三要点总结、引用建议。\n'
        '## 对本人的用法\n本文的方法模板可接到使用者某条研究主线上，'
        '接在体外验证这一步，解决机制做实的问题。\n')
    tail = '（补足以达字数下限）。' * 500
    return head + ''.join(blocks) + mid + tail

# 注意：合规 fixture 不写死，而是用 build_compliant_fixture() 按原文图数动态生成——
# 写死的 fixture 只能覆盖固定图数，拿去测别的原文会被门禁正确判为"漏图"（假失败）。


def run_audit(orig, md):
    """调用图数审计.py，返回 (exit_code, stdout)。"""
    import subprocess
    r = subprocess.run([sys.executable, AUDIT, '--原文', orig, '--稿', md],
                       capture_output=True, text=True, encoding='utf-8')
    return r.returncode, r.stdout or ''


def auto_pairs(orig_dir, md_dir):
    """按关键词模糊配对：原文 txt 与稿件 md 共享足够多的中英词元。"""
    def toks(s):
        return set(re.findall(r'[A-Za-z]{4,}|[\u4e00-\u9fff]{2,}', s.lower()))
    txts = [f for f in os.listdir(orig_dir) if f.lower().endswith('.txt')]
    mds = [f for f in os.listdir(md_dir) if f.lower().endswith('.md')]
    pairs = []
    used = set()
    for m in mds:
        mt = toks(m)
        best, best_s = None, 0
        for t in txts:
            if t in used:
                continue
            s = len(mt & toks(t))
            if s > best_s:
                best, best_s = t, s
        if best and best_s >= 2:
            used.add(best)
            pairs.append((best, m, m[:30]))
    return pairs


def unit_checks():
    """门禁自身的单元断言（不依赖原文/稿件目录）。

    这些都是**真实抓出来过的 bug**，每一条对应一次误判；
    改动脚本后若这里变红，说明修复被改回退了。
    """
    mod = _load_audit_module()
    results = []

    def chk(name, cond, detail=''):
        results.append((name, bool(cond), detail))

    # A. 列表展开必须有上限（防"Figure 1, 2, ... 15"被吃成 15 幅 → 假阳性）
    got = sorted(mod.expand_lists(
        'Figure 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 were analyzed',
        mod.RE_MAIN), key=int)
    chk('列表展开有上限（病态输入不超 7 项）', len(got) <= 7, 'got=%s' % got)
    # A2. 正常短列表仍必须能展开（护栏不能误伤）
    got2 = sorted(mod.expand_lists('Supplementary Figs. S1 and S2 were done',
                                   mod.RE_SUPP_S))
    chk('正常列表仍能展开', got2 == ['S1', 'S2'], 'got=%s' % got2)
    # A3. ★ 裸数字尾巴必须继承 S 前缀（真实 bug X35，2026-09-20 第四轮）
    #     原文写 `Figures S8 and 9` = `Figure S8 and Figure S9`。
    #     旧写法把尾巴收成裸 `9` → 门禁要求稿里出现"编号为 9 的补充图" →
    #     任何稿件都写不出这种编号 → **该稿永远无法通过**（实测报"未覆盖 1 幅：9"）。
    got3 = sorted(mod.expand_lists('Figures S8 and 9 (n = 6).', mod.RE_SUPP_S,
                                   prefix_letter=True), key=lambda x: (x[:1], int(''.join(c for c in x if c.isdigit()) or 0)))
    chk('裸数字尾巴继承 S 前缀（X35）', got3 == ['S8', 'S9'], 'got=%s' % got3)
    # A4. 反方向：已带前缀的尾巴不得被改写成 S+数字
    got4 = sorted(mod.expand_lists('Supplementary Figs. S1 and S2 were done',
                                   mod.RE_SUPP_S, prefix_letter=True))
    chk('带前缀的尾巴不被二次加前缀（X35 反向）', got4 == ['S1', 'S2'], 'got=%s' % got4)
    # A5. 反方向：XD / PLAIN 体系不受前缀继承影响（它们的编号本来就带字母/需外部补）
    got5 = sorted(mod.expand_lists('Extended Data Fig. 1 and 2', mod.RE_SUPP_XD))
    chk('XD 体系不受前缀继承影响（X35 隔离）', got5 == ['1', '2'], 'got=%s' % got5)

    # B. 声明剥离不得吃掉真实图号引用（防"凭空报零解析"）
    body = mod.strip_declarations(
        '如图 1 所示，全文共 5 幅主图与 3 幅补充图被逐条解析，'
        'Supplementary Fig. S1 显示时间依赖。')
    chk('混排句保留真解析 S1', 'Supplementary Fig. S1' in body, body[:60])
    # B2. 范围声明必须被挖掉（防"声明冒充解析"）
    body2 = mod.strip_declarations('全文共 7 幅扩展数据图（Extended Data Fig. 1–7）已解析。')
    chk('范围声明被剥离（不残留 XD1）',
        'Extended Data Fig. 1' not in body2, body2[:60])
    # B3. 真实稿件那行（含 + 连接）必须整行剥离
    body3 = mod.strip_declarations(
        '全文 7 幅主图（Fig. 1–7）+ 7 幅扩展数据图（Extended Data Fig. 1–7）+ 5 个补充表')
    leak = [m.group(1) for m in mod.RE_REF_XD.finditer(body3)]
    chk('“+ 连接”的复合声明整行剥离（不残留 XD）', not leak, 'leak=%s' % leak)
    # B4. 列表式真解析必须整体保留
    body4 = mod.strip_declarations('全文共 3 幅补充图，Supplementary Fig. S1、S2、S3 分别展示。')
    chk('列表式真解析整体保留',
        all(x in body4 for x in ['S1', 'S2', 'S3']), body4[:70])

    # C. 金句条目计数须容忍 markdown 修饰（真实 bug X17）
    #    稿件常写成 `1. > "**原文**"`（引用块 + 加粗），旧正则要求引号紧跟 "N. "，
    #    于是 3 条合规金句被数成 0 条 → 把合规稿判成"不通过"（假阴性）。
    quote_item = re.compile(r'^\s*(?:\d+\.|[-*])\s*(?:>\s*)?(?:\*\*|__)?\s*["“]', re.M)
    for sample, want in [
        ('1. "In this study we demonstrated the core finding."（本研究表明核心发现）—— PAGE 3', 1),
        ('1. > "**In summary, we demonstrated that NETs form.**"（摘  要）—— p.1736', 1),
        ('- > "**quote**" —— L1', 1),
        ('2. **"bold inside number"** —— L2', 1),
    ]:
        gotq = len(quote_item.findall(sample))
        chk('金句计数容忍引用块/加粗：%s' % sample[:28], gotq == want,
            'want=%d got=%d' % (want, gotq))
    # C2. 仍必须拒绝"编号但无引号"的行（不能被放宽到误数普通编号列表）
    chk('金句计数仍拒绝无引号编号行',
        len(quote_item.findall('1. 这里是普通说明，没有引号。\n2. 另一条说明。')) == 0)

    # D. 板块级上限提示不得把合规稿判为硬缺陷（上限只能是 warning）
    #    真实 bug：板块 6 的切分点在"## 板块 6 补充说明"处被截断，
    #    导致板块 6/7 的字数切分与实际不符；上限若做成 problems 会误杀。
    chk('板块 6 上限键存在且为提示位', 6 in mod.UPPER, 'UPPER=%s' % mod.UPPER)

    # E. ★ 覆盖判定必须"逐条目"，不能"全板块搜到就算"（真实 bug X18，静默漏报）
    #    构造：板块 6 只有 2 个主图条目，S1 只在说明文字里被提一句。
    #    旧逻辑会把 S1 算作"已覆盖" → 门禁通过 → 交付后才发现缺图。
    fake_s6 = (
        '## 图表 1：Figure 1 — 主图一\n- **原文标题**：Fig 1\n'
        '- **图注中译**：x\n- **图表类型**：柱\n- **数据模式**：x\n'
        '- **学术意义**：x\n- **统计方法**：x\n- **本图数值清单**：x\n\n'
        '## 图表 2：Figure 2 — 主图二\n- **原文标题**：Fig 2\n'
        '- **图注中译**：x\n- **图表类型**：柱\n- **数据模式**：x\n'
        '- **学术意义**：x\n- **统计方法**：x\n- **本图数值清单**：x\n\n'
        '## 板块 6 补充说明\n本文补充图 Supplementary Fig. S1 已在别处解析。\n')
    blocks = mod._split_entry_blocks(fake_s6)
    chk('条目切分只切出真条目（2 条，不含说明段）', len(blocks) == 2,
        'n=%d' % len(blocks))
    joined = '\n'.join(blocks)
    chk('说明段里的 S1 不算条目解析',
        not mod.RE_REF_S.search(joined),
        'S1 泄漏进条目体')

    # F. ★ 创新星级必须在"板块 8 内"计数，不能被板块 6 里的 ★ 抢走起点（真实 bug X19）
    #    构造：板块 6 里用 ★ 做要点标记，板块 8 里放 4 颗真正的评级星。
    #    旧逻辑从"全篇第一个 ★"开始数到下一个标题 → 起点落在板块 6 → 只数到 0 颗。
    fake2 = (
        '# 板块 6：图表解析\n'
        '## 图表 1：Figure 1 — 图\n- **数据模式**：★ 关键对照\n'
        '- **学术意义**：普通文字。\n\n'
        '## 图表 2：Figure 2 — 图\n- **数据模式**：普通。\n\n'
        '# 板块 8：创新点\n'
        '## 1. 理论创新　⭐⭐⭐\n'
        '## 2. 方法创新　⭐⭐\n'
        '## 3. 命名创新　⭐\n'
        '## 4. 应用创新　⭐\n')
    probs, warns = [], []
    stat = mod.check_whole_doc(fake2, probs, warns)
    got_star = stat['创新星级']['count']
    chk('创新星级在板块 8 内计数（不被板块 6 的 ★ 抢走）', got_star >= 4,
        'count=%d scope=%s' % (got_star, stat['创新星级'].get('scope')))
    chk('板块 8 星级达标时不得报"缺"',
        not any('创新星级' in p for p in probs),
        '误报：%s' % [p for p in probs if '创新星级' in p])
    # F2. 板块 8 真的没星时，必须仍然报缺（不能修成永远通过）
    fake3 = fake2.replace('⭐', '')
    probs3, warns3 = [], []
    stat3 = mod.check_whole_doc(fake3, probs3, warns3)
    chk('板块 8 无星时仍报缺（未被放宽）',
        any('创新星级' in p for p in probs3),
        'count=%d' % stat3['创新星级']['count'])

    # G. ★ 板块切分必须以**一级标题**为界（真实 bug X20，假阴性）
    #    稿件里的小节 `## 板块 6 补充说明` 不得被当成"第二个板块 6"，
    #    否则板块 6 被切成两段，字数地板误判"偏薄"——合规稿被冤枉。
    fake4 = (
        '# 板块 6：图表解析\n'
        + ('中文内容。' * 700) + '\n'          # ≈ 2800 中文字，远超地板 1200
        '## 板块 6 补充说明：本篇图表结构的特征\n'
        '这一小节也属于板块 6，必须一并计入。\n'
        '# 板块 7：主要结论\n中文结论。\n')
    secs = mod.slice_sections(fake4)
    chk('板块切分不被 `## 板块 N …` 小节截断（bug X20）',
        6 in secs and 7 in secs and '补充说明' in secs[6],
        'sections=%s' % sorted(secs.keys()))
    def _cjk(x):
        import re as _re
        return len(_re.findall(r'[\u4e00-\u9fff]', x))
    chk('板块 6 字数含小节内容（≥ 地板 1200）',
        _cjk(secs.get(6, '')) >= 1200,
        'cjk=%d' % _cjk(secs.get(6, '')))
    # G2. 反方向：真正的板块 7 一级标题仍必须正确切开
    chk('真正的板块 7 仍被正确切出',
        '中文结论' in secs.get(7, '') and '补充说明' not in secs.get(7, ''),
        'sec7=%r' % secs.get(7, '')[:40])

    # H. ★ "声明无表/无图"的收尾块不得被算成图条目（真实 bug X21，假阳性）
    #    实测来源：COVID-19 综述稿原文只有 Figure 1、Figure 2 两图，
    #    稿件因此写了两图七栏 + 一个 `## 图表 3：全文表格盘点（★ 如实标注）`，
    #    旧逻辑把该声明块算成第 3 个条目 → 6 条七栏齐全度全部误报"缺"。
    #    这是"惩罚诚实"的最坏信号，必须拦住。
    s6_fake = (
        '## 图表 1：Figure 1 — 示例主图\n'
        '- **原文标题**：Figure 1. X\n- **图注中译**：…\n- **图表类型**：…\n'
        '- **数据模式**：…\n- **学术意义**：…\n- **统计方法**：…\n- **本图数值清单**：…\n'
        '## 图表 2：Figure 2 — 示例机制图\n'
        '- **原文标题**：Figure 2. Y\n- **图注中译**：…\n- **图表类型**：…\n'
        '- **数据模式**：…\n- **学术意义**：…\n- **统计方法**：不适用\n- **本图数值清单**：…\n'
        '## 图表 3：全文表格盘点（★ 如实标注）\n'
        '本篇 **0 个表格**，正文与补充材料均无。此处如实标注，不虚构。\n')
    blks = mod._split_entry_blocks(s6_fake)
    chk('“全文表格盘点”声明块不算图条目（bug X21）',
        len(blks) == 2, 'blocks=%d' % len(blks))
    chk('两幅真图仍被完整切出',
        'Figure 1' in blks[0] and 'Figure 2' in blks[1],
        'heads=%r' % [b[:28] for b in blks])
    # H2. 反方向：形态正常的三图稿仍必须切出 3 条（不能被收尾词过滤误伤）
    s6_ok3 = s6_fake.replace(
        '## 图表 3：全文表格盘点（★ 如实标注）\n本篇 **0 个表格**，正文与补充材料均无。此处如实标注，不虚构。\n',
        '## 图表 3：Figure 3 — 第三幅真图\n- **原文标题**：Figure 3. Z\n')
    blks3 = mod._split_entry_blocks(s6_ok3)
    chk('正常三图稿仍切出 3 条（过滤未误伤）',
        len(blks3) == 3, 'blocks=%d' % len(blks3))
    # H3. ★ 元断言：条目计数**只有一条实现路径**。
    #     真实教训：X21 修在了 _split_entry_blocks，但 audit() 里另有 inline
    #     `RE_HEAD_FIG.findall` 独立计数，导致审计报告仍报 3 条。
    #     凡"同一事实有两处实现"，改一处必留另一处 —— 此处把两条路径钉死相等。
    chk('条目计数两路径一致（_entry_head_hits == audit 口径）',
        len(mod._entry_head_hits(s6_fake)) == len(blks),
        'helper=%d blocks=%d' % (len(mod._entry_head_hits(s6_fake)), len(blks)))
    chk('audit() 不再有 inline RE_HEAD_FIG 计数（X21 根因）',
        not any(
            'RE_HEAD_FIG.findall' in ln and not ln.lstrip().startswith('#')
            for ln in io.open(os.path.join(os.path.dirname(mod.__file__),
                                           '图数审计.py'),
                              encoding='utf-8')),
        '仍存在 inline findall 计数（非注释行）')

    # I. ★ 图条目标题级别必须覆盖**一级标题**（真实 bug X34，2026-09-20 第四轮）
    #    某篇的 8 个图条目写成 `# 图表 N：Figure N — …`（一级标题），
    #    旧正则只要 `#{2,4}` → 条目数 0 → 七栏检查被静默跳过 + 主图零解析不阻断
    #    → 一份 5,796 字的板块 6 被判"通过"。这是**静默给假成品**。
    s6_lvl1 = (
        '# 图表 1：Figure 1 — 甲\n'
        '- **原文标题**：A\n- **图注中译**：B\n- **图表类型**：C\n'
        '- **数据模式**：D\n- **学术意义**：E\n- **统计方法**：F\n- **本图数值清单**：G\n\n'
        '# 图表 2：Figure 2 — 乙\n'
        '- **原文标题**：H\n- **图注中译**：I\n- **图表类型**：J\n'
        '- **数据模式**：K\n- **学术意义**：L\n- **统计方法**：M\n- **本图数值清单**：N\n')
    chk('一级标题图条目被认出（X34）',
        len(mod._entry_head_hits(s6_lvl1)) == 2,
        'n=%d' % len(mod._entry_head_hits(s6_lvl1)))
    chk('一级标题图条目也能切块（X34）',
        len(mod._split_entry_blocks(s6_lvl1)) == 2,
        'n=%d' % len(mod._split_entry_blocks(s6_lvl1)))
    # I2. 反方向：`# 板块 N` 主标题不得被误认成图条目
    chk('“# 板块 N”不被误认成图条目（X34 反向）',
        len(mod._entry_head_hits('# 板块 6：图表解析\n正文\n')) == 0)

    # J. ★ 主图零解析必须硬拦（X34 连带；旧逻辑只拦补充图，主图零解析仅 warning）
    #    构造：原文 2 主图 0 补图（COVID-19 型），稿件板块 6 一个图号都不引用。
    probs_j, warns_j = [], []
    res_j = mod.audit(
        'Figure 1. A.\nFigure 2. B.\n',          # 原文：2 主图、0 补图
        '# 板块 6：图表解析\n本文图表结构见正文说明，此处从略。\n'
        + '# 板块 7：主要结论\n' + '中文字内容。' * 50 + '\n')
    chk('主图零解析被硬拦（EXIT=1）',
        bool(res_j['problems']),
        'problems=%d' % len(res_j['problems']))
    chk('主图零解析的措辞明确（含“主图零解析”）',
        any('主图零解析' in p for p in res_j['problems']),
        'problems=%s' % str(res_j['problems'])[:120])

    # K. ★ 板块号必须有词边界，否则 `板块 7` 会吞并 `板块 70`（真实 bug X36）
    #    旧写法 `^#+\\s*板块\\s*7` 命中 `# 板块 70 …` 的前缀 → slice_section6
    #    在 70 之前提前截断，后面的图条目被静默丢弃（条目数变少 → 七栏漏检）。
    #    同理 `板块 1` 会命中 `板块 10/11/12`。
    #
    #    不变式：**精确号码才是边界**。`板块 7` 切段，`板块 70` 不是边界
    #    （它只是另一个编号，内容应留在段内，不该被丢）。
    md70 = ('# 板块 6：图表解析\n'
            '## 图表 1：Figure 1 — 甲\n- **原文标题**：A\n'
            '## 图表 2：Figure 2 — 乙\n- **原文标题**：B\n'
            '# 板块 70：附录\n本节不应属于板块 6。\n')
    seg70, err70 = mod.slice_section6(md70)
    chk('`板块 70` 不被当成 `板块 7` 边界（X36）',
        err70 is None and '本节不应属于板块 6' in (seg70 or ''),
        'seg_tail=%r' % (seg70 or '')[-40:])
    chk('板块 70 情形下两图条目仍被切出（X36）',
        len(mod._entry_head_hits(seg70 or '')) == 2,
        'n=%d' % len(mod._entry_head_hits(seg70 or '')))
    # K1-b. 正例：真有 `板块 7` 时，它**必须**是边界，把 70 挡在段外
    md7_70 = md70.replace('# 板块 70：附录', '# 板块 7：主要结论')
    seg77, _e = mod.slice_section6(md7_70)
    chk('真有 `板块 7` 时正确截断（X36 正例）',
        '附录' not in (seg77 or '') and len(mod._entry_head_hits(seg77 or '')) == 2,
        'seg_tail=%r' % (seg77 or '')[-30:])
    # K2. slice_sections 同病：`板块 1` 不得吞并 `板块 10`
    secs_k = mod.slice_sections(
        '# 板块 1：基本资料\n甲内容\n'
        '# 板块 10：可复刻性\n乙内容\n')
    chk('板块 1 不吞并板块 10（X36）',
        1 in secs_k and 10 in secs_k and '乙内容' in secs_k.get(10, '')
        and '乙内容' not in secs_k.get(1, ''),
        'keys=%s' % sorted(secs_k.keys()))
    # K3. 正常编号相邻时仍必须逐一切开（词边界不得误伤）
    secs_k3 = mod.slice_sections(
        '# 板块 6：图表解析\nA\n# 板块 7：主要结论\nB\n# 板块 8：创新点\nC\n')
    chk('相邻板块号仍被逐一切开（X36 反向）',
        all(k in secs_k3 for k in (6, 7, 8)),
        'keys=%s' % sorted(secs_k3.keys()))

    # L. ★ 负例 fixture 必须**保持不合规**（元断言）
    #    方向一依赖一份"应被拦下"的稿件。若有人（包括我）顺手把 fixture 改好，
    #    方向一会静默退化成"只测 pass 项"，假阴性防线就此失效且**无人察觉**。
    #    故在此钉死：fixture 跑门禁必须 EXIT=1。
    fx_dir = HERE  # fixture 已平铺在 scripts/ 下（技能包仅两级目录）
    fx_orig = os.path.join(fx_dir, '负例_原文.txt')
    fx_md = os.path.join(fx_dir, '负例_稿件.md')
    if os.path.exists(fx_orig) and os.path.exists(fx_md):
        code_fx, out_fx = run_audit(fx_orig, fx_md)
        chk('负例 fixture 仍被拦下（EXIT=1，防被改好）', code_fx == 1,
            'EXIT=%d' % code_fx)
    else:
        chk('负例 fixture 文件存在', False, '缺失 %s' % fx_dir)

    for name, ok_, detail in results:
        print('  %s %s%s' % ('✓' if ok_ else '✗', name,
                             ('  [' + detail + ']') if (detail and not ok_) else ''))
    return [n for n, o, _ in results if o is False]


def jcr_checks():
    """影响因子匹配的单元断言（对应 2026-09-21 抓出的假匹配 bug X48）。

    X48 事实：`jcr_helper.match()` 第 3 级包含兜底 `nk in n` **无长度门槛**，
    导致不存在的刊名因含有短刊名子串（如 `RNA`）被匹配到**别的**期刊，
    返回**错误的**影响因子。实测：
        THIS IS NOT A JOURNAL NAME 12345        → 4.3  Q2（错！应为 None）
        Brain Research Bulletin of Nowhere      → 12.9 Q1（错！应为 None）
        JOURNAL THAT DOES NOT EXIST IN JCR XYZ  → 4.3  Q2（错！应为 None）
    污染后果：假 IF 一路流进 meta.json → 导航库 if_max/if_min/if_avg → 网页徽标。

    修法：`MIN_SUBSTR_LEN=12` + `MIN_SUBSTR_RATIO=0.75`（双向包含都须满足）。

    ★ 本函数的意义在于**钉住"不许把假匹配改回来"**：
      若有人为了"提高命中率"把门槛调松，这里立刻变红。
    """
    results = []

    def chk(name, cond, detail=''):
        results.append((name, bool(cond), detail))

    try:
        sys.path.insert(0, HERE)
        import jcr_helper
        jcr_helper.resolve  # noqa: B018  (确认模块可用)
    except Exception as e:  # pragma: no cover
        chk('jcr_helper 可导入', False, '%s: %s' % (type(e).__name__, e))
        for name, ok_, detail in results:
            print('  %s %s%s' % ('✓' if ok_ else '✗', name,
                                 ('  [' + detail + ']') if (detail and not ok_) else ''))
        return [n for n, o, _ in results if o is False]

    # A. 编造刊名**必须**返回 None（这几条是 X48 的原始复现用例，逐字保留）
    fake_cases = [
        'THIS IS NOT A JOURNAL NAME 12345',
        'Brain Research Bulletin of Nowhere',
        'JOURNAL THAT DOES NOT EXIST IN JCR AT ALL XYZ',
        'A Totally Fake Journal For Testing Purposes 987',
        'Zzz Nonexistent Periodical Qqq',
    ]
    for name in fake_cases:
        try:
            got = jcr_helper.match(name)
        except Exception as e:
            got = 'EXC:%s' % type(e).__name__
        chk('假刊名返回 None：%s' % name[:38], got is None, 'got=%r' % (got,))

    # B. 真刊名**必须**仍能匹配（护栏不能误伤真实查询）
    real_cases = [
        ('Parasites & Vectors', True),
        ('Nature Communications', True),
        ('Nat. Commun.', True),
        ('Advanced Science', True),
        ('Adv. Sci.', True),
        ('Journal of Biological Chemistry', True),
    ]
    for name, _ in real_cases:
        try:
            got = jcr_helper.match(name)
        except Exception as e:
            got = 'EXC:%s' % type(e).__name__
        chk('真刊名仍能匹配：%s' % name, got is not None, 'got=%r' % (got,))

    # C. 短刊名（≤4 字符，表内 79 个）不得被当子串到处命中。
    #    反例构造：随便一个含 `RNA` 的长串，不应命中 RNA 那本刊。
    probe = 'STUDIES ON SOMETHING RNA RELATED BUT NOT A JOURNAL'
    try:
        got = jcr_helper.match(probe)
    except Exception as e:
        got = 'EXC:%s' % type(e).__name__
    chk('含短刊名子串的长串不被误命中', got is None, 'got=%r' % (got,))

    # D. 门槛常量必须仍在位（防止被静默删掉退回旧行为）
    chk('MIN_SUBSTR_LEN 门槛在位（≥8）',
        getattr(jcr_helper, 'MIN_SUBSTR_LEN', 0) >= 8,
        'MIN_SUBSTR_LEN=%r' % getattr(jcr_helper, 'MIN_SUBSTR_LEN', None))
    chk('MIN_SUBSTR_RATIO 门槛在位（≥0.5）',
        getattr(jcr_helper, 'MIN_SUBSTR_RATIO', 0) >= 0.5,
        'MIN_SUBSTR_RATIO=%r' % getattr(jcr_helper, 'MIN_SUBSTR_RATIO', None))

    for name, ok_, detail in results:
        print('  %s %s%s' % ('✓' if ok_ else '✗', name,
                             ('  [' + detail + ']') if (detail and not ok_) else ''))
    return [n for n, o, _ in results if o is False]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--原文', required=True, help='原文 txt 所在目录')
    ap.add_argument('--稿', required=True, help='稿件 md 所在目录')
    ap.add_argument('--pairs', default=None, help='配对清单（每行：原文\\t稿件\\t篇名）')
    a = ap.parse_args()

    fails = []

    # ---------- 方向零：门禁自身单元断言 ----------
    print('=' * 72)
    print('方向零（单元）：门禁内部逻辑断言（对应历史真实 bug）')
    print('=' * 72)
    unit_fails = unit_checks()
    for n in unit_fails:
        fails.append('单元断言失败：' + n)

    # ---------- 方向三：影响因子匹配（对应 bug X48） ----------
    print()
    print('=' * 72)
    print('方向三（影响因子）：假匹配必须被拦住、真刊名必须仍能匹配')
    print('=' * 72)
    jcr_fails = jcr_checks()
    for n in jcr_fails:
        fails.append('影响因子匹配失败：' + n)

    if a.pairs:
        pairs = []
        for line in io.open(a.pairs, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                expect = parts[3].strip().lower() if len(parts) > 3 else 'pass'
                if expect not in ('pass', 'violate'):
                    expect = 'pass'
                pairs.append((parts[0], parts[1],
                              parts[2] if len(parts) > 2 else parts[1],
                              expect))
    else:
        pairs = [(o, m, n, 'pass') for o, m, n in auto_pairs(a.原文, a.稿)]

    # ---------- 方向一：假阴性 ----------
    #
    # ★ 语义澄清（2026-09-20 第四轮修正，属**诚实性**修复）：
    #   本方向原文写的是"历史稿件应被拦下"，但**事实已变**——五篇重写轮之后，
    #   outputs/ 里的稿件全部是**已修好的合规稿**，它们**应该 EXIT=0**。
    #   旧逻辑不加区分地把每篇 EXIT=0 一律判为"漏报！"，于是：
    #     · 报告打印 5 行 "**漏报！**"，看起来门禁全线失灵；
    #     · 整体 EXIT=1，把"回归测试失败"这个刺眼结论交出去；
    #     · 而真实情况是**门禁完全正常**、稿件也合规。
    #   这是"报告结论超出实际证据"的反向版本：**把正常的通过说成漏报**。
    #   更坏的是它会训练我"忽略这个方向的告警"——狼来了。
    #
    #   修法：显式区分稿件的**期望态**。配对文件第 4 列可写 `violate`（应被拦下）
    #   或 `pass`（应通过，默认）。期望 `pass` 而拿到 EXIT=1 → 才是真问题（误杀）。
    print('=' * 72)
    print('方向一（假阴性）：按配对清单声明的期望态逐篇核验')
    print('=' * 72)
    print('  期望态由配对文件第 4 列声明：violate=应被拦下 / pass=应通过（缺省）')
    print()
    if not pairs:
        print('  （无历史违规稿：五篇均已重写为合规版，本方向无 violate 项）')
        print('      —— 这是**预期状态**，不是失败。'
              '要恢复本方向，在 --pairs 清单里把某篇的期望态标成 violate 即可。')
    for o, m, name, expect in pairs:
        # ★ 配对清单里的路径允许两种写法：
        #   · 相对 --原文/--稿 目录的裸文件名（历史用法）
        #   · 相对**清单文件自身**的路径（新用法，供常驻 fixture 使用，如 ./负例_原文.txt）
        #   判据：裸文件名就按目录拼；含路径分隔符的按清单文件所在目录解析。
        def _resolve(p, base_dir):
            if os.sep in p or '/' in p:
                return os.path.normpath(
                    os.path.join(os.path.dirname(os.path.abspath(a.pairs)), p))
            return os.path.join(base_dir, p)
        op, mp = _resolve(o, a.原文), _resolve(m, a.稿)
        if not (os.path.exists(op) and os.path.exists(mp)):
            print('  ? %-14s 文件缺失，跳过' % name)
            fails.append('文件缺失：' + name)
            continue
        code, out = run_audit(op, mp)
        nprob = len(re.findall(r'^\d+\. ', out.split('### 提示')[0], re.M))
        supp = re.search(r'\| 补充图 \| (\d+) \|', out)
        if expect == 'violate':
            good = (code == 1)
            verdict = 'OK（已拦下）' if good else '**漏报！**'
            if not good:
                fails.append('漏报：' + name)
        else:
            good = (code == 0)
            verdict = 'OK（通过）' if good else '**误杀！**'
            if not good:
                fails.append('误杀（期望通过却 EXIT=1）：' + name)
        print('  %-4s %-14s 期望=%-8s EXIT=%d 补充图(源)=%s 硬缺陷=%d 条  %s'
              % ('✓' if good else '✗', name, expect, code,
                 supp.group(1) if supp else '?', nprob, verdict))

    # ---------- 方向二：假阳性 ----------
    print()
    print('=' * 72)
    print('方向二（假阳性）：合规稿应通过（EXIT=0）')
    print('=' * 72)
    # ★ 判据用"**有没有可用的真实稿配对**"，而不是"pairs 是否为空"。
    #   技能自带的配对清单是**模板**（只有负例 fixture 那一行），
    #   此时 pairs 非空但没有任何可用的真实稿——旧判据会走到 else 分支、
    #   挑不到原文而报"无法取得原文做假阳性测试"，把一条本该跑的防线整段丢掉。
    usable_pairs = [p for p in pairs
                    if os.path.exists(os.path.join(a.原文, p[0]))]
    if not usable_pairs:
        # 自足兜底：无可用真实稿时，用**合成原文**做端到端假阳性测试。
        # 目的：方向二检验的是"门禁会不会误杀好稿"，它只依赖"一份合规稿 + 一份对应原文"，
        #       与"是否存在真实测试稿"无关。若因此整段跳过，
        #       等于在"模板清单"的日子里丢掉最重要的那条防线（过严误杀）。
        synth = os.path.join(os.path.dirname(os.path.abspath(a.稿)),
                             '_fixture_synth_orig.txt')
        # ★ 合成原文必须**同时含主图与补充图**：只写 2 幅主图 0 幅补图的原文
        #   是一条过弱的用例——它恰好绕开门禁最强的补充图差集检查，
        #   拿它测"会不会误杀"，等于用最松的题面考最难的关卡。
        io.open(synth, 'w', encoding='utf-8').write(
            'Figure 1. Synthetic main figure for harness.\n'
            'Figure 2. Synthetic second figure.\n'
            'Extended Data Fig. 1. Synthetic supplementary figure.\n'
            'Extended Data Fig. 2. Synthetic supplementary figure.\n'
            'Supplementary Fig. 1. Plain-numbered supplementary figure.\n'
            'Supplementary Table 1. Synthetic supplementary table.\n')
        fixture_orig = synth
        print('  （无可用真实稿配对，改用合成原文做端到端假阳性测试：'
              '2 主图 + 3 补充图 + 1 补充表）')
    else:
        # 优先挑一篇**期望通过且原文有补充图**的稿做假阳性测试；
        # 挑不到才退回第一篇。理由同上：补充图差集是门禁最强的检查项。
        pick = None
        _mod = _load_audit_module()
        for o, m, nm, ex in usable_pairs:
            if ex != 'pass':
                continue
            srcp = os.path.join(a.原文, o)
            if not os.path.exists(srcp):
                continue
            try:
                txt = io.open(srcp, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            if _mod.count_source_figs(txt)['supp']:
                pick = o
                break
        fixture_orig = os.path.join(a.原文, pick) if pick else \
            os.path.join(a.原文, usable_pairs[0][0])
        if pick:
            print('  （假阳性用例选自含补充图的原文：%s）' % pick)
    if fixture_orig and os.path.exists(fixture_orig):
        tmp = os.path.join(os.path.dirname(os.path.abspath(fixture_orig)),
                           '_fixture_compliant.md')
        orig_text = io.open(fixture_orig, encoding='utf-8', errors='ignore').read()
        io.open(tmp, 'w', encoding='utf-8').write(
            build_compliant_fixture(orig_text))
        try:
            code, out = run_audit(fixture_orig, tmp)
            nprob = re.findall(r'^\d+\. (.+)$', out.split('### 提示')[0], re.M)
            if code == 0:
                print('  ✓ 合规稿 EXIT=0（通过）')
            else:
                print('  ✗ 合规稿 EXIT=%d —— 门禁过严，误杀好稿！' % code)
                for p in nprob:
                    print('      误判项：' + p.strip()[:100])
                fails.append('假阳性：合规稿被误杀')
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
            if not usable_pairs and os.path.exists(fixture_orig):
                os.remove(fixture_orig)      # 合成原文也要清掉，不留垃圾
            print('  （临时 fixture 已删除）')
    else:
        print('  ！无法取得原文做假阳性测试')
        fails.append('假阳性测试无法执行（缺原文）')

    print()
    print('=' * 72)
    if fails:
        print('回归测试未通过，问题：')
        for f in fails:
            print('  - ' + f)
        return 1
    n_viol = sum(1 for *_x, ex in pairs if ex == 'violate')
    n_pass = sum(1 for *_x, ex in pairs if ex == 'pass')
    print('回归测试通过：单元断言全绿；影响因子匹配全绿；'
          '%d 篇期望拦下的全部 EXIT=1；%d 篇期望通过的未被误杀；合规 fixture EXIT=0。'
          % (n_viol, n_pass))
    return 0


if __name__ == '__main__':
    sys.exit(main())
