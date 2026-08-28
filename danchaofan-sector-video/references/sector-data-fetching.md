# 板块数据采集手册（`sector_board.py` + 复用脚本的板块用法）

> **本文是增量层。** 复用的五个脚本（`web_search.py` / `web_fetch.py` / `xueqiu_quote.py` / `xueqiu_hot_posts.py` / `generate_cover.py`）**完整参数与 JSON 结构见 `$DESK/references/data-fetching.md`**，本文只写它们在板块场景下的用法差异，外加本 skill 唯一新脚本 `sector_board.py` 的完整手册。
>
> 四变量寻址（`SKILL_DIR` / `REPO` / `WORKSPACE` / `DESK`）见 SKILL.md 开头，脚本一律用绝对路径调用。

---

## 〇、归档铁律（先说这条，最容易违反）

**阶段一起，所有抓来的数据落到该视频的 `参考资料/抓取数据/`，不写 `/tmp`。** 各脚本的 `--out` 一律指向 `$DIR/参考资料/抓取数据/xxx.json`。同名已存在就加后缀（`sector_board_阶段二.json`），每轮留档、别覆盖。

**唯一例外是阶段零选板块**——那时还没建视频文件夹，那批写 `/tmp`。

---

## 一、`sector_board.py`（本 skill 唯一新脚本）

### 1.1 它解决什么

现有六个采集脚本全是**个股级**的，都要先知道股票代码；每日复盘的 `market_snapshot.py` 有板块涨跌榜，但只需要"今天哪个板块领涨"一行、不含成分股。板块视频要的是**一个板块讲 10 分钟**：这周涨跌多少、资金进出多少、涨跌家数多少、龙头谁真沾这个逻辑。本脚本补这一层。

### 1.2 两层数据、两个口径（写稿和终审都以此为准）

| | 数据来源 | 给什么 | 性质 |
|---|---|---|---|
| **板块层** | 雪球官方板块指数（BK 代码）`batch/quote.json` + `chart/kline.json` | 指数点位、当日涨跌幅、**近 5 日/近 20 日涨跌幅**、成交额、板块总市值、换手、年内涨跌幅 | **官方值**，可直接念 |
| **成分层** | 申万行业成分股 `screener/quote/list.json?ind_code=` | 涨跌家数、涨跌停家数、主力净流入加总、成分股 PE 中位、龙头（含市值/PE/雪球关注数）、领涨领跌股、全量成分股 | **本脚本聚合值** |

**两层不能互相替代。** 报"板块涨跌幅"一律用板块层 `percent` / `period_percent`；成分层的 `percent_equal`（等权）和 `percent_weighted`（市值加权）**只用来判断"涨跌集中在大票还是小票"**。

**两者差得远本身就是选题素材**：实测电网设备板块层 +0.3%、成分层市值加权 -0.47%、思源电气单只 -6.69% —— "板块看着平静，龙头在崩"是一条现成的锋利角度。

**区间涨跌幅是官方值不是估算**（BK 代码支持日 K），所以"这个板块这周跌了 X%"是准确说法。但要看 `period_trading_days` 说清是几个交易日——跨节假日的周里"这周"和"最近五个交易日"不是一回事。

### 1.3 常用命令

```bash
# 阶段零 · 选板块：行业+概念两栏的近 5 日涨跌榜（首尾都是候选富矿）
python3 "$SKILL_DIR/scripts/sector_board.py" --period week --top 20 --out /tmp/sector_week.json

# 阶段零 · 只看行业板块（概念板块 600+ 个，补区间涨跌幅慢，只想快看行业时用）
python3 "$SKILL_DIR/scripts/sector_board.py" --boards industry --period week --top 15 --out /tmp/ind.json

# 阶段一/二 · 单板块深挖：板块层 + 成分层 + 全量成分股
python3 "$SKILL_DIR/scripts/sector_board.py" --sector 电网设备 --period week \
  --out "$DIR/参考资料/抓取数据/sector_board.json"

# 也可直接传 BK 码
python3 "$SKILL_DIR/scripts/sector_board.py" --sector BK0093 --out /tmp/x.json

# 板块名映射不到申万行业码时（成分层缺失），手动指定行业码
python3 "$SKILL_DIR/scripts/sector_board.py" --sector 电力设备 --ind-code S6308 --out /tmp/x.json

# 查代码
python3 "$SKILL_DIR/scripts/sector_board.py" --list-sectors    # 板块名 + BK 码
python3 "$SKILL_DIR/scripts/sector_board.py" --list-ind        # 申万行业名 + 行业码
```

