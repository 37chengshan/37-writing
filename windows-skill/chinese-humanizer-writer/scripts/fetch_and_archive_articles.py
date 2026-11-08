#!/usr/bin/env python3
"""
WeChat Official Account & X (Twitter) Article Fetcher, Cleaner & Dual-Track Archiver
微信公众号 / X 文章清洗、双轨语料归档与索引重建器

融合以下开源项目的核心机制：
- AMarvelousJ/gongzhonghao-zhuaqu:
  1. 微信 HTML #js_content 与 content_noencode (\\xHH 十六进制反转义) 双通道提取
  2. og:title 长标题污染防护 (<=80字且无换行才采信，否则从正文首句提取)
  3. 排除 we-emoji 微信表情图片噪音，提取真实配图链接
  4. 标准 YAML frontmatter 与 mid+idx / status_id / 内容指纹无状态增量判重
  5. 自动按发布日期倒序非破坏性重建 `00-索引.md`
- larashero3-dotcom/writing-dna-skill:
  1. 自动建立 `raw/`、`_meta/`、`attachments/` 标准语料库目录
  2. 自动生成 11 字段 `_meta/<article>.json` 元数据文件
- 双轨物理隔离 (Dual-Track Isolation):
  强制通过 `--track external` (外部标杆公众号/X博主) 与 `--track self` (我们自己的公众号)
  将语料物理隔离到 `style_profiles/external_benchmarks/<account>/` 与 `style_profiles/our_own_voice/<account>/`

Usage:
    python3 fetch_and_archive_articles.py --input <file_or_dir> --account "半佛仙人" --track external --platform wechat
"""

import argparse
import datetime
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse


WECHAT_NOISE_PATTERNS = [
    r"点个?【?在看】?.*",
    r"喜欢(?:本文|这篇文章)的话.*?(?:分享|点赞|在看).*",
    r"关注(?:公众号|我们).*?回复.*?(?:领取|获取).*",
    r"长按(?:识别|扫描)(?:下方)?二维码.*",
    r"往期(?:精彩|推荐|回顾)[:：]?.*",
    r"本文(?:系|由).*?原创.*?转载.*",
]


def js_hex_unescape(raw_str: str) -> str:
    """解码微信 JS 变量 content_noencode 中的 \\xHH 十六进制转义序列与常见转义"""
    def _replace_hex(match: re.Match) -> str:
        return chr(int(match.group(1), 16))

    s = re.sub(r"\\x([0-9a-fA-F]{2})", _replace_hex, raw_str)
    s = (
        s.replace(r"\n", "\n")
        .replace(r"\r", "")
        .replace(r"\t", "\t")
        .replace(r"\"", '"')
        .replace(r"\'", "'")
        .replace(r"\\", "\\")
    )
    return html.unescape(s)


def extract_dedup_key(source_url: str, title: str, body: str) -> str:
    """提取无状态去重键：优先微信 mid+idx，次选 X status_id，兜底标题+前150字哈希"""
    if source_url:
        m_mid = re.search(r"[?&]mid=(\d+)", source_url)
        m_idx = re.search(r"[?&]idx=(\d+)", source_url)
        if m_mid and m_idx:
            return f"wx_mid_{m_mid.group(1)}_idx_{m_idx.group(1)}"
        m_status = re.search(r"status/(\d+)", source_url)
        if m_status:
            return f"x_status_{m_status.group(1)}"
    fingerprint_src = f"{title.strip()}::{body.strip()[:150]}"
    digest = hashlib.sha256(fingerprint_src.encode("utf-8")).hexdigest()[:16]
    return f"hash_{digest}"


