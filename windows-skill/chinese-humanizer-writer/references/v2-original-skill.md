---
name: chinese-humanizer-writer
description: 中文全栈去 AI 味写作、公众号/X 文章拉取、双轨风格 DNA 蒸馏（严格隔离外部标杆与自有公众号）与自我进化写作系统。当用户要求：(1) 抓取/拉取微信公众号或 X(Twitter) 文章并归档；(2) 蒸馏外部标杆博主或自己公众号的写作风格 DNA；(3) 指定某种已蒸馏风格辅助完成初稿（保留人审空间）；(4) 根据用户手改后的终稿比对 Diff 持续学习进化个人文风；(5) 对中文文稿去 AI 味、说人话、降 AI 率或进行 50 分制多维审查时，必须启用此技能。
---

# Chinese Humanizer Writer (Full-Stack Style Distillation & Self-Evolving System)

集“公众号/X 语料拉取归档 -> 双轨写作 DNA 蒸馏（外部标杆 vs 自有账号物理隔离） -> 选定风格辅助完稿 -> 用户手改 Diff 持续学习进化 -> 36 点去 AI 味与 50 分制审查”于一体的中文全栈写作系统。

本技能深度整合了 13 个高分开源项目的核心架构：
- **拉取、情报与公众号全栈工作流**：[AMarvelousJ/gongzhonghao-zhuaqu](https://github.com/AMarvelousJ/gongzhonghao-zhuaqu)（微信公众号清洗、YAML frontmatter 规范、无状态 `mid+idx` 判重与 `00-索引.md` 重建）、[SpaceZephyr/creator-buddy](https://github.com/SpaceZephyr/creator-buddy)（跨平台选题探测、`gzh-longform-writer` 六种写法路由、16 种爆款标题法与微信排版）、[@Vinkyu567/twitter-clipper-vink](https://github.com/Vink567/twitter-clipper-vink)（X 长文原汁原味剪藏）。
- **六层写作 DNA 蒸馏与认知提取**：[larashero3-dotcom/writing-dna-skill](https://github.com/larashero3-dotcom/writing-dna-skill)（L1-L6 六维蒸馏、5 份分层模板 + 5 篇同体裁原文语感校准、[`lieflat-less-ai-tone`](https://github.com/larashero3-dotcom/lieflat-less-ai-tone) 520 万字配对实测规则）、[alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)（心智模型三重验证与 6 维句式指纹）、[dongbeixiaohuo/writing-agent](https://github.com/dongbeixiaohuo/writing-agent)（伤疤素材、证据账本与 `edit-diff-learner` 初终稿差异自学习）。
- **去 AI 味、说人话与多维审查门禁**：[blader/humanizer](https://github.com/blader/humanizer)、[op7418/Humanizer-zh](https://github.com/op7418/humanizer-zh)、[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)、[MrGeDiao/shuorenhua](https://github.com/MrGeDiao/shuorenhua)、[Leonxlnx/taste-skill](https://github.com/leonxlnx/taste-skill)、[hylarucoder/ai-flavor-remover](https://github.com/hylarucoder/ai-flavor-remover)、[Hello-SimpleAI/chatgpt-comparison-detection](https://github.com/hello-simpleai/chatgpt-comparison-detection)（HC3 语料）与 [OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL](https://github.com/oubigfa/de-ai-prompt-enhancer-writer-booster-skill)。

## When to Use

- **拉取与入库**：用户提供微信公众号链接/HTML/文本或 X(Twitter) 推文，要求抓取清洗并归入风格语料库
- **双轨风格蒸馏**：用户要求分析、提炼某个外部标杆公众号/X 博主或自己公众号的写作风格，生成可复用的 `Writing-DNA.md`
- **选风格辅助完稿**：用户给出选题、零散素材或半截草稿，指定用某套已蒸馏风格（或融合外部技法 + 自有底色）帮其完成初稿，供其后续手动定稿
- **手改 Diff 进化学习**：用户把修改定稿后的文章发回（或提供 `AI初稿 vs 人工终稿`），要求技能吸收其修改习惯、更新自有公众号风格 DNA
- **去 AI 味与审稿**：用户要求消除文章机器味、说人话、降 AI 率或执行 50 分制多维质量审查

## 核心铁律一：外部标杆 vs 自有公众号「双轨物理隔离」（Dual-Track Isolation）

蒸馏和调用风格时，必须严格区分**别人的号（External Benchmarks）**与**我们自己的号（Our Own Voice）**，严禁跨轨污染（详见 `references/wechat-x-fetching-and-distillation.md`）：

| 隔离维度 | 外部标杆库 (`style_profiles/external_benchmarks/<账号名>/`) | 自有公众号库 (`style_profiles/our_own_voice/<账号名>/`) |
| :--- | :--- | :--- |
| **收录对象** | 想要学习借鉴的外部优秀微信公众号、X 博主、行业专栏 | 用户本人或团队自己运营的微信公众号、个人专栏与手改定稿库 |
| **允许提取与借用的层** | 仅允许借用 **L1 句法节奏/标点生态**、**L2 文章结构骨架**、**L3 破题切入方式**、**L6 排版与配图节奏** | 完整继承 **L1-L6 全维度** + **真实个人经历/业务案例库** + **核心立场库** + **手改进化账本 (`evolution_ledger.json`)** |
| **绝对禁止借用的红线** | **严禁借用外部作者的第一人称亲身经历、具体客户案例、专有口头禅自称（如别人自称“老王”）、人设背景与具体业务数据**（防止写成抄袭洗稿或精神分裂的冒牌货） | 严禁把外部标杆的虚构或他人经历写入自有账号；自有账号的每一次人工定稿都会反向覆盖更新本库规则 |
| **混合调用优先级** | 当用户说“用外部博主 X 的结构帮我写一篇我们公众号的文章”时：**自有账号的底色、人设、禁用词与进化账本（最高优） > 外部博主 X 的 L2 结构骨架与节奏（次优） > 通用去 AI 味规则（兜底）** | 当自有账号的 `Writing-DNA.md`（例如用户本人就喜欢用短碎句或特定标点）与通用去 AI 味规则冲突时，**无条件服从自有账号 DNA**（[`lieflat-less-ai-tone`](https://github.com/larashero3-dotcom/lieflat-less-ai-tone) 风格优先铁律） |

## 核心铁律二：四级事实与结构保护优先级（零幻觉红线）

1. **事实账本与确定性守恒**：不编造原文或用户未提供的数字、日期、姓名、引文或“凉咖啡雨夜/我有个朋友”等假故事；严格锁死情态词（`可能`不改`必然`、`计划`不改`已完成`、`超过`不改`等于`）；对“专家认为”等无源引用保留其归属局限，绝不洗白成裸事实。
2. **受保护片段（Protected Spans）冻结**：代码块、行内代码、命令、路径、URL、YAML front matter、表格数据与 Markdown 标题层级默认逐字保留。
3. **自有 DNA 与选定风格优先**：优先对齐目标风格档案的句长、段落密度与结构模板。
4. **清除统计均值痕迹**：保留的每一句话必须提供增量信息；未命中具体病灶的通顺句子原样保留，绝不为了展示工作量而强行换词。

## 五大核心工作流（Core Workflows）

### Workflow 1: 公众号 / X 文章拉取、清洗与双轨归档

当用户提供微信公众号链接、网页 HTML、复制文本或 X 推文时（详见 `references/wechat-x-fetching-and-distillation.md`）：

1. **获取与解析内容**：
   - 若有网络浏览工具（`google:browse` / `google:search`），先读取目标 URL 提取标题、作者、发布日期与完整正文（遵循 [@Vinkyu567/twitter-clipper-vink](https://github.com/Vink567/twitter-clipper-vink) 铁律：100% 提取原文正文，严禁抓取时把原文缩写成 AI 摘要）。
   - 若为本地 HTML、URL 列表或粘贴文本，调用归档脚本完成微信 `#js_content` / `content_noencode` 十六进制反转义清洗、去尾部二维码/抓手噪音、生成标准 YAML frontmatter（含 `mid+idx` 去重键与 `track: external | self` 标记）并更新 `00-索引.md`（源自 [AMarvelousJ/gongzhonghao-zhuaqu](https://github.com/AMarvelousJ/gongzhonghao-zhuaqu)）：

   ```bash
   python3 skills/chinese-humanizer-writer/scripts/fetch_and_archive_articles.py \
     --input <html_or_md_or_dir> \
     --account "<账号名称>" \
     --track <external|self> \
     --platform <wechat|x> \
     --article-type <深度分析|短评|教程攻略|访谈|实测>
   ```

### Workflow 2: 六维写作 DNA 深度蒸馏与建档

当语料库积累了样本文章（快速建档 3-5 篇，完整建档建议 ≥20 篇，源自 [larashero3-dotcom/writing-dna-skill](https://github.com/larashero3-dotcom/writing-dna-skill) 与 [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)）：

1. **运行 L1 量化脚本分析**：
   调用蒸馏脚本自动计算句长分布（均值、标准差、≤15 字短句占比、≥50 字长句占比）、段落句数与字数（公众号手机屏单段常 ≤90 字）、标点指纹（破折号 vs 括号比、分号、引号、感叹号）、高频动词/名词与连接词习惯，并初始化目录骨架：

   ```bash
   python3 skills/chinese-humanizer-writer/scripts/distill_style_dna.py \
     --profile-dir style_profiles/<external_benchmarks|our_own_voice>/<账号名称>
   ```

2. **完成 L2-L6 深度阅读归纳并生成 5 份分层文档**：
   - `语言DNA.md`（L1）：高频签名词、禁用噪声副词、句长与标点硬约束。
   - `文章结构模板.md`（L2）：按体裁提炼 `[开头 Hook 类型+字数] -> [第一转折点] -> [正文推进骨架] -> [收尾方式]`。
   - `写作视角与认知框架.md`（L3-L5）：选题切入时机、一手/截图素材策略、3-5 条跨选题非显而易见的核心判断（若为 `external` 轨，显式标注“仅借鉴切入视角，严禁借用其个人经历与专有案例”）。
   - `视觉风格指南.md`（L6）：图文比、6 类配图功能、加粗密度、短段落呼吸节奏。
   - `Writing-DNA.md`（总入口，严格控制在 4000 字以内）：汇总可直接加载的规则集。

### Workflow 3: 选定风格辅助起草完稿（Co-Drafting for User Final Polish）

当用户要求“用 X 风格帮我写/完成这篇稿子，我最后自己改”时（融合 [larashero3-dotcom/writing-dna-skill](https://github.com/larashero3-dotcom/writing-dna-skill) 与 [SpaceZephyr/creator-buddy](https://github.com/SpaceZephyr/creator-buddy) `gzh-longform-writer`）：

1. **强制预读与 5 篇原文语感校准（严禁凭印象下笔）**：
   - 完整读取目标风格目录下的全部 5 份蒸馏文档；若同时存在 `our_own_voice` 自有账号档案与 `external_benchmarks` 目标风格档案，**必须同时加载自有账号的 `evolution_ledger.json`（历史手改偏好）与人设边界**。
   - 从目标风格的 `raw/` 中筛选 **5 篇同体裁、近期发布的原文**通读，先用 3-5 句话向用户（或在思考链中）总结这 5 篇原文的微观呼吸感（怎么起手、段间怎么跳接、何时突然插短句），绝不照搬原文的事实内容。
2. **六种起草路由诊断（源自 `gzh-longform-writer`）**：
   - 根据用户手头材料自动选择：**① 访谈式**（只有念头 -> 先追问 3-5 个具体细节）、**② 大纲式**（先给带字数配额和“反面/边界”章节的大纲）、**③ 续写式**（顺着用户半截草稿往下接）、**④ 素材整合式**（将零散资料压成唯一主线）、**⑤ 破题式**（提供 5 个反直觉切入角度）、**⑥ 定点重写式**。
3. **留白式辅助完稿（专为人工定稿设计）**：
   - 严格按目标风格的句长、段长（如公众号单段 ≤90 字、首段独立成立）与结构骨架完成高质量初稿。
   - **绝不替用户捏造个人经历**：遇到需要填入个人真实故事、内部数据或主观定调的位置，使用显式人工锚点 `【待你补充个人实历/数据：此处建议填入 1 个你在 XX 场景下的具体踩坑细节，约 80 字】` 留白，方便用户最后顺畅接手修改。
   - 同步附上基于 `baokuan-title-generator` 16 种方法生成的 **Top 5 候选标题**（综合首选、稳健版、传播版、搜索版、实验版）。
   - 将本次生成的初稿保存至工作区（如 `drafts/YYYY-MM-DD_<标题>_ai_draft.md`），以便后续与用户手改终稿做 Diff 学习。

### Workflow 4: 用户手改终稿 Diff 持续学习与风格进化（Self-Evolving Loop）

当用户自己改完稿子，把最终定稿发回（或说“这是我改完的终稿，学习一下我的修改”）时（详见 `references/self-evolving-diff-learning.md`，源自 [dongbeixiaohuo/writing-agent](https://github.com/dongbeixiaohuo/writing-agent) `edit-diff-learner`）：

1. **运行初终稿 Diff 进化脚本**：
   调用 `learn_from_user_edits.py` 对比 `ai_draft.md` 与 `user_final.md`：

   ```bash
   python3 skills/chinese-humanizer-writer/scripts/learn_from_user_edits.py \
     --draft <ai_draft.md> \
     --final <user_final.md> \
     --profile-dir style_profiles/our_own_voice/<自有账号名称>
   ```

2. **四维差异归因与规则固化**：
   脚本与 Agent 协同分析用户到底改了什么，并自动写入 `our_own_voice/<账号>/evolution_ledger.json` 与 `Writing-DNA.md` 的「人工手改进化规则（Learned User Preferences）」章节：
   - **词汇黑名单进化（Lexical Kills）**：被用户高频删掉或替换的词 -> 自动加入该账号的 `banned_words`（下次起草永不再用）与 `preferred_replacements`（用户偏爱的地道替换词）。
   - **句法与节奏校准（Rhythm & Pacing Delta）**：统计用户手改后的句长变化、段落拆分/合并习惯、标点增删（例如用户把所有分号都改成了句号，或把 120 字的段拆成了两段）。
   - **开头与收尾审美（Hook & Closer Taste）**：记录用户如何砍掉 AI 的铺垫开头、如何改写结尾。
   - **同时将用户的 `user_final.md` 自动归入 `our_own_voice/<账号>/raw/` 语料库**，作为最新鲜的一手真迹样本（权重最高）。

### Workflow 5: 36 点去 AI 味精修与 50 分制多维审查门禁

无论是直接润色文稿，还是在 Workflow 3 交付初稿前，均须执行多维去味审查（详见 `references/ai-tells-31-checkpoints.md` 与 `references/audit-rubric-and-hc3.md`）：

1. **扫描 A-G 七大类 36 个检查点 + `lieflat` 实测强信号**：
   重点清除翻案腔二元对比（`不是 X，而是 Y`，实测 AI 最强信号）、结论提示冒号（`一句话总结：`、`核心在于：`）、起跑清嗓词（`说白了`、`值得注意的是`、`随着……的发展`）、4 类特定翻译腔（>15 字长前置定语、`当……时`、`对于……来说`、段首机械连接词）、同构三连排比、段内同义词躲避轮换、以及连续 ≥6 段紧扣承接链。
2. **遵守 `lieflat-less-ai-tone` X 级免改清单（防过度删改）**：
   保留正文中自然的真问题/设问（人类使用率是 AI 的 17 倍）、保留恰当的独立比喻段、保留有实质信息的序数词小标题与“这意味着”正常推导，绝不为了制造参差而故意把通顺句子改碎。
3. **运行静态审查脚本与 50 分制门禁**：

   ```bash
   python3 skills/chinese-humanizer-writer/scripts/audit_chinese_ai_flavor.py <target.md> --original <orig.md>
   ```

   按直接性、节奏感、信任度、真实感、信息密度五维打分，总分 **<40/50** 必须返工重修后再交付。

## 参考资料、模板与脚本导航（References, Templates & Scripts）

- `references/wechat-x-fetching-and-distillation.md`：公众号/X 拉取清洗、双轨目录隔离（外部标杆 vs 自有账号）、L1-L6 六维蒸馏与 5 篇原文语感校准完整规范。
- `references/self-evolving-diff-learning.md`：选定风格辅助起草（6 种写法路由、人工留白锚点、16 种爆款标题法）与“AI 初稿 vs 用户手改稿” Diff 持续进化机制详解。
- `references/ai-tells-31-checkpoints.md`：36 个中文 AI 写作痕迹检查点、保留边界及 `lieflat-less-ai-tone` X 级永不改清单。
- `references/style-dna-and-scenes.md`：反统计均值审美、6 维句式指纹、厚段长句链、隐性过渡词库与 5 大场景护栏。
- `references/audit-rubric-and-hc3.md`：12 项清零清单、50 分制五维评分量表、HC3 语言学基准与事实账本双向核对表。
- `templates/`：包含 `Writing-DNA.template.md`、`language-dna.template.md`、`structure-patterns.template.md`、`cognitive-framework.template.md`、`visual-style-guide.template.md` 与 `article-meta.schema.json`。
- `scripts/fetch_and_archive_articles.py`：微信公众号 / X 文章清洗、YAML 归档与 `00-索引.md` 生成器。
- `scripts/distill_style_dna.py`：L1 量化句式/词频/标点指纹统计与双轨风格档案初始化脚本。
- `scripts/learn_from_user_edits.py`：AI 初稿 vs 用户手改终稿 Diff 对比、删改偏好提取与 `evolution_ledger.json` 自进化更新脚本。
- `scripts/audit_chinese_ai_flavor.py`：36 点去 AI 味静态检测、50 分制打分与原稿事实/代码块守恒校验脚本。

## Gotchas

- **绝不混淆“别人的故事”和“自己的嘴”**：用外部公众号的 `Writing-DNA.md` 辅助写稿时，只借它的骨架、节奏和切入技法，绝不能把外部作者的公司、朋友、经历或专属人设写进我们的稿子里。
- **自有 DNA 与进化账本永远高于通用规则**：一旦 `evolution_ledger.json` 记录了用户在手改时明确偏爱的表达或标点，哪怕它触发了通用去 AI 味提示，也无条件以用户的个人习惯为准。