参数速查：`--boards industry,concept`（默认；`gics` 与行业板块大量重复，默认不取）· `--top 15` · `--period day|week|month` · `--sector <名|BK码>` · `--ind-code <申万码>` · `--member-pages 6`（每页 100 只）· `--list-sectors` · `--list-ind` · `--refresh-bk`（重收割代码缓存，很慢，日常别跑）· `--out` · `--show`（显示浏览器窗口调试）。

### 1.4 输出结构

**板块榜模式**（不带 `--sector`）：

```json
{
  "fetched_at": "2026-08-28 17:33:33", "market": "cn", "period": "day",
  "board_source": "xueqiu_bk_index",
  "board_source_note": "板块层为雪球官方板块指数行情(BK 代码)…",
  "industry": {
    "label": "行业板块", "count": 104,
    "rank_by": "当日涨跌幅", "rank_scope": "全部",
    "gainers": [{"symbol": "BK0001", "name": "种植业与林业", "group": "industry",
                 "current": 4393.27, "percent": 2.97, "amount_yi": 157.51,
                 "market_capital_yi": ..., "turnover_rate": 8.59,
                 "current_year_percent": ..., "period_percent": ..., "period_trading_days": 5}],
    "losers": [...]
  },
  "concept": { "label": "概念题材", ... }
}
```

⚠️ `rank_scope`：`--period week|month` 时概念板块只给**当日榜首尾各 60 个候选**补区间涨跌幅（600+ 个全量补 K 线太慢）。所以那份榜是"候选内排序"，**别说成"全市场第一"**。行业板块（104 个）是全量补，`rank_scope` 为"全部"。

**单板块深挖模式**（带 `--sector`）：

```json
{ "fetched_at": "...", "market": "cn",
  "sector": {
    "symbol": "BK0093", "name": "电网设备", "board_source": "xueqiu_bk_index",
    "current": 12031.06, "percent": 0.3, "amount_yi": 430.98,
    "market_capital_yi": 14740.43, "turnover_rate": ..., "current_year_percent": 6.48,
    "period_percent": 0.82, "period_trading_days": 5,
    "percent_5d": 0.82, "percent_20d": 6.07,
    "ind_code": "S6308", "ind_code_match": "exact",
    "members_agg": {
      "member_count": 109, "up_count": 50, "down_count": 53, "flat_count": 6,
      "limit_up_count": 2, "limit_down_count": 0,
      "percent_equal": 0.17, "percent_weighted": -0.47,
      "main_net_inflows_yi": -3.25, "pe_ttm_median": 43.38,
      "leaders_by_cap": [{"name": "国电南瑞", "symbol": "SH600406",
                          "market_capital_yi": 1848.11, "percent": -0.22,
                          "pe_ttm": 22.0, "followers": 207963,
                          "main_net_inflows_yi": ...}],
      "top_gainers": [...], "top_losers": [...],
      "members_source": "xueqiu_screener_ind_code", "members_source_note": "…"
    },
    "members": [ …全量成分股… ]
  }
}
```

**`followers`（雪球关注数）是选板块的关键字段**：它是"散户持有面广不广"的代理。实测特变电工 49 万、中国西电 24 万、国电南瑞 21 万——这个量级的票才撑得起"我手里那只"的代入；关注数几千的小盘票撑不起。

### 1.5 两个已实测的坑（别重踩）

