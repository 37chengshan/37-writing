# Chinese Humanizer Writer v3 · Windows 三平台写作 Skill

基于用户提供的 v2 全栈包增量修复，支持**公众号长文 / X 短帖或线程 / 小红书笔记**。保留双轨风格 DNA、原文归档、人工改稿学习和 50 分参考审稿；新增平台独立路由、证据账本、离线发布前门禁、Windows 安装及自动化测试。

## 架构

```text
                          自有作者账号 DNA (self)
                               │
已获授权的资料 → 事实/版权账本 → 单一核心观点 ← 外部范例(external，技法参考)
                               │
                     平台独立内容编辑路由
                ┌──────────────┼──────────────┐
                ↓              ↓              ↓
             公众号长文        X 短帖/线程      小红书笔记
             叙事/悬念       观点/证据        搜索/前三行
                └──────────────┼──────────────┘
                               ↓
                 静态质量门禁 + 作者人工审定
                               ↓
                     手动发布 → 用户修改 Diff
```

## 1. Windows 安装（不需管理员权限）

在解压后的 `chinese-humanizer-writer` 根目录打开 PowerShell：

```powershell
# 先预演，不改你的文件
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target Both -Scope User -DryRun

# 安装到用户目录：Claude Code 与 Codex
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target Both -Scope User

# 只安装到当前项目（若不想全局生效）
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ClaudeCode -Scope Project -ProjectPath '.'

# 已有旧版：先备份旧安装再升级
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target Both -Scope User -Force
```

安装位置：Claude Code 为 `%USERPROFILE%\.claude\skills\chinese-humanizer-writer`；Codex 为 `%USERPROFILE%\.agents\skills\chinese-humanizer-writer`。只安装文本 Skill；不自动连接任何公众号、小红书或 X 账号。

`-Force` 会先把原安装文件夹移动为带时间戳的 `.backup-*` 后再安装；请保存个人 `style_profiles` 和草稿，不要长期放在易被替换的 Skill 安装目录内。推荐把语料放到独立工作目录，通过命令路径指向它。

## 2. Python 依赖与创建工作区

需要 Python 3.10+（已加入 PATH 或可使用 Windows `py -3`）。

```powershell
cd .\chinese-humanizer-writer
py -3 -m pip install -r requirements.txt
py -3 scripts/prepare_campaign.py --topic "历史人物财富与代价" --account "你的账号" --out ".\workspace\example01"
```

生成一个不会伪造素材的结构：`brief.json`、`evidence-ledger.json`、`source-notes.md`、三个平台各自的 `draft-*.md`。填入真实证据、明确读者和观点，再让 Agent 按 `SKILL.md` + 三平台指南分别创作。

## 3. 三平台写作命令示例

对本地已合法取得的素材归档：

```powershell
py -3 scripts/fetch_and_archive_articles.py --input ".\samples" --account "参考号" --track external --platform wechat --base-dir ".\style_profiles"
py -3 scripts/distill_style_dna.py --profile-dir ".\style_profiles\external_benchmarks\参考号" --platform wechat
```

检查稿件：

```powershell
py -3 scripts/platform_quality_gate.py --platform wechat --input ".\workspace\example01\draft-wechat.md" --evidence ".\workspace\example01\evidence-ledger.json" --json --strict
py -3 scripts/platform_quality_gate.py --platform x --input ".\workspace\example01\draft-x.md" --json --strict
py -3 scripts/platform_quality_gate.py --platform xiaohongshu --input ".\workspace\example01\draft-xiaohongshu.md" --json --strict
py -3 scripts/audit_chinese_ai_flavor.py ".\finished.md" --original ".\source-draft.md" --json --strict
```

学习作者手改偏好（只能写到自有轨）：

```powershell
py -3 scripts/learn_from_user_edits.py --draft ".\ai-draft.md" --final ".\user-final.md" --profile-dir ".\style_profiles\our_own_voice\我的号" --platform wechat
```

## 4. 测试

```powershell
py -3 -m compileall -q scripts
py -3 -m unittest discover -s tests -v
```

- `platform_quality_gate.py` 的 X 字数是**离线近似值**，不等同平台最终计数；`--x-limit` 可调，默认普通短帖 280。
- 小红书 20 字只作为短标题提示阈值，不是法律或永久官方规则。
- `audit_chinese_ai_flavor.py` 评分只用于机械套话/节奏提示；“缺少错误”不证明一篇文章事实真实。
- 不支持绕过登录/付费墙抓网页；本地归档器接收 HTML/MD/TXT，不负责真实账号抓取和发布。

## 5. 内容来源与迁移

原 v2 内容和四个脚本保留并维护；改动原因见 `docs/REVIEW-AND-MIGRATION.md`，参考仓库和 X 帖链接的验证边界见 `docs/SOURCES.md`。**先通过静态门禁，再人工核实与发布，最后把作者定稿反哺自有风格库。**
