# -*- coding: utf-8 -*-
"""
视觉规格门禁（交付前必跑，退出码 1 = 不许交付）

为什么需要这个脚本（2026-09-20 第五轮，使用者提问后核实发现）：
  使用者问："该 skill 产出的版式、字体、颜色、排版等参数是否已固定？
            保证每次精读任务不会变化整体风格？"

  核实结论：**当时并不"固定"，只是"恰好一致"。**
  证据：
    · 版式全部写死在 `templates/精读转网页.py` 的 CSS 常量里，**没有任何独立配置文件**；
    · 5 个门禁脚本（图数审计/数字校验/人名审计/导航测试/回归测试）里，
      对 CSS / 字号 / 颜色的校验**命中 0 处** —— 没有任何机器在守它；
    · 6 份 HTML 当前 CSS 逐字节一致，但那是"已经生成过的一致"，
      不是"被强制的一致"。**下一次转换时，只要 CSS 常量被改动，
      没有任何东西会报警。**
    · 同理，`详情页视觉规格` 那张表只写在 SKILL.md 里靠自觉遵守 ——
      而 SKILL.md 里已经有过记录："文字规则拦不住我，机械校验才拦得住。"

  所以本脚本把视觉参数**钉成机器可校验的基线**：
    ① 校验 `templates/精读转网页.py` 里的 CSS 常量本身是否被改动（基线指纹）；
    ② 校验产出的 .html 是否与脚本 CSS **逐字节一致**（防止有人手改 HTML 而不过脚本）；
    ③ 把关键视觉参数（字号 / 颜色 / 圆角 / 字体栈）逐条断言，改动必须显式改基线。

  设计原则（沿用本技能红线 26 的取舍原则）：
    宁可报"规格漂移，请确认"，也不许静默漂移。
    若确实要改样式：改 `templates/精读转网页.py` → 跑 `--update-baseline` 更新基线 →
    在 SKILL.md 的"详情页视觉规格"表里同步写入新值。**三处必须同时改，缺一不可。**

用法：
    python 视觉规格门禁.py <产出目录或单个.html>        # 校验（退出码 1 = 不通过）
    python 视觉规格门禁.py --script-only                 # 只校验脚本 CSS 常量
    python 视觉规格门禁.py --selftest                    # 自测门禁本身能不能拦住漂移
    python 视觉规格门禁.py --update-baseline             # 显式更新基线（需人工确认后跑）
"""
import io
import os
import re
import sys
import glob
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
TEMPLATE = os.path.join(SKILL_DIR, 'templates', '精读转网页.py')
BASELINE = os.path.join(HERE, '视觉规格基线.txt')

# ── 关键视觉参数（改动必须显式改这里 + SKILL.md 表格 + 更新基线）────────────
# 每条 = (人类可读名, 在 CSS 里必须出现的精确片段)
SPEC = [
    ('页面底色 --bg',            '--bg:#0e1117'),
    ('面板底色 --panel',         '--panel:#141b22'),
    ('次级面板 --panel2',        '--panel2:#18212a'),
    ('边框 --border',            '--border:#26313c'),
    ('主文字 --txt',             '--txt:#d7e0ea'),
    ('详情页正文 --txt2',        '--txt2:#b9c4d1'),
    ('弱化文字 --dim',           '--dim:#8b97a6'),
    ('最弱文字 --faint',         '--faint:#5c6b78'),
    ('主强调 --a1',              '--a1:#34d3c4'),
    ('次强调 --a2',              '--a2:#4a9eff'),
    ('警示 --warn',              '--warn:#ffb454'),
    ('圆角 --radius',            '--radius:14px'),
    ('body 字号',                'font-size:16px'),
    ('正文行高',                 'line-height:1.78'),
    ('详情页字号',               'font-size:14.5px'),
    ('h1 字号',                  'h1{font-size:21.5px'),
    ('h2 字号',                  'h2{font-size:17.5px'),
    ('h3 字号',                  'h3{font-size:15px'),
    ('h4 字号（正文级）',         'h4{font-size:14px'),
    ('表格字号',                 'table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px'),
    ('代码字号',                 'font-size:12.5px'),
    ('加粗色',                   'strong{color:var(--txt)}'),
    ('正文颜色绑定',             'color:var(--txt2)'),
    ('字体栈',                   '"Segoe UI","PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif'),
    ('等宽字体栈',               'ui-monospace,Consolas,monospace'),
    ('栅格 侧栏宽',              'grid-template-columns:286px 1fr'),
    ('容器最大宽',               'max-width:1280px'),
    ('滚动留白',                 'scroll-padding-top:88px'),
]


