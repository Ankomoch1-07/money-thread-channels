#!/usr/bin/env python3
"""正規化・関連度採点・直近フィルタ・topN選別。

reference等の生アイテムを、金関連キーワードのヒット数＋新しさで採点して上位を選ぶ。
"""
from __future__ import annotations
import datetime

def _recency_score(published_iso: str | None) -> float:
    if not published_iso:
        return 0.3
    try:
        dt = datetime.datetime.fromisoformat(published_iso)
        hours = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 3600
        return max(0.0, 1.0 - hours / 72)     # 3日で0に減衰
    except Exception:
        return 0.3

def rank(items: list[dict], keywords: list[str], top_n: int = 5) -> list[dict]:
    scored = []
    for it in items:
        title = (it.get("title") or "").lower()
        kw = sum(1 for k in keywords if k.lower() in title)
        score = kw + _recency_score(it.get("published"))
        scored.append((score, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:top_n]]

if __name__ == "__main__":
    print("rank: import OK")
