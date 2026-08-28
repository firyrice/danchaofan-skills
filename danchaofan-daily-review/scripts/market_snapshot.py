#!/usr/bin/env python3
"""
抓取「当日收盘全市场快照」：指数板 + 市场广度(涨跌家数/中位数) + 涨跌停 + 板块涨跌榜，
清洗成一份结构化 JSON，供每日复盘（danchaofan-daily-review）阶段一直接吃。

为什么要新写这个脚本：
    创作 skill 现有的三个雪球脚本全是【个股级】的——xueqiu_quote.py 要先知道代码、
    xueqiu_hot_posts.py 抓单只票的帖子、xueqiu_hot_stocks.py 只给四个榜各 30 只。
    复盘要的是【市场级】口径："今天成交多少万亿、多少只上涨、中位数涨跌多少、
    哪个板块领涨领跌"——这三个脚本都答不了，本脚本补上这一层。

用法:
    python3 market_snapshot.py --out /tmp/snap.json      # 全部板块，写文件
    python3 market_snapshot.py --blocks index,breadth    # 只要指数和广度
    python3 market_snapshot.py --refresh-bk              # 重新收割板块代码缓存
    python3 market_snapshot.py --show                    # 显示浏览器窗口调试

原理:
    与 xueqiu_hot_stocks.py 完全一致——雪球接口受阿里云 WAF 保护，纯 curl 会被
    JS 挑战拦。这里【整段复用】那套方案：Playwright 驱动真实 Chromium 打开一个
    股票页过 WAF 拿匿名 token，再用 ctx.request（复用 WAF cookie、不受 CORS 限制）
    请求各接口。东方财富(push2.eastmoney.com)在本环境不可达，所以板块数据也走雪球。

    用到的接口:
      指数行情    /v5/stock/quote.json?symbol=SH000001&extend=detail
      全市场排序  /v5/stock/screener/quote/list.json?order_by=percent&order=desc&...
      板块行情    /v5/stock/batch/quote.json?symbol=BK0475,BK0448,...

几个口径上的坑（会影响口播怎么说，别绕过）:
    - screener 单页最多返回 30 条（传 size=200 也只给 30），且 type=sh_sz 的 count
      被截在 5000。所以广度【按 sha/kcb/sza 三段分别算再相加】，绕开 5000 截断。
    - 涨跌家数用「在 percent 降序列表上二分找 0 的边界」得到，是精确值不是估算。
    - 市场中位数用【分层抽样】估（跨三段等距取页），是近似值，输出里标了
      approx=true 和样本量；但它的正负号可以用精确的涨跌家数交叉验证。
"""
import argparse
import json
import os
import statistics
import sys
import time

from playwright.sync_api import sync_playwright

# 与 xueqiu_hot_stocks.py 共用同一套会话/反检测逻辑，避免两处各写一版反爬
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
except ImportError:  # 创作 skill 不在预期位置时给出可执行的提示，而不是抛裸异常
    print("[error] 找不到 bilibili-finance-video/scripts/xueqiu_hot_stocks.py，"
          "本脚本复用它的过 WAF 逻辑。请确认创作 skill 与本 skill 在同一仓库，"
          "或设 PYTHONPATH 指向它的 scripts 目录。", file=sys.stderr)
    raise

QUOTE_API = "https://stock.xueqiu.com/v5/stock/quote.json"
SCREENER_API = "https://stock.xueqiu.com/v5/stock/screener/quote/list.json"
BATCH_API = "https://stock.xueqiu.com/v5/stock/batch/quote.json"

PAGE_SIZE = 30          # screener 单页硬上限，传更大也只返回 30
BK_BATCH = 40           # batch/quote 一次问多少个板块代码
BK_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bk_codes.json")

