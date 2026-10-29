# -*- coding: utf-8 -*-
"""按 WorkBuddy 技能（skill）上架规范打包并自检。

官方结构（技能 skill）：
    {skill-name}/
    ├── SKILL.md            # 必须，YAML frontmatter + 正文
    ├── avatars/expert.png  # 必须，512x512、<=500KB（与专家同规格）
    ├── references/         # 可选
    ├── scripts/            # 可选
    └── templates/          # 可选

关键约束（据上架助手专家文档 + 平台实测）：
  · zip 内**第一层就是技能内容**（SKILL.md 在根，不再套一层目录名）
  · 目录层级 **≤2 级**
  · **解压后总大小 <3MB（3145728 字节）** ← ★ 平台卡的是"解压后"，不是 zip 大小
    （2026-09-21 实测被驳回：zip 仅 0.89MB，但解压后 4.78MB → "解析失败：压缩包解压后超出大小限制"）
  · frontmatter 必填：display_name / description / description_zh / description_en / version / author
    （display_name 缺失是**最常见驳回原因**）
  · 中文文件名须 UTF-8 无 BOM（否则解压乱码）
  · 严禁硬编码 Token/密钥；严禁硬编码个人绝对路径

用法：
    python scripts/打包自检.py                      # 打包上一级目录为 <技能名>.zip 并自检
    python scripts/打包自检.py --out D:/x.zip       # 指定输出
    python scripts/打包自检.py --check-only --out D:/x.zip   # 只自检已有 zip
退出码：0 = 全部通过可上传；1 = 存在不通过项，禁止上传。
"""
import os
import re
import sys
import json
import zipfile
import hashlib
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(_HERE)                      # 技能根（SKILL.md 所在层）
OUT = os.environ.get("SKILL_ZIP_OUT") or os.path.join(
    os.path.dirname(SRC), os.path.basename(SRC) + ".zip")

SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini",
              # 本地诊断/审计产出的报告，不属于技能内容，不进包
              "全量同源比对报告.txt", "压缩校验报告.txt"}
SKIP_SUFFIXES = ("_报告.txt", "报告.txt")          # 兜底：本地报告一律排除
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache",
             "node_modules", ".codebuddy-plugin"}

# ★ 技能包上限（2026-09-21 被平台驳回后纠正）
#   平台报错原文："压缩包解压后超出大小限制（最大 3MB，即 3145728 字节），
#                 当前解压后总大小 4633.49 KB（4744690 字节）"
#   —— 卡的是**解压后**总大小，不是 zip 文件大小！
#   我此前错判为"zip 体积 <3MB"，导致 zip 只有 0.89MB 却仍被判超限。
MAX_UNPACKED_BYTES = 3 * 1024 * 1024      # 解压后总大小上限（平台硬限）
MAX_ZIP_BYTES = 3 * 1024 * 1024           # zip 自身（顺带看一眼，非平台判据）
# 头像上限
MAX_AVATAR_BYTES = 500 * 1024
AVATAR_SIZE = (512, 512)
# frontmatter 必填字段
REQUIRED_FM = ["display_name", "description", "description_zh",
               "description_en", "version", "author"]

# 凭证特征
RE_CRED = re.compile(
    r"sk-[A-Za-z0-9]{16,}"
    r"|(?i:(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]{12,}['\"])"
)
# 个人绝对路径特征（盘符 + 用户目录 / 业务目录）
RE_PERSONAL_PATH = re.compile(
    r"[A-Za-z]:[\\/]\s*(?:Users|Documents|Desktop)"
    r"|[\\/]Users[\\/][^\\/\s\"'<>]+"
)


def collect():
    items = []
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in sorted(files):
            if n in SKIP_NAMES or n.endswith((".pyc", ".pyo")):
                continue
            if n.endswith(SKIP_SUFFIXES):
                continue
            fp = os.path.join(root, n)
            rel = os.path.relpath(fp, SRC).replace("\\", "/")
            items.append((rel, fp))
    return sorted(items)


