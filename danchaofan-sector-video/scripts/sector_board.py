#!/usr/bin/env python3
"""抓取「板块级」数据：板块指数行情 + 区间涨跌幅 + 成分股聚合（涨跌家数/资金流/龙头分化）。

为什么要新写这个脚本:
    创作 skill 的六个采集脚本全是【个股级】的，都要先知道股票代码。
    每日复盘的 market_snapshot.py 有板块涨跌榜，但它只需要"今天哪个板块领涨"这一行，
    不需要成分股。板块视频要的是【一个板块讲 10 分钟】：这周涨跌多少、资金进出多少、
    涨跌家数多少、龙头谁真沾这个逻辑谁只是名字沾——本脚本补上这一层。

用法:
    python3 sector_board.py --out /tmp/board.json            # 板块榜(行业/概念分开，当日)
    python3 sector_board.py --period week --top 15           # 按近5日涨跌幅排(选板块常用)
    python3 sector_board.py --sector 电网设备 --out /tmp/x.json  # 单板块深挖(成分股+龙头分化)
    python3 sector_board.py --sector BK0088                  # 也可直接传 BK 码
    python3 sector_board.py --list-sectors                   # 列出全部板块名与代码
    python3 sector_board.py --refresh-bk                     # 重收割板块代码缓存

两层数据、两个口径，别混用:
    ① 板块层 = 雪球官方板块指数（BK 代码），这是【官方值】
       /v5/stock/batch/quote.json?symbol=BK0088,BK0093,...
         → current 指数点位、percent 当日涨跌幅、amount 成交额、
           market_capital 板块总市值、turnover_rate 换手、current_year_percent 年内涨跌幅
       /v5/stock/chart/kline.json?symbol=BK0093&period=day
         → 实测 BK 代码支持日 K，所以近 5 日 / 近 20 日涨跌幅也是【官方值】，
           不需要拿几只龙头去加权近似。写稿时可以直接说"板块这周跌了 X%"。
    ② 成分层 = 申万行业成分股行情，板块级指标由它【聚合】得出
       /v5/stock/screener/quote/list.json?market=CN&ind_code=S6308&size=100
         → 涨跌家数、涨跌停家数、主力净流入加总、龙头(按市值)、领涨/领跌股、PE 分布
       BK 官方行情【不给】这些字段，只能这样算。

    两层的涨跌幅【不要互相替代】：板块层是官方指数口径（成分与权重是雪球定的），
    成分层的 percent_equal/percent_weighted 是本脚本按申万行业自算的。
    口播报"板块涨跌幅"一律用板块层的官方值；成分层的两个口径只用来判断
    "涨跌是集中在大票还是普涨"（两者差得远本身就是选题素材）。

BK ↔ 申万 的映射:
    实测 BK 行业板块 104 个、申万行业 134 个，但名字只有 67 个能直接对上
    （BK 叫「煤炭开采加工」，申万叫「煤炭开采」；BK 叫「电力设备」，申万拆成
     「电网设备/光伏设备/风电设备/电池」）。所以映射走"精确 → 去后缀 → 包含关系"
    三步模糊匹配，仍对不上就把 members 置空并在输出里写明原因，
    此时深挖模式可以直接传申万码（--ind-code S6308）指定成分口径。

降级:
    板块层拿不到 → 非零码退出，改用 web_search.py 搜"今日板块涨幅榜 主力资金流 最新"，
    并在稿子里标注该数字来自搜索而非接口。
    成分层单个板块失败 → 该板块带 members_error 字段，板块层数据照常返回。
    见 references/sector-data-fetching.md。

注意:
    - 仅作个人研究，脚本已控制请求频率，别改小 sleep 去压对方服务器。
    - 输出里的 source / *_source 字段标明每层数据来源，终审回查数字时要能分辨。
    - 板块稿里的【个股】数字仍以 xueqiu_quote.py 当日返回为准，这条红线不变。
"""
import argparse
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

# 过 WAF 那套逻辑只有一份，在创作 skill 里。这里照 danchaofan-daily-review/scripts/
# market_snapshot.py 已跑通的写法 import，不复制第二版反爬代码。
_DESK_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__)))), "bilibili-finance-video", "scripts"),
    os.path.expanduser("~/.claude/skills/bilibili-finance-video/scripts"),
    os.path.expanduser("~/.codex/skills/bilibili-finance-video/scripts"),
]
for _p in _DESK_CANDIDATES:
    if os.path.isdir(_p):
        sys.path.insert(0, _p)
        break
