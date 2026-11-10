#!/usr/bin/env python3
"""
证据截图：把口播稿里引用的财报、新闻/研报、行情页、雪球原帖等"在视频里有展示价值"的证据，
自动打开原网页 / 原 PDF，高亮关键词，截图，连同原链接一起归档到视频的 参考资料/证据截图/。

用法:
    # 批量（推荐）：按证据清单逐条截图
    python3 evidence_capture.py --manifest 证据清单_输入.json --out-dir "$DIR/参考资料/证据截图"

    # 截之前先查一遍清单里每个链接的权威等级
    python3 evidence_capture.py --manifest 证据清单_输入.json --out-dir "$DIR/参考资料/证据截图" --check

    # 只重跑其中几条 / 覆盖已有截图
    python3 evidence_capture.py --manifest ... --out-dir ... --only 03,07 --force

    # 单条：直接给链接（结果追加进同一份证据清单）
    python3 evidence_capture.py --out-dir ... --url "https://..." --name 期货单日暴跌 \
        --highlight "11.79%" --highlight "最大单日跌幅" --kind 新闻 --quote "稿中原句"

证据清单（manifest）格式:
    {
      "project": "赣锋锂业 · 锂价腰斩……",
      "items": [
        {
          "id": "01",                       # 可省略，按顺序自动编号
          "name": "三季报主要会计数据",       # 短名，进文件名
          "kind": "财报",                    # 财报/公告/政策/行情/研报/新闻/数据
          "url": "http://static.cninfo.com.cn/....PDF",
          "alt_urls": ["..."],               # 可选：原链接打不开/被拦截时依次尝试
          "type": "auto",                    # auto(默认，按扩展名判断)/web/pdf
          "source": "赣锋锂业2026年三季报（巨潮资讯）",
          "quote": "稿中对应的原句",
          "highlight": ["7.55", "50.12"],    # 要高亮的原文字面（须与原文写法一致）
          "pages": [2],                      # 可选，仅 PDF：限定页码（从 1 开始）
          "selector": "#chart",              # 可选，仅网页：额外截这个元素
          "wait": 5,                         # 可选，网页加载后等待秒数
          "full_page": false,                # 可选，网页额外存整页长图
          "tier": "B", "tier_reason": "..."  # 可选：域名不在名单、但人工确认是权威出处时才写
        }
      ],
      "unsourced": [                         # 稿中有、但找不到 A/B 级出处的说法（不截图，只进清单提醒）
        {"quote": "稿中原句", "current_source": "目前只有百家号转载", "suggestion": "改稿或补权威出处"}
      ]
    }

信源权威性（脚本按域名自动判，见 TIER_* 名单）:
    A 官方原文   巨潮/交易所/港交所披露易、*.gov.cn（财政部、税务总局、证监会、地方政府）、期货交易所
    B 权威媒体   新华社/人民网/央视/中新社/经济日报、四大证券报、第一财经/财新/21世纪/界面/澎湃/每经/财联社、
                 券商研报平台（新浪研报中心、东方财富研报中心）、SMM/Mysteel
    C 不收       雪球、股吧、百家号、东方财富号、网易号、搜狐号、微博、头条、知乎、公众号、腾讯新闻转载等
    未分级       默认不截；人工确认后在条目里写 tier + tier_reason 放行
    C 级和未分级的链接会被跳过，状态记为"🚫 拒截"。先跑 --check 看清单里每个链接的等级。

产出（out-dir 下）:
    NN_<名>_首屏.png        网页首屏（带标题、来源、日期，用于"新闻引文"镜头）
    NN_<名>_高亮.png        关键词所在段落的高亮截图（多处相距较远时会有 _高亮2、_高亮3）
    NN_<名>_第X页.png       PDF 整页（已高亮）
    NN_<名>_高亮_pX.png     PDF 关键词所在区域裁切
    原文/NN_<名>.pdf        PDF 原文留档
    证据清单.md / 证据清单.json   索引：稿中对应句、来源、原链接、截图、抓取时间、状态

依赖:
    playwright（与 web_fetch.py 共用 Chromium）、requests、pymupdf（pip install pymupdf）
"""
import argparse
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from web_fetch import STEALTH_JS, UA, find_chromium, goto_robust  # noqa: E402

