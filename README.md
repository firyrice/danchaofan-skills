# danchaofan-skills

「蛋炒饭财经」自媒体工作台的全部 skill。账号级共享工作台在仓库根的 `workspace/`（人设 Memory `huasheng.md` + 各视频文件夹），被下面各 skill 共读写。

**三条内容产线：**

- **bilibili-finance-video** — 个股深度分析（8-12 分钟，一支票一期）：选股→选题→写稿→终审→封面→分镜。
- **danchaofan-daily-review** — 每日收盘复盘（5-8 分钟，日更）：盘面快照→主线候选→写稿+终审→封面→分镜。自带 `market_snapshot.py` 抓市场级数据（指数/成交额/涨跌家数/涨跌停/板块榜），其余脚本与方法论复用创作 skill。
- **danchaofan-sector-video** — 板块分析（8-12 分钟，周级，一个板块一期）：选板块→选题→写稿+终审→封面→分镜。自带 `sector_board.py` 抓板块级数据（板块指数官方行情 + 区间涨跌幅 + 成分股聚合的涨跌家数/资金流/龙头分化），其余脚本与方法论复用创作 skill。

**两个横切工具**（靠 `workspace/*/视频基础信息.md` 定位，自动覆盖两条产线）：

- **danchaofan-data-tracker** — 发布后多平台（抖音/小红书/B站/视频号）数据抓取，写回 `workspace/`。
- **danchaofan-comment-reply** — 评论区回复：按账号人设产出回复并落档到各视频文件夹。

## 安装

各技能通过软链接挂到 `~/.claude/skills/<技能名>` 被 Claude Code / Codex 发现：

```bash
ln -s "$(pwd)/bilibili-finance-video"   ~/.claude/skills/bilibili-finance-video
ln -s "$(pwd)/danchaofan-daily-review"  ~/.claude/skills/danchaofan-daily-review
ln -s "$(pwd)/danchaofan-sector-video"  ~/.claude/skills/danchaofan-sector-video
ln -s "$(pwd)/danchaofan-data-tracker"  ~/.claude/skills/danchaofan-data-tracker
ln -s "$(pwd)/danchaofan-comment-reply" ~/.claude/skills/danchaofan-comment-reply
```

各平台会话 cookie（`.douyin_cookie` 等）为私有文件，已 gitignore，不入库。