try:
    from xueqiu_hot_stocks import (UA, STEALTH_JS, find_chromium,
                                   ctx_fetch_json, round_or_none, humanize_cap)
except ImportError:
    print("[error] 找不到 bilibili-finance-video/scripts/xueqiu_hot_stocks.py，"
          "本脚本复用它的过 WAF 逻辑。请确认创作 skill 与本 skill 在同一仓库，"
          "或设 PYTHONPATH 指向它的 scripts 目录。", file=sys.stderr)
    raise

BATCH_API = "https://stock.xueqiu.com/v5/stock/batch/quote.json"
KLINE_API = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
SCREENER_API = "https://stock.xueqiu.com/v5/stock/screener/quote/list.json"
INDUSTRIES_API = "https://stock.xueqiu.com/v5/stock/screener/industries.json"
PROBE = "https://xueqiu.com/hq"

BK_BATCH = 40            # batch/quote 一次问多少个板块代码
MEMBER_PAGE = 100        # screener 单页上限，实测传更大无效
MEMBER_MAX_PAGES = 6     # 单板块最多翻 6 页(600 只，覆盖所有申万行业)

# 板块代码缓存：优先用本 skill 的，没有就借每日复盘那份（同一份 BK 空间，没必要各收一次），
# 两处都没有才自己收割。收割一次要扫 1200 个代码，别在日常流程里跑。
_HERE = os.path.dirname(os.path.abspath(__file__))
BK_CACHE_CANDIDATES = [
    os.path.join(_HERE, "bk_codes.json"),
    os.path.join(os.path.dirname(os.path.dirname(_HERE)),
                 "danchaofan-daily-review", "scripts", "bk_codes.json"),
    os.path.expanduser("~/.claude/skills/danchaofan-daily-review/scripts/bk_codes.json"),
]
BK_CACHE_WRITE = BK_CACHE_CANDIDATES[0]

# BK 代码空间实测分三段（与 market_snapshot.py 同一套判据，保持口径一致）：
#   BK0001-0104  申万行业板块（"煤炭开采加工""电网设备"）
#   BK0400-0999  概念/题材板块（"白酒概念""智能电网""供销社"）
#   BK1001-1200  另一套 GICS 风格分类，与第一段大量重复且带 Ⅲ/Ⅳ 后缀 → 默认排除
BK_GROUPS = [
    {"key": "industry", "label": "行业板块", "lo": 1, "hi": 104},
    {"key": "concept", "label": "概念题材", "lo": 400, "hi": 999},
    {"key": "gics", "label": "GICS行业(与行业板块重复)", "lo": 1000, "hi": 1300},
]
DEFAULT_GROUPS = ["industry", "concept"]

PERIOD_DAYS = {"day": 0, "week": 5, "month": 20}

# 概念板块有 600 多个，period=week/month 时全量补 K 线太慢。只给当日榜首尾的候选补，
# 输出里会写明补算范围，避免把"候选里的第一"说成"全市场第一"。
CONCEPT_PERIOD_POOL = 60


def bk_group(symbol):
    try:
        n = int(str(symbol)[2:])
    except (TypeError, ValueError):
        return None
    for g in BK_GROUPS:
        if g["lo"] <= n <= g["hi"]:
            return g["key"]
    return None


# --------------------------------------------------------------------------- #
#  1. 板块代码缓存
# --------------------------------------------------------------------------- #
def fetch_bk_batch(ctx, codes):
    """一次问一批板块代码的官方行情。无效代码的 quote 是 None，跳过。"""
    status, body, raw = ctx_fetch_json(ctx, f"{BATCH_API}?symbol={','.join(codes)}")
    if status != 200 or not body:
        raise RuntimeError(f"batch status={status} {raw[:80]}")
    rows = []
    for it in ((body.get("data") or {}).get("items") or []):
        q = it.get("quote") or {}
        if not q.get("name"):
            continue
        rows.append({
            "symbol": q.get("symbol"),
            "name": q.get("name"),
            "group": bk_group(q.get("symbol")),
            "current": round_or_none(q.get("current")),        # 板块指数点位
            "percent": round_or_none(q.get("percent")),        # 当日涨跌幅(官方)
            "amount_yi": humanize_cap(q.get("amount")),
            "market_capital_yi": humanize_cap(q.get("market_capital")),
            "turnover_rate": round_or_none(q.get("turnover_rate")),
            "current_year_percent": round_or_none(q.get("current_year_percent")),
            "amplitude": round_or_none(q.get("amplitude"), 4),
        })
    return rows


