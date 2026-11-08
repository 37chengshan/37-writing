#!/usr/bin/env python3
"""
Six-Layer Writing DNA Distiller (Dual-Track: External Benchmarks vs. Our Own Voice)
六维写作 DNA 量化蒸馏器（支持外部标杆账号与自有公众号双轨隔离建档）

融合以下开源项目的设计：
- larashero3-dotcom/writing-dna-skill (L1-L6 六维分析 + 5 份分层文档 + 5 篇近期同体裁原文抽取器)
- alchaincyf/nuwa-skill (6 项量化句式指纹与心智模型框架)
- SpaceZephyr/creator-buddy (公众号单段字数分布、开头 Hook 统计与排版特征)

Usage:
    python3 distill_style_dna.py --profile-dir style_profiles/external_benchmarks/某博主
    python3 distill_style_dna.py --profile-dir style_profiles/our_own_voice/我的公众号 --select-samples "深度分析"
"""

import argparse
import collections
import datetime
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


COMMON_CONNECTORS = [
    "说白了",
    "其实",
    "说实话",
    "话说回来",
    "反过来想",
    "往深里看",
    "更麻烦的是",
    "问题在于",
    "但实际上",
    "换句话说",
    "换个角度",
    "哪怕",
    "偏偏",
    "索性",
    "干脆",
    "固然",
    "诚然",
    "未尝不",
    "大抵",
    "罢了",
    "顺着这个逻辑",
    "回过头来看",
    "说到底",
]

AI_NOISE_ADVERBS = [
    "非常",
    "极其",
    "深刻地",
    "全方位地",
    "毫无疑问地",
    "至关重要",
    "值得注意的是",
    "不难发现",
    "综上所述",
    "总而言之",
]


