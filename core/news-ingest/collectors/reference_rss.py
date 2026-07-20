#!/usr/bin/env python3
"""reference層：ニュースRSSから金関連の見出し・URL・日時を収集（stdlibのみ）。

本文はコピーしない（見出し/URL/日時のみ保持）。金関連キーワード＋直近lookbackHoursで絞り込み。
why_moved(因果)への加工は digest.py が行う。
"""
from __future__ import annotations
import urllib.request, xml.etree.ElementTree as ET, datetime, email.utils

def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read()

def _parse_dt(s: str):
    if not s:
        return None
    try:
        return email.utils.parsedate_to_datetime(s)
    except Exception:
        return None

def collect(rss_sources: list[dict], keywords: list[str], lookback_hours: int) -> list[dict]:
    """[{title, url, publisher, published(iso)}] を返す。失敗したフィードはスキップ。"""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=lookback_hours)
    out = []
    for src in rss_sources or []:
        url = src.get("url")
        if not url:
            continue
        try:
            root = ET.fromstring(_fetch(url))
        except Exception:
            continue
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            dt = _parse_dt(it.findtext("pubDate") or "")
            if keywords and not any(k.lower() in title.lower() for k in keywords):
                continue
            if dt and dt < cutoff:
                continue
            out.append({"title": title, "url": link, "publisher": src.get("id", ""),
                        "published": dt.isoformat() if dt else None})
    return out

if __name__ == "__main__":
    demo = collect([{"id": "yahoo_gold",
                     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US"}],
                   [], 24 * 30)
    print(f"{len(demo)} items")
    for d in demo[:5]:
        print(" -", d["title"][:80])
