---
name: danchaofan-data-tracker
description: 「蛋炒饭财经」自媒体多平台发布后数据抓取助手。视频发到抖音/小红书/B站/视频号之后，抓账号级或稿件级后台数据、落盘归档、供复盘。当用户说"更新数据""刷新数据""更新账号数据""更新B站账号数据""更新小红书账号数据""更新视频号数据"，或给出一条创作者后台数据页链接（抖音作品详情页 work-detail、小红书 note-detail 含 noteId、B站 upload-manager 含 BV 号）时使用本技能。它按平台注入会话 cookie 抓后台接口，把数据写进创作 skill 的 workspace/ 下（账号级落 `账号数据/<平台>.md`，稿件级落各视频 `数据/<平台>_数据.md`）。注意：这是发布【之后】的数据工作流，和「把股票变成视频」的创作流程（bilibili-finance-video）是两件事。
---

# 蛋炒饭财经 · 发布后数据抓取

视频发布**之后**追踪四平台（抖音 / 小红书 / B站 / 视频号）后台数据的一条独立工作流。和创作流程（选题→口播稿→封面→分镜，走 `bilibili-finance-video` 技能）是两件事——这里只管"已经发出去的视频/账号现在数据怎么样"。

## 与创作 skill 的关系（务必先懂）

- **脚本住在本技能** `scripts/` 下，**cookie 也在本技能根目录**（`.douyin_cookie` / `.xiaohongshu_cookie` / `.bilibili_cookie` / `.channels_cookie`，已 gitignore）。
- **但数据产出写回创作 skill `bilibili-finance-video` 的 `workspace/`**——视频文件夹、`账号数据/`、`reports/` 都归创作 skill 所有，是那条"记录作品→追踪数据→复盘→反哺创作"闭环的落脚点。脚本内部用 `scripts/_paths.py` 自动定位创作 skill 的 workspace/（解析顺序：环境变量 `BILIBILI_FINANCE_SKILL_DIR` > `~/.claude/skills/bilibili-finance-video` > `~/.codex/...` > 同级目录），**无需手动传路径**。
- 若两个 skill 不在同一 `skills/` 目录下、自动定位失败，设一次环境变量即可：`export BILIBILI_FINANCE_SKILL_DIR=/abs/path/to/bilibili-finance-video`。

## 脚本路径

脚本随本技能安装在 `scripts/` 下。**不要假设 shell 的 cwd 是技能目录**——运行前先解析本技能根目录，用绝对路径调用：

```bash
SKILL_DIR="$HOME/.claude/skills/danchaofan-data-tracker"
[ -d "$SKILL_DIR" ] || SKILL_DIR="$HOME/.codex/skills/danchaofan-data-tracker"
```

下文示例为简洁写成 `scripts/xxx.py`，实际调用替换为 `"$SKILL_DIR/scripts/xxx.py"`。

## 触发语 → 脚本速查表

| 触发语 / 输入 | 脚本 | 落盘（在创作 skill 的 workspace/ 下） |
|---|---|---|
| "更新账号数据"/"刷新账号数据" | `douyin_account.py --save-raw` | `账号数据/抖音.md` |
| "更新小红书账号数据" | `xiaohongshu_account.py --save-raw` | `账号数据/小红书.md` |
| "更新B站账号数据" | `bilibili_account.py --save-raw` | `账号数据/账号数据_B站.md` |
| "更新视频号数据"（不点名视频） | `channels_metrics.py --save-raw` | `账号数据/视频号.md`（账号+全部稿件一次抓全） |
| 给抖音作品详情页链接 / "更新某支视频数据" | `douyin_metrics.py --url "<链接>" --video "<日期_标题>" --save-raw` | 该视频 `数据/抖音_数据.md` |
| 给小红书笔记数据页链接（含 noteId） | `xiaohongshu_metrics.py --url "<链接>" --video "<日期_标题>" --save-raw` | 该视频 `数据/小红书_数据.md` |
| 给 B站稿件数据页链接（含 BV） | `bilibili_metrics.py --url "<链接>" --video "<日期_标题>" --save-raw` | 该视频 `数据/B站_数据.md` |
| 点名某支视频的视频号数据 | `channels_metrics.py --video "<日期_标题>" --save-raw` | 该视频 `数据/视频号_数据.md` |
| 备选：抖音手动 xlsx 导入 | `ingest_metrics.py --video "<日期_标题>" 导出.xlsx` | 该视频 `数据/抖音_数据.md` |

`--video` 传带日期前缀的完整文件夹名，须与 workspace 下文件夹名完全一致；`--url` 从该视频 `视频基础信息.md` 的 `创作后台链接（各平台）` 块对应平台行读，不用每次找用户要。

## 「更新数据」范围规则（四平台通用）

**更新范围由用户当次描述决定**，不要自作主张扩大或缩小：

- **点名某支/某几支** → 只对被点名的视频跑稿件级脚本。
- **说"更新所有""全部刷一遍"** → 遍历 `workspace/*/视频基础信息.md`，对每支后台链接不是"待填"的依次跑（一支 cookie 失效/抓空不中断其余，最后汇总成功/失败）。
- **只说"更新数据"没指范围** → 默认更新所有已发布的；有歧义先问一句确认，别默认全量猛跑。
- **未指平台先确认平台**（抖音 / 小红书 / B站 / 视频号，或多个）。
- 某支后台链接还是"待填" → 提示用户补链接，别跳过时不吭声。
- **账号级 vs 稿件级别混淆**：账号级触发语是"更新账号数据""更新B站账号数据"等，走各自的 account 脚本。

## 完整说明

各平台接口字段、cookie 过期处理、每个脚本的产出小节、发布后回填后台链接的规则、分析复盘写法，全部见 **[references/data-tracking.md](references/data-tracking.md)**。

cookie 过期时（脚本报"未抓到…数据"或 `code!=0`），让用户从浏览器复制对应平台的 `document.cookie` 覆盖本技能根目录下的 `.<平台>_cookie` 文件即可，脚本无需改动。