def _selfcheck(zip_path):
    """对已有 zip 做上架规范自检。返回 0/1。"""
    zsize = os.path.getsize(zip_path)
    zha = hashlib.sha256(open(zip_path, "rb").read()).hexdigest()
    errs, warns, oks = [], [], []

    print("\n" + "=" * 72)
    print("上架规范自检")
    print("=" * 72)

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()

        # ① SKILL.md 位于 zip 根层
        if "SKILL.md" in names:
            oks.append("① SKILL.md 位于 zip 根层（未多套一层目录名）")
        else:
            errs.append("① SKILL.md 不在 zip 根层（平台解析不到技能主体）")

        # ② 首层结构
        tops = sorted(set(n.split("/")[0] for n in names))
        expect_tops = {"SKILL.md", "avatars", "scripts", "templates",
                       "references", "assets"}
        extra = [t for t in tops if t not in expect_tops]
        if extra:
            warns.append("② zip 首层含非标准项：%s（确认是否有必要）" % extra)
        else:
            oks.append("② zip 首层仅含标准项：%s" % tops)

        # ③ 目录层级 ≤2
        depth = max(len(n.strip("/").split("/")) for n in names)
        if depth <= 2:
            oks.append("③ 目录层级 %d 级（≤2 级，符合技能结构）" % depth)
        else:
            errs.append("③ 目录层级 %d 级，超出技能上限 2 级" % depth)

        # ④ 头像规格
        av = "avatars/expert.png"
        if av in names:
            import struct
            data = z.read(av)
            sig_ok = data[:8] == b"\x89PNG\r\n\x1a\n"
            if not sig_ok:
                errs.append("④ 头像非 PNG（%s 头 8 字节异常）" % av)
            else:
                w, h = struct.unpack(">II", data[16:24])
                if (w, h) != AVATAR_SIZE:
                    errs.append("④ 头像 %dx%d，非规范 512x512" % (w, h))
                elif len(data) > MAX_AVATAR_BYTES:
                    errs.append("④ 头像 %d 字节，超 500KB 上限" % len(data))
                else:
                    oks.append("④ 头像 avatars/expert.png OK"
                               "（PNG %dx%d，%d 字节 ≤500KB）" % (w, h, len(data)))
        else:
            errs.append("④ 缺 avatars/expert.png（技能同样要求头像）")

        # ⑤ frontmatter 必填字段
        if "SKILL.md" in names:
            fm_text = z.read("SKILL.md").decode("utf-8-sig")
            fm = ""
            if fm_text.lstrip().startswith("---"):
                parts = fm_text.split("---")
                fm = parts[1] if len(parts) >= 2 else ""
            miss = [k for k in REQUIRED_FM
                    if not re.search(r"^%s\s*:" % k, fm, re.M)]
            if miss:
                errs.append("⑤ frontmatter 缺必填字段：%s"
                            "（display_name 缺失是最常见驳回原因）" % "、".join(miss))
            else:
                oks.append("⑤ frontmatter 必填字段齐全（%s）" % "、".join(REQUIRED_FM))
            if re.search(r"^tools\s*:", fm, re.M):
                errs.append("⑤ frontmatter 出现 tools 字段（技能不应声明 tools）")

        # ⑥ 体积（★ 判据是**解压后**总大小，不是 zip 大小）
        unpacked = sum(i.file_size for i in z.infolist())
        zsize_now = os.path.getsize(zip_path)
        if unpacked < MAX_UNPACKED_BYTES:
            oks.append("⑥ 解压后总大小 %d 字节 = %.2f MB"
                       "（平台上限 3MB，余量 %.2f MB）"
                       % (unpacked, unpacked / 1048576,
                          (MAX_UNPACKED_BYTES - unpacked) / 1048576))
        else:
            # 顺便指出谁是"体积大户"，方便定位
            big = sorted(z.infolist(), key=lambda i: -i.file_size)[:3]
            who = "、".join("%s(%.2fMB)" % (i.filename, i.file_size / 1048576) for i in big)
            errs.append("⑥ 解压后总大小 %d 字节 = %.2f MB，**超平台 3MB 上限**"
                        "（超出 %.2f MB）。体积大户：%s"
                        % (unpacked, unpacked / 1048576,
                           (unpacked - MAX_UNPACKED_BYTES) / 1048576, who))
        if zsize_now >= MAX_ZIP_BYTES:
            errs.append("⑥ zip 自身 %.2f MB，超 3MB" % (zsize_now / 1048576))

        # ⑦ 中文文件名 UTF-8 无 BOM
        bom = [n for n in names if "\ufeff" in n]
        cn = [n for n in names if any("\u4e00" <= c <= "\u9fff" for c in n)]
        if bom:
            errs.append("⑦ 文件名含 BOM 字符：%s" % bom[:3])
        else:
            oks.append("⑦ 中文文件名 UTF-8 正常（含中文名 %d 个），无 BOM" % len(cn))

        # ⑧ 无硬编码凭证
        chit = []
        for n in names:
            if n.endswith((".py", ".md", ".json", ".txt", ".yaml", ".yml")):
                try:
                    t = z.read(n).decode("utf-8", "ignore")
                except Exception:
                    continue
                if RE_CRED.search(t):
                    chit.append(n)
        if chit:
            errs.append("⑧ 疑似硬编码凭证：%s" % chit)
        else:
            oks.append("⑧ 无硬编码 Token/密钥")

        # ⑨ 无个人绝对路径
        phit = []
        for n in names:
            if n.endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml")):
                try:
                    t = z.read(n).decode("utf-8", "ignore")
                except Exception:
                    continue
                for i, l in enumerate(t.split("\n"), 1):
                    if RE_PERSONAL_PATH.search(l):
                        phit.append("%s:%d" % (n, i))
        if phit:
            errs.append("⑨ 含个人绝对路径：%s" % phit[:8])
        else:
            oks.append("⑨ 无个人绝对路径泄漏")

    print("\n【通过项】")
    for o in oks:
        print("  ✓ " + o)
    if warns:
        print("\n【提示】")
        for w in warns:
            print("  ! " + w)
    if errs:
        print("\n【★ 不通过项】")
        for e in errs:
            print("  ✗ " + e)

    print("\n" + "=" * 72)
    print("产物指纹")
    print("=" * 72)
    print("  路径   ：%s" % zip_path)
    print("  体积   ：%d 字节 = %.2f MB" % (zsize, zsize / 1048576))
    print("  条目数 ：%d" % len(names))
    print("  sha256 ：%s" % zha)
    print()
    print("自检结论：%s"
          % ("全部通过（可上传）" if not errs
             else "存在 %d 项不通过，禁止上传" % len(errs)))
    return 0 if not errs else 1


