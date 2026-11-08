# 微信公众号与 X 文章拉取、清洗及双轨风格 DNA 蒸馏规范

本指南深度整合了 [AMarvelousJ/gongzhonghao-zhuaqu](https://github.com/AMarvelousJ/gongzhonghao-zhuaqu)、[SpaceZephyr/creator-buddy](https://github.com/SpaceZephyr/creator-buddy)、[larashero3-dotcom/writing-dna-skill](https://github.com/larashero3-dotcom/writing-dna-skill)、[alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill) 与 [@Vinkyu567/twitter-clipper-vink](https://github.com/Vink567/twitter-clipper-vink) 的工程规范，用于指导 Agent 拉取微信公众号或 X(Twitter) 文章，并在**严格区分「外部标杆账号」与「我们自己的公众号」**的前提下提炼可复用的写作 DNA。

---

## 一、 外部标杆 vs 自有公众号「双轨物理隔离」架构（Dual-Track Isolation）

多账号内容创作中最致命的错误是“风格与人设串味”——把别人公众号里的个人经历、公司背景、自称口癖当成自己的写进稿子，或者把几个不同风格的外部博主混在一个文件夹里导致蒸馏出四不像的统计均值。

### 1. 标准物理目录结构
所有拉取的语料与蒸馏产物必须按 `external_benchmarks`（别人的号）与 `our_own_voice`（我们自己的号）分轨存储：

```text
style_profiles/
├── external_benchmarks/                 # 【外部标杆轨】别人的公众号 / X 博主（可建多个）
│   └── <外部账号名，如：半佛仙人_或_Khazix>/
│       ├── 00-索引.md                   # 按日期倒序的文章双链总索引
│       ├── raw/                         # 清洗后的完整原文（YYYY-MM-DD_体裁_标题.md）
│       ├── _meta/                       # 每篇文章的 11 字段 JSON 元数据标注
│       ├── attachments/                 # 本地化保存的配图/截图资产
│       ├── 语言DNA.md                   # L1 表层语言统计与特征
│       ├── 文章结构模板.md              # L2 分体裁文章骨架模板
│       ├── 写作视角与认知框架.md        # L3-L5 选题切入与素材策略（含跨轨借用警告）
│       ├── 视觉风格指南.md              # L6 排版、段落行数与配图协作规则
│       └── Writing-DNA.md               # ≤4000 字总入口规则集（标明 track: external）
│
└── our_own_voice/                       # 【自有主创轨】我们自己的公众号 / 个人主账号
    └── <自有账号名，如：我的主号>/
        ├── 00-索引.md                   # 自有已发表/已定稿文章总索引
        ├── raw/                         # 我们自己写的历史文章 + 每次人工手改定稿后的终稿
        ├── _meta/                       # 元数据标注
        ├── evolution_ledger.json        # 【核心】从“AI初稿 vs 用户手改终稿”自动学习的进化账本
        ├── 语言DNA.md                   # L1 自有语言习惯与专属禁用词表
        ├── 文章结构模板.md              # L2 自有常用结构骨架
        ├── 写作视角与认知框架.md        # L3-L5 自有核心立场、真实案例库与人设边界
        ├── 视觉风格指南.md              # L6 自有公众号排版与配图规范
        └── Writing-DNA.md               # 自有账号最高优先级总入口（含最新手改进化规则）
```

### 2. 双轨提取与调用的硬性边界

| 维度 | `external_benchmarks`（外部标杆账号） | `our_own_voice`（我们自己的账号） |
| :--- | :--- | :--- |
| **蒸馏目标** | 拆解他为什么写得吸引人：怎么起标题、怎么写前 200 字 Hook、怎么搭段落骨架、长短句怎么交替、怎么用截图佐证 | 沉淀我们自己的表达基因、真实经历资产、核心判断底线与每一次审稿手改偏好 |
| **写作调用权限** | **只借“壳”与“术”，绝不借“肉”与“魂”**：只允许调用其 L1 句长/节奏、L2 结构模板、L3 破题角度、L6 段落排版；**严禁复制其专有自称、个人故事、具体客户案例与独创黑话口头禅** | **全量调用**：人设、语气、历史观点、真实伤疤案例库、禁用词表与 `evolution_ledger.json` 全部生效 |
| **混合模式（借壳上市）** | 当用户指令为“用外部标杆 A 的风格/结构，写一篇发在我们自己公众号上的文章”时：<br>1. **结构与节奏层**：加载外部标杆 A 的 `文章结构模板.md` 与 `语言DNA.md` 的句长/段落呼吸感；<br>2. **人设、词汇禁忌与底色层**：强制加载 `our_own_voice` 的 `evolution_ledger.json` 与 `写作视角与认知框架.md`，自动过滤外部标杆 A 中不符合我们人设的口癖。 | 自有账号的 `evolution_ledger.json` 拥有最高否决权：凡是用户手改历史中删掉过的句式或词汇，即使外部标杆爱用，也一律拦截。 |

---

## 二、 微信公众号与 X(Twitter) 文章拉取与清洗规范

融合 [AMarvelousJ/gongzhonghao-zhuaqu](https://github.com/AMarvelousJ/gongzhonghao-zhuaqu)、[SpaceZephyr/creator-buddy](https://github.com/SpaceZephyr/creator-buddy) 与 [@Vinkyu567/twitter-clipper-vink](https://github.com/Vink567/twitter-clipper-vink) 的实战标准：

### 1. 获取渠道与反爬/空壳处理
- **在线单篇/多篇拉取**：当用户给出 `mp.weixin.qq.com/s/...` 或 `x.com/.../status/...` 链接时，优先调用环境中的浏览工具读取全文；若在本地终端抓取微信页面，请求头必须使用 PC 微信 User-Agent 并强制设置 `r.encoding = "utf-8"`（防止 GBK 乱码）。
- **微信特殊页面兜底（源自 `gongzhonghao-zhuaqu`）**：
  - 标准图文提取 `#js_content` 节点内容；
  - 若无 `#js_content`（如微信纯文字消息或特殊模板），从页面脚本的 `content_noencode:` 变量中提取，并完整解码 `\xHH` 十六进制转义序列（`\x3c` -> `<`）；
  - 提取标题时优先读 `var msg_title`，若读 `og:title` 必须校验**长度 ≤80 字且不含换行符**，否则从正文首句提炼标题，防止将整段文字消息误作超长文件名；
  - 提取图片时优先读取 `<img data-src="...">`（过滤掉 `class="we-emoji"` 微信表情包与头像/封面噪点），下载图片时携带 `Referer: https://mp.weixin.qq.com/`。
- **原汁原味剪藏铁律（源自 `twitter-clipper-vink`）**：
  - 拉取入库阶段的目标是 **100% 保真还原作者原文正文與结构**，严禁在 `raw/` 原文文件中把文章缩写成 AI 摘要，也严禁在正文里插入 `## AI 总结`、`## 抓取日志` 等机器外壳。
  - 自动剥离微信公众号文末的固定推广尾巴（如“点个在看”、“关注公众号回复 XXX 领取”、“往期推荐阅读”等与正文无关的运营组件），避免运营套话污染 L1 词频统计。

### 2. 标准 YAML Frontmatter 与无状态去重
每篇归入 `raw/` 的文章顶部必须包含如下标准 YAML frontmatter（通过 `scripts/fetch_and_archive_articles.py` 自动生成）：

```yaml
---
title: "文章标题"
date: "2026-11-07"
author: "作者名"
account: "公众号或X账号名"
track: "external"          # external (外部标杆) | self (自有账号)
platform: "wechat"         # wechat | x | blog
article_type: "深度分析"    # 深度分析 | 短评 | 教程攻略 | 访谈 | 实测
source: "https://mp.weixin.qq.com/s?__biz=...&mid=...&idx=..."
dedup_key: "mid_224748_idx_1"
word_count: 2850
imported_at: "2026-11-07T20:00:00"
---
```

- **无状态增量判重**：脚本自动扫描目标账号 `raw/` 下现有笔记的 `dedup_key`（微信提取 `mid+idx`，X 提取 `status_id`，无链接文本提取标题+前 150 字 SHA-256 指纹），已存在则跳过，并在每次归档后按日期倒序非破坏性重建 `00-索引.md`。

---

## 三、 六维写作 DNA 深度蒸馏流程（L1–L6 七步法）

参考 [larashero3-dotcom/writing-dna-skill](https://github.com/larashero3-dotcom/writing-dna-skill/blob/main/SKILL.md) 与 [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill/blob/main/SKILL.md)，从 `raw/` 语料库（快速模式 ≥3 篇，完整模式 ≥20 篇）中按 7 个步骤蒸馏出 5 份分层文档：

### Step 1 & Step 2：语料收集与 `_meta/*.json` 标注
对每篇入库文章生成或补全 `_meta/<文件名>.json`（遵循 `templates/article-meta.schema.json` 的 11 个字段）：重点标注 `article_type`（体裁）、`hook_type`（问题式 / 场景式 / 数据反差式 / 暴击观点式 / 时间锚点动作式）与 `structure_pattern`（总-分-总 / 单点推进 / 问题链 / 时间线 / 对比式）。

### Step 3：运行 `distill_style_dna.py` 提取 L1 表层语言 DNA（产出 `语言DNA.md`）
脚本自动统计并由 Agent 归纳以下量化指纹：
1. **句长与段落呼吸分布**：平均句长、句长标准差、短句（≤15 字）占比、长句（≥50 字）占比、每段平均句数与每段平均字数（如公众号常见 1-2 句一段、单段 ≤90 字的手机屏快节奏，或深度评论 300 字一段的厚重砖块节奏）。
2. **标点生态与排版习惯**：每千字破折号 `——`、括号 `（）`（是否爱用括号插话吐槽）、分号 `；`、感叹号 `！`、问号 `？` 的精确密度；引号是用 `“”` 还是 `「」`；小标题平均字数与编号格式（如 `01 / 02`、`一、二、` 还是无编号陈述句）。
3. **高频词与禁用噪声词**：高频实词/动词偏好、高频连接词（如偏爱“说白了/其实/反过来想”还是零连接词直接硬切）、中英文混排习惯（英文术语与中文之间是否加空格）。

### Step 4：归纳 L2 分体裁文章结构模板（产出 `文章结构模板.md`）
**严禁把不同体裁混成一个平均模板！** 必须按 `_meta` 中的 `article_type` 分别归纳（至少提炼 2-3 种高频体裁）：
- 记录每种体裁的固定节拍：`[开头 Hook 写法 + 精确字数区间] -> [如何引出核心问题/第一转折点] -> [主体小节数量、每节字数配额与推进关系] -> [收尾方式：戛然而止 / 留悬念 / 唯一行动引导]`。
- 标注该账号的**反模板特征**（如：是否全文从不用项目符号列表？是否在 60% 处必有一段反面边界讨论？）。

### Step 5：深度阅读归纳 L3 选题逻辑、L4 素材策略与 L5 认知框架（产出 `写作视角与认知框架.md`）
此步不可用脚本替代，需深度阅读原文并结合 [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill) 的**三重验证法（跨域复现、有生成力、有排他性）**：
- **L3 选题判断树**：喜欢在什么时机切入（早期预判 / 热点拆解 / 事后复盘）？站什么视角（一线实操者 / 行业冷眼观察者 / 用户嘴替）？明确不写什么话题？
- **L4 素材与证据链策略**：依赖一手实测截图、财报数据、人物对话还是跨界类比？图片/截图在文中承担什么功能（是“先给结论再放截图当证据”还是“直接用截图推进叙事”）？
- **L5 核心认知框架**：提炼 3-5 条跨文章反复出现的非显而易见判断（决策启发式：`当遇到 X 时，倾向于判断 Y`）以及作者思想中的内在张力。
- **【双轨安全锁】**：若当前蒸馏的是 `external_benchmarks`，必须在文档顶部自动写入红线声明：*“本档案为外部标杆，写作调用时仅允许借鉴其视角切入方法与证据组织形式，严禁挪用其个人履历、专有案例与第一人称故事。”*

### Step 6：提取 L6 视觉与排版指南（产出 `视觉风格指南.md`）
统计图文比（每隔多少字出现一张图）、图片 6 类功能占比（证据型 / 演示型 / 数据型 / 叙事推进型 / 情绪型 / 权威型）、每千字加粗次数（只加粗核心判断句还是零加粗）、引用块 `>` 的使用场景。

### Step 7：生成总入口 `Writing-DNA.md`（≤4000 字）
将 L1-L6 的可执行规则浓缩进 `Writing-DNA.md`（若为 `our_own_voice` 自有账号，底部自动挂载来自 `evolution_ledger.json` 的「用户手改进化规则」章节）。

---

## 四、 按风格 DNA 写作时的「5 份产物 + 5 篇原文」强制校准协议

参考 [larashero3-dotcom/writing-dna-skill](https://github.com/larashero3-dotcom/writing-dna-skill/blob/main/SKILL.md) 第六节，每当用户要求使用某套已蒸馏风格辅助写稿时，严禁只读 `Writing-DNA.md` 概要就匆忙下笔，必须执行以下三步：

1. **全量读取分层产物**：依次读取目标风格目录下的 `语言DNA.md`、`文章结构模板.md`、`写作视角与认知框架.md`、`视觉风格指南.md` 与 `Writing-DNA.md`；同时读取 `our_own_voice` 自有账号下的 `evolution_ledger.json`。
2. **抽取 5 篇同体裁近期原文校准微语感**：
   - 优先从目标风格的 `raw/` 中按 `article_type`（同体裁）+ `topic_tags`（相近题材）挑选发布时间最近的 **5 篇原文**（不足 5 篇则取全部同体裁原文）。
   - **先总结语感再动笔**：通读这 5 篇原文，重点捕捉规则文档写不出来的微妙节奏——第一句话怎么落字、段与段之间怎么换气、什么时候突然甩出一句短判断、口语词和书面词怎么咬合。先用简短几句话概括这 5 篇原文的语感特征，随后开始起草正文。
3. **冲突裁决优先级**：
   `1. 用户本次明确指令（主题、字数、留白要求）` > `2. 自有账号 evolution_ledger.json 手改进化偏好与人设红线` > `3. 目标风格的 L2 同体裁结构模板与 L1 语言/L6 排版特征` > `4. 通用去 AI 味规则`。