VIEWPORT = {"width": 1440, "height": 900}
SCALE = 2                      # 截图按 2 倍像素输出，成片放大不糊
MAX_HITS_PER_KW = 3            # 每个关键词最多高亮几处
CLUSTER_GAP = 700              # 两处高亮纵向相距超过这个像素，就拆成两张截图
MAX_CLUSTERS = 3
BLOCK_HINTS = ("安全验证", "验证码", "访问被拒绝", "Access Denied", "请完成验证", "滑动验证")

# ---------------- 信源权威性分级 ----------------
# A 官方原文：公司公告/财报、交易所、监管和政府部门、期货交易所
# B 权威媒体与研报：官方媒体、证券报、主流财经媒体、券商研报平台、权威行业数据商
# C 不收：自媒体、社区、转载聚合（雪球、股吧、百家号、财富号、网易号、搜狐号、微博、公众号……）
# 其余域名一律"未分级"，默认不截；确认是权威出处后在清单里写 tier + tier_reason 放行。
TIER_A = (
    "cninfo.com.cn", "sse.com.cn", "szse.cn", "bse.cn", "hkexnews.hk", "hkex.com.hk",
    ".gov.cn", "gfex.com.cn", "shfe.com.cn", "dce.com.cn", "czce.com.cn", "cffex.com.cn", "ine.cn",
    "sec.gov",
)
TIER_B = (
    # 官方媒体
    "xinhuanet.com", "news.cn", "cnfin.com", "people.com.cn", "cctv.com", "cntv.cn", "cnr.cn",
    "chinanews.com.cn", "chinanews.com", "ce.cn", "gmw.cn", "chinadaily.com.cn", "jjckb.cn", "financialnews.com.cn",
    # 证券报
    "stcn.com", "cs.com.cn", "cnstock.com", "zqrb.cn",
    # 主流财经媒体
    "yicai.com", "caixin.com", "21jingji.com", "eeo.com.cn", "jiemian.com", "thepaper.cn", "nbd.com.cn",
    "cls.cn", "bjnews.com.cn", "chinatimes.net.cn", "cb.com.cn", "lifeweek.com.cn",
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "nikkei.com",
    # 权威行业数据商
    "smm.cn", "mysteel.com",
)
# 研报平台：按 域名+路径 判断（同一域名下其他页面不一定权威）
TIER_B_PATHS = (
    ("stock.finance.sina.com.cn", "/stock/go.php/vReport_Show"),
    ("data.eastmoney.com", "/report/"),
    ("robo.datayes.com", "/"),
)
TIER_C = (
    "xueqiu.com", "guba.eastmoney.com", "gubaformgr.eastmoney.com", "caifuhao.eastmoney.com",
    "baijiahao.baidu.com", "mbd.baidu.com", "baike.baidu.com", "tieba.baidu.com",
    "weibo.com", "weibo.cn", "toutiao.com", "zhihu.com", "bilibili.com", "douyin.com", "xiaohongshu.com",
    "mp.weixin.qq.com", "new.qq.com", "news.qq.com", "k.sina.com.cn", "k.sina.cn", "guba.sina",
    "mp.sohu.com", "chejiahao.autohome.com.cn", "yiche.com", "9fzt.com", "taobao.com",
)
TIER_C_PATHS = (                         # 路径里包含即命中
    ("163.com", "/dy/"),                 # 网易号
    ("sohu.com", "/a/"),                 # 搜狐号
    ("sina.com.cn", "/articles/"),       # 新浪看点
    ("sina.com.cn", "/stockzmt/"),       # 新浪财经自媒体
    ("sina.com.cn", "/wm/"),             # 新浪财经头条自媒体
)
TIER_LABEL = {"A": "A 官方原文", "B": "B 权威媒体/研报", "C": "C 自媒体/社区（不收）", "U": "未分级（需人工确认）"}


def classify(url):
    pr = urlparse(url)
    host, path = pr.netloc.lower(), pr.path
    def hit(names):
        return any(host == n.lstrip(".") or host.endswith("." + n.lstrip(".")) or (n.startswith(".") and host.endswith(n))
                   for n in names)
    def hit_path(pairs, contains=False):
        return any((host == h or host.endswith("." + h)) and ((pp in path) if contains else path.startswith(pp))
                   for h, pp in pairs)
    if hit(TIER_C) or hit_path(TIER_C_PATHS, contains=True):
        return "C"
    if hit(TIER_A):
        return "A"
    if hit(TIER_B) or hit_path(TIER_B_PATHS):
        return "B"
    return "U"


