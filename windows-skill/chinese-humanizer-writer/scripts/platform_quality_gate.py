#!/usr/bin/env python3
"""Offline deterministic preflight for WeChat / X / Xiaohongshu drafts.

This is NOT a factual or platform-policy certification. Editor requirements and
limits change; final account-side checks and human approval remain mandatory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

URL_RE = re.compile(r"https?://[^\s<>)]+")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
MARKDOWN_H1 = re.compile(r"^#\s+(.+)$", re.M)
SOURCE_PLACEHOLDERS = ("【待核实", "【待补", "【待你补", "【待拟", "【待写", "[待", "TODO", "TBD")


def parse_draft(raw: str) -> tuple[str, str]:
    title = ""
    fm = FRONTMATTER_RE.match(raw)
    body = raw[fm.end():] if fm else raw
    if fm:
        for line in fm.group(1).splitlines():
            if line.startswith("title:"):
                value = line.split(":", 1)[1].strip()
                try:
                    title = json.loads(value)
                except (ValueError, TypeError):
                    title = value.strip("'\"")
                break
    if not title:
        m = MARKDOWN_H1.search(body)
        if m:
            title = m.group(1).strip()
            body = body[:m.start()] + body[m.end():]
    body = re.sub(r"<!--(?!\s*POST\s*-->)[\s\S]*?-->", "", body)
    return title, body.strip()


def x_weight_estimate(content: str) -> int:
    """Conservative approximation, not the official twitter-text implementation."""
    content = URL_RE.sub(lambda _: "A" * 23, content)
    total = 0
    for ch in content:
        if ch in "\r\n":
            total += 1
        elif unicodedata.combining(ch) or ch == "\u200d":
            total += 0
        else:
            total += 2 if (unicodedata.east_asian_width(ch) in "WF" or ord(ch) >= 0x1F000) else 1
    return total


def validate(platform: str, raw: str, evidence: dict | None = None,
             x_limit: int = 280, xhs_title_limit: int = 20) -> dict:
    title, body = parse_draft(raw)
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict = {"title": title, "body_chars": len(body)}

    if not body.strip():
        errors.append("稿件正文为空")
    for placeholder in SOURCE_PLACEHOLDERS:
        if placeholder in body or placeholder in title:
            errors.append("发现未完成的素材/事实/人工体验占位符，发布前必须处理")
            break

    if platform == "wechat":
        if not title:
            warnings.append("公众号缺少标题，请检查编辑器中的最终标题")
        if title and len(title) > 40:
            warnings.append("公众号标题较长，可能影响手机端展示（仅编辑建议）")
        paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip() and not p.lstrip().startswith("#")]
        metrics["paragraphs"] = len(paras)
        metrics["long_paragraphs_over_180"] = sum(1 for p in paras if len(p) > 180)
        if metrics["long_paragraphs_over_180"]:
            warnings.append(f"有 {metrics['long_paragraphs_over_180']} 段超过180字，检查手机端阅读节奏")
        if len(body) < 350:
            warnings.append("正文偏短；若是长文栏目，请确认有足够的故事/证据与论点")

    elif platform == "x":
        # Only explicit delimiters split tweets: do not split ordinary Markdown horizontal rules.
        posts = [v.strip() for v in re.split(r"(?m)^\s*<!--\s*POST\s*-->\s*$", body) if v.strip()]
        metrics["post_count"] = len(posts)
        metrics["estimated_post_lengths"] = [x_weight_estimate(p) for p in posts]
        for n, length in enumerate(metrics["estimated_post_lengths"], 1):
            if length > x_limit:
                errors.append(f"X 第 {n} 条预计 {length} 加权字符，超过当前设置上限 {x_limit}")
            elif length >= x_limit - 10:
                warnings.append(f"X 第 {n} 条接近上限，请用 X 编辑器复核实际字符计数")
        if title and not posts:
            errors.append("X 内容为空")
        if len(posts) > 1 and any(len(p) < 15 for p in posts):
            warnings.append("线程中存在极短帖子，请确认每条都有独立的信息增量")
        if title:
            warnings.append("X 稿件的标题仅作为归档元数据，发布时不要自动加入帖子正文")
        warnings.append("X 字符计数仅为离线估算；最终以平台编辑器为准")

    elif platform == "xiaohongshu":
        if not title:
            warnings.append("小红书笔记没有标题")
        metrics["title_codepoints"] = len(title)
        if len(title) > xhs_title_limit:
            warnings.append(f"标题超过 {xhs_title_limit} 个 Python 字符；请在小红书编辑器核对标题限制")
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        metrics["first_3_nonempty_lines"] = lines[:3]
        if len(lines) < 3:
            warnings.append("开头不足3行，检查信息流可见部分是否讲清受众与收益")
        if len(body) > 1500:
            warnings.append("笔记较长，请复核折叠展示、信息密度、内页分图")
        if not re.search(r"(?<!\w)#[^\s#]{2,20}", body):
            warnings.append("未发现话题标签，可根据搜索意图人工选择相关标签")
        if not re.search(r"\b(广告|商单|合作|赞助|推广)\b", body):
            warnings.append("如存在品牌合作/广告关系，须按照平台规则清晰披露；纯非商业稿可忽略")
    else:
        raise ValueError("unsupported platform: " + platform)

    if evidence is None:
        warnings.append("未提供证据账本：仅能做文本静态检查，不能确认日期/金额/引文的真实性")
    else:
        claims = evidence.get("claims")
        if not isinstance(claims, list):
            errors.append("证据账本的 claims 必须是数组")
        else:
            metrics["claims_total"] = len(claims)
            for i, claim in enumerate(claims, 1):
                if not isinstance(claim, dict):
                    errors.append(f"证据第{i}条不是对象")
                    continue
                status = claim.get("status", "unverified")
                statement = str(claim.get("statement", "")).strip()
                url = str(claim.get("source_url", "")).strip()
                if status != "verified":
                    errors.append(f"证据第{i}条未核实：{statement[:30] or '未填写陈述'}")
                elif not url.startswith(("https://", "http://")):
                    errors.append(f"证据第{i}条标记为已核实，但缺少可追溯来源链接")
                if not statement:
                    errors.append(f"证据第{i}条缺少事实陈述")
            if not claims:
                warnings.append("证据账本为空；涉及事实断言、数字、引文时应补证据")

    return {
        "platform": platform,
        "passed_static_gate": not errors,
        "errors": errors,
        "warnings": list(dict.fromkeys(warnings)),
        "metrics": metrics,
        "scope": "静态检查，不等于真实性/版权/平台政策审定，也不代表可自动发布",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="三平台稿件发布前静态门禁（离线）")
    ap.add_argument("--platform", choices=("wechat", "x", "xiaohongshu"), required=True)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--evidence", type=Path)
    ap.add_argument("--x-limit", type=int, default=280, help="默认普通短帖280，付费长帖可自行按当前账号能力覆盖")
    ap.add_argument("--xhs-title-limit", type=int, default=20, help="默认参考值而非官方合规证明")
    ap.add_argument("--strict", action="store_true", help="发现 errors 时以退出码2结束")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.x_limit < 1 or args.xhs_title_limit < 1:
        ap.error("limits must be positive")
    try:
        raw = args.input.read_text(encoding="utf-8-sig")
        ledger = json.loads(args.evidence.read_text(encoding="utf-8-sig")) if args.evidence else None
        result = validate(args.platform, raw, ledger, args.x_limit, args.xhs_title_limit)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"输入读取或解析失败：{e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[{result['platform']}] 静态门禁: {'PASS' if result['passed_static_gate'] else 'FAIL'}")
        for x in result["errors"]:
            print("[BLOCK]", x)
        for x in result["warnings"]:
            print("[REVIEW]", x)
    if args.strict and not result["passed_static_gate"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