def parse_wechat_or_generic_html(raw_html: str, default_account: str) -> Dict:
    """从微信公众号 HTML 或通用网页 HTML 中提取干净的标题、作者、日期、正文与图片列表"""
    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. 提取标题（防范文字消息 og:title 塞入整篇正文造成长标题污染）
    title = ""
    m_msg_title = re.search(
        r"var\s+msg_title\s*=\s*['\"]([^'\"]+)['\"]", raw_html
    )
    if m_msg_title:
        title = html.unescape(m_msg_title.group(1)).strip()
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            cand = og_title["content"].strip()
            if len(cand) <= 80 and "\n" not in cand:
                title = cand
    if not title and soup.title and soup.title.string:
        cand = soup.title.string.strip()
        if len(cand) <= 80 and "\n" not in cand:
            title = cand

    # 2. 提取公众号名与作者
    account = default_account
    m_nick = re.search(r"var\s+nickname\s*=\s*htmlDecode\(['\"]([^'\"]+)['\"]\)", raw_html)
    if m_nick and not account:
        account = html.unescape(m_nick.group(1)).strip()
    author_el = soup.find(id="js_author_name") or soup.find(class_="rich_media_meta_text")
    author = author_el.get_text(strip=True) if author_el else account

    # 3. 提取发布日期
    pub_date = "unknown"
    m_ct = re.search(r"var\s+ct\s*=\s*['\"]?(\d{10})['\"]?", raw_html)
    if m_ct:
        dt = datetime.datetime.fromtimestamp(int(m_ct.group(1)), tz=datetime.timezone(datetime.timedelta(hours=8)))
        pub_date = dt.strftime("%Y-%m-%d")
    else:
        m_date = re.search(r"(20\d{2}-\d{2}-\d{2})", raw_html)
        if m_date:
            pub_date = m_date.group(1)

    # 4. 提取原始 URL
    source_url = ""
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        source_url = og_url["content"].strip()

    # 5. 提取正文 DOM（优先 #js_content，兜底 content_noencode 十六进制解码，再兜底 <article>/<body>）
    content_node = soup.find(id="js_content")
    if not content_node:
        m_noenc = re.search(
            r"content_noencode\s*:\s*JsDecode\(['\"](.*?)['\"]\)",
            raw_html,
            flags=re.DOTALL,
        ) or re.search(
            r"content_noencode\s*:\s*['\"](.*?)['\"]\s*,",
            raw_html,
            flags=re.DOTALL,
        )
        if m_noenc:
            decoded_html = js_hex_unescape(m_noenc.group(1))
            content_node = BeautifulSoup(decoded_html, "html.parser")
    if not content_node:
        content_node = soup.find("article") or soup.body or soup

    # 6. 移除脚本和导航噪音；外链仅保存安全 HTTP(S) 目标（不执行脚本）
    for node in content_node.find_all(["script", "style", "noscript", "iframe"]):
        node.decompose()
    for link in content_node.find_all("a"):
        label = link.get_text(" ", strip=True)
        href = html.unescape((link.get("href") or "").strip())
        if label and urlparse(href).scheme in ("https", "http"):
            link.replace_with(f"[{label}]({href.replace(')', '%29')})")

    # 7. 提取真实配图（排除 we-emoji 微信表情包）
    images = []
    for img in content_node.find_all("img"):
        cls_list = img.get("class") or []
        if "we-emoji" in cls_list or "rich_pages_wxw-img" in cls_list and "emoji" in str(img):
            img.decompose()
            continue
        img_url = img.get("data-src") or img.get("src") or ""
        if img_url and urlparse(img_url).scheme in ("https", "http"):
            images.append(img_url)
            img.replace_with(f"\n\n![配图]({img_url.replace(chr(41), '%29')})\n\n")

    # 8. 结构化转为干净的 Markdown 段落
    for h_level in range(1, 7):
        for h in content_node.find_all(f"h{h_level}"):
            txt = h.get_text(" ", strip=True)
            if txt:
                h.replace_with(f"\n\n{'#' * h_level} {txt}\n\n")

    for bq in content_node.find_all("blockquote"):
        txt = bq.get_text(" ", strip=True)
        if txt:
            bq.replace_with(f"\n\n> {txt}\n\n")

    for li in content_node.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if txt:
            li.replace_with(f"\n- {txt}")

    for p in content_node.find_all(["p", "section"]):
        # 仅在叶子块节点或直接含文本处加换行
        if not p.find(["p", "section", "h1", "h2", "h3", "h4", "blockquote"]):
            txt = p.get_text("", strip=True)
            if txt:
                p.replace_with(f"\n\n{txt}\n\n")

    raw_text = content_node.get_text("\n")
    cleaned_body = clean_article_body(raw_text)

    if not title:
        first_line = next(
            (l.strip("# ").strip() for l in cleaned_body.splitlines() if len(l.strip()) >= 4),
            "未命名文章",
        )
        title = first_line[:40]

    return {
        "title": title,
        "author": author or account,
        "account": account,
        "date": pub_date,
        "source_url": source_url,
        "body": cleaned_body,
        "image_count": len(images),
    }


def clean_article_body(text: str) -> str:
    """清洗多余空行、移除文末微信固定引导噪音"""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
            continue
        # 检查是否命中微信尾部营销噪音
        if any(re.match(pat, s) for pat in WECHAT_NOISE_PATTERNS):
            continue
        lines.append(s)

    joined = "\n".join(lines)
    joined = re.sub(r"\n{3,}", "\n\n", joined).strip()
    return joined