def resolve_tier(item, url):
    """返回 (tier, 说明)。C 级永远不放行；未分级的只有清单里写了 tier+tier_reason 才放行。"""
    auto = classify(url)
    if auto == "C":
        return "C", "自媒体/社区/转载平台，没有引用价值"
    if auto in ("A", "B"):
        return auto, ""
    if item.get("tier") in ("A", "B") and item.get("tier_reason"):
        return item["tier"], f"人工确认：{item['tier_reason']}"
    return "U", "域名不在权威名单。确认是官方原文/权威媒体/研报后，在清单里写 tier 和 tier_reason"

HIGHLIGHT_JS = """
({keywords, maxPerKw}) => {
  const style = 'background:#ffd400 !important;color:#000 !important;padding:0 2px;'
              + 'border-radius:2px;box-shadow:0 0 0 2px #ff3b30;';
  const out = {};
  for (const kw of keywords) {
    let count = 0;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        if (!n.nodeValue || !n.nodeValue.includes(kw)) return NodeFilter.FILTER_REJECT;
        const p = n.parentElement;
        if (!p || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA'].includes(p.tagName)) return NodeFilter.FILTER_REJECT;
        if (p.closest('mark[data-evi]')) return NodeFilter.FILTER_REJECT;
        const st = getComputedStyle(p);
        if (st.display === 'none' || st.visibility === 'hidden') return NodeFilter.FILTER_REJECT;
        const r = p.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    let n;
    while ((n = walker.nextNode())) nodes.push(n);
    for (const node of nodes) {
      if (count >= maxPerKw) break;
      const idx = node.nodeValue.indexOf(kw);
      if (idx < 0) continue;
      try {
        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + kw.length);
        const mark = document.createElement('mark');
        mark.setAttribute('data-evi', '1');
        mark.style.cssText = style;
        range.surroundContents(mark);
        count++;
      } catch (e) {}
    }
    out[kw] = count;
  }
  return out;
}
"""

# 关键词还没出现在页面上时，点"展开/查看更多"类按钮（雪球评论区、折叠正文），再滚一轮
EXPAND_JS = r"""
() => {
  const words = ['展开查看更多', '查看更多评论', '展开全文', '阅读全文', '展开更多', '加载更多'];
  const here = location.href.split('#')[0];
  let n = 0;
  for (const el of document.querySelectorAll('a,button,span,div')) {
    const t = (el.innerText || '').trim();
    if (!t || t.length > 12) continue;
    const hit = words.some(w => t.includes(w)) || t === '展开' || /^查看(\d+条)?回复/.test(t);
    if (!hit || el.children.length > 2 || el.dataset.eviClicked) continue;
    // 只点页内展开，不点会跳走的链接（跳走就截不到原帖了）
    const a = el.closest('a[href]');
    if (a) {
      const h = a.getAttribute('href') || '';
      if (!(h.startsWith('#') || h.startsWith('javascript') || a.href.split('#')[0] === here)) continue;
    }
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    try { el.dataset.eviClicked = '1'; el.click(); n++; } catch (e) {}
  }
  return n;
}
"""


def reveal_keywords(pg, kws, rounds=5):
    """逐轮展开 + 滚到底，直到所有关键词都出现在页面文字里或轮数用完。"""
    for _ in range(rounds):
        text = pg.evaluate("() => document.body.innerText")
        if all(k in text for k in kws):
            return
        url_before = pg.url
        clicked = pg.evaluate(EXPAND_JS)
        pg.wait_for_timeout(800)
        if pg.url.split("#")[0] != url_before.split("#")[0]:
            log("展开按钮跳走了页面，退回原页")
            pg.go_back()
            pg.wait_for_timeout(3000)
            return
        for _ in range(4):
            pg.evaluate("window.scrollBy(0, innerHeight)")
            pg.wait_for_timeout(500)
        pg.wait_for_timeout(1000)
        if not clicked:
            text = pg.evaluate("() => document.body.innerText")
            if all(k in text for k in kws):
                return


