# 37 Writing｜ChatGPT Web 私有写作插件

此包是 **Skills-only** ChatGPT 插件，无第三方 MCP 服务、API Key、本地 Python、账号抓取、定时任务或自动发布。把 Windows 本地写作系统的可复用部分迁移为 ChatGPT 网页版能直接使用的提示与参考文件。

六个 Skill：`writing-workbench` 总调度、`wechat-story-editor`、`x-native-writer`、`xiaohongshu-native-writer`、`natural-chinese-editor`、`content-hook-lab`。支持公众号/X/小红书各自写作、文章改稿、事实审查、爆款标题与长文情绪曲线。用户仅需问自然语言问题。

**触发例子**：
- 帮我把这段历史素材写成公众号故事，第一段直接上矛盾。
- 这篇文章转成 X 线程，不要摘要腔。
- 写一篇可以收藏的小红书 AI 工具教程。
- 去掉这篇的 AI 味，事实、数字、立场全部保留。
- 这 6 个标题哪个更可能被点？分析原因，不要乱编数据。

不自动学习你的私人文章；只有你在对话中提供或授权可访问的样本，才根据样本临时调整风格。每日研究由独立定时任务负责，**不会自动更改已安装插件**。

已内置 `user-edit-feedback.md` 对话式改稿反馈，不含自动修改记忆、私人作者训练或永久封禁词。
