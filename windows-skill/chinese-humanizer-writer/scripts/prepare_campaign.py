#!/usr/bin/env python3
"""Create a minimal, editable tri-platform content workspace; never invent copy."""
from __future__ import annotations
import argparse
import datetime
import json
import sys
from pathlib import Path

PLATFORMS = ("wechat", "x", "xiaohongshu")
TEMPLATES = {
 "wechat": "---\ntitle: \"【待拟公众号标题】\"\n---\n\n【待写：先放悬念或具体反常事实，再用一条可核验的故事主线推进。】\n",
 "x": "【待写：一个明确观点 + 一条具体证据或观察】\n\n<!-- POST -->\n\n【待写：线程第2条，不复述第1条】\n",
 "xiaohongshu": "---\ntitle: \"【待拟小红书标题】\"\n---\n\n【待写：前三行明确人群、处境、收获】\n\n【待写：步骤/体验/清单与适用边界】\n\n#相关搜索词\n",
}


def prepare(out: Path, topic: str, account: str, platforms: list[str], overwrite=False) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    brief = {
      "topic": topic,
      "account": account,
      "created_date": datetime.date.today().isoformat(),
      "status": "draft",
      "target_platforms": platforms,
      "core_thesis": "【待填：读者看完能复述的一句话】",
      "target_reader": "【待填：画像与实际处境】",
      "editorial_angle": "【待填：信息增量/反直觉切口】",
      "storyline": "【待填：事件→悬念→反转→代价→落点】",
      "author_voice": "【待填：自有账号DNA路径，禁止冒充外部作者】",
      "copyright_permissions": "【待填：有权使用的素材范围与授权情况】",
      "human_approval_required": True,
    }
    files = {"brief.json": json.dumps(brief, ensure_ascii=False, indent=2)+"\n",
             "evidence-ledger.json": json.dumps({"claims": []}, ensure_ascii=False, indent=2)+"\n",
             "source-notes.md": "# 素材与来源备忘\n\n- 【待填】来源URL、作者、日期、已核实的对应事实\n- 【待填】反证/争议与删去的夸张推断\n"}
    for platform in platforms:
        files[f"draft-{platform}.md"] = TEMPLATES[platform]
    written = []
    for name, content in files.items():
        path = out / name
        if path.exists() and not overwrite:
            raise FileExistsError(f"文件已存在，禁止覆盖：{path}；如确需覆盖请加 --force")
    for name, content in files.items():
        path = out / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    ap=argparse.ArgumentParser(description="三平台编辑项目骨架初始化（不生成虚构正文）")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--account", required=True)
    ap.add_argument("--platforms", nargs="+", choices=PLATFORMS, default=list(PLATFORMS))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--force", action="store_true")
    args=ap.parse_args()
    try:
        files=prepare(args.out,args.topic,args.account,list(dict.fromkeys(args.platforms)),args.force)
    except (OSError,ValueError) as exc:
        print(exc,file=sys.stderr);sys.exit(1)
    print(json.dumps({"created":[str(p) for p in files]},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
