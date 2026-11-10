#!/usr/bin/env python3
"""
在巨潮资讯（证监会指定披露网站）查 A 股公司公告，拿到财报 / 业绩预告等原文 PDF 链接，
给 evidence_capture.py 当证据清单里的 url 用。

用法:
    python3 cninfo_announcements.py 赣锋锂业 --keyword 三季度报告
    python3 cninfo_announcements.py 002460 --keyword 年度报告 --start 2023-01-01 --end 2023-12-31
    python3 cninfo_announcements.py 赣锋锂业 --keyword 业绩预告 --json
    python3 cninfo_announcements.py 赣锋锂业 --ir          # 投资者关系活动记录表（公司口径的经营说明）

说明:
    - 第一个参数传股票名或 6 位代码都行，脚本先查 orgId 再查公告。
    - --keyword 按公告标题包含关系过滤（不传就列出时间段内全部公告）。
    - 默认查最近 365 天。年报想看"主要会计数据"优先用「年度报告摘要」，页数少、截图快。
    - 只覆盖 A 股（沪深北）。港股、美股公告不在巨潮。
"""
import argparse
import datetime as dt
import json
import sys

import requests

BASE = "http://www.cninfo.com.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": f"{BASE}/new/disclosure",
}


def lookup(session, key):
    r = session.post(f"{BASE}/new/information/topSearch/query",
                     data={"keyWord": key, "maxNum": "10"}, timeout=20)
    r.raise_for_status()
    hits = [h for h in r.json() if h.get("category") == "A股"]
    if not hits:
        raise SystemExit(f"巨潮里没找到 A 股「{key}」")
    exact = [h for h in hits if key in (h["code"], h["zwjc"])]
    return (exact or hits)[0]


def column_of(code):
    if code.startswith(("6", "9")):
        return "sse"
    if code.startswith(("4", "8")):
        return "bj"
    return "szse"


def query(session, sec, start, end, keyword, tab="fulltext"):
    out, page = [], 1
    while True:
        r = session.post(f"{BASE}/new/hisAnnouncement/query", data={
            "stock": f"{sec['code']},{sec['orgId']}", "tabName": tab,
            "pageSize": "30", "pageNum": str(page), "column": column_of(sec["code"]),
            "category": "", "plate": "", "seDate": f"{start}~{end}",
            "searchkey": "", "isHLtitle": "true",
        }, timeout=20)
        r.raise_for_status()
        j = r.json()
        for a in j.get("announcements") or []:
            title = a["announcementTitle"].replace("<em>", "").replace("</em>", "")
            if keyword and keyword not in title:
                continue
            out.append({
                "date": dt.datetime.fromtimestamp(a["announcementTime"] / 1000).strftime("%Y-%m-%d"),
                "title": title,
                "url": f"http://static.cninfo.com.cn/{a['adjunctUrl']}",
                "size_kb": a.get("adjunctSize"),
            })
        if not j.get("hasMore"):
            break
        page += 1
        if page > 20:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description="巨潮资讯公告查询（拿财报 PDF 链接）")
    ap.add_argument("stock", help="股票名或 6 位代码")
    ap.add_argument("--keyword", "-k", default="", help="公告标题关键词，如 三季度报告 / 年度报告摘要 / 业绩预告")
    ap.add_argument("--start", default=(dt.date.today() - dt.timedelta(days=365)).isoformat())
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--ir", action="store_true", help="查投资者关系活动记录表（调研纪要、业绩说明会），而不是公告")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update(HEADERS)
    sec = lookup(s, args.stock)
    rows = query(s, sec, args.start, args.end, args.keyword, "relation" if args.ir else "fulltext")
    if args.json:
        print(json.dumps({"code": sec["code"], "name": sec["zwjc"], "items": rows}, ensure_ascii=False, indent=2))
        return
    print(f"{sec['zwjc']}（{sec['code']}） {args.start}~{args.end} 共 {len(rows)} 条", file=sys.stderr)
    for r in rows:
        print(f"{r['date']}  {r['title']}  {r['url']}  ({r['size_kb']}KB)")


if __name__ == "__main__":
    main()