def refresh_bk_cache(ctx, scan_max=1200):
    """扫一遍 BK 代码空间存成缓存。

    BK 代码空间【稀疏且有大段空洞】：BK0105-0436 整段是空的，BK0437+ 又是概念板块。
    所以不能"连续几批空就提前收工"，早停会把概念板块整批丢掉。整段扫完，不提前退出。
    """
    found = []
    for start in range(1, scan_max + 1, BK_BATCH):
        codes = [f"BK{n:04d}" for n in range(start, min(start + BK_BATCH, scan_max + 1))]
        try:
            rows = fetch_bk_batch(ctx, codes)
        except Exception as e:
            print(f"[warn] 扫 BK{start:04d} 起失败: {e}", file=sys.stderr)
            rows = []
        found.extend({"symbol": r["symbol"], "name": r["name"]} for r in rows)
        if rows:
            print(f"[bk] BK{start:04d}+ → 命中 {len(rows)}，累计 {len(found)}", file=sys.stderr)
        time.sleep(0.15)
    with open(BK_CACHE_WRITE, "w", encoding="utf-8") as f:
        json.dump({"updated_at": time.strftime("%Y-%m-%d"), "count": len(found),
                   "boards": found}, f, ensure_ascii=False, indent=2)
    print(f"[bk] 已写入 {BK_CACHE_WRITE}，共 {len(found)} 个", file=sys.stderr)
    return found


def load_bk_boards(ctx, refresh=False):
    if not refresh:
        for path in BK_CACHE_CANDIDATES:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                boards = data.get("boards") or []
                if boards:
                    print(f"[bk] 用缓存 {path}（{data.get('updated_at')}，"
                          f"{len(boards)} 个板块）", file=sys.stderr)
                    return boards
    return refresh_bk_cache(ctx)


# --------------------------------------------------------------------------- #
#  2. 区间涨跌幅（BK 支持日 K，所以是官方值）
# --------------------------------------------------------------------------- #
def fetch_period_percent(ctx, symbol, days):
    """用板块指数日 K 算近 N 个交易日累计涨跌幅。返回 (percent, 实际用到的交易日数)。"""
    url = (f"{KLINE_API}?symbol={symbol}&begin={int(time.time() * 1000)}"
           f"&period=day&type=before&count=-{days + 1}")
    status, body, _ = ctx_fetch_json(ctx, url)
    data = (body or {}).get("data") or {}
    cols, items = data.get("column") or [], data.get("item") or []
    if not items or "close" not in cols:
        return None, None
    ci = cols.index("close")
    closes = [r[ci] for r in items if r[ci] is not None]
    if len(closes) < 2 or not closes[0]:
        return None, None
    return round((closes[-1] - closes[0]) / closes[0] * 100, 2), len(closes) - 1


def enrich_period(ctx, rows, days, label):
    """给一批板块补区间涨跌幅，逐个打进 rows（原地改）。"""
    print(f"[period] 补算 {len(rows)} 个{label}的近 {days} 交易日涨跌幅", file=sys.stderr)
    for i, r in enumerate(rows, 1):
        try:
            pct, used = fetch_period_percent(ctx, r["symbol"], days)
            r["period_percent"] = pct
            r["period_trading_days"] = used
        except Exception as e:
            print(f"[warn] {r['name']} K线失败: {e}", file=sys.stderr)
            r["period_percent"] = None
        if i % 40 == 0:
            print(f"[period] {label} {i}/{len(rows)}", file=sys.stderr)
        time.sleep(0.15)


# --------------------------------------------------------------------------- #
#  3. 成分股聚合（BK 官方行情给不了的那些字段）
# --------------------------------------------------------------------------- #
def fetch_industries(ctx, category="CN"):
    """申万行业列表：[{encode, name, ...}]。

    ⚠️ 只能用 ?category=CN；?type=CN 会报 400016。
    """
    status, body, raw = ctx_fetch_json(ctx, f"{INDUSTRIES_API}?category={category}")
    inds = ((body or {}).get("data") or {}).get("industries") or []
    if status != 200 or not inds:
        raise RuntimeError(f"申万行业列表拉取失败 status={status} {raw[:80]}")
    return inds