# BK 代码空间实测分成三段不同口径的板块，混在一张榜里会串味，所以分组：
#   BK0001-0104  申万行业板块（"煤炭开采""半导体"这类，复盘报"行业涨幅榜"用这个）
#   BK0400-0999  概念/题材板块（"新能源汽车""稀土永磁""供销社"这类，报"题材榜"用）
#   BK1001-1200  另一套 GICS 风格行业分类，和上面第一段大量重复且带 Ⅲ/Ⅳ 后缀
#                （"建筑产品Ⅲ""建筑产品Ⅳ"会双双挤上榜单造成噪音）→ 默认排除
BK_GROUPS = [
    {"key": "industry", "label": "行业板块", "lo": 1, "hi": 104, "include": True},
    {"key": "concept", "label": "概念题材", "lo": 400, "hi": 999, "include": True},
    {"key": "gics", "label": "GICS行业(与行业板块重复)", "lo": 1000, "hi": 1300,
     "include": False},
]


def bk_group(symbol):
    """BK 代码 → 分组 key；落在空洞里的返回 None。"""
    try:
        n = int(str(symbol)[2:])
    except (TypeError, ValueError):
        return None
    for g in BK_GROUPS:
        if g["lo"] <= n <= g["hi"]:
            return g["key"]
    return None

# 复盘每天必报的指数（口播顺序也大致按这个来）
INDICES = [
    ("SH000001", "上证指数"),
    ("SZ399001", "深证成指"),
    ("SZ399006", "创业板指"),
    ("SH000688", "科创50"),
    ("SH000300", "沪深300"),
    ("SH000905", "中证500"),
    ("SH000852", "中证1000"),
]

# 广度分段：三段互不重叠、各自 count 都远小于 5000，相加即全 A 口径。
# （实测 sza 的 2898 已含创业板 1404，所以不再单列 cyb，否则会重复计数。）
SEGMENTS = [
    {"type": "sha", "label": "沪市主板", "limit_pct": 10.0},
    {"type": "kcb", "label": "科创板", "limit_pct": 20.0},
    {"type": "sza", "label": "深市(含创业板)", "limit_pct": 10.0},
]


# --------------------------------------------------------------------------- #
#  基础取数
# --------------------------------------------------------------------------- #
def fetch_page(ctx, seg_type, page, order="desc", order_by="percent"):
    """取 screener 的一页，返回 (count, [item...])。"""
    url = (f"{SCREENER_API}?order_by={order_by}&order={order}"
           f"&page={page}&size={PAGE_SIZE}&market=CN&type={seg_type}")
    status, body, raw = ctx_fetch_json(ctx, url)
    if status != 200 or not body:
        raise RuntimeError(f"screener {seg_type} page={page} status={status} {raw[:80]}")
    data = body.get("data") or {}
    return data.get("count"), (data.get("list") or [])


def pct_of(item):
    """取一条记录的当日涨跌幅；停牌等情况可能为 None。"""
    v = item.get("percent")
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
#  1. 指数板
# --------------------------------------------------------------------------- #
def fetch_indices(ctx):
    """逐个拿指数行情。单个指数失败不影响其它（带 error 字段返回）。"""
    rows = []
    for symbol, label in INDICES:
        try:
            status, body, raw = ctx_fetch_json(
                ctx, f"{QUOTE_API}?symbol={symbol}&extend=detail")
            if status != 200 or not body:
                raise RuntimeError(f"status={status} {raw[:80]}")
            q = ((body.get("data") or {}).get("quote") or {})
            rows.append({
                "symbol": symbol,
                "name": q.get("name") or label,
                "current": round_or_none(q.get("current")),
                "percent": round_or_none(q.get("percent")),
                "amount_yi": humanize_cap(q.get("amount")),      # 成交额(亿)
                "turnover_rate": round_or_none(q.get("turnover_rate")),
                "timestamp": q.get("timestamp"),
            })
        except Exception as e:
            rows.append({"symbol": symbol, "name": label, "error": str(e)})
        finally:
            time.sleep(0.15)
    return rows


def total_turnover(index_rows):
    """沪深两市成交额合计 —— 复盘开头必报的那个"今天成交 X 万亿"。

    口径说明（实测确认，别改成"把所有指数成交额相加"）：指数行情返回的 amount 是
    该指数所在【整个市场】的成交额，不是成分股的。实测同一天 深证成指(SZ399001) 与
    深证综指(SZ399106) 返回完全相同的 amount（都是深市全市场），所以只取
    上证 + 深证成指两个就是沪深两市合计，多加一个就会重复计数。
    """
    idx = {r.get("symbol"): r for r in index_rows if isinstance(r, dict)}
    sh = (idx.get("SH000001") or {}).get("amount_yi")
    sz = (idx.get("SZ399001") or {}).get("amount_yi")
    if sh is None or sz is None:
        return None
    total_yi = sh + sz
    return {
        "sh_amount_yi": round(sh, 2),
        "sz_amount_yi": round(sz, 2),
        "total_amount_yi": round(total_yi, 2),
        "total_wanyi": round(total_yi / 1e4, 2),   # 万亿，口播直接念这个
    }