def read_template_css():
    if not os.path.isfile(TEMPLATE):
        return None
    t = io.open(TEMPLATE, encoding='utf-8').read()
    m = re.search(r'CSS = """(.*?)"""', t, re.S)
    return m.group(1) if m else None


def norm(s):
    return re.sub(r'\s+', '', s)


def css_of_html(path):
    t = io.open(path, encoding='utf-8', errors='ignore').read()
    m = re.search(r'<style>(.*?)</style>', t, re.S)
    return m.group(1) if m else None


def load_baseline():
    if not os.path.isfile(BASELINE):
        return None
    d = {}
    for ln in io.open(BASELINE, encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        if '\t' in ln:
            k, v = ln.split('\t', 1)
            d[k] = v
    return d


def write_baseline(css):
    with io.open(BASELINE, 'w', encoding='utf-8') as f:
        f.write('# 视觉规格基线（自动生成，勿手改）\n')
        f.write('# 改样式的正确流程：改 templates/精读转网页.py → 跑 --update-baseline → 同步 SKILL.md 表格\n')
        f.write('# 说明：以 # 开头的是注释；数据行为 `<名称>\\t<期望片段>`；\n')
        f.write('#       `__meta_css_sha1` / `__meta_css_norm_len` 为元数据（**不加 # 前缀**，否则读取时会被当注释跳过）。\n')
        f.write('#\n')
        # ★ 元数据行不能带 '#' 前缀——load_baseline() 会按注释跳过，
        #   导致 sha1 永远读不到、指纹校验静默失效（本 bug 由 --selftest 抓出）。
        f.write('__meta_css_sha1\t%s\n' % hashlib.sha1(norm(css).encode('utf-8')).hexdigest())
        f.write('__meta_css_norm_len\t%d\n' % len(norm(css)))
        for name, frag in SPEC:
            f.write('%s\t%s\n' % (name, frag))


def run_selftest():
    """自测：门禁本身能不能拦住漂移（避免"看起来有守卫，其实不会报警"）。

    做法：在内存里对 CSS 施加两类真实漂移，断言 SPEC 能识别出「参数缺失」；
    再断言未漂移的原文能全部命中。**不落盘、不改文件。**
    """
    css = read_template_css()
    if css is None:
        print('[自测失败] 读不到 CSS')
        return 1
    results = []

    def chk(name, cond, detail=''):
        results.append((name, bool(cond), detail))

    # ① 未漂移：28 项必须全部命中
    miss0 = [n for n, f in SPEC if f not in css]
    chk('未漂移时 28 项全部命中', not miss0, 'miss=%s' % miss0)

    # ② 字号漂移：14.5 → 15
    d1 = css.replace('font-size:14.5px', 'font-size:15px')
    chk('字号漂移 14.5→15 被识别',
        any('详情页字号' == n for n, f in SPEC if f not in d1))

    # ③ 颜色漂移：--txt2 改亮
    d2 = css.replace('--txt2:#b9c4d1', '--txt2:#d7e0ea')
    chk('颜色漂移 --txt2 被识别',
        any('详情页正文 --txt2' == n for n, f in SPEC if f not in d2))

    # ④ 字体栈漂移
    d3 = css.replace('"Segoe UI","PingFang SC"', '"Segoe UI"')
    chk('字体栈漂移被识别',
        any('字体栈' == n for n, f in SPEC if f not in d3))

    # ⑤ 栅格漂移（侧栏宽度变了 → 整体排版变）
    d4 = css.replace('286px 1fr', '320px 1fr')
    chk('栅格漂移 286→320 被识别',
        any('栅格 侧栏宽' == n for n, f in SPEC if f not in d4))

    # ⑥ 圆角漂移
    d5 = css.replace('--radius:14px', '--radius:8px')
    chk('圆角漂移被识别',
        any('圆角 --radius' == n for n, f in SPEC if f not in d5))

    # ⑦ 基线指纹确实存在且非空
    b = load_baseline()
    chk('基线文件存在且含 sha1', bool(b and b.get('__meta_css_sha1')),
        'baseline=%s' % (BASELINE if b else 'None'))

    # ⑧ 基线 sha1 与当前 CSS 一致（防止有人改了模板却没更新基线）
    if b and b.get('__meta_css_sha1'):
        got = hashlib.sha1(norm(css).encode('utf-8')).hexdigest()
        chk('基线 sha1 与当前 CSS 一致', b['__meta_css_sha1'] == got,
            'want=%s got=%s' % (b['__meta_css_sha1'][:12], got[:12]))

    for name, ok_, detail in results:
        print('  %s %s%s' % ('✓' if ok_ else '✗', name,
                             ('  [' + detail + ']') if (detail and not ok_) else ''))
    bad = [n for n, o, _ in results if not o]
    print()
    if bad:
        print('自测不通过 %d 条：%s' % (len(bad), '；'.join(bad)))
        return 1
    print('自测通过：门禁能识别字号/颜色/字体栈/栅格/圆角五类漂移。')
    return 0


def main():
    args = sys.argv[1:]

    if '--selftest' in args:
        print('=' * 72)
        print('视觉规格门禁 · 自测（不落盘）')
        print('=' * 72)
        return run_selftest()

    css = read_template_css()
    if css is None:
        print('[错误] 读不到 templates/精读转网页.py 的 CSS 常量')
        return 1

    if '--update-baseline' in args:
        write_baseline(css)
        print('[完成] 基线已更新：%s' % BASELINE)
        print('       ★ 别忘了同步 SKILL.md「详情页视觉规格」表，否则规则与实现脱节。')
        return 0

    problems = []

    # ① 逐条断言关键视觉参数是否仍在 CSS 里
    miss = [(n, f) for n, f in SPEC if f not in css]
    if miss:
        for n, f in miss:
            problems.append('视觉参数缺失/被改：%s —— 期望片段 `%s` 未找到' % (n, f))

    # ② 与基线指纹比对（脚本自身是否被改动）
    base = load_baseline()
    if base is None:
        problems.append('基线文件不存在：%s（首次请跑 --update-baseline 生成）' % BASELINE)
    else:
        want = base.get('__meta_css_sha1')
        got = hashlib.sha1(norm(css).encode('utf-8')).hexdigest()
        if want and want != got:
            problems.append(
                '脚本 CSS 与基线不一致（sha1 %s… vs %s…）——'
                '样式被改动过。若是有意改版，请跑 --update-baseline 并同步 SKILL.md；'
                '若不是有意，说明发生了未经审查的样式漂移。'
                % (want[:12], got[:12]))

    print('=' * 72)
    print('视觉规格门禁')
    print('=' * 72)
    print('脚本 CSS 常量：%s' % TEMPLATE)
    print('规格条目：%d 条' % len(SPEC))
    print()

    # ③ 校验产出的 .html 是否与脚本 CSS 逐字节一致
    targets = [a for a in args if not a.startswith('--')]
    if '--script-only' not in args and targets:
        files = []
        for t in targets:
            if os.path.isdir(t):
                files += sorted(glob.glob(os.path.join(t, '**', '*.html'), recursive=True))
            elif os.path.isfile(t) and t.lower().endswith('.html'):
                files.append(t)
        if not files:
            print('（未找到 .html 待校验）')
        else:
            print('待校验 HTML：%d 份' % len(files))
            ref = norm(css)
            for p in files:
                hc = css_of_html(p)
                nm = os.path.basename(p)
                if hc is None:
                    problems.append('HTML 无 <style> 块：%s' % nm)
                    print('  ✗ %-52s 无内联样式' % nm[:52])
                    continue
                if norm(hc) == ref:
                    print('  ✓ %-52s 与脚本逐字节一致' % nm[:52])
                else:
                    problems.append(
                        'HTML 样式与脚本不一致：%s —— 该页面被手改过，'
                        '或用了旧版脚本生成。会产生风格漂移。' % nm)
                    print('  ✗ %-52s **样式漂移**' % nm[:52])
            print()

    print('=' * 72)
    if problems:
        print('不通过（%d 条）：' % len(problems))
        for i, p in enumerate(problems, 1):
            print('  %d. %s' % (i, p))
        print()
        print('若确认是有意改版：')
        print('  1) 改 templates/精读转网页.py')
        print('  2) python scripts/视觉规格门禁.py --update-baseline')
        print('  3) 同步 SKILL.md「详情页视觉规格」表')
        return 1
    print('通过：视觉参数与基线一致，产出页面与脚本样式逐字节相同。')
    print()
    print('能力边界（必须诚实标注）：')
    print('  · 本脚本校验的是**样式声明的一致性**，不判断样式好不好看；')
    print('  · 它拦得住"参数被改动"，拦不住"参数没改但正文内容导致排版差异"')
    print('    （如超长表格、超长英文单词撑破容器）——那属于内容问题，须人工看图。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