# 映射时要剥掉的构词后缀。BK 与申万经常只差这些字（煤炭开采加工 ↔ 煤炭开采）。
_TRIM = ["加工制造", "开采加工", "及其他", "及服务", "制造", "开采", "加工",
         "应用", "工程", "装备", "运输", "服务", "设备", "业"]


def _norm(name):
    s = name.replace("概念", "").replace("Ⅲ", "").replace("Ⅳ", "")
    for suf in _TRIM:
        if s.endswith(suf) and len(s) > len(suf) + 1:
            s = s[:-len(suf)]
            break
    return s


def match_ind_code(board_name, industries):
    """BK 板块名 → 申万行业码。三步：精确 → 去后缀 → 包含关系。

    对不上返回 (None, 原因)。硬映射不出来不是 bug——BK「电力设备」在申万里被拆成
    电网设备/光伏设备/风电设备/电池四个，本来就没有一对一的答案，
    这时候由人（或 --ind-code）指定成分口径才对。
    """
    by_name = {i["name"]: i["encode"] for i in industries}
    if board_name in by_name:
        return by_name[board_name], "exact"

    target = _norm(board_name)
    norm_map = {}
    for i in industries:
        norm_map.setdefault(_norm(i["name"]), []).append(i)
    if target in norm_map and len(norm_map[target]) == 1:
        return norm_map[target][0]["encode"], f"normalized→{norm_map[target][0]['name']}"

    contains = [i for i in industries
                if _norm(i["name"]) and (target in _norm(i["name"])
                                         or _norm(i["name"]) in target)]
    if len(contains) == 1:
        return contains[0]["encode"], f"fuzzy→{contains[0]['name']}"
    if contains:
        names = "/".join(i["name"] for i in contains)
        return None, f"申万里对应多个行业({names})，请用 --ind-code 指定"
    return None, "申万行业列表里没有对应项"


def struct_member(item):
    """成分股行情精简成"讲龙头分化"要用的字段。

    除了行情，市值/PE/资金流/关注数都留着——市值判断是不是龙头，
    雪球关注数是"散户持有面广不广"的代理（板块题最缺的就是"我手里那只"）。
    """
    return {
        "symbol": item.get("symbol"),
        "name": item.get("name"),
        "current": round_or_none(item.get("current")),
        "percent": round_or_none(item.get("percent")),
        "market_capital_yi": humanize_cap(item.get("market_capital")),
        "pe_ttm": round_or_none(item.get("pe_ttm")),
        "pb": round_or_none(item.get("pb")),
        "amount_yi": humanize_cap(item.get("amount")),
        "main_net_inflows_yi": humanize_cap(item.get("main_net_inflows")),
        "turnover_rate": round_or_none(item.get("turnover_rate")),
        "followers": item.get("followers"),
        "current_year_percent": round_or_none(item.get("current_year_percent")),
    }


def fetch_members(ctx, ind_code, market="CN", max_pages=MEMBER_MAX_PAGES):
    """拉一个申万行业的全部成分股（自动分页）。

    ⚠️ 不要往 URL 里加 type=sh_sz——实测会让 ind_code 静默失效、返回全市场 5000 条。
    只用 market=CN + ind_code。
    """
    out, page = [], 1
    while page <= max_pages:
        url = (f"{SCREENER_API}?page={page}&size={MEMBER_PAGE}"
               f"&order=desc&order_by=percent&market={market}&ind_code={ind_code}")
        status, body, raw = ctx_fetch_json(ctx, url)
        if status != 200 or not body:
            raise RuntimeError(f"成分股拉取失败 status={status} {raw[:80]}")
        data = (body or {}).get("data") or {}
        lst = data.get("list") or []
        out.extend(struct_member(x) for x in lst)
        total = data.get("count")
        if len(lst) < MEMBER_PAGE or (total and len(out) >= total):
            break
        page += 1
        time.sleep(0.4)
    return out