# 截首屏前：只藏大面积遮罩（登录弹窗、全屏广告），保留顶部导航（显示站点身份）
HIDE_OVERLAYS_JS = """
() => {
  const vw = innerWidth, vh = innerHeight;
  let n = 0;
  for (const el of document.querySelectorAll('body *')) {
    const st = getComputedStyle(el);
    if (st.position !== 'fixed') continue;
    const r = el.getBoundingClientRect();
    if (r.width * r.height > vw * vh * 0.25) { el.style.setProperty('display', 'none', 'important'); n++; }
  }
  // 弹窗常把滚动锁在 html/body 上。只解 html 的锁；body 设 visible，
  // 不能设 auto：html/body 高度 100% 的页面会让 body 变成滚动容器，window.scrollTo 就失效了。
  document.documentElement.style.setProperty('overflow', 'auto', 'important');
  document.body.style.setProperty('overflow', 'visible', 'important');
  return n;
}
"""

# 截高亮片段前：所有悬浮/吸顶元素都藏掉，避免盖住正文
HIDE_FIXED_JS = """
() => {
  let n = 0;
  for (const el of document.querySelectorAll('body *')) {
    const pos = getComputedStyle(el).position;
    if (pos === 'fixed' || pos === 'sticky') { el.style.setProperty('display', 'none', 'important'); n++; }
  }
  return n;
}
"""

# 按纵向距离把高亮聚成几簇，每簇算一个带上下文的裁切框（页面坐标）
CLUSTER_JS = """
({gap, maxClusters, maxH}) => {
  const marks = [...document.querySelectorAll('mark[data-evi]')];
  if (!marks.length) return [];
  const docW = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
  const docH = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
  const boxes = marks.map(m => {
    const blk = m.closest('p,li,tr,blockquote,h1,h2,h3,h4,dd,pre') || m.parentElement;
    let r = blk.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) r = m.getBoundingClientRect();
    return {top: r.top + scrollY, bottom: r.bottom + scrollY, left: r.left + scrollX, right: r.right + scrollX,
            ok: r.width >= 4 && r.height >= 4};
  }).filter(b => b.ok && b.top >= 0).sort((a, b) => a.top - b.top);
  const clusters = [];
  for (const b of boxes) {
    const last = clusters[clusters.length - 1];
    if (last && b.top - last.bottom < gap) {
      last.top = Math.min(last.top, b.top); last.bottom = Math.max(last.bottom, b.bottom);
      last.left = Math.min(last.left, b.left); last.right = Math.max(last.right, b.right);
    } else clusters.push({...b});
  }
  return clusters.slice(0, maxClusters).map(c => {
    let x = c.left - 32, w = (c.right - c.left) + 64;
    if (w < 760) { x -= (760 - w) / 2; w = 760; }
    x = Math.max(0, x); w = Math.min(w, docW - x);
    let y = Math.max(0, c.top - 140);
    let h = Math.min((c.bottom + 140) - y, maxH, docH - y);
    return {x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h)};
  }).filter(b => b.width > 20 && b.height > 20);
}
"""


def log(msg):
    print(f"[evidence] {msg}", file=sys.stderr)


def safe_name(s):
    s = re.sub(r'[\\/:*?"<>|（）()\s，,。；;、]+', "_", s.strip())
    return s.strip("_")[:40] or "证据"


def detect_type(item):
    t = (item.get("type") or "auto").lower()
    if t in ("web", "pdf"):
        return t
    return "pdf" if urlparse(item["url"]).path.lower().endswith(".pdf") else "web"


def referer_for(url):
    host = urlparse(url).netloc
    if "xueqiu.com" in host:
        return "https://www.xueqiu.com"
    if "eastmoney.com" in host:
        return "https://www.eastmoney.com"
    return None


# ---------------- 网页 ----------------

