#!/usr/bin/env python3
"""
Chinese AI Flavor Multi-Dimensional Auditor & Structure Checker
中文去 AI 味多维静态审查与事实/结构门禁脚本

融合以下开源项目的检测规则：
- blader/humanizer & op7418/Humanizer-zh (31 个中文检查点与结构保护)
- hardikpandya/stop-slop (12 项快速检查与 50 分制五维评分参考)
- MrGeDiao/shuorenhua (破折号密度、二元对比密度、动词名词化、心理接住体检测)
- Hello-SimpleAI/chatgpt-comparison-detection (HC3 句长变异系数、词汇密度、路标词检测)
- OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL (段落厚度、装饰性排版、长定语检测)

Usage:
    python3 audit_chinese_ai_flavor.py <target_file> [--original <original_file>] [--json]
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


PATTERNS = {
    "A1_binary_contrast": {
        "name": "§1 虚假二元对比 (不是X而是Y / 不仅…更…)",
        "severity": "HIGH",
        "regex": [
            r"不仅(?:仅)?是[^，。；！？\n]{1,30}，更(?:是|在于)",
            r"不是[^，。；！？\n]{1,25}，而是",
            r"与其说是[^，。；！？\n]{1,25}，不如说是",
            r"问题不在于[^，。；！？\n]{1,25}，而在于",
        ],
    },
    "A3_pseudo_depth": {
        "name": "§3 伪深度格言与玄学定义",
        "severity": "HIGH",
        "regex": [
            r"是[^，。；！？\n]{2,12}的(?:语言|货币|基石|护城河|底色|解药)",
            r"归根结底，真正重要的",
            r"这才是真正的[^，。；！？\n]{2,10}[。！]",
            r"细品这句话",
        ],
    },
    "A4_throat_clearing": {
        "name": "§4 起跑式助跑铺垫与清嗓词",
        "severity": "HIGH",
        "regex": [
            r"值得注意的是",
            r"需要指出的是",
            r"不难发现",
            r"毋庸置疑",
            r"不可否认(?:的是)?",
            r"显而易见",
            r"让我们(?:一起)?深入(?:探讨|了解|看看)",
            r"以下是你需要(?:知道|了解)的",
            r"正如我们所(?:知|熟知的)",
        ],
    },
    "C12_ai_buzzwords": {
        "name": "§12 AI 高频套路词与商业黑话",
        "severity": "MEDIUM",
        "regex": [
            r"至关重要",
            r"深入探讨",
            r"交织成一幅",
            r"历史画卷",
            r"浓墨重彩",
            r"里程碑式",
            r"全方位赋能",
            r"底层逻辑",
            r"顶层设计",
            r"组合拳",
            r"降维打击",
            r"核心抓手",
            r"全链路闭环",
            r"心智渗透",
            r"生态矩阵",
        ],
    },
    "C15_shallow_riders": {
        "name": "§15 句尾拔高尾巴 (彰显了/体现了/折射出)",
        "severity": "HIGH",
        "regex": [
            r"，(?:从而|充分|深刻)?(?:彰显|凸显|体现|折射|映射|印证)了[^。！？\n]{2,35}[。！]",
            r"，标志着[^。！？\n]{2,35}(?:的到来|迈入|新纪元|新篇章)[。！]",
        ],
    },
    "E22_chatbot_residue": {
        "name": "§22 聊天机器人客服腔残留",
        "severity": "CRITICAL",
        "regex": [
            r"希望(?:以上内容|这)对(?:您|你)有所帮助",
            r"这是一个非常(?:好|深刻|有价值)的问题",
            r"如果您需要(?:进一步|更多)[^，。！？\n]{1,15}，请随时告诉我",
            r"作为一个人工智能",
        ],
    },
    "E25_meta_joiners": {
        "name": "§25 机械路标连接词与元叙述",
        "severity": "MEDIUM",
        "regex": [
            r"(?:^|\n|[。！？])\s*(?:首先|其次|再者|最后|第一，|第二，|第三，)",
            r"综上所述",
            r"总而言之",
            r"一言以蔽之",
            r"在接下来的(?:章节|部分)中，我们将",
            r"正如前文所(?:述|提到的)",
        ],
    },
    "F27_nominalization": {
        "name": "§27 动词名词化虚化 (进行了/实现了…的提升)",
        "severity": "MEDIUM",
        "regex": [
            r"进行了(?:全面|深入|系统|细致|有效)?的?[\u4e00-\u9fa5]{2,6}",
            r"实现了(?:对)?[^，。；！？\n]{2,12}的(?:提升|优化|跨越|突破|闭环|升级)",
            r"完成了对[^，。；！？\n]{2,12}的(?:梳理|重构|升级|搭建|部署)",
            r"起到了[^，。；！？\n]{2,10}的?作用",
        ],
    },
    "F29_hollow_idioms": {
        "name": "§29 空洞四字成语堆砌",
        "severity": "LOW",
        "regex": [
            r"相辅相成[、，]缺一不可",
            r"百花齐放[、，]百家争鸣",
            r"错综复杂[、，]瞬息万变",
            r"潜移默化[、，]润物无声",
            r"披荆斩棘[、，]乘风破浪",
        ],
    },
    "F30_opening_cliche": {
        "name": "§30 “随着…的发展”万金油起手",
        "severity": "HIGH",
        "regex": [
            r"(?:^|\n)\s*随着[^，。\n]{2,20}的(?:飞速|快速|不断|日益|持续)?(?:发展|演进|普及|深化)",
            r"(?:^|\n)\s*在[^，。\n]{2,20}的(?:时代|宏大|大)?背景下",
            r"(?:^|\n)\s*当今(?:世界|社会|时代)，",
        ],
    },
    "F31_closing_cliche": {
        "name": "§31 喊口号与展望式收尾",
        "severity": "HIGH",
        "regex": [
            r"让我们拭目以待",
            r"未来(?:依然)?充满无限可能",
            r"未来可期",
            r"唯有如此，我们才能在[^。！？\n]{2,20}立于不败之地",
        ],
    },
    "G33_therapy_and_punchy": {
        "name": "§33 心理接住体与自媒体暴力动作腔",
        "severity": "MEDIUM",
        "regex": [
            r"稳稳接住你的情绪",
            r"允许自己慢下来",
            r"与自己和解",
            r"掰开揉碎了讲",
            r"把天花板焊死",
            r"按在地上摩擦",
            r"超越了\s*\d+%\s*的(?:人|同龄人)",
        ],
    },
}


def strip_protected_spans(text: str) -> Tuple[str, List[str], List[str]]:
    """剥离代码块与 YAML Frontmatter，返回纯散文文本、代码块列表、标题列表"""
    prose = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    code_blocks = re.findall(r"```[\s\S]*?```", prose)
    prose = re.sub(r"```[\s\S]*?```", "", prose)
    headings = re.findall(r"^(#{1,6}\s+.*)$", prose, flags=re.MULTILINE)
    prose_no_inline = re.sub(r"`[^`\n]+`", "CODE_TOKEN", prose)
    return prose_no_inline, code_blocks, headings


def analyze_sentences_and_paragraphs(prose: str) -> Dict:
    """计算句长分布、变异系数、破折号密度、层叠“的”字链与列表占比"""
    lines = [line.strip() for line in prose.splitlines() if line.strip()]
    content_lines = [l for l in lines if not l.startswith("#")]

    bullet_lines = [
        l for l in content_lines if re.match(r"^(?:[-*+]|\d+\.)\s+", l)
    ]
    bold_label_bullets = [
        l
        for l in bullet_lines
        if re.match(r"^(?:[-*+]|\d+\.)\s+\*\*[^*]+\*\*[:：]?\s*", l)
    ]

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", prose)
        if p.strip() and not p.strip().startswith("#")
    ]

    em_dash_count = len(re.findall(r"——|--", prose))
    dense_dash_paras = 0
    for p in paragraphs:
        if len(re.findall(r"——|--", p)) >= 2 or p.startswith("——"):
            dense_dash_paras += 1

    raw_sentences = re.split(r"[。！？!?]+", "\n".join(content_lines))
    sentences = [
        re.sub(r"\s+", "", s)
        for s in raw_sentences
        if len(re.sub(r"\s+", "", s)) >= 3
    ]

    lengths = [len(s) for s in sentences]
    if lengths:
        mean_len = sum(lengths) / len(lengths)
        variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_len if mean_len > 0 else 0.0
    else:
        mean_len, std_dev, cv = 0.0, 0.0, 0.0

    metronomic_triplets = 0
    for i in range(len(lengths) - 2):
        if (
            max(lengths[i : i + 3]) - min(lengths[i : i + 3]) <= 3
            and lengths[i] >= 10
        ):
            metronomic_triplets += 1

    clauses = re.split(r"[，。；！？,.;!?]+", "\n".join(content_lines))
    stacked_de_clauses = [
        c.strip()
        for c in clauses
        if c.count("的") >= 3 and len(c.strip()) >= 12
    ]

    bold_spans = re.findall(r"\*\*[^*\n]+\*\*", prose)
    emoji_headings = [
        l
        for l in lines
        if l.startswith("#")
        and re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", l)
    ]

    total_chars = sum(len(l) for l in content_lines)

    return {
        "total_chars": total_chars,
        "paragraph_count": len(paragraphs),
        "sentence_count": len(sentences),
        "mean_sentence_length": round(mean_len, 2),
        "sentence_length_std_dev": round(std_dev, 2),
        "sentence_length_cv": round(cv, 2),
        "metronomic_triplets": metronomic_triplets,
        "em_dash_count": em_dash_count,
        "dense_dash_paragraphs": dense_dash_paras,
        "stacked_de_clauses_count": len(stacked_de_clauses),
        "stacked_de_examples": stacked_de_clauses[:3],
        "bullet_line_ratio": round(
            len(bullet_lines) / max(len(content_lines), 1), 2
        ),
        "bold_label_bullet_count": len(bold_label_bullets),
        "bold_span_count": len(bold_spans),
        "emoji_heading_count": len(emoji_headings),
    }


def check_fact_and_structure_preservation(
    orig_text: str, target_text: str
) -> Dict:
    """对照原稿与改写稿，检查代码块、标题层级与核心数字是否守恒"""
    _, orig_code, orig_headings = strip_protected_spans(orig_text)
    _, targ_code, targ_headings = strip_protected_spans(target_text)

    orig_prose, _, _ = strip_protected_spans(orig_text)
    targ_prose, _, _ = strip_protected_spans(target_text)
    # 排除 URL/行内代码里的数字，避免误把链接参数当作正文事实。
    def numeric_claims(prose: str) -> set:
        prose = re.sub(r"https?://[^\s)]+", "", prose)
        prose = prose.replace("CODE_TOKEN", "")
        return set(re.findall(r"(?<![A-Za-z0-9])\d+(?:\.\d+)?%?", prose))
    orig_numbers = numeric_claims(orig_prose)
    targ_numbers = numeric_claims(targ_prose)
    missing_numbers = sorted(list(orig_numbers - targ_numbers))
    added_numbers = sorted(list(targ_numbers - orig_numbers))

    # 数字相同但单位变成 "万/亿" 也是重大内容变更。
    claim_token_re = r"(?<![A-Za-z0-9])\d+(?:\.\d+)?%?(?:万亿|亿元|万元|亿美元|万|亿|千|百|元|美元|年|月|日|人|套|亩|件|%|倍)?"
    def claim_tokens(prose: str) -> set:
        cleaned = re.sub(r"https?://[^\s)]+", "", prose)
        return set(re.findall(claim_token_re, cleaned))
    changed_unit_tokens = sorted(list(claim_tokens(orig_prose) ^ claim_tokens(targ_prose)))

    # 受保护内容与本地文档结构：只检查变化，不臆测其含义。
    def inline_code(text: str) -> list:
        return re.findall(r"(?<!`)`[^`\n]+`(?!`)", text)
    def table_rows(text: str) -> list:
        return re.findall(r"^\s*\|.*\|\s*$", text, flags=re.MULTILINE)
    def frontmatter(text: str) -> str:
        match = re.match(r"\A---\n.*?\n---\n", text, flags=re.DOTALL)
        return match.group(0) if match else ""
    orig_inline = inline_code(orig_text)
    target_inline = inline_code(target_text)
    orig_tables = table_rows(orig_text)
    target_tables = table_rows(target_text)
    fm_original = frontmatter(orig_text)
    fm_target = frontmatter(target_text)

    return {
        "code_blocks_preserved": orig_code == targ_code,
        "orig_code_block_count": len(orig_code),
        "target_code_block_count": len(targ_code),
        "headings_preserved": orig_headings == targ_headings,
        "orig_heading_count": len(orig_headings),
        "target_heading_count": len(targ_headings),
        "missing_numbers": missing_numbers,
        "invented_numbers": added_numbers,
        "changed_number_or_unit_tokens": changed_unit_tokens,
        "inline_code_preserved": orig_inline == target_inline,
        "markdown_tables_preserved": orig_tables == target_tables,
        "frontmatter_preserved": fm_original == fm_target,
    }


def compute_50_point_score(
    hits: Dict[str, List[str]], stats: Dict, preservation: Optional[Dict]
) -> Dict:
    """基于 stop-slop 与 Humanizer-zh 规则计算 50 分制五维参考得分"""
    directness = 10.0
    rhythm = 10.0
    trust = 10.0
    authenticity = 10.0
    density = 10.0

    # 1. Directness 扣分项：起跑铺垫、二元对比、万金油开头、机械路标
    directness -= min(4.0, len(hits.get("A4_throat_clearing", [])) * 2.0)
    directness -= min(3.0, len(hits.get("A1_binary_contrast", [])) * 1.5)
    directness -= min(2.0, len(hits.get("F30_opening_cliche", [])) * 2.0)
    directness -= min(2.0, len(hits.get("E25_meta_joiners", [])) * 1.0)

    # 2. Rhythm 扣分项：句长标准差过低、等长句三连、破折号过密、层叠“的”
    if stats["sentence_count"] >= 4 and stats["sentence_length_std_dev"] < 4.5:
        rhythm -= 3.0
    rhythm -= min(3.0, stats["metronomic_triplets"] * 1.5)
    rhythm -= min(2.0, stats["dense_dash_paragraphs"] * 1.5)
    rhythm -= min(2.0, stats["stacked_de_clauses_count"] * 1.0)

    # 3. Trust 扣分项：伪深度格言、句尾拔高尾巴、粗体标签列表、喊口号结尾
    trust -= min(3.0, len(hits.get("A3_pseudo_depth", [])) * 2.0)
    trust -= min(3.0, len(hits.get("C15_shallow_riders", [])) * 2.0)
    trust -= min(2.0, stats["bold_label_bullet_count"] * 1.0)
    trust -= min(2.0, len(hits.get("F31_closing_cliche", [])) * 2.0)

    # 4. Authenticity 扣分项：客服残留、AI 黑话、心理接住体、事实篡改
    authenticity -= min(5.0, len(hits.get("E22_chatbot_residue", [])) * 4.0)
    authenticity -= min(3.0, len(hits.get("C12_ai_buzzwords", [])) * 1.0)
    authenticity -= min(2.0, len(hits.get("G33_therapy_and_punchy", [])) * 2.0)
    if preservation and (
        preservation["invented_numbers"] or not preservation["code_blocks_preserved"]
    ):
        authenticity -= 4.0

    # 5. Density 扣分项：动词名词化虚化、空洞四字成语
    density -= min(4.0, len(hits.get("F27_nominalization", [])) * 1.5)
    density -= min(3.0, len(hits.get("F29_hollow_idioms", [])) * 1.5)
    density -= min(2.0, len(hits.get("A4_throat_clearing", [])) * 1.0)

    scores = {
        "Directness (直接性)": max(1, round(directness)),
        "Rhythm (节奏感)": max(1, round(rhythm)),
        "Trust (信任度)": max(1, round(trust)),
        "Authenticity (真实感)": max(1, round(authenticity)),
        "Density (信息密度)": max(1, round(density)),
    }
    total = sum(scores.values())
    scores["Total (总分/50)"] = total
    scores["Pass (门禁通过 >=40)"] = total >= 40
    return scores


def audit_file(target_path: Path, orig_path: Optional[Path] = None) -> Dict:
    text = target_path.read_text(encoding="utf-8")
    prose, _, _ = strip_protected_spans(text)

    hits: Dict[str, List[str]] = {}
    detailed_findings = []

    for key, cfg in PATTERNS.items():
        matched_items = []
        for rgx in cfg["regex"]:
            for m in re.finditer(rgx, prose, flags=re.MULTILINE):
                snippet = m.group(0).strip().replace("\n", " ")
                matched_items.append(snippet)
        if matched_items:
            hits[key] = matched_items
            detailed_findings.append(
                {
                    "id": key,
                    "rule": cfg["name"],
                    "severity": cfg["severity"],
                    "count": len(matched_items),
                    "samples": matched_items[:5],
                }
            )

    stats = analyze_sentences_and_paragraphs(prose)
    preservation = None
    if orig_path and orig_path.exists():
        orig_text = orig_path.read_text(encoding="utf-8")
        preservation = check_fact_and_structure_preservation(orig_text, text)

    scores = compute_50_point_score(hits, stats, preservation)
    hard_errors = []
    if preservation:
        if not preservation["code_blocks_preserved"]:
            hard_errors.append("原稿代码块内容发生变化")
        if not preservation["headings_preserved"]:
            hard_errors.append("原稿 Markdown 标题发生变化（请人工确认是否为授权重构）")
        if preservation["invented_numbers"]:
            hard_errors.append("存在原稿未出现的数字，需逐项核实来源")
        if preservation["missing_numbers"]:
            hard_errors.append("存在原稿数字缺失，需逐项核实是否有意删除")
        if preservation["changed_number_or_unit_tokens"]:
            hard_errors.append("数字或单位表达发生变化，需核对万/亿/日期等单位与语境")
        if not preservation["inline_code_preserved"]:
            hard_errors.append("行内代码发生变化")
        if not preservation["markdown_tables_preserved"]:
            hard_errors.append("Markdown 表格数据发生变化")
        if not preservation["frontmatter_preserved"]:
            hard_errors.append("YAML frontmatter 发生变化（需人工确认）")
    scores["Pass (门禁通过 >=40)"] = scores["Pass (门禁通过 >=40)"] and not hard_errors

    return {
        "hard_errors": hard_errors,
        "disclaimer": "仅为启发式文风与文本差异检测；不能证明事实真实、原创性或平台合规。",
        "file": str(target_path),
        "scores": scores,
        "statistics": stats,
        "pattern_findings": detailed_findings,
        "preservation_check": preservation,
    }


def print_report(result: Dict) -> None:
    print("=" * 68)
    print(f"📋 中文去 AI 味多维审查报告 | 文件: {result['file']}")
    print("=" * 68)

    scores = result["scores"]
    status_str = (
        "✅ PASS (准予交付)"
        if scores["Pass (门禁通过 >=40)"]
        else "❌ FAIL (需返工重修)"
    )
    print(
        f"\n【1. 50 分制五维评分门禁】 总分: {scores['Total (总分/50)']}/50  --> {status_str}"
    )
    for k, v in scores.items():
        if k not in ("Total (总分/50)", "Pass (门禁通过 >=40)"):
            print(f"  - {k}: {v}/10")

    stats = result["statistics"]
    print("\n【2. 句法与排版分布指标 (HC3 & Style DNA 校准)】")
    print(
        f"  - 正文总字数: {stats['total_chars']} 字 | 段落数: {stats['paragraph_count']} | 句子数: {stats['sentence_count']}"
    )
    std_status = (
        "✅ 自然"
        if stats["sentence_length_std_dev"] >= 4.5
        else "⚠️ 偏单调 (建议 >= 4.5)"
    )
    print(
        f"  - 平均句长: {stats['mean_sentence_length']} 字 | 句长标准差: {stats['sentence_length_std_dev']} ({std_status})"
    )
    print(
        f"  - 连续三句等长次数: {stats['metronomic_triplets']} 次 | 破折号总数: {stats['em_dash_count']} (高密破折号段落: {stats['dense_dash_paragraphs']})"
    )
    print(
        f"  - 单分句 >=3 个“的”字链: {stats['stacked_de_clauses_count']} 处 | 粗体标签列表项: {stats['bold_label_bullet_count']} 处 | 标题 Emoji: {stats['emoji_heading_count']} 处"
    )

    findings = result["pattern_findings"]
    print(f"\n【3. 命中的 AI 痕迹检查点 ({len(findings)} 类)】")
    if not findings:
        print("  🎉 未检出典型 AI 套话、虚假二元对比或虚化动词结构！")
    else:
        for f in findings:
            print(
                f"  [{f['severity']}] {f['rule']} (命中 {f['count']} 处): 示例 -> {f['samples']}"
            )

    if result["preservation_check"]:
        p = result["preservation_check"]
        print("\n【4. 原稿事实账本与受保护结构核对】")
        print(
            f"  - 代码块完全守恒: {'✅ 是' if p['code_blocks_preserved'] else '❌ 否'}"
        )
        print(f"  - 标题层级守恒: {'✅ 是' if p['headings_preserved'] else '⚠️ 有变动'}")
        print(
            f"  - 疑似丢失的原稿数字: {p['missing_numbers'] if p['missing_numbers'] else '无'}"
        )
        print(
            f"  - 疑似新增的未授权数字: {p['invented_numbers'] if p['invented_numbers'] else '无'}"
        )
    print("=" * 68)


def main() -> None:
    parser = argparse.ArgumentParser(description="中文 AI 味多维静态审查脚本")
    parser.add_argument("target", type=Path, help="待审查的目标 Markdown/文本文件")
    parser.add_argument(
        "--original",
        type=Path,
        default=None,
        help="可选：用于比对事实与结构守恒的原始文件",
    )
    parser.add_argument(
        "--json", action="store_true", help="以 JSON 格式输出审查结果"
    )
    parser.add_argument("--strict", action="store_true", help="未通过评分或事实差异门禁时退出码为 2")
    args = parser.parse_args()

    if not args.target.exists():
        print(f"Error: 找不到目标文件 {args.target}", file=sys.stderr)
        sys.exit(1)

    res = audit_file(args.target, args.original)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print_report(res)
    if args.strict and not res["scores"]["Pass (门禁通过 >=40)"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