def strip_frontmatter_and_code(raw_md: str) -> Tuple[Dict[str, str], str]:
    meta = {}
    body = raw_md
    m = re.match(r"\A---\n(.*?)\n---\n([\s\S]*)", raw_md, flags=re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if v.startswith('"'):
                    try:
                        v = json.loads(v)
                    except ValueError:
                        v = v.strip('"')
                else:
                    v = v.strip("'")
                meta[k.strip()] = v
        body = m.group(2)
    body = re.sub(r"```[\s\S]*?```", "", body)
    return meta, body.strip()


def analyze_corpus_l1_l6(profile_dir: Path, platform_filter: str = "") -> Dict:
    raw_dir = profile_dir / "raw"
    meta_dir = profile_dir / "_meta"
    md_files = sorted(raw_dir.glob("*.md"))
    if platform_filter:
        md_files = [f for f in md_files if strip_frontmatter_and_code(f.read_text(encoding="utf-8"))[0].get("platform", "wechat") == platform_filter]
    if not md_files:
        raise ValueError(f"在 {raw_dir} 下未找到任何 .md 语料文件，请先运行 fetch_and_archive_articles.py")

    account_name = profile_dir.name
    # 只接受预期的双轨目录，不允许意外将 external 当自有素材使用。
    if profile_dir.parent.name not in ("our_own_voice", "external_benchmarks"):
        raise ValueError("profile-dir 必须位于 our_own_voice 或 external_benchmarks 下")
    track = "self" if profile_dir.parent.name == "our_own_voice" else "external"
    platform = "wechat"

    all_sent_lengths: List[int] = []
    all_para_chars: List[int] = []
    all_para_sents: List[int] = []
    heading_lengths: List[int] = []

    total_chars = 0
    em_dash_total = 0
    paren_total = 0
    semi_total = 0
    quest_total = 0
    exclam_total = 0
    bold_total = 0
    image_total = 0
    cjk_quote_curly = 0
    cjk_quote_corner = 0

    connector_counter: collections.Counter = collections.Counter()
    bigram_counter: collections.Counter = collections.Counter()
    hook_counter: collections.Counter = collections.Counter()
    structure_counter: collections.Counter = collections.Counter()
    type_counter: collections.Counter = collections.Counter()
    first_sentences: List[str] = []
    last_sentences: List[str] = []

    for fpath in md_files:
        fm, body = strip_frontmatter_and_code(fpath.read_text(encoding="utf-8"))
        if fm.get("account"):
            account_name = fm["account"]
        if fm.get("track") and fm["track"] != track:
            raise ValueError(f"检测到轨道不匹配语料 {fpath.name}：{fm['track']} != {track}")
        if fm.get("platform"):
            platform = fm["platform"]

        lines = [l.strip() for l in body.splitlines() if l.strip()]
        # 移除首行主标题
        if lines and lines[0].startswith("# "):
            lines = lines[1:]

        for l in lines:
            if l.startswith("#"):
                h_txt = l.lstrip("#").strip()
                heading_lengths.append(len(h_txt))

        content_text = "\n".join(l for l in lines if not l.startswith("#"))
        chars = len(re.sub(r"\s+", "", content_text))
        total_chars += chars

        em_dash_total += len(re.findall(r"——|--", content_text))
        paren_total += len(re.findall(r"[（(][^）)\n]{1,60}[）)]", content_text))
        semi_total += content_text.count("；") + content_text.count(";")
        quest_total += content_text.count("？") + content_text.count("?")
        exclam_total += content_text.count("！") + content_text.count("!")
        bold_total += len(re.findall(r"\*\*[^*\n]+\*\*", content_text))
        image_total += len(re.findall(r"!\[.*?\]\(.*?\)", content_text))
        cjk_quote_curly += content_text.count("“")
        cjk_quote_corner += content_text.count("「")

        for conn in COMMON_CONNECTORS:
            cnt = content_text.count(conn)
            if cnt > 0:
                connector_counter[conn] += cnt

        # 统计高频双字/四字中文词块
        for token in re.findall(r"[\u4e00-\u9fa5]{2,4}", content_text):
            if token not in ("我们", "他们", "这个", "一个", "可以", "因为", "所以", "如果", "没有", "就是", "不是"):
                bigram_counter[token] += 1

        paras = [
            p.strip()
            for p in re.split(r"\n\s*\n", body)
            if p.strip() and not p.strip().startswith("#") and not p.strip().startswith("![")
        ]
        for p in paras:
            p_clean = re.sub(r"\s+", "", p)
            if len(p_clean) >= 4:
                all_para_chars.append(len(p_clean))
            p_sents = [
                re.sub(r"\s+", "", s)
                for s in re.split(r"[。！？!?]+", p)
                if len(re.sub(r"\s+", "", s)) >= 3
            ]
            if p_sents:
                all_para_sents.append(len(p_sents))
                all_sent_lengths.extend(len(s) for s in p_sents)

        doc_sents = [
            re.sub(r"\s+", "", s)
            for s in re.split(r"[。！？!?]+", content_text)
            if len(re.sub(r"\s+", "", s)) >= 4
        ]
        if doc_sents:
            first_sentences.append(doc_sents[0][:60])
            last_sentences.append(doc_sents[-1][:60])

        meta_json_path = meta_dir / f"{fpath.stem}.json"
        if meta_json_path.exists():
            try:
                mdata = json.loads(meta_json_path.read_text(encoding="utf-8"))
                hook_counter[mdata.get("hook_type", "场景式")] += 1
                structure_counter[mdata.get("structure_pattern", "单点剥笋推进")] += 1
                type_counter[mdata.get("article_type", "深度分析")] += 1
            except Exception:
                pass

    k_factor = max(total_chars / 1000.0, 0.1)
    mean_sent = sum(all_sent_lengths) / max(len(all_sent_lengths), 1)
    std_sent = math.sqrt(
        sum((x - mean_sent) ** 2 for x in all_sent_lengths) / max(len(all_sent_lengths), 1)
    )
    short_ratio = (
        sum(1 for x in all_sent_lengths if x <= 15) / max(len(all_sent_lengths), 1) * 100
    )
    long_ratio = (
        sum(1 for x in all_sent_lengths if x >= 50) / max(len(all_sent_lengths), 1) * 100
    )
    mean_para_c = sum(all_para_chars) / max(len(all_para_chars), 1)
    mean_para_s = sum(all_para_sents) / max(len(all_para_sents), 1)
    mean_head_l = sum(heading_lengths) / max(len(heading_lengths), 1) if heading_lengths else 10.0

    quote_style = "「」直角引号" if cjk_quote_corner > cjk_quote_curly else "“”双弯引号"

    # 读取自有账号的进化账本（若存在）
    ledger_path = profile_dir / "evolution_ledger.json"
    ledger_data = {}
    if ledger_path.exists():
        try:
            ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "account": account_name,
        "track": track,
        "platform": platform,
        "article_count": len(md_files),
        "total_words": total_chars,
        "mean_sent_len": round(mean_sent, 1),
        "std_sent_len": round(std_sent, 1),
        "short_sent_ratio": round(short_ratio, 1),
        "long_sent_ratio": round(long_ratio, 1),
        "mean_para_chars": round(mean_para_c, 1),
        "mean_para_sents": round(mean_para_s, 1),
        "em_dash_per_1k": round(em_dash_total / k_factor, 2),
        "paren_per_1k": round(paren_total / k_factor, 2),
        "semi_per_1k": round(semi_total / k_factor, 2),
        "quest_per_1k": round(quest_total / k_factor, 2),
        "exclam_per_1k": round(exclam_total / k_factor, 2),
        "bold_per_1k": round(bold_total / k_factor, 2),
        "image_per_1k": round(image_total / k_factor, 2),
        "mean_heading_len": round(mean_head_l, 1),
        "quote_style": quote_style,
        "top_connectors": [k for k, _ in connector_counter.most_common(10)],
        "top_terms": [k for k, _ in bigram_counter.most_common(25)],
        "hook_distribution": dict(hook_counter),
        "structure_distribution": dict(structure_counter),
        "type_distribution": dict(type_counter),
        "sample_openings": first_sentences[:5],
        "sample_closings": last_sentences[:5],
        "evolution_ledger": ledger_data,
    }