def capture_web(ctx, item, url, out_dir, prefix, warmed):
    rec = {"used_url": url, "files": [], "hits": {}}
    ref = referer_for(url)
    pg = ctx.new_page()
    try:
        if ref and ref not in warmed:
            log(f"先访问 {ref} 获取 cookie")
            try:
                goto_robust(pg, ref, timeout=20000, retries=0)
                pg.wait_for_timeout(3000)
            except Exception as e:
                log(f"referer 访问异常（可忽略）: {e}")
            warmed.add(ref)

        log(f"打开 {url}")
        goto_robust(pg, url)
        pg.wait_for_timeout(int(item.get("wait", 5)) * 1000)
        # 逐段滚到底触发懒加载（评论区、图片），再回顶部
        for _ in range(6):
            pg.evaluate("window.scrollBy(0, Math.max(innerHeight, document.body.scrollHeight / 6))")
            pg.wait_for_timeout(500)
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(800)

        rec["final_url"] = pg.url
        rec["page_title"] = (pg.title() or "").strip()
        body_len = pg.evaluate("() => (document.body && document.body.innerText || '').length")
        if body_len < 300 or any(h in rec["page_title"] for h in BLOCK_HINTS):
            raise RuntimeError(f"疑似被拦截或空页（标题「{rec['page_title']}」，正文 {body_len} 字）")

        pg.evaluate(HIDE_OVERLAYS_JS)
        top = os.path.join(out_dir, f"{prefix}_首屏.png")
        pg.screenshot(path=top, animations="disabled", timeout=45000)
        rec["files"].append(os.path.basename(top))

        kws = item.get("highlight") or []
        if kws:
            reveal_keywords(pg, kws)
            rec["hits"] = pg.evaluate(HIGHLIGHT_JS, {"keywords": kws, "maxPerKw": MAX_HITS_PER_KW})
            pg.evaluate(HIDE_FIXED_JS)
            boxes = pg.evaluate(CLUSTER_JS, {"gap": CLUSTER_GAP, "maxClusters": MAX_CLUSTERS,
                                             "maxH": VIEWPORT["height"] - 100})
            n, problems = 0, []
            for box in boxes:
                # 把这一簇滚进视口再按视口坐标裁切。不用 full_page：整页截图会把视口拉到全高，
                # 有些页面（如税务局政策库）会因此重排，裁切框就对不上正文了。
                pg.evaluate(f"window.scrollTo(0, {max(0, box['y'] - 80)})")
                pg.wait_for_timeout(700)
                sy = pg.evaluate("() => scrollY")
                vh = VIEWPORT["height"]
                top = max(0, box["y"] - sy)
                clip = {"x": box["x"], "y": top, "width": box["width"], "height": min(box["height"], vh - top)}
                if clip["height"] < 40:
                    problems.append(f"第 {n + 1} 处高亮滚不进画面，没截到")
                    continue
                path = os.path.join(out_dir, f"{prefix}_高亮{'' if n == 0 else n + 1}.png")
                try:
                    pg.screenshot(path=path, clip=clip, animations="disabled", timeout=45000)
                except Exception as e:
                    log(f"一处高亮裁切失败，跳过: {str(e).splitlines()[0][:120]}")
                    continue
                visible = pg.evaluate(MARK_IN_CLIP_JS, clip)
                ink = ink_ratio(path)
                if not visible or (ink is not None and ink < 0.01):
                    problems.append(f"{os.path.basename(path)}：" + ("高亮不在画面里" if not visible else "截图近乎空白"))
                n += 1
                rec["files"].append(os.path.basename(path))
            if not n:
                problems.append("关键词命中了，但没截到任何高亮图")
            if problems:
                rec["crop_problems"] = problems

        if item.get("selector"):
            el = pg.query_selector(item["selector"])
            if el:
                el.scroll_into_view_if_needed()
                pg.wait_for_timeout(800)
                path = os.path.join(out_dir, f"{prefix}_元素.png")
                el.screenshot(path=path)
                rec["files"].append(os.path.basename(path))
            else:
                rec["note"] = f"选择器 {item['selector']} 未找到元素"

        if item.get("full_page"):
            path = os.path.join(out_dir, f"{prefix}_整页.png")
            pg.screenshot(path=path, full_page=True)
            rec["files"].append(os.path.basename(path))
    finally:
        pg.close()
    return rec


MARK_IN_CLIP_JS = """
(c) => [...document.querySelectorAll('mark[data-evi]')].some(m =>
  // 关键词可能折成两行，逐行检查，任一行落在裁切框里且没被别的元素盖住就算看得到
  [...m.getClientRects()].some(r => {
    if (r.width === 0 || r.height === 0) return false;
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    if (cx < c.x || cx > c.x + c.width || cy < c.y || cy > c.y + c.height) return false;
    const el = document.elementFromPoint(cx, cy);
    return !!el && (el === m || m.contains(el) || el.contains(m));
  })
)
"""


