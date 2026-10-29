#!/usr/bin/env python3
"""证据链硬审计：claims.csv / sources.json / Markdown 正文。

只读脚本，不修改任何文件。退出码：0 通过；1 审计错误；2 输入或参数错误。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Pattern, Sequence

CLAIM_ID_RE = re.compile(r"^C\d{3,}$")
SOURCE_ID_RE = re.compile(r"^S\d{3,}$")
CLAIM_REF_RE = re.compile(r"(?<![A-Za-z0-9_])C\d{3,}(?![A-Za-z0-9_])")
SOURCE_REF_RE = re.compile(r"(?<![A-Za-z0-9_])S\d{3,}(?![A-Za-z0-9_])")
SOURCE_ID_SPLIT_RE = re.compile(r"[;；,，|\s]+")
FENCE_RE = re.compile(r"^(```+|~~~+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")

CLAIM_TYPES = {"事实", "观点", "数据"}
CLAIM_STATUSES = {"已核验", "未查到", "待核实", "作者观点"}
SOURCE_STATUSES = {"已核验", "未查到", "待核实"}
VERIFIED = "已核验"
AUTHOR_VIEW = "作者观点"
UNVERIFIED_STATUSES = {"未查到", "待核实"}
DEFAULT_ALLOW_UNVERIFIED = r"待核实|待核验|未核实|未核验|待办|附录|参考文献|致谢"


class InputError(Exception):
    """输入文件缺失、格式错误或参数非法。"""


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None

    def as_dict(self) -> dict:
        data = {"severity": self.severity, "code": self.code, "message": self.message}
        if self.file is not None:
            data["file"] = self.file
        if self.line is not None:
            data["line"] = self.line
        return data


@dataclass
class Claim:
    claim_id: str
    text: str
    type: str
    source_ids: List[str]
    status: str
    file: str
    line: int


@dataclass
class Source:
    source_id: str
    title: str
    identifier: str
    verified: str


class Audit:
    def __init__(self, strict: bool = False) -> None:
        self.strict = strict
        self.errors: List[Issue] = []
        self.warnings: List[Issue] = []
        self.stats = {
            "manuscripts": 0,
            "claims": 0,
            "sources": 0,
            "claim_refs": 0,
            "source_refs": 0,
        }

    def error(
        self,
        code: str,
        message: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
    ) -> None:
        self.errors.append(Issue("error", code, message, file, line))

    def warning(
        self,
        code: str,
        message: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
    ) -> None:
        self.warnings.append(Issue("warning", code, message, file, line))

    @property
    def ok(self) -> bool:
        return not self.errors and not (self.strict and self.warnings)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def load_claims(path: Path, audit: Audit) -> Dict[str, Claim]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
    except OSError as exc:
        raise InputError(f"无法读取 {path}：{exc}")
    except UnicodeDecodeError as exc:
        raise InputError(f"{path} 不是 UTF-8 文本：{exc}")

    if not rows:
        raise InputError(f"{path} 是空文件")

    header = [cell.strip() for cell in rows[0]]
    required = ["claim_id", "claim_text", "type", "source_ids", "status"]
    missing = [name for name in required if name not in header]
    if missing:
        raise InputError(f"{path} 缺少必需列：{', '.join(missing)}")

    claims: Dict[str, Claim] = {}
    for line_no, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(header):
            audit.error(
                "ROW_SHAPE",
                f"第 {line_no} 行有 {len(row)} 列，表头是 {len(header)} 列",
                file=display_path(path),
                line=line_no,
            )
            row = (row + [""] * len(header))[: len(header)]

        record = {
            name: (row[index].strip() if index < len(row) else "")
            for index, name in enumerate(header)
        }
        claim_id = record["claim_id"]
        claim_text = record["claim_text"]
        claim_type = record["type"]
        status = record["status"]

        if not claim_id:
            audit.error(
                "MISSING_CLAIM_ID",
                f"第 {line_no} 行缺少 claim_id",
                file=display_path(path),
                line=line_no,
            )
            continue
        if not CLAIM_ID_RE.match(claim_id):
            audit.error(
                "INVALID_CLAIM_ID",
                f"claim_id {claim_id!r} 不符合 C+至少3位数字（如 C001）",
                file=display_path(path),
                line=line_no,
            )
        if claim_id in claims:
            audit.error(
                "DUPLICATE_CLAIM_ID",
                f"claim_id {claim_id} 重复",
                file=display_path(path),
                line=line_no,
            )
            continue
        if not claim_text:
            audit.error(
                "MISSING_CLAIM_TEXT",
                f"{claim_id} 的 claim_text 为空",
                file=display_path(path),
                line=line_no,
            )
        if claim_type not in CLAIM_TYPES:
            audit.error(
                "INVALID_CLAIM_TYPE",
                f"{claim_id} 的 type {claim_type!r} 不是 事实/观点/数据",
                file=display_path(path),
                line=line_no,
            )
        if status not in CLAIM_STATUSES:
            audit.error(
                "INVALID_CLAIM_STATUS",
                f"{claim_id} 的 status {status!r} 不是 已核验/未查到/待核实/作者观点",
                file=display_path(path),
                line=line_no,
            )

        source_ids: List[str] = []
        raw_sources = record["source_ids"]
        if raw_sources:
            for source_id in SOURCE_ID_SPLIT_RE.split(raw_sources):
                if not source_id or source_id in source_ids:
                    continue
                source_ids.append(source_id)
                if not SOURCE_ID_RE.match(source_id):
                    audit.error(
                        "INVALID_SOURCE_ID",
                        f"{claim_id} 的来源编号 {source_id!r} 不符合 S+至少3位数字（如 S001）",
                        file=display_path(path),
                        line=line_no,
                    )

        if claim_type != "观点" and status == AUTHOR_VIEW:
            audit.error(
                "STATUS_TYPE_MISMATCH",
                f"{claim_id} 的 type 是 {claim_type}，status 却是「作者观点」",
                file=display_path(path),
                line=line_no,
            )
        if claim_type in ("事实", "数据") and status == VERIFIED and not source_ids:
            audit.error(
                "VERIFIED_FACT_NO_SOURCE",
                f"{claim_id} 标为已核验，但没有登记任何来源",
                file=display_path(path),
                line=line_no,
            )

        claims[claim_id] = Claim(
            claim_id=claim_id,
            text=claim_text,
            type=claim_type,
            source_ids=source_ids,
            status=status,
            file=display_path(path),
            line=line_no,
        )

    audit.stats["claims"] = len(claims)
    return claims


def load_sources(path: Path, audit: Audit) -> Dict[str, Source]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise InputError(f"无法读取 {path}：{exc}")
    except UnicodeDecodeError as exc:
        raise InputError(f"{path} 不是 UTF-8 文本：{exc}")
    except json.JSONDecodeError as exc:
        raise InputError(
            f"{path} 不是合法 JSON：第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}"
        )

    if not isinstance(data, list):
        raise InputError(f"{path} 顶层必须是数组，每个元素是一条来源")

    sources: Dict[str, Source] = {}
    for index, item in enumerate(data, start=1):
        location = f"第 {index} 个来源"
        if not isinstance(item, dict):
            audit.error("INVALID_SOURCE", f"{location} 不是对象", file=display_path(path))
            continue

        source_id = str(item.get("id") or "").strip()
        title = str(item.get("title") or "").strip()
        identifier = str(item.get("identifier") or "").strip()
        verified = str(item.get("verified") or "").strip()

        if not source_id:
            audit.error("MISSING_SOURCE_ID", f"{location} 缺少 id", file=display_path(path))
            continue
        if not SOURCE_ID_RE.match(source_id):
            audit.error(
                "INVALID_SOURCE_ID",
                f"{location} 的 id {source_id!r} 不符合 S+至少3位数字（如 S001）",
                file=display_path(path),
            )
        if source_id in sources:
            audit.error(
                "DUPLICATE_SOURCE_ID",
                f"来源编号 {source_id} 重复",
                file=display_path(path),
            )
            continue
        if not title:
            audit.error(
                "MISSING_SOURCE_TITLE",
                f"来源 {source_id} 缺少 title",
                file=display_path(path),
            )
        if verified not in SOURCE_STATUSES:
            audit.error(
                "INVALID_SOURCE_STATUS",
                f"来源 {source_id} 的 verified {verified!r} 不是 已核验/未查到/待核实",
                file=display_path(path),
            )
        if verified == VERIFIED and not identifier:
            audit.warning(
                "SOURCE_WITHOUT_IDENTIFIER",
                f"来源 {source_id} 标为已核验，但没有 identifier（DOI / 数据库链接）",
                file=display_path(path),
            )

        sources[source_id] = Source(
            source_id=source_id,
            title=title,
            identifier=identifier,
            verified=verified,
        )

    audit.stats["sources"] = len(sources)
    return sources


def check_claim_sources(
    claims: Dict[str, Claim], sources: Dict[str, Source], audit: Audit
) -> None:
    for claim in claims.values():
        for source_id in claim.source_ids:
            source = sources.get(source_id)
            if source is None:
                audit.error(
                    "CLAIM_SOURCE_MISSING",
                    f"{claim.claim_id} 引用了 sources.json 中不存在的来源 {source_id}",
                    file=claim.file,
                    line=claim.line,
                )
            elif claim.status == VERIFIED and source.verified in UNVERIFIED_STATUSES:
                audit.error(
                    "VERIFIED_CLAIM_UNVERIFIED_SOURCE",
                    f"{claim.claim_id} 标为已核验，但来源 {source_id} 状态是「{source.verified}」",
                    file=claim.file,
                    line=claim.line,
                )


def compile_allow_patterns(values: Sequence[str]) -> List[Pattern]:
    patterns = [re.compile(DEFAULT_ALLOW_UNVERIFIED)]
    for value in values:
        try:
            patterns.append(re.compile(value))
        except re.error as exc:
            raise InputError(f"--allow-unverified-in 正则无效 {value!r}：{exc}")
    return patterns


def section_allowed(section: str, patterns: Sequence[Pattern]) -> bool:
    return bool(section) and any(pattern.search(section) for pattern in patterns)


def iter_manuscripts(paths: Iterable[Path]) -> List[Path]:
    files: List[Path] = []
    seen = set()
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise InputError(f"正文路径不存在：{path}")
        if path.is_dir():
            candidates = sorted(path.rglob("*.md"))
            candidates = [
                candidate
                for candidate in candidates
                if not any(
                    part.startswith(".") or part == "node_modules"
                    for part in candidate.relative_to(path).parts
                )
            ]
        else:
            candidates = [path]
        for candidate in candidates:
            key = candidate.resolve()
            if key in seen:
                continue
            seen.add(key)
            files.append(candidate)
    return files


def scan_manuscript(
    path: Path,
    claims: Dict[str, Claim],
    sources: Dict[str, Source],
    allow_patterns: Sequence[Pattern],
    audit: Audit,
) -> None:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise InputError(f"无法读取 {path}：{exc}")
    except UnicodeDecodeError as exc:
        raise InputError(f"{path} 不是 UTF-8 文本：{exc}")

    audit.stats["manuscripts"] += 1
    location = display_path(path)
    headings: List[tuple] = []
    in_fence = False
    fence_marker = ""
    in_html_comment = False
    in_frontmatter = False

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line

        if line_no == 1 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() in ("---", "..."):
                in_frontmatter = False
            continue

        if in_fence:
            if line.strip().startswith(fence_marker):
                in_fence = False
            continue

        if in_html_comment:
            end = line.find("-->")
            if end == -1:
                continue
            line = line[end + 3 :]
            in_html_comment = False

        while "<!--" in line:
            start = line.find("<!--")
            end = line.find("-->", start + 4)
            if end == -1:
                line = line[:start]
                in_html_comment = True
                break
            line = line[:start] + line[end + 3 :]

        stripped = line.strip()
        fence = FENCE_RE.match(stripped)
        if fence:
            in_fence = True
            fence_marker = fence.group(1)
            continue

        line = INLINE_CODE_RE.sub("", line)
        heading = HEADING_RE.match(line.strip())
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, title))
            continue

        section = " > ".join(title for _, title in headings)
        allowed = section_allowed(section, allow_patterns)

        claim_ids = CLAIM_REF_RE.findall(line)
        if claim_ids:
            audit.stats["claim_refs"] += len(claim_ids)
            for claim_id in dict.fromkeys(claim_ids):
                claim = claims.get(claim_id)
                if claim is None:
                    audit.error(
                        "UNKNOWN_CLAIM",
                        f"正文引用了 claims.csv 中不存在的编号 {claim_id}",
                        file=location,
                        line=line_no,
                    )
                elif claim.status in UNVERIFIED_STATUSES and not allowed:
                    audit.error(
                        "UNVERIFIED_IN_FACT",
                        f"未核验断言 {claim_id}（状态：{claim.status}）出现在事实段「{section or '文首'}」",
                        file=location,
                        line=line_no,
                    )

        source_ids = SOURCE_REF_RE.findall(line)
        if source_ids:
            audit.stats["source_refs"] += len(source_ids)
            for source_id in dict.fromkeys(source_ids):
                source = sources.get(source_id)
                if source is None:
                    audit.error(
                        "UNKNOWN_SOURCE",
                        f"正文引用了 sources.json 中不存在的编号 {source_id}",
                        file=location,
                        line=line_no,
                    )
                elif source.verified in UNVERIFIED_STATUSES and not allowed:
                    audit.warning(
                        "UNVERIFIED_SOURCE_IN_FACT",
                        f"正文在事实段「{section or '文首'}」引用了未核验来源 {source_id}（状态：{source.verified}）",
                        file=location,
                        line=line_no,
                    )

    if in_frontmatter:
        audit.warning(
            "UNCLOSED_FRONTMATTER",
            "文件开头的 YAML frontmatter 未闭合，全文未被审计",
            file=location,
            line=1,
        )
    if in_fence:
        audit.warning(
            "UNCLOSED_FENCE",
            "文件结束时仍有未闭合的代码块，后续内容未被审计",
            file=location,
            line=len(lines),
        )
    if in_html_comment:
        audit.warning(
            "UNCLOSED_COMMENT",
            "文件结束时仍有未闭合的 HTML 注释，后续内容未被审计",
            file=location,
            line=len(lines),
        )


def format_issue(issue: Issue) -> str:
    if issue.file and issue.line:
        prefix = f"{issue.file}:{issue.line}"
    elif issue.file:
        prefix = issue.file
    else:
        prefix = "-"
    return f"  {prefix}  [{issue.code}] {issue.message}"


def print_report(audit: Audit, manuscript_paths: Sequence[Path]) -> None:
    stats = audit.stats
    print(
        "审计范围："
        f"claims={stats['claims']}，sources={stats['sources']}，"
        f"正文={stats['manuscripts']} 个文件，"
        f"C 引用={stats['claim_refs']}，S 引用={stats['source_refs']}"
    )
    if manuscript_paths:
        print("正文文件：" + "，".join(display_path(path) for path in manuscript_paths))

    if audit.errors:
        print(f"\n错误（{len(audit.errors)}）：")
        for issue in audit.errors:
            print(format_issue(issue))
    if audit.warnings:
        print(f"\n警告（{len(audit.warnings)}）：")
        for issue in audit.warnings:
            print(format_issue(issue))

    if audit.ok:
        print("\n结果：通过")
    else:
        reason = f"{len(audit.errors)} 个错误，{len(audit.warnings)} 个警告"
        if audit.strict and audit.warnings and not audit.errors:
            reason += "（--strict 将警告视为失败）"
        print(f"\n结果：未通过（{reason}）")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="审计科研写作的证据链：C 编号、S 编号与未核验断言。",
        epilog=(
            "默认把除「待核实 / 待核验 / 未核实 / 未核验 / 待办 / 附录 / "
            "参考文献 / 致谢」之外的章节都视为事实段。"
        ),
    )
    parser.add_argument(
        "manuscripts",
        nargs="+",
        type=Path,
        metavar="MANUSCRIPT",
        help="正文 Markdown 文件或目录（目录会递归扫描 *.md）",
    )
    parser.add_argument(
        "--claims",
        type=Path,
        default=Path("claims.csv"),
        help="断言表路径（默认 claims.csv）",
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path("sources.json"),
        help="来源表路径（默认 sources.json）",
    )
    parser.add_argument(
        "--allow-unverified-in",
        action="append",
        default=[],
        metavar="REGEX",
        help="允许未核验内容出现的章节标题正则，可重复指定",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="把警告也视为失败",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="输出 JSON 报告",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        allow_patterns = compile_allow_patterns(args.allow_unverified_in)
        audit = Audit(strict=args.strict)
        claims = load_claims(args.claims, audit)
        sources = load_sources(args.sources, audit)
        check_claim_sources(claims, sources, audit)
        manuscripts = iter_manuscripts(args.manuscripts)
        if not manuscripts:
            audit.warning("NO_MANUSCRIPT", "没有找到 Markdown 正文文件")
        for manuscript in manuscripts:
            scan_manuscript(manuscript, claims, sources, allow_patterns, audit)
    except InputError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.as_json:
        payload = {
            "ok": audit.ok,
            "strict": audit.strict,
            "stats": audit.stats,
            "errors": [issue.as_dict() for issue in audit.errors],
            "warnings": [issue.as_dict() for issue in audit.warnings],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_report(audit, manuscripts)

    return 0 if audit.ok else 1


if __name__ == "__main__":
    sys.exit(main())
