#!/usr/bin/env python3
"""
Self-Evolving Writing Style Learner (Diff Analyzer between AI Draft & User Final Edit)
「AI 初稿 vs 用户手改终稿」Diff 进化学习引擎

融合 dongbeixiaohuo/writing-agent (edit-diff-learner) 与 writing-dna-skill 的迭代理念：
1. 对比 AI 辅助生成的初稿 (`--draft`) 与用户亲手修改定稿后的终稿 (`--final`)
2. 自动提取：
   - 被用户果断删掉的词句/套话 (`killed_phrases`) -> 晋升为自有公众号永久禁用词
   - 用户新增的高频个人表达 (`added_signature_expressions`)
   - 句级替换映射对 (`preferred_replacements`)
   - 句长、段落字数、标点密度的真实偏移量 (`metrics_delta`)
   - 开头与结尾的结构性手术特征 (`structural_rules_learned`)
3. 自动更新 `style_profiles/our_own_voice/<account>/evolution_ledger.json`
4. 将用户的终稿自动作为最新一手真迹归入 `raw/` 语料库，并重新触发 `distill_style_dna.py` 刷新 `Writing-DNA.md`

Usage:
    python3 learn_from_user_edits.py --draft ai_draft.md --final user_final.md --profile-dir style_profiles/our_own_voice/我的主号
"""

import argparse
import datetime
import hashlib
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 导入同目录下的归档与蒸馏模块
sys.path.insert(0, str(Path(__file__).parent))
import distill_style_dna
import fetch_and_archive_articles


CANDIDATE_CLICHES_AND_CONNECTORS = [
    "值得注意的是",
    "需要指出的是",
    "不难发现",
    "毋庸置疑",
    "不可否认",
    "显而易见",
    "与此同时",
    "综上所述",
    "总而言之",
    "一言以蔽之",
    "首先",
    "其次",
    "再者",
    "最后",
    "此外",
    "然而",
    "因此",
    "至关重要",
    "深入探讨",
    "全方位赋能",
    "底层逻辑",
    "顶层设计",
    "核心抓手",
    "全链路闭环",
    "相辅相成",
    "缺一不可",
    "让我们拭目以待",
    "未来可期",
    "进行了",
    "实现了",
    "完成了对",
    "起到了",
    "对于",
    "而言",
    "来说",
]


def strip_fm_and_anchors(text: str) -> str:
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    body = re.sub(r"```[\s\S]*?```", "", body)
    # 移除 AI 初稿中的人工留白锚点提示行，避免把占位提示误判为用户反感的正文
    body = re.sub(r"^>\s*✍️.*$", "", body, flags=re.MULTILINE)
    return body.strip()


def basic_metrics(body: str) -> Dict:
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
    paras = [
        re.sub(r"\s+", "", p)
        for p in re.split(r"\n\s*\n", body)
        if p.strip() and not p.strip().startswith("#")
    ]
    sents = [
        re.sub(r"\s+", "", s)
        for s in re.split(r"[。！？!?]+", "\n".join(lines))
        if len(re.sub(r"\s+", "", s)) >= 3
    ]
    total_chars = max(sum(len(l) for l in lines), 1)
    k = total_chars / 1000.0

    mean_sent = sum(len(s) for s in sents) / max(len(sents), 1)
    mean_para = sum(len(p) for p in paras) / max(len(paras), 1)

    return {
        "total_chars": total_chars,
        "para_count": len(paras),
        "sent_count": len(sents),
        "mean_sent_len": round(mean_sent, 1),
        "mean_para_chars": round(mean_para, 1),
        "em_dash_per_1k": round(len(re.findall(r"——|--", body)) / k, 2),
        "paren_per_1k": round(len(re.findall(r"[（(][^）)\n]{1,60}[）)]", body)) / k, 2),
        "quest_per_1k": round((body.count("？") + body.count("?")) / k, 2),
        "exclam_per_1k": round((body.count("！") + body.count("!")) / k, 2),
        "first_para": paras[0] if paras else "",
        "last_para": paras[-1] if paras else "",
    }