def ink_ratio(path):
    """非白像素占比，用来发现空白截图。读不了就返回 None。"""
    try:
        import pymupdf
        pix = pymupdf.Pixmap(path)
        if pix.alpha:
            pix = pymupdf.Pixmap(pix, 0)
        data, n = pix.samples, pix.n
        step = max(1, (pix.width * pix.height) // 40000)
        total = dark = 0
        for i in range(0, pix.width * pix.height, step):
            px = data[i * n:(i * n) + 3]
            total += 1
            dark += min(px) < 235
        return dark / total if total else None
    except Exception:
        return None


# ---------------- PDF ----------------

def capture_pdf(item, url, out_dir, prefix):
    import pymupdf as fitz

    rec = {"used_url": url, "final_url": url, "files": [], "hits": {}}
    raw_dir = os.path.join(out_dir, "原文")
    os.makedirs(raw_dir, exist_ok=True)
    pdf_path = os.path.join(raw_dir, f"{prefix}.pdf")
    log(f"下载 {url}")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=90)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise RuntimeError("下载内容不是 PDF")
    with open(pdf_path, "wb") as f:
        f.write(r.content)
    rec["files"].append(f"原文/{prefix}.pdf")

    doc = fitz.open(pdf_path)
    rec["page_title"] = (doc.metadata or {}).get("title") or ""
    pages = item.get("pages") or list(range(1, len(doc) + 1))
    kws = item.get("highlight") or []

    # 每个关键词取它最先出现的页（指定 pages 时在这些页里找）
    hit_pages = {}
    for kw in kws:
        rec["hits"][kw] = 0
        for pno in pages:
            quads = doc[pno - 1].search_for(kw, quads=True)
            if quads:
                hit_pages.setdefault(pno, {})[kw] = quads[:MAX_HITS_PER_KW]
                rec["hits"][kw] = len(quads[:MAX_HITS_PER_KW])
                break
    if not kws:
        hit_pages = {pages[0]: {}}

    zoom = fitz.Matrix(SCALE, SCALE)
    for pno in sorted(hit_pages)[:4]:
        page = doc[pno - 1]
        rects = []
        for kw, quads in hit_pages[pno].items():
            for q in quads:
                page.add_highlight_annot(q)
                rect = q.rect
                box = page.add_rect_annot(fitz.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2))
                box.set_colors(stroke=(1, 0.23, 0.19))
                box.set_border(width=1.2)
                box.update()
                rects.append(rect)
        full = os.path.join(out_dir, f"{prefix}_第{pno}页.png")
        page.get_pixmap(matrix=zoom, annots=True).save(full)
        rec["files"].append(os.path.basename(full))
        if rects:
            y0 = max(page.rect.y0, min(r.y0 for r in rects) - 110)
            y1 = min(page.rect.y1, max(r.y1 for r in rects) + 110)
            clip = fitz.Rect(page.rect.x0, y0, page.rect.x1, y1)
            crop = os.path.join(out_dir, f"{prefix}_高亮_p{pno}.png")
            page.get_pixmap(matrix=zoom, clip=clip, annots=True).save(crop)
            rec["files"].append(os.path.basename(crop))
    doc.close()
    return rec


# ---------------- 索引 ----------------

STATUS_ICON = {"ok": "✅ 成功", "partial": "⚠️ 部分（关键词未全部命中）", "error": "❌ 失败",
               "rejected": "🚫 拒截（信源不够权威）", "skipped": "⏭ 已存在，跳过"}


def judge_status(rec, item):
    if rec.get("rejected"):
        return "rejected"
    if rec.get("error"):
        return "error"
    kws = item.get("highlight") or []
    if kws and any(rec["hits"].get(k, 0) == 0 for k in kws):
        return "partial"
    if rec.get("crop_problems"):
        return "partial"
    return "ok"


