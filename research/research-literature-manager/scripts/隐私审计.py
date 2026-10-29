# -*- coding: utf-8 -*-
"""隐私 / 上架合规审计（交付前门禁，配合红线 34）。

它守的是什么
------------
本技能只做文献精读，**不得记录任何个人信息**。这条要求光写在文档里没有用
（本技能已有定论："文字规则拦不住，机械校验才拦得住"），所以做成机器门禁。

它查四类**结构**，不靠"认识某个具体的人"：

  ① 个人姓名元数据：技能自有文件的 YAML frontmatter 里出现 author / maintainer /
     owner 之类的字段并带了值 —— 技能包不该背任何人的名字。
  ② 身份采集机制：出现"使用者身份 / 我的姓名 / 我的单位 / 我的邮箱"这类
     要求使用者填写自身信息的配置节。
  ③ 真人邮箱：`someone@real-domain` 形态。`@example.com` / `@example.edu` 等
     保留域名一律放行（那是占位）。
  ④ 本机绝对路径：`C:\\Users\\<某用户名>\\...` 把开发者的机器用户名写进技能文件。
     文档里的 `C:\\Users\\<用户名>\\` 占位写法放行。

**能力边界（必须如实声明，不许读成"这个人一定没被泄露"）**：
它**不识别**"某串汉字是不是某个真实人名"——那是人名审计（红线 29）的职责，
且那边只需要判断"原文有没有汉字"，同样不需要认识任何人。
所以本门禁的结论只能读成"**未发现上述四类结构性痕迹**"，
**不能**读成"已确认全文无任何真实姓名"。

退出码：0 = 未发现痕迹；1 = 发现痕迹，禁止交付。
用法：
  python 隐私审计.py --skill-dir <技能根目录>
  python 隐私审计.py --selftest
"""
import io
import os
import re
import sys

# 保留/示例域名：命中即视为占位，放行
PLACEHOLDER_DOMAIN = re.compile(
    r'@(?:example\.(?:com|org|net|edu)|test\.(?:com|org)|invalid|localhost|'
    r'yourmail\.com|mail\.example\.com|yyy\.edu|foo\.example)\b', re.I)

# 邮箱形态（只用来找"真人邮箱"，占位域名在上面先放行）
EMAIL = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')

# ① frontmatter 里的个人元数据字段
#   ★ 取值必须吃到**行尾**（`[^\n]+`），不能用 `\S+` —— 后者只吃一个词，
#     `author: Jane Doe` 会被截成 `Jane`，导致后续"英文真名"判定漏报
#     （2026-09-21 由 --selftest 双向用例抓出，见自测第 6 条）。
FM_NAME_FIELDS = re.compile(
    r'^[ \t]*(author|maintainer|owner|created_by|by|contact|email)[ \t]*[:=][ \t]*([^\n]+)',
    re.I | re.M)

# ①-b 品牌署名白名单：**这些字段值属于产品/品牌标识，不是自然人姓名，不应告警。**
#
#   ★ 为什么需要（2026-09-21 实测纠正）：
#     原实现只看"字段名 + 有值"，把 SKILL.md 的 `author: 琅嬛` 判为个人元数据 → EXIT=1。
#     但「琅嬛」是本**专家花名**（《专家描述》明写"花名是专家对外的拟人化别名，用于头像、
#     吉祥物、品牌记忆点，**不替代正式专家名**"），是**对外品牌标识**，不是真人姓名。
#
#   ★ 本门禁的能力边界（脚本自己已声明）：
#     "不识别某串汉字是否为真实人名" —— 脚本本来就判不了。既然判不了，
#     就**不许**把"字段有值"直接等同于"这就是个人信息"。
#
#   ★ 判定口径：
#     - 值属于本白名单（已登记的品牌花名 / 产品名 / 团队名）→ **不告警**；
#     - 值形如"姓 名"两段中文（如 `张叁`、`李四`）→ **告警**（真人姓名特征）；
#     - 值形如英文 `First Last` 两词 → **告警**；
#     - 其余（组织名 / 占位符 / 明显品牌词）→ 不告警。
#     即：**从"字段即告警"收紧为"字段值像真人姓名才告警"**，避免品牌名被误杀。
BRAND_SIGNATURE = re.compile(
    r'^(?:琅嬛|知微|拾遗|文枢|科研文献精读与管理助手|Research Literature Close-Reading'
    r'|Firstname Lastname|某某|团队|组织名)$')