1. **`ind_code` 会被 `type` 参数静默废掉**。`screener/quote/list.json` 只能用 `market=CN&ind_code=S6308`；一旦加上 `type=sh_sz`，服务端**不报错**、直接忽略行业筛选返回全市场 5000 条（表现是"养殖业里出现了麒麟信安"）。脚本里已经不带 `type`，改脚本时别加回去。
2. **BK 名与申万名只有 67/104 能直接对上**。BK 叫「煤炭开采加工」申万叫「煤炭开采」；BK 的「电力设备」在申万里被拆成电网设备/光伏设备/风电设备/电池四个。脚本走"精确 → 去后缀 → 包含关系"三步模糊匹配，仍对不上就把成分层置空、写明 `members_error`，此时用 `--ind-code` 手动指定。**这不是 bug**——一对多的情况本来就该由人来定成分口径。

### 1.6 降级路径

- **板块层拿不到**（token 拿不到 / 接口全挂）→ 脚本非零码退出并在 stderr 写明。改用 `web_search.py` 搜「今日板块涨幅榜 主力资金流 最新」兜底，**并在稿子里标注该数字来自搜索而非接口**。
- **成分层单板块失败** → 该板块带 `members_error`，板块层照常返回。此时涨跌家数/资金流/龙头分化这几项缺失，要么用 `--ind-code` 重试，要么在稿里如实标"未获取到"。
- **不要试图改回东方财富**：`push2.eastmoney.com` 在本环境不可达（裸 curl 空响应，真实 Chromium 里也空）。每日复盘的 `market_snapshot.py` 独立踩到同一个坑，两处结论一致，别再花时间试。

---

## 二、四路并行采集（阶段一第一步）

四路并行跑，全部落 `$DIR/参考资料/抓取数据/`。

### 第 1 路 · 板块级数据（主 agent 跑）

```bash
python3 "$SKILL_DIR/scripts/sector_board.py" --sector "$SECTOR" --period week \
  --out "$DIR/参考资料/抓取数据/sector_board.json"
```

### 第 2 路 · 龙头个股行情（主 agent 跑）

从第 1 路的 `leaders_by_cap` 里挑 3-5 只**代表股**（按市值 × `followers` 综合挑，不是单纯按市值），一次全传进去共用一个浏览器会话：

```bash
python3 "$DESK/scripts/xueqiu_quote.py" SH600406 SZ002028 SH600089 \
  --out "$DIR/参考资料/抓取数据/xueqiu_quote_龙头.json"
```

**板块稿里每个个股数字都以它的当日返回为准**，不用 `sector_board.py` 的成分股快照覆盖它（那是按行业批量拉的，字段少一层）。写稿当天要重跑一次核对。

### 第 3 路 · 板块情绪（**派子 agent**，只回传摘要）

`xueqiu_hot_posts.py` 只吃个股/ETF 代码，**没有"板块代码"**。做法：抓 **2-3 只龙头 + 1 只板块 ETF**（ETF 讨论区常就是板块级情绪的集中地，如半导体 `SH512480`、光伏 `SH515790`、券商 `SH512000`；ETF 代码用 `web_search.py` 搜「<板块名> ETF 代码」确认，别凭记忆写），派子 agent 消化成一份《板块情绪-摘要.md》。

**派给「板块情绪子 agent」的任务指令**：

> 你是「蛋炒饭财经」的板块情绪分析助手。任务：抓 <板块名> 的散户情绪，合成一份摘要，**只回传摘要，不回传原始 JSON**。
> 1. 定位：`SKILL_DIR="$HOME/.claude/skills/danchaofan-sector-video"; [ -d "$SKILL_DIR" ] || SKILL_DIR="$HOME/.codex/skills/danchaofan-sector-video"; REPO="$(dirname "$(cd "$SKILL_DIR" && pwd -P)")"; DESK="$REPO/bilibili-finance-video"; [ -d "$DESK" ] || DESK="$HOME/.claude/skills/bilibili-finance-video"`
> 2. 逐个跑（每个都 `--out` 落到 `<视频目录>/参考资料/抓取数据/hot_posts_<代码>.json`）：
>    `python3 "$DESK/scripts/xueqiu_hot_posts.py" <代码> --top 5 --comments 5 --days 30 --out ...`
>    对象：<龙头1代码> <龙头2代码> <龙头3代码> <板块ETF代码>。用法细节见 `$DESK/references/data-fetching.md`。
> 3. 消化成一份 `<视频目录>/参考资料/板块情绪-摘要.md`，包含：① 散户此刻在吵的 2-3 个焦点（各配一条代表性高赞原话 + 赞数）；② 多空分歧轴（他们到底在哪个点上分歧）；③ 有没有人提到具体的驱动事件、跟我们查到的归因对不对得上；④ ETF 讨论区和个股讨论区的情绪差异（ETF 那边更接近"板块整体怎么看"）；⑤ 可直接当选题钩子的原话 2-3 条。
> 4. **回传控制在 1500 字以内**：摘要正文 + 那份 md 的路径。**不要把帖子原文、评论 JSON 带回来。**