def render_index(out_dir, project, records, unsourced=None):
    lines = [f"# 证据截图清单 · {project}" if project else "# 证据截图清单", ""]
    cnt = {k: sum(r["status"] == k for r in records) for k in ("ok", "partial", "error", "rejected")}
    lines += [
        f"> 共 {len(records)} 条：成功 {cnt['ok']} / 部分 {cnt['partial']} / 失败 {cnt['error']} / 拒截 {cnt['rejected']}。"
        f"更新于 {time.strftime('%Y-%m-%d %H:%M')}。",
        "> 只收 A 级（官方原文：财报公告、交易所、政府监管）和 B 级（官方媒体、证券报、主流财经媒体、券商研报）出处。"
        "雪球、股吧、百家号、东方财富号、网易号、搜狐号、微博、公众号等一律不截。",
        "> 截图是抓取当时的页面，行情页数字会随时间变化，以抓取时间为准。",
        "",
    ]
    if unsourced:
        lines += ["## ⚠️ 待补权威信源（稿中这些说法目前只有自媒体出处，没有截图）", ""]
        lines += ["| 稿中说法 | 目前出处 | 建议 |", "|---|---|---|"]
        for u in unsourced:
            lines.append(f"| {u.get('quote', '')} | {u.get('current_source', '')} | {u.get('suggestion', '')} |")
        lines.append("")
    for r in records:
        lines.append(f"## {r['id']} {r['name']}（{r.get('kind') or '未分类'}）")
        lines.append("")
        if r.get("quote"):
            lines.append(f"- 稿中对应：「{r['quote']}」")
        if r.get("source"):
            lines.append(f"- 来源：{r['source']}")
        if r.get("tier"):
            lines.append(f"- 权威等级：{TIER_LABEL.get(r['tier'], r['tier'])}" + (f"（{r['tier_note']}）" if r.get("tier_note") else ""))
        lines.append(f"- 原链接：{r['url']}")
        used = r.get("used_url")
        if used and used != r["url"]:
            lines.append(f"- 实际截图链接（原链接不可用，改用备用）：{used}")
        if r.get("page_title"):
            lines.append(f"- 页面标题：{r['page_title']}")
        if r.get("captured_at"):
            lines.append(f"- 抓取时间：{r['captured_at']}")
        if r.get("hits"):
            hits = " / ".join(f"{k} {'✅' if v else '❌'}" for k, v in r["hits"].items())
            lines.append(f"- 高亮关键词：{hits}")
        lines.append(f"- 状态：{STATUS_ICON.get(r['status'], r['status'])}")
        if r.get("rejected"):
            lines.append(f"- 拒截原因：{r['rejected']}")
        if r.get("error"):
            lines.append(f"- 失败原因：{r['error']}")
        if r.get("crop_problems"):
            lines.append(f"- 截图自检：{'；'.join(r['crop_problems'])}")
        if r.get("note"):
            lines.append(f"- 备注：{r['note']}")
        files = r.get("files") or []
        if files:
            lines.append("- 文件：" + "、".join(f"[{f}](<{f}>)" for f in files))
            pngs = [f for f in files if f.endswith(".png")]
            main = next((f for f in pngs if "_高亮" in f), None) or next((f for f in pngs if "_元素" in f), None) \
                or (pngs[0] if pngs else None)
            if main:
                lines += ["", f"![{r['name']}](<{main}>)"]
        lines.append("")
    with open(os.path.join(out_dir, "证据清单.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def load_index(out_dir):
    p = os.path.join(out_dir, "证据清单.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"project": "", "items": []}


def save_index(out_dir, data):
    data["items"].sort(key=lambda r: r["id"])
    with open(os.path.join(out_dir, "证据清单.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    render_index(out_dir, data.get("project", ""), data["items"], data.get("unsourced"))


# ---------------- 主流程 ----------------

def main():
    ap = argparse.ArgumentParser(description="证据截图：网页/PDF 高亮截图 + 原链接归档")
    ap.add_argument("--manifest", "-m", help="证据清单 JSON")
    ap.add_argument("--out-dir", "-o", required=True, help="输出目录（视频的 参考资料/证据截图）")
    ap.add_argument("--only", help="只跑这些 id，逗号分隔")
    ap.add_argument("--force", action="store_true", help="覆盖已成功的条目")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口（调试）")
    ap.add_argument("--check", action="store_true", help="只检查清单里每个链接的权威等级，不截图")
    # 单条模式
    ap.add_argument("--url")
    ap.add_argument("--id")
    ap.add_argument("--name")
    ap.add_argument("--kind")
    ap.add_argument("--type", default="auto")
    ap.add_argument("--source")
    ap.add_argument("--quote")
    ap.add_argument("--highlight", action="append", default=[])
    ap.add_argument("--pages", help="PDF 页码，逗号分隔")
    ap.add_argument("--selector")
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    index = load_index(out_dir)
    existing = {r["id"]: r for r in index["items"]}

    if args.manifest:
        with open(args.manifest, encoding="utf-8") as f:
            man = json.load(f)
        items = man.get("items", [])
        if man.get("project"):
            index["project"] = man["project"]
        index["unsourced"] = man.get("unsourced") or []
        # 清单里删掉的条目，索引里也删掉（文件留给用户自己决定）
        keep = {str(it.get("id", "")).zfill(2) for it in items if it.get("id")}
        if keep:
            existing = {k: v for k, v in existing.items() if k in keep}
    elif args.url:
        items = [{
            "id": args.id, "name": args.name or "证据", "kind": args.kind, "url": args.url,
            "type": args.type, "source": args.source, "quote": args.quote, "highlight": args.highlight,
            "pages": [int(x) for x in args.pages.split(",")] if args.pages else None,
            "selector": args.selector,
        }]
    else:
        ap.error("需要 --manifest 或 --url")

    if args.check:
        bad = 0
        for it in items:
            for url in [it["url"]] + list(it.get("alt_urls") or []):
                tier, why = resolve_tier(it, url)
                bad += tier in ("C", "U")
                print(f"{str(it.get('id', '')):>3} {TIER_LABEL[tier]:<18} {it.get('name', '')}  {url}" + (f"\n      {why}" if why else ""))
        print(f"\n不合格链接 {bad} 个" if bad else "\n全部链接都是 A/B 级")
        return

    next_no = max([int(k) for k in existing if str(k).isdigit()] + [0]) + 1
    for it in items:
        if not it.get("id"):
            it["id"] = f"{next_no:02d}"
            next_no += 1
        it["id"] = str(it["id"]).zfill(2)
    only = {x.strip().zfill(2) for x in args.only.split(",")} if args.only else None

    todo = []
    for it in items:
        if only and it["id"] not in only:
            continue
        old = existing.get(it["id"])
        if old and old["status"] == "ok" and not args.force and \
                all(os.path.exists(os.path.join(out_dir, f)) for f in old.get("files", [])):
            log(f"{it['id']} 已成功截过，跳过（--force 覆盖）")
            continue
        todo.append(it)

    pw = browser = ctx = None
    warmed = set()
    if any(detect_type(it) == "web" for it in todo):
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        launch = {"headless": not args.show, "args": ["--disable-blink-features=AutomationControlled"]}
        exe = find_chromium()
        if exe:
            launch["executable_path"] = exe
        browser = pw.chromium.launch(**launch)
        ctx = browser.new_context(user_agent=UA, locale="zh-CN", viewport=VIEWPORT, device_scale_factor=SCALE)
        ctx.add_init_script(STEALTH_JS)

    try:
        for it in todo:
            prefix = f"{it['id']}_{safe_name(it.get('name') or '证据')}"
            kind = detect_type(it)
            urls = [it["url"]] + list(it.get("alt_urls") or [])
            rec, errors = None, []
            rejected = []
            for url in urls:
                tier, why = resolve_tier(it, url)
                if tier in ("C", "U"):
                    rejected.append(f"{url}（{TIER_LABEL[tier]}：{why}）")
                    log(f"{it['id']} 跳过非权威链接 {url}：{why}")
                    if url == urls[-1] and rec is None:
                        break
                    continue
                try:
                    rec = capture_pdf(it, url, out_dir, prefix) if kind == "pdf" \
                        else capture_web(ctx, it, url, out_dir, prefix, warmed)
                    rec["tier"] = tier
                    if why:
                        rec["tier_note"] = why
                    if judge_status(rec, it) == "ok" or url == urls[-1]:
                        break
                    log(f"{it['id']} 关键词未全部命中，换备用链接")
                except Exception as e:
                    msg = str(e).splitlines()[0][:200]
                    errors.append(f"{url} → {msg}")
                    log(f"{it['id']} 失败: {msg}")
                    rec = None
                time.sleep(1.5)
            if rec is None and rejected and not errors:
                rec = {"files": [], "hits": {}, "rejected": "；".join(rejected)}
            elif rec is None:
                rec = {"files": [], "hits": {}, "error": "；".join(errors + rejected)}
            rec.update({k: it.get(k) for k in ("id", "name", "kind", "url", "source", "quote")})
            rec["captured_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            rec["status"] = judge_status(rec, it)
            if errors and rec["status"] != "error":
                rec["note"] = "前面的链接失败：" + "；".join(errors)
            existing[it["id"]] = rec
            index["items"] = list(existing.values())
            save_index(out_dir, index)   # 每条落一次盘，中途中断也不丢
            log(f"{it['id']} {it.get('name')}：{STATUS_ICON[rec['status']]}  {rec.get('files')}")
    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()

    index["items"] = list(existing.values())
    save_index(out_dir, index)
    log(f"证据清单：{os.path.join(out_dir, '证据清单.md')}")


if __name__ == "__main__":
    main()