def extract_diff_insights(draft_body: str, final_body: str) -> Dict:
    d_metrics = basic_metrics(draft_body)
    f_metrics = basic_metrics(final_body)

    # 1. 检测被用户斩杀的套话/连接词
    killed_phrases = []
    for phrase in CANDIDATE_CLICHES_AND_CONNECTORS:
        d_cnt = draft_body.count(phrase)
        f_cnt = final_body.count(phrase)
        if d_cnt > f_cnt:
            killed_phrases.append(phrase)

    # 2. 句级 SequenceMatcher 比对，提取修改对与被删短语
    draft_sents = [
        s.strip()
        for s in re.split(r"(?<=[。！？!?\n])", draft_body)
        if len(s.strip()) >= 4
    ]
    final_sents = [
        s.strip()
        for s in re.split(r"(?<=[。！？!?\n])", final_body)
        if len(s.strip()) >= 4
    ]

    matcher = difflib.SequenceMatcher(None, draft_sents, final_sents)
    sentence_replacements = []
    deleted_sentences = []
    added_sentences = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            d_chunk = "".join(draft_sents[i1:i2]).strip()
            f_chunk = "".join(final_sents[j1:j2]).strip()
            if 4 <= len(d_chunk) <= 90 and 4 <= len(f_chunk) <= 90:
                sentence_replacements.append({"from": d_chunk, "to": f_chunk})
        elif tag == "delete":
            for s in draft_sents[i1:i2]:
                if len(s.strip()) >= 6:
                    deleted_sentences.append(s.strip())
        elif tag == "insert":
            for s in final_sents[j1:j2]:
                if len(s.strip()) >= 6:
                    added_sentences.append(s.strip())

    # 3. 提炼结构与节奏进化规则
    learned_rules = []
    para_diff = f_metrics["mean_para_chars"] - d_metrics["mean_para_chars"]
    if para_diff <= -15:
        learned_rules.append(
            f"用户偏好更短促的段落呼吸感：手改后平均段长从 {d_metrics['mean_para_chars']} 字压缩至 {f_metrics['mean_para_chars']} 字，起草时应主动拆短段落。"
        )
    elif para_diff >= 20:
        learned_rules.append(
            f"用户偏好更厚重的段落论证：手改后平均段长从 {d_metrics['mean_para_chars']} 字增加至 {f_metrics['mean_para_chars']} 字，起草时应减少碎段。"
        )

    sent_diff = f_metrics["mean_sent_len"] - d_metrics["mean_sent_len"]
    if sent_diff <= -3.5:
        learned_rules.append(
            f"用户偏好更利落的短句：手改后平均句长从 {d_metrics['mean_sent_len']} 字缩短至 {f_metrics['mean_sent_len']} 字，应多拆长定语与复合句。"
        )

    if d_metrics["em_dash_per_1k"] > f_metrics["em_dash_per_1k"] + 0.5:
        learned_rules.append("用户在手改中删减了破折号（——），起草时应改用逗号或句号连接。")

    if f_metrics["paren_per_1k"] > d_metrics["paren_per_1k"] + 0.5:
        learned_rules.append("用户喜欢在句中使用括号（（））插入补充说明或冷幽默吐槽。")

    if d_metrics["first_para"] != f_metrics["first_para"]:
        learned_rules.append(
            f"用户重写了开篇首段（手改后首段：「{f_metrics['first_para'][:45]}……」），起手需更直接切入具体场景或判断。"
        )

    if d_metrics["last_para"] != f_metrics["last_para"]:
        learned_rules.append(
            f"用户修改了结尾落点（手改后末段：「{f_metrics['last_para'][:45]}……」），避免使用套路化总结收尾。"
        )

    return {
        "draft_metrics": d_metrics,
        "final_metrics": f_metrics,
        "killed_phrases": killed_phrases,
        "sentence_replacements": sentence_replacements[:8],
        "deleted_sentences_sample": deleted_sentences[:5],
        "added_sentences_sample": added_sentences[:5],
        "learned_rules": learned_rules,
    }