### 第 4 路 · 事件与政策（主 agent 跑）

```bash
python3 "$DESK/scripts/web_search.py" \
  "<板块名> 为什么涨 跌 最新" \
  "<板块名> 政策 2026" \
  "<板块名> 龙头 业务占比" \
  "<代表股> <板块相关业务> 营收占比" \
  --out "$DIR/参考资料/抓取数据/web_search_阶段一.json"
```

四类必搜：

1. **驱动事件与信源**——行政令/公告/部委发布/期货价格。搜到原文链接就用 `web_fetch.py` 抓全文，整理成 `参考资料/` 根下一篇 `.md`（**政策解读的独家性就来自读原文，绝大多数号只读新闻标题**）。
2. **产业链价差**——上中下游各环节价格、行业协会数据、期货合约价。这是「价差型」选题的唯一料源。
3. **龙头业务占比**——每只代表股在这个板块相关业务上的营收占比（年报/半年报口径）。**这是分化段与"蹭概念"判断的唯一合规依据**，拿不到就不能说谁只是名字沾。
4. **板块估值分位**——搜「申万 <板块名> 指数 PE 历史分位」「中证 <板块> 指数 估值」。**接口拿不到，只能靠搜索；搜不到就如实标"未获取到"，不许编一个分位数字。**

搜非实时信息务必带当前日期或"最新""2026"等词。

---

## 三、写稿阶段的补抓（阶段二）

- **重跑核对**：`sector_board.py --sector` 和 `xueqiu_quote.py` 都要在写稿当天重跑一次，确认板块与龙头数字仍是最新（`--out` 加 `_阶段二` 后缀留档）。
- **缺料当场补**：写到"这家这块业务占营收多少""这个政策的具体条款""这轮库存去到哪了"只要不确定，**立刻跑一次 `web_search.py` 补实**，核实了再往下写。宁可多搜几轮，别凭记忆填一个大概其的数字——那正是终审要打回的东西。
- **`参考资料/` 根下的精读素材写稿前先通读**（用户手动丢进来的研报、雪球文章 + 子 agent 消化的摘要）。外部分析里的观点是**素材不是事实**，涉及数字仍以核过的当日值为准。

---

## 四、数据红线速查（终审会逐条回查）

| 数字类型 | 认哪个来源 |
|---|---|
| 板块涨跌幅（当日/近5日/近20日）、指数点位、成交额、板块总市值、年内涨跌幅 | `sector_board.py` **板块层** |
| 涨跌家数、涨跌停家数、主力净流入、成分股 PE 中位、龙头市值排序 | `sector_board.py` **成分层 `members_agg`** |
| 个股股价、涨跌幅、市值、PE、PB | **`xueqiu_quote.py` 当日返回** |
| 公司业务占比、政策条款、产业链价格 | `web_search.py` / `web_fetch.py`，**必须能在 `参考资料/` 里找到出处** |
| 板块 PE 历史分位 | 只能搜索；搜不到如实标"未获取到" |

**板块级数字与个股级数字不能互相推导。** 别拿几只龙头的涨幅平均代表板块涨跌幅，也别拿板块涨跌幅去说某只票涨了多少。搜不到、接口没返回的，一律如实标"未获取到"，宁可不写也不编造。