def write_distilled_files(profile_dir: Path, stats: Dict, output_dir: Path | None = None) -> List[str]:
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    is_external = stats["track"] == "external"
    track_banner = (
        "⚠️ **【外部标杆安全锁】**：本账号为外部标杆（`track: external`）。借用本风格辅助写稿时，**仅允许借鉴其句长节奏、段落呼吸、开头 Hook 与结构骨架**；严禁挪用其第一人称个人经历、公司案例、人设自称与独创口头禅！"
        if is_external
        else "✅ **【自有公众号主创基因】**：本账号为我们自己的主创风格库（`track: self`）。写作时全量继承其人设、历史观点、语言习惯与底部的 `evolution_ledger.json` 手改进化规则。"
    )

    ledger = stats.get("evolution_ledger") or {}
    killed_words = ledger.get("hard_banned_phrases", [])
    replacements = ledger.get("preferred_replacements", [])
    learned_rules = ledger.get(
        "structural_rules_learned",
        ["尚未录入人工手改 Diff 记录；运行 learn_from_user_edits.py 后将自动在此沉淀。"],
    )

    # 1. 语言DNA.md (L1)
    l1_md = f"""# L1 表层语言 DNA（语言DNA.md）

{track_banner}

## 1. 句式与段落量化指纹（基于 {stats['article_count']} 篇原文 / {stats['total_words']} 字实测）
- **平均句长**：`{stats['mean_sent_len']}` 字 | **句长标准差**：`{stats['std_sent_len']}`（保持长短交错呼吸感）
- **短句（≤15字）占比**：`{stats['short_sent_ratio']}%` | **长句（≥50字）占比**：`{stats['long_sent_ratio']}%`
- **段落颗粒度**：平均每段 `{stats['mean_para_sents']}` 句、约 `{stats['mean_para_chars']}` 字（目标单段上限：`{max(90, int(stats['mean_para_chars'] * 1.3))}` 字）

## 2. 标点生态指纹（每千字频次）
- **破折号 (`——`)**：`{stats['em_dash_per_1k']}` 次/千字
- **括号插话 (`（）`)**：`{stats['paren_per_1k']}` 次/千字（用于补充背景、吐槽或限定条件）
- **分号 (`；`)**：`{stats['semi_per_1k']}` 次/千字
- **问号 (`？`)**：`{stats['quest_per_1k']}` 次/千字（保留推动思考的真问题）
- **感叹号 (`！`)**：`{stats['exclam_per_1k']}` 次/千字
- **引号规范**：统一使用 `{stats['quote_style']}`

## 3. 词汇与连接词偏好
- **高频自然过渡词**：`{', '.join(stats['top_connectors']) if stats['top_connectors'] else '直接靠逻辑硬切，极少用显性连词'}`
- **高频词块（粗统计，需人工去噪）**：`{', '.join(stats['top_terms'][:15])}`
- **经多轮学习确认的禁用词**：`{', '.join(killed_words) if killed_words else '暂无；通用 AI 味规则仅作参考'}`
"""

    # 2. 文章结构模板.md (L2)
    openings_bullets = "\n".join(f"  - 「{s}……」" for s in stats["sample_openings"])
    closings_bullets = "\n".join(f"  - 「……{s}」" for s in stats["sample_closings"])
    l2_md = f"""# L2 文章结构模板（文章结构模板.md）

{track_banner}

## 1. 语料体裁与结构分布统计
- **体裁分布**：`{json.dumps(stats['type_distribution'], ensure_ascii=False)}`
- **开头 Hook 分布**：`{json.dumps(stats['hook_distribution'], ensure_ascii=False)}`
- **主体推进骨架分布**：`{json.dumps(stats['structure_distribution'], ensure_ascii=False)}`

## 2. 原文真实开篇第一句采样（校准起手式）
{openings_bullets}

## 3. 原文真实收尾末句采样（校准落点感）
{closings_bullets}

## 4. 核心体裁可复用结构骨架
- **深度分析 / 评论体裁**：
  1. **起手 Hook（100-200 字）**：拒绝宏大背景铺垫，直接以具体时间锚点、反常数据或锋利判断切入。
  2. **第一转折（引出真问题）**：拆穿表面共识，指出真正常见但被忽略的矛盾点。
  3. **主体拆解（2-4 个小节）**：每节小标题平均 `{stats['mean_heading_len']}` 字，采用「结论句 -> 具体算账/案例截图 -> 冷峻推论」推进。
  4. **反面与边界讨论（约 250 字）**：主动交代方案的代价或适用条件，消灭公关吹捧感。
  5. **收尾落点**：不喊口号，落在最后一个具体判断或单一行动建议上。
"""

    # 3. 写作视角与认知框架.md (L3-L5)
    l35_md = f"""# L3-L5 写作视角与认知框架（写作视角与认知框架.md）

{track_banner}

## 1. L3 选题切入逻辑
- **样本真实切入视角**：【需人工通读样本后填写；仅凭词频无法得出作者观点】。
- **样本不写的话题边界**：【待人工核实】。

## 2. L4 素材策略与证据链组织
- **样本证据偏好**：【待人工核验每篇引用、截图、数字来源后填写】。不能因为文章出现数字就默认该数字真实。
- **通用编辑建议（不是作者真实偏好）**：需要数据时给出可追溯的事实锚点；缺个人经历时留白请作者补充，不允许 AI 凭空捏造。

## 3. L5 核心认知启发式（Decision Heuristics）
- **作者真实的跨选题判断 1**：【待人工从至少 3 篇不同主题原文交叉验证】。
- **作者真实的跨选题判断 2**：【待人工从至少 3 篇不同主题原文交叉验证】。
- **防幻觉原则**：空白不能自动填成「作者总是认为」，也不能将外部作者的判断当自有立场。
"""

    # 4. 视觉风格指南.md (L6)
    l6_md = f"""# L6 视觉与排版风格指南（视觉风格指南.md）

## 1. 排版与强调密度
- **段落呼吸感**：平均每段 `{stats['mean_para_chars']}` 字（`{stats['mean_para_sents']}` 句），手机屏阅读极度友好。
- **小标题长度**：平均 `{stats['mean_heading_len']}` 字。
- **加粗克制**：每千字加粗约 `{stats['bold_per_1k']}` 处，仅加粗核心判断句或关键结论，禁止给普通名词乱加粗。
- **图文密度**：每千字约 `{stats['image_per_1k']}` 张配图/截图。
"""

    # 5. 总入口 Writing-DNA.md
    rep_lines = (
        "\n".join(f"  - 将 `{item['from']}` 替换为 `{item['to']}`" for item in replacements)
        if replacements
        else "  - （暂无记录，运行 learn_from_user_edits.py 后自动生成）"
    )
    rule_lines = "\n".join(f"  - {r}" for r in learned_rules)

    dna_md = f"""# 写作 DNA 总入口文档（Writing-DNA.md） · {stats['account']}

> - **账号名称**：`{stats['account']}`
> - **轨道类型**：`{stats['track']}` ({'外部标杆：仅借结构与节奏，严禁借人设与个人经历' if is_external else '自有公众号：全量继承人设、案例与手改进化规则'})
> - **样本规模**：{stats['article_count']} 篇（共 {stats['total_words']} 字） | **更新时间**：{now_str}

{track_banner}

## 1. L1 语言与标点硬约束（来自 `语言DNA.md`）
- **句长分布**：目标平均句长 `{stats['mean_sent_len']}` 字（标准差 `{stats['std_sent_len']}`）；≤15字短句占 `{stats['short_sent_ratio']}%`，≥50字长句占 `{stats['long_sent_ratio']}%`。
- **段落节奏**：平均每段 `{stats['mean_para_sents']}` 句（约 `{stats['mean_para_chars']}` 字），严禁写超长密不透风的机器段。
- **标点指纹（每千字）**：破折号 `{stats['em_dash_per_1k']}`、括号 `{stats['paren_per_1k']}`、分号 `{stats['semi_per_1k']}`、问号 `{stats['quest_per_1k']}`、感叹号 `{stats['exclam_per_1k']}`；引号使用 `{stats['quote_style']}`。
- **偏好过渡词**：`{', '.join(stats['top_connectors']) if stats['top_connectors'] else '少用显性连词，靠句意自然推进'}`
- **禁用噪声词**：`{', '.join(killed_words)}`

## 2. L2 结构与起承转合模板（来自 `文章结构模板.md`）
- **高频开头 Hook**：`{json.dumps(stats['hook_distribution'], ensure_ascii=False)}`
- **主体结构骨架**：`{json.dumps(stats['structure_distribution'], ensure_ascii=False)}`
- **开头铁律**：第一句直接给时间/场景锚点或反差判断，严禁清嗓子预告。
- **结尾铁律**：落在具体判断或唯一行动建议上，严禁“让我们拭目以待”式升华。

## 3. L3-L5 视角、素材与认知底线（来自 `写作视角与认知框架.md`）
- **L3-L5 作者观点仍需人工复核**：本脚本只会生成待填模板，不从句长/词频自动捏造核心立场。
- 辅助起草遇到需填入作者私人经历处，用 `> ✍️ 【人工微调锚点】` 留白供作者手改。

## 4. L6 排版与视觉规范（来自 `视觉风格指南.md`）
- 小标题平均 `{stats['mean_heading_len']}` 字；每千字加粗 `{stats['bold_per_1k']}` 处；全文列表不超过 1 处。

## 5. 人工手改进化规则（来自 `evolution_ledger.json`，最高优先级）
- **用户手改高频斩杀词**：`{', '.join(killed_words)}`
- **用户偏爱表达替换**：
{rep_lines}
- **用户手改沉淀的结构与节奏铁律**：
{rule_lines}
"""

    files_written = []
    output_dir = output_dir or profile_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    for fname, content in [
        ("语言DNA.md", l1_md),
        ("文章结构模板.md", l2_md),
        ("写作视角与认知框架.md", l35_md),
        ("视觉风格指南.md", l6_md),
        ("Writing-DNA.md", dna_md),
    ]:
        out_p = output_dir / fname
        out_p.write_text(content, encoding="utf-8")
        files_written.append(str(out_p))

    return files_written