def aggregate_members(members):
    """成分股 → BK 官方行情给不了的那几项。

    两个自算涨跌幅口径都给，但它们【不能替代板块层的官方 percent】：
      - percent_equal    等权，小盘股影响放大
      - percent_weighted 市值加权，更接近指数
    这两个的用途是和官方 percent 对比看涨跌集中在大票还是小票，本身就是选题素材。
    """
    pcts = [m["percent"] for m in members if m.get("percent") is not None]
    caps = [(m["percent"], m["market_capital_yi"]) for m in members
            if m.get("percent") is not None and m.get("market_capital_yi")]
    inflows = [m["main_net_inflows_yi"] for m in members
               if m.get("main_net_inflows_yi") is not None]
    cap_all = [m["market_capital_yi"] for m in members if m.get("market_capital_yi")]

    weighted = None
    if caps:
        tot = sum(c for _, c in caps)
        if tot:
            weighted = round(sum(p * c for p, c in caps) / tot, 2)

    ranked = sorted([m for m in members if m.get("percent") is not None],
                    key=lambda m: m["percent"], reverse=True)
    by_cap = sorted([m for m in members if m.get("market_capital_yi")],
                    key=lambda m: m["market_capital_yi"], reverse=True)
    pes = [m["pe_ttm"] for m in members
           if isinstance(m.get("pe_ttm"), (int, float)) and m["pe_ttm"] > 0]

    return {
        "member_count": len(members),
        "up_count": sum(1 for p in pcts if p > 0),
        "down_count": sum(1 for p in pcts if p < 0),
        "flat_count": sum(1 for p in pcts if p == 0),
        "limit_up_count": sum(1 for p in pcts if p >= 9.9),
        "limit_down_count": sum(1 for p in pcts if p <= -9.9),
        "percent_equal": round(sum(pcts) / len(pcts), 2) if pcts else None,
        "percent_weighted": weighted,
        "main_net_inflows_yi": round(sum(inflows), 2) if inflows else None,
        "members_market_capital_yi": round(sum(cap_all), 2) if cap_all else None,
        "pe_ttm_median": (round(sorted(pes)[len(pes) // 2], 2) if pes else None),
        "leaders_by_cap": [
            {"name": m["name"], "symbol": m["symbol"],
             "market_capital_yi": m["market_capital_yi"], "percent": m["percent"],
             "pe_ttm": m["pe_ttm"], "followers": m["followers"],
             "main_net_inflows_yi": m["main_net_inflows_yi"]}
            for m in by_cap[:8]
        ],
        "top_gainers": [{"name": m["name"], "percent": m["percent"]} for m in ranked[:5]],
        "top_losers": [{"name": m["name"], "percent": m["percent"]}
                       for m in ranked[-5:]][::-1],
    }


# --------------------------------------------------------------------------- #
#  4. 会话编排
# --------------------------------------------------------------------------- #
def open_session(p, headless=True):
    exe = find_chromium()
    kw = {"headless": headless,
          "args": ["--disable-blink-features=AutomationControlled"]}
    if exe:
        kw["executable_path"] = exe
        print(f"[info] 使用浏览器: {exe}", file=sys.stderr)
    browser = p.chromium.launch(**kw)
    ctx = browser.new_context(user_agent=UA, locale="zh-CN",
                              viewport={"width": 1440, "height": 900})
    ctx.add_init_script(STEALTH_JS)
    pg = ctx.new_page()
    try:
        resp = pg.goto(PROBE, wait_until="networkidle", timeout=45000)
        print(f"[info] 探针页状态: {resp.status if resp else '?'}", file=sys.stderr)
    except Exception as e:
        print(f"[warn] 探针页导航: {e}", file=sys.stderr)
    for _ in range(15):
        pg.wait_for_timeout(1000)
        if any(c["name"] == "xq_a_token" for c in ctx.cookies()):
            print("[info] token 就绪", file=sys.stderr)
            break
    else:
        print("[warn] 未拿到 xq_a_token，接口可能仍被拦截", file=sys.stderr)
    return browser, ctx


def run_board(ctx, boards, groups, top, period):
    """板块榜模式：BK 官方行情，行业与概念分开出榜。

    分开不是洁癖：混在一张榜里，口播就会说出"今天领涨的是煤炭开采、供销社、
    智能电网"这种把行业和题材混着念的话，观众听不出层次。
    """
    codes = [b["symbol"] for b in boards]
    rows = []
    for i in range(0, len(codes), BK_BATCH):
        try:
            rows.extend(fetch_bk_batch(ctx, codes[i:i + BK_BATCH]))
        except Exception as e:
            print(f"[warn] 板块批次 {i} 失败: {e}", file=sys.stderr)
        time.sleep(0.15)
    have = [r for r in rows if r.get("percent") is not None]
    if not have:
        raise RuntimeError("板块行情全部为空")
    print(f"[board] 拿到 {len(have)} 个板块的官方行情", file=sys.stderr)

    days = PERIOD_DAYS[period]
    out = {"period": period,
           "board_source": "xueqiu_bk_index",
           "board_source_note": "板块层为雪球官方板块指数行情(BK 代码)，当日与区间涨跌幅均为官方值"}

    for g in BK_GROUPS:
        if g["key"] not in groups:
            continue
        seg = [r for r in have if r.get("group") == g["key"]]
        if not seg:
            continue
        scope = "全部"
        if days:
            pool = seg
            if g["key"] == "concept" and len(seg) > CONCEPT_PERIOD_POOL * 2:
                # 概念板块 600+ 个，全量补 K 线太慢：只给当日榜首尾各 60 个补。
                # 榜单因此是"候选内排序"，输出里写明范围，别当成全市场第一。
                byday = sorted(seg, key=lambda r: r["percent"], reverse=True)
                pool = byday[:CONCEPT_PERIOD_POOL] + byday[-CONCEPT_PERIOD_POOL:]
                scope = f"当日榜首尾各 {CONCEPT_PERIOD_POOL} 个候选"
            enrich_period(ctx, pool, days, g["label"])
            seg = [r for r in pool if r.get("period_percent") is not None]

        key = "period_percent" if days else "percent"
        seg.sort(key=lambda r: r[key], reverse=True)
        out[g["key"]] = {
            "label": g["label"],
            "count": len(seg),
            "rank_by": f"近{days}交易日涨跌幅" if days else "当日涨跌幅",
            "rank_scope": scope,
            "gainers": seg[:top],
            "losers": seg[-top:][::-1] if seg else [],
        }
    return out


def run_sector(ctx, boards, keyword, period, ind_code_override, members_max_pages):
    """单板块深挖：官方板块行情 + 区间涨跌幅 + 申万成分股聚合 + 全量成分。"""
    hit = next((b for b in boards
                if b["name"] == keyword or b["symbol"] == keyword.upper()), None)
    if not hit:
        fuzzy = [b for b in boards if keyword in b["name"]]
        if len(fuzzy) == 1:
            hit = fuzzy[0]
        elif fuzzy:
            names = "、".join(f"{b['name']}({b['symbol']})" for b in fuzzy)
            raise SystemExit(f"[error] 「{keyword}」匹配到多个板块，请指明: {names}")
        else:
            raise SystemExit(f"[error] 找不到板块「{keyword}」，"
                             f"跑 --list-sectors 看全部板块名与代码")

    rows = fetch_bk_batch(ctx, [hit["symbol"]])
    if not rows:
        raise RuntimeError(f"{hit['name']}({hit['symbol']}) 官方行情为空")
    detail = rows[0]
    detail["board_source"] = "xueqiu_bk_index"
    print(f"[sector] {detail['name']}({detail['symbol']}) "
          f"当日 {detail['percent']}%", file=sys.stderr)

    days = PERIOD_DAYS[period]
    if days:
        pct, used = fetch_period_percent(ctx, hit["symbol"], days)
        detail["period_percent"] = pct
        detail["period_trading_days"] = used
    # 选板块阶段常同时要周线和月线两个尺度，一次给全，省一趟
    for lbl, d in (("percent_5d", 5), ("percent_20d", 20)):
        if lbl not in detail:
            pct, _ = fetch_period_percent(ctx, hit["symbol"], d)
            detail[lbl] = pct
            time.sleep(0.15)

    # 成分层
    industries = fetch_industries(ctx)
    if ind_code_override:
        code, how = ind_code_override, "manual(--ind-code)"
    else:
        code, how = match_ind_code(detail["name"], industries)
    detail["ind_code"] = code
    detail["ind_code_match"] = how
    if not code:
        detail["members_error"] = (
            f"未能把板块名映射到申万行业码({how})。涨跌家数/资金流/龙头分化这几项缺失，"
            f"可跑 --list-ind 看申万行业码后用 --ind-code 指定。")
        print(f"[warn] {detail['members_error']}", file=sys.stderr)
        return {"sector": detail}

    try:
        members = fetch_members(ctx, code, max_pages=members_max_pages)
        agg = aggregate_members(members)
        agg["members_source"] = "xueqiu_screener_ind_code"
        agg["members_source_note"] = (
            f"成分层按申万行业 {code} 聚合({how})，与板块指数成分口径可能不完全一致；"
            f"percent_equal/percent_weighted 是自算值，报板块涨跌幅请用板块层 percent")
        detail["members_agg"] = agg
        detail["members"] = members
        print(f"[sector] 成分股 {len(members)} 只，涨 {agg['up_count']} "
              f"跌 {agg['down_count']}，主力净流入 {agg['main_net_inflows_yi']} 亿",
              file=sys.stderr)
    except Exception as e:
        detail["members_error"] = f"成分股拉取失败: {e}"
        print(f"[warn] {detail['members_error']}", file=sys.stderr)
    return {"sector": detail}


def scrape(args):
    result = {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "market": "cn",
    }
    with sync_playwright() as p:
        browser, ctx = open_session(p, headless=not args.show)
        try:
            if args.list_ind:
                inds = fetch_industries(ctx)
                result["industries"] = [{"ind_code": i["encode"], "name": i["name"]}
                                        for i in inds]
                return result

            boards = load_bk_boards(ctx, refresh=args.refresh_bk)
            groups = [g.strip() for g in args.boards.split(",") if g.strip()]
            pool = [b for b in boards if bk_group(b["symbol"]) in groups]

            if args.refresh_bk and not (args.sector or args.list_sectors):
                result["refreshed"] = len(boards)
                return result
            if args.list_sectors:
                result["sectors"] = [
                    {"symbol": b["symbol"], "name": b["name"],
                     "group": bk_group(b["symbol"])} for b in pool]
                return result
            if args.sector:
                result.update(run_sector(ctx, boards, args.sector, args.period,
                                         args.ind_code, args.member_pages))
                return result
            result.update(run_board(ctx, pool, groups, args.top, args.period))
            return result
        finally:
            browser.close()


def main():
    ap = argparse.ArgumentParser(
        description="抓板块级数据：官方板块指数行情 + 区间涨跌幅 + 成分股聚合"
                    "(涨跌家数/资金流/龙头分化)，供板块视频的选板块与写稿阶段使用")
    ap.add_argument("--boards", default=",".join(DEFAULT_GROUPS),
                    help="板块口径，逗号分隔: industry 行业板块 / concept 概念题材 / "
                         "gics(与行业重复，默认不取)。默认 industry,concept")
    ap.add_argument("--top", type=int, default=15, help="每栏取多少个(默认15)")
    ap.add_argument("--period", default="day", choices=list(PERIOD_DAYS),
                    help="排序口径: day 当日(默认) / week 近5日 / month 近20日。"
                         "区间值取自板块指数日K，是官方值不是估算")
    ap.add_argument("--sector", default=None,
                    help="只深挖单个板块(板块名如「电网设备」或 BK 码如 BK0093)，"
                         "返回官方行情 + 全量成分股 + 龙头分化素材")
    ap.add_argument("--ind-code", default=None,
                    help="深挖时手动指定申万行业码(如 S6308)，用于板块名映射不出来时")
    ap.add_argument("--member-pages", type=int, default=MEMBER_MAX_PAGES,
                    help=f"深挖时成分股最多翻几页(每页 {MEMBER_PAGE} 只，默认 {MEMBER_MAX_PAGES})")
    ap.add_argument("--list-sectors", action="store_true", help="只列出板块名与 BK 码")
    ap.add_argument("--list-ind", action="store_true", help="只列出申万行业名与行业码")
    ap.add_argument("--refresh-bk", action="store_true", help="重新收割板块代码缓存(慢)")
    ap.add_argument("--out", default=None, help="输出 JSON 路径(默认打印 stdout)")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口(调试)")
    args = ap.parse_args()

    try:
        result = scrape(args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"[error] 板块数据抓取失败: {e}", file=sys.stderr)
        print("[error] 改用 $DESK/scripts/web_search.py 搜"
              "「今日板块涨幅榜 主力资金流 最新」兜底，"
              "并在稿子里标注该数字来自搜索而非接口。", file=sys.stderr)
        sys.exit(1)

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n已写入 {args.out}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