# --------------------------------------------------------------------------- #
#  2. 市场广度（精确涨跌家数 + 抽样中位数 + 成交额汇总）
# --------------------------------------------------------------------------- #
def find_boundary(ctx, seg_type, total_pages, predicate):
    """在 percent 降序的全市场列表上二分，找出 predicate 为真的记录条数。

    列表按 percent 降序，所以"percent > 0"这类条件在列表上是一个前缀。
    二分定位该前缀落在哪一页，再在页内精确数——因此结果是精确值，不是页级估算。
    predicate 接收 float 涨跌幅，返回 bool。
    """
    lo, hi = 1, total_pages
    target_page = total_pages
    while lo <= hi:
        mid = (lo + hi) // 2
        _, items = fetch_page(ctx, seg_type, mid)
        pcts = [p for p in (pct_of(i) for i in items) if p is not None]
        if not pcts:
            hi = mid - 1
            continue
        if predicate(pcts[-1]):      # 整页都满足 → 前缀更长，往后找
            lo = mid + 1
        else:
            target_page = mid        # 前缀在本页内结束
            hi = mid - 1
    _, items = fetch_page(ctx, seg_type, target_page)
    in_page = 0
    for it in items:
        p = pct_of(it)
        if p is not None and predicate(p):
            in_page += 1
        else:
            break
    return (target_page - 1) * PAGE_SIZE + in_page


