#!/usr/bin/env python3
"""正規化・関連度採点・直近フィルタ・topN選別。

collectors の生データを {source, time, title, body, url, role} に正規化し、
直近lookbackHours × 金関連度 × 話題性(ソース重み) で採点して topN を選ぶ。
"""
from __future__ import annotations

def rank(items: list[dict], keywords: list[str], lookback_hours: int, top_n: int = 5) -> list[dict]:
    raise NotImplementedError("正規化→採点→topN選別")

if __name__ == "__main__":
    print("rank: stub")
