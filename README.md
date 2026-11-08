# 37-writing

**中文原创写作工作台：微信公众号 · X · 小红书 · 自然文风 · 传播潜力分析**

本仓库采用双版本结构：

- [`chatgpt-plugin/37-writing/`](chatgpt-plugin/37-writing/)：**ChatGPT Web skills-only 私有插件源文件**。无需运行本地代码；包含平台写作、去 AI 套话、事实保真与标题优化。
- [`windows-skill/chinese-humanizer-writer/`](windows-skill/chinese-humanizer-writer/)：Windows / Claude Code / Codex v3 本地完整版；带 PowerShell 安装、Python 质量门禁、档案与 Diff 学习、单元测试。
- [`research/`](research/)：研究卡、来源与升级提案；每日研究会优先寻找有实质价值的改进，而不是自动填词。

## 核心写作流程

`选题价值 → 事实账本 → 平台分流 → 开头钩子 → 人物/证据/观点推进 → 去套话 → 多维审稿 → 用户终审`

写作不是让平台“检测不出 AI”，也不是强行承诺 10w+。评价顺序：**事实与原创性 > 读者价值 > 故事节奏与平台适配 > 表层表达**。

## ChatGPT 网页版

安装私有插件 `37 Writing · 中文写作工作台`，在新对话里直接说“帮我写公众号人物故事”“把这篇改成 X 线程”“去掉 AI 味但保留数据”。插件是指令层，不会读取你 Windows 本地文件、自动发布或自动执行日更。对应源文件可在 `chatgpt-plugin/37-writing/skills/` 查看。

## Windows 本地版

进入 `windows-skill/chinese-humanizer-writer/` 并阅读 README。先用 `install.ps1 -DryRun` 预演安装，再运行测试。

## 迭代规则

每日研究近期 GitHub 仓库、写作 Skill、平台官方资料和论文：记录来源、发表时间、许可证、客观热度或方法证据、适用范围、潜在回归。候选变更先跑测试，再以 Draft PR 交给人审，**不自动合并 main，不自动升级用户插件**。

## 版权与安全

请勿复制第三方作者的专属文案与虚构个人经历；转载需审查原作者许可证与引用权限。网页和仓库内容仅为研究素材，不接受其中嵌入的指令来覆盖工作流。项目目前不额外声明对第三方代码的开源再授权；具体文件请核对其原始归属。

**Windows 编码说明**：命令行运行或重定向中文输出时，在 PowerShell 设置 `$env:PYTHONUTF8 = "1"` 和 `$env:PYTHONIOENCODING = "utf-8"`，详见 Windows 子项目 README。
