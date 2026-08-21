# danchaofan-skills

「蛋炒饭财经」自媒体工作台的两个独立 skill（与创作 skill `bilibili-finance-video` 配套）。

- **danchaofan-data-tracker** — 发布后多平台（抖音/小红书/B站/视频号）数据抓取。数据写回 `bilibili-finance-video` 的 `workspace/`。
- **danchaofan-comment-reply** — 评论区回复：按账号人设产出回复并落档到各视频文件夹。

## 安装

各技能通过软链接挂到 `~/.claude/skills/<技能名>` 被 Claude Code / Codex 发现：

```bash
ln -s "$(pwd)/danchaofan-data-tracker"  ~/.claude/skills/danchaofan-data-tracker
ln -s "$(pwd)/danchaofan-comment-reply" ~/.claude/skills/danchaofan-comment-reply
```

各平台会话 cookie（`.douyin_cookie` 等）为私有文件，已 gitignore，不入库。
