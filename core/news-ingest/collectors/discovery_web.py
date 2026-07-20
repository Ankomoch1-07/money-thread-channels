#!/usr/bin/env python3
"""discovery層：WebSearchで突発ネタを補完（定常コレクターの拾い漏れ）。

best-effort。検索APIキー(GOOGLE_CSE_KEY/GOOGLE_CSE_CX 等)が設定されていれば使い、
無ければ {} を返してスキップ（fact/referenceが本命なので無くても回る）。
将来：fact層の無料枠が落ちた日の価格拾いフォールバックもここに寄せられる。
"""
from __future__ import annotations
import os, urllib.request, urllib.parse, json

def collect(web_queries: list[str], max_per_query: int = 3) -> dict:
    key, cx = os.environ.get("GOOGLE_CSE_KEY"), os.environ.get("GOOGLE_CSE_CX")
    if not (key and cx):
        return {}   # キー未設定：スキップ（silent fail回避のため build_ingest 側でログ）
    topics = []
    for q in web_queries or []:
        try:
            url = ("https://www.googleapis.com/customsearch/v1?"
                   + urllib.parse.urlencode({"key": key, "cx": cx, "q": q, "num": max_per_query}))
            data = json.loads(urllib.request.urlopen(url, timeout=20).read())
            for item in data.get("items", []):
                topics.append(item.get("title", ""))
        except Exception:
            continue
    return {"extra_topics": list(dict.fromkeys(t for t in topics if t))}

if __name__ == "__main__":
    print("discovery_web: import OK（GOOGLE_CSE_KEY/CX未設定ならスキップ）")