def update_evolution_ledger(profile_dir: Path, insights: Dict, session_hash: str = "") -> Path:
    profile_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = profile_dir / "evolution_ledger.json"

    if ledger_path.exists():
        try:
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception:
            ledger = {}
    else:
        ledger = {}

    seen = ledger.get("processed_session_hashes", [])
    if session_hash and session_hash in seen:
        return ledger_path
    sessions = ledger.get("total_edit_sessions", 0) + 1
    existing_banned = set(ledger.get("hard_banned_phrases", []))
    candidates = dict(ledger.get("candidate_banned_phrases", {}))
    for phrase in set(insights["killed_phrases"]):
        candidates[phrase] = int(candidates.get(phrase, 0)) + 1
        if candidates[phrase] >= 3:
            existing_banned.add(phrase)

    existing_reps = ledger.get("preferred_replacements", [])
    for rep in insights["sentence_replacements"]:
        if rep not in existing_reps:
            existing_reps.append(rep)
    existing_reps = existing_reps[-15:]

    existing_rules = ledger.get("structural_rules_learned", [])
    for r in insights["learned_rules"]:
        if r not in existing_rules:
            existing_rules.append(r)
    existing_rules = existing_rules[-12:]

    f_m = insights["final_metrics"]
    updated_ledger = {
        "account": profile_dir.name,
        "track": "self",
        "total_edit_sessions": sessions,
        "last_updated": datetime.datetime.now().isoformat(timespec="seconds"),
        "hard_banned_phrases": sorted(list(existing_banned)),
        "candidate_banned_phrases": candidates,
        "processed_session_hashes": (seen + [session_hash])[-200:] if session_hash else seen,
        "learning_policy": "3独立修改会话晋升；明确用户偏好可人工确认，禁止一次删除直接永久封禁",
        "preferred_replacements": existing_reps,
        "metrics_target": {
            "target_mean_sentence_len": f_m["mean_sent_len"],
            "target_mean_para_chars": f_m["mean_para_chars"],
            "preferred_em_dash_per_1k": f_m["em_dash_per_1k"],
            "preferred_paren_per_1k": f_m["paren_per_1k"],
            "preferred_question_per_1k": f_m["quest_per_1k"],
        },
        "structural_rules_learned": existing_rules,
    }

    ledger_path.write_text(
        json.dumps(updated_ledger, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ledger_path


def main() -> None:
    parser = argparse.ArgumentParser(description="用户修改稿 Diff 持续学习进化引擎")
    parser.add_argument("--draft", type=Path, required=True, help="AI 辅助生成的初稿文件路径")
    parser.add_argument("--final", type=Path, required=True, help="用户亲手修改定稿后的终稿文件路径")
    parser.add_argument(
        "--profile-dir",
        type=Path,
        required=True,
        help="自有公众号风格目录 (如 style_profiles/our_own_voice/我的主号)",
    )
    parser.add_argument("--platform", choices=["wechat", "x", "xiaohongshu", "blog"], default="wechat")
    parser.add_argument(
        "--article-type",
        type=str,
        default="深度分析",
        help="本篇文章体裁分类",
    )
    args = parser.parse_args()

    if not args.draft.exists() or not args.final.exists():
        print("Error: 初稿或终稿文件不存在", file=sys.stderr)
        sys.exit(1)

    draft_body = strip_fm_and_anchors(args.draft.read_text(encoding="utf-8"))
    final_body = strip_fm_and_anchors(args.final.read_text(encoding="utf-8"))

    if args.profile_dir.parent.name != "our_own_voice":
        print("Error: 只能把人工手改学习写入 our_own_voice/<账号> 自有轨", file=sys.stderr)
        sys.exit(2)
    insights = extract_diff_insights(draft_body, final_body)
    session_hash = hashlib.sha256((draft_body + "\0" + final_body).encode("utf-8")).hexdigest()
    ledger_path = update_evolution_ledger(args.profile_dir, insights, session_hash)

    # 将用户的终稿自动归档入自有账号的 raw/ 语料库，并重跑蒸馏器刷新 Writing-DNA.md
    base_dir = args.profile_dir.parent.parent
    account_name = args.profile_dir.name
    archive_res = fetch_and_archive_articles.archive_inputs(
        input_path=args.final,
        base_dir=base_dir,
        account=account_name,
        track="self",
        platform=args.platform,
        article_type=args.article_type,
    )
    stats = distill_style_dna.analyze_corpus_l1_l6(args.profile_dir, args.platform)
    distilled_files = distill_style_dna.write_distilled_files(args.profile_dir, stats, args.profile_dir / "platforms" / args.platform)

    report = {
        "status": "evolved",
        "account": account_name,
        "track": "self",
        "platform": args.platform,
        "evolution_ledger_path": str(ledger_path),
        "diff_insights": insights,
        "archived_final_article": archive_res["imported_files"],
        "refreshed_dna_files": distilled_files,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