def select_5_reference_articles(profile_dir: Path, target_type: str = "", platform_filter: str = "") -> List[Dict]:
    """按 writing-dna-skill Step 6.1 规则抽取 5 篇最接近的同体裁近期原文供写作前校准语感"""
    raw_dir = profile_dir / "raw"
    meta_dir = profile_dir / "_meta"
    candidates = []

    for md_file in sorted(raw_dir.glob("*.md"), reverse=True):
        fm, body = strip_frontmatter_and_code(md_file.read_text(encoding="utf-8"))
        if platform_filter and fm.get("platform", "wechat") != platform_filter:
            continue
        art_type = fm.get("article_type", "深度分析")
        meta_file = meta_dir / f"{md_file.stem}.json"
        if meta_file.exists():
            try:
                mdata = json.loads(meta_file.read_text(encoding="utf-8"))
                art_type = mdata.get("article_type", art_type)
            except Exception:
                pass
        candidates.append(
            {
                "file": md_file.name,
                "date": fm.get("date", ""),
                "title": fm.get("title", md_file.stem),
                "article_type": art_type,
                "opening_preview": body[:200].replace("\n", " "),
            }
        )

    if target_type:
        same_type = [c for c in candidates if c["article_type"] == target_type]
        others = [c for c in candidates if c["article_type"] != target_type]
        selected = (same_type + others)[:5]
    else:
        selected = candidates[:5]
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="六维写作 DNA 量化蒸馏器")
    parser.add_argument(
        "--profile-dir",
        type=Path,
        required=True,
        help="目标风格目录 (如 style_profiles/external_benchmarks/某博主)",
    )
    parser.add_argument(
        "--select-samples",
        type=str,
        default="",
        help="可选：指定体裁并抽取 5 篇近期原文用于写前语感校准",
    )
    parser.add_argument("--platform", choices=["wechat", "x", "xiaohongshu", "blog"], default="", help="可选：按发布平台过滤语料；避免跨平台 DNA 统计混合")
    args = parser.parse_args()

    if not args.profile_dir.exists():
        print(f"Error: 找不到风格目录 {args.profile_dir}", file=sys.stderr)
        sys.exit(1)

    stats = analyze_corpus_l1_l6(args.profile_dir, args.platform)
    written = write_distilled_files(args.profile_dir, stats, args.profile_dir / "platforms" / args.platform if args.platform else None)
    selected_5 = select_5_reference_articles(args.profile_dir, args.select_samples, args.platform)

    output = {
        "status": "distilled",
        "platform_filter": args.platform or "all",
        "account": stats["account"],
        "track": stats["track"],
        "metrics_summary": {
            "article_count": stats["article_count"],
            "total_words": stats["total_words"],
            "mean_sent_len": stats["mean_sent_len"],
            "std_sent_len": stats["std_sent_len"],
            "mean_para_chars": stats["mean_para_chars"],
            "em_dash_per_1k": stats["em_dash_per_1k"],
            "quest_per_1k": stats["quest_per_1k"],
        },
        "generated_files": written,
        "five_calibration_articles": selected_5,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