def main():
    global SRC, OUT
    print("=" * 72)
    print("打包并自检：%s" % os.path.basename(SRC))
    print("=" * 72)

    if not os.path.isfile(os.path.join(SRC, "SKILL.md")):
        print("★ 技能根缺少 SKILL.md：%s" % SRC)
        return 1

    items = collect()
    print("\n【打包内容 %d 个文件】" % len(items))
    total = 0
    for rel, fp in items:
        s = os.path.getsize(fp)
        total += s
        pct = s / total * 100 if total else 0
        print("  %-58s %10d" % (rel, s))
    print("  %-58s %10d" % ("[解压后合计]", total))
    # 体积预警：接近上限时先提示，免得白跑一趟上传
    if total >= MAX_UNPACKED_BYTES * 0.9:
        print("\n  ⚠ 解压后合计已达平台上限的 %.0f%%（上限 %d 字节），"
              "余量仅 %.2f MB，建议先瘦身"
              % (total / MAX_UNPACKED_BYTES * 100, MAX_UNPACKED_BYTES,
                 (MAX_UNPACKED_BYTES - total) / 1048576))
        big = sorted(items, key=lambda x: -os.path.getsize(x[1]))[:3]
        for rel, fp in big:
            print("      大户：%-46s %.2f MB" % (rel, os.path.getsize(fp) / 1048576))

    tmp_zip = OUT + ".tmp"
    if os.path.exists(tmp_zip):
        os.remove(tmp_zip)
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, fp in items:
            z.write(fp, rel)

    for attempt in range(10):
        try:
            os.replace(tmp_zip, OUT)
            break
        except PermissionError as e:
            import time
            print("  [重试 %d] 目标被占用：%s" % (attempt + 1, e))
            time.sleep(2.5)
    else:
        print("★ 无法替换目标 zip（持续被占用）")
        return 1

    # 校验 zip 与磁盘一致
    with zipfile.ZipFile(OUT) as z:
        bad = z.testzip()
        if bad:
            print("★ zip 完整性校验失败：%s" % bad)
            return 1
        print("\n  zip 完整性：OK（CRC 全部通过，%d 条目）" % len(z.namelist()))

    return _selfcheck(OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="按 WorkBuddy 技能上架规范打包并自检")
    ap.add_argument("--src", default=None, help="技能根目录（含 SKILL.md），默认本脚本上一级")
    ap.add_argument("--out", default=None, help="输出 zip 路径")
    ap.add_argument("--check-only", action="store_true", help="只自检已有 zip，不打包")
    a = ap.parse_args()
    if a.src:
        SRC = os.path.abspath(a.src)
    if a.out:
        OUT = os.path.abspath(a.out)
    if a.check_only:
        sys.exit(_selfcheck(OUT))
    sys.exit(main())