def fetch_breadth(ctx, sample_pages=6):
    """逐段算精确涨/平/跌家数；顺带抽样估中位数、汇总分段成交额。"""
    segs, sample_pcts = [], []
    for seg in SEGMENTS:
        try:
            total, first_items = fetch_page(ctx, seg["type"], 1)
            if not total:
                raise RuntimeError("count 为空")
            total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

            # 涨 = percent > 0 的前缀长度；涨+平 = percent >= 0 的前缀长度
            up = find_boundary(ctx, seg["type"], total_pages, lambda p: p > 0)
            up_flat = find_boundary(ctx, seg["type"], total_pages, lambda p: p >= 0)
            flat, down = up_flat - up, total - up_flat

            # 涨停/跌停：涨跌幅贴着该板涨跌停限制（留 0.2 个点容差给四舍五入）
            thr = seg["limit_pct"] - 0.2
            limitup = find_boundary(ctx, seg["type"], total_pages, lambda p: p >= thr)
            limitdown_from_top = find_boundary(
                ctx, seg["type"], total_pages, lambda p: p > -thr)
            limitdown = total - limitdown_from_top

            # 分层抽样：跨全段等距取若干页，攒中位数样本 + 顺带汇总成交额
            step = max(1, total_pages // sample_pages)
            amount_sum, sampled = 0.0, 0
            for pno in range(1, total_pages + 1, step):
                items = first_items if pno == 1 else fetch_page(ctx, seg["type"], pno)[1]
                for it in items:
                    p = pct_of(it)
                    if p is not None:
                        sample_pcts.append(p)
                        sampled += 1
                    try:
                        amount_sum += float(it.get("amount") or 0)
                    except (TypeError, ValueError):
                        pass

            segs.append({
                "segment": seg["type"], "label": seg["label"], "total": total,
                "up": up, "flat": flat, "down": down,
                "limit_up": limitup, "limit_down": limitdown,
                "limit_pct": seg["limit_pct"], "sampled_stocks": sampled,
            })
        except Exception as e:
            segs.append({"segment": seg["type"], "label": seg["label"], "error": str(e)})

    ok = [s for s in segs if "error" not in s]
    agg = {
        "segments": segs,
        "total": sum(s["total"] for s in ok) or None,
        "up": sum(s["up"] for s in ok) or None,
        "flat": sum(s["flat"] for s in ok) or None,
        "down": sum(s["down"] for s in ok) or None,
        "limit_up": sum(s["limit_up"] for s in ok) or None,
        "limit_down": sum(s["limit_down"] for s in ok) or None,
        "counts_are_exact": bool(ok),
    }
    if sample_pcts:
        agg["median_percent"] = round(statistics.median(sample_pcts), 2)
        agg["median_is_approx"] = True
        agg["median_sample_size"] = len(sample_pcts)
        # 用精确家数交叉验证抽样中位数的正负号，对不上就标出来别硬用
        if agg["total"]:
            expect_positive = agg["up"] > agg["total"] / 2
            agg["median_sign_consistent"] = (
                expect_positive == (agg["median_percent"] > 0))
    return agg


# --------------------------------------------------------------------------- #
#  3. 板块涨跌榜
# --------------------------------------------------------------------------- #
def fetch_bk_batch(ctx, codes):
    """一次问一批板块代码，返回 [{symbol,name,percent,...}]。"""
    url = f"{BATCH_API}?symbol={','.join(codes)}"
    status, body, raw = ctx_fetch_json(ctx, url)
    if status != 200 or not body:
        raise RuntimeError(f"batch status={status} {raw[:80]}")
    rows = []
    for it in ((body.get("data") or {}).get("items") or []):
        q = it.get("quote") or {}      # 无效代码这里是 None，跳过
        if not q.get("name"):
            continue
        rows.append({
            "symbol": q.get("symbol"), "name": q.get("name"),
            "group": bk_group(q.get("symbol")),
            "percent": round_or_none(q.get("percent")),
            "current": round_or_none(q.get("current")),
            "amount_yi": humanize_cap(q.get("amount")),
        })
    return rows


def refresh_bk_cache(ctx, scan_max=1200):
    """扫一遍 BK 代码空间，把有名字的板块存成缓存，供日常直接用。

    注意：BK 代码空间是【稀疏且有大段空洞】的，不能"连续几批空就提前收工"。
    实测 BK0001-0104 是申万行业板块，之后 BK0105-0436 整段是空的，
    BK0437+ 又是概念板块（白酒概念、新能源汽车这些）。早停会把概念板块整批丢掉，
    所以这里整段扫完不提前退出。这个函数只在 --refresh-bk 时跑（结果进缓存），
    日常复盘直接读缓存，慢一点无所谓。
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
    with open(BK_CACHE, "w", encoding="utf-8") as f:
        json.dump({"updated_at": time.strftime("%Y-%m-%d"), "count": len(found),
                   "boards": found}, f, ensure_ascii=False, indent=2)
    print(f"[bk] 已写入 {BK_CACHE}，共 {len(found)} 个板块", file=sys.stderr)
    return [b["symbol"] for b in found]


def load_bk_codes(ctx, refresh=False):
    if not refresh and os.path.exists(BK_CACHE):
        with open(BK_CACHE, "r", encoding="utf-8") as f:
            return [b["symbol"] for b in (json.load(f).get("boards") or [])]
    return refresh_bk_cache(ctx)


def fetch_sectors(ctx, top=10, refresh=False):
    """拉全部板块行情，【按口径分开】各出领涨/领跌榜。

    分开是必要的，不是洁癖：行业板块和概念题材混在一张榜里，口播就会说出
    "今天领涨的是软件开发、计算机、供销社、煤炭开采"这种把行业和题材混着念的话，
    观众听不出层次。分开后可以按复盘的自然语序讲："行业上煤炭领涨，题材上供销社最猛。"
    """
    codes = load_bk_codes(ctx, refresh=refresh)
    if not codes:
        raise RuntimeError("没有可用的板块代码（缓存为空且收割失败）")
    rows = []
    for i in range(0, len(codes), BK_BATCH):
        try:
            rows.extend(fetch_bk_batch(ctx, codes[i:i + BK_BATCH]))
        except Exception as e:
            print(f"[warn] 板块批次 {i} 失败: {e}", file=sys.stderr)
        time.sleep(0.15)

    out = {"count": len([r for r in rows if r.get("percent") is not None])}
    for g in BK_GROUPS:
        if not g["include"]:
            continue
        have = [r for r in rows
                if r.get("group") == g["key"] and r.get("percent") is not None]
        have.sort(key=lambda r: r["percent"], reverse=True)
        out[g["key"]] = {
            "label": g["label"],
            "count": len(have),
            "gainers": have[:top],
            "losers": list(reversed(have[-top:])) if have else [],
        }
    return out


# --------------------------------------------------------------------------- #
#  4. 会话编排
# --------------------------------------------------------------------------- #
def scrape(blocks, top, refresh_bk, headless=True):
    exe = find_chromium()
    launch_kwargs = {"headless": headless,
                     "args": ["--disable-blink-features=AutomationControlled"]}
    if exe:
        launch_kwargs["executable_path"] = exe
        print(f"[info] 使用浏览器: {exe}", file=sys.stderr)

    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(user_agent=UA, locale="zh-CN",
                                  viewport={"width": 1440, "height": 900})
        ctx.add_init_script(STEALTH_JS)
        pg = ctx.new_page()
        try:
            pg.goto("https://xueqiu.com/S/SH000001",
                    wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[warn] 探针页导航: {e}", file=sys.stderr)
        for _ in range(15):
            pg.wait_for_timeout(1000)
            if any(c["name"] == "xq_a_token" for c in ctx.cookies()):
                print("[info] token 就绪", file=sys.stderr)
                break
        else:
            print("[warn] 未拿到 xq_a_token，接口可能仍被拦截", file=sys.stderr)

        # 每块独立 try：一块崩掉照常返回其它块（带 error 字段），别让整条流程停摆
        if "index" in blocks:
            try:
                out["indices"] = fetch_indices(ctx)
                out["turnover"] = total_turnover(out["indices"])
                t = out["turnover"] or {}
                print(f"[block] 指数: {len(out['indices'])} 条，"
                      f"两市成交 {t.get('total_wanyi')} 万亿", file=sys.stderr)
            except Exception as e:
                out["indices"] = {"error": str(e)}
                print(f"[warn] 指数块失败: {e}", file=sys.stderr)
        if "breadth" in blocks:
            try:
                out["breadth"] = fetch_breadth(ctx)
                b = out["breadth"]
                print(f"[block] 广度: 涨{b.get('up')}/平{b.get('flat')}/跌{b.get('down')}"
                      f" 中位数≈{b.get('median_percent')}", file=sys.stderr)
            except Exception as e:
                out["breadth"] = {"error": str(e)}
                print(f"[warn] 广度块失败: {e}", file=sys.stderr)
        if "sectors" in blocks:
            try:
                out["sectors"] = fetch_sectors(ctx, top=top, refresh=refresh_bk)
                print(f"[block] 板块: {out['sectors']['count']} 个", file=sys.stderr)
            except Exception as e:
                out["sectors"] = {"error": str(e)}
                print(f"[warn] 板块块失败: {e}", file=sys.stderr)

        browser.close()
    return out


def main():
    ap = argparse.ArgumentParser(
        description="当日收盘全市场快照：指数 + 广度(涨跌家数/中位数) + 涨跌停 + 板块榜")
    ap.add_argument("--blocks", default="index,breadth,sectors",
                    help="逗号分隔: index,breadth,sectors (默认全部)")
    ap.add_argument("--top", type=int, default=10, help="板块榜领涨/领跌各取多少个(默认10)")
    ap.add_argument("--refresh-bk", action="store_true",
                    help="重新收割板块代码缓存 bk_codes.json")
    ap.add_argument("--out", default=None, help="输出 JSON 路径(默认打到 stdout)")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口(调试)")
    args = ap.parse_args()

    blocks = [b.strip() for b in args.blocks.split(",")
              if b.strip() in ("index", "breadth", "sectors")]
    if not blocks:
        print("[error] --blocks 无有效值，可选: index,breadth,sectors", file=sys.stderr)
        sys.exit(2)

    data = scrape(blocks, args.top, args.refresh_bk, headless=not args.show)
    result = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
              "trade_date": time.strftime("%Y-%m-%d"), **data}
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n已写入 {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