def parse_markdown_or_text_file(path: Path, default_account: str) -> Dict:
    """解析已有的 Markdown 或纯文本文件（支持带或不带 YAML frontmatter）"""
    raw = path.read_text(encoding="utf-8")
    meta = {}
    body = raw

    m_fm = re.match(r"\A---\n(.*?)\n---\n([\s\S]*)", raw, flags=re.DOTALL)
    if m_fm:
        fm_text, body = m_fm.group(1), m_fm.group(2)
        for line in fm_text.splitlines():
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

    body = clean_article_body(body)
    title = meta.get("title", "")
    if not title:
        for line in body.splitlines():
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break
        if not title:
            title = path.stem

    date_str = meta.get("date", "")
    if not date_str:
        m_d = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
        date_str = m_d.group(1) if m_d else "unknown"

    return {
        "title": title,
        "author": meta.get("author", default_account),
        "account": meta.get("account", default_account),
        "date": date_str,
        "source_url": meta.get("source", ""),
        "body": body,
        "image_count": len(re.findall(r"!\[.*?\]\(.*?\)", body)),
    }


def infer_hook_and_structure(body: str) -> Tuple[str, str]:
    """自动启发式推断开头 Hook 类型与文章主体结构模式"""
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    first_para = paragraphs[0] if paragraphs else ""

    if "？" in first_para or "?" in first_para:
        hook_type = "问题式"
    elif re.search(r"\d+(?:\.\d+)?%|\d+万|\d+亿", first_para):
        hook_type = "数据反差式"
    elif re.search(r"昨天|上周|前几天|凌晨|刚才|20\d{2}年", first_para):
        hook_type = "时间锚点式"
    elif len(first_para) <= 45:
        hook_type = "观点暴击式"
    else:
        hook_type = "场景式"

    headings = re.findall(r"^#{1,3}\s+.*$", body, flags=re.MULTILINE)
    if len(headings) >= 3:
        structure = "总-分-总"
    elif body.count("？") >= 5:
        structure = "问题链驱动"
    else:
        structure = "单点剥笋推进"

    return hook_type, structure


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|\n\r\t]+', "_", name).strip(" ._")
    clean = clean[:60].rstrip(" .") or "article"
    # Windows 禁止使用设备名作为文件/目录名；兼容 CON.txt 等变体
    if clean.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)], *[f"LPT{i}" for i in range(1, 10)]}:
        clean = "_" + clean
    return clean