# 真实人名特征：2–4 个汉字、或两个英文单词（首字母大写）
PERSON_NAME_CN = re.compile(r'^[\u4e00-\u9fff]{2,4}$')
PERSON_NAME_EN = re.compile(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$')

# ② 身份采集机制（要求使用者填写自己的信息）
IDENTITY_COLLECT = re.compile(
    r'使用者身份|用户身份|我的姓名|我的名字|我的单位|我的邮箱|我的账号|'
    r'填写你的姓名|填入你的姓名|你的姓名|你的单位|你的邮箱')

# ④ 本机绝对路径里带**具体用户名**（非占位）
WIN_USER_PATH = re.compile(
    r'[A-Za-z]:[\\/]+Users[\\/]+([^\\/\s<>*"\'`|]+)')
HOME_USER_PATH = re.compile(r'/(?:Users|home)/([^/\s<>*"\'`|]+)')
PATH_PLACEHOLDER = re.compile(r'^(?:<[^>]+>|\$\{?[A-Za-z_]+\}?|%[A-Za-z_]+%|用户名|username|xxx|\*+)$', re.I)

# 只审这些后缀的文本文件；二进制/缓存跳过
# 只审这些后缀的文本文件；二进制/缓存跳过
BS = chr(92)   # 反斜杠。写成变量是为了让本文件自身不出现"完整 Windows 路径字面量"，
               # 否则门禁扫自己时会命中自测用例里的假路径（自排除已做，这里是双保险）。

TEXT_EXT = {'.md', '.py', '.txt', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.html', '.js', '.ts'}
SKIP_DIRS = {'__pycache__', '.git', '.pytest_cache', 'node_modules'}

# ★ 必须排除门禁自己。这一点容易被误读成"给自己开后门"，故写清理由与代价：
#
#   为什么必须排除：本文件里**必然**含有这些模式的字面量——正则源码写着
#   `author|maintainer`、`我的姓名|我的单位`，自测用例里写着假邮箱与假路径。
#   若不排除，这个门禁扫任何目录都会**永远报自己有问题**（实测：首版跑出 27 处
#   全部是自报）。一条永远为真的告警等于没有告警，而且会训练人忽略该方向（红线 32）。
#
#   代价与补偿：排除后，理论上"把违规内容藏进本文件"就不会被发现。补偿手段是
#   ① 本文件被 `--selftest` 覆盖（11 条双向断言，每次都跑）；
#   ② 本文件不含任何真实姓名/邮箱/路径——所有用例值都是构造出来的占位值；
#   ③ 人工评审本文件时，它只有 200 余行，可整读。
#
#   排除的是"模式的定义处"，不是"模式要抓的东西"：违规文本出现在别的文件里
#   仍会被抓到（见下方的真实目录扫描）。
SELF_EXCLUDE = {'隐私审计.py'}


def _iter_text_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn in SELF_EXCLUDE:
                continue
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, fn)


def _frontmatter(text):
    """取 YAML frontmatter 原文（无则返回空串）。"""
    if not text.startswith('---'):
        return ''
    end = text.find('\n---', 3)
    return text[3:end] if end > 0 else ''


def scan_text(text, rel):
    """扫描一段文本，返回 (类别, 证据) 列表。唯一实现（红线 27）。"""
    hits = []

    # ① frontmatter 个人元数据
    #
    # ★ 判据已收紧（2026-09-21）：不再"字段有值即告警"，而是**只在该字段值看起来像
    #   自然人姓名时**才告警。理由见 BRAND_SIGNATURE 上方注释——专家花名（如「琅嬛」）
    #   是对外品牌标识，不是个人信息，误判会制造伪缺陷并浪费用户决策。
    fm = _frontmatter(text)
    if fm:
        for m in FM_NAME_FIELDS.finditer(fm):
            raw = m.group(0).strip()
            # 值直接取第 2 组（正则已吃到行尾），无需再手工切分
            val = (m.group(2) or '').strip().strip('"\'')
            if not val:
                continue
            if BRAND_SIGNATURE.match(val):
                continue                      # 品牌署名：放行
            if PERSON_NAME_CN.match(val) or PERSON_NAME_EN.match(val):
                hits.append(('frontmatter 个人元数据', '%s: %s' % (rel, raw)))
            # 其余形态（组织名 / URL 形态 / 不具姓名特征的串）不告警，避免误杀品牌标识

    # ② 身份采集机制
    for m in IDENTITY_COLLECT.finditer(text):
        ls = text.rfind('\n', 0, m.start()) + 1
        le = text.find('\n', m.end())
        line = text[ls:le if le > 0 else len(text)].strip()
        hits.append(('身份采集机制', '%s: %s' % (rel, line[:100])))

    # ③ 真人邮箱（跳过占位域名）
    for m in EMAIL.finditer(text):
        addr = m.group(0)
        if PLACEHOLDER_DOMAIN.search(addr):
            continue
        hits.append(('非占位邮箱', '%s: %s' % (rel, addr)))

    # ④ 本机绝对路径里的具体用户名
    for rx in (WIN_USER_PATH, HOME_USER_PATH):
        for m in rx.finditer(text):
            user = m.group(1)
            if PATH_PLACEHOLDER.match(user):
                continue
            # 用户名长度 1 的极可能是盘符误伤，跳过
            if len(user) < 2:
                continue
            hits.append(('路径含具体用户名', '%s: %s' % (rel, m.group(0))))
    return hits


def scan_dir(root):
    """扫描技能目录，返回全部命中。"""
    all_hits = []
    for p in _iter_text_files(root):
        rel = os.path.relpath(p, root).replace('\\', '/')
        try:
            t = io.open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        all_hits.extend(scan_text(t, rel))
    return all_hits


def selftest():
    """双向自测（红线 24）：既验证"能抓到"，也验证"不误伤占位写法"。

    用例里的"真名 / 邮箱 / 路径"全部是**构造出来的假值**，
    只为触发对应模式，不对应任何真实人物或真实机器。
    """
    cases = [
        # (描述, 文本, 期望是否报警)
        ('frontmatter author 带真名',
         '---\nname: x\nauthor: 张叁\n---\n正文', True),
        ('frontmatter author 空值（不报警）',
         '---\nname: x\nauthor:\n---\n正文', False),
        # ★ 2026-09-21 新增：品牌署名（专家花名）不是个人信息，不许误杀
        ('frontmatter author 为专家花名（不报警）',
         '---\nname: x\nauthor: 琅嬛\n---\n正文', False),
        ('frontmatter author 为品牌花名-知微（不报警）',
         '---\nname: x\nauthor: 知微\n---\n正文', False),
        ('frontmatter author 为英文占位（不报警）',
         '---\nname: x\nauthor: Firstname Lastname\n---\n正文', False),
        ('frontmatter author 为英文真名（报警）',
         '---\nname: x\nauthor: Jane Doe\n---\n正文', True),
        ('身份采集节', '## 使用前填一次\n我的姓名：______\n', True),
        ('询问你的单位', '请填写你的单位关键词', True),
        ('真人邮箱', '联系：nonexistent.person@sample-domain-zz.org', True),
        ('占位邮箱（不报警）', '联系：xxx@example.edu', False),
        ('本机路径带用户名', 'C:' + BS + 'Users' + BS + 'placeholder-user' + BS + 'a.md', True),
        ('路径占位符（不报警）',
         'C:' + BS + 'Users' + BS + '<用户名>' + BS + 'python', False),
        ('%VAR% 环境变量（不报警）',
         '打开 %USERPROFILE%' + BS + 'Documents' + BS + 'a.md', False),
        ('Linux 家目录带用户名', '/home/placeholder-user/work/a.md', True),
        ('普通技术文本（不报警）',
         '板块 6 七栏：原文标题 / 图注中译 / 图表类型 / 数据模式', False),
    ]
    bad = 0
    for desc, text, expect in cases:
        hits = scan_text(text, 'x.md')
        got = bool(hits)
        mark = '✓' if got == expect else '✗'
        if got != expect:
            bad += 1
        print('  %s %-30s 期望=%s 实际=%s' % (mark, desc[:30], expect, got))
        if got != expect:
            for cat, ev in hits:
                print('        [%s] %s' % (cat, ev))
    print()
    return bad


def main():
    args = sys.argv[1:]
    if not args:
        print('用法: python 隐私审计.py --skill-dir <技能根目录> | --selftest')
        return 2
    if args[0] == '--selftest':
        print('=== 隐私审计·双向自测（红线 24）===')
        bad = selftest()
        if bad:
            print('自测不通过：%d 条与期望不符 —— 门禁自身有问题，禁止用于判定。' % bad)
            return 1
        print('自测通过：能抓真名/邮箱/身份采集，不误伤占位写法。')
        return 0

    if args[0] == '--skill-dir':
        root = args[1]
    else:
        root = args[0]
    if not os.path.isdir(root):
        print('[目录不存在]', root)
        return 1

    hits = scan_dir(root)
    if hits:
        print('✗ 发现 %d 处个人信息 / 身份采集痕迹：' % len(hits))
        for cat, ev in hits:
            print('    [%s] %s' % (cat, ev))
        print()
        print('结论：不通过。技能自有文件不得含个人信息 —— 逐个删掉（示例改用占位写法）。')
        print('边界声明：本门禁只查上述四类结构性痕迹，不识别"某串汉字是否为真实人名"。')
        return 1
    print('✓ 未发现 frontmatter 个人元数据 / 身份采集机制 / 非占位邮箱 / 本机用户名路径。')
    print('边界声明：仅表示"未发现上述四类结构性痕迹"，不等于"已确认全文无任何真实姓名"。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