def rebuild_index(profile_dir: Path, account: str, track: str) -> Path:
    """扫描 raw/ 下所有文章，按发布日期倒序非破坏性重建 00-索引.md (源自 gongzhonghao-zhuaqu reindex.py)"""
    raw_dir = profile_dir / "raw"
    entries = []
    for md_file in sorted(raw_dir.glob("*.md")):
        parsed = parse_markdown_or_text_file(md_file, account)
        word_cnt = len(re.sub(r"\s+", "", parsed["body"]))
        entries.append(
            {
                "date": parsed["date"],
                "title": parsed["title"],
                "filename": md_file.name,
                "word_count": word_cnt,
            }
        )

    entries.sort(key=lambda x: (x["date"] != "unknown", x["date"], x["filename"]), reverse=True)
    track_label = "外部标杆公众号/博主 (仅借鉴结构与技法)" if track == "external" else "我们自己的公众号/主创语料库 (全量继承人设与进化账本)"

    lines = [
        f"# 📚 {account} · 语料库总索引 (00-索引)",
        "",
        f"- **所属轨道**：`{track}` ({track_label})",
        f"- **收录篇数**：{len(entries)} 篇",
        f"- **最近同步**：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 发布日期 | 文章双链标题 | 字数 |",
        "| :--- | :--- | :--- |",
    ]
    for e in entries:
        lines.append(f"| {e['date']} | [[raw/{e['filename']}|{e['title']}]] | {e['word_count']} 字 |")

    index_path = profile_dir / "00-索引.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def archive_inputs(
    input_path: Path,
    base_dir: Path,
    account: str,
    track: str,
    platform: str,
    article_type: str,
) -> Dict:
    sub_folder = "external_benchmarks" if track == "external" else "our_own_voice"
    profile_dir = base_dir / sub_folder / sanitize_filename(account)
    raw_dir = profile_dir / "raw"
    meta_dir = profile_dir / "_meta"
    attach_dir = profile_dir / "attachments"
    for d in (raw_dir, meta_dir, attach_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 读取已有 dedup_key 集合实现无状态判重
    existing_keys = set()
    for meta_file in meta_dir.glob("*.json"):
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            if data.get("dedup_key"):
                existing_keys.add(data["dedup_key"])
        except Exception:
            pass

    files_to_process: List[Path] = []
    if input_path.is_dir():
        for ext in ("*.html", "*.htm", "*.md", "*.txt"):
            files_to_process.extend(sorted(input_path.glob(ext)))
    else:
        files_to_process.append(input_path)

    imported, skipped = [], []
    for fpath in files_to_process:
        if fpath.suffix.lower() in (".html", ".htm"):
            raw_html = fpath.read_text(encoding="utf-8", errors="replace")
            info = parse_wechat_or_generic_html(raw_html, account)
        else:
            info = parse_markdown_or_text_file(fpath, account)

        dedup_key = extract_dedup_key(info["source_url"], info["title"], info["body"])
        if dedup_key in existing_keys:
            skipped.append(info["title"])
            continue

        existing_keys.add(dedup_key)
        word_count = len(re.sub(r"\s+", "", info["body"]))
        hook_type, structure_pattern = infer_hook_and_structure(info["body"])
        safe_title = sanitize_filename(info["title"])
        stem_name = f"{info['date']}_{article_type}_{safe_title}"

        md_out = raw_dir / f"{stem_name}.md"
        counter = 2
        while md_out.exists():
            md_out = raw_dir / f"{stem_name}_{counter}.md"
            counter += 1

        now_iso = datetime.datetime.now().isoformat(timespec="seconds")
        # JSON 字符串也是合法 YAML 双引号标量，能安全保留双引号/反斜线等字符。
        yaml_string = lambda value: json.dumps(str(value), ensure_ascii=False)
        fm_lines = [
            "---",
            f"title: {yaml_string(info['title'])}",
            f"date: {yaml_string(info['date'])}",
            f"author: {yaml_string(info['author'])}",
            f"account: {yaml_string(account)}",
            f"track: {yaml_string(track)}",
            f"platform: {yaml_string(platform)}",
            f"article_type: {yaml_string(article_type)}",
            f"source: {yaml_string(info['source_url'])}",
            f"dedup_key: {yaml_string(dedup_key)}",
            f"word_count: {word_count}",
            f"imported_at: {yaml_string(now_iso)}",
            "---",
            "",
            f"# {info['title']}",
            "",
            info["body"],
            "",
        ]
        md_out.write_text("\n".join(fm_lines), encoding="utf-8")

        meta_obj = {
            "title": info["title"],
            "date": info["date"],
            "author": info["author"],
            "account": account,
            "track": track,
            "platform": platform,
            "column": "",
            "article_type": article_type,
            "topic_tags": [],
            "hook_type": hook_type,
            "structure_pattern": structure_pattern,
            "source_types": ["自有定稿（事实来源待核）"] if track == "self" else ["外部公开资料（未自动核实）"],
            "word_count": word_count,
            "notable": f"开头采用{hook_type}，主体为{structure_pattern}",
            "source_url": info["source_url"],
            "dedup_key": dedup_key,
        }
        (meta_dir / f"{md_out.stem}.json").write_text(
            json.dumps(meta_obj, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        imported.append(str(md_out.name))

    index_path = rebuild_index(profile_dir, account, track)
    return {
        "account": account,
        "track": track,
        "profile_dir": str(profile_dir),
        "imported_count": len(imported),
        "imported_files": imported,
        "skipped_duplicates_count": len(skipped),
        "index_file": str(index_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="微信公众号 / X 文章清洗与双轨语料库归档器")
    parser.add_argument("--input", type=Path, required=True, help="输入的 HTML/Markdown/TXT 文件或目录")
    parser.add_argument("--account", type=str, required=True, help="公众号或 X 账号名称")
    parser.add_argument(
        "--track",
        type=str,
        choices=["external", "self"],
        required=True,
        help="双轨隔离：external (外部标杆账号) | self (我们自己的公众号)",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="wechat",
        choices=["wechat", "x", "blog", "xiaohongshu"],
        help="来源平台",
    )
    parser.add_argument(
        "--article-type",
        type=str,
        default="深度分析",
        help="内容体裁 (深度分析|短评|教程攻略|访谈|实测)",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("style_profiles"),
        help="风格库根目录 (默认: ./style_profiles)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: 找不到输入路径 {args.input}", file=sys.stderr)
        sys.exit(1)

    res = archive_inputs(
        args.input,
        args.base_dir,
        args.account,
        args.track,
        args.platform,
        args.article_type,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
